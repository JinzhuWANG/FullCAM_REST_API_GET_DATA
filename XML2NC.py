import xarray as xr
import rioxarray as rio
import numpy as np

from tools.XML2NetCDF import get_siteinfo_data
from tools.cache_manager import get_existing_downloads
from joblib import Parallel, delayed
from tqdm.auto import tqdm

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
RES5_siteinfo = set(existing_siteinfo).intersection(set(RES5_coords))
RES5_species = set(existing_species).intersection(set(RES5_coords))
RES5_carbon = set(existing_dfs).intersection(set(RES5_coords))



# Get data holder
all_lats = sorted(set(lat for lat, lon in RES5_siteinfo))
all_lons = sorted(set(lon for lat, lon in RES5_siteinfo))

sample_lat, sample_lon = next(iter(RES5_siteinfo))
sample_data = get_siteinfo_data(sample_lon, sample_lat)

sample_template = sample_data.squeeze(['y', 'x'], drop=True)
ds_full = sample_template.expand_dims(y=all_lats, x=all_lons) * np.nan


# Parallel fetch data
def fetch_with_coords(lon, lat):
    data = get_siteinfo_data(lon, lat)
    return (lon, lat, data)

tasks = [
    delayed(fetch_with_coords)(lon, lat)
    for lat, lon in RES5_siteinfo
]

for lon, lat, data in tqdm(Parallel(n_jobs=-1, return_as='generator_unordered')(tasks), total=len(tasks)):
    ds_full.loc[dict(y=lat, x=lon)] = data.squeeze(dict(y=lat, x=lon))
    
    

