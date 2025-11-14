
import xarray as xr
import rioxarray as rio
import numpy as np

from tools.XML2NetCDF import get_carbon_data, get_siteinfo_data
from tools.cache_manager import get_existing_downloads
from joblib import Parallel, delayed
from tqdm.auto import tqdm
from affine import Affine



# Get variables
RES_factor = 10
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads()


# Get the RES coords
Aus_xr = rio.open_rasterio("data/lumap.tif").sel(band=1, drop=True).compute() >= -1 # >=-1 means all Australia continent
lon_lat = Aus_xr.to_dataframe(name='mask').reset_index()[['y', 'x', 'mask']].round({'x':2, 'y':2})
lon_lat['cell_idx'] = range(len(lon_lat))

Aus_cell = xr.DataArray(np.arange(Aus_xr.size).reshape(Aus_xr.shape), coords=Aus_xr.coords, dims=Aus_xr.dims)
Aus_cell_RES = Aus_cell.coarsen(x=RES_factor, y=RES_factor, boundary='trim').max()
Aus_cell_RES_df = Aus_cell_RES.to_dataframe(name='cell_idx').reset_index()['cell_idx']

RES_df = lon_lat.query('mask == True').loc[lon_lat['cell_idx'].isin(Aus_cell_RES_df)].reset_index(drop=True)
RES_coords = RES_df.set_index(['x', 'y']).index.tolist()


# Get the transform
all_lats = sorted(set([lat for lat, lon in RES_coords]))
all_lons = sorted(set([lon for lat, lon in RES_coords]))

cell_size_x = abs(all_lons[1] - all_lons[0])
cell_size_y = abs(all_lats[1] - all_lats[0])

# Get affine transform
lumap_xr = rio.open_rasterio('data/lumap.tif', masked=True)
trans = list(lumap_xr.rio.transform())
trans[2] = min(all_lons) - (cell_size_x / 2)
trans[5] = max(all_lats) + (cell_size_y / 2)
trans[0] = trans[0] * 5
trans[4] = trans[4] * 5
trans = Affine(*trans)



# ---------------------- Get SiteInfo data ------------------------
siteInfo_coords = set(existing_siteinfo).intersection(set(RES_coords))

sample_lon, sample_lat  = next(iter(siteInfo_coords))
sample_template = get_siteinfo_data(sample_lon, sample_lat) * np.nan
siteInfo_full = sample_template.squeeze(['y', 'x'], drop=True).expand_dims(y=all_lats, x=all_lons) * np.nan


# Parallel fetch data
def fetch_with_coords(lon, lat):
    try:
        data = get_siteinfo_data(lon, lat)
        return (lon, lat, data)
    except Exception as e:
        return (lon, lat, sample_template)
    



tasks = [
    delayed(fetch_with_coords)(lon, lat)
    for lon, lat in siteInfo_coords
]

for lon, lat, data in tqdm(Parallel(n_jobs=16, return_as='generator_unordered')(tasks), total=len(tasks)):
    siteInfo_full.loc[dict(y=lat, x=lon)] = data.squeeze(['y', 'x'], drop=True)
    
    

# Save to NetCDF
siteInfo_full.rio.write_crs("EPSG:4283", inplace=True)
siteInfo_full.rio.write_transform(trans, inplace=True)
siteInfo_full.to_netcdf('data/processed/siteinfo_RES.nc', encoding={var: {'zlib': True, 'complevel': 5} for var in siteInfo_full.data_vars})

# Save to GeoTIFFs
for var, xarry in siteInfo_full.data_vars.items():
    if len(xarry.dims) > 2:
        to_stack_dims = [dim for dim in xarry.dims if dim not in ['y', 'x']]
        xarry = xarry.stack(band=to_stack_dims).transpose('band', 'y', 'x').astype(np.float32)
    xarry.rio.to_raster(f'data/processed/{var}_RES_multiband.tif', compress='lzw')
    print(f"Saved {var} with shape {xarry.shape}")
    
fpiAvgLT = siteInfo_full['fpiAvgLT']
fpiAvgLT.rio.write_crs("EPSG:4283", inplace=True)
fpiAvgLT.rio.write_transform(trans, inplace=True)
fpiAvgLT.rio.to_raster('data/processed/fpiAvgLT_RES_multiband.tif', compress='lzw')
    




# ---------------------- Get CarbonStock data ------------------------
lon, lat = next(iter(coords_carbon))
carbon_template = get_carbon_data(lon, lat).squeeze(['y', 'x'], drop=True) * np.nan
carbon_siteInfo_full = carbon_template.expand_dims(y=all_lats, x=all_lons) * np.nan

# Parallel fetch data
def fetch_carbon_with_coords(lon, lat):
    try:
        data = get_carbon_data(lon, lat)
        return (lon, lat, data)
    except Exception as e:
        return (lon, lat, carbon_template)
    
tasks = [
    delayed(fetch_carbon_with_coords)(lon, lat)
    for lat, lon in coords_carbon
]

for lon, lat, data in tqdm(Parallel(n_jobs=8, return_as='generator_unordered')(tasks), total=len(tasks)):
    carbon_siteInfo_full.loc[dict(y=lat, x=lon)] = data.squeeze(['y', 'x'], drop=True)
    

get_carbon_data(lon, lat)
    

# Save to NetCDF
carbon_siteInfo_full.name = 'data'
carbon_siteInfo_full = carbon_siteInfo_full.astype(np.float32)
carbon_siteInfo_full.rio.write_crs("EPSG:4326", inplace=True)
carbon_siteInfo_full.rio.write_transform(trans, inplace=True)
carbon_siteInfo_full.to_netcdf('data/processed/carbonstock_RES.nc', encoding={'data': {'zlib': True, 'complevel': 5}})


# Save to GeoTIFFs
carbon_arr_stack = carbon_siteInfo_full.stack(band=['YEAR', 'VARIABLE']).transpose('band', 'y', 'x')
carbon_arr_stack.rio.to_raster(f'data/processed/carbonstock_RES_multiband.tif', compress='lzw')










