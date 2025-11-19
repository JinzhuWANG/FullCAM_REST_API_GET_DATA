# FullCAM REST API & PLO File Generator

Python toolkit for interacting with Australia's **FullCAM (Full Carbon Accounting Model) REST API** and programmatically generating PLO (Plot) files for carbon accounting simulations.

## Overview

**FullCAM** is Australia's official carbon accounting model maintained by the Department of Climate Change, Energy, the Environment and Water (DCCEEW).

**What this toolkit does:**
- **Bulk data download** - Cache climate, soil, and species data for Australian locations
- **PLO file generation** - Programmatically create plot files from cached data
- **Simulation workflow** - Submit PLO files to FullCAM and retrieve carbon accounting results
- **Data processing** - Convert XML to NetCDF/GeoTIFF for spatial analysis

**Typical Workflow:**
1. Run [get_data.py](get_data.py) once to download and cache data for Australian locations
2. Use `assemble_plo_sections(lon, lat, year_start)` to generate PLO files from cached data
3. Submit PLO files to FullCAM Simulator API to get carbon stock/flux time series
4. Convert results to NetCDF/GeoTIFF for spatial analysis

**Target Users:** Researchers, policy analysts, and developers working with Australia's carbon accounting systems for forestry and land use sectors.

## Quick Start

### Installation

**Prerequisites:**
```bash
# Python 3.8 or higher recommended
pip install requests lxml pandas rioxarray xarray numpy joblib tqdm affine rasterio
```

**Optional (for faster directory operations):**
```bash
pip install scandir_rs
```

**Set up API key:**

The API key is stored in the `FULLCAM_API_KEY` environment variable.

```bash
# Windows (User environment variable - permanent)
setx FULLCAM_API_KEY "your_key_here"

# Linux/Mac (add to ~/.bashrc or ~/.zshrc for persistence)
export FULLCAM_API_KEY="your_key_here"
```

To verify:
```bash
# Windows Command Prompt
echo %FULLCAM_API_KEY%

# PowerShell
echo $env:FULLCAM_API_KEY

# Linux/Mac
echo $FULLCAM_API_KEY
```

**Get your API key:** Contact DCCEEW or visit their developer portal.

### Quick Example

**Most common operation - Generate PLO file from cached data:**

```python
from tools.plo_section_functions import assemble_plo_sections

# Generate complete PLO file for Canberra region
lon, lat = 148.16, -35.61
year_start = 2010

plo_xml = assemble_plo_sections(lon, lat, year_start)

# Save to file
with open("my_plot.plo", "w", encoding="utf-8") as f:
    f.write(plo_xml)

print("✓ PLO file generated successfully!")
```

**Complete workflow example:** See [get_PLO.py](get_PLO.py)

## Project Structure

```
.
├── get_data.py                          # Bulk API downloader (35 threads, caching)
├── get_PLO.py                           # PLO generation + simulation workflow
├── XML2NC.py                            # Convert XML cache → NetCDF/GeoTIFF
├── XML2NC_PLO.py                        # Convert PLO files → NetCDF/GeoTIFF
├── README.md                            # User documentation (this file)
├── CLAUDE.md                            # Developer guide for Claude Code
├── data/                                # Templates and examples
│   ├── dataholder_*.xml                 # PLO section templates (8 files)
│   ├── siteInfo_*.xml                   # Example API responses
│   ├── lumap.tif                        # LUTO land use raster (coordinate source)
│   └── processed/                       # NetCDF/GeoTIFF outputs
├── docs/                                # Documentation
│   ├── claude/                          # Claude Code development guides
│   │   ├── architecture.md              # System design & data flow
│   │   ├── api-reference.md             # Functions & API endpoints
│   │   ├── plo-files.md                 # PLO XML structure & validation
│   │   └── development.md               # Workflows & patterns
│   ├── FullCAM_Documentation_Complete.html  # Official parameter specs
│   └── FullCAM Databuilder API Documentation v0.1 DRAFT.pdf
├── downloaded/                          # API cache (excluded from git)
│   ├── siteInfo_{lon}_{lat}.xml         # Climate/soil/FPI data per location
│   ├── species_{lon}_{lat}.xml          # Species parameters per location
│   ├── df_{lat}_{lon}.csv               # Simulation results per location
│   └── successful_downloads.txt         # Cache index (fast startup)
└── tools/                               # Libraries and utilities
    ├── plo_section_functions.py         # PLO generation (13 sections)
    ├── XML2Data.py                      # Parse API cache XML
    ├── XML2Data_PLO.py                  # Parse PLO XML
    ├── cache_manager.py                 # Cache rebuild/verify
    ├── batch_manipulate_XML.py          # Batch XML processing
    └── get_fullcam_help.py              # Documentation helper
```

