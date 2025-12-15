import numpy as np
import xarray as xr
import rioxarray as rio

from joblib import Parallel, delayed
from tqdm.auto import tqdm
from affine import Affine

from tools import get_downloading_coords
from tools.helpers.cache_manager import get_existing_downloads
from tools.XML2Data import (
    export_to_geotiff_with_band_names, 
    get_carbon_data, 
    get_siteinfo_data,
    get_species_data, 
)




# Get variables
RES_factor = 3
SPECIES_ID = 8          # Eucalyptus globulus
SPECIES_CAT = 'Block'   # Block or Belt; need to confirm with individual species
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads(SPECIES_ID, SPECIES_CAT)


# Get the RES coords
RES_df = get_downloading_coords(resfactor=RES_factor)
RES_coords = RES_df.set_index(['x', 'y']).index.tolist()


# Get the transform
all_lats = np.arange(max(RES_df['y']), min(RES_df['y']) - 0.001, -RES_factor * 0.01).astype(np.float32)
all_lons = np.arange(min(RES_df['x']), max(RES_df['x']) + 0.001, RES_factor * 0.01).astype(np.float32)
cell_size_x = abs(all_lons[1] - all_lons[0])
cell_size_y = abs(all_lats[1] - all_lats[0])

# Get affine transform
lumap_xr = rio.open_rasterio('data/lumap.tif', masked=True)
trans = list(lumap_xr.rio.transform())
trans[2] = min(all_lons) + (cell_size_x / 2)
trans[5] = max(all_lats) - (cell_size_y / 2)
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
    



# ---------------------- Get species data ------------------------
species_coords = set(existing_species).intersection(set(RES_coords))

sample_lon, sample_lat  = next(iter(species_coords))
species_template = get_species_data(sample_lon, sample_lat)  # Warm up cache
species_full = species_template.squeeze(['y', 'x'], drop=True).expand_dims(y=all_lats, x=all_lons) * np.nan


# Parallel fetch data
def fetch_species_with_coords(lon, lat):
    try:
        data = get_species_data(lon, lat)
        return (lon, lat, data)
    except Exception as e:
        print(f"Error fetching species data for ({lon}, {lat}): {e}")
        return (lon, lat, species_template)
    
tasks = [delayed(fetch_species_with_coords)(lon, lat) for lon, lat in species_coords]
for lon, lat, data in tqdm(Parallel(n_jobs=16, return_as='generator_unordered')(tasks), total=len(tasks)):
    species_full.loc[dict(y=lat, x=lon)] = data.squeeze(['y', 'x'], drop=True)
    
    
# Save to NetCDF
species_full.rio.write_crs("EPSG:4283", inplace=True)
species_full.rio.write_transform(trans, inplace=True)
species_full.to_netcdf(
    'data/processed/species_RES.nc', 
    encoding={var: {'zlib': True, 'complevel': 5} for var in species_full.data_vars}
)


# Save to GeoTIFFs
for var in species_full.data_vars:
    xarry = species_full[var]
    for TYF_Type in xarry['TYF_Type'].values:
        export_to_geotiff_with_band_names(
            xarry.sel(TYF_Type=TYF_Type, drop=True), 
            f'data/processed/species_{var}_{TYF_Type}_RES_{RES_factor}_multiband.tif',
            band_dim='YEAR'
        )





# ---------------------- Get CarbonStock data ------------------------
Carbon_coords = set(existing_dfs).intersection(set(RES_coords))

template_lon, template_lat = next(iter(Carbon_coords))
carbon_template = get_carbon_data(template_lon, template_lat, SPECIES_ID) * np.nan
carbon_full = carbon_template.squeeze(['y', 'x'], drop=True).expand_dims(y=all_lats, x=all_lons) * np.nan


# Parallel fetch data
def fetch_carbon_with_coords(lon, lat):
    try:
        data = get_carbon_data(lon, lat, SPECIES_ID)
        return (lon, lat, data)
    except Exception as e:
        print(f"Error fetching carbon data for ({lon}, {lat}): {e}")
        return (lon, lat, carbon_template)
    
tasks = [delayed(fetch_carbon_with_coords)(lon, lat) for lon, lat in Carbon_coords]
for lon, lat, data in tqdm(Parallel(n_jobs=16, return_as='generator_unordered')(tasks), total=len(tasks)):
    carbon_full.loc[dict(y=lat, x=lon)] = data.squeeze(['y', 'x'], drop=True)


# Save to NetCDF
carbon_full.name = 'data'
carbon_full = carbon_full.astype(np.float32)
carbon_full.rio.write_crs("EPSG:4283", inplace=True)
carbon_full.rio.write_transform(trans, inplace=True)
carbon_full.to_netcdf(
    f'data/processed/carbonstock_RES_{RES_factor}.nc', 
    encoding={'data': {'zlib': True, 'complevel': 5}}
)

# Save to GeoTIFFs
for var in carbon_full['VARIABLE'].values:
    xarry = carbon_full.sel(VARIABLE=var, drop=True)
    export_to_geotiff_with_band_names(
        xarry, 
        f'data/processed/carbonstock_{var}_RES_{RES_factor}_multiband.tif',
        band_dim='YEAR'
    )










