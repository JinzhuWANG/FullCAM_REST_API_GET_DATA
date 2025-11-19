# CLAUDE.md

**Quick Navigation for Claude Code** - Detailed documentation is split into focused sections in [docs/claude/](docs/claude/)

## Project Summary

This is a Python toolkit for Australia's **FullCAM (Full Carbon Accounting Model) REST API** with tools for:
1. **Bulk data download** - Cache climate/soil/species data for Australian locations
2. **PLO file generation** - Programmatically create plot files from cached data
3. **Simulation workflow** - Submit PLO files and retrieve carbon accounting results
4. **Data processing** - Convert XML to NetCDF/GeoTIFF for spatial analysis

### Core Modules

| Module | Purpose | Documentation |
|--------|---------|---------------|
| [get_data.py](get_data.py) | Bulk API downloader (35 threads, caching) | [Architecture →](docs/claude/architecture.md#data-download-pipeline) |
| [get_PLO.py](get_PLO.py) | PLO generation + simulation workflow | [Development →](docs/claude/development.md#workflow-examples) |
| [tools/plo_section_functions.py](tools/plo_section_functions.py) | PLO file generator (13 sections) | [API Reference →](docs/claude/api-reference.md#plo-generation) |
| [XML2NC.py](XML2NC.py) | Convert XML cache to NetCDF/GeoTIFF | [Architecture →](docs/claude/architecture.md#data-processing-pipeline) |
| [XML2NC_PLO.py](XML2NC_PLO.py) | Convert PLO files to NetCDF/GeoTIFF | [Architecture →](docs/claude/architecture.md#data-processing-pipeline) |
| [tools/XML2Data.py](tools/XML2Data.py) | XML parsing for API cache files | [API Reference →](docs/claude/api-reference.md#data-extraction) |
| [tools/XML2Data_PLO.py](tools/XML2Data_PLO.py) | XML parsing for PLO files | [API Reference →](docs/claude/api-reference.md#data-extraction) |

### Quick Start (Most Common Task)

**Generate PLO file from cached data:**
```python
from tools.plo_section_functions import assemble_plo_sections
plo_xml = assemble_plo_sections(lon=148.16, lat=-35.61, year_start=2010)
```

**See:** [Development Guide](docs/claude/development.md) for complete workflows

## Key Implementation Details

**Critical Rules:**
- All PLO section functions return XML fragments (no `<?xml?>` declaration)
- Boolean attributes use strings: `"true"/"false"` not Python booleans
- Data loaded from `downloaded/siteInfo_{lon}_{lat}.xml` and `downloaded/species_{lon}_{lat}.xml`
- Cache index at `downloaded/successful_downloads.txt` enables fast startup
- API key stored in `FULLCAM_API_KEY` environment variable (never hardcode)
- **NEVER** read XML from `downloaded/` directory directly - use examples in `data/` folder

**See:** [PLO Files Guide](docs/claude/plo-files.md) for XML structure and validation rules

## Documentation Index

### 📖 For Understanding the Codebase
- **[Architecture Guide](docs/claude/architecture.md)** - System design, module responsibilities, data flow
- **[PLO Files Guide](docs/claude/plo-files.md)** - XML structure, sections, attributes, validation rules

### 🔧 For Development Tasks
- **[API Reference](docs/claude/api-reference.md)** - Functions, parameters, FullCAM API endpoints
- **[Development Patterns](docs/claude/development.md)** - Common workflows, code patterns, examples

### 📚 Official FullCAM Resources
- **[FullCAM Documentation Complete](docs/FullCAM_Documentation_Complete.html)** - Parameter specs, valid ranges
- **[FullCAM API Documentation](docs/FullCAM%20Databuilder%20API%20Documentation%20v0.1%20DRAFT.pdf)** - REST API reference

## Claude Code Configuration

### Python Interpreter
```
F:\jinzhu\conda_env\luto\python.exe
```
Configured in `.claude/settings.local.json` for automatic use.

### Context Optimization

**`.claudeignore` excludes:**
- `downloaded/` - Contains thousands of XML cache files (use cache index instead)
- `__pycache__/` - Python bytecode
- `*.pyc`, `*.pyo`, `*.pyd` - Compiled Python files

**Reading XML Examples:**
- ✅ **USE:** `data/siteInfo_*.xml`, `data/species_response.xml` (fast access, same structure)
- ❌ **AVOID:** `downloaded/` files (millions of files, extremely slow)
- Only read from `downloaded/` when you need data for a specific lon/lat coordinate

**See:** [Architecture Guide](docs/claude/architecture.md#caching-system) for cache management details

## Project Structure

```
.
├── get_data.py                          # Bulk API downloader
├── get_PLO.py                           # PLO generation + simulation
├── XML2NC.py                            # XML cache → NetCDF/GeoTIFF
├── XML2NC_PLO.py                        # PLO files → NetCDF/GeoTIFF
├── README.md                            # User documentation
├── CLAUDE.md                            # This file (navigation hub)
├── data/                                # Templates and examples
│   ├── dataholder_*.xml                 # PLO section templates (8 files)
│   ├── siteInfo_*.xml                   # Example API responses
│   ├── lumap.tif                        # LUTO land use raster
│   └── processed/                       # NetCDF/GeoTIFF outputs
├── docs/                                # Documentation
│   ├── claude/                          # Claude Code guides (4 files)
│   │   ├── architecture.md              # System design & data flow
│   │   ├── api-reference.md             # Functions & API endpoints
│   │   ├── plo-files.md                 # PLO XML structure
│   │   └── development.md               # Patterns & workflows
│   ├── FullCAM_Documentation_Complete.html
│   └── FullCAM Databuilder API Documentation v0.1 DRAFT.pdf
├── downloaded/                          # API cache (excluded from git)
│   ├── siteInfo_{lon}_{lat}.xml         # Climate/soil/FPI data
│   ├── species_{lon}_{lat}.xml          # Species parameters
│   ├── df_{lat}_{lon}.csv               # Simulation results
│   └── successful_downloads.txt         # Cache index
└── tools/                               # Libraries and utilities
    ├── plo_section_functions.py         # PLO generation (13 sections)
    ├── XML2Data.py                      # Parse API cache XML
    ├── XML2Data_PLO.py                  # Parse PLO XML
    ├── cache_manager.py                 # Cache rebuild/verify
    └── batch_manipulate_XML.py          # Batch XML processing
```

## Common Tasks Quick Reference

| Task | Command/Code | Documentation |
|------|-------------|---------------|
| Generate PLO file | `assemble_plo_sections(lon, lat, year_start)` | [Development →](docs/claude/development.md#generate-plo-files) |
| Download bulk data | `python get_data.py` | [Architecture →](docs/claude/architecture.md#data-download-pipeline) |
| Run simulation | See [get_PLO.py](get_PLO.py) | [Development →](docs/claude/development.md#simulation-workflow) |
| Convert to NetCDF | `python XML2NC.py` | [Development →](docs/claude/development.md#data-processing) |
| Rebuild cache | `python tools/cache_manager.py rebuild` | [API Reference →](docs/claude/api-reference.md#cache-management) |
| Verify cache | `python tools/cache_manager.py verify` | [API Reference →](docs/claude/api-reference.md#cache-management) |

## Dependencies

**Required packages:**
```bash
pip install requests lxml pandas rioxarray xarray numpy joblib tqdm affine rasterio
```

**Optional (for utilities):**
```bash
pip install scandir_rs  # Only for copy_files.py
```

**See:** [Architecture Guide](docs/claude/architecture.md#dependencies) for detailed dependency information

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
- ✅ Use environment variables
- ❌ Never hardcode API keys
- ❌ Never commit keys to git
- ❌ Never print keys in logs

## Version Information

- **FullCAM 2024:** PLO version `5009` (current default)
- **FullCAM 2020:** PLO version `5007` (legacy)
- **API Version:** `/2024/` in endpoint paths

## License

This code interfaces with FullCAM, licensed under CC BY 4.0 by the Australian Department of Climate Change, Energy, the Environment and Water (DCCEEW).

**Resources:**
- Official docs: https://dcceew.gov.au
- FullCAM support: fullcam@dcceew.gov.au
