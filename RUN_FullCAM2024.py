import os
import xarray as xr

from joblib import Parallel, delayed
from tqdm.auto import tqdm

from tools.helpers.cache_manager import get_existing_downloads
from tools import get_downloading_coords, get_plot_simulation, get_species
from tools.parameter import (SSPS, FUTURE_DATA_YR_RANGES, SPECIES_GEOMETRY,
                             RES_FACTOR, SIM_LENGTH, HIST_SIM_YEAR_START, HIST_SIM_YEAR_END)



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
MAX_MISSING_COORDS = 10     # Stop once at most this many coords are still missing
MAX_RETRY_ROUNDS = 10       # Safety net; some coords may never succeed
N_WORKERS = 32               # Number of parallel threads to use for downloading

# Get resfactored coords for downloading
scrap_coords = get_downloading_coords(resfactor=RES_FACTOR, include_region='ALL')
RES_FACTOR_coords = scrap_coords.set_index(['x', 'y']).index.tolist()
coords_tuples = scrap_coords[['x', 'y']].apply(tuple, axis=1)


def get_coords_to_request(specId, specCat, ssp, data_year_range, sim_year_start, sim_year_end):
    '''
    Coords that still need simulating for a given run, i.e. all resfactored coords minus
    the ones already downloaded. Results are tracked per species, category, scenario and
    simulation period, so each combination is filtered against its own set of CSVs.

    Parameters
    ----------
    specId : int
        Species ID; see `SPECIES_MAP`.
    specCat : str
        Planting category; see `SPECIES_GEOMETRY`.
    ssp : str
        Climate scenario; one of `SSPS`, e.g. 'historical' or 'SSP245'.
    data_year_range : str
        Year span of the input climate data, e.g. '1970_2023' or '2021_2040'.
    sim_year_start, sim_year_end : int
        Simulation period, e.g. 2050 and 2150.

    Returns
    -------
        List of (lon, lat) tuples still to be requested.
    '''
    _, _, existing_dfs = get_existing_downloads(specId, specCat, ssp, data_year_range, sim_year_start, sim_year_end)
    existing_dfs_set = set((x, y) for x, y in existing_dfs)

    # Filter coords using vectorized pandas operations
    mask_coords = ~coords_tuples.isin(existing_dfs_set)
    return list(zip(scrap_coords.loc[mask_coords, 'x'], scrap_coords.loc[mask_coords, 'y']))


def run_simulations(data_site, specId, specCat, ssp, data_year_range, sim_year_start, sim_year_end):
    '''
    Simulate every coord of one run, resubmitting whatever is still missing.

    Because the results come back over the network, a single pass always loses a few
    points to transient failures. Each round re-reads the download cache and resubmits
    only the coords that have no CSV yet, until at most `MAX_MISSING_COORDS` remain.
    Gives up early if a whole round recovers nothing, since those coords will not
    succeed on a further attempt either.

    Parameters
    ----------
    data_site : xr.Dataset
        Site/climate/soil data for the scenario, in `siteinfo_cache.nc` layout.
    specId : int
        Species ID; see `SPECIES_MAP`.
    specCat : str
        Planting category; see `SPECIES_GEOMETRY`.
    ssp : str
        Climate scenario; one of `SSPS`, e.g. 'historical' or 'SSP245'.
    data_year_range : str
        Year span of the input climate data, e.g. '1970_2023' or '2021_2040'.
        Its first year becomes yr0TS on the climate/FPI time series.
    sim_year_start, sim_year_end : int
        Simulation period, e.g. 2050 and 2150.

    Returns
    -------
        List of (lon, lat) tuples that never came back.
    '''
    # yr0TS is where the input series is pinned on the calendar, so it is the first year
    #   of the data itself: 1970 historically, or the start of the 20-year future window.
    data_yr0TS = int(data_year_range.split('_')[0])
    data_species = xr.load_dataset(f"data/Species_TYF_R/specId_{specId}_match_LUTO.nc")

    previous_missing = None

    for attempt in range(1, MAX_RETRY_ROUNDS + 1):
        to_request_coords = get_coords_to_request(specId, specCat, ssp, data_year_range, sim_year_start, sim_year_end)
        n_missing = len(to_request_coords)

        # Few enough points left that the gaps can be ignored
        if n_missing <= MAX_MISSING_COORDS:
            print(f"  {n_missing} coords missing - within the tolerance of {MAX_MISSING_COORDS}.")
            return to_request_coords

        # A round that recovered nothing will not do better on the next one
        if n_missing == previous_missing:
            print(f"  Round {attempt}: {n_missing:,} coords still missing and no progress made - giving up.")
            return to_request_coords

        previous_missing = n_missing
        print(f"  Round {attempt} of {MAX_RETRY_ROUNDS}: submitting {n_missing:,} coords...")

        tasks = [
            delayed(get_plot_simulation)(
                'Cache', lon, lat, data_site, data_species, specId, specCat,
                ssp, data_year_range,
                sim_year_start=sim_year_start,
                sim_year_end=sim_year_end,
                data_yr0TS=data_yr0TS,
                url=url, headers=headers
            )
            for lon, lat in to_request_coords
        ]

        for _ in tqdm(Parallel(n_jobs=N_WORKERS, return_as='generator_unordered', backend='threading')(tasks), total=len(tasks)):
            pass

    to_request_coords = get_coords_to_request(specId, specCat, ssp, data_year_range, sim_year_start, sim_year_end)
    print(f"  Hit the {MAX_RETRY_ROUNDS}-round limit with {len(to_request_coords):,} coords still missing.")
    return to_request_coords




