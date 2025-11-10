# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository provides tools for interacting with the **FullCAM (Full Carbon Accounting Model) REST API** and programmatically generating **PLO (Plot) files** for carbon accounting simulations in forestry and land use sectors.

**FullCAM** is Australia's official carbon accounting model maintained by the Department of Climate Change, Energy, the Environment and Water (DCCEEW). This codebase enables:
1. Fetching site data, climate time series, and templates from the FullCAM API
2. Programmatically assembling PLO files from scratch or API data
3. Running plot simulations via the FullCAM Simulator API

## FullCAM Documentation

**For detailed information about FullCAM model parameters, PLO file structure, and configuration options, refer to:**

[tools/FullCAM_Documentation_Complete.html](tools/FullCAM_Documentation_Complete.html)

This comprehensive HTML documentation contains:
- Complete PLO file format specifications
- Detailed parameter descriptions and valid ranges
- XML element attributes and their meanings
- Model configuration options and their effects
- Time series data requirements
- Species and regime configuration details

When working with PLO files or understanding parameter settings, **always consult this documentation** for authoritative information about parameter meanings, valid values, and proper usage.

## Architecture

### Three-Module Design

The codebase consists of three primary Python modules with distinct responsibilities:

1. **`get_data.py`** - Bulk API data download for Australian locations
   - Fetches site information and species data across all Australian coordinates
   - Uses LUTO land use raster (`data/lumap.tif`) to identify valid coordinates at 5x downsampled resolution
   - Parallel processing with 35 concurrent threads for efficient bulk downloads
   - Includes retry logic with exponential backoff (up to 8 attempts per request)
   - Downloads two types of data:
     - `siteInfo_{lon}_{lat}.xml`: Climate time series, soil data, FPI values
     - `species_{lon}_{lat}.xml`: Eucalyptus globulus (specId=8) species parameters for Plantation category
   - **Intelligent caching system** using `downloaded/successful_downloads.txt`:
     - Logs all successful downloads to a text file (one filename per line)
     - Fast startup: Reads cache file (seconds) instead of scanning millions of files (minutes/hours)
     - Thread-safe append operations for concurrent downloads
     - Automatic resume on interruption (no state loss)
     - See [CACHE_USAGE.md](CACHE_USAGE.md) for detailed documentation
   - Saves all API responses to `downloaded/` directory
   - Skips already-downloaded coordinates based on cache file
   - Primary use: Pre-populate data cache for large-scale spatial modeling projects

2. **`tools/plo_section_functions.py`** - Complete PLO file generation from cached data
   - **Section creation functions** for each PLO XML section:
     - `create_meta_section()`: Plot metadata and notes
     - `create_config_section()`: Simulation configuration flags
     - `create_timing_section()`: Start/end years, time steps, output frequency
     - `create_build_section()`: Geographic location and spatial parameters
     - `create_site_section()`: Site parameters with time series (loads from `downloaded/`)
     - `create_species_section()`: Species parameters (loads from `downloaded/`)
     - `create_soil_section()`: Soil carbon pools and cover (loads from `downloaded/`)
     - `create_init_section()`: Initial conditions for carbon pools
     - `create_event_section()`: Management events (reads from dataholder template)
     - `create_outwinset_section()`: GUI output window settings
     - `create_logentryset_section()`: Audit log entries
     - `create_mnrl_mulch_section()`: Nitrogen cycling and mulch layer parameters
     - `create_other_info_section()`: Economic, sensitivity, optimization settings
   - **Assembly function**: `assemble_plo_sections(lon, lat, year_start=2010)`
     - Takes coordinates and start year
     - Loads site-specific data from `downloaded/` directory
     - Loads template data from `data/dataholder_*.xml` files
     - Returns complete PLO file as XML string ready for simulation
   - All functions include comprehensive NumPy-style docstrings
   - Enhanced documentation on calibrations, convergence, nitrogen cycling, irrigation modes
   - Critical guidance on forest category selection and its impact on carbon predictions

