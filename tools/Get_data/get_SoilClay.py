
import os
import re
import pandas as pd
import rioxarray as rio
import xarray as xr
import numpy as np
import plotnine as p9

from glob import glob
from tqdm.auto import tqdm

from pathlib import Path
from tools.XML2Data import parse_soil_data
from tools.helpers.cache_manager import get_existing_downloads


# Config
RES_factor = 10
SPECIES_ID = 8          # Eucalyptus globulus
SPECIES_CAT = 'Block'   # Block or Belt; need to confirm with individual species
soil_path = Path('data/Soil_landscape_AUS/ClayContent/000055684v002/data')

# --------------- Get valid coords ---------------
PLO_data_path = Path('N:/Data-Master/FullCAM/FullCAM_REST_API_GET_DATA_2025/data/processed/BB_PLO_OneKm')
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads(SPECIES_ID, SPECIES_CAT)

Aus_xr = rio.open_rasterio("data/lumap.tif").sel(band=1, drop=True) >= -1 # >=-1 means all Australia continent
lon_lat = Aus_xr.to_dataframe(name='mask').reset_index()[['y', 'x', 'mask']].round({'x':2, 'y':2})
lon_lat['cell_idx'] = range(len(lon_lat))

Aus_cell = xr.DataArray(np.arange(Aus_xr.size).reshape(Aus_xr.shape), coords=Aus_xr.coords, dims=Aus_xr.dims)
Aus_cell_RES = Aus_cell.coarsen(x=RES_factor, y=RES_factor, boundary='trim').max()
Aus_cell_RES_df = Aus_cell_RES.to_dataframe(name='cell_idx').reset_index()['cell_idx']

RES_df = lon_lat.query('mask == True').loc[lon_lat['cell_idx'].isin(Aus_cell_RES_df)].reset_index(drop=True)
RES_coords = RES_df.set_index(['x', 'y']).index.tolist()

res_coords = set(existing_siteinfo).intersection(set(RES_coords))
res_coords_x = xr.DataArray([coord[0] for coord in res_coords], dims=['cell'])
res_coords_y = xr.DataArray([coord[1] for coord in res_coords], dims=['cell'])



# --------------- Load Soil Clay Data ---------------
clay_FULLCAM_ds = (
    xr.open_dataset('data/processed/soilbase_soilother_RES.nc')['data']
    .sel(band='clayFrac', drop=True)
)

soil_00_05 = (
    rio.open_rasterio(soil_path / '000-005cm/CLY_000_005_EV_N_P_AU_TRN_N_20210902.tif')
    .sel(band=1, drop=True)
)
soil_05_15 = (
    rio.open_rasterio(soil_path / '005-015cm/CLY_005_015_EV_N_P_AU_TRN_N_20210902.tif')
    .sel(band=1, drop=True)
)
soil_15_30 = (
    rio.open_rasterio(soil_path / '015-030cm/CLY_015_030_EV_N_P_AU_TRN_N_20210902.tif')
    .sel(band=1, drop=True)
)

soil_00_30 = (soil_00_05 + soil_05_15  + soil_15_30) / 3 / 100

soil_00_30.rio.write_crs("EPSG:4326", inplace=True)
soil_00_30.rio.write_transform(clay_FULLCAM_ds.rio.transform(), inplace=True)
soil_00_30.rio.to_raster(
    'data/Soil_landscape_AUS/ClayContent/clayFrac_00_30cm.tif',
    compress='LZW'
)



# ---------------------------- Plot comparison -------------------------------------

# Load SoilClay from Landscape Grid of Australia (SLGA)
soilClay_SLGA = rio.open_rasterio('data/Soil_landscape_AUS/ClayContent/clayFrac_00_30cm.tif').sel(band=1, drop=True).compute()

# Get downloaded carbon data CSV files; does not matter which species because SiteInfo is the same for all species
FullCAM_retrive_dir ='data/processed/Compare_API_and_Assemble_Data_Simulations/download_csv'
csv_files = [i for i in glob(f'{FullCAM_retrive_dir}/*.csv') if f'specId_8_specCat_Block' in i]

data_compare = pd.DataFrame()
for f in tqdm(csv_files):
    # Get Cache data
    #   The SiteInfo data for the FullCAM carbon df at lon/lat already downloaded
    lon, lat  = re.findall(r'df_(-?\d+\.\d+)_(-?\d+\.\d+)_specId_', os.path.basename(f))[0]
    with open(f'downloaded/siteInfo_{lon}_{lat}.xml', 'r') as file:
        FullCAM_soil = parse_soil_data(file.read())['clayFrac'].data.item()
    # Get SoilClay from SLGA at the lon/lat
    soilClay_pt = (
        soilClay_SLGA
        .sel(x=float(lon), y=float(lat), method='nearest')
        .data
        .item()
    )
    # Merge FullCAM and SLGA SoilClay data, then append to main dataframe
    soilClay_merged = pd.DataFrame({
        'soilClay_FullCAM': [FullCAM_soil],
        'soilClay_SLGA': [soilClay_pt],
        'x': [float(lon)],
        'y': [float(lat)],
    })
    data_compare = pd.concat([data_compare, soilClay_merged], ignore_index=True)
    

# Plot comparison
p9.options.figure_size = (6, 6)
p9.options.dpi = 150

fig = (
    p9.ggplot(data_compare)
    + p9.aes(x='soilClay_FullCAM', y='soilClay_SLGA')
    + p9.geom_point(alpha=0.3, size=0.5)
    + p9.geom_abline(slope=1, intercept=0, linetype='dashed', color='red')
    + p9.theme_bw()
    + p9.labs(
        title='Soil Clay Fraction Comparison (0-30cm)',
        x='Soil Clay Fraction FullCAM',
        y='Soil Clay Fraction SLGA'
    )
)

fig.save('data/processed/Compare_API_and_Assemble_Data_Simulations/Data_compare_SiteInfo_soilClay.svg', dpi=150)