## Core Modules

| Module | Purpose | Documentation |
|--------|---------|---------------|
| [get_data.py](get_data.py) | Bulk download of API data for Australian locations | [Architecture →](docs/claude/architecture.md#data-download-pipeline) |
| [get_PLO.py](get_PLO.py) | Complete workflow: PLO generation → simulation → results | [Development →](docs/claude/development.md#workflow-2-generate-plo-and-run-simulation) |
| [tools/plo_section_functions.py](tools/plo_section_functions.py) | PLO file generator (13 sections + assembly) | [API Reference →](docs/claude/api-reference.md#plo-generation-functions) |
| [XML2NC.py](XML2NC.py) | Convert API cache XML to NetCDF/GeoTIFF | [Development →](docs/claude/development.md#pattern-convert-xml-to-netcdfgeotiff) |
| [XML2NC_PLO.py](XML2NC_PLO.py) | Convert PLO files to NetCDF/GeoTIFF | [Architecture →](docs/claude/architecture.md#data-processing-pipeline) |
| [tools/XML2Data.py](tools/XML2Data.py) | XML parsing for API cache files | [API Reference →](docs/claude/api-reference.md#xml2datapy-api-cache-files) |
| [tools/XML2Data_PLO.py](tools/XML2Data_PLO.py) | XML parsing for PLO files | [API Reference →](docs/claude/api-reference.md#xml2data_plopy-plo-files) |

## Usage Guide

### Step 1: Download API Data (One-Time Setup)

**Download climate, soil, and species data for Australian locations:**

```bash
python get_data.py
```

**What it does:**
- Identifies valid coordinates from LUTO land use raster (`data/lumap.tif`)
- Downloads `siteInfo_{lon}_{lat}.xml` (climate, soil, FPI) for each location
- Downloads `species_{lon}_{lat}.xml` (Eucalyptus globulus parameters)
- Uses **35 concurrent threads** with exponential backoff retry logic
- **Intelligent caching** via `downloaded/successful_downloads.txt`:
  - Fast startup (reads cache file in seconds vs scanning millions of files)
  - Thread-safe logging for concurrent downloads
  - Automatic resume on interruption
- Saves to `downloaded/` directory
- Skips already-downloaded coordinates

**Note:** This is a long-running script (4-8 hours for full Australia). Suitable for large-scale spatial modeling projects.

### Step 2: Generate PLO Files

**Generate PLO file from cached data:**

```python
from tools.plo_section_functions import assemble_plo_sections

# Specify location and start year
lon, lat = 148.16, -35.61  # Canberra region
year_start = 2010

# Generate complete PLO file
# (automatically loads from downloaded/siteInfo_*.xml and downloaded/species_*.xml)
plo_xml = assemble_plo_sections(lon, lat, year_start)

# Save to file
with open("canberra_plot.plo", "w", encoding="utf-8") as f:
    f.write(plo_xml)
```

**What `assemble_plo_sections()` does:**
1. Loads climate time series from `downloaded/siteInfo_{lon}_{lat}.xml`
2. Loads species parameters from `downloaded/species_{lon}_{lat}.xml`
3. Calculates initial TSMD (Top Soil Moisture Deficit) for start year
4. Merges with templates from `data/dataholder_*.xml` files
5. Assembles 13 sections into complete PLO XML string
6. Returns simulation-ready PLO file

**See:** [API Reference](docs/claude/api-reference.md#assemble_plo_sectionslat-lon-year_start2010) for parameters

### Step 3: Run Simulation

**Submit PLO file to FullCAM Simulator and get results:**

```python
import requests
import pandas as pd
from io import StringIO
import os

# Configuration
API_KEY = os.getenv("FULLCAM_API_KEY")
SIMULATOR_URL = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1"

# Submit PLO file
response = requests.post(
    f"{SIMULATOR_URL}/2024/fullcam-simulator/run-plotsimulation",
    files={'file': ('plot.plo', plo_xml)},
    headers={"Ocp-Apim-Subscription-Key": API_KEY},
    timeout=30
)

# Parse results
if response.status_code == 200:
    results_df = pd.read_csv(StringIO(response.text))

    # Save results
    results_df.to_csv('simulation_results.csv', index=False)

    # Display carbon stocks over time
    print(results_df[['Year', 'TotalC_tCha', 'AboveGround_tCha']].head(10))
else:
    print(f"Simulation failed: {response.status_code}")
```

**CSV Output Columns:**
- `Year` - Simulation year
- `TotalC_tCha` - Total carbon stock [tC/ha]
- `AboveGround_tCha` - Aboveground biomass carbon [tC/ha]
- `BelowGround_tCha` - Belowground biomass carbon [tC/ha]
- `Debris_tCha` - Debris carbon [tC/ha]
- `Soil_tCha` - Soil carbon [tC/ha]
- `NPP_tCha_yr` - Net Primary Productivity [tC/ha/year]
- ... (many other pools and fluxes)

**Complete workflow script:** [get_PLO.py](get_PLO.py)

### Step 4: Process Results (Optional)

**Convert XML cache to NetCDF/GeoTIFF for spatial analysis:**

```bash
python XML2NC.py
```

**What it does:**
- Reads cache index (`downloaded/successful_downloads.txt`)
- Extracts climate, soil, and simulation data from XML files
- Creates spatially gridded xarray DataArrays
- Exports to NetCDF and GeoTIFF formats in `data/processed/`

**See:** [Development Guide](docs/claude/development.md#pattern-convert-xml-to-netcdfgeotiff) for custom processing examples

## Key Features

### Intelligent Caching System

**Cache Index:** `downloaded/successful_downloads.txt`

**Benefits:**
- **Fast startup:** Reading cache file takes ~1 second vs scanning millions of files (minutes/hours)
- **Resume on interruption:** No state loss if download crashes
- **Thread-safe:** Concurrent downloads logged safely
- **Zero overhead:** Simple text file, no database required

**Performance Comparison:**

| Operation | Without Cache | With Cache |
|-----------|---------------|------------|
| Check 100k files | 5-10 minutes | ~1 second |
| Resume after crash | Re-scan directory | Instant |
| Parallel downloads | Race conditions | Thread-safe |

**Cache Management:**
```bash
# Rebuild cache from existing files (if cache deleted/corrupted)
python tools/cache_manager.py rebuild

# Verify cache integrity (check all files exist)
python tools/cache_manager.py verify
```

**See:** [Architecture Guide](docs/claude/architecture.md#caching-system) for implementation details

### PLO File Generation

**13 Sections Generated:**
1. **Meta** - Plot metadata and notes
2. **Config** - Simulation configuration flags
3. **Timing** - Start/end years, time steps
4. **Build** - Geographic location, spatial parameters
5. **Site** - Climate time series (temp, rainfall, evap, FPI)
6. **Species** - Eucalyptus globulus growth calibrations
7. **Soil** - Soil carbon pools and texture
8. **Init** - Initial carbon pool values
9. **Event** - Management events timeline
10. **OutWinSet** - GUI output window settings
11. **LogEntrySet** - Audit log entries
12. **Mnrl_Mulch** - Nitrogen cycling parameters
13. **other_info** - Economic/sensitivity settings

**See:** [PLO Files Guide](docs/claude/plo-files.md) for XML structure and validation rules

## Common Operations

| Task | Command/Code | Documentation |
|------|-------------|---------------|
| Download bulk data | `python get_data.py` | [Architecture →](docs/claude/architecture.md#data-download-pipeline) |
| Generate PLO file | `assemble_plo_sections(lon, lat, year_start)` | [API Reference →](docs/claude/api-reference.md#assemble_plo_sectionslat-lon-year_start2010) |
| Run simulation | See [get_PLO.py](get_PLO.py) | [Development →](docs/claude/development.md#workflow-2-generate-plo-and-run-simulation) |
| Convert to NetCDF | `python XML2NC.py` | [Development →](docs/claude/development.md#pattern-convert-xml-to-netcdfgeotiff) |
| Rebuild cache | `python tools/cache_manager.py rebuild` | [API Reference →](docs/claude/api-reference.md#cache-management-functions) |
| Verify cache | `python tools/cache_manager.py verify` | [API Reference →](docs/claude/api-reference.md#cache-management-functions) |

## Examples

### Example 1: Batch Process Multiple Locations

```python
import pandas as pd
from tools.plo_section_functions import assemble_plo_sections

# Define locations
locations = pd.DataFrame({
    'name': ['Plot_A', 'Plot_B', 'Plot_C'],
    'lat': [-35.61, -36.12, -34.89],
    'lon': [148.16, 149.23, 147.45]
})

# Generate PLO files
for idx, row in locations.iterrows():
    try:
        plo_xml = assemble_plo_sections(row['lon'], row['lat'], year_start=2010)

        # Save to file
        with open(f"{row['name']}.plo", "w", encoding="utf-8") as f:
            f.write(plo_xml)

        print(f"✓ Created {row['name']}.plo")
    except FileNotFoundError as e:
        print(f"✗ Skipping {row['name']}: Cache data not found")
```

### Example 2: Extract Climate Data from Cache

```python
from tools.XML2Data import get_siteinfo_data
import matplotlib.pyplot as plt

# Load climate data for Canberra
climate_ds = get_siteinfo_data(lat=-35.61, lon=148.16, year=2020)

# Plot monthly temperature
temp_2020 = climate_ds.avgAirTemp.sel(year=2020)
plt.plot(range(1, 13), temp_2020.values, marker='o')
plt.xlabel('Month')
plt.ylabel('Temperature (°C)')
plt.title('Canberra Temperature 2020')
plt.savefig('temperature_2020.png')
```

### Example 3: Analyze Simulation Results

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load simulation results
df = pd.read_csv('downloaded/df_-35.61_148.16.csv')

# Plot carbon stocks over time
plt.figure(figsize=(10, 6))
plt.plot(df['Year'], df['TotalC_tCha'], label='Total Carbon', linewidth=2)
plt.plot(df['Year'], df['AboveGround_tCha'], label='Aboveground', linestyle='--')
plt.plot(df['Year'], df['Soil_tCha'], label='Soil', linestyle=':')
plt.xlabel('Year')
plt.ylabel('Carbon Stock (tC/ha)')
plt.legend()
plt.grid(True)
plt.savefig('carbon_stocks.png')
```

**More examples:** [Development Guide](docs/claude/development.md)

## Documentation

### User Documentation
- **[README.md](README.md)** (this file) - Quick start and usage guide
- **[FullCAM Documentation Complete](docs/FullCAM_Documentation_Complete.html)** - Official parameter specifications
- **[FullCAM API Documentation](docs/FullCAM%20Databuilder%20API%20Documentation%20v0.1%20DRAFT.pdf)** - REST API reference

### Developer Documentation (Claude Code)
- **[CLAUDE.md](CLAUDE.md)** - Navigation hub for Claude Code
- **[Architecture Guide](docs/claude/architecture.md)** - System design, module responsibilities, data flow
- **[API Reference](docs/claude/api-reference.md)** - Function signatures, parameters, API endpoints
- **[PLO Files Guide](docs/claude/plo-files.md)** - XML structure, sections, validation rules
- **[Development Patterns](docs/claude/development.md)** - Common workflows and code examples

## Troubleshooting

### Issue: "Invalid API key"
**Error:** `401 Unauthorized`

**Solution:** Check `FULLCAM_API_KEY` environment variable is set correctly:
```bash
# Windows
echo %FULLCAM_API_KEY%

# Linux/Mac
echo $FULLCAM_API_KEY
```

### Issue: "Site info not found"
**Error:** `FileNotFoundError: downloaded/siteInfo_148.16_-35.61.xml`

**Solution:** Run `get_data.py` first to download cache data for this location, or download individual location manually (see [Development Guide](docs/claude/development.md#workflow-4-download-data-for-new-location))

### Issue: "Slow startup"
**Problem:** `get_data.py` takes minutes to start

**Solution:** Rebuild cache index:
```bash
python tools/cache_manager.py rebuild
```

### Issue: "Time series count mismatch"
**Error from simulator:** `Expected 2412 values, found 2400`

**Solution:** PLO file has invalid time series. Check `rawTS` count attribute matches actual number of values. See [PLO Files Guide](docs/claude/plo-files.md#validation-rules) for validation.

**More troubleshooting:** [Development Guide](docs/claude/development.md#troubleshooting)

## Version Compatibility

- **FullCAM 2024:** PLO version `5009` (current default)
- **FullCAM 2020:** PLO version `5007` (legacy)
- **API Version:** `/2024/` in endpoint paths
- **Python:** 3.8 or higher recommended

## License

This code interfaces with FullCAM, which is licensed under **Creative Commons Attribution 4.0 International License** by the Australian Department of Climate Change, Energy, the Environment and Water (DCCEEW).

## Resources

- **Official Documentation:** https://dcceew.gov.au
- **FullCAM Support:** fullcam@dcceew.gov.au
- **API Portal:** Contact DCCEEW for API access

## Contributing

When modifying this codebase:

1. Follow parameter ordering convention (required first, optional with defaults)
2. Use NumPy-style docstrings for all functions
3. Test PLO files with FullCAM simulator before committing
4. Update documentation when adding new patterns or modules
5. **Never commit API keys** - use environment variables only

## Security Note

**API Key Security:**
- ✅ Use `FULLCAM_API_KEY` environment variable
- ❌ Never hardcode API keys in source files
- ❌ Never commit keys to version control
- ❌ Never share keys publicly

If you accidentally expose your key, contact DCCEEW immediately for rotation.

## Contact

For questions about this toolkit:
- Create an issue on the repository
- Contact the project maintainers

For FullCAM model questions:
- Email: fullcam@dcceew.gov.au
- Official documentation: https://dcceew.gov.au
