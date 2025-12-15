# CLAUDE.md

**Quick Navigation for Claude Code** - Detailed documentation is split into focused sections in [docs/claude/](docs/claude/)

## Project Summary

This is a Python toolkit for Australia's **FullCAM (Full Carbon Accounting Model) REST API** with tools for:
1. **PLO file generation** - Programmatically create plot files from cached/assembled data
2. **Simulation workflow** - Submit PLO files and retrieve carbon accounting results
3. **Data processing** - Convert results to NetCDF/GeoTIFF for spatial analysis
4. **Data assembly** - Combine climate data from multiple sources (ANUClim, FPI, soil data)

### Core Modules

| Module | Purpose |
|--------|---------|
| [RUN_FullCAM2024.py](RUN_FullCAM2024.py) | Main entry point: run FullCAM simulations via REST API |
| [FullCAM2NC.py](FullCAM2NC.py) | Convert simulation results to NetCDF/GeoTIFF |
| [tools/__init__.py](tools/__init__.py) | Core PLO generation (13 sections) + API utilities |
| [tools/XML2Data.py](tools/XML2Data.py) | XML parsing for API cache files |
| [tools/helpers/cache_manager.py](tools/helpers/cache_manager.py) | Download cache management |
| [tools/Get_data/](tools/Get_data/) | Data acquisition utilities (ANUClim, FPI, soil) |
| [tools/FullCAM2020_to_NetCDF/](tools/FullCAM2020_to_NetCDF/) | Legacy FullCAM 2020 PLO processing |

### Quick Start (Most Common Task)

**Generate PLO file from cached data (recommended for bulk processing):**
```python
import xarray as xr
from tools import assemble_plo_sections

# Load pre-assembled data caches
data_site = xr.open_dataset("data/data_assembled/siteinfo_cache.nc")
data_species = xr.open_dataset("data/Species_TYF_R/specId_8_match_LUTO.nc")

# Generate PLO file
plo_xml = assemble_plo_sections(
    data_source='Cache',
    lon=148.16, lat=-35.61,
    data_site=data_site,
    data_species=data_species,
    specId=8,           # Eucalyptus globulus
    specCat='Block',    # Block planting
    year_start=2010
)
```

**Run simulation:**
```python
from tools import get_plot_simulation
import os

url = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1/2024/fullcam-simulator/run-plotsimulation"
headers = {"Ocp-Apim-Subscription-Key": os.getenv("FULLCAM_API_KEY")}
get_plot_simulation('Cache', lon, lat, data_site, data_species, specId=8, specCat='Block', url=url, headers=headers)
```

## Key Implementation Details

**Critical Rules:**
- All PLO section functions return XML fragments (no `<?xml?>` declaration)
- Boolean attributes use strings: `"true"/"false"` not Python booleans
- Two data modes: `"API"` (per-location download) or `"Cache"` (pre-assembled NetCDF)
- Cache index at `downloaded/successful_downloads.txt` enables fast startup
- API key stored in `FULLCAM_API_KEY` environment variable (never hardcode)
- **NEVER** read XML from `downloaded/` directory directly - use examples in `data/` folder

**Data Modes:**
| Mode | Description | Performance |
|------|-------------|-------------|
| `"API"` | Downloads data per location from FullCAM REST API | Slow, use for testing |
| `"Cache"` | Loads from pre-assembled `siteinfo_cache.nc` + species NetCDF | Fast, use for bulk |

**Currently Supported Species (specId):**
- `8` - Eucalyptus globulus (default, with TYF calibration)

**Planting Categories (specCat):**
- `"Block"` - Block planting configuration
- `"Belt"` - Belt/shelterbelt planting configuration

## Project Structure

