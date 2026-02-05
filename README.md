# FullCAM REST API & PLO File Generator

Python toolkit for interacting with Australia's **FullCAM (Full Carbon Accounting Model) REST API** and programmatically generating PLO (Plot) files for carbon accounting simulations.

## Overview

**FullCAM** is Australia's official carbon accounting model maintained by the Department of Climate Change, Energy, the Environment and Water (DCCEEW).

**What this toolkit does:**
- **PLO file generation** - Programmatically create plot files with climate, soil, and species data
- **Bulk simulation** - Submit PLO files to FullCAM and retrieve carbon accounting results
- **Data processing** - Convert results to NetCDF/GeoTIFF for spatial analysis
- **Data assembly** - Combine climate data from multiple sources (ANUClim, FPI layers, soil data)
- **Species calibration** - Process TYF (Tree Yield Formula) parameters for different planting types

**Target Users:** Researchers, policy analysts, and developers working with Australia's carbon accounting systems for forestry and land use sectors.

## Supported Species

The toolkit currently supports the following species with their corresponding planting categories:

| Species ID | Species Name | Planting Categories | Description |
|------------|-------------|---------------------|-------------|
| `7` | Environmental plantings | `BeltH`, `BlockES`, `Water` | Mixed native species plantings for environmental restoration |
| `8` | Eucalyptus globulus | `Belt`, `Block` | Blue gum plantations for timber/pulp production |
| `23` | Mallee eucalypt species | `BeltHW`, `BlockES` | Mallee eucalypts for arid/semi-arid regions |

### Planting Category Descriptions

| Category | Full Name | Description |
|----------|-----------|-------------|
| `Block` | Block Planting | Standard block plantation with full canopy coverage |
| `BlockES` | Block Environmental System | Block planting for environmental/ecological purposes |
| `Belt` | Belt Planting | Linear/belt planting configuration (shelterbelts, windbreaks) |
| `BeltH` | Belt High-density | High-density belt planting |
| `BeltHW` | Belt High-density Wide | High-density wide belt (used for Mallee species) |
| `Water` | Water/Riparian | Plantings in riparian zones or water-adjacent areas |

## Project Structure

```
.
├── RUN_FullCAM2024.py                                  # Main entry point: run FullCAM simulations
├── FullCAM2NC.py                                       # Convert simulation results to NetCDF/GeoTIFF
├── README.md                                           # User documentation (this file)
├── CLAUDE.md                                           # Developer guide for Claude Code
├── data/                                               # Templates and examples
│   ├── dataholder_*.xml                                # PLO section templates
│   ├── dataholder_specId_*.xml                         # Species-specific templates (events, parameters)
│   ├── dataholder_Event_specId_*_tTYFCat_*.xml         # Event templates per species/category
│   ├── lumap.tif                                       # LUTO land use raster (coordinate source)
│   ├── ANUClim/                                        # Climate data from NCI (temp, rain, evap)
│   ├── FPI_lys/                                        # Forest Productivity Index layers (37 grids)
│   ├── maxAbgMF/                                       # Maximum aboveground mass fraction data
│   ├── Soil_landscape_AUS/                             # Soil clay content data (90m resolution)
│   ├── Species_TYF_R/                                  # Species TYF coefficients (tyf_G, tyf_r)
│   │   ├── specId_7_match_LUTO.nc                      # Environmental plantings TYF data
│   │   ├── specId_8_match_LUTO.nc                      # Eucalyptus globulus TYF data
│   │   └── specId_23_match_LUTO.nc                     # Mallee species TYF data
│   ├── data_assembled/                                 # Assembled siteInfo cache (NetCDF/Zarr)
│   │   └── siteinfo_cache.nc                           # Pre-assembled site data for all locations
│   └── processed/                                      # NetCDF/GeoTIFF outputs
│       └── Output_GeoTIFFs/                            # Carbon stock outputs by species/category
├── docs/                                               # Documentation
│   ├── claude/                                         # Claude Code development guides
│   │   ├── architecture.md                             # System design & data flow
│   │   ├── api-reference.md                            # Functions & API endpoints
│   │   ├── plo-files.md                                # PLO XML structure
│   │   └── development.md                              # Patterns & workflows
│   └── FullCAM_Documentation_Complete.html
├── downloaded/                                         # API cache (excluded from git)
│   ├── siteInfo_{lon}_{lat}.xml                        # Climate/soil/FPI data per location
│   ├── species_{lon}_{lat}_specId_{id}.xml             # Species parameters per location
│   ├── df_{lon}_{lat}_specId_{id}_specCat_{cat}.csv    # Simulation results
│   └── successful_downloads.txt                        # Cache index (fast startup)
└── tools/                                              # Libraries and utilities
    ├── __init__.py                                     # Core PLO functions + API utilities
    ├── XML2Data.py                                     # Parse API cache XML files
    ├── parameter.py                                    # Species mappings and geometry definitions
    ├── FullCAM2020_to_NetCDF/                          # Legacy FullCAM 2020 PLO processing
    │   ├── __init__.py                                 # PLO XML parsing functions
    │   ├── XML2NC_PLO.py                               # Convert PLO files to NetCDF
    │   └── Compare_PLO_SiteInfo.py                     # Compare PLO vs API data
    ├── Get_data/                                       # Data acquisition utilities
    │   ├── assemble_data.py                            # Assemble all data sources to match LUTO
    │   ├── get_ANUClim.py                              # Download ANUClim v2.0 climate data
    │   ├── get_FPI_lyrs.py                             # Get Forest Productivity Index layers
    │   ├── get_SoilClay.py                             # Get soil clay fraction data
    │   ├── get_maxAbgMF.py                             # Get maximum aboveground mass fraction
    │   └── get_TYR_R.py                                # Transform TYF R coefficients for species
    └── helpers/                                        # Helper utilities
        ├── cache_manager.py                            # Cache rebuild/verify/load (fast startup)
        ├── batch_manipulate_XML.py                     # Batch XML processing
        └── get_fullcam_help.py                         # FullCAM documentation helper
```

