# FullCAM REST API & PLO File Generator

Python toolkit for interacting with the FullCAM (Full Carbon Accounting Model) REST API and programmatically generating PLO (Plot) files for carbon accounting simulations.

## Overview

**FullCAM** is Australia's official carbon accounting model maintained by the Department of Climate Change, Energy, the Environment and Water (DCCEEW). This repository provides tools to:

- Fetch site data, climate time series, and species information from the FullCAM API
- Programmatically generate PLO files from scratch or using API data
- Submit PLO files for simulation and retrieve carbon stock/flux results
- Parse and analyze simulation outputs

## Quick Start

### Prerequisites

**Install dependencies:**
```bash
pip install requests lxml pandas
```

**Set up API key:**

The API key is stored in the `FULLCAM_API_KEY` environment variable (user variable for Windows).

To verify it's set:
```bash
# Windows Command Prompt
echo %FULLCAM_API_KEY%

# Windows PowerShell
echo $env:FULLCAM_API_KEY

# Linux/Mac
echo $FULLCAM_API_KEY
```

If not set, add it to your user environment variables (Windows) or export it in your shell profile.

### Basic Usage

**1. Fetch site data from API:**

```python
import requests
from lxml import etree
import os

# Configuration (reads from environment variable)
API_KEY = os.getenv("FULLCAM_API_KEY")
BASE_URL = "https://api.dcceew.gov.au/climate/carbon-accounting/2024/data/v1"

# Get climate and soil data for a location
response = requests.get(
    f"{BASE_URL}/2024/data-builder/siteinfo",
    params={
        "latitude": -35.61,
        "longitude": 148.16,
        "area": "OneKm",
        "plotT": "CompF"
    },
    headers={"Ocp-Apim-Subscription-Key": API_KEY}
)

# Parse response
root = etree.fromstring(response.content)
print(f"Site data retrieved: {response.status_code}")
```

**2. Generate a PLO file:**

```python
from plo_section_functions import (
    create_meta_section,
    create_build_section,
    create_config_section,
    create_timing_section,
    create_site_section
)

# Create sections
meta = create_meta_section("My_Plot", notesME="Test plot for forest carbon")
config = create_config_section(tPlot="CompF")
build = create_build_section(lonBL=148.16, latBL=-35.61, frCat="Plantation")
timing = create_timing_section(stYrYTZ="2000", enYrYTZ="2050")
site = create_site_section(0, [])  # Empty site for now

# Assemble and save
plo_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<DocumentPlot version="5009">
{meta}
{config}
{timing}
{build}
{site}
</DocumentPlot>'''

with open("my_plot.plo", "w", encoding="utf-8") as f:
    f.write(plo_content)
```

**3. Run a simulation:**

```python
import requests
import os

# Configuration (reads from environment variable)
API_KEY = os.getenv("FULLCAM_API_KEY")
SIMULATOR_URL = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1"

# Submit PLO file and get results
with open("my_plot.plo", "rb") as f:
    files = {"file": ("my_plot.plo", f, "application/octet-stream")}
    response = requests.post(
        f"{SIMULATOR_URL}/2024/fullcam-simulator/run-plotsimulation",
        files=files,
        headers={"Ocp-Apim-Subscription-Key": API_KEY}
    )

# Get CSV results
results_csv = response.text
print(results_csv)
```

## Project Structure

```
.
├── get_data.py                    # API client (fetch data, run simulations)
├── plo_section_functions.py       # Modular PLO section builders
├── README.md                      # User documentation (this file)
├── CLAUDE.md                      # Developer guide for Claude Code
├── .gitignore                     # Git ignore patterns
├── data/                          # Cached API responses and examples
│   ├── siteinfo_response.xml      # Site climate and soil data
│   ├── species_response.xml       # Species information
│   ├── regimes_response.xml       # Management regime data
│   ├── templates_response.xml     # List of available templates
│   ├── E_globulus_2024.plo        # Example Eucalyptus plot
│   └── ...
└── tools/                         # Documentation and utilities
    ├── FullCAM_Documentation_Complete.html
    └── get_fullcam_help.py
```

