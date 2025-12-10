"""
FullCAM PLO File Section Functions
Modular functions for creating individual sections of PLO files.
Each function generates XML for a specific section with proper Python docstrings.
"""

import os
import time
import numpy as np
import pandas as pd
import requests
import xarray as xr
import rioxarray as rio

from lxml import etree
from io import StringIO
from threading import Lock
from collections import Counter
from tools.XML2Data import parse_site_data, parse_init_data, parse_soil_data


# Configuration
API_KEY = os.getenv("FULLCAM_API_KEY")
if not API_KEY: raise ValueError("`FULLCAM_API_KEY`environment variable not set!")

BASE_URL_DATA = "https://api.dcceew.gov.au/climate/carbon-accounting/2024/data/v1"
HEADERS = {
    "Host": "api.dcceew.gov.au",
    "Ocp-Apim-Subscription-Key": API_KEY,
    "Content-Type": "application/json"
}

# Thread-safe lock for cache file writes
_cache_write_lock = Lock()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_downloading_coords(resfactor:int=10):
    '''
    Base on LUTO's spatial template (data/lumap.tif), get resfactored lon/lat coords.
    '''

    # Get all lon/lat for Australia; the raster used is taken from the template of LUTO
    Aus_xr = rio.open_rasterio("data/lumap.tif").sel(band=1, drop=True).compute() >= -1 # >=1 means the continental Australia 
    lon_lat = Aus_xr.to_dataframe(name='mask').reset_index()[['y', 'x', 'mask']]
    lon_lat['cell_idx'] = range(len(lon_lat))

    Aus_cell = xr.DataArray(np.arange(Aus_xr.size).reshape(Aus_xr.shape), coords=Aus_xr.coords, dims=Aus_xr.dims)
    Aus_cell_RES = Aus_cell.isel(x=slice(None, None, resfactor), y=slice(None, None, resfactor))
    Aus_cell_RES_df = Aus_cell_RES.to_dataframe(name='cell_idx').reset_index()[['y', 'x', 'cell_idx']]

    scrap_coords = (
        lon_lat
        .query('mask == True')
        .loc[lon_lat['cell_idx'].isin(Aus_cell_RES_df['cell_idx'])]
        .drop(columns=['mask', 'cell_idx'])
        .sort_values(by=['x', 'y'])
        .reset_index(drop=True)
    ).round({'x': 4, 'y': 4})
    
    return scrap_coords


def _bool_to_xml(value: bool) -> str:
    """Convert Python bool to XML string format ('true'/'false')."""
    return "true" if value else "false"


