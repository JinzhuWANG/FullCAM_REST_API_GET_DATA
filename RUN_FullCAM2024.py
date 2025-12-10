import os

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

# Get resfactored coords for downloading
scrap_coords = get_downloading_coords(resfactor=10)
RES_factor_coords = scrap_coords.set_index(['x', 'y']).index.tolist()

# Load existing downloaded files from cache
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads()
to_request_coords = set(RES_factor_coords) - set(existing_dfs)




###########################################################
#              Run FullCAM with REST API                  #
###########################################################
url = f"{BASE_URL_SIM}{ENDPOINT}"
headers = {"Ocp-Apim-Subscription-Key": API_KEY}

tasks = [
    delayed(get_plot_simulation)(lon, lat, url, headers)
    for lon, lat in tqdm(to_request_coords, total=len(to_request_coords))
]

for _ in tqdm(Parallel(n_jobs=20, return_as='generator_unordered')(tasks), total=len(tasks)):
    pass



###########################################################
#           Run FullCAM with local cache                  #
###########################################################