```
.
├── RUN_FullCAM2024.py                   # Main entry: run FullCAM simulations
├── FullCAM2NC.py                        # Convert results to NetCDF/GeoTIFF
├── README.md                            # User documentation
├── CLAUDE.md                            # This file (navigation hub)
├── data/                                # Templates and examples
│   ├── dataholder_*.xml                 # PLO section templates
│   ├── dataholder_specId_*.xml          # Species-specific templates (events, TYF params)
│   ├── siteInfo_*.xml                   # Example API responses
│   ├── lumap.tif                        # LUTO land use raster (spatial template)
│   ├── ANUClim/                         # Climate data from NCI
│   ├── FPI_lys/                         # Forest Productivity Index layers
│   ├── maxAbgMF/                        # Max aboveground mass data
│   ├── Soil_landscape_AUS/              # Soil clay content data
│   ├── Species_TYF_R/                   # Species TYF coefficients (tyf_G, tyf_r)
│   ├── data_assembled/                  # Assembled siteInfo cache (NC/Zarr)
│   └── processed/                       # NetCDF/GeoTIFF outputs
├── docs/                                # Documentation
│   ├── claude/                          # Claude Code guides
│   │   ├── architecture.md              # System design & data flow
│   │   ├── api-reference.md             # Functions & API endpoints
│   │   ├── plo-files.md                 # PLO XML structure
│   │   └── development.md               # Patterns & workflows
│   ├── FullCAM_Documentation_Complete.html
│   └── FullCAM Databuilder API Documentation v0.1 DRAFT.pdf
├── downloaded/                          # API cache (excluded from git)
│   ├── siteInfo_{lon}_{lat}.xml         # Climate/soil/FPI data
│   ├── species_{lon}_{lat}_specId_{id}.xml  # Species parameters
│   ├── df_{lon}_{lat}_specId_{id}.csv   # Simulation results
│   └── successful_downloads.txt         # Cache index
└── tools/                               # Libraries and utilities
    ├── __init__.py                      # Core PLO functions + API utilities (1100+ lines)
    ├── XML2Data.py                      # Parse API cache XML
    ├── FullCAM2020_to_NetCDF/           # Legacy FullCAM 2020 processing
    │   ├── __init__.py                  # PLO XML parsing + GeoTIFF export
    │   ├── XML2NC_PLO.py                # Convert PLO files to NetCDF
    │   └── Compare_PLO_SiteInfo.py      # Compare PLO vs API data
    ├── Get_data/                        # Data acquisition utilities
    │   ├── assemble_data.py             # Assemble all sources → siteinfo_cache.nc
    │   ├── get_ANUClim.py               # Download ANUClim v2.0 climate data
    │   ├── get_FPI_lyrs.py              # Extract FPI layers from 37 grids
    │   ├── get_SoilClay.py              # Extract soil clay fraction (90m→1km)
    │   ├── get_maxAbgMF.py              # Extract max aboveground mass
    │   └── get_TYR_R.py                 # Transform TYF R coefficients for species
    └── helpers/                         # Helper utilities
        ├── cache_manager.py             # Cache management (fast startup)
        ├── batch_manipulate_XML.py      # Batch XML processing
        └── get_fullcam_help.py          # Documentation helper
```

## Common Tasks Quick Reference

| Task | Command/Code |
|------|-------------|
| Generate PLO file | `assemble_plo_sections('Cache', lon, lat, data_site, data_species, specId, specCat)` |
| Run simulation | `get_plot_simulation('Cache', lon, lat, data_site, data_species, specId, specCat, url, headers)` |
| Convert to NetCDF | `python FullCAM2NC.py` |
| Load cache | `get_existing_downloads(specId=8)` |
| Rebuild cache | `rebuild_cache(specId=8)` |
| Get coordinates | `get_downloading_coords(resfactor=3)` |
| Assemble data | `python tools/Get_data/assemble_data.py` |
| Transform species | `python tools/Get_data/get_TYR_R.py` |

## Key Functions in tools/__init__.py

### PLO Generation
- `assemble_plo_sections(data_source, lon, lat, data_site, data_species, specId, specCat, year_start)` - Generate complete PLO file
- `create_meta_section()` - Plot metadata
- `create_config_section(tPlot)` - Simulation configuration (CompF, SoilF, CompA, SoilA, CompM)
- `create_timing_section(stYrYTZ, enYrYTZ, stepsPerYrYTZ)` - Time range settings
- `create_build_section(lonBL, latBL)` - Geographic location
- `create_site_section(data_source, lon, lat, data_site)` - Climate time series
- `create_species_section(data_source, lon, lat, data_species, specId, specCat)` - Species parameters
- `create_soil_section(data_source, lon, lat, data_site, yr0TS)` - Soil properties
- `create_init_section(data_source, lon, lat, data_site, tsmd_year)` - Initial carbon pools
- `create_event_section(specId, specCat)` - Management events
- `create_outwinset_section()` - Output settings
- `create_logentryset_section()` - Audit log
- `create_mnrl_mulch_section()` - Nitrogen cycling
- `create_other_info_section()` - Economic settings

### API Utilities
- `get_siteinfo(lat, lon, sim_start_year, consensus_count)` - Download siteInfo with consensus mechanism
- `get_species(lon, lat, specId, consensus_count)` - Download species data
- `get_plot_simulation(data_source, lon, lat, data_site, data_species, specId, specCat, url, headers)` - Run simulation via API
- `get_downloading_coords(resfactor)` - Get grid coordinates from LUTO raster

