# Architecture Guide

This document describes the system architecture, module design, and data flow for the FullCAM REST API toolkit.

## System Overview

The codebase consists of **three main pipelines**:

```
┌──────────────────┐    ┌────────────────┐    ┌──────────────────┐
│  PLO Generation  │───▶│  Simulation    │───▶│ Data Processing  │
│    Pipeline      │    │   Pipeline     │    │    Pipeline      │
└──────────────────┘    └────────────────┘    └──────────────────┘
   tools/__init__.py    RUN_FullCAM2024.py      FullCAM2NC.py
```

### Pipeline 1: PLO Generation + Data Download

**Module:** [tools/__init__.py](../../tools/__init__.py)

**Purpose:** Generate PLO files from cached API data and download data if missing

**Key Features:**
- Identifies valid coordinates from LUTO land use raster (`data/lumap.tif`)
- Downloads siteInfo data with consensus mechanism (3 matching responses)
- Auto-downloads missing data when generating PLO files
- Thread-safe caching via `downloaded/successful_downloads.txt`

**Key Function:** `assemble_plo_sections(lon, lat, species, year_start=2010)`

**Architecture:**
```
assemble_plo_sections()
├── create_meta_section()           # Plot metadata
├── create_config_section()         # Simulation flags (from dataholder_config.xml)
├── create_timing_section()         # Time parameters (from dataholder_timing.xml)
├── create_build_section()          # Location & spatial params
├── create_site_section()           # Loads siteInfo XML + dataholder_site.xml
├── create_species_section()        # Loads species template (dataholder_species_*.xml)
├── create_soil_section()           # Loads siteInfo XML + dataholder_soil.xml
├── create_init_section()           # Loads siteInfo XML + dataholder_init.xml
├── create_event_section()          # Loads dataholder_event_block.xml
├── create_outwinset_section()      # Loads dataholder_OutWinSet.xml
├── create_logentryset_section()    # Loads dataholder_logentryset.xml
├── create_mnrl_mulch_section()     # Loads dataholder_Mnrl_Mulch.xml
└── create_other_info_section()     # Loads dataholder_other_info.xml
```

**Data Sources:**
- `downloaded/siteInfo_{lon}_{lat}.xml` - Climate/soil data (downloaded on demand)
- `data/dataholder_*.xml` - Section templates
- `data/dataholder_species_*.xml` - Species templates (Eucalyptus_globulus, Mallee_eucalypt, Environmental_plantings)

**Helper Functions in tools/__init__.py:**
- `get_siteinfo(lat, lon)` - Download siteInfo with consensus mechanism
- `get_species(lat, lon)` - Download species data
- `get_downloading_coords(resfactor)` - Get grid coordinates from LUTO raster
- `get_plot_simulation(lon, lat, url, headers)` - Run simulation via API

**Output:** Complete PLO XML string ready for simulation

### Pipeline 2: Simulation

**Module:** [RUN_FullCAM2024.py](../../RUN_FullCAM2024.py)

**Purpose:** Run batch FullCAM simulations for multiple locations

**Workflow:**
```python
1. Load coordinates from LUTO raster (via get_downloading_coords)
2. Check cache for existing simulation results
3. Generate PLO files: assemble_plo_sections(lon, lat, species, year_start)
4. Submit to FullCAM Simulator API via get_plot_simulation()
5. Save results to downloaded/df_{lon}_{lat}.csv
```

**API Interaction:**
- **Endpoint:** `POST /2024/fullcam-simulator/run-plotsimulation`
- **Input:** PLO file as multipart form data
- **Output:** CSV with columns: Year, TotalC_tCha, AboveGround_tCha, BelowGround_tCha, etc.

### Pipeline 3: Data Processing

**Modules:**
- [FullCAM2NC.py](../../FullCAM2NC.py) - Convert simulation results to NetCDF/GeoTIFF
- [tools/XML2Data.py](../../tools/XML2Data.py) - Parse API cache XML
- [tools/FullCAM2020_to_NetCDF/](../../tools/FullCAM2020_to_NetCDF/) - Legacy PLO processing

**Purpose:** Convert XML data to NetCDF/GeoTIFF for spatial analysis

**Workflow (FullCAM2NC.py):**
```python
1. Load cache index via get_existing_downloads()
2. Get grid coordinates via get_downloading_coords(resfactor)
3. Extract data using XML2Data functions:
   - get_siteinfo_data() → Climate time series
   - get_carbon_data() → Simulation results
4. Create xarray DataArrays with spatial dimensions
5. Export to NetCDF and GeoTIFF formats
```

