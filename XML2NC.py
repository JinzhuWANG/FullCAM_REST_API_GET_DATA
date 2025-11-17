import numpy as np
import xarray as xr
import rioxarray as rio

from tools.cache_manager import get_existing_downloads
from joblib import Parallel, delayed
from tqdm.auto import tqdm
from affine import Affine
from tools.XML2Data import (
    export_to_geotiff_with_band_names, 
    get_carbon_data, 
    get_siteinfo_data, 
    get_soilbase_data,
    get_soilInit_data
)





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
all_lats = np.arange(max(RES_df['y']), min(RES_df['y']) - 0.001, -RES_factor * 0.01).astype(np.float32)
all_lons = np.arange(min(RES_df['x']), max(RES_df['x']) + 0.001, RES_factor * 0.01).astype(np.float32)

cell_size_x = abs(all_lons[1] - all_lons[0])
cell_size_y = abs(all_lats[1] - all_lats[0])

# Get affine transform
lumap_xr = rio.open_rasterio('data/lumap.tif', masked=True)
trans = list(lumap_xr.rio.transform())
trans[2] = min(all_lons) - (cell_size_x / 2)
trans[5] = max(all_lats) + (cell_size_y / 2)
trans[0] = trans[0] * RES_factor
trans[4] = trans[4] * RES_factor
trans = Affine(*trans)



# ---------------------- Get SiteInfo data ------------------------
siteInfo_coords = set(existing_siteinfo).intersection(set(RES_coords))

sample_lon, sample_lat  = next(iter(siteInfo_coords))
sample_template = get_siteinfo_data(sample_lon, sample_lat) * np.nan
siteInfo_full = sample_template.squeeze(['y', 'x'], drop=True).expand_dims(y=all_lats, x=all_lons) * np.nan
siteInfo_full = siteInfo_full.astype(np.float32)


# Parallel fetch data
def fetch_with_coords(lon, lat):
    try:
        data = get_siteinfo_data(lon, lat)
        return (lon, lat, data)
    except Exception as e:
        return (lon, lat, sample_template)
    
tasks = [delayed(fetch_with_coords)(lon, lat) for lon, lat in siteInfo_coords]
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
        xarry = xarry.stack(band=to_stack_dims).astype(np.float32)
    export_to_geotiff_with_band_names(xarry, f'data/processed/siteInfo_{var}_RES_multiband.tif')
    


# ---------------------- Get SoilBase data ------------------------
sample_lon, sample_lat  = next(iter(siteInfo_coords))
sample_template_forest, sample_template_agriculture, sample_template_soilother = get_soilbase_data(sample_lon, sample_lat).values()

sample_template_forest*= np.nan
sample_template_agriculture *= np.nan
sample_template_soilother *= np.nan

soilbase_full_forest = sample_template_forest.squeeze(['y', 'x'], drop=True).expand_dims(y=all_lats, x=all_lons) * np.nan
soilbase_full_agriculture = sample_template_agriculture.squeeze(['y', 'x'], drop=True).expand_dims(y=all_lats, x=all_lons) * np.nan
soilbase_full_soilother = sample_template_soilother.squeeze(['y', 'x'], drop=True).expand_dims(y=all_lats, x=all_lons) * np.nan

# Parallel fetch data
def fetch_soil_with_coords(lon, lat):
    try:
        data_forest, data_agriculture, data_soilother = get_soilbase_data(lon, lat).values()
        return (lon, lat, data_forest, data_agriculture, data_soilother)
    except Exception as e:
        return (lon, lat, sample_template_forest, sample_template_agriculture, sample_template_soilother)
    
    
tasks = [delayed(fetch_soil_with_coords)(lon, lat) for lon, lat in siteInfo_coords]
for lon, lat, data_forest, data_agriculture, data_soilother in tqdm(Parallel(n_jobs=16, return_as='generator_unordered')(tasks), total=len(tasks)):
    soilbase_full_forest.loc[dict(y=lat, x=lon)] = data_forest.squeeze(['y', 'x'], drop=True)
    soilbase_full_agriculture.loc[dict(y=lat, x=lon)] = data_agriculture.squeeze(['y', 'x'], drop=True)
    soilbase_full_soilother.loc[dict(y=lat, x=lon)] = data_soilother.squeeze(['y', 'x'], drop=True)
    
