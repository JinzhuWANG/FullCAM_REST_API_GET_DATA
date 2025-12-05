
import requests
import io
import rioxarray as rxr
import numpy as np
import pandas as pd
import xarray as xr
import pathlib
import plotnine as p9


from tqdm.auto import tqdm
from lxml import etree
from joblib import Parallel, delayed
from tqdm.auto import tqdm
from pathlib import Path

from tools.cache_manager import get_existing_downloads


######################################################################################
#                  Download ANUClim data from NCI Thredds server                     #    
######################################################################################


# the top level folder on the NCI
thredds_link_fileServer = 'https://thredds.nci.org.au/thredds/fileServer/gh70/ANUClimate/v2-0/stable'


def get_data_urls(years: range, var:str, cadence:str='month', n_jobs:int=32):
    
    if var not in ['evap', 'frst', 'pw', 'rain', 'srad', 'tavg', 'tmax', 'tmin', 'vp', 'vpd']:
        raise ValueError("Variable must be one of: ['evap', 'frst', 'pw', 'rain', 'srad', 'tavg', 'tmax', 'tmin', 'vp', 'vpd']")
    if cadence not in ['day', 'month']:
        raise ValueError("Cadence must be one of: ['day', 'month']")
    
    # get the urls for each year
    datasets = []
    for yr in years:
        thredds_link_catalog = f'https://thredds.nci.org.au/thredds/catalog/gh70/ANUClimate/v2-0/stable/{cadence}'
        soup = etree.HTML(requests.get(f'{thredds_link_catalog}/{var}/{yr}/catalog.html').content)
        url_base = [i.get('href') for i in soup.xpath('//a[contains(@href, ".html")]') if "dataset" in i.get('href')]
        datasets.extend([f'{thredds_link_fileServer}/{i.replace("catalog.html?dataset=gh70/", "")}' for i in url_base])
        
    return datasets

    
    
def parallel_download(urls:list, n_jobs=32):
    
    def _download_url(url):
        f_name = pathlib.Path(url).name
        
        if pathlib.Path(f'data/ANUClim/raw_data/{f_name}').exists():
            return None
        
        try:
            dataBytes = requests.get(url).content
            ds = xr.open_dataset(io.BytesIO(dataBytes))
            ds.to_netcdf(f'data/ANUClim/raw_data/{f_name}', mode='w')
            return None
        except Exception as e:
            return url
    
    tasks = [delayed(_download_url)(url) for url in urls]
    failed_downloads = []
    for mes in tqdm(Parallel(n_jobs=n_jobs, return_as='generator_unordered')(tasks), total=len(tasks)):
        if mes is not None:  # Only append actual failures
            failed_downloads.append(mes)

    return failed_downloads



# Download data
#   The available years as of 3 Dec 2025 is checked from 
#   https://thredds.nci.org.au/thredds/catalog/gh70/ANUClimate/v2-0/stable/month/catalog.html
#   Although the web has 2030 dataset links, the actual data files only go up to 2024.

data_avail = {
    'evap': range(1970, 2030 + 1),
    'frst': range(1970, 2030 + 1),
    'pw':   range(1900, 2030 + 1),
    'rain': range(1900, 2030 + 1),
    'srad': range(1960, 2030 + 1),
    'tavg': range(1960, 2030 + 1),
    'tmax': range(1960, 2030 + 1),
    'tmin': range(1960, 2030 + 1),
    'vp':   range(1960, 2030 + 1),
    'vpd':  range(1960, 2030 + 1),
}

# Initial download attempt
failed_urls = []
for var, years in data_avail.items():
    download_urls = get_data_urls(years, var)
    print(f'Downloading {var} for years {years.start} to {years.stop - 1}')
    failed_urls.extend(parallel_download(download_urls, n_jobs=32))
    
    
# Retry failed downloads with a maximum retry limit
max_retries = 3
retry_count = 0

retry_urls = failed_urls.copy()
while len(retry_urls) > 0 and (retry_count < max_retries):
    retry_count += 1
    print(f'Retry attempt {retry_count}/{max_retries}: {len(retry_urls)} failed downloads...')
    failed_urls = parallel_download(retry_urls, n_jobs=16)
    retry_urls = failed_urls.copy()  # Retry all URLs that failed this attempt

if len(failed_urls) > 0:
    print(f'WARNING: {len(failed_urls)} downloads failed after {max_retries} retries')
    print('Failed URLs:')
    for url in failed_urls:
        print(f'  - {url}')







