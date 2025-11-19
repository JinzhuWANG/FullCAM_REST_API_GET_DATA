# API Reference

Complete reference for functions, FullCAM API endpoints, and utilities.

## Table of Contents

- [PLO Generation Functions](#plo-generation-functions)
- [Data Extraction Functions](#data-extraction-functions)
- [Cache Management Functions](#cache-management-functions)
- [FullCAM REST API](#fullcam-rest-api)

## PLO Generation Functions

All functions in [tools/plo_section_functions.py](../../tools/plo_section_functions.py)

### Primary Function

#### `assemble_plo_sections(lon, lat, year_start=2010)`

Generate complete PLO file from cached API data.

**Parameters:**
- `lon` (float): Longitude in decimal degrees (required)
- `lat` (float): Latitude in decimal degrees (required)
- `year_start` (int, optional): Simulation start year (default: 2010)

**Returns:** str - Complete PLO XML string ready for simulation

**Raises:**
- `FileNotFoundError`: If required cache files don't exist
  - `downloaded/siteInfo_{lon}_{lat}.xml`
  - `downloaded/species_{lon}_{lat}.xml`

**Example:**
```python
from tools.plo_section_functions import assemble_plo_sections

plo_xml = assemble_plo_sections(lon=148.16, lat=-35.61, year_start=2010)

# Save to file
with open("plot.plo", "w", encoding="utf-8") as f:
    f.write(plo_xml)
```

**Data Requirements:**
- Run `get_data.py` first to populate cache
- Template files in `data/dataholder_*.xml` (8 files)

**What it does internally:**
1. Loads climate time series from `siteInfo_{lon}_{lat}.xml`
2. Loads species parameters from `species_{lon}_{lat}.xml`
3. Calculates initial TSMD (Top Soil Moisture Deficit) for start year
4. Merges with templates from `data/dataholder_*.xml`
5. Assembles 13 sections into complete PLO file
6. Returns XML string with declaration and root wrapper

### Section Creation Functions

All functions return XML fragments (no `<?xml?>` declaration).

#### `create_meta_section(nmME="New_Plot", notesME="")`

Generate Meta section (plot metadata).

**Parameters:**
- `nmME` (str, optional): Plot name (default: "New_Plot")
- `notesME` (str, optional): Plot notes (default: "")

**Returns:** str - XML fragment: `<Meta nmME="..." notesME="..."/>`

**Example:**
```python
meta = create_meta_section("Eucalyptus_Trial", notesME="Commercial plantation test plot")
# Returns: <Meta nmME="Eucalyptus_Trial" notesME="Commercial plantation test plot"/>
```

#### `create_config_section(tPlot="CompF", userN=False, ...)`

Generate Config section (simulation configuration).

**Key Parameters:**
- `tPlot` (str): Plot type - `"CompF"` (forest composite), `"SoilF"` (soil only), `"CompA"` (agricultural), `"CompM"` (mixed)
- `userN` (bool): Enable nitrogen cycling (default: False)
- `useFSI` (bool): Use Forest Succession Index (default: True)
- `userFI` (bool): Use Fire Index (default: False)

**Returns:** str - XML fragment: `<Config tPlot="..." userN="true/false" .../>`

**Example:**
```python
config = create_config_section(tPlot="CompF", userN=True)
# Enables nitrogen cycling for forest composite plot
```

**See:** [PLO Files Guide](plo-files.md#config-section) for all parameters

#### `create_timing_section(stYrYTZ="2000", enYrYTZ="2100", ...)`

Generate Timing section (simulation time parameters).

**Key Parameters:**
- `stYrYTZ` (str): Start year (default: "2000")
- `enYrYTZ` (str): End year (default: "2100")
- `stepsPerYrYTZ` (str): Simulation steps per year (default: "1")
  - `"1"` = annual resolution
  - `"12"` = monthly resolution
  - `"110"` = ~3.3 day resolution (limiting value)
- `stepsPerOutYTZ` (str): Output frequency (default: "1")
  - Controls CSV output frequency independently from simulation resolution
  - `stepsPerOutYTZ="1"` with `stepsPerYrYTZ="12"` → monthly outputs
  - `stepsPerOutYTZ="12"` with `stepsPerYrYTZ="12"` → annual outputs

**Returns:** str - XML fragment: `<Timing stYrYTZ="..." enYrYTZ="..." .../>`

**Example:**
```python
# Monthly simulation, annual outputs
timing = create_timing_section(stYrYTZ="2010", enYrYTZ="2050",
                                stepsPerYrYTZ="12", stepsPerOutYTZ="12")
```

**Important:** `stepsPerYrYTZ` affects simulation accuracy, `stepsPerOutYTZ` affects output file size. See [PLO Files Guide](plo-files.md#simulation-resolution) for details.

#### `create_build_section(lonBL, latBL, frCat="null", areaBL="OneKm")`

Generate Build section (geographic location and spatial parameters).

**Parameters:**
- `lonBL` (float, required): Longitude in decimal degrees
- `latBL` (float, required): Latitude in decimal degrees
- `frCat` (str): Forest category (default: "null")
  - `"Plantation"` - Commercial plantations (use for Eucalyptus globulus)
  - `"MVG"` - Major Vegetation Groups (native forests)
  - `"EnvMallee"` - Environmental plantings
  - `"ERF"` - Emissions Reduction Fund
  - `"null"` - All categories
- `areaBL` (str): Spatial averaging area (default: "OneKm")
  - `"Cell"` - Single grid cell (~100m × 100m)
  - `"Hectare"` - 1 hectare
  - `"OneKm"` - 1 km² (recommended)
  - `"TwoKm"`, `"ThreeKm"`, `"FiveKm"` - Larger areas

**Returns:** str - XML fragment: `<Build lonBL="..." latBL="..." .../>`

**Example:**
```python
build = create_build_section(148.16, -35.61, frCat="Plantation", areaBL="OneKm")
```

**Critical:** Using wrong `frCat` can cause 20-50% errors in carbon predictions. Plantation calibrations differ significantly from MVG calibrations. See [PLO Files Guide](plo-files.md#forest-categories) for details.

#### `create_site_section(lon, lat)`

Generate Site section (climate time series and site parameters).

**Parameters:**
- `lon` (float, required): Longitude (used to locate cache file)
- `lat` (float, required): Latitude (used to locate cache file)

**Returns:** str - XML fragment: `<Site>...</Site>` with embedded `<TimeSeries>` elements

**Data Sources:**
- `downloaded/siteInfo_{lon}_{lat}.xml` - Climate data from API
- `data/dataholder_site.xml` - Template for site parameters

**Raises:** `FileNotFoundError` if cache file doesn't exist

**Example:**
```python
site = create_site_section(148.16, -35.61)
# Loads avgAirTemp, rainfall, openPanEvap, forestProdIx from cache
```

**What it does:**
1. Loads `siteInfo_{lon}_{lat}.xml` from cache
2. Extracts time series: avgAirTemp, rainfall, openPanEvap, forestProdIx
3. Loads template from `data/dataholder_site.xml`
4. Merges time series into template
5. Returns complete Site section with all time series

#### `create_species_section(lon, lat)`

Generate SpeciesForestSet section (species growth parameters).

**Parameters:**
- `lon` (float, required): Longitude
- `lat` (float, required): Latitude

**Returns:** str - XML fragment: `<SpeciesForestSet>...</SpeciesForestSet>`

**Data Source:** `downloaded/species_{lon}_{lat}.xml` (Eucalyptus globulus, specId=8)

**Raises:** `FileNotFoundError` if cache file doesn't exist

**Example:**
```python
species = create_species_section(148.16, -35.61)
# Returns species definition with calibrations for E. globulus
```

**Contains:**
- Growth calibrations (a1spc, a2spc, kxspc, etc.)
- Turnover rates (foliage, fine roots, bark)
- Allocation parameters (stem, branch, foliage)
- Productivity modifiers

#### `create_soil_section(lon, lat, yr0TS)`

Generate Soil section (soil carbon pools and cover).

**Parameters:**
- `lon` (float, required): Longitude
- `lat` (float, required): Latitude
- `yr0TS` (int, required): Base year for time series alignment

**Returns:** str - XML fragment: `<Soil>...</Soil>`

**Data Sources:**
- `downloaded/siteInfo_{lon}_{lat}.xml` - Soil parameters from API
- `data/dataholder_soil.xml` - Template

**Example:**
```python
soil = create_soil_section(148.16, -35.61, yr0TS=2000)
```

#### `create_init_section(lon, lat, tsmd_year)`

Generate Init section (initial carbon pool values).

**Parameters:**
- `lon` (float, required): Longitude
- `lat` (float, required): Latitude
- `tsmd_year` (int, required): Year for TSMD calculation (typically simulation start year)

**Returns:** str - XML fragment: `<Init>...</Init>`

**Data Sources:**
- `downloaded/siteInfo_{lon}_{lat}.xml` - Initial values from API
- `data/dataholder_init.xml` - Template

**What it does:**
- Calculates initial TSMD (Top Soil Moisture Deficit) for specified year
- Uses avgAirTemp, rainfall, openPanEvap time series
- Merges with template initial carbon pools

**Example:**
```python
init = create_init_section(148.16, -35.61, tsmd_year=2010)
# Calculates TSMD for year 2010
```

#### `create_event_section()`

Generate Event section (management events from template).

**Returns:** str - XML fragment: `<RegimeSet>...</RegimeSet>`

**Data Source:** `data/dataholder_event_block.xml`

**Example:**
```python
events = create_event_section()
# Returns template events (typically empty or default events)
```

#### `create_outwinset_section()`

Generate OutWinSet section (GUI output window settings).

**Returns:** str - XML fragment: `<OutWinSet>...</OutWinSet>`

**Data Source:** `data/dataholder_OutWinSet.xml`

#### `create_logentryset_section()`

Generate LogEntrySet section (audit log entries).

**Returns:** str - XML fragment: `<LogEntrySet>...</LogEntrySet>`

**Data Source:** `data/dataholder_logentryset.xml`

#### `create_mnrl_mulch_section()`

Generate Mnrl_Mulch section (nitrogen cycling and mulch layer parameters).

**Returns:** str - XML fragment: `<Mnrl_Mulch>...</Mnrl_Mulch>`

**Data Source:** `data/dataholder_Mnrl_Mulch.xml`

**Note:** Only used when `userN=True` in Config section

#### `create_other_info_section()`

Generate other_info section (economic, sensitivity, optimization settings).

**Returns:** str - XML fragment: `<other_info>...</other_info>`

**Data Source:** `data/dataholder_other_info.xml`

## Data Extraction Functions

Functions in [tools/XML2Data.py](../../tools/XML2Data.py) and [tools/XML2Data_PLO.py](../../tools/XML2Data_PLO.py)

### XML2Data.py (API Cache Files)

#### `parse_siteinfo_data(xml_string: str) -> xr.Dataset`

Parse siteInfo XML and return climate/FPI data as xarray Dataset.

**Parameters:**
- `xml_string` (str): Raw XML content from `siteInfo_{lon}_{lat}.xml`

**Returns:** `xr.Dataset` with variables:
- `avgAirTemp` (year, month): Average air temperature [°C]
- `rainfall` (year, month): Precipitation [mm]
- `openPanEvap` (year, month): Pan evaporation [mm]
- `forestProdIx` (year): Forest Productivity Index [unitless]
- `maxAbgMF`: Maximum aboveground biomass modifier
- `fpiAvgLT`: Long-term average FPI

**Example:**
```python
from tools.XML2Data import parse_siteinfo_data

with open('downloaded/siteInfo_148.16_-35.61.xml', 'r') as f:
    xml_string = f.read()

ds = parse_siteinfo_data(xml_string)
print(ds.avgAirTemp.sel(year=2020, month=1).values)  # Jan 2020 temperature
```

#### `get_siteinfo_data(lat: float, lon: float, year: int = None) -> xr.Dataset`

Load and parse siteInfo file for given coordinates.

**Parameters:**
- `lat` (float): Latitude
- `lon` (float): Longitude
- `year` (int, optional): Extract specific year (returns full range if None)

**Returns:** `xr.Dataset` - Same structure as `parse_siteinfo_data()`

**Raises:** `FileNotFoundError` if cache file doesn't exist

**Example:**
```python
from tools.XML2Data import get_siteinfo_data

# Get all years
ds = get_siteinfo_data(-35.61, 148.16)

# Get single year
ds_2020 = get_siteinfo_data(-35.61, 148.16, year=2020)
```

#### `get_soilbase_data(lat: float, lon: float) -> dict`

Extract soil base parameters from siteInfo file.

**Parameters:**
- `lat` (float): Latitude
- `lon` (float): Longitude

**Returns:** dict with keys:
- `clay_content`: Clay fraction [0-1]
- `silt_content`: Silt fraction [0-1]
- `sand_content`: Sand fraction [0-1]
- `bulk_density`: Soil bulk density [g/cm³]
- `pH`: Soil pH
- `initOMF`: Initial organic matter fraction

**Example:**
```python
from tools.XML2Data import get_soilbase_data

soil = get_soilbase_data(-35.61, 148.16)
print(f"Clay content: {soil['clay_content']:.2%}")
```

#### `get_soilInit_data(lat: float, lon: float, year: int) -> dict`

Extract initial soil carbon pools for given year.

**Parameters:**
- `lat` (float): Latitude
- `lon` (float): Longitude
- `year` (int): Year for initial values

**Returns:** dict with keys:
- `biomC`: Biomass carbon [tC/ha]
- `debC`: Debris carbon [tC/ha]
- `humC`: Humus carbon [tC/ha]
- `soilC`: Total soil carbon [tC/ha]

**Example:**
```python
from tools.XML2Data import get_soilInit_data

init = get_soilInit_data(-35.61, 148.16, year=2010)
print(f"Initial soil C: {init['soilC']:.2f} tC/ha")
```

#### `get_carbon_data(lat: float, lon: float) -> pd.DataFrame`

Load simulation results CSV for given coordinates.

**Parameters:**
- `lat` (float): Latitude
- `lon` (float): Longitude

**Returns:** `pd.DataFrame` with columns:
- `Year`: Simulation year
- `TotalC_tCha`: Total carbon [tC/ha]
- `AboveGround_tCha`: Aboveground carbon [tC/ha]
- `BelowGround_tCha`: Belowground carbon [tC/ha]
- ... (many other carbon pools and fluxes)

**Raises:** `FileNotFoundError` if `downloaded/df_{lat}_{lon}.csv` doesn't exist

**Example:**
```python
from tools.XML2Data import get_carbon_data

df = get_carbon_data(-35.61, 148.16)
print(df[['Year', 'TotalC_tCha']].head())
```

#### `export_to_geotiff_with_band_names(arr, output_path, transform, ...)`

Export xarray DataArray to GeoTIFF with band names.

**Parameters:**
- `arr` (xr.DataArray): Data to export (2D or 3D)
- `output_path` (str): Output file path
- `transform` (affine.Affine): Geospatial transform
- `crs` (str, optional): Coordinate reference system (default: "EPSG:4326")
- `nodata` (float, optional): NoData value (default: -9999.0)

**Example:**
```python
from tools.XML2Data import export_to_geotiff_with_band_names
import xarray as xr
from affine import Affine

arr = xr.DataArray(data, dims=['lat', 'lon'], coords={'lat': lats, 'lon': lons})
transform = Affine(0.1, 0, 110.0, 0, -0.1, -10.0)  # 0.1° resolution

export_to_geotiff_with_band_names(arr, 'output.tif', transform)
```

### XML2Data_PLO.py (PLO Files)

Similar functions but parse PLO XML structure instead of API cache:

- `parse_siteinfo_data(xml_string)` - Parse Site section from PLO
- `get_siteinfo_data(lat, lon, year)` - Load from PLO file
- `get_soilbase_data(lat, lon)` - Extract Soil section
- `get_soilInit_data(lat, lon, year)` - Extract Init section

**Difference:** These functions parse `<DocumentPlot>` XML instead of API response XML.

## Cache Management Functions

Functions in [tools/cache_manager.py](../../tools/cache_manager.py)

#### `get_existing_downloads() -> tuple[set, set, set]`

Read cache index and return sets of existing files.

**Returns:** tuple of 3 sets:
1. `existing_siteinfo` - Set of siteInfo filenames
2. `existing_species` - Set of species filenames
3. `existing_dfs` - Set of simulation CSV filenames

**Example:**
```python
from tools.cache_manager import get_existing_downloads

siteinfo, species, dfs = get_existing_downloads()
print(f"Cached siteInfo files: {len(siteinfo)}")
print(f"Cached species files: {len(species)}")
print(f"Simulation results: {len(dfs)}")
```

#### `rebuild_cache()`

Scan `downloaded/` directory and rebuild cache index.

**Warning:** Slow operation (scans all files). Only run when cache is corrupted or missing.

**Example:**
```bash
python tools/cache_manager.py rebuild
```

**When to use:**
- Cache file deleted
- Manually copied files from another system
- Cache corrupted

#### `verify_cache()`

Check that all files in cache index actually exist on disk.

**Example:**
```bash
python tools/cache_manager.py verify
```

**Output:**
```
Verifying cache integrity...
Checking 50000 siteInfo files...
Checking 50000 species files...
Missing files: 0
Cache integrity: OK
```

## FullCAM REST API

### Authentication

All requests require header:
```python
headers = {"Ocp-Apim-Subscription-Key": os.getenv("FULLCAM_API_KEY")}
```

### Base URLs

```python
DATA_API_BASE = "https://api.dcceew.gov.au/climate/carbon-accounting/2024/data/v1"
SIMULATOR_API_BASE = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1"
```

### Endpoints

#### GET /2024/data-builder/siteinfo

Fetch climate, soil, and species data for coordinates.

**Parameters:**
- `latitude` (float): Latitude in decimal degrees
- `longitude` (float): Longitude in decimal degrees
- `area` (str): Spatial averaging - `"Cell"`, `"Hectare"`, `"OneKm"`, `"TwoKm"`, etc.
- `plotT` (str): Plot type - `"CompF"`, `"SoilF"`, `"CompA"`, etc.
- `frCat` (str): Forest category - `"Plantation"`, `"MVG"`, `"ERF"`, etc.
- `incGrowth` (str): Include growth data - `"true"` or `"false"`
- `version` (int): API version - `2024`

**Returns:** XML with structure:
```xml
<root>
  <SiteInfo>
    <TimeSeries tInTS="avgAirTemp" yr0TS="1900" nYrsTS="201" dataPerYrTS="12">
      <rawTS count="2412">12.5,13.2,...</rawTS>
    </TimeSeries>
    <TimeSeries tInTS="rainfall">...</TimeSeries>
    <TimeSeries tInTS="openPanEvap">...</TimeSeries>
    <TimeSeries tInTS="forestProdIx" dataPerYrTS="1">...</TimeSeries>
  </SiteInfo>
  <LocnSoil clay="0.25" silt="0.35" sand="0.40" ... />
  <ItemList>
    <Item specId="8" speciesNm="Eucalyptus globulus" ... />
  </ItemList>
</root>
```

**Example:**
```python
import requests
import os

API_KEY = os.getenv("FULLCAM_API_KEY")
BASE_URL = "https://api.dcceew.gov.au/climate/carbon-accounting/2024/data/v1"

params = {
    "latitude": -35.61,
    "longitude": 148.16,
    "area": "OneKm",
    "plotT": "CompF",
    "frCat": "Plantation",
    "incGrowth": "false",
    "version": 2024
}

response = requests.get(
    f"{BASE_URL}/2024/data-builder/siteinfo",
    params=params,
    headers={"Ocp-Apim-Subscription-Key": API_KEY},
    timeout=30
)

if response.status_code == 200:
    with open('siteInfo_148.16_-35.61.xml', 'wb') as f:
        f.write(response.content)
```

#### GET /2024/data-builder/species

Fetch species parameters for specific species and location.

**Parameters:**
- `latitude` (float): Latitude
- `longitude` (float): Longitude
- `area` (str): Spatial averaging
- `specId` (int): Species ID (e.g., 8 for Eucalyptus globulus)
- `frCat` (str): Forest category
- `version` (int): API version

**Returns:** XML with `<SpeciesForest>` element containing calibrations

**Example:**
```python
params = {
    "latitude": -35.61,
    "longitude": 148.16,
    "area": "OneKm",
    "specId": 8,  # Eucalyptus globulus
    "frCat": "Plantation",
    "version": 2024
}

response = requests.get(
    f"{BASE_URL}/2024/data-builder/species",
    params=params,
    headers={"Ocp-Apim-Subscription-Key": API_KEY},
    timeout=30
)
```

#### POST /2024/fullcam-simulator/run-plotsimulation

Submit PLO file for simulation and receive results.

**Request:**
- Method: POST
- Content-Type: multipart/form-data
- Body: PLO file as file upload

**Returns:** CSV with carbon stocks/fluxes over time

**Example:**
```python
SIMULATOR_URL = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1"

# Generate or load PLO file
plo_xml = assemble_plo_sections(148.16, -35.61, year_start=2010)

# Submit to simulator
response = requests.post(
    f"{SIMULATOR_URL}/2024/fullcam-simulator/run-plotsimulation",
    files={'file': ('plot.plo', plo_xml)},
    headers={"Ocp-Apim-Subscription-Key": API_KEY},
    timeout=30
)

# Parse CSV results
from io import StringIO
import pandas as pd

df = pd.read_csv(StringIO(response.text))
print(df[['Year', 'TotalC_tCha']].head())
```

**CSV Columns (partial list):**
- `Year`: Simulation year
- `TotalC_tCha`: Total carbon stock [tC/ha]
- `AboveGround_tCha`: Aboveground biomass carbon [tC/ha]
- `BelowGround_tCha`: Belowground biomass carbon [tC/ha]
- `Debris_tCha`: Debris carbon [tC/ha]
- `Soil_tCha`: Soil carbon [tC/ha]
- `NPP_tCha_yr`: Net Primary Productivity [tC/ha/year]
- `NEP_tCha_yr`: Net Ecosystem Productivity [tC/ha/year]

#### GET /2024/data-builder/template

Download pre-configured PLO template files.

**Parameters:**
- `templatePath` (str): Template path (e.g., `"ERF\\Environmental Plantings Method.plo"`)
- `version` (int): API version

**Returns:** Complete PLO file as XML

**Example:**
```python
params = {
    "templatePath": "ERF\\Environmental Plantings Method.plo",
    "version": 2024
}

response = requests.get(
    f"{BASE_URL}/2024/data-builder/template",
    params=params,
    headers={"Ocp-Apim-Subscription-Key": API_KEY},
    timeout=30
)

with open('template.plo', 'wb') as f:
    f.write(response.content)
```

### Rate Limits

**Current Implementation:** No explicit rate limiting in code

**Retry Strategy:**
- Exponential backoff: `2^attempt` seconds (up to 8 attempts)
- Total wait time: 2 + 4 + 8 + 16 + 32 + 64 + 128 = 254 seconds max

**Recommendations:**
- Respect API rate limits (check with DCCEEW)
- Add rate limiting using `time.sleep()` or `ratelimit` package
- Monitor API response headers for rate limit info

### Error Handling

**HTTP Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid parameters
- `401 Unauthorized` - Invalid API key
- `404 Not Found` - Resource doesn't exist
- `429 Too Many Requests` - Rate limit exceeded
- `500 Internal Server Error` - Server error

**Example Error Handling:**
```python
response = requests.get(url, params=params, headers=headers, timeout=30)

if response.status_code == 200:
    # Success
    return response.content
elif response.status_code == 401:
    raise ValueError("Invalid API key. Check FULLCAM_API_KEY environment variable")
elif response.status_code == 429:
    raise Exception("Rate limit exceeded. Wait before retrying")
else:
    raise Exception(f"API error: {response.status_code} - {response.text}")
```

## Related Documentation

- **[Architecture Guide](architecture.md)** - System design and data flow
- **[PLO Files Guide](plo-files.md)** - XML structure and validation
- **[Development Guide](development.md)** - Common workflows and patterns
