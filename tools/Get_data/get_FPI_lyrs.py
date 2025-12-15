import os, re
import rioxarray as rio
import numpy as np
import xarray as xr
import plotnine as p9

from glob import glob
from tqdm.auto import tqdm
from joblib import Parallel, delayed
from rioxarray import merge as rio_merge

from tools import get_downloading_coords
from tools.helpers.cache_manager import get_existing_downloads


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
FPI_restfull = (
    xr.open_dataset('data/processed/siteinfo_RES.nc')['forestProdIx']
    .compute()
    .sel(x=res_coords_x, y=res_coords_y)
)

FPI_SoilLandscape = (
    xr.open_dataset('data/FPI_lys/FPI_lyrs.nc')['data']
    .compute()
    .sel(x=res_coords_x, y=res_coords_y, method='nearest')
    .assign_coords(x=res_coords_x, y=res_coords_y)
)

plot_data = (
    xr.concat([FPI_restfull, FPI_SoilLandscape], dim='source', join ='inner')
    .assign_coords(source=['RESTful', 'FPI_SoilLandscape'])
    .to_dataframe()
    .reset_index()
    .round({'x':3, 'y':3})
    .pivot(index=['year','x', 'y'], columns=['source'], values='forestProdIx')
    .reset_index()
    .dropna()
)

fig = (
    p9.ggplot()
    + p9.aes(x=plot_data[::100]['RESTful'], y=plot_data[::100]['FPI_SoilLandscape'])
    + p9.geom_point(alpha=0.3, size=0.5)
    + p9.geom_abline(slope=1, intercept=0, linetype='dashed', color='red')
    + p9.theme_bw()
    + p9.labs(
        title='Forest Productivity Index Comparison',
        x='FPI FullCAM',
        y='FPI Downloaded'
    )
)
