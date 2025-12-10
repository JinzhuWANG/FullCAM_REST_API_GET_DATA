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

**Generate PLO file from cached data:**
```python
from tools import assemble_plo_sections
plo_xml = assemble_plo_sections(lon=148.16, lat=-35.61, year_start=2010)
```

**Run simulation:**
```python
from tools import get_plot_simulation
import os

url = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1/2024/fullcam-simulator/run-plotsimulation"
headers = {"Ocp-Apim-Subscription-Key": os.getenv("FULLCAM_API_KEY")}
get_plot_simulation(lon, lat, url, headers)
```

## Key Implementation Details

**Critical Rules:**
- All PLO section functions return XML fragments (no `<?xml?>` declaration)
- Boolean attributes use strings: `"true"/"false"` not Python booleans
- Data loaded from `downloaded/siteInfo_{lon}_{lat}.xml`
- Cache index at `downloaded/successful_downloads.txt` enables fast startup
- API key stored in `FULLCAM_API_KEY` environment variable (never hardcode)
- **NEVER** read XML from `downloaded/` directory directly - use examples in `data/` folder

**Supported Species:**
- `Eucalyptus_globulus` (default)
- `Mallee_eucalypt`
- `Environmental_plantings`

## Project Structure

```
.
├── RUN_FullCAM2024.py                   # Main entry: run FullCAM simulations
├── FullCAM2NC.py                        # Convert results to NetCDF/GeoTIFF
├── README.md                            # User documentation
├── CLAUDE.md                            # This file (navigation hub)
├── data/                                # Templates and examples
│   ├── dataholder_*.xml                 # PLO section templates (8 files)
│   ├── dataholder_species_*.xml         # Species-specific templates (3 files)
│   ├── siteInfo_*.xml                   # Example API responses
│   ├── lumap.tif                        # LUTO land use raster
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
│   ├── species_{lon}_{lat}.xml          # Species parameters
│   ├── df_{lon}_{lat}.csv               # Simulation results
│   └── successful_downloads.txt         # Cache index
└── tools/                               # Libraries and utilities
    ├── __init__.py                      # Core PLO functions + API utilities
    ├── XML2Data.py                      # Parse API cache XML
    ├── FullCAM2020_to_NetCDF/           # Legacy FullCAM 2020 processing
    │   ├── __init__.py                  # PLO XML parsing functions
    │   ├── XML2NC_PLO.py                # Convert PLO files to NetCDF
    │   └── Compare_PLO_SiteInfo.py      # Compare PLO vs API data
    ├── Get_data/                        # Data acquisition utilities
    │   ├── assemble_data.py             # Assemble data from sources
    │   ├── get_ANUClim.py               # Download ANUClim climate data
    │   ├── get_FPI_lyrs.py              # Get FPI layers
    │   ├── get_SoilClay.py              # Get soil clay fraction
    │   └── get_maxAbgMF.py              # Get max aboveground mass
    └── helpers/                         # Helper utilities
        ├── cache_manager.py             # Cache management
        ├── batch_manipulate_XML.py      # Batch XML processing
        └── get_fullcam_help.py          # Documentation helper
```

## Common Tasks Quick Reference

| Task | Command/Code |
|------|-------------|
| Generate PLO file | `assemble_plo_sections(lon, lat, year_start)` |
| Run simulation | `get_plot_simulation(lon, lat, url, headers)` |
| Convert to NetCDF | `python FullCAM2NC.py` |
| Load cache | `get_existing_downloads()` |
| Rebuild cache | `rebuild_cache()` |
| Get coordinates | `get_downloading_coords(resfactor=10)` |

## Key Functions in tools/__init__.py

### PLO Generation
- `assemble_plo_sections(lon, lat, species, year_start)` - Generate complete PLO file
- `create_meta_section()` - Plot metadata
- `create_config_section()` - Simulation configuration
- `create_timing_section()` - Time range settings
- `create_build_section()` - Geographic location
- `create_site_section()` - Climate time series
- `create_species_section()` - Species parameters
- `create_soil_section()` - Soil properties
- `create_init_section()` - Initial carbon pools
- `create_event_section()` - Management events
- `create_outwinset_section()` - Output settings
- `create_logentryset_section()` - Audit log
- `create_mnrl_mulch_section()` - Nitrogen cycling
- `create_other_info_section()` - Economic settings

### API Utilities
- `get_siteinfo(lat, lon)` - Download siteInfo with consensus mechanism
- `get_species(lat, lon)` - Download species data
- `get_plot_simulation(lon, lat, url, headers)` - Run simulation via API
- `get_downloading_coords(resfactor)` - Get grid coordinates from LUTO raster

## Key Functions in tools/XML2Data.py

- `parse_site_data(xml_string)` - Parse site data from XML
- `parse_soil_data(xml_string)` - Parse soil data from XML
- `parse_init_data(xml_string, tsmd_year)` - Parse init data from XML
- `get_siteinfo_data(lon, lat, tsmd_year)` - Load and parse siteInfo file
- `get_carbon_data(lon, lat)` - Load carbon stock data from CSV
- `export_to_geotiff_with_band_names()` - Export xarray to GeoTIFF

## Key Functions in tools/helpers/cache_manager.py

- `load_cache(cache_file)` - Load existing downloads from cache
- `rebuild_cache(downloaded_dir, cache_file)` - Rebuild cache from directory
- `get_existing_downloads()` - Main entry point for cache access

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
