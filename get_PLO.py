import os

from joblib import Parallel, delayed
from tqdm.auto import tqdm
from tools.cache_manager import get_existing_downloads
from tools.plo_section_functions import assemble_plo_sections, get_plot_simulation



# Configuration
#   If having issues with API access, try running below snippet to temporarily adding key to current session:
#   WARNING: Do not hardcode API keys in production code!

'''
import os
os.environ["FULLCAM_API_KEY"] = "your_api_key_here"
'''

# ----------- Set up key and Server Url --------------
API_KEY = os.getenv("FULLCAM_API_KEY")
if not API_KEY: raise ValueError("`FULLCAM_API_KEY`environment variable not set!")

BASE_URL_SIM = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1"
ENDPOINT = "/2024/fullcam-simulator/run-plotsimulation"


# ----------- Get downloaded files --------------
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads()
existing_data_coords = set(existing_siteinfo).intersection(set(existing_species))
existing_CSV_coords = set(existing_dfs)
to_request_coords = existing_data_coords - existing_CSV_coords


# ----------------------- Plot simulation --------------------------
if not os.path.exists('downloaded'): os.makedirs('downloaded')

url = f"{BASE_URL_SIM}{ENDPOINT}"
headers = {"Ocp-Apim-Subscription-Key": API_KEY}

tasks = [
    delayed(get_plot_simulation)(lon, lat, url, headers)
    for lat, lon in tqdm(to_request_coords, total=len(to_request_coords))
]

for _ in tqdm(Parallel(n_jobs=35,  backend='threading', return_as='generator_unordered')(tasks), total=len(tasks)):
    pass




