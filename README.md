# FullCAM REST API & PLO File Generator

Python toolkit for interacting with the FullCAM (Full Carbon Accounting Model) REST API and programmatically generating PLO (Plot) files for carbon accounting simulations.

## Overview

**FullCAM** is Australia's official carbon accounting model maintained by the Department of Climate Change, Energy, the Environment and Water (DCCEEW).

**What this toolkit does:**
- Fetches site data, climate time series, and species information from the FullCAM API
- Generates PLO (Plot) files programmatically for carbon accounting simulations
- Submits PLO files for simulation and retrieves carbon stock/flux results
- Provides intelligent caching for large-scale spatial modeling (thousands of locations)

**Typical Workflow:**
1. Run `get_data.py` once to download and cache data for all Australian locations
2. Use `assemble_plo_sections(lon, lat, year_start)` to generate PLO files from cached data
3. Submit PLO files to FullCAM Simulator API to get carbon stock/flux time series
4. Analyze results (CSV output with annual/monthly carbon stocks)

**Target Users:** Researchers, policy analysts, and developers working with Australia's carbon accounting systems for forestry and land use sectors.

## Quick Start

### Quick Reference

**Most common operations:**

```python
# 1. Generate PLO file from cached data
from tools.plo_section_functions import assemble_plo_sections
plo_xml = assemble_plo_sections(lon=148.16, lat=-35.61, year_start=2010)

# 2. Save PLO to file
with open("my_plot.plo", "w", encoding="utf-8") as f:
    f.write(plo_xml)

# 3. Run simulation via API
import requests, os
response = requests.post(
    "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1/2024/fullcam-simulator/run-plotsimulation",
    files={'file': ('plot.plo', plo_xml)},
    headers={"Ocp-Apim-Subscription-Key": os.getenv("FULLCAM_API_KEY")}
)

# 4. Parse results
import pandas as pd
from io import StringIO
results_df = pd.read_csv(StringIO(response.text))
print(results_df[['Year', 'TotalC_tCha']].head())
```

**See [get_PLO.py](get_PLO.py) for complete working example.**

### Prerequisites

**Install dependencies:**
```bash
pip install requests lxml pandas rioxarray xarray numpy joblib tqdm
```

*Note: `scandir_rs` is only needed for the `copy_files.py` utility script.*

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

**Workflow: Download data → Generate PLO → Run simulation**

**Step 1: Download API data (one-time setup):**

```python
# Run the bulk download script to cache data for Australian locations
# This downloads siteInfo and species data for thousands of coordinates
# WARNING: This is a long-running script (hours to days depending on network)

python get_data.py
```

This script:
- Uses LUTO land use raster to identify valid Australian coordinates
- Downloads `siteInfo_{lon}_{lat}.xml` (climate, soil, FPI) for each location
- Downloads `species_{lon}_{lat}.xml` (Eucalyptus globulus parameters)
- **Intelligent caching**: Logs successful downloads to `downloaded/successful_downloads.txt`
  - Fast resume on interruption (reads cache file in seconds vs scanning millions of files)
  - Thread-safe logging for concurrent downloads
  - Automatic skip of already-downloaded coordinates
  - See [CACHE_USAGE.md](CACHE_USAGE.md) for detailed documentation
- Saves to `downloaded/` directory
- Uses 35 concurrent threads with exponential backoff retry logic

**Step 2: Generate PLO file from cached data:**

```python
from tools.plo_section_functions import assemble_plo_sections

# Specify coordinates and start year
lon, lat = 148.16, -35.61  # Canberra region
year_start = 2010

# Generate complete PLO file (loads from downloaded/ directory)
plo_xml = assemble_plo_sections(lon, lat, year_start)

# Optional: Save to file
with open("my_plot.plo", "w", encoding="utf-8") as f:
    f.write(plo_xml)

print("PLO file generated successfully!")
```