######################################################################################
#                  Process ANUClim data for FullCAM input requirements               #
######################################################################################


'''
The FullCAM model needs monthly data for:
- evap, corresponding to FullCAM variable 'openPanEvap'
- rain, corresponding to FullCAM variable 'rainfall'
- tavg, corresponding to FullCAM variable 'avgAirTemp'

As of Dec 2025, the FullCAM model requires data from 1970 to 2022.
'''

# Get variable and files
files = sorted(pathlib.Path("data/ANUClim/raw_data/").glob("*.nc"))
years_FullCAM = range(1970, 2023)


# ------ evap ------ 
evap_f = [i for i in files if "evap" in i.name]
years = sorted(set([int(i.name.split("monthly_")[1][:4]) for i in evap_f]))
months = sorted(set([int(i.name.split("monthly_")[1][4:6]) for i in evap_f]))

evap_ds = (
    xr.open_dataset(evap_f[0])['evap'] 
    .isel(time=0, drop=True)
    .rename({'lon': 'x', 'lat': 'y'})
    .expand_dims(year=years, month=months
    ) 
) * np.nan

for f in tqdm(evap_f):
    ds = xr.open_dataset(f)['evap']
    _year = ds.time.dt.year.item()
    _month = ds.time.dt.month.item()
    evap_ds.loc[dict(year=_year, month=_month)] = ds.isel(time=0, drop=True).values
    
    
# ----- rain ----- 
rain_f = [i for i in files if "rain" in i.name]
years = sorted(set([int(i.name.split("monthly_")[1][:4]) for i in rain_f]))
months = sorted(set([int(i.name.split("monthly_")[1][4:6]) for i in rain_f]))

rain_ds =( 
    xr.open_dataset(rain_f[0])['rain']
    .isel(time=0, drop=True)
    .expand_dims(year=years, month=months)
    .rename({'lon': 'x', 'lat': 'y'})
) * np.nan
    
for f in tqdm(rain_f):
    ds = xr.open_dataset(f)['rain']
    _year = ds.time.dt.year.item()
    _month = ds.time.dt.month.item()
    rain_ds.loc[dict(year=_year, month=_month)] = ds.isel(time=0, drop=True).values
    
    
    
# ----- tavg ----- 
tavg_f = [i for i in files if "tavg" in i.name]
years = sorted(set([int(i.name.split("monthly_")[1][:4]) for i in tavg_f]))
months = sorted(set([int(i.name.split("monthly_")[1][4:6]) for i in tavg_f]))

tavg_ds = (
    xr.open_dataset(tavg_f[0])['tavg']
    .isel(time=0, drop=True)
    .expand_dims(year=years, month=months)
    .rename({'lon': 'x', 'lat': 'y'})
) * np.nan


for f in tqdm(tavg_f):
    ds = xr.open_dataset(f)['tavg']
    _year = ds.time.dt.year.item()
    _month = ds.time.dt.month.item()
    tavg_ds.loc[dict(year=_year, month=_month)] = ds.isel(time=0, drop=True).values
    
    
# Combine dataarray to a dataset
combined_ds = xr.Dataset({
    'openPanEvap': evap_ds.sel(year=years_FullCAM),
    'rainfall': rain_ds.sel(year=years_FullCAM),
    'avgAirTemp': tavg_ds.sel(year=years_FullCAM)
})

combined_ds.to_netcdf(
    "data/ANUClim/processed/ANUClim_to_FullCAM.nc", 
    mode='w',
    encoding={
        'openPanEvap': {'zlib': True, 'complevel': 5, 'chunksizes': (1, 1, 256, 256)},
        'rainfall': {'zlib': True, 'complevel': 5, 'chunksizes': (1, 1, 256, 256)},
        'avgAirTemp': {'zlib': True, 'complevel': 5, 'chunksizes': (1, 1, 256, 256)},
    }
)




######################################################################################
#                        Compare ANUClim data with FullCAM                           #
######################################################################################


# Config
RES_factor = 10
soil_path = Path('data/Soil_landscape_AUS/ClayContent/000055684v002/data')

# --------------- Get valid coords ---------------
PLO_data_path = Path('N:/Data-Master/FullCAM/FullCAM_REST_API_GET_DATA_2025/data/processed/BB_PLO_OneKm')
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads()

Aus_xr = rxr.open_rasterio("data/lumap.tif").sel(band=1, drop=True) >= -1 # >=-1 means all Australia continent
lon_lat = Aus_xr.to_dataframe(name='mask').reset_index()[['y', 'x', 'mask']].round({'x':2, 'y':2})
lon_lat['cell_idx'] = range(len(lon_lat))

