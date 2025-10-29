# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This repository provides tools for interacting with the **FullCAM (Full Carbon Accounting Model) REST API** and programmatically generating **PLO (Plot) files** for carbon accounting simulations in forestry and land use sectors.

**FullCAM** is Australia's official carbon accounting model maintained by the Department of Climate Change, Energy, the Environment and Water (DCCEEW). This codebase enables:
1. Fetching site data, climate time series, and templates from the FullCAM API
2. Programmatically assembling PLO files from scratch or API data
3. Running plot simulations via the FullCAM Simulator API

## Architecture

### Three-Module Design

The codebase consists of three primary Python modules with distinct responsibilities:

1. **`get_data.py`** - API interaction and data retrieval
   - Fetches site information, climate data, and species lists
   - Retrieves PLO templates from the FullCAM API
   - Submits PLO files for simulation and retrieves results
   - Parses XML responses into usable Python structures (dicts, DataFrames)

2. **`plo_section_functions.py`** - Modular PLO section builders (NEW approach)
   - Individual functions for each PLO XML section
   - Required parameters listed first, optional parameters with defaults
   - Comprehensive NumPy-style docstrings
   - Functions: `create_meta_section()`, `create_config_section()`, `create_timing_section()`, `create_build_section()`, `create_site_section()`, `create_timeseries()`

3. **`get_FullCAM_plo_file.py`** - PLO assembly and legacy templates
   - Contains raw XML template strings (constants starting with `PLO_`)
   - `assemble_plo_full()` - Combines sections into complete PLO document
   - `save_plo_file()` - Writes PLO content to disk
   - Imports and demonstrates the new modular functions from `plo_section_functions.py`

### Key Design Pattern: Two Approaches to PLO Generation

**Legacy Approach (Raw Templates):**
```python
# Uses pre-defined XML string templates
from get_FullCAM_plo_file import assemble_plo_full, save_plo_file
plo = assemble_plo_full()  # Uses PLO_META, PLO_CONFIG, etc.
save_plo_file(plo, "output.plo")
```

**New Approach (Modular Functions):**
```python
# Build sections programmatically with type-safe functions
from plo_section_functions import create_meta_section, create_build_section, create_timeseries
from get_FullCAM_plo_file import assemble_plo_full, save_plo_file

meta = create_meta_section("Plot_Name", notesME="My notes")
build = create_build_section(lonBL=148.16, latBL=-35.61)
# ... create other sections
plo = assemble_plo_full(meta=meta, build=build)
save_plo_file(plo, "output.plo")
```

Both approaches are valid and can be mixed. The new approach provides better documentation, type safety, and parameter validation.

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

The API key in `get_data.py` is hardcoded. For production use, extract to environment variables or config file.

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
Outputs formatted examples of each section type.

**Generate example PLO files:**
```bash
python get_FullCAM_plo_file.py
```
Creates two example PLO files demonstrating both approaches (legacy templates and modular functions).

**Fetch API data and run simulation:**
```bash
python get_data.py
```
Fetches site info, downloads template, runs simulation. Requires valid API key.

### File Locations

**Generated outputs:** `/mnt/user-data/outputs/` (Linux) or local directory (Windows)
**API response cache:** `data/` directory contains cached XML responses and example PLO files

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

1. **No HEAD in section functions** - The XML declaration (`<?xml version...?>`) and `<DocumentPlot>` root wrapper are added only by `assemble_plo_full()`
2. **All boolean attributes are strings** - Use `"true"/"false"`, not Python booleans
3. **Empty attributes use empty strings** - `lockTime=""` not `lockTime=None`
4. **TimeSeries count must match** - The `count` attribute in `<rawTS>` must equal the number of comma-separated values

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

Set version in `PLO_DOCUMENTPLOT_OPEN` constant or when using modular functions. API endpoints use `/2024/` for current version.

## Common Patterns

### Pattern: Build PLO from API Data

```python
from lxml import etree
import requests
from plo_section_functions import create_meta_section, create_build_section, create_timeseries, create_site_section
from get_FullCAM_plo_file import assemble_plo_full, save_plo_file

# 1. Fetch site data
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
    raw_data = [float(x) for x in ts_elem.find('rawTS').text.split(',') if x.strip()]
    ts_list.append(create_timeseries(ts_type, raw_data, yr0TS=ts_elem.get('yr0TS')))

# 3. Build sections
meta = create_meta_section("API_Generated_Plot")
build = create_build_section(148.16, -35.61)
site = create_site_section(len(ts_list), ts_list)

# 4. Assemble and save
plo = assemble_plo_full(meta=meta, build=build, site_timeseries=site)
save_plo_file(plo, "api_plot.plo")
```

### Pattern: Batch Processing Multiple Plots

```python
import pandas as pd

locations_df = pd.read_csv("plot_locations.csv")
# CSV columns: name, latitude, longitude, start_year, end_year

for idx, row in locations_df.iterrows():
    meta = create_meta_section(row['name'])
    build = create_build_section(row['longitude'], row['latitude'])
    timing = create_timing_section(stYrYTZ=str(row['start_year']), enYrYTZ=str(row['end_year']))

    plo = assemble_plo_full(meta=meta, build=build, timing=timing)
    save_plo_file(plo, f"{row['name']}.plo")
```

## Notes on PLO_FILE_FORMAT_GUIDE.md

The file `PLO_FILE_FORMAT_GUIDE.md` (formerly CLAUDE.MD) contains comprehensive **end-user documentation** for the PLO file format. It documents a hypothetical `PLOBuilder` class API and provides tutorials about FullCAM concepts. While that class doesn't exist in this codebase, the documentation provides valuable domain knowledge about:
- PLO file structure and XML schema
- Time series types and their meanings
- Forest categories and spatial parameters
- Troubleshooting common issues

Refer to that file for understanding FullCAM domain concepts, and this CLAUDE.md for architectural/implementation guidance.

## Dependencies

The codebase requires:
- `requests` - HTTP requests to FullCAM API
- `lxml` - XML parsing and generation
- `pandas` - Data manipulation and CSV handling
- `json` - JSON handling (minimal usage)
- `typing` - Type hints

No requirements.txt exists. Typical installation:
```bash
pip install requests lxml pandas
```

## Important Constraints

1. **API Key Security**: The API key is currently hardcoded. Extract to environment variables for production.
2. **No Input Validation**: Section functions don't validate parameter ranges (e.g., latitude -90 to 90). Rely on FullCAM API/simulator to reject invalid values.
3. **XML Escaping**: Special characters in notes/names are not escaped. Use plain ASCII for safety or implement proper XML escaping.
4. **Windows Paths**: Code uses both Windows (`\`) and Unix (`/`) path styles. Use `os.path` or `pathlib` for cross-platform compatibility.
5. **Timeout Values**: API requests have short timeouts (10-30s). Simulation endpoint may need longer timeout for complex plots.

## API Key Note

**The API key in get_data.py (`50b1d2f22cb34a3eb0d76391f6ce59cb`) appears to be an active subscription key for the FullCAM API.** When working with this code:
- Do not commit changes that expose this key to public repositories
- Consider moving to environment variable: `os.getenv("FULLCAM_API_KEY")`
- For new users, obtain API key from DCCEEW API portal

## License and Attribution

This code interfaces with FullCAM, which is licensed under Creative Commons Attribution 4.0 International License by the Australian Department of Climate Change, Energy, the Environment and Water (DCCEEW).

Official documentation: https://dcceew.gov.au
FullCAM support: fullcam@dcceew.gov.au