This automatically:
- Loads climate time series from `downloaded/siteInfo_{lon}_{lat}.xml`
- Loads species parameters from `downloaded/species_{lon}_{lat}.xml`
- Merges with templates from `data/dataholder_*.xml` files
- Returns complete, simulation-ready PLO XML string

**Step 3: Run simulation and get results:**

```python
import requests
import pandas as pd
from io import StringIO
import os

# Configuration
API_KEY = os.getenv("FULLCAM_API_KEY")
SIMULATOR_URL = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1"

# Submit PLO file to FullCAM Simulator
response = requests.post(
    f"{SIMULATOR_URL}/2024/fullcam-simulator/run-plotsimulation",
    files={'file': ('plot.plo', plo_xml)},
    headers={"Ocp-Apim-Subscription-Key": API_KEY},
    timeout=30
)

# Parse CSV results into DataFrame
results_df = pd.read_csv(StringIO(response.text))

# Save results
results_df.to_csv('simulation_results.csv', index=False)

# Display carbon stocks over time
print(results_df[['Year', 'TotalC_tCha']].head())
```

**Complete workflow script:** See [get_PLO.py](get_PLO.py) for a working example that combines all steps.

## Project Structure

```
.
├── get_data.py                                 # Bulk API data download (Australian coordinates)
├── get_PLO.py                                  # PLO generation and simulation workflow
├── convert_data2tif.py                         # Helper script for converting data to raster format
├── README.md                                   # User documentation (this file)
├── CLAUDE.md                                   # Developer guide for Claude Code
├── .gitignore                                  # Git ignore patterns (excludes downloaded/, __pycache__)
├── .claudeignore                               # Claude Code ignore patterns (reduces context usage)
├── data/                                       # Template XML files and example data
│   ├── dataholder_*.xml                        # XML templates for PLO sections (8 files)
│   ├── E_globulus_2024.plo                     # Example Eucalyptus plot
│   ├── plot_simulation_response.csv            # Example simulation results
│   ├── lumap.tif                               # LUTO land use raster (coordinate source)
│   ├── siteinfo_response.xml                   # Example API response (site info)
│   ├── species_response.xml                    # Example API response (species)
│   └── single_template_response.xml            # Example API response (template)
├── downloaded/                                 # Cached API responses (thousands of files, excluded from git)
│   ├── siteInfo_{lon}_{lat}.xml                # Climate, soil, FPI data per location
│   ├── species_{lon}_{lat}.xml                 # Species parameters per location
│   ├── df_{lat}_{lon}.csv                      # Carbon stock/flux time series per location
│   └── successful_downloads.txt                # Cache index tracking all successful downloads
└── tools/                                      # PLO generation library and utilities
    ├── plo_section_functions.py                # Complete PLO file generation module
    ├── cache_manager.py                        # Cache file management utilities
    ├── copy_files.py                           # Utility to copy downloaded files between directories
    ├── FullCAM_Documentation_Complete.html     # Official FullCAM docs
    └── get_fullcam_help.py                     # Documentation helper script
```

**Note:** The `downloaded/` directory contains thousands of XML files and is excluded from version control. The intelligent caching system uses `successful_downloads.txt` to track what's been downloaded, enabling fast resume on interruption.

### Caching System Benefits

The repository implements an intelligent caching system with significant performance benefits:

**Cache Index File:** `downloaded/successful_downloads.txt`
- Plain text file listing all successfully downloaded files (one per line)
- Thread-safe append operations for concurrent downloads
- Fast startup: Reading cache file takes seconds vs scanning millions of files (minutes/hours)

**Performance Comparison:**

| Operation | Without Cache | With Cache |
|-----------|---------------|------------|
| Check 100k files | ~5-10 minutes (file system scan) | ~1 second (text file read) |
| Resume after crash | Re-scan entire directory | Instant (read cache file) |
| Parallel downloads | Race conditions possible | Thread-safe logging |

**Cache Management:**
```bash
# Rebuild cache from existing files (if cache deleted/corrupted)
python tools/cache_manager.py rebuild

# Verify cache integrity (check all cached files exist)
python tools/cache_manager.py verify
```

