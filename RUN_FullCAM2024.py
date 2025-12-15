import os
import xarray as xr

from joblib import Parallel, delayed
from tqdm.auto import tqdm

from tools.helpers.cache_manager import get_existing_downloads
from tools import get_downloading_coords, get_plot_simulation



###########################################################
#                         Config                          #
###########################################################


# Get API Key
API_KEY = os.getenv("FULLCAM_API_KEY")
BASE_URL_SIM = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1"
ENDPOINT = "/2024/fullcam-simulator/run-plotsimulation"

url = f"{BASE_URL_SIM}{ENDPOINT}"
headers = {"Ocp-Apim-Subscription-Key": API_KEY}

# Define download parameters
RES_factor = 3
SPECIES_ID = 8          # Refer to `get_plot_simulation` docstring for species ID mapping
SPECIES_CAT = 'Belt'    # Refer individual species in the web API to see specific category; such as 'Block' or 'Belt'

# Get resfactored coords for downloading
scrap_coords = get_downloading_coords(resfactor=RES_factor, include_region='LUTO')
RES_factor_coords = scrap_coords.set_index(['x', 'y']).index.tolist()

# Load existing downloaded files from cache
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads(SPECIES_ID, SPECIES_CAT)
existing_dfs_set = set((x, y) for x, y in existing_dfs)

# Filter coords while preserving row order from scrap_coords
to_request_coords = [
    (x, y) for x, y in zip(scrap_coords['x'], scrap_coords['y'])
    if (x, y) not in existing_dfs_set
]




###########################################################
#              Run FullCAM with REST API                  #
###########################################################

# Get cached data
siteInfo_fill = xr.load_dataset("data/data_assembled/siteinfo_cache.nc", chunks={})
species_fill = xr.load_dataset(f"data/Species_TYF_R/specId_{SPECIES_ID}_match_LUTO.nc", chunks={})


# Prepare download tasks
tasks = [
    delayed(get_plot_simulation)('Cache', lon, lat, siteInfo_fill, species_fill, SPECIES_ID, SPECIES_CAT, url, headers)
    for lon, lat in to_request_coords
]

for _ in tqdm(Parallel(n_jobs=32, return_as='generator_unordered', backend='threading')(tasks), total=len(tasks)):
    pass