def get_siteinfo(
    lat, 
    lon, 
    sim_start_year:int=2010,
    try_number=10, 
    download_records='downloaded/successful_downloads.txt', 
    consensus_count=3
):
    '''
    Download siteinfo XML for given lat/lon with consensus mechanism.
    To ensure data integrity, multiple attempts are made to download the siteinfo.
    A consensus is reached when the same soilBase and soilInit data are obtained
    a specified number of times (consensus_count). This helps mitigate transient
    network issues or server inconsistencies.
    
    Parameters
    ----------
    lat : float
        Latitude of the site.
    lon : float
        Longitude of the site.
    sim_start_year : int
        Year for TSMDInitF data extraction.
    try_number : int
        Maximum number of download attempts.
    download_records : str
        Path to the cache file for recording successful downloads.
    consensus_count : int
        Number of matching downloads required for consensus.
        
    Returns
    -------
        None if successful, else (lon, lat), "Failed" on failure.
    '''
    
    PARAMS = {
        "latitude": lat,
        "longitude": lon,
        "area": "OneKm",
        "plotT": "CompF",
        "frCat": "All",
        "incGrowth": "false",
        "version": 2024
    }
    url = f"{BASE_URL_DATA}/2024/data-builder/siteinfo"
    
    soilbase_map = {}               # Maps soilBase hash to response text
    soilinit_map = {}               # Maps soilInit hash to response text
    soilbase_counter = Counter()    # Count occurrences of each soilBase hash
    soilinit_counter = Counter()    # Count occurrences of each soilInit hash

    for attempt in range(try_number):
        is_last_attempt = (attempt == try_number - 1)

        try:
            response = requests.get(url, params=PARAMS, headers=HEADERS, timeout=100)

            # Apply exponential backoff and retry for non-200 status
            if response.status_code != 200:
                if not is_last_attempt:
                    time.sleep(2**attempt)
                continue


            # Track SoilBase occurrences for consensus
            #   Here we use `clayFrac` as a representative metric for soilBase
            soilBase = parse_soil_data(response.text)['clayFrac'].item()
            soilbase_counter[soilBase] += 1
            soilbase_map[soilBase] = response.text
            most_common_soilbase, base_count = soilbase_counter.most_common(1)[0]
            
            # Track SoilInit occurrences for consensus
            #   Here we use 'TSMDInitF' as representative metrics for soilInit
            soilInit = parse_init_data(response.text, sim_start_year)['TSMDInitF'].item()
            soilinit_counter[soilInit] += 1
            soilinit_map[soilInit] = response.text
            most_common_soilinit, init_count = soilinit_counter.most_common(1)[0]

            # Check if consensus reached for both soilBase and soilInit
            if (base_count < consensus_count) or (init_count < consensus_count):
                if not is_last_attempt:
                    time.sleep(0.5)
                continue
            
            # Extract soilBase and soilInit consensus elements
            consense_soilinit = soilinit_map[most_common_soilinit]
            consense_soilinit_tree = etree.fromstring(consense_soilinit.encode('utf-8'))

            consense_soilbase = soilbase_map[most_common_soilbase]
            consense_soilbase_tree = etree.fromstring(consense_soilbase.encode('utf-8'))

            # Find SoilBase elements
            soilinit_soilbase_elem = consense_soilinit_tree.find('.//SoilBase')
            consensus_soilbase_elem = consense_soilbase_tree.find('.//SoilBase')
            soilinit_soilbase_elem.getparent().replace(soilinit_soilbase_elem, consensus_soilbase_elem)


            # Consensus reached: save merged response and return
            print(f"Consensus reached for siteinfo at ({lon}, {lat}) after {attempt + 1} attempts.")
            filename = f'siteInfo_{lon}_{lat}.xml'
            consensus_response = etree.tostring(consense_soilinit_tree, encoding='utf-8', xml_declaration=True)

            with open(f'downloaded/{filename}', 'wb') as f:
                f.write(consensus_response)

            with _cache_write_lock:
                with open(download_records, 'a', encoding='utf-8') as cache:
                    cache.write(f'{filename}\n')
                    
            return 

        except requests.RequestException:
            if not is_last_attempt:
                time.sleep(2**attempt)

    return f'{lon}, {lat}', "Failed"



def get_species(lat, lon, try_number=10, download_records='downloaded/successful_downloads.txt'):
    url = f"{BASE_URL_DATA}/2024/data-builder/species"
    PARAMS = {
        "latitude": lat,
        "longitude": lon,
        "area": "OneKm",
        "frCat": "Plantation",
        "specId": 8,  # Eucalyptus globulus, used as Carbon Plantations in LUTO
        "version": 2024
    }

    for attempt in range(try_number):
        is_last_attempt = (attempt == try_number - 1)

        try:
            response = requests.get(url, params=PARAMS, headers=HEADERS, timeout=100)

            # Non-200 status: apply exponential backoff and retry
            if response.status_code != 200:
                if not is_last_attempt:
                    time.sleep(2**attempt)
                continue

            # Success: save and return
            filename = f'species_{lon}_{lat}.xml'
            with open(f'downloaded/{filename}', 'wb') as f:
                f.write(response.content)

            with _cache_write_lock:
                with open(download_records, 'a', encoding='utf-8') as cache:
                    cache.write(f'{filename}\n')
            return

        except requests.RequestException:
            if not is_last_attempt:
                time.sleep(2**attempt)

    return f'{lon},{lat}', "Failed"



def get_plot_simulation(
    data_source:str, 
    lon:float, 
    lat:float, 
    data_obj:xr.Dataset, 
    url:str,
    headers:dict,  
    try_number:int=5, 
    timeout:int=60, 
    download_records:str='downloaded/successful_downloads.txt'
):

    # Re-attempt assembly after redownloading
    for attempt in range(try_number):
        try:
            plo_str = assemble_plo_sections(data_source, lon, lat, data_obj, 'Eucalyptus_globulus', 2010)
                        
            response = requests.post(
                url, 
                files={'file': ('my_plo.plo', plo_str)}, 
                headers=headers,  
                timeout=timeout
            )

            if response.status_code == 200:
                response_df = pd.read_csv(StringIO(response.text))
                response_df.to_csv(f'downloaded/df_{lon}_{lat}.csv', index=False)
                
                # Add the record to cache file
                with _cache_write_lock:
                    with open(download_records, 'a', encoding='utf-8') as cache:
                        cache.write(f'df_{lon}_{lat}.csv\n')
                return 
            
            else:
                # HTTP error - apply backoff before retry
                if attempt < try_number - 1:
                    time.sleep(2**attempt)

        except Exception as e:
            if attempt < try_number - 1:
                time.sleep(2**attempt)
    