### Module Responsibilities

| Module | Purpose |
|--------|---------|
| [get_data.py](get_data.py) | API interactions, data fetching, simulation submission |
| [plo_section_functions.py](plo_section_functions.py) | Individual PLO section generators with type-safe parameters |

## PLO File Structure

PLO files are XML documents representing carbon accounting plots:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DocumentPlot version="5009">
  <Meta nmME="Plot_Name" notesME="Description"/>
  <Config tPlot="CompF" useFSI="true"/>
  <Timing stYrYTZ="2000" enYrYTZ="2050"/>
  <Build lonBL="148.16" latBL="-35.61" frCat="Plantation" areaBL="OneKm"/>
  <Site>
    <TimeSeries tInTS="avgAirTemp" yr0TS="2000" nYrsTS="50" dataPerYrTS="12">
      <rawTS count="600">12.5,13.2,14.8,...</rawTS>
    </TimeSeries>
  </Site>
  <!-- Optional: SpeciesForestSet, RegimeSet -->
</DocumentPlot>
```

### Key Plot Types

| Type | Description |
|------|-------------|
| `CompF` | Forest Composite (above & below ground biomass) |
| `SoilF` | Forest soil analysis only |
| `CompA` | Agricultural Composite |
| `SoilA` | Agricultural soil only |
| `CompM` | Mixed forest/agricultural |

### Forest Categories

| Category | Description |
|----------|-------------|
| `Plantation` | Commercial plantation species |
| `MVG` | Major Vegetation Groups (native) |
| `EnvMallee` | Environmental plantings |
| `ERF` | Emissions Reduction Fund methods |
| `ERFH` | ERF with EMP-specific calibrations |

## FullCAM API

### Authentication

All API requests require a subscription key stored in the `FULLCAM_API_KEY` environment variable:

```python
import os

API_KEY = os.getenv("FULLCAM_API_KEY")
headers = {"Ocp-Apim-Subscription-Key": API_KEY}
```

**Get your API key:** Contact DCCEEW or visit their developer portal

**Set up the environment variable:**
- Windows: Add `FULLCAM_API_KEY` as a user environment variable
- Linux/Mac: Add `export FULLCAM_API_KEY="your_key"` to your `.bashrc` or `.zshrc`

### Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/2024/data-builder/siteinfo` | Fetch climate, soil, species data for coordinates |
| `/2024/data-builder/template` | Download pre-configured PLO templates |
| `/2024/fullcam-simulator/run-plotsimulation` | Submit PLO file and get simulation results |

**Base URLs:**
- Data API: `https://api.dcceew.gov.au/climate/carbon-accounting/2024/data/v1`
- Simulation API: `https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1`

## Common Time Series Types

Climate and productivity data used in PLO files:

| Type | Description | Unit | Frequency |
|------|-------------|------|-----------|
| `avgAirTemp` | Average air temperature | °C | Monthly |
| `rainfall` | Precipitation | mm | Monthly |
| `openPanEvap` | Pan evaporation | mm | Monthly |
| `forestProdIx` | Forest Productivity Index | unitless | Annual |
| `VPD` | Vapor Pressure Deficit | kPa | Monthly |
| `solarRad` | Solar radiation | MJ/m² | Monthly |

## Examples

### Example 1: Create PLO from API Data

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
API_KEY = os.getenv("FULLCAM_API_KEY")
BASE_URL = "https://api.dcceew.gov.au/climate/carbon-accounting/2024/data/v1"

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

# 3. Build PLO sections
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

### Example 2: Batch Processing Locations