## Core Modules

| Module | Purpose |
|--------|---------|
| [RUN_FullCAM2024.py](RUN_FullCAM2024.py) | Run FullCAM simulations via REST API |
| [FullCAM2NC.py](FullCAM2NC.py) | Convert simulation results to NetCDF/GeoTIFF |
| [tools/__init__.py](tools/__init__.py) | Core PLO generation functions (13 sections) + API utilities |
| [tools/XML2Data.py](tools/XML2Data.py) | XML parsing for API cache files |
| [tools/parameter.py](tools/parameter.py) | Species mappings (`SPECIES_MAP`, `SPECIES_GEOMETRY`) |
| [tools/helpers/cache_manager.py](tools/helpers/cache_manager.py) | Download cache management |
| [tools/Get_data/assemble_data.py](tools/Get_data/assemble_data.py) | Assemble data from multiple sources to LUTO grid |

## Quick Start

### Installation

**Prerequisites:**
```bash
# Python 3.8 or higher recommended
pip install requests lxml pandas rioxarray xarray numpy joblib tqdm affine rasterio scipy
```

**Required for fast directory scanning (recommended):**
```bash
pip install scandir_rs
```

**Set up API key:**

```bash
# Windows (User environment variable - permanent)
setx FULLCAM_API_KEY "your_key_here"

# Linux/Mac (add to ~/.bashrc or ~/.zshrc for persistence)
export FULLCAM_API_KEY="your_key_here"
```

### Quick Example

**Generate PLO file and run simulation:**

```python
import os
import xarray as xr
from tools import assemble_plo_sections, get_plot_simulation

# Configuration
SPECIES_ID = 8          # Eucalyptus globulus (see SPECIES_MAP for all options)
SPECIES_CAT = 'Block'   # Block planting (see SPECIES_GEOMETRY for valid categories)

# Load assembled data cache (for "Cache" mode - faster for bulk processing)
data_site = xr.open_dataset("data/data_assembled/siteinfo_cache.nc")
data_species = xr.open_dataset(f"data/Species_TYF_R/specId_{SPECIES_ID}_match_LUTO.nc")

# Generate complete PLO file for a location
lon, lat = 148.16, -35.61
plo_xml = assemble_plo_sections(
    data_source='Cache',  # or 'API' for direct API calls
    lon=lon,
    lat=lat,
    data_site=data_site,
    data_species=data_species,
    specId=SPECIES_ID,
    specCat=SPECIES_CAT,
    year_start=2010
)

# Save PLO to file
with open("my_plot.plo", "w", encoding="utf-8") as f:
    f.write(plo_xml)

# Or run simulation directly via REST API
url = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1/2024/fullcam-simulator/run-plotsimulation"
headers = {"Ocp-Apim-Subscription-Key": os.getenv("FULLCAM_API_KEY")}
get_plot_simulation('Cache', lon, lat, data_site, data_species, SPECIES_ID, SPECIES_CAT, url, headers)
# Results saved to: downloaded/df_{lon}_{lat}_specId_{SPECIES_ID}_specCat_{SPECIES_CAT}.csv
```