**Key Functions in XML2Data.py:**
- `parse_site_data(xml_string)` → xr.Dataset with climate/FPI data
- `parse_soil_data(xml_string)` → Extract soil clay fraction
- `parse_init_data(xml_string, tsmd_year)` → Extract initial soil carbon
- `get_siteinfo_data(lon, lat, tsmd_year)` → Load + parse siteInfo file
- `get_carbon_data(lon, lat)` → Load simulation results CSV
- `export_to_geotiff_with_band_names(arr, output_path)` → Save with band names

**Output:** NetCDF/GeoTIFF files in `data/processed/` directory

## Caching System

### Cache Index Design

**File:** `downloaded/successful_downloads.txt`

**Format:** Plain text, one filename per line
```
siteInfo_148.16_-35.61.xml
species_148.16_-35.61.xml
siteInfo_149.23_-36.12.xml
species_149.23_-36.12.xml
...
```

**Benefits:**

| Feature | Without Cache | With Cache |
|---------|---------------|------------|
| Startup time (100k files) | 5-10 minutes (filesystem scan) | ~1 second (text file read) |
| Resume after crash | Re-scan entire directory | Instant (read cache) |
| Parallel safety | Race conditions possible | Thread-safe append |
| Memory usage | High (scan all files) | Low (read text file) |

### Cache Management

**Module:** [tools/helpers/cache_manager.py](../../tools/helpers/cache_manager.py)

**Functions:**
```python
get_existing_downloads()  # Read cache index, return sets of filenames
rebuild_cache()          # Scan downloaded/ and recreate cache file
verify_cache()          # Check all cached files exist on disk
```

**Commands:**
```python
# Rebuild cache from scratch (one-time slow operation)
from tools.helpers.cache_manager import rebuild_cache
rebuild_cache()

# Load existing downloads
from tools.helpers.cache_manager import get_existing_downloads
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads()
```

**When to rebuild cache:**
- Cache file deleted or corrupted
- Manually copied files from another system

### Thread-Safe Logging

**In tools/__init__.py:**
```python
from threading import Lock
_cache_write_lock = Lock()

# Thread-safe append to cache file
with _cache_write_lock:
    with open(download_records, 'a', encoding='utf-8') as cache:
        cache.write(f'{filename}\n')
```

**Why this works:**
- Uses threading.Lock for proper synchronization
- Each thread writes a complete line (no partial writes)

## Module Responsibilities

### Core Modules

| Module | Responsibilities |
|--------|------------------|
| [RUN_FullCAM2024.py](../../RUN_FullCAM2024.py) | Run batch FullCAM simulations |
| [FullCAM2NC.py](../../FullCAM2NC.py) | Convert results to NetCDF/GeoTIFF |
| [tools/__init__.py](../../tools/__init__.py) | PLO generation (13 sections), API utilities, data download |
| [tools/XML2Data.py](../../tools/XML2Data.py) | Parse API cache XML, extract time series |

### Utility Modules

| Module | Responsibilities |
|--------|------------------|
| [tools/helpers/cache_manager.py](../../tools/helpers/cache_manager.py) | Cache rebuild, load, utilities |
| [tools/helpers/batch_manipulate_XML.py](../../tools/helpers/batch_manipulate_XML.py) | Batch XML processing |
| [tools/helpers/get_fullcam_help.py](../../tools/helpers/get_fullcam_help.py) | FullCAM documentation helper |
| [tools/FullCAM2020_to_NetCDF/](../../tools/FullCAM2020_to_NetCDF/) | Legacy PLO processing |
| [tools/Get_data/](../../tools/Get_data/) | Data acquisition (ANUClim, FPI, soil) |

## Data Flow Diagram

```
┌──────────────────┐
│   LUTO Raster    │
│   (lumap.tif)    │
└─────────┬────────┘
          │
          ▼
┌──────────────────────────────────────────┐
│       tools/__init__.py                  │
│  • get_downloading_coords() - grid setup │
│  • get_siteinfo() - download with        │
│    consensus mechanism                   │
│  • assemble_plo_sections() - generate    │
│    complete PLO files                    │
│  • get_plot_simulation() - run via API   │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│     downloaded/ Directory (Cache)        │
│  • siteInfo_{lon}_{lat}.xml              │
│  • df_{lon}_{lat}.csv (simulation)       │
│  • successful_downloads.txt (index)      │
└──────┬───────────────────────────────────┘
       │
       ├──────────────────────────┬─────────────────────┐
       │                          │                     │
       ▼                          ▼                     ▼
┌──────────────┐      ┌──────────────────┐   ┌─────────────────┐
│ XML2Data.py  │      │ RUN_FullCAM2024  │   │ FullCAM2NC.py   │
│              │      │ .py              │   │                 │
│ Parse XML →  │      │ Batch simulation │   │ Results →       │
│ xarray       │      │ workflow         │   │ NetCDF/GeoTIFF  │
└──────┬───────┘      └─────────┬────────┘   └────────┬────────┘
       │                        │                      │
       ▼                        ▼                      ▼
┌──────────────────────────────────────────┐
│     data/processed/ Directory            │
│  • siteinfo_RES.nc (climate data)        │
│  • carbonstock_RES.nc (carbon stocks)    │
│  • GeoTIFF files (spatial rasters)       │
└──────────────────────────────────────────┘
```

