
import re
import numpy as np
import rioxarray as rio
import pandas as pd
import xarray as xr
import rioxarray as rxr
import plotnine as p9

from glob import glob
from tqdm.auto import tqdm
from joblib import Parallel, delayed
from affine import Affine

from rasterio.enums import Resampling
from scipy.ndimage import distance_transform_edt
from tools.FullCAM2020_to_NetCDF import export_to_geotiff_with_band_names
from tools.XML2Data import get_species_data, parse_species_data

from tools.helpers.cache_manager import get_existing_downloads
from tools import get_downloading_coords, get_plot_simulation, get_species


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


# ----------------------------- Prepare data for downloading -------------------------------------
RES_factor = 3             # Resolution factor; 1 = 1km, 2 = 2km, etc.
SPECIES_ID = 8             # Refer to `get_plot_simulation` docstring for species ID mapping
SPECIES_CAT = 'Belt'       # Refer individual species in the web API to see specific category; such as 'Block' or 'Belt'

# Get resfactored coords for downloading
scrap_coords = get_downloading_coords(resfactor=RES_factor, include_region='ALL')
RES_factor_coords = scrap_coords.set_index(['x', 'y']).index.tolist()


# Load existing downloaded files from cache
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads(SPECIES_ID, SPECIES_CAT)
existing_dfs_set = set((x, y) for x, y in existing_species)


# Filter coords using vectorized pandas operations
coords_tuples = scrap_coords[['x', 'y']].apply(tuple, axis=1)
mask_coords = ~coords_tuples.isin(existing_dfs_set)
to_request_coords = list(zip(scrap_coords.loc[mask_coords, 'x'], scrap_coords.loc[mask_coords, 'y']))



# Prepare download tasks
tasks = [
    delayed(get_species)(lon, lat, SPECIES_ID)
    for lon, lat in to_request_coords
]

for _ in tqdm(Parallel(n_jobs=32, return_as='generator_unordered', backend='threading')(tasks), total=len(tasks)):
    pass


# ----------------------------- Process downloaded data and save to NetCDF and GeoTIFF -------------------------------------

# Get the transform
all_lats = np.arange(max(scrap_coords['y']), min(scrap_coords['y']) - 0.001, -RES_factor * 0.01).astype(np.float32)
all_lons = np.arange(min(scrap_coords['x']), max(scrap_coords['x']) + 0.001, RES_factor * 0.01).astype(np.float32)
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

# Get downloaded species data; 
#   using the same coordinates as carbon data because they are downloaded together
species_coords = set(existing_species).intersection(set(RES_factor_coords))

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
for lon, lat, data in tqdm(Parallel(n_jobs=32, return_as='generator_unordered')(tasks), total=len(tasks)):
    species_full.loc[dict(y=lat, x=lon)] = data.squeeze(['y', 'x'], drop=True)
    
    
# Save to NetCDF
species_full.rio.write_crs("EPSG:4283", inplace=True)
species_full.rio.write_transform(trans, inplace=True)
species_full.to_netcdf(
    'data/processed/20251228_RES3_Species/species_RES.nc', 
    encoding={var: {'zlib': True, 'complevel': 5} for var in species_full.data_vars}
)


# Save to GeoTIFFs
for var in species_full.data_vars:
    xarry = species_full[var]
    for TYF_Type in xarry['TYF_Type'].values:
        export_to_geotiff_with_band_names(
            xarry.sel(TYF_Type=TYF_Type, drop=True), 
            f'data/processed/20251228_RES3_Species/species_{var}_{TYF_Type}_RES_{RES_factor}_multiband.tif',
            band_dim='YEAR'
        )


# ----------------------------- Convert to GEOTIFF -------------------------------------

# Match spatial resolution and extent to template
species_ds = xr.open_dataset('data/processed/20251228_RES3_Species/species_RES.nc').compute()
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
        arr = subset.rio.reproject_match(spatial_template, nodata=np.nan, resampling=Resampling.cubic_spline).compute()
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
      
      
        
# ---------------------------- Plot comparison -------------------------------------

# Load original TYR R data
TYF_specID_8 = xr.open_dataset(f'data/Species_TYF_R/specId_8_match_LUTO.nc').compute()


# Get downloaded carbon data CSV files; does not matter which species because SiteInfo is the same for all species
FullCAM_retrive_dir ='data/processed/Compare_API_and_Assemble_Data_Simulations/download_csv'
csv_files = [i for i in glob(f'{FullCAM_retrive_dir}/*.csv') if f'specId_8_specCat_Block' in i]

