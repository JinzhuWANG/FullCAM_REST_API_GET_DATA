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

## Project Structure

```
.
├── RUN_FullCAM2024.py                   # Main entry point: run FullCAM simulations
├── FullCAM2NC.py                        # Convert simulation results to NetCDF/GeoTIFF
├── README.md                            # User documentation (this file)
├── CLAUDE.md                            # Developer guide for Claude Code
├── data/                                # Templates and examples
│   ├── dataholder_*.xml                 # PLO section templates
│   ├── dataholder_specId_*.xml          # Species-specific templates (events, parameters)
│   ├── lumap.tif                        # LUTO land use raster (coordinate source)
│   ├── ANUClim/                         # Climate data from NCI (temp, rain, evap)
│   ├── FPI_lys/                         # Forest Productivity Index layers (37 grids)
│   ├── maxAbgMF/                        # Maximum aboveground mass fraction data
│   ├── Soil_landscape_AUS/              # Soil clay content data (90m resolution)
│   ├── Species_TYF_R/                   # Species TYF coefficients (tyf_G, tyf_r)
│   ├── data_assembled/                  # Assembled siteInfo cache (NetCDF/Zarr)
│   └── processed/                       # NetCDF/GeoTIFF outputs
├── docs/                                # Documentation
│   ├── claude/                          # Claude Code development guides
│   │   ├── architecture.md              # System design & data flow
│   │   ├── api-reference.md             # Functions & API endpoints
│   │   ├── plo-files.md                 # PLO XML structure
│   │   └── development.md               # Patterns & workflows
│   └── FullCAM_Documentation_Complete.html
├── downloaded/                          # API cache (excluded from git)
│   ├── siteInfo_{lon}_{lat}.xml         # Climate/soil/FPI data per location
│   ├── species_{lon}_{lat}_specId_{id}.xml  # Species parameters per location
│   ├── df_{lon}_{lat}_specId_{id}.csv   # Simulation results per location
│   └── successful_downloads.txt         # Cache index (fast startup)
└── tools/                               # Libraries and utilities
    ├── __init__.py                      # Core PLO functions + API utilities (1100+ lines)
    ├── XML2Data.py                      # Parse API cache XML files
    ├── FullCAM2020_to_NetCDF/           # Legacy FullCAM 2020 PLO processing
    │   ├── __init__.py                  # PLO XML parsing functions
    │   ├── XML2NC_PLO.py                # Convert PLO files to NetCDF
    │   └── Compare_PLO_SiteInfo.py      # Compare PLO vs API data
    ├── Get_data/                        # Data acquisition utilities
    │   ├── assemble_data.py             # Assemble all data sources to match LUTO
    │   ├── get_ANUClim.py               # Download ANUClim v2.0 climate data
    │   ├── get_FPI_lyrs.py              # Get Forest Productivity Index layers
    │   ├── get_SoilClay.py              # Get soil clay fraction data
    │   ├── get_maxAbgMF.py              # Get maximum aboveground mass fraction
    │   └── get_TYR_R.py                 # Transform TYF R coefficients for species
    └── helpers/                         # Helper utilities
        ├── cache_manager.py             # Cache rebuild/verify/load (fast startup)
        ├── batch_manipulate_XML.py      # Batch XML processing
        └── get_fullcam_help.py          # FullCAM documentation helper
```

## Core Modules

| Module | Purpose |
|--------|---------|
| [RUN_FullCAM2024.py](RUN_FullCAM2024.py) | Run FullCAM simulations via REST API |
| [FullCAM2NC.py](FullCAM2NC.py) | Convert simulation results to NetCDF/GeoTIFF |
| [tools/__init__.py](tools/__init__.py) | Core PLO generation functions (13 sections) + API utilities |
| [tools/XML2Data.py](tools/XML2Data.py) | XML parsing for API cache files |
| [tools/helpers/cache_manager.py](tools/helpers/cache_manager.py) | Download cache management |
| [tools/Get_data/assemble_data.py](tools/Get_data/assemble_data.py) | Assemble data from multiple sources to LUTO grid |

## Quick Start

### Installation

**Prerequisites:**
```bash
# Python 3.8 or higher recommended
pip install requests lxml pandas rioxarray xarray numpy joblib tqdm affine rasterio scipy
```

**Optional (for faster directory scanning):**
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

# Load assembled data cache (for "Cache" mode - faster for bulk processing)
data_site = xr.open_dataset("data/data_assembled/siteinfo_cache.nc")
data_species = xr.open_dataset("data/Species_TYF_R/specId_8_match_LUTO.nc")

# Generate complete PLO file for a location
lon, lat = 148.16, -35.61
plo_xml = assemble_plo_sections(
    data_source='Cache',  # or 'API' for direct API calls
    lon=lon,
    lat=lat,
    data_site=data_site,
    data_species=data_species,
    specId=8,             # Eucalyptus globulus
    specCat='Block',      # Block planting (or 'Belt')
    year_start=2010
)

# Save to file
with open("my_plot.plo", "w", encoding="utf-8") as f:
    f.write(plo_xml)

