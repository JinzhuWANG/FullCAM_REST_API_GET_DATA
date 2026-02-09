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
LUTO_lumap = rxr.open_rasterio('data/lumap.tif', masked=True)


# Get coordinates for comparison
compare_coords = scrap_coords.sample(n=1000, random_state=42).set_index(['x', 'y']).index.tolist()
compare_coords_x = xr.DataArray([coord[0] for coord in compare_coords], dims='points')
compare_coords_y = xr.DataArray([coord[1] for coord in compare_coords], dims='points')

# Set data paths
v2020_path = Path('N:/Data-Master/FullCAM/Output_layers')
comparison_dir = Path('data/processed/Compare_API_and_Assemble_Data_Simulations')
download_csv_dir = comparison_dir/'download_csv'

# Set the directory to save downloaded CSV files
get_plot_simulation = partial(get_plot_simulation, download_csv_dir=download_csv_dir)

# Set comparison year
compare_year = 2100
SPECIES_ID = 23
SPECIES_CAT = 'BeltHW'

# Set the species to previous v2020 naming convention
v2020_extra_case = 'ld'  # ld or hd.

if SPECIES_ID == 7 and SPECIES_CAT == 'BeltH':
    SPECIES_v2020_NAME = 'ep'
    SPECIES_v2020_CAT = f'belt_{v2020_extra_case}'
    v2020_debris_layer = v2020_path / f'{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_c_debris.tif'
    v2020_tree_layer = v2020_path / f'{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_c_trees.tif'
    v2020_soil_layer = v2020_path / f'{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_c_soil.tif'
elif SPECIES_ID == 7 and SPECIES_CAT == 'BlockES':
    SPECIES_v2020_NAME = 'ep'
    SPECIES_v2020_CAT = 'block'
    v2020_debris_layer = v2020_path / f'{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_c_debris.tif'
    v2020_tree_layer = v2020_path / f'{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_c_trees.tif'
    v2020_soil_layer = v2020_path / f'{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_c_soil.tif'
elif SPECIES_ID == 7 and SPECIES_CAT == 'Water':
    SPECIES_v2020_NAME = 'ep'
    SPECIES_v2020_CAT = 'rip'
    v2020_debris_layer = v2020_path / f'{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_c_debris.tif'
    v2020_tree_layer = v2020_path / f'{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_c_trees.tif'
    v2020_soil_layer = v2020_path / f'{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_c_soil.tif'
elif SPECIES_ID == 8:
    SPECIES_v2020_NAME = 'eglob'
    SPECIES_v2020_CAT = 'lr'
    v2020_debris_layer = v2020_path / f'{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_c_debris.tif'
    v2020_tree_layer = v2020_path / f'{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_c_trees.tif'
    v2020_soil_layer = v2020_path / f'{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_c_soil.tif'
elif SPECIES_ID == 23 and SPECIES_CAT == 'BeltHW':
    SPECIES_v2020_NAME = 'mal'
    SPECIES_v2020_CAT = f'belt_{v2020_extra_case}'
    v2020_debris_layer = v2020_path / f'{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_c_debris.tif'
    v2020_tree_layer = v2020_path / f'{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_c_trees.tif'
    v2020_soil_layer = v2020_path / f'{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_c_soil.tif'
elif SPECIES_ID == 23 and SPECIES_CAT == 'BlockES':
    SPECIES_v2020_NAME = 'mal'
    SPECIES_v2020_CAT = 'block'
    v2020_debris_layer = v2020_path / f'{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_c_debris.tif'
    v2020_tree_layer = v2020_path / f'{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_c_trees.tif'
    v2020_soil_layer = v2020_path / f'{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_c_soil.tif'
else:
    raise ValueError(f"Unsupported SPECIES_ID {SPECIES_ID} and SPECIES_CAT {SPECIES_CAT} combination for v2020 comparison.")


################################################################
#                          Get API data                        #
################################################################
'''
Individual data points are saved as CSV files in the `download_csv_dir` directory.
'''

# # Get API Key
# API_KEY = os.getenv("FULLCAM_API_KEY")
# BASE_URL_SIM = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1"
# ENDPOINT = "/2024/fullcam-simulator/run-plotsimulation"

# url = f"{BASE_URL_SIM}{ENDPOINT}"
# headers = {"Ocp-Apim-Subscription-Key": API_KEY}


# # Download data from API for comparison coords
# def download_api_data(compare_coords, specId, specCat):
#     for lon, lat in tqdm(compare_coords):
#         if os.path.exists(f'{download_csv_dir}/df_{lon}_{lat}_specId_{specId}_specCat_{specCat}.csv'):
#             continue
#         get_plot_simulation('API', lon, lat, None, None, specId, specCat, url, headers)

# for specId, specCats in SPECIES_GEOMETRY.items():
#     for specCat in specCats:
#         download_api_data(compare_coords, specId, specCat)