## Key Functions in tools/XML2Data.py

- `parse_site_data(xml_string)` - Parse site data from XML
- `parse_soil_data(xml_string)` - Parse soil data from XML
- `parse_init_data(xml_string, tsmd_year)` - Parse init data from XML
- `get_siteinfo_data(lon, lat, tsmd_year)` - Load and parse siteInfo file
- `get_carbon_data(lon, lat)` - Load carbon stock data from CSV
- `export_to_geotiff_with_band_names()` - Export xarray to GeoTIFF

## Key Functions in tools/helpers/cache_manager.py

- `load_cache(specId, cache_file)` - Load existing downloads from cache file
- `rebuild_cache(specId, downloaded_dir, cache_file)` - Rebuild cache from directory scan
- `get_existing_downloads(specId, cache_file, downloaded_dir)` - Main entry point for cache access
- `batch_remove_files(pattern, directory, n_jobs)` - Batch delete files by pattern

## Key Functions in tools/Get_data/

### assemble_data.py
Assembles data from multiple sources into a unified LUTO-aligned grid.

**Inputs:**
- `data/ANUClim/processed/ANUClim_to_FullCAM.nc` - Climate data
- `data/FPI_lys/FPI_lyrs.nc` - Forest Productivity Index
- `data/processed/BB_PLO_OneKm/siteinfo_PLO_RES.nc` - maxAbgMF, fpiAvgLT
- `data/Soil_landscape_AUS/ClayContent/clayFrac_00_30cm.tif` - Soil clay
- `data/processed/BB_PLO_OneKm/soilInit_PLO_RES.nc` - Soil init values

**Output:**
- `data/data_assembled/siteinfo_cache.nc` - Complete assembled dataset
- `data/data_assembled/siteinfo_cache.zarr` - Zarr format (faster loading)

**Variables in siteinfo_cache.nc:**
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

### get_ANUClim.py
Downloads ANUClim v2.0 climate data from NCI Thredds server.

**Parameters:**
- Variables: `evap`, `frst`, `pw`, `rain`, `srad`, `tavg`, `tmax`, `tmin`, `vp`, `vpd`
- Cadence: `daily` or `monthly`
- Years: 1970-2024

**Output:** `data/ANUClim/processed/ANUClim_to_FullCAM.nc`

### get_FPI_lyrs.py
Extracts Forest Productivity Index from 37 regional TIFF files.

**Input:** `data/FPI_lys/FPI_tiff/s{grid}_fpi_7022/`
**Output:** `data/FPI_lys/FPI_lyrs.nc`

### get_SoilClay.py
Extracts soil clay fraction from 90m resolution soil landscape data.

**Input:** `data/Soil_landscape_AUS/ClayContent/000055684v002/data/`
**Output:** `data/Soil_landscape_AUS/ClayContent/clayFrac_00_30cm.tif`

### get_maxAbgMF.py
Extracts maximum aboveground mass fraction for forest.

**Input:** `data/maxAbgMF/Site potential and FPI version 2_0/`
**Output:** `data/processed/maxAbgMF_*.tif`

### get_TYR_R.py
Transforms TYF R (Tree Yield Formula) coefficients for species to match LUTO spatial template.

**Input:** `data/processed/species_RES.nc`
**Output:**
- `data/Species_TYF_R/specId_8_match_LUTO.nc` - Complete dataset
- `data/Species_TYF_R/specId_8_{var}_{TYF_Type}.tif` - Per-variable GeoTIFFs

**TYF Parameters:**
| Parameter | Description |
|-----------|-------------|
| `tyf_G` | Growth rate parameter |
| `tyf_r` | Decay rate parameter |

**TYF Types (planting categories):**
- `Block` - Block planting configuration
- `Belt` - Belt/shelterbelt planting configuration

## Documentation Index

### For Understanding the Codebase
- **[Architecture Guide](docs/claude/architecture.md)** - System design, module responsibilities, data flow
- **[PLO Files Guide](docs/claude/plo-files.md)** - XML structure, sections, attributes, validation rules

### For Development Tasks
- **[API Reference](docs/claude/api-reference.md)** - Functions, parameters, FullCAM API endpoints
- **[Development Patterns](docs/claude/development.md)** - Common workflows, code patterns, examples

### Official FullCAM Resources
- **[FullCAM Documentation Complete](docs/FullCAM_Documentation_Complete.html)** - Parameter specs, valid ranges
- **[FullCAM API Documentation](docs/FullCAM%20Databuilder%20API%20Documentation%20v0.1%20DRAFT.pdf)** - REST API reference

