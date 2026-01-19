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
RES_factor = 1
SPECIES_ID = 23         # Refer to `get_plot_simulation` docstring for species ID mapping
SPECIES_CAT = 'BeltH'    # Refer individual species in the web API to see specific category; such as 'Block' or 'Belt'

# Get resfactored coords for downloading
scrap_coords = get_downloading_coords(resfactor=RES_factor, include_region='LUTO')
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



###########################################################
#                    Get Species data                     #
###########################################################
# Vectorized filtering: convert existing_species to a set for O(1) lookup,
# then use pandas isin() for vectorized membership check
existing_species_set = set(existing_species)
existing_species_df = scrap_coords[['x', 'y']].apply(tuple, axis=1)
mask = ~existing_species_df.isin(existing_species_set)
to_request_species = list(zip(scrap_coords.loc[mask, 'x'], scrap_coords.loc[mask, 'y']))

tasks = [
    delayed(get_species)(lon, lat)
    for lon, lat in to_request_species
]

for _ in tqdm(Parallel(n_jobs=32, return_as='generator_unordered', backend='threading')(tasks), total=len(tasks)):
    pass


