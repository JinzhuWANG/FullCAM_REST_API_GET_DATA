import os
import re
import numpy as np
import pandas as pd
import xarray as xr
import rioxarray as rxr
import plotnine as p9

from pathlib import Path
from tqdm.auto import tqdm
from glob import glob
from functools import partial

from tools import get_downloading_coords, get_plot_simulation
from tools.parameter import SPECIES_GEOMETRY


# Get all coordinates for selected region and RES
RES_factor = 1
scrap_coords = get_downloading_coords(resfactor=3, include_region='LUTO') # Here use resfactor=3 just to get random coords faster

# Get coordinates for comparison
compare_coords = scrap_coords.sample(n=1000, random_state=42).set_index(['x', 'y']).index.tolist()
compare_coords_x = xr.DataArray([coord[0] for coord in compare_coords], dims='points')
compare_coords_y = xr.DataArray([coord[1] for coord in compare_coords], dims='points')

# Set data paths
v2000_path = Path('N:/Data-Master/FullCAM/Output_TOT_CO2_HA_GeoTiffs')
comparison_dir = Path('data/processed/Compare_API_and_Assemble_Data_Simulations')
download_csv_dir = comparison_dir/'download_csv'

# Set the directory to save downloaded CSV files
get_plot_simulation = partial(get_plot_simulation, download_csv_dir=download_csv_dir)

# Set comparison year
compare_year = 2100
SPECIES_ID = 8
SPECIES_CAT = 'Belt'

# Set the species to previous v2000 naming convention
if SPECIES_ID == 7:
    SPECIES_v2000_NAME = 'EP'
elif SPECIES_ID == 8:
    SPECIES_v2000_NAME = 'EGLOB'
elif SPECIES_ID == 23:
    SPECIES_v2000_NAME = 'MALLEE'

if 'block' in SPECIES_CAT.lower():
    SPECIES_v2000_CAT = 'BLOCK' 
elif 'belt' in SPECIES_CAT.lower():
    SPECIES_v2000_CAT = 'BELT' 
elif 'water' in SPECIES_CAT.lower():
    SPECIES_v2000_CAT = 'RIP' 


################################################################
#                          Get API data                        #
################################################################
'''
Individual data points are saved as CSV files in the `download_csv_dir` directory.
'''

# Get API Key
API_KEY = os.getenv("FULLCAM_API_KEY")
BASE_URL_SIM = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1"
ENDPOINT = "/2024/fullcam-simulator/run-plotsimulation"

url = f"{BASE_URL_SIM}{ENDPOINT}"
headers = {"Ocp-Apim-Subscription-Key": API_KEY}


# Download data from API for comparison coords
def download_api_data(compare_coords, specId, specCat):
    for lon, lat in tqdm(compare_coords):
        if os.path.exists(f'{download_csv_dir}/df_{lon}_{lat}_specId_{specId}_specCat_{specCat}.csv'):
            continue
        get_plot_simulation('API', lon, lat, None, None, specId, specCat, url, headers)

for specId, specCats in SPECIES_GEOMETRY.items():
    for specCat in specCats:
        download_api_data(compare_coords, specId, specCat)





################################################################
#                Get Cache simulation data                     #
################################################################

# Get FullCAM Cached data
fullcam_cache_data = f"data/processed/Output_GeoTIFFs/carbonstock_RES_{RES_factor}_specId_{SPECIES_ID}_specCat_{SPECIES_CAT}.nc"
ds_cache = xr.open_dataset(fullcam_cache_data, chunks={})['data'].sel(YEAR=compare_year, drop=True).compute() 



################################################################
#                        Get v2000 data                        #
################################################################

C_CO2_ratio = 12 / 44  # To convert from CO2 to C

# Get v2000 Cached data; band 91 is carbon in 2100
Debries_C = rxr.open_rasterio(v2000_path / f'{SPECIES_v2000_NAME}_{SPECIES_v2000_CAT}_TREES_T_CO2_HA.tif', masked=True, chunks={}) * C_CO2_ratio
Trees_C = rxr.open_rasterio(v2000_path   / f'{SPECIES_v2000_NAME}_{SPECIES_v2000_CAT}_DEBRIS_T_CO2_HA.tif', masked=True, chunks={}) * C_CO2_ratio
Soil_C = rxr.open_rasterio(v2000_path    / f'{SPECIES_v2000_NAME}_{SPECIES_v2000_CAT}_SOIL_T_CO2_HA.tif', masked=True, chunks={}) * C_CO2_ratio

# Select only year 2100 (band 91)
Debries_C_sel = Debries_C.sel(band=91, drop=True).compute()
Trees_C_sel = Trees_C.sel(band=91, drop=True).compute()
Soil_C_sel = Soil_C.sel(band=91, drop=True).compute()

# Combine v2000 data into a single DataArray
ds_v2000 = xr.DataArray(
    data = np.stack([Debries_C_sel.data, Trees_C_sel.data, Soil_C_sel.data], axis=0),
    dims = ['VARIABLE', 'y', 'x'],
    coords = {
        'VARIABLE': ['TREE_C_HA', 'DEBRIS_C_HA', 'SOIL_C_HA'],
        'y': Trees_C_sel.y,
        'x': Soil_C_sel.x,
    }
)


################################################################
#               API v.s Cached v.s v2000                       #
################################################################

csv_files = [i for i in glob(f'{download_csv_dir}/*.csv') if f'specId_{SPECIES_ID}_specCat_{SPECIES_CAT}' in i]

