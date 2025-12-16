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
#         Transform TYR R data for Eucalyptus globulus  (specId = 8)               #
####################################################################################

# Match spatial resolution and extent to template
species_ds = xr.open_dataset('data/Species_TYF_R/specId_8_match_LUTO.nc').compute()
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
    f'data/Species_TYF_R/specId_8_match_LUTO.nc', 
    encoding={var: {'zlib': True, 'complevel': 5} for var in species_reprojected.data_vars}
)


for var in species_reprojected.data_vars:
    xarry = species_reprojected[var]
    for TYF_Type in xarry['TYF_Type'].values:
        export_to_geotiff_with_band_names(
            xarry.sel(TYF_Type=TYF_Type, drop=True), 
            f'data/Species_TYF_R/specId_8_{var}_{TYF_Type}.tif',
            band_dim='YEAR'
        )


####################################################################################
#         Transform TYR R data for Environmental plantings  (specId = 7)           #
####################################################################################

'''
The Tree Yield Formula (TYF) parameter for Environmental Plantings are not varied by changing locations. 
So we create dataset with constant TYF parameters based on the following values:

<TYFParameters count="4" idSP="7">
    <TYFCategory tTYFCat="Custom" tyf_G="10" tyf_r="1"/>
    <TYFCategory tTYFCat="BeltH" tyf_G="3.492" tyf_r="1.2"/>
    <TYFCategory tTYFCat="BeltL" tyf_G="4.533" tyf_r="1.2"/>
    <TYFCategory tTYFCat="BlockES" tyf_G="6.317" tyf_r="1.0"/>
    <TYFCategory tTYFCat="Water" tyf_G="5.724" tyf_r="1.2"/>
</TYFParameters>

'''

species_EP = xr.Dataset(
    {
        'BeltH': xr.DataArray([spatial_template * 3.492, spatial_template * 1.2], dims=['TYF_Type', 'y', 'x'], coords={'TYF_Type': ['tyf_G', 'tyf_r']}),
        'BeltL': xr.DataArray([spatial_template * 4.533, spatial_template * 1.2], dims=['TYF_Type', 'y', 'x'], coords={'TYF_Type': ['tyf_G', 'tyf_r']}),
        'BlockES': xr.DataArray([spatial_template * 6.317, spatial_template * 1.0], dims=['TYF_Type', 'y', 'x'], coords={'TYF_Type': ['tyf_G', 'tyf_r']}),
        'Water': xr.DataArray([spatial_template * 5.724, spatial_template * 1.2], dims=['TYF_Type', 'y', 'x'], coords={'TYF_Type': ['tyf_G', 'tyf_r']}),
    }
).assign_coords({'x': spatial_template['x'], 'y': spatial_template['y']})
          
# Save the reprojected dataset
species_EP.to_netcdf(
    f'data/Species_TYF_R/specId_7_match_LUTO.nc', 
    encoding={var: {'zlib': True, 'complevel': 5} for var in species_EP.data_vars}
)




####################################################################################
#         Transform TYR R data for Mallee eucalypt species  (specId = 23)          #
####################################################################################

'''
The Tree Yield Formula (TYF) parameter for Mallee eucalypt species are not varied by changing locations. 
So we create dataset with constant TYF parameters based on the following values:

<TYFParameters count="5" idSP="23">
    <TYFCategory tTYFCat="Custom" tyf_G="10" tyf_r="1"/>
    <TYFCategory tTYFCat="BeltH" tyf_G="3.492" tyf_r="1.2"/>
    <TYFCategory tTYFCat="BeltL" tyf_G="4.533" tyf_r="1.2"/>
    <TYFCategory tTYFCat="BlockES" tyf_G="6.317" tyf_r="1.0"/>
    <TYFCategory tTYFCat="BeltHW" tyf_G="3.492" tyf_r="1.2"/>
    <TYFCategory tTYFCat="BeltHN" tyf_G="2.288" tyf_r="1.608"/>
</TYFParameters>

'''

species_Mallee = xr.Dataset(
    {
        'BeltH': xr.DataArray([spatial_template * 3.492, spatial_template * 1.2], dims=['TYF_Type', 'y', 'x'], coords={'TYF_Type': ['tyf_G', 'tyf_r']}),
        'BeltL': xr.DataArray([spatial_template * 4.533, spatial_template * 1.2], dims=['TYF_Type', 'y', 'x'], coords={'TYF_Type': ['tyf_G', 'tyf_r']}),
        'BlockES': xr.DataArray([spatial_template * 6.317, spatial_template * 1.0], dims=['TYF_Type', 'y', 'x'], coords={'TYF_Type': ['tyf_G', 'tyf_r']}),
        'BeltHW': xr.DataArray([spatial_template * 3.492, spatial_template * 1.2], dims=['TYF_Type', 'y', 'x'], coords={'TYF_Type': ['tyf_G', 'tyf_r']}),
        'BeltHN': xr.DataArray([spatial_template * 2.288, spatial_template * 1.608], dims=['TYF_Type', 'y', 'x'], coords={'TYF_Type': ['tyf_G', 'tyf_r']}),
    }
).assign_coords({'x': spatial_template['x'], 'y': spatial_template['y']})

# Save the reprojected dataset
species_Mallee.to_netcdf(
    f'data/Species_TYF_R/specId_23_match_LUTO.nc', 
    encoding={var: {'zlib': True, 'complevel': 5} for var in species_Mallee.data_vars}
)