```python
import pandas as pd
from plo_section_functions import (
    create_meta_section,
    create_build_section,
    create_config_section,
    create_timing_section,
    create_site_section
)

# Load locations
locations = pd.DataFrame({
    'name': ['Plot_A', 'Plot_B', 'Plot_C'],
    'lat': [-35.61, -36.12, -34.89],
    'lon': [148.16, 149.23, 147.45]
})

# Generate PLO files
for idx, row in locations.iterrows():
    # Create sections
    meta = create_meta_section(row['name'])
    config = create_config_section(tPlot="CompF")
    timing = create_timing_section(stYrYTZ="2020", enYrYTZ="2050")
    build = create_build_section(row['lon'], row['lat'])
    site = create_site_section(0, [])  # Empty site

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
    print(f"Created {row['name']}.plo")
```

## Documentation

**For detailed parameter specifications and model configuration:**

See [tools/FullCAM_Documentation_Complete.html](tools/FullCAM_Documentation_Complete.html) for comprehensive documentation including:
- Complete PLO XML schema
- Parameter descriptions and valid ranges
- Time series requirements
- Species and regime configuration
- Model configuration options

**For development with Claude Code:**

See [CLAUDE.md](CLAUDE.md) for architecture details, design patterns, and implementation guidelines.

## Function Reference

### Section Creation Functions

All functions in [plo_section_functions.py](plo_section_functions.py):

| Function | Required Params | Purpose |
|----------|----------------|---------|
| `create_meta_section()` | `nmME` | Plot metadata and notes |
| `create_config_section()` | None | Simulation configuration |
| `create_timing_section()` | None | Start/end years, time steps |
| `create_build_section()` | `lonBL`, `latBL` | Geographic location |
| `create_site_section()` | `count`, `timeseries_list` | Site data with time series |
| `create_timeseries()` | `tInTS`, `rawTS_values` | Individual time series |

### API Data Script

[get_data.py](get_data.py) is a standalone script (not a module with functions) that fetches data from the FullCAM API:

**What it does:**
- Fetches site information (climate, soil data) for specified coordinates
- Downloads species information for a specific species ID
- Retrieves management regime data
- Gets list of available PLO templates
- Downloads a specific template file
- Converts plot files to updated format
- Saves all responses to the `data/` directory as XML files

**Usage:**
```bash
python get_data.py
```

Modify the parameters in the script (latitude, longitude, species ID, etc.) before running.

## Troubleshooting

**Issue: "Invalid coordinate values"**
- Ensure latitude is between -90 and 90, longitude between -180 and 180

**Issue: "Time series count mismatch"**
- The `count` attribute must equal the number of comma-separated values
- Total values should equal `nYrsTS * dataPerYrTS`

**Issue: "PLO file not recognized by FullCAM"**
- Check version matches FullCAM (5007 for 2020, 5009 for 2024)
- Verify all required sections are present: Meta, Config, Timing, Build, Site

**Issue: "API authentication failed"**
- Verify your API key is correct
- Check the key is included in request headers: `Ocp-Apim-Subscription-Key`

## Version Compatibility

- **FullCAM 2020:** Use version `5007` in DocumentPlot
- **FullCAM 2024:** Use version `5009` (current default)
- **API Version:** All endpoints use `/2024/` in path

## License

This code interfaces with FullCAM, which is licensed under Creative Commons Attribution 4.0 International License by the Australian Department of Climate Change, Energy, the Environment and Water (DCCEEW).

## Resources

- **Official Documentation:** https://dcceew.gov.au
- **FullCAM Support:** fullcam@dcceew.gov.au
- **API Portal:** Contact DCCEEW for API access

## Contributing

When modifying this codebase:

1. Follow the parameter ordering convention (required first, optional with defaults)
2. Use NumPy-style docstrings for all functions
3. Test PLO files with the FullCAM simulator before committing
4. Update [CLAUDE.md](CLAUDE.md) when adding new patterns or modules
5. Keep API keys out of version control (use environment variables)

## Security Note

The API key is stored in the `FULLCAM_API_KEY` environment variable and is **not** committed to the repository. This is the secure approach for managing API credentials.

**Important:**
- Never hardcode API keys in source files
- The `FULLCAM_API_KEY` environment variable must be set before running scripts
- Do not share your API key publicly or commit it to version control
- If you accidentally expose your key, contact DCCEEW to get a new one