## Design Patterns

### Pattern: Required vs Optional Parameters

All section creation functions follow this convention:

```python
def create_build_section(
    lonBL, latBL,              # Required: no defaults
    frCat="null",              # Optional: with sensible default
    areaBL="OneKm",            # Optional: with sensible default
    applyDownloadedData="true" # Optional: with sensible default
):
    """Build section for PLO file"""
    ...
```

**Rules:**
1. Required parameters come first (no default value)
2. Optional parameters follow (with default empty string or sensible value)
3. Functions raise errors for missing required params
4. Defaults represent most common use cases

### Pattern: XML Fragment Generation

All section functions return XML fragments (not complete documents):

```python
def create_meta_section(nmME="New_Plot", notesME=""):
    """Generate Meta section XML fragment"""
    return f'<Meta nmME="{nmME}" notesME="{notesME}"/>'

# Returns: <Meta nmME="New_Plot" notesME=""/>
# NOT: <?xml version="1.0"?><Meta>...</Meta>
```

**Assembly happens in `assemble_plo_sections()`:**
```python
def assemble_plo_sections(lon, lat, year_start):
    meta = create_meta_section("Plot_Name")
    config = create_config_section()
    # ... other sections

    # Add XML declaration and root wrapper here
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<DocumentPlot version="5009">
{meta}
{config}
...
</DocumentPlot>'''
```

### Pattern: Data Loading with Fallback

Functions load data from cache with error handling:

```python
def create_site_section(lon, lat):
    """Load site data from cache or raise error"""
    siteinfo_path = f"downloaded/siteInfo_{lon}_{lat}.xml"

    if not os.path.exists(siteinfo_path):
        raise FileNotFoundError(
            f"Site info not found: {siteinfo_path}\n"
            f"Run get_data.py first to download cache data"
        )

    with open(siteinfo_path, 'r', encoding='utf-8') as f:
        siteinfo_xml = f.read()

    # Parse and merge with template...
```

### Pattern: Template Merging

Functions merge API data with XML templates:

```python
def create_soil_section(lon, lat, yr0TS):
    # 1. Load template
    with open('data/dataholder_soil.xml', 'r') as f:
        template = etree.fromstring(f.read())

    # 2. Load API data
    with open(f'downloaded/siteInfo_{lon}_{lat}.xml', 'r') as f:
        api_data = etree.fromstring(f.read())

    # 3. Extract values from API
    soil_elem = api_data.find('.//LocnSoil')
    init_om = soil_elem.get('initOMF')

    # 4. Update template
    template.set('initOMF', init_om)

    # 5. Return merged XML
    return etree.tostring(template, encoding='unicode')
```

## Dependencies

### Required Packages

```python
requests       # HTTP API calls (get_data.py, get_PLO.py)
lxml          # XML parsing/generation (all modules)
pandas        # CSV/DataFrame handling (XML2Data.py)
rioxarray     # Geospatial raster I/O (get_data.py, XML2NC.py)
xarray        # Multi-dimensional arrays (XML2Data.py, XML2NC.py)
numpy         # Numerical operations (XML2Data.py, XML2NC.py)
joblib        # Parallel processing (get_data.py, XML2NC.py)
tqdm          # Progress bars (get_data.py, XML2NC.py)
affine        # Affine transforms (XML2NC.py)
rasterio      # GeoTIFF export (XML2Data.py)
```

### Optional Packages

```python
scandir_rs    # Fast directory scanning (XML2NC_PLO.py only)
              # Project works without it, just slower for large directories
```

### Installation

```bash
# Core dependencies
pip install requests lxml pandas rioxarray xarray numpy joblib tqdm affine rasterio

# Optional (for faster directory scanning)
pip install scandir_rs
```

## File Naming Conventions

### Downloaded Cache Files

```
siteInfo_{lon}_{lat}.xml       # Climate/soil/FPI data from API
species_{lon}_{lat}.xml        # Species parameters from API
df_{lat}_{lon}.csv             # Simulation results (note: lat/lon reversed!)
```

**Important:** CSV filenames use `df_{lat}_{lon}.csv` (lat first), while XML uses `{lon}_{lat}` (lon first). This inconsistency exists in the codebase.

### Template Files

```
dataholder_site.xml            # Site section template
dataholder_soil.xml            # Soil section template
dataholder_init.xml            # Init section template
dataholder_event_block.xml     # Event section template
dataholder_OutWinSet.xml       # GUI output template
dataholder_logentryset.xml     # Log entries template
dataholder_Mnrl_Mulch.xml      # Nitrogen/mulch template
dataholder_other_info.xml      # Economic/sensitivity template
```