###########################################################
#              Run FullCAM with historical data           #
###########################################################

# Get cached data; takes ~10 mins to load and use ~100 GB of RAM;
#   using the bottom test snippet if just run FullCAM for a single point.
siteInfo_fill = xr.load_dataset("data/data_assembled/siteinfo_cache.nc")

# Year span actually held in the cache, e.g. '1970_2023'
hist_data_year_range = f"{int(siteInfo_fill['year'].min())}_{int(siteInfo_fill['year'].max())}"

# Run every species x category; driven by the observed climate, so tagged 'historical'
for specId, specCats in SPECIES_GEOMETRY.items():
    for specCat in specCats:
        print(f"Running historical {hist_data_year_range} "
              f"({HIST_SIM_YEAR_START}-{HIST_SIM_YEAR_END}), specId={specId}, specCat={specCat}...")
        missing_coords = run_simulations(
            siteInfo_fill, specId, specCat,
            'historical', hist_data_year_range,
            HIST_SIM_YEAR_START, HIST_SIM_YEAR_END
        )




###########################################################
#          Run FullCAM with future climate data           #
###########################################################


# Future-climate scenarios to run.
#   FUTURE_SIM_YEARS are the simulation start years; each maps to the 20-year climate window
#   driving it (see `FUTURE_DATA_YR_RANGES`), which is also the year postfix of the input files.
FUTURE_DATA_DIR = 'data/future_climate_data'
RUN_SSPS = [ssp for ssp in SSPS if ssp != 'historical']   # e.g. ['SSP245'] to run a single scenario
FUTURE_SIM_YEARS = list(FUTURE_DATA_YR_RANGES)            # e.g. [2030] to run a single window


# Get cache data
data_site = xr.open_dataset(f"data/data_assembled/siteinfo_cache.nc", chunks={})

# --------- Assemble using future datasets ----------
#   Soil comes from the historical cache; the climate/productivity layers are swapped
#   for the scenario ones.
data_soil = data_site[[
    'clayFrac',
    'rpmaCMInitF',
    'humsCMInitF',
    'inrtCMInitF',
    'TSMDInitF'
]]