Aus_cell = xr.DataArray(np.arange(Aus_xr.size).reshape(Aus_xr.shape), coords=Aus_xr.coords, dims=Aus_xr.dims)
Aus_cell_RES = Aus_cell.coarsen(x=RES_factor, y=RES_factor, boundary='trim').max()
Aus_cell_RES_df = Aus_cell_RES.to_dataframe(name='cell_idx').reset_index()['cell_idx']

RES_df = lon_lat.query('mask == True').loc[lon_lat['cell_idx'].isin(Aus_cell_RES_df)].reset_index(drop=True)
RES_coords = RES_df.set_index(['x', 'y']).index.tolist()

res_coords = set(existing_siteinfo).intersection(set(RES_coords))
res_coords_x = xr.DataArray([coord[0] for coord in res_coords], dims=['cell'])
res_coords_y = xr.DataArray([coord[1] for coord in res_coords], dims=['cell'])



# --------------- Load ANUClim Data ---------------

data_FullCam = (
    xr.open_dataset('data/processed/siteinfo_RES.nc')
    .compute()
    .sel(x=res_coords_x, y=res_coords_y)
)

data_ANUClim = (
    xr.open_dataset("data/ANUClim/processed/ANUClim_to_FullCAM.nc")
    .compute()
    .sel(x=res_coords_x,  y=res_coords_y, method='nearest') 
)



# openPanEvap
evap_FullCAM = data_FullCam['openPanEvap'].to_dataframe().reset_index()
evap_downloaded = data_ANUClim['openPanEvap'].to_dataframe().reset_index()

plot_data = (
    pd.merge(
        evap_FullCAM,
        evap_downloaded,
        on=['cell', 'year', 'month'],
        suffixes=('_FullCAM', '_Downloaded')
    )
    .round({'x':3, 'y':3})
    .dropna()
)


fig = (
    p9.ggplot(plot_data[::1000], p9.aes(x='openPanEvap_FullCAM', y='openPanEvap_Downloaded'))
    + p9.geom_point(alpha=0.3)
    + p9.geom_abline(slope=1, intercept=0, color='red', linetype='dashed')
    + p9.labs(
        title='ANUClim Data Download vs FullCAM Data',
        x='FullCAM openPanEvap (mm/month)',
        y='Downloaded openPanEvap (mm/month)'
    )
    + p9.theme_bw()
)


# rainfull
rain_FullCAM = data_FullCam['rainfall'].to_dataframe().reset_index()
rain_downloaded = data_ANUClim['rainfall'].to_dataframe().reset_index()

plot_data = (
    pd.merge(
        rain_FullCAM,
        rain_downloaded,
        on=['cell', 'year', 'month'],
        suffixes=('_FullCAM', '_Downloaded')
    )
    .round({'x':3, 'y':3})
    .dropna()
)

fig = (
    p9.ggplot(plot_data[::1000], p9.aes(x='rainfall_FullCAM', y='rainfall_Downloaded'))
    + p9.geom_point(alpha=0.3)
    + p9.geom_abline(slope=1, intercept=0, color='red', linetype='dashed')
    + p9.labs(
        title='ANUClim Data Download vs FullCAM Data',
        x='FullCAM rainfall (mm/month)',
        y='Downloaded rainfall (mm/month)'
    )
    + p9.theme_bw()
)


# avgAirTemp
tavg_FullCAM = data_FullCam['avgAirTemp'].to_dataframe().reset_index()
tavg_downloaded = data_ANUClim['avgAirTemp'].to_dataframe().reset_index()  

plot_data = (
    pd.merge(
        tavg_FullCAM,
        tavg_downloaded,
        on=['cell', 'year', 'month'],
        suffixes=('_FullCAM', '_Downloaded')
    )
    .round({'x':3, 'y':3})
    .dropna()
)

fig = (
    p9.ggplot(plot_data[::1000], p9.aes(x='avgAirTemp_FullCAM', y='avgAirTemp_Downloaded'))
    + p9.geom_point(alpha=0.3)
    + p9.geom_abline(slope=1, intercept=0, color='red', linetype='dashed')
    + p9.labs(
        title='ANUClim Data Download vs FullCAM Data',
        x='FullCAM avgAirTemp (°C)',
        y='Downloaded avgAirTemp (°C)'
    )
    + p9.theme_bw()
)