# ============================================================================
# SECTION CREATION FUNCTIONS
# ============================================================================

def create_meta_section(
    nmME: str = 'New_Plot',
    savedByResearch: bool = True,
    savedByVersion: str = "",
    lockTime: str = "",
    lockId: str = "",
    lockOnME: str = "",
    notesME: str = ""
) -> str:
    """
    Create Meta section for PLO file with plot metadata.

    The Meta section contains file metadata about the plot including name,
    version information, locking status, and optional notes.

    Parameters
    ----------
    nmME : str
        Plot name shown in FullCAM UI. Required parameter.
        Use descriptive names with dates for tracking.

    savedByResearch : bool, optional
        Whether saved from research UI (default: True).
        - True = Simulates creation from FullCAM web-UI
        - False = Created by desktop application

    savedByVersion : str, optional
        Version of FullCAM that saved it (default: "").
        Empty string "" when created programmatically.

    lockTime : str, optional
        ISO timestamp of last modification (default: "").
        Empty string "" if not locked.

    lockId : str, optional
        User/system ID that locked the file (default: "").
        Empty string "" if not locked.

    lockOnME : str, optional
        Is file currently locked (default: "").
        - "false" or "" for newly created files
        - "true" when file is in use

    notesME : str, optional
        Optional plot notes/description (default: "").
        Empty string or text content.

    Returns
    -------
        XML string for Meta section.
    """
    notes_element = f"<notesME>{notesME}</notesME>" if notesME else "<notesME/>"

    savedByResearch_xml = _bool_to_xml(savedByResearch)

    return (f'<Meta nmME="{nmME}" savedByResearch="{savedByResearch_xml}" '
            f'savedByVersion="{savedByVersion}" lockTime="{lockTime}" '
            f'lockId="{lockId}" lockOnME="{lockOnME}">{notes_element}</Meta>')


def create_config_section(tPlot: str  = "CompF") -> str:
    """
    Create Config section for PLO file with simulation configuration.

    The Config section controls calculation modules, parameters, and the type
    of analysis to be performed.
    

    Parameters
    ----------
    tPlot : str, optional
        Plot type determining analysis type (default: "CompF").

        - "CompF" : Comprehensive Forest System
            Complete multilayer forest simulation with trees, debris, mulch, soil, and products.
            Models: CAMFor (trees), GENDEC (debris), RothC (soil).
            Use for: Full carbon accounting in forestry projects with above/belowground biomass.

        - "SoilF" : Forest Soil Only
            Forest soil analysis without tree/debris layers. RothC runs in standalone mode.
            Use for: Soil carbon dynamics in forested systems without modeling tree growth.

        - "CompA" : Comprehensive Agricultural System
            Complete multilayer agricultural simulation with crops, debris, mulch, soil, and products.
            Models: CAMAg (crops), GENDEC (debris), RothC (soil).
            Use for: Agricultural carbon accounting including crop residues and soil.

        - "SoilA" : Agricultural Soil Only
            Agricultural soil analysis without crop/debris layers. RothC runs in standalone mode.
            Use for: Soil carbon under agricultural management without modeling crops.

        - "CompM" : Mixed/Multilayer System
            Combined forest and agricultural systems with variable mixing over time.
            Use for: Woodland grazing, deforestation/reforestation transitions, agroforestry.
            Note: Forest percentage can vary; systems share climate but have separate irrigation.

    Returns
    -------
        XML string for Config section.
    """
    
    holder_root = etree.parse("data/dataholder_config.xml").getroot()
    holder_root.set('tPlot', tPlot)
    
    return etree.tostring(holder_root).decode('utf-8')