df_comparison = pd.DataFrame()
for f in tqdm(csv_files):
    # Get API data
    df_api = pd.read_csv(f)[['Year', 'C mass of plants  (tC/ha)', 'C mass of debris  (tC/ha)', 'C mass of soil  (tC/ha)']]
    df_api = df_api.rename(columns={
        'C mass of plants  (tC/ha)': 'TREE_C_HA',
        'C mass of debris  (tC/ha)': 'DEBRIS_C_HA',
        'C mass of soil  (tC/ha)': 'SOIL_C_HA',
    })
    df_api = df_api.query(f'Year == {compare_year}')
    df_api = df_api.melt(id_vars=['Year'], var_name='VARIABLE', value_name='data_api')
    
    # Get Cache data
    lon, lat  = re.findall(r'df_(-?\d+\.\d+)_(-?\d+\.\d+)_specId_', os.path.basename(f))[0]
    lon, lat = float(lon), float(lat)
    df_cache = ds_cache.sel(x=lon, y=lat, method='nearest').to_dataframe().reset_index()
    df_cache = df_cache.rename(columns={'YEAR':'Year', 'data':'data_cache'})
    df_cache = df_cache[['VARIABLE', 'data_cache']]
    
    # Get v2000 data
    df_v2000 = ds_v2000.sel(x=lon, y=lat, method='nearest').to_dataframe('data_v2000').reset_index()
    df_v2000 = df_v2000[['VARIABLE', 'data_v2000']]
    
    
    df_combine = df_api.merge(df_cache, on=['VARIABLE']).merge(df_v2000, on=['VARIABLE'])
    df_combine[['lon', 'lat']] = lon, lat
    df_comparison = pd.concat([df_comparison, df_combine], ignore_index=True)



# API v.s Cache simulation
p9.options.figure_size = (10, 6)
p9.options.dpi = 100

fig1 = (
    p9.ggplot(df_comparison)
    + p9.geom_point(
        p9.aes(x='data_api', y='data_cache'), size=0.5, alpha=0.3
    )
    + p9.facet_wrap('~VARIABLE', scales='free')
    + p9.geom_abline(slope=1, intercept=0, color='red', linetype='dashed')
    + p9.labs(
        title=f'Carbon Comparison at Year {compare_year} (API vs Cache)',
        x='Carbon from API (tC/ha)',
        y='Carbon from Cache (tC/ha)',
    )
)

fig1.save(comparison_dir/f'{SPECIES_v2000_NAME}_{SPECIES_CAT}_Compare_API_V.S_Cache_Year_{compare_year}.svg', dpi=300)


# Cache simulation v.s v2000
fig2 = (
    p9.ggplot(df_comparison)
    + p9.geom_point(
        p9.aes(x='data_cache', y='data_v2000'), size=0.5, alpha=0.3
    )
    + p9.facet_wrap('~VARIABLE', scales='free')
    + p9.geom_abline(slope=1, intercept=0, color='red', linetype='dashed')
    + p9.labs(
        title=f'Carbon Comparison at Year {compare_year} (Cache vs v2000)',
        x='FullCam v2024 (tC/ha)',
        y='FullCam v2000 (tC/ha)',
    )
)

fig2.save(comparison_dir/f'{SPECIES_v2000_NAME}_{SPECIES_CAT}_Compare_New_V.S_Old_Year_{compare_year}.svg', dpi=300)


# Compute difference ratios
ds_v2000['x'] = ds_cache['x']
ds_v2000['y'] = ds_cache['y']
diff_ratio = ds_cache / ds_v2000
diff_ratio.rio.write_crs(Debries_C.rio.crs, inplace=True)
diff_ratio.rio.write_transform(Debries_C.rio.transform(), inplace=True)

for var in diff_ratio['VARIABLE'].values:
    diff_ratio.sel(VARIABLE=var).rio.to_raster(comparison_dir/f'{SPECIES_v2000_NAME}_{SPECIES_CAT}_{var}_New_V.S_Old_ratio_{compare_year}.tif', compress='LZW')




################################################################
#                  Trees v.s Debries v.s Soil                  #
################################################################


# Componet boxplot
ds_cache_sel = ds_cache.sel(x=compare_coords_x, y=compare_coords_y).to_dataframe().reset_index()

fig3 = (
    p9.ggplot(ds_cache_sel)
    + p9.geom_violin(
        p9.aes(x='VARIABLE', y='data'), fill='lightblue', alpha=0.7
    )
    + p9.geom_boxplot(
        p9.aes(x='VARIABLE', y='data'), width=0.1, fill='white', outlier_size=0.5
    )
    + p9.labs(
        title=f'Carbon Component Distribution at Year {compare_year} (Cache Data)',
        x='Carbon Component',
        y='Carbon Stock (tC/ha)',
    )
)

fig3.save(comparison_dir/f'{SPECIES_v2000_NAME}_{SPECIES_CAT}_Componet_Boxplot_Year_{compare_year}.svg', dpi=300)


# Componet ratio layers
total_carbon = ds_cache.sum(dim='VARIABLE', skipna=False)

tree_ratio = ds_cache.sel(VARIABLE='TREE_C_HA') / total_carbon * 100
debries_ratio = ds_cache.sel(VARIABLE='DEBRIS_C_HA') / total_carbon * 100
soil_ratio = ds_cache.sel(VARIABLE='SOIL_C_HA') / total_carbon * 100

for ratio_da, name in zip(
    [tree_ratio, debries_ratio, soil_ratio],
    ['Tree', 'Debries', 'Soil']
):
    ratio_da.rio.write_crs(Debries_C.rio.crs, inplace=True)
    ratio_da.rio.write_transform(Debries_C.rio.transform(), inplace=True)
    ratio_da.rio.to_raster(comparison_dir/f'{SPECIES_v2000_NAME}_{SPECIES_CAT}_Componet_ratio_{name}_Year_{compare_year}.tif', compress='LZW')