3. **`get_PLO.py`** - PLO generation and simulation workflow
   - Generates PLO file using `assemble_plo_sections()` from `tools/plo_section_functions.py`
   - Submits PLO to FullCAM Simulator API for carbon accounting simulation
   - Receives CSV results with carbon stock/flux time series
   - Saves simulation results to `data/plot_simulation_response.csv`
   - Demonstrates end-to-end workflow: coordinates → PLO file → simulation → results
   - Primary use: Single-plot simulation from cached data

### Project Structure

```
.
├── get_data.py                                 # Bulk API data download script (Australian coordinates)
├── get_PLO.py                                  # PLO generation and simulation workflow
├── README.md                                   # User-facing documentation
├── CLAUDE.md                                   # Developer guide (this file)
├── .gitignore                                  # Git ignore patterns
├── data/                                       # Template XML files and example data
│   ├── dataholder_site.xml                     # Site section template
│   ├── dataholder_soil.xml                     # Soil section template
│   ├── dataholder_init.xml                     # Init section template
│   ├── dataholder_event_block.xml              # Event section template
│   ├── dataholder_OutWinSet.xml                # GUI output window template
│   ├── dataholder_logentryset.xml              # Log entries template
│   ├── dataholder_Mnrl_Mulch.xml               # Nitrogen/Mulch template
│   ├── dataholder_other_info.xml               # Economic/Sensitivity/Optimization template
│   ├── E_globulus_2024.plo                     # Example Eucalyptus plot
│   ├── plot_simulation_response.csv            # Simulation results CSV
│   ├── lumap.tif                               # LUTO land use raster (coordinate source)
│   ├── siteinfo_response.xml                   # Example API response (site info)
│   ├── species_response.xml                    # Example API response (species)
│   └── single_template_response.xml            # Example API response (template)
├── downloaded/                                 # Cached API responses for all Australian locations
│   ├── siteInfo_{lon}_{lat}.xml                # Climate, soil, FPI data (thousands of files)
│   ├── species_{lon}_{lat}.xml                 # Species parameters (thousands of files)
│   ├── successful_downloads.txt                # Cache file tracking all successful downloads
│   └── simulation/                             # Simulation results
│       └── df_{lat}_{lon}.csv                  # Carbon stock/flux time series per location
└── tools/                                      # PLO generation library and utilities
    ├── plo_section_functions.py                # Complete PLO file generation module
    ├── cache_manager.py                        # Cache file management utilities
    ├── copy_files.py                           # Utility to copy downloaded files between directories
    ├── FullCAM_Documentation_Complete.html     # Official FullCAM docs
    └── get_fullcam_help.py                     # Helper script for documentation

```

### PLO Generation Approach

**The project uses a data-driven approach that combines cached API data with XML templates:**

1. **Pre-download data** using `get_data.py` (one-time setup for large areas)
2. **Generate PLO files** using `assemble_plo_sections()` which:
   - Loads site-specific data from `downloaded/siteInfo_{lon}_{lat}.xml` and `species_{lon}_{lat}.xml`
   - Merges with XML templates from `data/dataholder_*.xml` files
   - Returns complete, simulation-ready PLO file

**Quick Example - Generate PLO for a single location:**
```python
from tools.plo_section_functions import assemble_plo_sections

# Generate complete PLO file from cached data
lon, lat = 148.16, -35.61
year_start = 2010

plo_xml = assemble_plo_sections(lon, lat, year_start)

# Save to file (optional)
with open("my_plot.plo", "w", encoding="utf-8") as f:
    f.write(plo_xml)
```

**What `assemble_plo_sections()` does internally:**
- Calls 13 section creation functions in sequence
- Loads climate time series (avgAirTemp, rainfall, openPanEvap, forestProdIx) from API cache
- Populates soil carbon pools from siteinfo data
- Calculates initial TSMD (Top Soil Moisture Deficit) for specified start year
- Merges species parameters (growth calibrations, turnover rates, allocation)
- Includes management events, nitrogen cycling, and GUI configuration from templates
- Returns complete `<?xml version...><DocumentPlot>...</DocumentPlot>` string