def create_timing_section(
    stYrYTZ: str = "2010",
    enYrYTZ: str = "2100",
    stepsPerYrYTZ: str = "1",
    tStepsYTZ: str = "Yearly",
) -> str:
    """
    Create Timing section for PLO file with simulation timing configuration.

    The Timing section defines the simulation period, time steps, and output
    frequency for the FullCAM model run.

    Parameters
    ----------
    stYrYTZ : str, optional
        Starting year for simulation (default: "2010").
        Must be 4-digit year string. Simulation begins January 1 (or first timestep) of this year.
        Note: Climate time series should cover at least this year (or use extrapolation).

    enYrYTZ : str, optional
        Ending year for simulation (default: "2100").
        Must be 4-digit year string. Simulation ends December 31 (or last timestep) of this year.
        Typical range: 30-90 years for forestry (one rotation to maturity), 10-30 years for agriculture.

    stepsPerYrYTZ : str, optional
        Number of simulation timesteps per year (default: "110").
        Valid values: 1 to 8760 (annual to hourly).
        Common values:
        - "1" = Annual timesteps (fastest; long-term forest projections)
        - "12" = Monthly timesteps (most common for carbon accounting; adequate for most purposes)
        - "52" = Weekly timesteps (detailed crop growth)
        - "110" = ~3.3 day resolution (typical for FullCAM E_globulus simulations)
        - "365" = Daily timesteps (detailed soil moisture/crop modeling)
        - "8760" = Hourly timesteps (research/detailed process studies)
    
    tStepsYTZ : str, optional
        Time step structure within year (default: "Yearly").
        Values:
        - "Yearly" = Single annual timestep (use with stepsPerYrYTZ="1")
        - "Monthly" = 12 monthly timesteps (use with stepsPerYrYTZ="12")
        - "Weekly" = 52 weekly timesteps (use with stepsPerYrYTZ="52")
        Note: Should match stepsPerYrYTZ value for consistency.

    Returns
    -------
        XML string for Timing section.
    """
    
    holder_root = etree.parse("data/dataholder_timing.xml").getroot()
    holder_root.set('stYrYTZ', stYrYTZ)
    holder_root.set('enYrYTZ', enYrYTZ)
    holder_root.set('stepsPerYrYTZ', stepsPerYrYTZ)
    holder_root.set('tStepsYTZ', tStepsYTZ)
    
    return etree.tostring(holder_root).decode('utf-8')


def create_build_section(
    lonBL: float,
    latBL: float,
    frCat: str = "null",
    applyDownloadedData: bool = True,
    areaBL: str = "OneKm",
    frFracBL: str = ""
) -> str:
    """
    Create Build section for PLO file with geographic location configuration.

    The Build section defines the geographic location and spatial parameters
    for data retrieval and averaging.

    Parameters
    ----------
    lonBL : float
        Longitude in decimal degrees. Required parameter.
        Negative = Western hemisphere

    latBL : float
        Latitude in decimal degrees. Required parameter.
        Negative = Southern hemisphere

    frCat : str, optional
        Forest category controlling species availability and calibrations (default: "null").

    applyDownloadedData : bool, optional
        Whether to apply spatial data downloaded from Data Builder API (default: True).
        When True: Use API-downloaded climate, soil, and species data for this location.
        When False: Use manual values or defaults; ignore downloaded data.
        Use for: Set False when using entirely custom/manual data inputs.

    areaBL : str, optional
        Spatial averaging area for climate and soil data (default: "OneKm").

        - "Cell" : Single Grid Cell
            Single cell from spatial data (~100m x 100m, ~1 ha depending on resolution).
            Use for: Precise location data; minimal spatial averaging.
            Note: Uses data from exact coordinates; sensitive to local anomalies.

        - "Hectare" : One Hectare
            1 hectare (10,000 m², 0.01 km²) centered on coordinates.
            Use for: Small plots or trial sites.

        - "OneKm" : One Square Kilometer (DEFAULT, RECOMMENDED)
            100 hectares (1 km²) centered on plot coordinates.
            Use for: Most applications; good balance between representativeness and site-specificity.
            Note: Recommended default for standard carbon accounting projects.

        - "TwoKm" : Two Square Kilometers
            2 km² area for broader spatial averaging.
            Use for: When larger spatial averaging desired to reduce local variability.

        - "ThreeKm" : Three Square Kilometers
            3 km² area for regional-scale averaging.

        - "FiveKm" : Five Square Kilometers
            5 km² area for regional-scale analysis.
            Use for: Regional analysis where fine spatial detail not required.
            Note: Smooths out local variability; more representative of regional conditions.

    frFracBL : str, optional
        Forest fraction of the plot area (default: "").
        Empty string ("") = Automatically calculated from spatial data.
        Value range: "0.0" to "1.0" (0% to 100% forest cover).
        Use for: Mixed systems (CompM) where forest/agricultural proportions need specification.
        Note: Rarely needs manual specification; use default for most cases.

    Returns
    -------
        XML string for Build section.
    """
    return (f'<Build lonBL="{lonBL}" latBL="{latBL}" frCat="{frCat}" '
            f'applyDownloadedData="{_bool_to_xml(applyDownloadedData)}" '
            f'areaBL="{areaBL}" frFracBL="{frFracBL}"/>')