# Save to NetCDF
soilbase_full_forest.name = 'data'
soilbase_full_forest.rio.write_crs("EPSG:4283", inplace=True)
soilbase_full_forest.rio.write_transform(trans, inplace=True)
soilbase_full_forest.to_netcdf('data/processed/soilbase_forest_RES.nc')

soilbase_full_agriculture.name = 'data'
soilbase_full_agriculture.rio.write_crs("EPSG:4283", inplace=True)
soilbase_full_agriculture.rio.write_transform(trans, inplace=True)
soilbase_full_agriculture.to_netcdf('data/processed/soilbase_agriculture_RES.nc')

soilbase_full_soilother.name = 'data'
soilbase_full_soilother.rio.write_crs("EPSG:4283", inplace=True)
soilbase_full_soilother.rio.write_transform(trans, inplace=True)
soilbase_full_soilother.to_netcdf('data/processed/soilbase_soilother_RES.nc')

# Save to GeoTIFFs
export_to_geotiff_with_band_names(soilbase_full_soilother, f'data/processed/soilbase_soilother_RES_multiband.tif')
export_to_geotiff_with_band_names(soilbase_full_agriculture, f'data/processed/soilbase_agriculture_RES_multiband.tif')
export_to_geotiff_with_band_names(soilbase_full_forest, f'data/processed/soilbase_forest_RES_multiband.tif')



# ---------------------- Get InitSoil data ------------------------
sample_lon, sample_lat  = next(iter(siteInfo_coords))

sample_soilInit = get_soilInit_data(sample_lon, sample_lat) * np.nan
soilInit_full = sample_soilInit.squeeze(['y', 'x'], drop=True).expand_dims(y=all_lats, x=all_lons) * np.nan

# Parallel fetch data
def fetch_soilInit_with_coords(lon, lat):
    try:
        data = get_soilInit_data(lon, lat)
        return (lon, lat, data)
    except Exception as e:
        return (lon, lat, sample_soilInit)
    
tasks = [delayed(fetch_soilInit_with_coords)(lon, lat) for lon, lat in siteInfo_coords]
for lon, lat, data in tqdm(Parallel(n_jobs=16, return_as='generator_unordered')(tasks), total=len(tasks)):
    soilInit_full.loc[dict(y=lat, x=lon)] = data.squeeze(['y', 'x'], drop=True)
    
# Save to NetCDF
soilInit_full.name = 'data'
soilInit_full.rio.write_crs("EPSG:4283", inplace=True)
soilInit_full.rio.write_transform(trans, inplace=True)
soilInit_full.to_netcdf('data/processed/soilInit_RES.nc', encoding={'data': {'zlib': True, 'complevel': 5} })

# Save to GeoTIFFs
export_to_geotiff_with_band_names(soilInit_full, f'data/processed/soilInit_RES_multiband.tif')



# ---------------------- Get CarbonStock data ------------------------
Carbon_coords = set(existing_dfs).intersection(set(RES_coords))

template_lon, template_lat = next(iter(Carbon_coords))
carbon_template = get_carbon_data(template_lon, template_lat) * np.nan
carbon_full = carbon_template.squeeze(['y', 'x'], drop=True).expand_dims(y=all_lats, x=all_lons) * np.nan


# Parallel fetch data
def fetch_carbon_with_coords(lon, lat):
    try:
        data = get_carbon_data(lon, lat)
        return (lon, lat, data)
    except Exception as e:
        print(f"Error fetching carbon data for ({lon}, {lat}): {e}")
        return (lon, lat, carbon_template)
    
tasks = [delayed(fetch_carbon_with_coords)(lon, lat) for lon, lat in Carbon_coords]
for lon, lat, data in tqdm(Parallel(n_jobs=8, return_as='generator_unordered')(tasks), total=len(tasks)):
    carbon_full.loc[dict(y=lat, x=lon)] = data.squeeze(['y', 'x'], drop=True)


# Save to NetCDF
carbon_full.name = 'data'
carbon_full = carbon_full.astype(np.float32)
carbon_full.rio.write_crs("EPSG:4326", inplace=True)
carbon_full.rio.write_transform(trans, inplace=True)
carbon_full.to_netcdf('data/processed/carbonstock_RES.nc', encoding={'data': {'zlib': True, 'complevel': 5}})

# Save to GeoTIFFs
for var in carbon_full['VARIABLE'].values:
    xarry = carbon_full.sel(VARIABLE=var, drop=True)
    export_to_geotiff_with_band_names(xarry, f'data/processed/carbonstock_{var}_RES_multiband.tif', band_dim='YEAR')










