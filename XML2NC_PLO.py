"""
XML2NC_PLO.py

Convert PLO XML files to NetCDF and GeoTIFF formats using XML2Data_PLO functionality.

This script mirrors the structure of XML2NC.py but processes PLO files instead of API cache files.
It extracts siteinfo, soilbase, and soilinit data from PLO files and creates spatially gridded datasets.
"""


import os, re
import scandir_rs
import numpy as np
import xarray as xr
import rioxarray as rio

from pathlib import Path
from joblib import Parallel, delayed
from tqdm.auto import tqdm
from affine import Affine
from tools.XML2Data_PLO import (
    export_to_geotiff_with_band_names,
    get_siteinfo_data,
    get_soilbase_data,
    get_soilInit_data
)


# ===================== Configuration =====================
# Resolution factor for downsampling (10 = 0.1° grid spacing)
RES_factor = 1
PLO_dir = Path('N:/Data-Master/FullCAM/XMLfiles')
Cache_dir = Path('F:/jinzhu/TMP/Full_cam_tmp')
OUTPUT_DIR = Path('N:/Data-Master/FullCAM/FullCAM_REST_API_GET_DATA_2025/data/processed/BB_PLO_OneKm')
lon_lat_reg_xml = re.compile(r'.*_(-?\d+\.\d+)_(-?\d+\.\d+)\.plo')


# ===================== Get cached PLO files =====================
# Cache existing PLO files
if not os.path.exists('downloaded/BB_PLO_files.txt'):
    files = [entry.path for entry in scandir_rs.Scandir(PLO_dir)]
    with open('downloaded/BB_PLO_files.txt', 'w', encoding='utf-8') as cache_file:
        cache_file.writelines('\n'.join(files))
                
# Build PLO coordinate map
plo_coord_map = {}
with open('downloaded/BB_PLO_files.txt', 'r', encoding='utf-8') as cache_file:
    lines = cache_file.readlines()
    for line in tqdm(lines, desc="Building PLO coordinate map"):
        filepath = line.strip()
        match = lon_lat_reg_xml.findall(filepath)
        if match:
            lat, lon = match[0]
            plo_coord_map[(float(lon), float(lat))] = Path(PLO_dir) / filepath


# ===================== Get Coordinates =====================
print("Loading Australian coordinate grid...")
Aus_xr = rio.open_rasterio("data/lumap.tif").sel(band=1, drop=True).compute() >= -1
lon_lat = Aus_xr.to_dataframe(name='mask').reset_index()[['y', 'x', 'mask']].round({'x':2, 'y':2})
lon_lat['cell_idx'] = range(len(lon_lat))

# Downsample to RES_factor resolution
Aus_cell = xr.DataArray(np.arange(Aus_xr.size).reshape(Aus_xr.shape), coords=Aus_xr.coords, dims=Aus_xr.dims)
Aus_cell_RES = Aus_cell.coarsen(x=RES_factor, y=RES_factor, boundary='trim').max()
Aus_cell_RES_df = Aus_cell_RES.to_dataframe(name='cell_idx').reset_index()['cell_idx']

RES_df = lon_lat.query('mask == True').loc[lon_lat['cell_idx'].isin(Aus_cell_RES_df)].reset_index(drop=True)
RES_coords = RES_df.set_index(['x', 'y']).index.tolist()

# Get resfactored coords
available_coords = set(RES_coords).intersection(set(plo_coord_map.keys()))
sample_lon, sample_lat = next(iter(available_coords))
sample_plo = plo_coord_map[(sample_lon, sample_lat)]


# ===================== Setup Spatial Grid =====================
all_lats = np.arange(max(RES_df['y']), min(RES_df['y']) - 0.001, -RES_factor * 0.01).astype(np.float32)
all_lons = np.arange(min(RES_df['x']), max(RES_df['x']) + 0.001, RES_factor * 0.01).astype(np.float32)

cell_size_x = abs(all_lons[1] - all_lons[0])
cell_size_y = abs(all_lats[1] - all_lats[0])

# Get affine transform from reference raster
lumap_xr = rio.open_rasterio('data/lumap.tif', masked=True)
trans = list(lumap_xr.rio.transform())
trans[2] = min(all_lons) + (cell_size_x / 2)
trans[5] = max(all_lats) - (cell_size_y / 2)
trans[0] = trans[0] * RES_factor
trans[4] = trans[4] * RES_factor
trans = Affine(*trans)


# ===================== Process SiteInfo Data =====================
sample_template = get_siteinfo_data(plo_coord_map[(sample_lon, sample_lat)]) * np.nan

# Create full spatial grid
siteInfo_full = sample_template.squeeze(['y', 'x'], drop=True).expand_dims(y=all_lats, x=all_lons) * np.nan
siteInfo_full = siteInfo_full.astype(np.float32)

# Parallel fetch data
def fetch_siteinfo_from_plo(lon, lat):
    """Fetch siteinfo data from PLO file."""
    try:
        plo_file_from = plo_coord_map.get((lon, lat))
        data = get_siteinfo_data(plo_file_from)
        return (lon, lat, data)
    except Exception as e:
        print(f"Error processing siteinfo for ({lon}, {lat}): {e}")
        return (lon, lat, sample_template)

tasks = [delayed(fetch_siteinfo_from_plo)(lon, lat) for lon, lat in available_coords]
for lon, lat, data in tqdm(Parallel(n_jobs=16, backend='threading', return_as='generator')(tasks), total=len(tasks)):
    siteInfo_full.loc[dict(y=lat, x=lon)] = data.squeeze(['y', 'x'], drop=True)
    