**When cache helps:**
- Large-scale downloads (thousands of locations)
- Interrupted downloads (network issues, crashes)
- Frequent script restarts during development
- Copying files between systems (rebuild cache after transfer)

### Module Responsibilities

| Module | Purpose |
|--------|---------|
| [get_data.py](get_data.py) | Bulk download of API data for all Australian locations (one-time setup) |
| [get_PLO.py](get_PLO.py) | Example workflow: generate PLO → run simulation → save results |
| [tools/plo_section_functions.py](tools/plo_section_functions.py) | Complete PLO file generation from cached data |
| [tools/cache_manager.py](tools/cache_manager.py) | Cache file rebuild and verification utilities |
| [tools/copy_files.py](tools/copy_files.py) | Utility to copy downloaded files between directories (parallel processing) |

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

### Example 1: Generate Single PLO File

```python
from tools.plo_section_functions import assemble_plo_sections

# Generate PLO for a specific location using cached data
lon, lat = 148.16, -35.61  # Canberra region
year_start = 2010

# This automatically loads data from:
# - downloaded/siteInfo_148.16_-35.61.xml
# - downloaded/species_148.16_-35.61.xml
# - data/dataholder_*.xml templates
plo_xml = assemble_plo_sections(lon, lat, year_start)

# Save to file
with open("canberra_plot.plo", "w", encoding="utf-8") as f:
    f.write(plo_xml)

print("PLO file generated successfully!")
```

### Example 2: Batch Process Multiple Locations

```python
import pandas as pd
from tools.plo_section_functions import assemble_plo_sections

# Load locations from CSV or define manually
locations = pd.DataFrame({
    'name': ['Plot_A', 'Plot_B', 'Plot_C'],
    'lat': [-35.61, -36.12, -34.89],
    'lon': [148.16, 149.23, 147.45]
})

# Generate PLO files for all locations
for idx, row in locations.iterrows():
    try:
        # Generate PLO from cached data
        plo_xml = assemble_plo_sections(
            lon=row['lon'],
            lat=row['lat'],
            year_start=2010
        )

        # Save to file
        filename = f"{row['name']}.plo"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(plo_xml)

        print(f"Created {filename}")

    except FileNotFoundError as e:
        print(f"Skipping {row['name']}: {e}")
```

### Example 3: Generate PLO and Run Simulation

```python
import requests
import pandas as pd
from io import StringIO
import os
from tools.plo_section_functions import assemble_plo_sections

# Configuration
API_KEY = os.getenv("FULLCAM_API_KEY")
SIMULATOR_URL = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1"

# Generate PLO file
lon, lat = 148.16, -35.61
plo_xml = assemble_plo_sections(lon, lat, year_start=2010)

# Submit to simulator
response = requests.post(
    f"{SIMULATOR_URL}/2024/fullcam-simulator/run-plotsimulation",
    files={'file': ('plot.plo', plo_xml)},
    headers={"Ocp-Apim-Subscription-Key": API_KEY},
    timeout=30
)

# Parse and save results
results_df = pd.read_csv(StringIO(response.text))
results_df.to_csv(f'results_{lon}_{lat}.csv', index=False)

print(f"Simulation complete. Total carbon at year 2100: {results_df.iloc[-1]['TotalC_tCha']:.2f} tC/ha")
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

### Primary Function (Recommended Entry Point)

**`assemble_plo_sections(lon, lat, year_start=2010)`**

Generates a complete, simulation-ready PLO file from cached API data.

**Parameters:**
- `lon` (float): Longitude in decimal degrees
- `lat` (float): Latitude in decimal degrees
- `year_start` (int, optional): Simulation start year (default: 2010)

**Returns:** Complete PLO XML string ready for submission to FullCAM Simulator

**Data Requirements:**
- `downloaded/siteInfo_{lon}_{lat}.xml` must exist (run `get_data.py` first)
- `downloaded/species_{lon}_{lat}.xml` must exist (run `get_data.py` first)
- `data/dataholder_*.xml` template files must exist (included in repository)

**Example:**
```python
from tools.plo_section_functions import assemble_plo_sections

