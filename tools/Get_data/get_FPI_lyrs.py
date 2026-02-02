import os, re
import rioxarray as rio
import numpy as np
import pandas as pd
import xarray as xr
import plotnine as p9

from glob import glob
from tqdm.auto import tqdm
from joblib import Parallel, delayed
from rioxarray import merge as rio_merge

from tools import get_downloading_coords
from tools.helpers.cache_manager import get_existing_downloads
from tools.XML2Data import parse_site_data


# Config
RES_factor = 10
SPECIES_ID = 8          # Eucalyptus globulus
SPECIES_CAT = 'Block'   # Block or Belt; need to confirm with individual species

# Get resfactored coords
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads(SPECIES_ID, SPECIES_CAT)

RES_df = get_downloading_coords(resfactor=10)
RES_coords = RES_df.set_index(['x', 'y']).index.tolist()

res_coords = set(existing_siteinfo).intersection(set(RES_coords))
res_coords_x = xr.DataArray([coord[0] for coord in res_coords], dims=['cell'])
res_coords_y = xr.DataArray([coord[1] for coord in res_coords], dims=['cell'])


# Get FPR shads
def load_tif_year(tif, year):
    return year, rio.open_rasterio(tif, masked=True).sel(band=1, drop=True).compute()

def merge_arrays(arrays, year):
    """Merge a list of xarray DataArrays into a single DataArray by stacking them along a new dimension."""
    return year, rio_merge.merge_arrays(arrays)


# Load FPI tiffs
tasks = []
for dir in glob('data//FPI_lys/FPI_tiff/*fpi_7022'):
    for tif in glob(os.path.join(dir, '*.tif')):
        year = re.search(r'(\d{4})_001.tif', tif).group(1)
        tasks.append(delayed(load_tif_year)(tif, year))

FPI_lyrs = {}
for year, data in tqdm(Parallel(n_jobs=16, return_as='generator_unordered')(tasks), total=len(tasks)):
    if year not in FPI_lyrs:
        FPI_lyrs[year] = [data]
    else:
        FPI_lyrs[year].append(data)
        
# Merge FPI layers per year
tasks = []
for year in FPI_lyrs:
    tasks.append(delayed(merge_arrays)(FPI_lyrs[year], year))
    
FPI_lyrs_merged = {}
for year, data in tqdm(Parallel(n_jobs=8, return_as='generator_unordered')(tasks), total=len(tasks)):
    FPI_lyrs_merged[year] = data


# Merge all years into a single xarray DataArray; Save to NetCDF
FPI_all_years = xr.concat([FPI_lyrs_merged[year].expand_dims(year=[int(year)]) for year in sorted(FPI_lyrs_merged.keys())], dim='year')
FPI_all_years.name = 'data'  
FPI_all_years.to_netcdf('data/FPI_lys/FPI_lyrs.nc', encoding={'data': {'zlib': True, 'complevel': 5}})



# ------------------ Plot RESTful vs SoilLandscape Clay Comparison ------------------

# Get FPI data from DCCEEW 
FPI_DCCEEW = xr.load_dataset('data/FPI_lys/FPI_lyrs.nc')['data']


# Get downloaded carbon data CSV files; does not matter which species because SiteInfo is the same for all species
FullCAM_retrive_dir ='data/processed/Compare_API_and_Assemble_Data_Simulations/download_csv'
csv_files = [i for i in glob(f'{FullCAM_retrive_dir}/*.csv') if f'specId_8_specCat_Block' in i]

data_compare = pd.DataFrame()
for f in tqdm(csv_files):
    # Get Cache data
    #   The SiteInfo data for the FullCAM carbon df at lon/lat already downloaded
    lon, lat  = re.findall(r'df_(-?\d+\.\d+)_(-?\d+\.\d+)_specId_', os.path.basename(f))[0]
    with open(f'downloaded/siteInfo_{lon}_{lat}.xml', 'r') as file:
        FullCAM_siteinfo = parse_site_data(file.read())['forestProdIx']
        FullCAM_siteinfo = FullCAM_siteinfo.to_dataframe().reset_index()
        FullCAM_siteinfo[['x', 'y']] = float(lon), float(lat)
    # Get FPI from DCCEEW at the lon/lat
    FPI_pt = (
        FPI_DCCEEW
        .sel(x=float(lon), y=float(lat), method='nearest')
        .to_dataframe()
        .reset_index()
        .rename(columns={'data':'forestProdIx'})
    )
    FPI_pt[['x', 'y']] = float(lon), float(lat)
    # Merge FullCAM and DCCEEW FPI data, then append to main dataframe
    FPI_merged = pd.merge(
        FullCAM_siteinfo,
        FPI_pt,
        on=['year', 'x', 'y'],
        suffixes=('_FullCAM', '_DCCEEW')
    )
    data_compare = pd.concat([data_compare, FPI_merged], ignore_index=True)
    


# Plot comparison
p9.options.figure_size = (6, 6)
p9.options.dpi = 150

fig = (
    p9.ggplot(data_compare.sample(2000))
    + p9.aes(x='forestProdIx_FullCAM', y='forestProdIx_DCCEEW')
    + p9.geom_point(alpha=0.3, size=0.5)
    + p9.geom_abline(slope=1, intercept=0, linetype='dashed', color='red')
    + p9.theme_bw()
    + p9.labs(
        title='Forest Productivity Index Comparison',
        x='FPI FullCAM',
        y='FPI DCCEEW'
    )
)

fig.save('data/processed/Compare_API_and_Assemble_Data_Simulations/Data_compare_SiteInfo_FPI.svg', dpi=150)
