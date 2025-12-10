# FullCAM REST API & PLO File Generator

Python toolkit for interacting with Australia's **FullCAM (Full Carbon Accounting Model) REST API** and programmatically generating PLO (Plot) files for carbon accounting simulations.

## Overview

**FullCAM** is Australia's official carbon accounting model maintained by the Department of Climate Change, Energy, the Environment and Water (DCCEEW).

**What this toolkit does:**
- **PLO file generation** - Programmatically create plot files with climate, soil, and species data
- **Bulk simulation** - Submit PLO files to FullCAM and retrieve carbon accounting results
- **Data processing** - Convert results to NetCDF/GeoTIFF for spatial analysis
- **Data assembly** - Combine climate data from multiple sources (ANUClim, FPI layers, soil data)

**Target Users:** Researchers, policy analysts, and developers working with Australia's carbon accounting systems for forestry and land use sectors.

## Project Structure

```
.
├── RUN_FullCAM2024.py                   # Main entry point: run FullCAM simulations
├── FullCAM2NC.py                        # Convert simulation results to NetCDF/GeoTIFF
├── README.md                            # User documentation (this file)
├── CLAUDE.md                            # Developer guide for Claude Code
├── data/                                # Templates and examples
│   ├── dataholder_*.xml                 # PLO section templates (8 files)
│   ├── dataholder_species_*.xml         # Species-specific templates
│   ├── lumap.tif                        # LUTO land use raster (coordinate source)
│   └── processed/                       # NetCDF/GeoTIFF outputs
├── docs/                                # Documentation
│   ├── claude/                          # Claude Code development guides
│   └── FullCAM_Documentation_Complete.html
├── downloaded/                          # API cache (excluded from git)
│   ├── siteInfo_{lon}_{lat}.xml         # Climate/soil/FPI data per location
│   ├── species_{lon}_{lat}.xml          # Species parameters per location
│   ├── df_{lon}_{lat}.csv               # Simulation results per location
│   └── successful_downloads.txt         # Cache index (fast startup)
└── tools/                               # Libraries and utilities
    ├── __init__.py                      # Core PLO functions + API utilities
    ├── XML2Data.py                      # Parse API cache XML files
    ├── FullCAM2020_to_NetCDF/           # Legacy FullCAM 2020 PLO processing
    │   ├── __init__.py                  # PLO XML parsing functions
    │   ├── XML2NC_PLO.py                # Convert PLO files to NetCDF
    │   └── Compare_PLO_SiteInfo.py      # Compare PLO vs API data
    ├── Get_data/                        # Data acquisition utilities
    │   ├── assemble_data.py             # Assemble data from multiple sources
    │   ├── get_ANUClim.py               # Download ANUClim climate data
    │   ├── get_FPI_lyrs.py              # Get Forest Productivity Index layers
    │   ├── get_SoilClay.py              # Get soil clay fraction data
    │   └── get_maxAbgMF.py              # Get maximum aboveground mass fraction
    └── helpers/                         # Helper utilities
        ├── cache_manager.py             # Cache rebuild/verify/load
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
from tools import assemble_plo_sections, get_plot_simulation

# Generate complete PLO file for a location
lon, lat = 148.16, -35.61
plo_xml = assemble_plo_sections(lon, lat, species='Eucalyptus_globulus', year_start=2010)

# Save to file
with open("my_plot.plo", "w", encoding="utf-8") as f:
    f.write(plo_xml)

# Or run simulation directly (saves results to downloaded/df_{lon}_{lat}.csv)
import os
url = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1/2024/fullcam-simulator/run-plotsimulation"
headers = {"Ocp-Apim-Subscription-Key": os.getenv("FULLCAM_API_KEY")}
get_plot_simulation(lon, lat, url, headers)
```

## Usage Guide

### Step 1: Ensure Site Data Exists

The toolkit requires site-specific data files in `downloaded/`. If they don't exist, `assemble_plo_sections()` will automatically download them:

```python
from tools import assemble_plo_sections

# This will auto-download siteInfo if not cached
plo_xml = assemble_plo_sections(lon=148.16, lat=-35.61, year_start=2010)
```

### Step 2: Run Batch Simulations

**Run simulations for multiple locations:**

```python
# See RUN_FullCAM2024.py for complete example
from tools import get_downloading_coords, get_plot_simulation
from tools.helpers.cache_manager import get_existing_downloads
from joblib import Parallel, delayed

# Get coordinates to process
coords = get_downloading_coords(resfactor=10)  # 10x downsampled grid
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads()

# Filter to coordinates not yet processed
to_request = set(coords.set_index(['x', 'y']).index) - set(existing_dfs)

# Run in parallel
url = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1/2024/fullcam-simulator/run-plotsimulation"
headers = {"Ocp-Apim-Subscription-Key": API_KEY}

tasks = [delayed(get_plot_simulation)(lon, lat, url, headers) for lon, lat in to_request]
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

The toolkit can assemble data from multiple sources:

| Data Type | Source | Module |
|-----------|--------|--------|
| Climate (temp, rain, evap) | ANUClim via NCI Thredds | `tools/Get_data/get_ANUClim.py` |
| Forest Productivity Index | FPI raster layers | `tools/Get_data/get_FPI_lyrs.py` |
| Soil clay fraction | Soil landscape data | `tools/Get_data/get_SoilClay.py` |
| Maximum aboveground mass | FullCAM API | `tools/Get_data/get_maxAbgMF.py` |

## Common Operations

| Task | Code/Command |
|------|--------------|
| Generate PLO file | `assemble_plo_sections(lon, lat, year_start)` |
| Run simulation | `get_plot_simulation(lon, lat, url, headers)` |
| Convert to NetCDF | `python FullCAM2NC.py` |
| Load cache | `get_existing_downloads()` |
| Rebuild cache | `rebuild_cache()` |

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