## Configuration Reference

### RUN_FullCAM2024.py Parameters

```python
###########################################################
#                         Config                          #
###########################################################

# API Configuration
API_KEY = os.getenv("FULLCAM_API_KEY")
BASE_URL_SIM = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1"
ENDPOINT = "/2024/fullcam-simulator/run-plotsimulation"

# Download Parameters
RES_factor = 1          # Resolution factor: 1 = 1km, 2 = 2km, 3 = 3km, etc.
SPECIES_ID = 8          # Species ID (7, 8, or 23)
SPECIES_CAT = 'Block'   # Planting category (depends on SPECIES_ID)

# Coordinate Selection
include_region = 'LUTO' # 'ALL' = entire Australia, 'LUTO' = LUTO study area only
```

### Resolution Factor (`RES_factor`)

Controls the spatial resolution for batch processing:

| RES_factor | Resolution | Approx. Points | Use Case |
|------------|------------|----------------|----------|
| `1` | 1 km | ~4.3 million | Full resolution, production runs |
| `3` | 3 km | ~480,000 | Moderate resolution, testing at scale |
| `10` | 10 km | ~43,000 | Fast testing, prototyping |

### Region Selection (`include_region`)

| Value | Description |
|-------|-------------|
| `'ALL'` | All continental Australia cells (includes ocean/empty cells masked as -1) |
| `'LUTO'` | Only LUTO model study area cells (agricultural/forestry potential areas) |

## Usage Guide

### Data Modes

The toolkit supports two data modes:

| Mode | Description | Use Case |
|------|-------------|----------|
| `"API"` | Download data from FullCAM REST API per location | Testing, small batches (<100 locations) |
| `"Cache"` | Load from pre-assembled NetCDF/Zarr files | Production, bulk processing (1000s-millions of locations) |

### Step 1: Prepare Data (Cache Mode - Recommended)

For bulk processing, pre-assemble all data sources to match LUTO spatial template:

```bash
# Run data assembly scripts (one-time setup)
python tools/Get_data/get_ANUClim.py      # Download ANUClim climate data (temp, rain, evap)
python tools/Get_data/get_FPI_lyrs.py     # Extract Forest Productivity Index layers
python tools/Get_data/get_SoilClay.py     # Extract soil clay fraction (90m → 1km)
python tools/Get_data/get_maxAbgMF.py     # Extract max aboveground mass
python tools/Get_data/get_TYR_R.py        # Transform species TYF coefficients
python tools/Get_data/assemble_data.py    # Combine into siteinfo_cache.nc
```

**Output files:**
- `data/data_assembled/siteinfo_cache.nc` - Complete site data (climate, soil, FPI)
- `data/Species_TYF_R/specId_{ID}_match_LUTO.nc` - Species TYF parameters

### Step 2: Run Batch Simulations

**Full example from RUN_FullCAM2024.py:**

```python
import os
import xarray as xr
from joblib import Parallel, delayed
from tqdm.auto import tqdm
from tools import get_downloading_coords, get_plot_simulation
from tools.helpers.cache_manager import get_existing_downloads

# Configuration
API_KEY = os.getenv("FULLCAM_API_KEY")
url = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1/2024/fullcam-simulator/run-plotsimulation"
headers = {"Ocp-Apim-Subscription-Key": API_KEY}

RES_factor = 1              # 1km resolution
SPECIES_ID = 23             # Mallee eucalypt species
SPECIES_CAT = 'BeltHW'      # Belt high-density wide

# Load cached data
siteInfo_fill = xr.load_dataset("data/data_assembled/siteinfo_cache.nc", chunks={})
species_fill = xr.load_dataset(f"data/Species_TYF_R/specId_{SPECIES_ID}_match_LUTO.nc", chunks={})

# Get coordinates to process
scrap_coords = get_downloading_coords(resfactor=RES_factor, include_region='LUTO')

# Load existing downloads to skip already-processed locations
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads(SPECIES_ID, SPECIES_CAT)
existing_dfs_set = set((x, y) for x, y in existing_dfs)

# Filter to unprocessed coordinates
coords_tuples = scrap_coords[['x', 'y']].apply(tuple, axis=1)
mask_coords = ~coords_tuples.isin(existing_dfs_set)
to_request_coords = list(zip(scrap_coords.loc[mask_coords, 'x'], scrap_coords.loc[mask_coords, 'y']))

# Run simulations in parallel (32 threads)
tasks = [
    delayed(get_plot_simulation)('Cache', lon, lat, siteInfo_fill, species_fill,
                                  SPECIES_ID, SPECIES_CAT, url, headers)
    for lon, lat in to_request_coords
]

for _ in tqdm(Parallel(n_jobs=32, return_as='generator_unordered', backend='threading')(tasks),
              total=len(tasks)):
    pass
```