**Advanced - Customize individual sections:**
```python
from tools.plo_section_functions import (
    create_meta_section,
    create_config_section,
    create_build_section,
    create_site_section,
    # ... other section functions
)

# Override specific sections with custom parameters
meta = create_meta_section("Custom_Plot_Name", notesME="My research plot")
config = create_config_section(tPlot="CompF", userN=True)  # Enable nitrogen cycling
build = create_build_section(lon, lat, frCat="Plantation", areaBL="FiveKm")

# Load site data from cache (requires lon/lat parameters)
site = create_site_section(lon, lat)

# Manually assemble if needed (see assemble_plo_sections() for full example)
```

This approach provides:
- **Efficiency**: Reuse cached API data for millions of plots without repeated API calls
- **Consistency**: All plots use same XML structure and parameter defaults
- **Flexibility**: Override any section with custom parameters when needed
- **Documentation**: Comprehensive docstrings explain every parameter's effect on carbon simulation

## PLO File Structure

PLO files are XML documents with the following hierarchy:
```
DocumentPlot (root)
├── Meta (plot metadata, name, notes)
├── Config (simulation configuration flags)
├── Timing (start/end years, time steps, output frequency)
├── Build (geographic location, spatial parameters)
├── Site (site-level parameters)
│   └── TimeSeries[] (climate/productivity data arrays)
├── SpeciesForestSet (optional)
│   └── SpeciesForest[] (species definitions)
└── RegimeSet (optional)
    └── Regime[] (management events)
```

### Critical XML Attributes

**IMPORTANT - Understanding Calibrations:**

Calibrations are statistically fitted parameters that control tree growth and biomass allocation in FullCAM. They represent the "recipe" for species behavior under specific conditions. Different forest categories use fundamentally different calibrations:

- **Plantation calibrations**: Fitted to commercial forestry data (intensive management, fast growth, high stem allocation, optimized spacing, 100% light capture)
- **MVG (native) calibrations**: Fitted to natural forest data (natural competition, slower growth, lower stem allocation, endemic canopy cover)

**Using wrong calibrations can result in 20-50% errors in carbon predictions.** For example, using native forest calibrations for a commercial eucalyptus plantation will systematically underestimate biomass by ~30% over the rotation period.

**For commercial Eucalyptus globulus plantations → Always use `frCat="Plantation"`**

**Plot Types (`tPlot` in Config):**
- `CompF` - Forest Composite (above & below ground biomass)
- `SoilF` - Forest soil analysis only
- `CompA` - Agricultural Composite
- `SoilA` - Agricultural soil only
- `CompM` - Mixed forest/agricultural

**Forest Categories (`frCat` in Build):**
- `null` - All categories
- `Plantation` - Commercial plantation species
- `MVG` - Major Vegetation Groups (native)
- `EnvMallee` - Environmental plantings
- `ERF` - Emissions Reduction Fund methods
- `ERFH` - ERF with EMP-specific calibrations

**Spatial Averaging (`areaBL` in Build):**
- `Cell` - Single grid cell (~100m × 100m)
- `Hectare` - 1 hectare
- `OneKm` - 1 km² (default, good for most cases)
- `TwoKm`, `ThreeKm`, `FiveKm` - Larger averaging areas

**IMPORTANT - Simulation Resolution vs Output Frequency:**

Two independent parameters control simulation behavior in the Timing section:

1. **`stepsPerYrYTZ`** - INTERNAL SIMULATION RESOLUTION (how many times per year carbon moves between pools)
   - Common values: "1" (annual), "12" (monthly), "110" (~3.3 day resolution)
   - Higher values approach "limiting values" where further increases produce identical outputs
   - For typical forest carbon accounting with annual/monthly climate data, `stepsPerYrYTZ="1"` vs `stepsPerYrYTZ="110"` often produce the same annual carbon stocks

2. **`stepsPerOutYTZ`** - OUTPUT FREQUENCY (how often results are written to CSV)
   - Controls output file size independently from simulation accuracy
   - Examples:
     - `stepsPerYrYTZ="12"`, `stepsPerOutYTZ="1"` → Simulate monthly, output monthly (12 rows/year)
     - `stepsPerYrYTZ="12"`, `stepsPerOutYTZ="12"` → Simulate monthly, output annually (1 row/year)
     - `stepsPerYrYTZ="110"`, `stepsPerOutYTZ="110"` → Simulate 110 steps/year, output annually (1 row/year)