def create_site_section(
    data_source: str = "API",
    lon: float = None,
    lat: float = None,
    data_obj: xr.DataArray = None
) -> str:
    """
    Create Site section for PLO file with site parameters and time series.

    Parameters
    ----------
    data_source (str): Source of site data: "API" or "Cache".
        - "API": Load site data from FULLCAM Data Builder API using provided lon/lat.
        - "Cache": Load site data from local cache files in 'downloaded/' directory.
    lon (float): Longitude of the site.
    lat (float): Latitude of the site.
    data_obj (xr.DataArray): Optional xarray DataArray for site data when using "Cache" mode.
    
    Returns
    -------
    str
        XML string for complete Site section including all TimeSeries.
    
    """
    
    if data_source == "API":        # API Data Mode: Load from downloaded files
        file_path = f'downloaded/siteInfo_{lon}_{lat}.xml'
        with open(file_path, 'r', encoding='utf-8') as f:
            parsed_data = parse_site_data(f.read())

    elif data_source == "Cache":    # Cache Data Mode: Load from local cache (xarray dataset)
        parsed_data = data_obj.sel(x=lon, y=lat, method='nearest', drop=True)
    else:
        raise ValueError(f"data_source '{data_source}' not recognized. Use 'API' or 'Cache'.")
        
        
    # Parse data holder XML 
    holder_root = etree.parse('data/dataholder_site.xml').getroot()
    
    # Extract time series and populate   
    avgAirTemp_values = parsed_data['avgAirTemp'].values.flatten()
    holder_root.xpath(f'.//*[@tInTS="avgAirTemp"]/rawTS')[0].text = ','.join(map(str, avgAirTemp_values))
    holder_root.xpath(f'.//*[@tInTS="avgAirTemp"]/rawTS')[0].set('count', str(len(avgAirTemp_values)))
    
    openPanEvap_values = parsed_data['openPanEvap'].values.flatten()
    holder_root.xpath(f'.//*[@tInTS="openPanEvap"]/rawTS')[0].text = ','.join(map(str, openPanEvap_values))
    holder_root.xpath(f'.//*[@tInTS="openPanEvap"]/rawTS')[0].set('count', str(len(openPanEvap_values)))
    
    rainfall_values = parsed_data['rainfall'].values.flatten()
    holder_root.xpath(f'.//*[@tInTS="rainfall"]/rawTS')[0].text = ','.join(map(str, rainfall_values))
    holder_root.xpath(f'.//*[@tInTS="rainfall"]/rawTS')[0].set('count', str(len(rainfall_values)))
    
    forestProdIx_values = [i for i in parsed_data['forestProdIx'].values.flatten() if not np.isnan(i)]
    holder_root.xpath(f'.//*[@tInTS="forestProdIx"]/rawTS')[0].text = ','.join(map(str, forestProdIx_values))
    holder_root.xpath(f'.//*[@tInTS="forestProdIx"]/rawTS')[0].set('count', str(len(forestProdIx_values)))
    
    
    # Get count
    timeseries_elements = holder_root.findall('.//TimeSeries')
    count = len(timeseries_elements)
    holder_root.set('count', str(count))

    # Set fpiAvgLT and maxAbgMF from parsed data
    fpiAvgLT = parsed_data['fpiAvgLT'].item()
    maxAbgMF = parsed_data['maxAbgMF'].item()
    holder_root.set('fpiAvgLT', str(fpiAvgLT))
    holder_root.set('maxAbgMF', str(maxAbgMF))

    return etree.tostring(holder_root).decode()