### Step 3: Convert Results to NetCDF/GeoTIFF

```bash
python FullCAM2NC.py
```

**Outputs per species/category combination:**
- `data/processed/Output_GeoTIFFs/carbonstock_RES_{RES}_specId_{ID}_specCat_{CAT}.nc` - Full NetCDF
- `data/processed/Output_GeoTIFFs/carbonstock_{VAR}_RES_{RES}_specId_{ID}_specCat_{CAT}.tif` - Per-variable GeoTIFF

**Variables in carbon stock outputs:**
- Annual carbon stocks for various pools (trees, soil, debris, products)
- Time series from simulation start year to end year (default: 2010-2100)

## PLO File Generation

The `assemble_plo_sections()` function generates complete PLO files by combining 13 sections:

| # | Section | Function | Description |
|---|---------|----------|-------------|
| 1 | Meta | `create_meta_section()` | Plot metadata (name, version, notes) |
| 2 | Config | `create_config_section()` | Simulation configuration (plot type: CompF, SoilF, CompA, SoilA, CompM) |
| 3 | Timing | `create_timing_section()` | Start/end years, time steps per year |
| 4 | Build | `create_build_section()` | Geographic location (lon/lat, area averaging) |
| 5 | Site | `create_site_section()` | Climate time series (temp, rainfall, evap, FPI) |
| 6 | Species | `create_species_section()` | Species TYF parameters (tyf_G, tyf_r) |
| 7 | Soil | `create_soil_section()` | Soil properties (clay fraction) |
| 8 | Init | `create_init_section()` | Initial carbon pools (rpmaCMInitF, humsCMInitF, etc.) |
| 9 | Event | `create_event_section()` | Management events (planting, thinning, harvest) |
| 10 | OutWinSet | `create_outwinset_section()` | GUI output settings |
| 11 | LogEntrySet | `create_logentryset_section()` | Audit log |
| 12 | Mnrl/Mulch | `create_mnrl_mulch_section()` | Nitrogen cycling parameters |
| 13 | Other Info | `create_other_info_section()` | Economic/sensitivity settings |

### Plot Types (tPlot parameter)

| Type | Name | Description |
|------|------|-------------|
| `CompF` | Comprehensive Forest | Full forest simulation with trees, debris, mulch, soil, products |
| `SoilF` | Forest Soil Only | Soil carbon dynamics without tree modeling |
| `CompA` | Comprehensive Agriculture | Full agricultural simulation with crops, debris, soil |
| `SoilA` | Agricultural Soil Only | Soil carbon under agriculture without crop modeling |
| `CompM` | Mixed/Multilayer | Combined forest + agriculture systems (agroforestry) |

## Intelligent Caching System

**Cache Index:** `downloaded/successful_downloads.txt`

The cache provides:
- **Fast startup:** Reading cache file takes ~1 second vs scanning millions of files
- **Resume on interruption:** No state loss if download crashes
- **Thread-safe:** Concurrent downloads logged safely with file locking
- **Species filtering:** Load only records for specific specId/specCat combinations

**Cache Management:**

```python
from tools.helpers.cache_manager import get_existing_downloads, rebuild_cache, batch_remove_files

# Load existing downloads (auto-rebuilds cache if missing)
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads(
    specId=8,           # Filter for Eucalyptus globulus
    specCat='Block'     # Filter for Block planting
)

# Rebuild cache from scratch (if corrupted)
rebuild_cache(
    downloaded_dir='downloaded',
    cache_file='downloaded/successful_downloads.txt'
)

# Batch remove files by pattern (e.g., remove all specId=8 results)
batch_remove_files(
    pattern='specId_8',
    directory='downloaded',
    n_jobs=100
)
```

## API Endpoints

### Data Builder API (for downloading site/species data)

| Endpoint | Purpose | Parameters |
|----------|---------|------------|
| `/2024/data-builder/siteinfo` | Site climate, soil, FPI data | latitude, longitude, area, plotT, frCat, incGrowth, version |
| `/2024/data-builder/species` | Species TYF parameters | latitude, longitude, area, frCat, specId, version |