################################################################
#                Get Cache simulation data                     #
################################################################

# Get FullCAM Cached data
fullcam_cache_data = f"data/processed/Output_GeoTIFFs/carbonstock_RES_{RES_factor}_specId_{SPECIES_ID}_specCat_{SPECIES_CAT}.nc"
ds_cache = xr.open_dataset(fullcam_cache_data, chunks={})['data'].sel(YEAR=compare_year, drop=True).compute() 



################################################################
#                        Get v2020 data                        #
################################################################


# Get v2020 Cached data; band 91 is carbon in 2100
Debries_C = rxr.open_rasterio(v2020_debris_layer, masked=True, chunks={})
Trees_C = rxr.open_rasterio(v2020_tree_layer, masked=True, chunks={})
Soil_C = rxr.open_rasterio(v2020_soil_layer, masked=True, chunks={})

# Select only year 2100 (band 91)
Debries_C_sel = Debries_C.sel(band=91, drop=True).compute()
Trees_C_sel = Trees_C.sel(band=91, drop=True).compute()
Soil_C_sel = Soil_C.sel(band=91, drop=True).compute()

# Combine v2020 data into a single DataArray
ds_v2020 = xr.DataArray(
    data = np.stack([Debries_C_sel.data, Trees_C_sel.data, Soil_C_sel.data], axis=0),
    dims = ['VARIABLE', 'y', 'x'],
    coords = {
        'VARIABLE': ['DEBRIS_C_HA', 'TREE_C_HA', 'SOIL_C_HA'],
        'y': Trees_C_sel.y,
        'x': Soil_C_sel.x,
    }
)


################################################################
#               API v.s Cached v.s v2020                       #
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
    
    # Get v2020 data
    df_v2020 = ds_v2020.sel(x=lon, y=lat, method='nearest').to_dataframe('data_v2020').reset_index()
    df_v2020 = df_v2020[['VARIABLE', 'data_v2020']]
    
    
    df_combine = df_api.merge(df_cache, on=['VARIABLE']).merge(df_v2020, on=['VARIABLE'])
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

fig1.save(comparison_dir/f'{SPECIES_v2020_NAME}_{SPECIES_CAT}_Compare_API_V.S_Cache.svg', dpi=300)


# Cache simulation v.s v2020
fig2 = (
    p9.ggplot(df_comparison)
    + p9.geom_point(
        p9.aes(x='data_cache', y='data_v2020'), size=0.5, alpha=0.3
    )
    + p9.facet_wrap('~VARIABLE', scales='free')
    + p9.geom_abline(slope=1, intercept=0, color='red', linetype='dashed')
    + p9.labs(
        title=f'Carbon Comparison at Year {compare_year} (Cache vs v2020)',
        x='FullCam v2024 (tC/ha)',
        y='FullCam v2020 (tC/ha)',
    )
)

fig2.save(comparison_dir/f'{SPECIES_v2020_NAME}_{SPECIES_CAT}_v2024_V.S_{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_v2020.svg', dpi=300)


# Compute difference ratios
ds_v2020['x'] = ds_cache['x']
ds_v2020['y'] = ds_cache['y']
diff_ratio = ds_cache / ds_v2020
diff_ratio.rio.write_crs(Debries_C.rio.crs, inplace=True)
diff_ratio.rio.write_transform(Debries_C.rio.transform(), inplace=True)

for var in diff_ratio['VARIABLE'].values:
    diff_ratio.sel(VARIABLE=var).rio.to_raster(comparison_dir/f'ratio_layer_{SPECIES_v2020_NAME}_{SPECIES_CAT}_v2024_V.S_{SPECIES_v2020_NAME}_{SPECIES_v2020_CAT}_v2020_{var}.tif', compress='LZW')




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

fig3.save(comparison_dir/f'{SPECIES_v2020_NAME}_{SPECIES_CAT}_Componet_Boxplot_Year_{compare_year}.svg', dpi=300)


# Componet ratio layers
total_carbon = ds_cache.sum(dim='VARIABLE', skipna=False)

tree_ratio = ds_cache.sel(VARIABLE='TREE_C_HA') / total_carbon * 100
debries_ratio = ds_cache.sel(VARIABLE='DEBRIS_C_HA') / total_carbon * 100
soil_ratio = ds_cache.sel(VARIABLE='SOIL_C_HA') / total_carbon * 100

for ratio_da, name in zip(
    [tree_ratio, debries_ratio, soil_ratio],
    ['Tree', 'Debries', 'Soil']
):
    ratio_da.rio.write_crs(LUTO_lumap.rio.crs, inplace=True)
    ratio_da.rio.write_transform(LUTO_lumap.rio.transform(), inplace=True)
    ratio_da.rio.to_raster(comparison_dir/f'componet_layer_{SPECIES_v2020_NAME}_{SPECIES_CAT}_Componet_ratio_{name}_Year_{compare_year}.tif', compress='LZW')