def create_species_section(species) -> str:
    '''
    Create the Species section of the PLO file by reading species data
    
    Note: the species XML files are the same for the same species at different locations,
    so lon and lat are not needed as parameters here.
    
    Currently only supports the below species per PLO file.
    - Eucalyptus_globulus
    - Mallee_eucalypt
    - Environmental_plantings
    
    '''
    if species not in ['Eucalyptus_globulus', 'Mallee_eucalypt', 'Environmental_plantings']:
        raise ValueError(f"Species '{species}' not supported. Supported species: "
                         f"'Eucalyptus_globulus', 'Mallee_eucalypt', 'Environmental_plantings'.")
    
    file_path = f'data/dataholder_species_{species}.xml'
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Required file '{file_path}' not found!"
        )
        
    species_root = etree.parse(file_path).getroot().findall('SpeciesForest')
    if len(species_root) != 1:
        raise ValueError(f"Expected one SpeciesForest element in {file_path}, found {len(species_root)}")
    species = etree.tostring(species_root[0], encoding='unicode', pretty_print=True).replace('\n', '')
    
    return (
        f'<SpeciesForestSet count="{len(species_root)}" showOnlyInUse="false">{species}</SpeciesForestSet>'
        f'<SpeciesAgricultureSet count="0" showOnlyInUse="false"/>'
    )


def create_soil_section(
    data_source:str = 'API', 
    lon:float=None, 
    lat:float=None, 
    data_obj:xr.Dataset=None,
    yr0TS:int=None
) -> str:
    '''
    Create the Soil section of the PLO file by replacing the SoilBase and soilCover TimeSeries
    with site-specific data downloaded from the FULLCAM API.
    Parameters:
        data_source (str): Source of site data: "API" or "Cache".
            - "API": Load site data from FULLCAM Data Builder API using provided lon/lat.
            - "Cache": Load site data from local cache files in 'downloaded/' directory.
        lon (float): Longitude of the site.
        lat (float): Latitude of the site.
        data_obj (xr.Dataset): Optional xarray Dataset for site data when using "Cache" mode.
        yr0TS (int): Year to set as yr0TS attribute in TimeSeries elements.
        
    Returns:
        str: The Soil section as an XML string.
    '''
    
    if data_source == "API":        # API Data Mode: Load from downloaded files
        file_path = f'downloaded/siteInfo_{lon}_{lat}.xml'
        with open(file_path, 'r', encoding='utf-8') as f:
            parsed_data = parse_soil_data(f.read())
    elif data_source == "Cache":    # Cache Data Mode: Load from local cache (xarray dataset)
        parsed_data = data_obj.sel(x=lon, y=lat, method='nearest', drop=True).compute()
    else:
        raise ValueError(f"data_source '{data_source}' not recognized. Use 'API' or 'Cache'.")
    
    
    # Read soil template
    holder_soil = etree.parse("data/dataholder_soil.xml").getroot()

    # Update SoilBase element
    #   Currently only need to update the `clayFrac` value
    clayFrac = parsed_data['clayFrac'].item()
    holder_soil.xpath('.//SoilOther')[0].set('clayFrac', str(clayFrac))
    
    # Also, need to update the `yr0TS` attribute of all 'TimeSeries' elements 
    for ts in holder_soil.findall('.//TimeSeries'):
        ts.set('yr0TS', str(yr0TS))
    
        
    return etree.tostring(holder_soil, encoding='unicode')