**Base URL:** `https://api.dcceew.gov.au/climate/carbon-accounting/2024/data/v1`

### Simulation API (for running simulations)

| Endpoint | Purpose | Method |
|----------|---------|--------|
| `/2024/fullcam-simulator/run-plotsimulation` | Run FullCAM simulation | POST (multipart/form-data with PLO file) |

**Base URL:** `https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1`

## Data Sources

The toolkit assembles data from multiple sources into a unified LUTO-aligned grid:

| Data Type | Source | Module | Output |
|-----------|--------|--------|--------|
| Climate (temp, rain, evap) | ANUClim v2.0 via NCI Thredds | `get_ANUClim.py` | `data/ANUClim/processed/` |
| Forest Productivity Index | 37 regional FPI rasters | `get_FPI_lyrs.py` | `data/FPI_lys/FPI_lyrs.nc` |
| Soil clay fraction | Soil landscape 90m data | `get_SoilClay.py` | `data/Soil_landscape_AUS/` |
| Max aboveground mass | Site potential rasters | `get_maxAbgMF.py` | `data/processed/maxAbgMF_*.tif` |
| Species TYF coefficients | Species calibration data | `get_TYR_R.py` | `data/Species_TYF_R/` |
| Assembled siteInfo | All above combined | `assemble_data.py` | `data/data_assembled/siteinfo_cache.nc` |

### Variables in siteinfo_cache.nc

| Variable | Dimensions | Description |
|----------|------------|-------------|
| `avgAirTemp` | (year, month, y, x) | Average air temperature (°C) |
| `rainfall` | (year, month, y, x) | Monthly rainfall (mm) |
| `openPanEvap` | (year, month, y, x) | Open pan evaporation (mm) |
| `forestProdIx` | (year, y, x) | Forest Productivity Index |
| `maxAbgMF` | (y, x) | Max aboveground mass for forest |
| `fpiAvgLT` | (y, x) | Long-term average FPI |
| `clayFrac` | (y, x) | Soil clay fraction (0-1) |
| `rpmaCMInitF` | (y, x) | Initial resistant plant material carbon |
| `humsCMInitF` | (y, x) | Initial humus carbon |
| `inrtCMInitF` | (y, x) | Initial inert carbon |
| `TSMDInitF` | (y, x) | Initial topsoil moisture deficit |

### Species TYF Parameters

TYF (Tree Yield Formula) parameters control species growth calibration:

| Parameter | Description |
|-----------|-------------|
| `tyf_G` | Growth rate parameter |
| `tyf_r` | Decay rate parameter |

## Function Reference

### Core Functions (tools/__init__.py)

| Function | Description |
|----------|-------------|
| `assemble_plo_sections(data_source, lon, lat, data_site, data_species, specId, specCat, year_start)` | Generate complete PLO file |
| `get_plot_simulation(data_source, lon, lat, data_site, data_species, specId, specCat, url, headers)` | Run simulation via API |
| `get_siteinfo(lat, lon, sim_start_year, try_number, consensus_count)` | Download siteInfo with consensus |
| `get_species(lon, lat, specId, try_number, consensus_count)` | Download species data with consensus |
| `get_downloading_coords(resfactor, include_region)` | Get grid coordinates from LUTO raster |

### PLO Section Functions (tools/__init__.py)

| Function | Description |
|----------|-------------|
| `create_meta_section(nmME, notesME)` | Plot metadata |
| `create_config_section(tPlot)` | Simulation configuration |
| `create_timing_section(stYrYTZ, enYrYTZ, stepsPerYrYTZ)` | Time range settings |
| `create_build_section(lonBL, latBL, areaBL)` | Geographic location |
| `create_site_section(data_source, lon, lat, data_site)` | Climate time series |
| `create_species_section(data_source, lon, lat, data_species, specId)` | Species parameters |
| `create_soil_section(data_source, lon, lat, data_site, yr0TS)` | Soil properties |
| `create_init_section(data_source, lon, lat, data_site, tsmd_year, specId)` | Initial carbon pools |
| `create_event_section(specId, specCat)` | Management events |
| `create_outwinset_section()` | Output settings |
| `create_logentryset_section()` | Audit log |
| `create_mnrl_mulch_section()` | Nitrogen cycling |
| `create_other_info_section()` | Economic settings |

### Cache Management Functions (tools/helpers/cache_manager.py)

