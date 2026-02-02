
import io
import os
import re
import zipfile
import pandas as pd
import rioxarray as rio
import xarray as xr
import numpy as np
import plotnine as p9

from glob import glob
from tqdm.auto import tqdm

from tools import get_downloading_coords
from tools.XML2Data import parse_site_data
from tools.helpers.cache_manager import get_existing_downloads




# Get resfactored coords for downloading
SPECIES_ID = 8          # Eucalyptus globulus
SPECIES_CAT = 'Block'   # Block or Belt; need to confirm with individual species
scrap_coords = get_downloading_coords(resfactor=10).set_index(['x', 'y']).index.tolist()
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads(SPECIES_ID, SPECIES_CAT)

res_coords = set(existing_siteinfo).intersection(set(scrap_coords))
res_coords_x = xr.DataArray([coord[0] for coord in res_coords], dims=['cell'])
res_coords_y = xr.DataArray([coord[1] for coord in res_coords], dims=['cell'])



# Get data
with zipfile.ZipFile("data/maxAbgMF/Site potential and FPI version 2_0/New_M_2019.zip", 'r') as zip_ref:
    maxAbgMF_data = xr.open_dataarray(
        io.BytesIO(zip_ref.read('New_M_2019.tif')), 
        engine='rasterio'
    ).sel(band=1, drop=True)

maxAbgMF_data.name = 'data'
maxAbgMF_data.to_netcdf('data/maxAbgMF/maxAbgMF.nc', encoding={'data': {'zlib': True, 'complevel': 5}})




# -------------------------------- Plot comparison -------------------------------- 

# Load  maxAbgMF from DCCEEW
maxAbgMF_DCCEEW = xr.load_dataset('data/maxAbgMF/maxAbgMF.nc')['data']


# Get downloaded carbon data CSV files; does not matter which species because SiteInfo is the same for all species
FullCAM_retrive_dir ='data/processed/Compare_API_and_Assemble_Data_Simulations/download_csv'
csv_files = [i for i in glob(f'{FullCAM_retrive_dir}/*.csv') if f'specId_8_specCat_Block' in i]

data_compare = pd.DataFrame()
for f in tqdm(csv_files):
    # Get Cache data
    #   The SiteInfo data for the FullCAM carbon df at lon/lat already downloaded
    lon, lat  = re.findall(r'df_(-?\d+\.\d+)_(-?\d+\.\d+)_specId_', os.path.basename(f))[0]
    with open(f'downloaded/siteInfo_{lon}_{lat}.xml', 'r') as file:
        FullCAM_siteinfo = parse_site_data(file.read())['maxAbgMF']
        FullCAM_siteinfo = FullCAM_siteinfo.data.item()
    # Get maxAbgMF from DCCEEW at the lon/lat
    maxAbgMF_pt = maxAbgMF_DCCEEW.sel(x=float(lon), y=float(lat), method='nearest').data.item()
    # Merge FullCAM and DCCEEW maxAbgMF data, then append to main dataframe
    maxAbgMF_merged = pd.DataFrame({
        'maxAbgMF_FullCAM': [FullCAM_siteinfo],
        'maxAbgMF_DCCEEW': [maxAbgMF_pt],
        'x': [float(lon)],
        'y': [float(lat)],
    })
    data_compare = pd.concat([data_compare, maxAbgMF_merged], ignore_index=True)
    

# Plot comparison
p9.options.figure_size = (6, 6)
p9.options.dpi = 150

fig = (
    p9.ggplot(data_compare)
    + p9.aes(x='maxAbgMF_FullCAM', y='maxAbgMF_DCCEEW')
    + p9.geom_point(alpha=0.3, size=0.5)
    + p9.geom_abline(slope=1, intercept=0, linetype='dashed', color='red')
    + p9.theme_bw()
    + p9.labs(
        title='Maximum Above Ground Mass Factor Comparison',
        x='maxAbgMF FullCAM',
        y='maxAbgMF DCCEEW'
    )
)

fig.save('data/processed/Compare_API_and_Assemble_Data_Simulations/Data_compare_SiteInfo_maxAbgMF.svg', dpi=150)
