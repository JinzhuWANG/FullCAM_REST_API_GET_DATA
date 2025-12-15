import numpy as np
import xarray as xr
import rioxarray as rio

from scipy.ndimage import distance_transform_edt
from tqdm.auto import tqdm
from joblib import Parallel, delayed


# Get the spatial template
template_2d_xr = rio.open_rasterio("data/lumap.tif", chunks={}).sel(band=1, drop=True).drop_vars('spatial_ref').compute()
template_2d_xr = xr.where(template_2d_xr >= -1, 1, np.nan).astype('float32')


# Function to fill NaN values using nearest neighbor interpolation
def fill_nan_nearest(data_2d:xr.DataArray) -> np.ndarray:
    indices = distance_transform_edt(data_2d.isnull(), return_distances=False, return_indices=True)
    data_2d.values = data_2d.values[tuple(indices)]
    return data_2d


############################################################################
#                Assemble siteInfo data to match LUTO                      #
############################################################################ 


# Read in cached siteInfo data
siteInfo_ANUClim = xr.open_dataset("data/ANUClim/processed/ANUClim_to_FullCAM.nc")
siteInfo_forestProdIx = xr.open_dataset("data/FPI_lys/FPI_lyrs.nc")['data'].rename('forestProdIx')
siteInfo_maxAbgMF_fpiAvgLT = xr.open_dataset("data/processed/BB_PLO_OneKm/siteinfo_PLO_RES.nc")[['maxAbgMF','fpiAvgLT']]


# Initialize full siteInfo dataset with NaNs
siteInfo_fill = xr.Dataset({
    'openPanEvap': template_2d_xr.expand_dims(siteInfo_ANUClim[['year','month']].coords),
    'rainfall': template_2d_xr.expand_dims(siteInfo_ANUClim[['year','month']].coords),
    'avgAirTemp': template_2d_xr.expand_dims(siteInfo_ANUClim[['year','month']].coords),
    'forestProdIx': template_2d_xr.expand_dims(siteInfo_forestProdIx['year'].coords),
    'maxAbgMF': template_2d_xr,
    'fpiAvgLT': template_2d_xr,
}) * np.nan



# Fill openPanEvap, rainfall, avgAirTemp
tasks = []
def _get_climate_arr(var:str, yr:int, mon:int):
    arr = siteInfo_ANUClim[var].sel(year=yr, month=mon, drop=True).compute()
    arr = fill_nan_nearest(arr).reindex_like(template_2d_xr, method='nearest') * template_2d_xr
    return var, yr, mon, arr
    
for yr, mon in tqdm(siteInfo_ANUClim[['year','month']].to_dataframe().index):
    tasks.append(delayed(_get_climate_arr)('openPanEvap', yr, mon))
    tasks.append(delayed(_get_climate_arr)('rainfall', yr, mon))
    tasks.append(delayed(_get_climate_arr)('avgAirTemp', yr, mon))
    
for var, yr, mon, arr in tqdm(Parallel(n_jobs=20, return_as='generator_unordered')(tasks), total=len(tasks)):
    siteInfo_fill[var].loc[dict(year=yr, month=mon)] = arr
    
    
    
# Fill forestProdIx
tasks = []
def _get_fpi_arr(yr:int):
    arr = siteInfo_forestProdIx.sel(year=yr, drop=True).compute()
    arr = fill_nan_nearest(arr).reindex_like(template_2d_xr, method='nearest') * template_2d_xr
    return 'forestProdIx', yr, arr

for yr in tqdm(siteInfo_forestProdIx['year'].to_dataframe().index):
    tasks.append(delayed(_get_fpi_arr)(yr))
    
for var, yr, arr in tqdm(Parallel(n_jobs=20, return_as='generator_unordered')(tasks), total=len(tasks)):
    siteInfo_fill[var].loc[dict(year=yr)] = arr



# Fill maxAbgMF and fpiAvgLT
siteInfo_fill['maxAbgMF'] = fill_nan_nearest(siteInfo_maxAbgMF_fpiAvgLT['maxAbgMF']).reindex_like(template_2d_xr, method='nearest') * template_2d_xr
siteInfo_fill['fpiAvgLT'] = fill_nan_nearest(siteInfo_maxAbgMF_fpiAvgLT['fpiAvgLT']).reindex_like(template_2d_xr, method='nearest') * template_2d_xr
  

############################################################################
#                   Assemble Soil data to match LUTO                       #
############################################################################ 


# Read in soil data
#   Coarsen the 90m clayFrac to 1km
soil_clayfrac = ( 
    rio.open_rasterio("data/Soil_landscape_AUS/ClayContent/clayFrac_00_30cm.tif")
    .sel(band=1, drop=True)
    .coarsen(x=11, y=11, boundary='trim') # 1000m // 90m = 11
    .mean()
    .drop_vars('spatial_ref')
)

soil_init = (
    xr.open_dataset("data/processed/BB_PLO_OneKm/soilInit_PLO_RES.nc")
    .isel(band=range(0,7))
    .sel(band=['rpmaCMInitF','humsCMInitF','inrtCMInitF','TSMDInitF'])
    .compute()
    .drop_vars('spatial_ref')
)


# Fill clayFrac to match LUTO
siteInfo_fill['clayFrac'] = fill_nan_nearest(soil_clayfrac).reindex_like(template_2d_xr, method='nearest') * template_2d_xr

# Fill soil init variables
for band in ['rpmaCMInitF','humsCMInitF','inrtCMInitF','TSMDInitF']:
    arr = soil_init.sel(band=band, drop=True)['data']
    arr = fill_nan_nearest(arr).reindex_like(template_2d_xr, method='nearest') * template_2d_xr
    siteInfo_fill[band] = arr
    
    
############################################################################
#                  Save assembled data to file                             #
############################################################################

# Build encoding with chunking: x,y = 256, other dims = full size
encoding = {}
for var in siteInfo_fill.data_vars:
    dims = siteInfo_fill[var].dims
    chunks = []
    for dim in dims:
        if dim in ('x', 'y'):
            chunks.append(256)
        else:
            chunks.append(siteInfo_fill.sizes[dim])  # Full size for other dims
    encoding[var] = {'zlib': True, 'complevel': 4, 'chunksizes': tuple(chunks)}
    
    
# Save the filled siteInfo dataset
siteInfo_fill.to_netcdf(
    "data/data_assembled/siteinfo_cache.nc",
    encoding=encoding
)