**Key insight:** Increasing `stepsPerYrYTZ` without adjusting `stepsPerOutYTZ` may not change outputs because you're still only outputting at the same frequency. To see finer-resolution outputs, adjust both parameters.

### Time Series Types

Time series data (`TimeSeries` elements) represent temporal climate/productivity parameters. Common types (`tInTS` attribute):

| Type | Description | Unit | Frequency |
|------|-------------|------|-----------|
| `avgAirTemp` | Average air temperature | °C | Monthly (12/year) |
| `rainfall` | Precipitation | mm | Monthly |
| `openPanEvap` | Pan evaporation | mm | Monthly |
| `forestProdIx` | Forest Productivity Index | unitless | Annual (1/year) |
| `VPD` | Vapor Pressure Deficit | kPa | Monthly |
| `soilTemp` | Soil temperature | °C | Monthly |
| `solarRad` | Solar radiation | MJ/m² | Monthly |
| `fertility` | Soil fertility modifier | unitless | Monthly |
| `conditIrrigF` | Conditional irrigation (forest) | mm | Monthly |
| `defnitIrrigA` | Definite irrigation (agriculture) | mm | Monthly |

## FullCAM API Integration

### API Configuration

**Base URLs:**
- Data/Templates API: `https://api.dcceew.gov.au/climate/carbon-accounting/2024/data/v1`
- Simulation API: `https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1`

**Authentication:**
All requests require header: `Ocp-Apim-Subscription-Key: YOUR_API_KEY`

The API key is read from the `FULLCAM_API_KEY` environment variable in `get_data.py`. The script will raise a `ValueError` if this environment variable is not set.

### API Workflow

**Standard workflow for creating and running a plot:**

1. **Fetch Site Info** (`/2024/data-builder/siteinfo`)
   - Retrieves climate time series, soil data, species lists for coordinates
   - Parameters: `latitude`, `longitude`, `area`, `plotT`, `frCat`, `incGrowth`
   - Returns: XML with `<SiteInfo>`, `<LocnSoil>`, `<TimeSeries>`, `<ItemList>` elements

2. **Get Templates** (optional, `/2024/data-builder/template`)
   - Download pre-configured PLO templates (e.g., "ERF\Environmental Plantings Method.plo")
   - Useful for complex scenarios with species/regime configurations

3. **Build PLO File**
   - Use API data + section functions to construct custom PLO
   - OR modify downloaded template

4. **Run Simulation** (`/2024/fullcam-simulator/run-plotsimulation`)
   - POST PLO file as multipart form data
   - Returns: CSV with carbon stock/flux time series

### XML Parsing Pattern

The codebase uses `lxml.etree` for XML parsing. Standard pattern:
```python
from lxml import etree

root = etree.fromstring(response.content)

# Find element by XPath
site_elem = root.find('.//SiteInfo')
metadata = dict(site_elem.attrib)

# Find specific TimeSeries
ts_elem = root.find(".//TimeSeries[@tInTS='avgAirTemp']")
raw_data = ts_elem.find('rawTS').text.split(',')
```

## Development Commands

### Running Scripts

**Download bulk API data (one-time setup for Australian locations):**
```bash
python get_data.py
```
- Fetches site info and species data for all Australian locations
- Uses LUTO land use raster (`data/lumap.tif`) at 5x downsampled resolution
- Parallel processing with 35 concurrent threads
- Includes exponential backoff retry logic (up to 8 attempts per request)
- **Intelligent caching**: Logs successful downloads to `downloaded/successful_downloads.txt`
  - Fast resume on interruption (reads cache file in seconds vs scanning millions of files)
  - Thread-safe logging for concurrent downloads
  - See [CACHE_USAGE.md](CACHE_USAGE.md) for details
- Saves to `downloaded/` directory: `siteInfo_{lon}_{lat}.xml` and `species_{lon}_{lat}.xml`
- Skips already-downloaded coordinates based on cache file
- Requires valid API key in `FULLCAM_API_KEY` environment variable
- Note: This is a long-running script for large-scale spatial modeling (thousands of locations)