| Function | Description |
|----------|-------------|
| `get_existing_downloads(specId, specCat)` | Main entry point - loads from cache or rebuilds |
| `load_cache(specId, specCat, cache_file)` | Load existing downloads from cache file |
| `rebuild_cache(downloaded_dir, cache_file)` | Rebuild cache from directory scan |
| `batch_remove_files(pattern, directory, n_jobs)` | Batch delete files by pattern |

### XML Parsing Functions (tools/XML2Data.py)

| Function | Description |
|----------|-------------|
| `parse_site_data(xml_string)` | Parse site data from XML |
| `parse_soil_data(xml_string)` | Parse soil data from XML |
| `parse_init_data(xml_string, tsmd_year)` | Parse initial soil carbon data from XML |
| `parse_species_data(xml_string)` | Parse species TYF parameters from XML |
| `get_siteinfo_data(lon, lat, tsmd_year)` | Load and parse siteInfo file |
| `get_carbon_data(lon, lat, specId, specCat)` | Load carbon stock data from CSV |
| `export_to_geotiff_with_band_names()` | Export xarray to GeoTIFF with named bands |

## Common Operations

| Task | Code/Command |
|------|--------------|
| Generate PLO file | `assemble_plo_sections('Cache', lon, lat, data_site, data_species, specId, specCat)` |
| Run simulation | `get_plot_simulation('Cache', lon, lat, data_site, data_species, specId, specCat, url, headers)` |
| Convert to NetCDF | `python FullCAM2NC.py` |
| Load cache | `get_existing_downloads(specId=8, specCat='Block')` |
| Rebuild cache | `rebuild_cache()` |
| Get coordinates | `get_downloading_coords(resfactor=3, include_region='LUTO')` |
| Assemble data | `python tools/Get_data/assemble_data.py` |

## Troubleshooting

### Issue: "Invalid API key"
**Error:** `401 Unauthorized`

**Solution:** Check `FULLCAM_API_KEY` environment variable:
```bash
# Windows
echo %FULLCAM_API_KEY%

# Linux/Mac
echo $FULLCAM_API_KEY
```

### Issue: "Species not supported"
**Error:** `ValueError: specId 'X' not supported`

**Solution:** Use one of the supported species IDs:
- `7` - Environmental plantings
- `8` - Eucalyptus globulus
- `23` - Mallee eucalypt species

Check `tools/parameter.py` for the `SPECIES_GEOMETRY` dictionary to see valid `specCat` values for each species.

### Issue: "Site info not found"
**Error:** `FileNotFoundError: downloaded/siteInfo_148.16_-35.61.xml`

**Solution:** The file will be auto-downloaded when you call `assemble_plo_sections()` with `data_source='API'`. Alternatively:
- Use `data_source='Cache'` with pre-assembled data (recommended for bulk processing)
- Call `get_siteinfo(lat, lon)` directly to download

### Issue: "Slow startup"
**Problem:** Loading existing downloads takes minutes

**Solution:** The cache system should handle this automatically. If needed, rebuild cache:
```python
from tools.helpers.cache_manager import rebuild_cache
rebuild_cache()
```

### Issue: "scandir_rs not found"
**Error:** `ModuleNotFoundError: No module named 'scandir_rs'`

**Solution:** Install the fast directory scanning package:
```bash
pip install scandir_rs
```

## Version Information

- **FullCAM 2024:** PLO version `5009` (current default)
- **FullCAM 2020:** PLO version `5007` (legacy, see `tools/FullCAM2020_to_NetCDF/`)
- **API Version:** `/2024/` in endpoint paths

## Documentation

### User Documentation
- **[README.md](README.md)** (this file) - Quick start and usage guide
- **[FullCAM Documentation](docs/FullCAM_Documentation_Complete.html)** - Official parameter specifications

### Developer Documentation
- **[CLAUDE.md](CLAUDE.md)** - Navigation hub for Claude Code
- **[docs/claude/](docs/claude/)** - Architecture, API reference, PLO files guide

## License

This code interfaces with FullCAM, which is licensed under **Creative Commons Attribution 4.0 International License** by the Australian Department of Climate Change, Energy, the Environment and Water (DCCEEW).

## Resources

- **Official Documentation:** https://dcceew.gov.au
- **FullCAM Support:** fullcam@dcceew.gov.au
- **API Portal:** Contact DCCEEW for API access

## Security Note

**API Key Security:**
- Use `FULLCAM_API_KEY` environment variable
- Never hardcode API keys in source files
- Never commit keys to version control
- Never log or print API keys

If you accidentally expose your key, contact DCCEEW immediately for rotation.
