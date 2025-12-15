import os
import numpy as np
import xarray as xr

from joblib import Parallel, delayed
from tqdm.auto import tqdm
from itertools import product

from tools.helpers.cache_manager import get_existing_downloads
from tools import get_downloading_coords, get_plot_simulation, get_species



###########################################################
#                         Config                          #
###########################################################


# Get API Key
API_KEY = os.getenv("FULLCAM_API_KEY")
BASE_URL_SIM = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1"
ENDPOINT = "/2024/fullcam-simulator/run-plotsimulation"

url = f"{BASE_URL_SIM}{ENDPOINT}"
headers = {"Ocp-Apim-Subscription-Key": API_KEY}

# Define species ID to download
SPECIES_ID = 8  # Eucalyptus globulus

# Get resfactored coords for downloading
scrap_coords = get_downloading_coords(resfactor=10)
RES_factor_coords = scrap_coords.set_index(['x', 'y']).index.tolist()

# Load existing downloaded files from cache
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads(SPECIES_ID)
to_request_coords = set(RES_factor_coords) - set(existing_dfs)
to_request_coords = set((round(x, 2), round(y, 2)) for x, y in to_request_coords)




###########################################################
#              Run FullCAM with REST API                  #
###########################################################

# Get cached data
siteInfo_fill = xr.load_dataset("data/data_assembled/siteinfo_cache.nc", chunks={})
species_fill = xr.load_dataset("data/Species_TYF_R/specId_8_match_LUTO.nc", chunks={})


# Prepare download tasks
tasks = [
    delayed(get_plot_simulation)('Cache', lon, lat, siteInfo_fill, species_fill, SPECIES_ID, 'Block', url, headers)
    for lon, lat in to_request_coords
]

for _ in tqdm(Parallel(n_jobs=128, return_as='generator_unordered', backend='threading')(tasks), total=len(tasks)):
    pass