**Generate PLO file and run simulation:**
```bash
python get_PLO.py
```
- Generates complete PLO file using `assemble_plo_sections()` from `tools/plo_section_functions.py`
- Uses cached data from `downloaded/` directory for specified coordinates
- Submits PLO to FullCAM Simulator API
- Saves simulation results to `data/plot_simulation_response.csv`
- Edit coordinates in script to change location (default: lon=148.16, lat=-35.61)

**Copy downloaded files between directories:**
```bash
python tools/copy_files.py
```
- Utility to copy downloaded API responses from network drive to local machine
- Uses parallel processing for fast file transfers
- Skips files that already exist in destination
- Edit `dir_from` and `dir_to` variables in script to change source/destination paths

**Rebuild cache file (if needed):**
```bash
python tools/cache_manager.py rebuild
```
- Scans `downloaded/` directory and recreates `successful_downloads.txt`
- Use when: cache file deleted, manually copied files, or cache corrupted
- One-time slow operation (scans all files), but cache provides fast startup afterward

**Verify cache integrity:**
```bash
python tools/cache_manager.py verify
```
- Checks that all files in cache actually exist on disk
- Reports missing files and cache statistics
- Use for diagnostics or after moving files between systems

### File Locations

**Downloaded API cache:** `downloaded/` directory contains thousands of XML files (siteInfo and species data)
**Cache index:** `downloaded/successful_downloads.txt` tracks all successfully downloaded files
**Simulation results:** `downloaded/simulation/df_{lat}_{lon}.csv` contains carbon stock/flux time series per location
**Template XML files:** `data/` directory contains dataholder_*.xml templates used by section functions
**Documentation:** `tools/` directory contains FullCAM documentation HTML and helper scripts
**PLO generation library:** `tools/plo_section_functions.py` contains all section creation functions
**Cache management:** `tools/cache_manager.py` provides cache rebuild and verification utilities
**Generated PLO files:** Created in-memory by `assemble_plo_sections()` (save to file if needed)

## Important Implementation Details

### Required vs Optional Parameters

When creating PLO section functions, the design principle is:
1. **Required parameters come first** (no default value)
2. **Optional parameters follow** (with default empty string or sensible value)

Example:
```python
def create_build_section(
    lonBL, latBL,              # Required: coordinates
    frCat="null",              # Optional with default
    areaBL="OneKm",            # Optional with default
    applyDownloadedData="true" # Optional with default
):
```

### XML Generation Rules

1. **No HEAD in section functions** - The XML declaration (`<?xml version...?>`) and `<DocumentPlot>` root wrapper are added manually when assembling the complete PLO file
2. **All boolean attributes are strings** - Use `"true"/"false"`, not Python booleans. Section functions handle conversion automatically via `_bool_to_xml()` helper
3. **Empty attributes use empty strings** - `lockTime=""` not `lockTime=None`
4. **TimeSeries count must match** - The `count` attribute in `<rawTS>` must equal the number of comma-separated values
5. **Section functions return XML fragments** - Each `create_*_section()` function returns only the section XML, not a complete document

### Time Series Data Format

Time series values are stored as comma-separated strings in `<rawTS>` elements:
- Missing data: empty string between commas (e.g., `"1.5,,2.3"`)
- Must specify: `yr0TS` (start year), `nYrsTS` (num years), `dataPerYrTS` (points per year)
- Total values should equal `nYrsTS * dataPerYrTS`

### API Response Handling

API responses are XML. To convert TimeSeries to pandas DataFrame:
```python
import pandas as pd

# Parse metadata
metadata = dict(ts_elem.attrib)
start_year = int(metadata['yr0TS'])
data_per_year = int(metadata['dataPerYrTS'])

# Parse data
raw_ts = ts_elem.find('rawTS')
data = [float(x.strip()) for x in raw_ts.text.split(',') if x.strip()]

# Create DataFrame
if data_per_year == 12:  # Monthly
    dates = pd.date_range(start=f'{start_year}-01', periods=len(data), freq='MS')
    df = pd.DataFrame({'date': dates, 'value': data})
elif data_per_year == 1:  # Annual
    years = range(start_year, start_year + len(data))
    df = pd.DataFrame({'year': years, 'value': data})
```

## Version Compatibility

