
import xarray as xr
import rioxarray as rio
import numpy as np

from tools.XML2NetCDF import get_carbon_data, get_siteinfo_data
from tools.cache_manager import get_existing_downloads
from joblib import Parallel, delayed
from tqdm.auto import tqdm
from affine import Affine

# Get existing data
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads()

# Get the RES5 coords
Aus_xr = rio.open_rasterio("data/lumap.tif").sel(band=1, drop=True).compute() >= -1 # >=-1 means all Australia continent
lon_lat = Aus_xr.to_dataframe(name='mask').reset_index()[['y', 'x', 'mask']].round({'x':2, 'y':2})
lon_lat['cell_idx'] = range(len(lon_lat))

Aus_cell = xr.DataArray(np.arange(Aus_xr.size).reshape(Aus_xr.shape), coords=Aus_xr.coords, dims=Aus_xr.dims)
Aus_cell_RES5 = Aus_cell.coarsen(x=5, y=5, boundary='trim').max()
Aus_cell_RES5_df = Aus_cell_RES5.to_dataframe(name='cell_idx').reset_index()['cell_idx']

RES5_df = lon_lat.query('mask == True').loc[lon_lat['cell_idx'].isin(Aus_cell_RES5_df)].reset_index(drop=True)
RES5_coords = RES5_df.set_index(['y', 'x']).index.tolist()


# Get downloaded data points
coords_siteinfo = set(existing_siteinfo).intersection(set(RES5_coords))
coords_species = set(existing_species).intersection(set(RES5_coords))
coords_carbon = set(existing_dfs).intersection(set(RES5_coords))

# Get the transform
all_lats = sorted(set([lat for lat, lon in RES5_coords]))
all_lons = sorted(set([lon for lat, lon in RES5_coords]))

cell_size_x = abs(all_lons[1] - all_lons[0])
cell_size_y = abs(all_lats[1] - all_lats[0])

trans = Affine(
    cell_size_x,
    0.0,
    min(all_lons) - cell_size_x / 2,
    0.0,
    cell_size_y,
    min(all_lats) - cell_size_y / 2 
)




# ---------------------- Get SiteInfo data ------------------------
sample_lat, sample_lon = next(iter(coords_siteinfo))
sample_template = get_siteinfo_data(sample_lon, sample_lat).squeeze(['y', 'x'], drop=True) * np.nan
ds_full = sample_template.expand_dims(y=all_lats, x=all_lons) * np.nan


# Parallel fetch data
def fetch_with_coords(lon, lat):
    try:
        data = get_siteinfo_data(lon, lat)
        return (lon, lat, data)
    except Exception as e:
        return (lon, lat, sample_template)

tasks = [
    delayed(fetch_with_coords)(lon, lat)
    for lat, lon in coords_siteinfo
]

for lon, lat, data in tqdm(Parallel(n_jobs=8, return_as='generator_unordered')(tasks), total=len(tasks)):
    ds_full.loc[dict(y=lat, x=lon)] = data.squeeze(['y', 'x'], drop=True)


# Save to NetCDF
ds_full.rio.write_crs("EPSG:4326", inplace=True)
ds_full.rio.write_transform(trans, inplace=True)

ds_full.to_netcdf('data/processed/siteinfo_RES5.nc', encoding={var: {'zlib': True, 'complevel': 5} for var in ds_full.data_vars})



# Save to GeoTIFFs
for var, xarry in ds_full.data_vars.items():
    to_stack_dims = [dim for dim in xarry.dims if dim not in ['y', 'x']]
    arr_stack = xarry.stack(band=to_stack_dims).transpose('band', 'y', 'x').astype(np.float32)
    arr_stack.rio.to_raster(f'data/processed/{var}_RES5_multiband.tif', compress='lzw')
    print(f"Saved {var} with shape {arr_stack.shape}")



# ---------------------- Get CarbonStock data ------------------------
lon, lat = next(iter(coords_carbon))
carbon_template = get_carbon_data(lon, lat).squeeze(['y', 'x'], drop=True) * np.nan
carbon_ds_full = carbon_template.expand_dims(y=all_lats, x=all_lons) * np.nan

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
    carbon_ds_full.loc[dict(y=lat, x=lon)] = data.squeeze(['y', 'x'], drop=True)
    

get_carbon_data(lon, lat)
    

# Save to NetCDF
carbon_ds_full.name = 'data'
carbon_ds_full = carbon_ds_full.astype(np.float32)
carbon_ds_full.rio.write_crs("EPSG:4326", inplace=True)
carbon_ds_full.rio.write_transform(trans, inplace=True)
carbon_ds_full.to_netcdf('downloaded/carbonstock_RES5.nc', encoding={'data': {'zlib': True, 'complevel': 5}})


# Save to GeoTIFFs
carbon_arr_stack = carbon_ds_full.stack(band=['YEAR', 'VARIABLE']).transpose('band', 'y', 'x')
carbon_arr_stack.rio.to_raster(f'data/processed/carbonstock_RES5_multiband.tif', compress='lzw')










