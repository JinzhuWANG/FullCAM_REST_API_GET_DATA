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
RES_factor = 3
scrap_coords = get_downloading_coords(resfactor=RES_factor, include_region='LUTO')

# Get coordinates for comparison
compare_coords = scrap_coords.sample(n=1000, random_state=42).set_index(['x', 'y']).index.tolist()
compare_coords_x = xr.DataArray([coord[0] for coord in compare_coords], dims='points')
compare_coords_y = xr.DataArray([coord[1] for coord in compare_coords], dims='points')

# Set data paths
v2016_path = Path('N:/Data-Master/FullCAM/Output_TOT_CO2_HA_GeoTiffs')
comparison_dir = Path('data/processed/Compare_API_and_Assemble_Data_Simulations')
download_csv_dir = comparison_dir/'download_csv'

# Set the directory to save downloaded CSV files
get_plot_simulation = partial(get_plot_simulation, download_csv_dir=download_csv_dir)

# Set comparison year
compare_year = 2100
SPECIES_ID = 8
SPECIES_CAT = 'Belt'



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
fullcam_cache_data = "data/processed/20260101_RES1_CP_Block/carbonstock_RES_1.nc"
ds_cache = xr.open_dataset(fullcam_cache_data, chunks={})['data'].sel(YEAR=compare_year, drop=True).compute() 



################################################################
#                        Get v2016 data                        #
################################################################

C_CO2_ratio = 12 / 44  # To convert from CO2 to C

# Get v2016 Cached data; band 91 is carbon in 2100

Debries_C = rxr.open_rasterio(v2016_path / 'CP_BLOCK_TREES_T_CO2_HA.tif', masked=True, chunks={}) * C_CO2_ratio
Trees_C = rxr.open_rasterio(v2016_path   / 'CP_BLOCK_DEBRIS_T_CO2_HA.tif', masked=True, chunks={}) * C_CO2_ratio
Soil_C = rxr.open_rasterio(v2016_path    / 'CP_BLOCK_SOIL_T_CO2_HA.tif', masked=True, chunks={}) * C_CO2_ratio

ds_v2016 = xr.DataArray(
    data = np.stack([Trees_C.data, Debries_C.data, Soil_C.data], axis=0),
    dims = ['VARIABLE', 'band', 'y', 'x'],
    coords = {
        'VARIABLE': ['TREE_C_HA', 'DEBRIS_C_HA', 'SOIL_C_HA'],
        'band': range(2010, 2101),
        'y': Trees_C.y,
        'x': Trees_C.x,
    }
).rename({'band':'Year'}).sel(Year=compare_year, drop=True).compute()



################################################################
#                       API v.s Cached                         #
################################################################


csv_files = [i for i in glob(f'{download_csv_dir}/*.csv') if f'specId_{SPECIES_ID}_specCat_{SPECIES_CAT}' in i]

df_comparison = pd.DataFrame()
for f in tqdm(glob(f'{download_csv_dir}/*.csv')):
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
    
    # Get v2016 data
    df_v2016 = ds_v2016.sel(x=lon, y=lat, method='nearest').to_dataframe('data_v2016').reset_index()
    df_v2016 = df_v2016[['VARIABLE', 'data_v2016']]
    
    
    df_combine = df_api.merge(df_cache, on=['VARIABLE']).merge(df_v2016, on=['VARIABLE'])
    df_comparison = pd.concat([df_comparison, df_combine], ignore_index=True)



# API v.s Cache simulation
p9.options.figure_size = (10, 6)
p9.options.dpi = 100

fig = (
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

# Cache simulation v.s v2016
fig2 = (
    p9.ggplot(df_comparison)
    + p9.geom_point(
        p9.aes(x='data_cache', y='data_v2016'), size=0.5, alpha=0.3
    )
    + p9.facet_wrap('~VARIABLE', scales='free')
    + p9.geom_abline(slope=1, intercept=0, color='red', linetype='dashed')
    + p9.labs(
        title=f'Carbon Comparison at Year {compare_year} (Cache vs v2016)',
        x='Carbon from Cache (tC/ha)',
        y='Carbon from v2016 (tC/ha)',
    )
)


################################################################
#                     Spatial differences                      #
################################################################

# Compute difference ratios
ds_v2016['x'] = ds_cache['x']
ds_v2016['y'] = ds_cache['y']
diff_ratio = ds_cache / ds_v2016
diff_ratio.rio.write_crs(Debries_C.rio.crs, inplace=True)
diff_ratio.rio.write_transform(Debries_C.rio.transform(), inplace=True)

for var in diff_ratio['VARIABLE'].values:
    diff_ratio.sel(VARIABLE=var).rio.to_raster(comparison_dir/f'Cache_simulation_over_V2016_diff_ratio_{var}_{compare_year}.tif', compress='LZW')