# Save to NetCDF
print("Saving SiteInfo NetCDF...")
siteInfo_full.rio.write_crs("EPSG:4283", inplace=True)
siteInfo_full.rio.write_transform(trans, inplace=True)

encoding = {}   # Chunk the data to x-64, y-64, full-year, full-month for faster access
for var in siteInfo_full.data_vars:
    dims = siteInfo_full[var].dims
    if dims == ('y', 'x', 'year', 'month'):
        encoding[var] = {'zlib': True, 'complevel': 5, 'chunksizes': [64, 64, 49, 12]}
    elif dims == ('y', 'x'):
        encoding[var] = {'zlib': True, 'complevel': 5, 'chunksizes': [64, 64]}
    elif dims == ('y', 'x', 'year'):
        # Handle any other dimension combinations
        encoding[var] = {'zlib': True, 'complevel': 5, 'chunksizes': [64, 64, 49]}
        
siteInfo_full.to_netcdf(OUTPUT_DIR / 'siteinfo_PLO_RES_chunk.nc', encoding=encoding)

# Save to GeoTIFFs
print("Saving SiteInfo GeoTIFFs...")
for var, xarry in siteInfo_full.data_vars.items():
    if len(xarry.dims) > 2:
        to_stack_dims = [dim for dim in xarry.dims if dim not in ['y', 'x']]
        xarry = xarry.stack(band=to_stack_dims).astype(np.float32)
    export_to_geotiff_with_band_names(xarry, str(OUTPUT_DIR / f'siteInfo_PLO_{var}_RES_multiband.tif'))


# ===================== Process SoilBase Data =====================
print("\n=== Processing SoilBase data from PLO files ===")

# Get sample template
sample_soilother = get_soilbase_data(str(sample_plo))['SoilOther'] * np.nan

# Create full spatial grid
soilbase_full_soilother = sample_soilother.squeeze(['y', 'x'], drop=True).expand_dims(y=all_lats, x=all_lons) * np.nan

# Parallel fetch data
def fetch_soilbase_from_plo(lon, lat):
    """Fetch soilbase data from PLO file."""
    try:
        plo_file = plo_coord_map.get((lon, lat))
        if plo_file is None:
            return (lon, lat, sample_soilother)
        data_dict = get_soilbase_data(str(plo_file))
        return (lon, lat, data_dict['SoilOther'])
    except Exception as e:
        print(f"Error processing soilbase for ({lon}, {lat}): {e}")
        return (lon, lat, sample_soilother)

tasks = [delayed(fetch_soilbase_from_plo)(lon, lat) for lon, lat in available_coords]
for lon, lat, data_soilother in tqdm(Parallel(n_jobs=64, backend='threading', batch_size=32, pre_dispatch='4*n_jobs', return_as='generator_unordered')(tasks), total=len(tasks)):
    soilbase_full_soilother.loc[dict(y=lat, x=lon)] = data_soilother.squeeze(['y', 'x'], drop=True)

# Save to NetCDF
print("Saving SoilBase NetCDF...")
soilbase_full_soilother.name = 'data'
soilbase_full_soilother.rio.write_crs("EPSG:4283", inplace=True)
soilbase_full_soilother.rio.write_transform(trans, inplace=True)
soilbase_full_soilother.to_netcdf(OUTPUT_DIR / 'soilbase_PLO_soilother_RES.nc')

# Save to GeoTIFF
print("Saving SoilBase GeoTIFF...")
export_to_geotiff_with_band_names(soilbase_full_soilother, str(OUTPUT_DIR / 'soilbase_PLO_soilother_RES_multiband.tif'))


# ===================== Process SoilInit Data =====================
print("\n=== Processing SoilInit data from PLO files ===")

# Get sample template
sample_soilInit = get_soilInit_data(str(sample_plo)) * np.nan

# Create full spatial grid
soilInit_full = sample_soilInit.squeeze(['y', 'x'], drop=True).expand_dims(y=all_lats, x=all_lons) * np.nan

# Parallel fetch data
def fetch_soilInit_from_plo(lon, lat):
    """Fetch soilInit data from PLO file."""
    try:
        plo_file = plo_coord_map.get((lon, lat))
        if plo_file is None:
            return (lon, lat, sample_soilInit)
        data = get_soilInit_data(str(plo_file))
        return (lon, lat, data)
    except Exception as e:
        print(f"Error processing soilInit for ({lon}, {lat}): {e}")
        return (lon, lat, sample_soilInit)

tasks = [delayed(fetch_soilInit_from_plo)(lon, lat) for lon, lat in available_coords]
for lon, lat, data in tqdm(Parallel(n_jobs=64, backend='threading', batch_size=32, pre_dispatch='4*n_jobs', return_as='generator_unordered')(tasks), total=len(tasks)):
    soilInit_full.loc[dict(y=lat, x=lon)] = data.squeeze(['y', 'x'], drop=True)

# Save to NetCDF
print("Saving SoilInit NetCDF...")
soilInit_full.name = 'data'
soilInit_full.rio.write_crs("EPSG:4283", inplace=True)
soilInit_full.rio.write_transform(trans, inplace=True)
soilInit_full.to_netcdf(OUTPUT_DIR / 'soilInit_PLO_RES.nc', encoding={'data': {'zlib': True, 'complevel': 5}})

# Save to GeoTIFF
print("Saving SoilInit GeoTIFF...")
export_to_geotiff_with_band_names(soilInit_full, str(OUTPUT_DIR / 'soilInit_PLO_RES_multiband.tif'))