### Processed Outputs

```
data/processed/{variable}_{resolution}.nc        # NetCDF files
data/processed/{variable}_{resolution}.tif       # GeoTIFF files
```

Example: `data/processed/avgAirTemp_OneKm.nc`

## Performance Characteristics

### RUN_FullCAM2024.py (Batch Simulation)

**Typical Performance:**
- **Coordinates:** Configurable via resfactor (10 = ~5,000 locations)
- **Threads:** 20 concurrent (configurable)
- **Retry Logic:** Up to 5 attempts with exponential backoff

**Optimization Strategies:**
1. Cache index lookup via get_existing_downloads()
2. Parallel execution via joblib.Parallel
3. Skip already-processed coordinates
4. Thread-safe cache file updates

### FullCAM2NC.py (Batch Processing)

**Typical Performance:**
- **Files:** ~100,000 XML files
- **Threads:** Configurable (default: CPU cores)
- **Speed:** ~1000 files/minute
- **Total Time:** 1-2 hours for full Australia
- **Memory:** Processes in chunks to avoid OOM

**Optimization Strategies:**
1. Cache index: Fast coordinate lookup without filesystem scan
2. Parallel parsing: Process multiple files simultaneously
3. Chunked processing: Avoid loading all data into memory
4. Lazy evaluation: Use xarray's lazy loading

## Error Handling

### API Request Errors

```python
# In get_data.py
for attempt in range(8):  # Up to 8 retries
    try:
        response = requests.get(url, params=params, headers=headers, timeout=100)
        if response.status_code == 200:
            return response  # Success
        else:
            if attempt < 7:
                time.sleep(2**attempt)  # Exponential backoff
    except requests.RequestException as e:
        if attempt < 7:
            time.sleep(2**attempt)
        else:
            raise  # Final attempt failed
```

### Missing Cache Files

```python
# In plo_section_functions.py
def create_site_section(lon, lat):
    siteinfo_path = f"downloaded/siteInfo_{lon}_{lat}.xml"
    if not os.path.exists(siteinfo_path):
        raise FileNotFoundError(
            f"Site info not found: {siteinfo_path}\n"
            f"Run get_data.py first to download cache data for this location"
        )
```

### XML Parsing Errors

```python
# In XML2Data.py
try:
    root = etree.fromstring(xml_string.encode('utf-8'))
except etree.XMLSyntaxError as e:
    raise ValueError(f"Invalid XML format: {e}")
```

## Testing Strategy

**Current State:** No formal test suite exists

**Recommended Testing Approach:**

1. **Unit Tests:** Test individual section creation functions
   ```python
   def test_create_meta_section():
       result = create_meta_section("Test_Plot")
       assert 'nmME="Test_Plot"' in result
   ```

2. **Integration Tests:** Test full PLO generation and simulation
   ```python
   def test_plo_generation():
       plo = assemble_plo_sections(148.16, -35.61, 2010)
       assert '<?xml version' in plo
       assert '<DocumentPlot version="5009">' in plo
   ```

3. **Data Validation:** Verify cached files are well-formed
   ```python
   def test_cache_integrity():
       verify_cache()  # Should not raise errors
   ```

## Future Improvements

**Potential Enhancements:**

1. **Async I/O:** Replace `requests` with `aiohttp` for better concurrency
2. **Database Cache:** Store metadata in SQLite for faster lookups
3. **Progress Persistence:** Save download progress to resume exact state after crash
4. **Validation:** Add XML schema validation for generated PLO files
5. **Testing:** Add comprehensive unit/integration tests
6. **CLI:** Create command-line interface for common operations
7. **Logging:** Replace print statements with proper logging module

## Security Considerations

### API Key Management

**Current Implementation:**
```python
import os
API_KEY = os.getenv("FULLCAM_API_KEY")
if not API_KEY:
    raise ValueError("FULLCAM_API_KEY environment variable not set")
```

**Security Best Practices:**
- ✅ Use environment variables (not hardcoded)
- ✅ Check key exists before making requests
- ✅ Never commit keys to git (.gitignore configured)
- ❌ No key rotation mechanism
- ❌ No rate limit handling beyond retries

### Data Validation

**Current Implementation:**
- Minimal validation on API responses
- Trust FullCAM API to return valid XML
- No sanitization of user-provided coordinates

**Recommendations:**
1. Validate coordinate ranges (lat: -90 to 90, lon: -180 to 180)
2. Validate XML structure before parsing
3. Sanitize file paths to prevent directory traversal
4. Add checksums to cache files for integrity verification

## Related Documentation

- **[API Reference](api-reference.md)** - Function signatures and parameters
- **[PLO Files Guide](plo-files.md)** - XML structure and sections
- **[Development Guide](development.md)** - Common workflows and patterns