**FullCAM Versions:**
- `5007` - FullCAM 2020 PR format
- `5009` - FullCAM 2024 PR format (current default)

Set version in the `<DocumentPlot version="5009">` root element when assembling PLO files. API endpoints use `/2024/` in the path for current version.

## Common Patterns

### Pattern: Parallel Bulk Data Download

```python
import rioxarray as rio
from joblib import Parallel, delayed
from tqdm.auto import tqdm
import time
import requests

# Load Australian coordinates from NLUM raster
Aus_xr = rio.open_rasterio("data/NLUM_2010-11_clip.tif").sel(band=1, drop=True).compute() > 0
lon_lat = Aus_xr.to_dataframe(name='mask').reset_index().query('mask == True')[['x', 'y']].round({'x':2, 'y':2})

# Define retry function with exponential backoff
def get_siteinfo(idx, lat, lon, try_number=10):
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

    for attempt in range(try_number):
        try:
            response = requests.get(url, params=PARAMS, headers=HEADERS, timeout=100)
            if response.status_code == 200:
                with open(f'downloaded/siteInfo_{lon}_{lat}.xml', 'wb') as f:
                    f.write(response.content)
                return idx, 'Success'
            else:
                if attempt < try_number - 1:
                    time.sleep(2**attempt)
        except requests.RequestException:
            if attempt < try_number - 1:
                time.sleep(2**attempt)

    return idx, "Failed"

# Create parallel tasks
tasks = [delayed(get_siteinfo)(idx, lat, lon)
         for idx, lat, lon in zip(lon_lat.index, lon_lat['y'], lon_lat['x'])]

# Execute with progress bar (50 concurrent threads)
status = []
for rtn in tqdm(Parallel(n_jobs=50, backend='threading', return_as='generator')(tasks), total=len(tasks)):
    idx, msg = rtn
    if msg != 'Success':
        print(idx, msg)
    status.append(rtn)
```

This pattern demonstrates:
- Loading Australian coordinates from geospatial raster data
- Parallel API requests with configurable concurrency (50 threads)
- Exponential backoff retry logic (2^attempt seconds)
- Progress tracking with tqdm
- Robust error handling for network failures

### Pattern: Build PLO from API Data

```python
from lxml import etree
import requests
import os
from plo_section_functions import (
    create_meta_section,
    create_build_section,
    create_config_section,
    create_timing_section,
    create_timeseries,
    create_site_section
)

# 1. Fetch site data
BASE_URL = "https://api.dcceew.gov.au/climate/carbon-accounting/2024/data/v1"
API_KEY = os.getenv("FULLCAM_API_KEY")

response = requests.get(
    f"{BASE_URL}/2024/data-builder/siteinfo",
    params={"latitude": -35.61, "longitude": 148.16, "area": "OneKm", "plotT": "CompF"},
    headers={"Ocp-Apim-Subscription-Key": API_KEY}
)
root = etree.fromstring(response.content)

# 2. Extract time series
ts_list = []
for ts_elem in root.findall('.//TimeSeries'):
    ts_type = ts_elem.get('tInTS')
    raw_data = ts_elem.find('rawTS').text
    ts_list.append(create_timeseries(
        tInTS=ts_type,
        rawTS_values=raw_data,
        yr0TS=ts_elem.get('yr0TS'),
        nYrsTS=ts_elem.get('nYrsTS'),
        dataPerYrTS=ts_elem.get('dataPerYrTS')
    ))

# 3. Build sections
meta = create_meta_section("API_Generated_Plot")
config = create_config_section(tPlot="CompF")
timing = create_timing_section(stYrYTZ="2020", enYrYTZ="2050")
build = create_build_section(148.16, -35.61)
site = create_site_section(len(ts_list), ts_list)

# 4. Assemble and save
plo_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<DocumentPlot version="5009">
{meta}
{config}
{timing}
{build}
{site}
</DocumentPlot>'''

with open("api_plot.plo", "w", encoding="utf-8") as f:
    f.write(plo_content)
```

### Pattern: Batch Processing Multiple Plots