def create_init_section(
    data_source:str='API', 
    lon: float=None, 
    lat: float=None, 
    data_obj:xr.Dataset=None,
    tsmd_year:int=None
) -> str:
    '''
    Create the Init section of the PLO file by reading siteinfo data and calculating
    soil carbon pool values, then updating dataholder_init.xml with these values.

    Parameters:
        data_source (str): Source of site data: "API" or "Cache".
            - "API": Load site data from FULLCAM Data Builder API using provided lon/lat.
            - "Cache": Load site data from local cache files in 'downloaded/' directory.
        lon (float): Longitude of the site.
        lat (float): Latitude of the site.
        data_obj (xr.Dataset): Optional xarray Dataset for site data when using "Cache" mode.
        tsmd_year (int): Year to use for TSMD initial value extraction.

    Returns:
        str: The Init section as an XML string with updated soil carbon values.
    '''
    
    if data_source == "API":        # API Data Mode: Load from downloaded files
        file_path = f'downloaded/siteInfo_{lon}_{lat}.xml'
        with open(file_path, 'r', encoding='utf-8') as f:
            soil_init = parse_init_data(f.read(), tsmd_year)
    elif data_source == "Cache":    # Cache Data Mode: Load from local cache (xarray dataset)
        soil_init = data_obj.sel(x=lon, y=lat, method='nearest', drop=True).compute()
    else:
        raise ValueError(f"data_source '{data_source}' not recognized. Use 'API' or 'Cache'.")


    # Load the dataholder_init.xml template
    holder_init = etree.parse("data/dataholder_init.xml").getroot()

    # Update InitSoilF element
    init_soil_f = holder_init.xpath('.//InitSoilF')[0]
    # init_soil_f.set('dpmaCMInitF', str(soil_init['dpmaCMInitF']))     # dpmaCMInitF is constantly 0
    # init_soil_f.set('biofCMInitF', str(soil_init['biofCMInitF']))     # biofCMInitF is constantly 0
    # init_soil_f.set('biosCMInitF', str(soil_init['biosCMInitF']))     # biosCMInitF is constantly 0
    init_soil_f.set('rpmaCMInitF', str(soil_init['rpmaCMInitF'].item()))
    init_soil_f.set('humsCMInitF', str(soil_init['humsCMInitF'].item()))
    init_soil_f.set('inrtCMInitF', str(soil_init['inrtCMInitF'].item()))
    init_soil_f.set('TSMDInitF',   str(soil_init['TSMDInitF'].item()))

    # Update InitSoilA element (only TSMD, soil carbon stays empty for agriculture)
    #   TSMDInitA is the same as TSMDInitA
    init_soil_a = holder_init.xpath('.//InitSoilA')[0]
    init_soil_a.set('TSMDInitA', str(soil_init['TSMDInitF'].item()))

    # Return the updated Init section as XML string
    return etree.tostring(holder_init, encoding='unicode')


def create_event_section() -> str:
    """
    Create Event section by reading the raw XML from dataholder_event_block.xml.

    The Event section contains management events such as planting, thinning,
    harvesting, fertilization, and other silvicultural operations. This function
    simply reads and returns the event template as-is.

    Returns
    -------
    str
        The complete EventQ section as an XML string from the dataholder file.
    """
    event_file_path = "data/dataholder_event_block.xml"

    if not os.path.exists(event_file_path):
        raise FileNotFoundError(
            f"Required file '{event_file_path}' not found! "
            f"Ensure dataholder_event_block.xml exists in the data/ directory."
        )

    # Read and return the raw XML content
    with open(event_file_path, 'r', encoding='utf-8') as f:
        return f.read()


def create_outwinset_section() -> str:
    """
    Create OutWinSet section by reading the raw XML from dataholder_OutWinSet.xml.

    The OutWinSet section defines output window configurations for FullCAM GUI display,
    including graph settings, axis parameters, colors, legends, and which carbon pools
    to visualize. This section controls how simulation results are displayed in the
    FullCAM desktop application.

    Returns
    -------
    str
        The complete OutWinSet section as an XML string from the dataholder file.

    Notes
    -----
    This function reads a static template file and does not modify its contents. We just
    need to include this content in the final PLO file.
    """
    outwinset_file_path = "data/dataholder_OutWinSet.xml"

    if not os.path.exists(outwinset_file_path):
        raise FileNotFoundError(
            f"Required file '{outwinset_file_path}' not found! "
            f"Ensure dataholder_OutWinSet.xml exists in the data/ directory."
        )

    # Read and return the raw XML content
    with open(outwinset_file_path, 'r', encoding='utf-8') as f:
        return f.read()


def create_logentryset_section() -> str:
    """
    Create LogEntrySet section by reading the raw XML from dataholder_logentryset.xml.

    The LogEntrySet section contains a chronological log of operations and events that
    occurred during PLO file creation and modification. It tracks configuration changes,
    spatial data downloads, species selections, and document saves with timestamps.
    This section is primarily for debugging and audit trail purposes.

    Returns
    -------
    str
        The complete LogEntrySet section as an XML string from the dataholder file.

    Raises
    ------
    FileNotFoundError
        If dataholder_logentryset.xml is not found in the data/ directory.

    Notes
    -----
    This function reads a static template file and does not modify its contents. We just
    need to include this content in the final PLO file.
    """
    logentryset_file_path = "data/dataholder_logentryset.xml"

    if not os.path.exists(logentryset_file_path):
        raise FileNotFoundError(
            f"Required file '{logentryset_file_path}' not found! "
            f"Ensure dataholder_logentryset.xml exists in the data/ directory."
        )

    # Read and return the raw XML content
    with open(logentryset_file_path, 'r', encoding='utf-8') as f:
        return f.read()


