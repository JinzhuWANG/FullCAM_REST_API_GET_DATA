import os
import xarray as xr

from joblib import Parallel, delayed
from tqdm.auto import tqdm

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



# Define download parameters
RES_factor = 1              # Resolution factor; 1 = 1km, 2 = 2km, etc.
SPECIES_ID = 23             # Refer to `get_plot_simulation` docstring for species ID mapping
SPECIES_CAT = 'BlockES'       # Refer individual species in the web API to see specific category; such as 'Block' or 'Belt'

# Get resfactored coords for downloading
scrap_coords = get_downloading_coords(resfactor=RES_factor, include_region='ALL')
RES_factor_coords = scrap_coords.set_index(['x', 'y']).index.tolist()



# Load existing downloaded files from cache
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads(SPECIES_ID, SPECIES_CAT)
existing_dfs_set = set((x, y) for x, y in existing_dfs)

# Filter coords using vectorized pandas operations
coords_tuples = scrap_coords[['x', 'y']].apply(tuple, axis=1)
mask_coords = ~coords_tuples.isin(existing_dfs_set)
to_request_coords = list(zip(scrap_coords.loc[mask_coords, 'x'], scrap_coords.loc[mask_coords, 'y']))




###########################################################
#              Run FullCAM with REST API                  #
###########################################################

# Get cached data; tankes ~10 mins to load and use ~100 GB of RAM; 
#   using the below test snippet if just run FullCAM for a single point.
siteInfo_fill = xr.load_dataset("data/data_assembled/siteinfo_cache.nc", chunks={})
species_fill = xr.load_dataset(f"data/Species_TYF_R/specId_{SPECIES_ID}_match_LUTO.nc", chunks={})


# Prepare download tasks
tasks = [
    delayed(get_plot_simulation)('Cache', lon, lat, siteInfo_fill, species_fill, SPECIES_ID, SPECIES_CAT, url, headers)
    for lon, lat in to_request_coords
]

for _ in tqdm(Parallel(n_jobs=64, return_as='generator_unordered', backend='threading')(tasks), total=len(tasks)):
    pass




# ---------- Testing ----------

lon = 147.5
lat = -37.5

specId = 7
specCat = 'BlockES' 

try_number:int=5
timeout:int=60

# Test Cache data retrieval
data_source = "Cache"
data_site = xr.open_dataset("data/data_assembled/siteinfo_cache.nc", chunks={})
data_species = xr.open_dataset(f"data/Species_TYF_R/specId_{specId}_match_LUTO.nc", chunks={})

# Test API data retrieval
data_source = "API"
data_site = None
data_species = None


# Run FullCAM
get_plot_simulation(data_source, lon, lat, data_site, data_species, specId, specCat, url, headers, try_number, timeout)