# Or run simulation directly (saves results to downloaded/df_{lon}_{lat}_specId_8.csv)
url = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1/2024/fullcam-simulator/run-plotsimulation"
headers = {"Ocp-Apim-Subscription-Key": os.getenv("FULLCAM_API_KEY")}
get_plot_simulation('Cache', lon, lat, data_site, data_species, specId=8, specCat='Block', url=url, headers=headers)
```

## Usage Guide

### Data Modes

The toolkit supports two data modes:

| Mode | Description | Use Case |
|------|-------------|----------|
| `"API"` | Download data from FullCAM REST API per location | Testing, small batches |
| `"Cache"` | Load from pre-assembled NetCDF/Zarr files | Production, bulk processing |

### Step 1: Prepare Data (Cache Mode - Recommended)

For bulk processing, pre-assemble all data sources to match LUTO spatial template:

```python
# Run data assembly scripts (one-time setup)
python tools/Get_data/get_ANUClim.py      # Download ANUClim climate data
python tools/Get_data/get_FPI_lyrs.py     # Extract FPI layers
python tools/Get_data/get_SoilClay.py     # Extract soil clay fraction
python tools/Get_data/get_maxAbgMF.py     # Extract max aboveground mass
python tools/Get_data/get_TYR_R.py        # Transform species TYF coefficients
python tools/Get_data/assemble_data.py    # Combine into siteinfo_cache.nc
```

### Step 2: Run Batch Simulations

**Run simulations for multiple locations (see RUN_FullCAM2024.py):**

```python
import os
import xarray as xr
from tools import get_downloading_coords, get_plot_simulation
from tools.helpers.cache_manager import get_existing_downloads
from joblib import Parallel, delayed

# Load cached data (much faster than per-location API calls)
data_site = xr.open_dataset("data/data_assembled/siteinfo_cache.nc")
data_species = xr.open_dataset("data/Species_TYF_R/specId_8_match_LUTO.nc")

# Get coordinates to process
coords = get_downloading_coords(resfactor=3)  # 3x downsampled grid
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads(specId=8)

# Filter to coordinates not yet processed
to_request = set(coords.set_index(['x', 'y']).index) - set(existing_dfs)

# Run in parallel
url = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1/2024/fullcam-simulator/run-plotsimulation"
headers = {"Ocp-Apim-Subscription-Key": os.getenv("FULLCAM_API_KEY")}

tasks = [
    delayed(get_plot_simulation)(
        'Cache', lon, lat, data_site, data_species,
        specId=8, specCat='Block', url=url, headers=headers
    )
    for lon, lat in to_request
]
Parallel(n_jobs=20, return_as='generator_unordered')(tasks)
```

### Step 3: Convert Results to NetCDF/GeoTIFF

```bash
python FullCAM2NC.py
```

This creates spatially gridded datasets from simulation results:
- `data/processed/siteinfo_RES.nc` - Site information
- `data/processed/carbonstock_RES.nc` - Carbon stock time series

## PLO File Generation

The `assemble_plo_sections()` function generates complete PLO files by combining 13 sections:

1. **Meta** - Plot metadata and notes
2. **Config** - Simulation configuration (plot type)
3. **Timing** - Start/end years, time steps
4. **Build** - Geographic location
5. **Site** - Climate time series (temp, rainfall, evap, FPI)
6. **Species** - Species growth calibrations
7. **Soil** - Soil properties (clay fraction)
8. **Init** - Initial carbon pool values
9. **Event** - Management events timeline
10. **OutWinSet** - GUI output settings
11. **LogEntrySet** - Audit log
12. **Mnrl_Mulch** - Nitrogen cycling
13. **other_info** - Economic/sensitivity settings

**Supported species:**
- `Eucalyptus_globulus` (default)
- `Mallee_eucalypt`
- `Environmental_plantings`

## Intelligent Caching System

**Cache Index:** `downloaded/successful_downloads.txt`

The cache provides:
- **Fast startup:** Reading cache file takes ~1 second vs scanning millions of files
- **Resume on interruption:** No state loss if download crashes
- **Thread-safe:** Concurrent downloads logged safely

**Cache Management:**
```bash
# Rebuild cache from existing files (if corrupted)
python -c "from tools.helpers.cache_manager import rebuild_cache; rebuild_cache()"

# Load cache programmatically
from tools.helpers.cache_manager import get_existing_downloads
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads()
```

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

### Species TYF Parameters

TYF (Tree Yield Formula) parameters control species growth calibration:

| Parameter | Description |
|-----------|-------------|
| `tyf_G` | Growth rate parameter |
| `tyf_r` | Decay rate parameter |

**Planting categories (specCat):**
- `Block` - Block planting configuration
- `Belt` - Belt/shelterbelt planting configuration

## Common Operations

| Task | Code/Command |
|------|--------------|
| Generate PLO file | `assemble_plo_sections('Cache', lon, lat, data_site, data_species, specId, specCat)` |
| Run simulation | `get_plot_simulation('Cache', lon, lat, data_site, data_species, specId, specCat, url, headers)` |
| Convert to NetCDF | `python FullCAM2NC.py` |
| Load cache | `get_existing_downloads(specId=8)` |
| Rebuild cache | `rebuild_cache(specId=8)` |
| Get coordinates | `get_downloading_coords(resfactor=3)` |
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

### Issue: "Site info not found"
**Error:** `FileNotFoundError: downloaded/siteInfo_148.16_-35.61.xml`

**Solution:** The file will be auto-downloaded when you call `assemble_plo_sections()`. Alternatively, call `get_siteinfo(lat, lon)` directly.

### Issue: "Slow startup"
**Problem:** Loading existing downloads takes minutes

**Solution:** Rebuild cache index:
```python
from tools.helpers.cache_manager import rebuild_cache
rebuild_cache()
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

If you accidentally expose your key, contact DCCEEW immediately for rotation.