def create_mnrl_mulch_section() -> str:
    """
    Create Mnrl and Mulch sections by reading the raw XML from dataholder_Mnrl_Mulch.xml.

    Returns
    -------
    str
        The complete Mnrl and Mulch sections as XML strings from the dataholder file.
        Includes both <Mnrl>...</Mnrl> and <Mulch>...</Mulch> sections concatenated.

    """
    mnrl_mulch_file_path = "data/dataholder_Mnrl_Mulch.xml"

    if not os.path.exists(mnrl_mulch_file_path):
        raise FileNotFoundError(
            f"Required file '{mnrl_mulch_file_path}' not found! "
            f"Ensure dataholder_Mnrl_Mulch.xml exists in the data/ directory."
        )

    # Read and return the raw XML content
    with open(mnrl_mulch_file_path, 'r', encoding='utf-8') as f:
        return f.read()


def create_other_info_section() -> str:
    """
    Create other information sections (EconInfo, RINSet, SensPkg, etc.) by reading
    the raw XML from dataholder_other_info.xml.

    Returns
    -------
    str
        The complete other information sections as an XML string from the dataholder file.
    """
    other_info_file_path = "data/dataholder_other_info.xml"

    if not os.path.exists(other_info_file_path):
        raise FileNotFoundError(
            f"Required file '{other_info_file_path}' not found! "
            f"Ensure dataholder_other_info.xml exists in the data/ directory."
        )

    # Read and return the raw XML content
    with open(other_info_file_path, 'r', encoding='utf-8') as f:
        return f.read()



def assemble_plo_sections(
    data_source:str='Cache', 
    lon:float=None, 
    lat:float=None, 
    data_obj:xr.Dataset=None,
    species:str='Eucalyptus_globulus', 
    year_start=2010, 
) -> str:
    """Assemble all sections of a PLO file for given lon/lat.

    Parameters
    ----------
    data_source : str, optional
        Source of site data: "API" or "Cache" (default is 'Cache').
        - "API": Load site data from FULLCAM Data Builder API using provided lon/lat.
        - "Cache": Load site data from local cache files in 'downloaded/' directory.
    lon : float
        Longitude of the plot.
    lat : float
        Latitude of the plot.
    data_obj : xr.Dataset, optional
        Optional xarray Dataset for site data when using "Cache" mode.
    species : str, optional
        Species name for the simulation (default is 'Eucalyptus_globulus').
        Currently supported species:
         - 'Eucalyptus_globulus'
         - 'Mallee_eucalypt'
         - 'Environmental_plantings'
    year_start : int, optional
        The starting year for the simulation (default is 2010).
    
    Returns
    -------
    dict
        A dictionary containing all sections of the PLO file as XML strings.
    """
    
    if data_source not in ['API', 'Cache']:
        raise ValueError(f"data_source '{data_source}' not recognized. Use 'API' or 'Cache'.")

    if data_source == 'API':
        site_file = f'downloaded/siteInfo_{lon}_{lat}.xml'
        if not os.path.exists(site_file):
            get_siteinfo(lat, lon)
            print(f'Downloaded site file: {site_file}')

    return (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<DocumentPlot FileType="FullCAM Plot " Version="5009" pageIxDO="10" tDiagram="-1">'
                f'{create_meta_section("My_Plot", notesME="")}\n'
                f'{create_config_section()}\n'
                f'{create_timing_section()}\n'
                f'{create_build_section(lon, lat)}\n'
                f'{create_site_section(data_source, lon, lat, data_obj)}\n'
                f'{create_species_section(species)}\n'
                f'{create_soil_section(data_source, lon, lat, data_obj, year_start)}\n'
                f'{create_init_section(data_source, lon, lat, data_obj, year_start)}\n'
                f'{create_event_section()}\n'
                f'{create_outwinset_section()}\n'
                f'{create_logentryset_section()}\n'
                f'{create_mnrl_mulch_section()}\n'
                f'{create_other_info_section()}\n'
            f'</DocumentPlot>')

