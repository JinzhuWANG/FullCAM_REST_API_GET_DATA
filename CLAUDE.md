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

### Two-Module Design

The codebase consists of two primary Python modules with distinct responsibilities:

1. **`get_data.py`** - API interaction and data retrieval
   - Fetches site information, climate data, and species lists from FullCAM API
   - Parallel processing for bulk data downloads across Australian locations
   - Uses NLUM raster data to identify valid coordinates across Australia
   - Retrieves PLO templates from the FullCAM API
   - Submits PLO files for simulation and retrieves results (CSV format)
   - Includes retry logic with exponential backoff for robust API calls
   - Saves API responses to `downloaded/` directory for caching and analysis

2. **`plo_section_functions.py`** - Modular PLO section builders
   - Individual functions for each PLO XML section
   - Required parameters listed first, optional parameters with defaults
   - Comprehensive NumPy-style docstrings with parameter descriptions
   - Enhanced documentation on calibrations, convergence, and parameter relationships
   - Critical guidance on forest category selection and its impact on carbon predictions
   - Detailed explanations of simulation vs output resolution parameters
   - Functions: `create_meta_section()`, `create_config_section()`, `create_timing_section()`, `create_build_section()`, `create_site_section()`, `create_timeseries()`
   - Returns XML string fragments (no root wrapper or declaration)

### Project Structure

```
.
├── get_data.py                    # API client (fetch data, run simulations)
├── plo_section_functions.py       # Modular PLO section builders
├── README.md                      # User-facing documentation
├── CLAUDE.md                      # Developer guide (this file)
├── .gitignore                     # Git ignore patterns
├── data/                          # Cached API responses and example PLO files
│   ├── siteinfo_response.xml      # Site climate and soil data
│   ├── species_response.xml       # Species information
│   ├── regimes_response.xml       # Management regime data
│   ├── templates_response.xml     # List of available templates
│   ├── single_template_response.xml  # Downloaded PLO template
│   ├── updated_plotfile_response.xml # Updated plot file
│   ├── E_globulus_2024.plo        # Example Eucalyptus plot
│   └── E_globulus_2024 copy.plo   # Example plot copy
└── tools/                         # Documentation and utilities
    ├── FullCAM_Documentation_Complete.html  # Official FullCAM docs
    └── get_fullcam_help.py        # Helper script for documentation

```

### PLO Generation Approach

**Modular Function Approach:**
```python
# Build sections programmatically with type-safe functions
from plo_section_functions import (
    create_meta_section,
    create_build_section,
    create_timing_section,
    create_config_section,
    create_site_section,
    create_timeseries
)

# Create individual sections
meta = create_meta_section("Plot_Name", notesME="My notes")
config = create_config_section(tPlot="CompF")
timing = create_timing_section(stYrYTZ="2020", enYrYTZ="2050")
build = create_build_section(lonBL=148.16, latBL=-35.61)

# Create time series
temps = [15.68, 17.65, 13.03, 10.66, 5.53, 4.72,
         2.97, 3.65, 4.72, 9.66, 11.96, 15.80]
ts = create_timeseries("avgAirTemp", temps, yr0TS="2020", nYrsTS="1")

# Create site with time series
site = create_site_section(1, [ts])

# Manually assemble the complete PLO file
plo_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<DocumentPlot version="5009">
{meta}
{config}
{timing}
{build}
{site}
</DocumentPlot>'''

# Save to file
with open("my_plot.plo", "w", encoding="utf-8") as f:
    f.write(plo_content)
```

This approach provides better documentation, type safety, and parameter validation through comprehensive docstrings and Python type hints.

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

**Test modular section functions:**
```bash
python plo_section_functions.py
```
Outputs formatted examples of each section type to the console.

**Fetch API data (cache responses):**
```bash
python get_data.py
```
Fetches site info and species data for all Australian locations using parallel processing (50 concurrent threads). Uses NLUM raster data to identify valid coordinates. Includes exponential backoff retry logic for robustness. Saves responses to `downloaded/` directory. Requires valid API key and NLUM raster file (`data/NLUM_2010-11_clip.tif`).

### File Locations

**API response cache:** `data/` directory contains cached XML responses and example PLO files
**Documentation:** `tools/` directory contains FullCAM documentation HTML and helper scripts
**Generated PLO files:** Saved to current working directory or specified path

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

### Section Creation Functions

All section creation functions in `plo_section_functions.py` follow these design principles:
- Required parameters come first (no defaults)
- Optional parameters follow (with sensible defaults)
- Return XML string fragments (no XML declaration or root wrapper)
- Include comprehensive NumPy-style docstrings

**Available Functions:**

| Function | Required Parameters | Purpose |
|----------|-------------------|---------|
| `create_meta_section()` | `nmME` (plot name) | Plot metadata and notes |
| `create_config_section()` | None (all optional) | Simulation configuration flags |
| `create_timing_section()` | None (all optional) | Start/end years, time steps |
| `create_build_section()` | `lonBL`, `latBL` | Geographic location |
| `create_site_section()` | `count`, `timeseries_list` | Site parameters with time series |
| `create_timeseries()` | `tInTS`, `rawTS_values` | Individual time series data |

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
- `pandas` - Data manipulation and CSV handling
- `rioxarray` - Geospatial raster data handling (NLUM coordinate extraction)
- `joblib` - Parallel processing for bulk API calls
- `tqdm` - Progress bars for long-running operations
- `json` - JSON handling (minimal usage)
- `typing` - Type hints

No requirements.txt exists. Typical installation:
```bash
pip install requests lxml pandas rioxarray joblib tqdm
```

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
