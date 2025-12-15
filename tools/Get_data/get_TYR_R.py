import numpy as np
import xarray as xr
import rioxarray as rxr

from rasterio.enums import Resampling
from scipy.ndimage import distance_transform_edt
from tools.FullCAM2020_to_NetCDF import export_to_geotiff_with_band_names


# Read spatial template
spatial_template = rxr.open_rasterio('data/lumap.tif', masked=True).sel(band=1, drop=True).compute()
spatial_template = xr.where(spatial_template.isnull(), np.nan, 1)


# Function to fill NaN values using nearest neighbor interpolation
def fill_nan_nearest(data_2d:xr.DataArray) -> np.ndarray:
    indices = distance_transform_edt(data_2d.isnull(), return_distances=False, return_indices=True)
    data_2d.values = data_2d.values[tuple(indices)]
    return data_2d



####################################################################################
#         Transform TYR R data fro Eucalyptus globulus  (specId = 8)               #
####################################################################################

specId = 8

# Match spatial resolution and extent to template
species_ds = xr.open_dataset('data/processed/species_RES.nc').compute()
species_ds = species_ds.rio.write_crs("EPSG:4326")
species_ds = species_ds.rio.set_spatial_dims(x_dim='x', y_dim='y')

# Collect reprojected arrays
reprojected_vars = {}

for var in species_ds.data_vars:
    if var == 'spatial_ref':
        continue
    ds = species_ds[var]
    tyf_arrays = []
    for TYF_Type in ds['TYF_Type'].values:
        subset = ds.sel(TYF_Type=TYF_Type)
        arr = subset.rio.reproject_match(spatial_template, nodata=np.nan, resampling=Resampling.bilinear).compute()
        arr = fill_nan_nearest(arr) * spatial_template
        tyf_arrays.append(arr)

    # Concat along TYF_Type dimension
    reprojected_vars[var] = xr.concat(tyf_arrays, dim='TYF_Type').assign_coords(TYF_Type=ds['TYF_Type'].values)

# Create the final dataset
species_reprojected = xr.Dataset(reprojected_vars)
species_reprojected = species_reprojected.rio.write_crs("EPSG:4326")

# Save the reprojected dataset
species_reprojected.to_netcdf(
    f'data/Species_TYF_R/specId_{specId}_match_LUTO.nc', 
    encoding={var: {'zlib': True, 'complevel': 5} for var in species_reprojected.data_vars}
)


for var in species_reprojected.data_vars:
    xarry = species_reprojected[var]
    for TYF_Type in xarry['TYF_Type'].values:
        export_to_geotiff_with_band_names(
            xarry.sel(TYF_Type=TYF_Type, drop=True), 
            f'data/Species_TYF_R/specId_{specId}_{var}_{TYF_Type}.tif',
            band_dim='YEAR'
        )