def load_future_site_data(ssp:str, data_year_range:str) -> xr.Dataset:
    '''
    Assemble a site dataset driven by one future-climate scenario.

    Reads the per-variable layers of `data/future_climate_data/{var}/{ssp}/`, which are
    20-year averages, and combines them with the historical soil layers. The returned
    dataset has the same variable names as `siteinfo_cache.nc`, so it can be passed
    straight to `get_plot_simulation(data_source='Cache', ...)`.

    Parameters
    ----------
    ssp : str
        Future climate scenario, e.g. 'SSP245'; one of `SSPS` other than 'historical'.
    data_year_range : str
        Year span of the input climate data, e.g. '2021_2040'; the year postfix of the
        input files.

    Returns
    -------
        xr.Dataset with the site, climate and soil variables for the scenario.
    '''

    def _open(var):
        # x/y are re-assigned from the soil grid to guard against float rounding
        # differences between the two sources; the grids themselves already align.
        return xr.open_dataarray(
            f"{FUTURE_DATA_DIR}/{var}/{ssp}/{var}_{ssp}_{data_year_range}.nc",
            chunks={}
        ).assign_coords(x=data_soil['x'].values, y=data_soil['y'].values)

    data_zohr_temp = _open('avgAirTemp')
    data_zohr_fpi = _open('forestProdIx')
    data_zohr_rain = _open('rainFall')
    data_zohr_opan = _open('openPanEvap')
    data_zohr_mf = _open('maxAbgMF')

    return xr.Dataset({
        'avgAirTemp': data_zohr_temp,
        'forestProdIx': data_zohr_fpi,
        'fpiAvgLT': data_zohr_fpi,
        'rainfall': data_zohr_rain,
        'openPanEvap': data_zohr_opan,
        'maxAbgMF': data_zohr_mf,
        'clayFrac': data_soil['clayFrac'],
        'rpmaCMInitF': data_soil['rpmaCMInitF'],
        'humsCMInitF': data_soil['humsCMInitF'],
        'inrtCMInitF': data_soil['inrtCMInitF'],
        'TSMDInitF': data_soil['TSMDInitF']
    }).compute()


# --------- Run every scenario x simulation-year x species x category ----------
for SSP in RUN_SSPS:
    for sim_year_start in FUTURE_SIM_YEARS:

        data_year_range = FUTURE_DATA_YR_RANGES[sim_year_start]
        sim_year_end = sim_year_start + SIM_LENGTH

        # Assembled once per scenario/window and reused across all species
        data_zohr_comb = load_future_site_data(SSP, data_year_range)

        for specId, specCats in SPECIES_GEOMETRY.items():
            for specCat in specCats:
                print(f"Running {SSP} {data_year_range} ({sim_year_start}-{sim_year_end}), "
                      f"specId={specId}, specCat={specCat}...")

                # The scenario climate is a single 20-year average, so yr0TS (taken from
                #   data_year_range) only labels the series; with one year of data FullCAM
                #   applies it to every simulation year regardless.
                missing_coords = run_simulations(
                    data_zohr_comb, specId, specCat,
                    SSP, data_year_range,
                    sim_year_start, sim_year_end
                )













# ---------- Testing ----------

lon = 147.5
lat = -37.5

specId = 7
specCat = 'BlockES'

sim_year_start = 2035
sim_year_end = sim_year_start + 100

try_number:int=5
timeout:int=60

# Historical run; writes
#   df_..._specCat_BlockES_ssp_historical_InData_1970_2023_SIM_YR_2035_2135.csv
ssp = 'historical'
data_year_range = hist_data_year_range

# Test Cache data retrieval
data_source = "Cache"
data_site = xr.open_dataset(f"data/data_assembled/siteinfo_cache.nc", chunks={}).sel(year=2020)
data_species = xr.open_dataset(f"data/Species_TYF_R/specId_{specId}_match_LUTO.nc", chunks={})

# # Test a future scenario; writes
# #   df_..._specCat_BlockES_ssp_SSP245_InData_2041_2060_SIM_YR_2050_2150.csv
# ssp = 'SSP245'
# sim_year_start = 2050
# sim_year_end = sim_year_start + SIM_LENGTH
# data_year_range = FUTURE_DATA_YR_RANGES[sim_year_start]
# data_site = load_future_site_data(ssp, data_year_range)

# # Test API data retrieval
# data_source = "API"
# data_site = None
# data_species = None


# yr0TS is the first year of the input data, same rule as in `run_simulations`
data_yr0TS = int(data_year_range.split('_')[0])

# Run FullCAM
get_plot_simulation(data_source, lon, lat, data_site, data_species, specId, specCat, ssp, data_year_range, sim_year_start=sim_year_start, sim_year_end=sim_year_end, data_yr0TS=data_yr0TS, url=url, headers=headers, try_number=try_number, timeout=timeout)