```python
import pandas as pd
from plo_section_functions import (
    create_meta_section,
    create_build_section,
    create_config_section,
    create_timing_section
)

locations_df = pd.read_csv("plot_locations.csv")
# CSV columns: name, latitude, longitude, start_year, end_year

for idx, row in locations_df.iterrows():
    # Create sections
    meta = create_meta_section(row['name'])
    config = create_config_section(tPlot="CompF")
    timing = create_timing_section(
        stYrYTZ=str(row['start_year']),
        enYrYTZ=str(row['end_year'])
    )
    build = create_build_section(row['longitude'], row['latitude'])
    site = create_site_section(0, [])  # Empty site for template

    # Assemble PLO
    plo_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<DocumentPlot version="5009">
{meta}
{config}
{timing}
{build}
{site}
</DocumentPlot>'''

    # Save to file
    with open(f"{row['name']}.plo", "w", encoding="utf-8") as f:
        f.write(plo_content)
```

### Pattern: Create Helper Function for PLO Assembly

Since there's no built-in `assemble_plo_full()` function, you may want to create a helper:

```python
def assemble_plo(meta, config, timing, build, site, version="5009"):
    """
    Assemble complete PLO file from section components.

    Parameters
    ----------
    meta : str
        Meta section XML
    config : str
        Config section XML
    timing : str
        Timing section XML
    build : str
        Build section XML
    site : str
        Site section XML (with TimeSeries)
    version : str, optional
        FullCAM version number (default: "5009")

    Returns
    -------
    str
        Complete PLO XML document
    """
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<DocumentPlot version="{version}">
{meta}
{config}
{timing}
{build}
{site}
</DocumentPlot>'''

def save_plo(content, filepath):
    """Save PLO content to file with UTF-8 encoding."""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

# Usage
meta = create_meta_section("My_Plot")
config = create_config_section()
timing = create_timing_section()
build = create_build_section(148.16, -35.61)
site = create_site_section(0, [])

plo = assemble_plo(meta, config, timing, build, site)
save_plo(plo, "my_plot.plo")
```

## Function Reference

### Assembly Function (Primary Entry Point)

**`assemble_plo_sections(lon, lat, year_start=2010)`** - Complete PLO file generation
- **Required Parameters:** `lon` (longitude), `lat` (latitude)
- **Optional Parameters:** `year_start` (simulation start year, default: 2010)
- **Returns:** Complete PLO XML string ready for simulation
- **Data Sources:**
  - Loads from `downloaded/siteInfo_{lon}_{lat}.xml` (climate, soil, FPI)
  - Loads from `downloaded/species_{lon}_{lat}.xml` (species parameters)
  - Loads from `data/dataholder_*.xml` (template sections)
- **Usage:** Primary function for generating PLO files from cached data
- **Raises:** `FileNotFoundError` if required downloaded files missing

### Section Creation Functions

All section creation functions in `tools/plo_section_functions.py` follow these design principles:
- Required parameters come first (no defaults)
- Optional parameters follow (with sensible defaults)
- Most functions load data from `downloaded/` or `data/` directories
- Return XML string fragments (no XML declaration or root wrapper)
- Include comprehensive NumPy-style docstrings

**Available Functions (called internally by `assemble_plo_sections()`):**

| Function | Required Parameters | Data Source | Purpose |
|----------|--------------------|--------------| ---------|
| `create_meta_section()` | `nmME` (plot name, default: "New_Plot") | Manual/defaults | Plot metadata and notes |
| `create_config_section()` | None (all optional) | Defaults | Simulation configuration flags |
| `create_timing_section()` | None (all optional) | Defaults | Start/end years, time steps |
| `create_build_section()` | `lonBL`, `latBL` | Manual | Geographic location |
| `create_site_section()` | `lon`, `lat` | `downloaded/siteInfo_{lon}_{lat}.xml` + `data/dataholder_site.xml` | Site parameters with time series |
| `create_species_section()` | `lon`, `lat` | `downloaded/species_{lon}_{lat}.xml` | Species growth calibrations |
| `create_soil_section()` | `lon`, `lat`, `yr0TS` | `downloaded/siteInfo_{lon}_{lat}.xml` + `data/dataholder_soil.xml` | Soil carbon pools and cover |
| `create_init_section()` | `lon`, `lat`, `tsmd_year` | `downloaded/siteInfo_{lon}_{lat}.xml` + `data/dataholder_init.xml` | Initial carbon pool values |
| `create_event_section()` | None | `data/dataholder_event_block.xml` | Management events template |
| `create_outwinset_section()` | None | `data/dataholder_OutWinSet.xml` | GUI output window settings |
| `create_logentryset_section()` | None | `data/dataholder_logentryset.xml` | Audit log entries |
| `create_mnrl_mulch_section()` | None | `data/dataholder_Mnrl_Mulch.xml` | Nitrogen cycling and mulch |
| `create_other_info_section()` | None | `data/dataholder_other_info.xml` | Economic/sensitivity/optimization |