data_compare = pd.DataFrame()
for f in tqdm(csv_files):
    # Get Cache data
    #   The SiteInfo data for the FullCAM carbon df at lon/lat already downloaded
    lon, lat  = re.findall(r'df_(-?\d+\.\d+)_(-?\d+\.\d+)_specId_', os.path.basename(f))[0]
    with open(f'downloaded/species_{lon}_{lat}_specId_8.xml', 'r') as file:
        FullCAM_soil = parse_species_data(file.read())
        FullCAM_soil = FullCAM_soil.to_dataframe().reset_index()
        FullCAM_soil = FullCAM_soil.melt(id_vars=['TYF_Type'], value_vars=['Block', 'Belt'], var_name='Geometry', value_name='Value')
    # Get TYF data from reprojected dataset at the lon/lat
    TYF_specID_8_pt = (
        TYF_specID_8
        .sel(x=float(lon), y=float(lat), method='nearest')
        .to_dataframe()
        .reset_index()
        .melt(id_vars=['TYF_Type'], value_vars=['Block', 'Belt'], var_name='Geometry', value_name='Value')
    )
    # Merge FullCAM and reprojected TYF data, then append to main dataframe
    TYF_merged = pd.merge(
        FullCAM_soil,
        TYF_specID_8_pt,
        on=['TYF_Type', 'Geometry'],
        suffixes=('_FullCAM', '_v2020')
    )
    TYF_merged[['x', 'y']] = float(lon), float(lat)
    data_compare = pd.concat([data_compare, TYF_merged], ignore_index=True)
    
# Plot comparison
p9.options.figure_size = (6, 6)
p9.options.dpi = 150

fig = (
    p9.ggplot(data_compare)
    + p9.aes(x='Value_v2020', y='Value_FullCAM')
    + p9.geom_point(alpha=0.3, size=0.5)
    + p9.geom_abline(slope=1, intercept=0, linetype='dashed', color='red')
    + p9.facet_grid('Geometry ~ TYF_Type')
    + p9.theme_bw()
    + p9.labs(
        title='TYF Parameter Comparison for Eucalyptus globulus (specId=8)',
        x='TYF Parameter v2020',
        y='TYF Parameter FullCAM'
    )
)

fig.save('data/processed/Compare_API_and_Assemble_Data_Simulations/Data_compare_Species_TYF_R_specId_8.svg', dpi=150)
    


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
    <TYFCategory tTYFCat="BeltH" tyf_G="3.492" tyf_r="1.2"/>    # "BeltH" is the same as "BeltHW"; "BeltH" is not shown in the species PLO file from FullCAM
    <TYFCategory tTYFCat="BeltHN" tyf_G="2.288" tyf_r="1.608"/>
    <TYFCategory tTYFCat="BeltHW" tyf_G="3.492" tyf_r="1.2"/>
    <TYFCategory tTYFCat="BeltL" tyf_G="4.533" tyf_r="1.2"/>
    <TYFCategory tTYFCat="BlockES" tyf_G="6.317" tyf_r="1.0"/>
</TYFParameters>

'''

species_Mallee = xr.Dataset(
    {
        'BeltL': xr.DataArray([spatial_template * 4.533, spatial_template * 1.2], dims=['TYF_Type', 'y', 'x'], coords={'TYF_Type': ['tyf_G', 'tyf_r']}),
        'BeltH': xr.DataArray([spatial_template * 3.492, spatial_template * 1.2], dims=['TYF_Type', 'y', 'x'], coords={'TYF_Type': ['tyf_G', 'tyf_r']}),
        'BeltHW': xr.DataArray([spatial_template * 3.492, spatial_template * 1.2], dims=['TYF_Type', 'y', 'x'], coords={'TYF_Type': ['tyf_G', 'tyf_r']}),
        'BeltHN': xr.DataArray([spatial_template * 2.288, spatial_template * 1.608], dims=['TYF_Type', 'y', 'x'], coords={'TYF_Type': ['tyf_G', 'tyf_r']}),
        'BlockES': xr.DataArray([spatial_template * 6.317, spatial_template * 1.0], dims=['TYF_Type', 'y', 'x'], coords={'TYF_Type': ['tyf_G', 'tyf_r']}),
    }
).assign_coords({'x': spatial_template['x'], 'y': spatial_template['y']})

# Save the reprojected dataset
species_Mallee.to_netcdf(
    f'data/Species_TYF_R/specId_23_match_LUTO.nc', 
    encoding={var: {'zlib': True, 'complevel': 5} for var in species_Mallee.data_vars}
)