plo_xml = assemble_plo_sections(148.16, -35.61, year_start=2010)
```

### Section Creation Functions

Individual section functions in [tools/plo_section_functions.py](tools/plo_section_functions.py):

| Function | Parameters | Data Source | Purpose |
|----------|-----------|-------------|---------|
| `create_meta_section()` | `nmME` (plot name, optional) | Manual | Plot metadata and notes |
| `create_config_section()` | All optional | Defaults | Simulation configuration flags |
| `create_timing_section()` | All optional | Defaults | Start/end years, timesteps |
| `create_build_section()` | `lonBL`, `latBL` (required) | Manual | Geographic location |
| `create_site_section()` | `lon`, `lat` (required) | `downloaded/siteInfo_*.xml` | Site data with time series |
| `create_species_section()` | `lon`, `lat` (required) | `downloaded/species_*.xml` | Species parameters |
| `create_soil_section()` | `lon`, `lat`, `yr0TS` | `downloaded/siteInfo_*.xml` | Soil carbon pools |
| `create_init_section()` | `lon`, `lat`, `tsmd_year` | `downloaded/siteInfo_*.xml` | Initial carbon values |
| `create_event_section()` | None | `data/dataholder_event_block.xml` | Management events |
| `create_outwinset_section()` | None | `data/dataholder_OutWinSet.xml` | GUI settings |
| `create_logentryset_section()` | None | `data/dataholder_logentryset.xml` | Audit log |
| `create_mnrl_mulch_section()` | None | `data/dataholder_Mnrl_Mulch.xml` | Nitrogen cycling |
| `create_other_info_section()` | None | `data/dataholder_other_info.xml` | Economic/sensitivity |

**Note:** These functions are called internally by `assemble_plo_sections()`. You typically don't need to call them directly unless customizing specific sections.

### Data Download Scripts

**`get_data.py`** - Bulk API data download for Australian locations

Fetches and caches site information and species data for thousands of coordinates:

- Identifies valid coordinates from LUTO land use raster (`data/lumap.tif`)
- Downloads `siteInfo_{lon}_{lat}.xml` (climate, soil, FPI) for each location
- Downloads `species_{lon}_{lat}.xml` (Eucalyptus globulus parameters)
- Uses 35 concurrent threads with exponential backoff retry logic
- **Intelligent caching** via `downloaded/successful_downloads.txt`:
  - Logs all successful downloads (thread-safe append)
  - Fast startup: Reads cache file (seconds) vs scanning millions of files (minutes/hours)
  - Automatic resume on interruption
  - See [CACHE_USAGE.md](CACHE_USAGE.md) for details
- Skips already-downloaded coordinates based on cache
- Saves to `downloaded/` directory

**Usage:**
```bash
python get_data.py
```

**Warning:** This is a long-running script (hours to days) for large-scale spatial modeling.

**`get_PLO.py`** - Complete workflow example

Demonstrates PLO generation and simulation:

- Calls `assemble_plo_sections()` to generate PLO from cached data
- Submits PLO to FullCAM Simulator API
- Saves results to `data/plot_simulation_response.csv`

**Usage:**
```bash
python get_PLO.py
```

Edit the `lon`, `lat`, and `year_start` variables in the script to change location.

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

**Issue: "Slow startup when running get_data.py"**
- Check that `downloaded/successful_downloads.txt` exists
- If missing or corrupted, rebuild with: `python tools/cache_manager.py rebuild`
- See [CACHE_USAGE.md](CACHE_USAGE.md) for cache management details

**Issue: "Cache out of sync with actual files"**
- Run `python tools/cache_manager.py verify` to check integrity
- Rebuild cache with: `python tools/cache_manager.py rebuild`

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