**Note:** Most functions require pre-downloaded data from `get_data.py`. Run `get_data.py` first to populate the `downloaded/` directory before generating PLO files.

### Troubleshooting Common Issues

**Issue: "Invalid coordinate values"**
- Ensure latitude is between -90 and 90, longitude between -180 and 180

**Issue: "XML parsing error"**
- Check that all special characters are properly escaped
- Verify all boolean attributes use strings ("true"/"false")

**Issue: "Time series count mismatch"**
- The `count` attribute in `<rawTS>` must equal number of values
- Total values should equal `nYrsTS * dataPerYrTS`

**Issue: "PLO file not recognized by FullCAM"**
- Check version matches FullCAM installation (5007 for 2020, 5009 for 2024)
- Verify all required sections are present (Meta, Config, Timing, Build, Site)
- Ensure XML is well-formed

## Dependencies

The codebase requires:
- `requests` - HTTP requests to FullCAM API
- `lxml` - XML parsing and generation
- `pandas` - Data manipulation and CSV handling (simulation results)
- `rioxarray` - Geospatial raster data handling (LUTO coordinate extraction in `get_data.py`)
- `xarray` - Raster data manipulation (used with rioxarray)
- `numpy` - Numerical operations (array handling)
- `joblib` - Parallel processing for bulk API calls and file copying
- `tqdm` - Progress bars for long-running operations
- `scandir_rs` - Fast directory scanning (used in `copy_files.py`)
- `shutil` - File operations (used in `copy_files.py`)
- `os`, `time`, `re` - Standard library modules

No requirements.txt exists. Typical installation:
```bash
pip install requests lxml pandas rioxarray xarray numpy joblib tqdm scandir_rs
```

**Note:** `scandir_rs` is only needed for `copy_files.py` utility script. Core PLO generation functionality (get_data.py, get_PLO.py, plo_section_functions.py) works without it.

## Important Constraints

1. **API Key Security**: The API key is read from the `FULLCAM_API_KEY` environment variable. The script will fail with a clear error message if this is not set.
2. **No Input Validation**: Section functions don't validate parameter ranges (e.g., latitude -90 to 90). Rely on FullCAM API/simulator to reject invalid values.
3. **XML Escaping**: Special characters in notes/names are not escaped. Use plain ASCII for safety or implement proper XML escaping.
4. **Windows Paths**: Code uses both Windows (`\`) and Unix (`/`) path styles. Use `os.path` or `pathlib` for cross-platform compatibility.
5. **Timeout Values**: API requests have short timeouts (10-30s). Simulation endpoint may need longer timeout for complex plots.

## API Key Configuration

**The API key is stored in the `FULLCAM_API_KEY` environment variable.** This is configured as a Windows user environment variable.

**Setup:**
- Windows: The user variable `FULLCAM_API_KEY` is already configured with value `50b1d2f22cb34a3eb0d76391f6ce59cb`
- Linux/Mac: Add `export FULLCAM_API_KEY="your_key"` to `.bashrc` or `.zshrc`
- For new users, obtain API key from DCCEEW API portal

**In code:**
```python
import os
API_KEY = os.getenv("FULLCAM_API_KEY")
```

The `get_data.py` script includes error handling that raises a `ValueError` if the environment variable is not set.

## License and Attribution

This code interfaces with FullCAM, which is licensed under Creative Commons Attribution 4.0 International License by the Australian Department of Climate Change, Energy, the Environment and Water (DCCEEW).

Official documentation: https://dcceew.gov.au
FullCAM support: fullcam@dcceew.gov.au