## Dependencies

**Required packages:**
```bash
pip install requests lxml pandas rioxarray xarray numpy joblib tqdm affine rasterio scipy
```

**Optional (for faster directory scanning):**
```bash
pip install scandir_rs
```

## Security & API Keys

**API Key Storage:**
- Environment variable: `FULLCAM_API_KEY`
- Windows: User environment variable (already configured)
- Linux/Mac: `export FULLCAM_API_KEY="your_key"` in shell profile

**In code:**
```python
import os
API_KEY = os.getenv("FULLCAM_API_KEY")
if not API_KEY:
    raise ValueError("FULLCAM_API_KEY environment variable not set")
```

**Security rules:**
- Use environment variables
- Never hardcode API keys
- Never commit keys to git
- Never print keys in logs

## Comparing PLO Files

When debugging carbon stock discrepancies, compare two PLO files by checking these key input values:

### Key Input Parameters to Compare

| Parameter | Location in PLO | Description |
|-----------|-----------------|-------------|
| `lonBL`, `latBL` | `<Build>` | Geographic coordinates - must match! |
| `maxAbgMF` | `<Site>` attribute | Max aboveground mass for forest |
| `fpiAvgLT` | `<Site>` attribute | Long-term average forest productivity index |
| `clayFrac` | `<SoilOther>` | Soil clay fraction (affects decomposition) |
| `rpmaCMInitF` | `<InitSoilF>` | Initial resistant plant material carbon |
| `humsCMInitF` | `<InitSoilF>` | Initial humus carbon |
| `inrtCMInitF` | `<InitSoilF>` | Initial inert carbon |
| `TSMDInitF` | `<InitSoilF>` | Initial topsoil moisture deficit |

### Time Series to Compare

| Time Series | `tInTS` value | Expected Count |
|-------------|---------------|----------------|
| `avgAirTemp` | avgAirTemp | 648 (54 years × 12 months) |
| `rainfall` | rainfall | 648 (54 years × 12 months) |
| `openPanEvap` | openPanEvap | 648 (54 years × 12 months) |
| `forestProdIx` | forestProdIx | 53 (annual values) |

### Quick Comparison Checklist

1. **Location match**: Both files have same `lonBL` and `latBL`
2. **Time series count**: All climate series have 648 values (or same count)
3. **Site attributes**: `maxAbgMF` and `fpiAvgLT` within 1-2%
4. **Soil init values**: All `*CMInitF` values within 1%
5. **Clay fraction**: `clayFrac` values within 1%

### Common Issues

| Issue | Symptom | Cause |
|-------|---------|-------|
| Wrong location | All values differ significantly | `lonBL`/`latBL` mismatch |
| Missing year | Time series has 636 instead of 648 | Cache missing last year of data |
| Different timesteps | `stepsPerYrYTZ` differs | Web UI uses 110, cache may use 1 |

### Example: Ask Claude to Compare PLO Files

```
Compare the key input data in these two PLO files:
- data/Web_ui_140.05_-25.49.plo (reference from web UI)
- data/Web_ui_140.05_-25.49_cache.plo.xml (generated from cache)

Check: avgAirTemp, rainfall, openPanEvap, forestProdIx, maxAbgMF, fpiAvgLT,
       clayFrac, rpmaCMInitF, humsCMInitF, inrtCMInitF, TSMDInitF
```

## Version Information

- **FullCAM 2024:** PLO version `5009` (current default)
- **FullCAM 2020:** PLO version `5007` (legacy)
- **API Version:** `/2024/` in endpoint paths

## Claude Code Configuration

### Python Interpreter
```
F:\Users\jinzhu\Documents\miniforge\envs\luto\python.exe
```
Configured in `.claude/settings.local.json` for automatic use.

### Context Optimization

**`.claudeignore` excludes:**
- `downloaded/` - Contains thousands of XML cache files (use cache index instead)
- `__pycache__/` - Python bytecode

**Reading XML Examples:**
- **USE:** `data/siteInfo_*.xml`, `data/dataholder_*.xml` (fast access, same structure)
- **AVOID:** `downloaded/` files (millions of files, extremely slow)
- Only read from `downloaded/` when you need data for a specific lon/lat coordinate

## License

This code interfaces with FullCAM, licensed under CC BY 4.0 by the Australian Department of Climate Change, Energy, the Environment and Water (DCCEEW).

**Resources:**
- Official docs: https://dcceew.gov.au
- FullCAM support: fullcam@dcceew.gov.au
