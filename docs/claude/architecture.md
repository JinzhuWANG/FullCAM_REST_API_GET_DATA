# Architecture Guide

This document describes the system architecture, module design, and data flow for the FullCAM REST API toolkit.

## System Overview

The codebase consists of **four main pipelines**:

```
┌─────────────────┐    ┌──────────────────┐    ┌────────────────┐    ┌──────────────────┐
│  Data Download  │───▶│  PLO Generation  │───▶│  Simulation    │───▶│ Data Processing  │
│   Pipeline      │    │    Pipeline      │    │   Pipeline     │    │    Pipeline      │
└─────────────────┘    └──────────────────┘    └────────────────┘    └──────────────────┘
   get_data.py      plo_section_functions.py     get_PLO.py          XML2NC.py
                                                                      XML2NC_PLO.py
```

### Pipeline 1: Data Download

**Module:** [get_data.py](../../get_data.py)

**Purpose:** Bulk download and cache API data for Australian locations

**Key Features:**
- Identifies valid coordinates from LUTO land use raster (`data/lumap.tif`)
- Downloads two types of data per location:
  - `siteInfo_{lon}_{lat}.xml` - Climate time series, soil data, FPI values
  - `species_{lon}_{lat}.xml` - Eucalyptus globulus (specId=8) parameters
- **35 concurrent threads** with exponential backoff retry (up to 8 attempts)
- **Intelligent caching system** (see [Caching System](#caching-system) below)

**Workflow:**
```python
1. Load Australian coordinates from lumap.tif (5x downsampled)
2. Read cache index (successful_downloads.txt)
3. Filter out already-downloaded coordinates
4. Parallel download with retry logic:
   - Request siteInfo from API
   - Request species data from API
   - Save to downloaded/ directory
   - Append to cache index (thread-safe)
5. Resume on interruption (cache provides state)
```

**Output:** Thousands of XML files in `downloaded/` directory

### Pipeline 2: PLO Generation

**Module:** [tools/plo_section_functions.py](../../tools/plo_section_functions.py)

**Purpose:** Generate complete PLO files from cached API data

**Key Function:** `assemble_plo_sections(lon, lat, year_start=2010)`

**Architecture:**
```
assemble_plo_sections()
├── create_meta_section()           # Plot metadata
├── create_config_section()         # Simulation flags
├── create_timing_section()         # Time parameters
├── create_build_section()          # Location & spatial params
├── create_site_section()           # Loads siteInfo XML + template
├── create_species_section()        # Loads species XML
├── create_soil_section()           # Loads siteInfo XML + template
├── create_init_section()           # Loads siteInfo XML + template
├── create_event_section()          # Loads event template
├── create_outwinset_section()      # Loads GUI template
├── create_logentryset_section()    # Loads log template
├── create_mnrl_mulch_section()     # Loads nitrogen template
└── create_other_info_section()     # Loads economic template
```

**Data Sources:**
- `downloaded/siteInfo_{lon}_{lat}.xml` - Climate/soil data
- `downloaded/species_{lon}_{lat}.xml` - Species parameters
- `data/dataholder_*.xml` - Section templates (8 files)

**Output:** Complete PLO XML string ready for simulation

### Pipeline 3: Simulation

**Module:** [get_PLO.py](../../get_PLO.py)

**Purpose:** End-to-end workflow from coordinates to simulation results

**Workflow:**
```python
1. Generate PLO file: assemble_plo_sections(lon, lat, year_start)
2. Submit to FullCAM Simulator API (POST multipart/form-data)
3. Receive CSV results (carbon stocks/fluxes over time)
4. Save to downloaded/df_{lat}_{lon}.csv
```

**API Interaction:**
- **Endpoint:** `POST /2024/fullcam-simulator/run-plotsimulation`
- **Input:** PLO file as multipart form data
- **Output:** CSV with columns: Year, TotalC_tCha, AboveGround_tCha, BelowGround_tCha, etc.

### Pipeline 4: Data Processing

**Modules:**
- [XML2NC.py](../../XML2NC.py) - Process API cache files
- [XML2NC_PLO.py](../../XML2NC_PLO.py) - Process PLO files
- [tools/XML2Data.py](../../tools/XML2Data.py) - Parse API cache XML
- [tools/XML2Data_PLO.py](../../tools/XML2Data_PLO.py) - Parse PLO XML

**Purpose:** Convert XML data to NetCDF/GeoTIFF for spatial analysis

**Workflow (XML2NC.py):**
```python
1. Load cache index (successful_downloads.txt)
2. Build coordinate map from cached files
3. Extract data using XML2Data functions:
   - get_siteinfo_data() → Climate time series
   - get_soilbase_data() → Soil parameters
   - get_soilInit_data() → Initial soil carbon
   - get_carbon_data() → Simulation results
4. Create xarray DataArrays with spatial dimensions
5. Export to NetCDF and GeoTIFF formats
```

**Key Functions in XML2Data.py:**
- `parse_siteinfo_data(xml_string)` → xr.Dataset with climate/FPI data
- `get_siteinfo_data(lat, lon, year=None)` → Load + parse siteInfo file
- `get_soilbase_data(lat, lon)` → Extract soil parameters
- `get_soilInit_data(lat, lon, year)` → Extract initial soil carbon
- `get_carbon_data(lat, lon)` → Load simulation results CSV
- `export_to_geotiff_with_band_names(arr, output_path, transform)` → Save with metadata

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

**Module:** [tools/cache_manager.py](../../tools/cache_manager.py)

**Functions:**
```python
get_existing_downloads()  # Read cache index, return sets of filenames
rebuild_cache()          # Scan downloaded/ and recreate cache file
verify_cache()          # Check all cached files exist on disk
```

**Commands:**
```bash
# Rebuild cache from scratch (one-time slow operation)
python tools/cache_manager.py rebuild

# Verify cache integrity
python tools/cache_manager.py verify
```

**When to rebuild cache:**
- Cache file deleted or corrupted
- Manually copied files from another system
- After running tools/copy_files.py

### Thread-Safe Logging

**In get_data.py:**
```python
def log_success(filename):
    """Append to cache file (thread-safe)"""
    with open('downloaded/successful_downloads.txt', 'a', encoding='utf-8') as f:
        f.write(f"{filename}\n")

# After successful download
save_xml(response.content, f"siteInfo_{lon}_{lat}.xml")
log_success(f"siteInfo_{lon}_{lat}.xml")
```

**Why this works:**
- File append operations are atomic on most filesystems
- Each thread writes a complete line (no partial writes)
- No file locking needed for simple appends

## Module Responsibilities

### Core Modules

| Module | Lines | Responsibilities |
|--------|-------|------------------|
| [get_data.py](../../get_data.py) | ~200 | Bulk API download, parallel processing, retry logic, cache management |
| [get_PLO.py](../../get_PLO.py) | ~100 | PLO generation, API simulation, results saving |
| [tools/plo_section_functions.py](../../tools/plo_section_functions.py) | ~2000 | 13 section creation functions, XML generation, data loading |
| [XML2NC.py](../../XML2NC.py) | ~300 | Batch XML→NetCDF conversion, GeoTIFF export, spatial gridding |
| [XML2NC_PLO.py](../../XML2NC_PLO.py) | ~250 | PLO→NetCDF conversion, similar to XML2NC.py but for PLO files |

### Utility Modules

| Module | Lines | Responsibilities |
|--------|-------|------------------|
| [tools/XML2Data.py](../../tools/XML2Data.py) | ~500 | Parse siteInfo/species XML, extract time series, load simulation results |
| [tools/XML2Data_PLO.py](../../tools/XML2Data_PLO.py) | ~400 | Parse PLO XML, extract Site/Soil/Init sections |
| [tools/cache_manager.py](../../tools/cache_manager.py) | ~250 | Cache rebuild, verification, utilities |
| [tools/batch_manipulate_XML.py](../../tools/batch_manipulate_XML.py) | ~100 | Batch XML processing utilities |
| [tools/get_fullcam_help.py](../../tools/get_fullcam_help.py) | ~800 | FullCAM documentation helper |

## Data Flow Diagram

```
┌──────────────────┐
│   LUTO Raster    │
│   (lumap.tif)    │
└─────────┬────────┘
          │
          ▼
┌──────────────────────────────────────────┐
│       get_data.py (Bulk Download)        │
│  • Extract coordinates (5x downsampled)  │
│  • Parallel API requests (35 threads)    │
│  • Exponential backoff retry             │
│  • Thread-safe cache logging             │
└──────────────┬───────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────┐
│     downloaded/ Directory (Cache)        │
│  • siteInfo_{lon}_{lat}.xml              │
│  • species_{lon}_{lat}.xml               │
│  • successful_downloads.txt (index)      │
└──────┬───────────────────────────────────┘
       │
       ├──────────────────────────┬─────────────────────┐
       │                          │                     │
       ▼                          ▼                     ▼
┌──────────────┐      ┌──────────────────┐   ┌─────────────────┐
│ XML2Data.py  │      │ plo_section_     │   │  get_PLO.py     │
│              │      │ functions.py     │   │                 │
│ Parse XML →  │      │ Generate PLO →   │   │ Workflow:       │
│ xarray       │      │ Assemble 13      │   │ 1. Gen PLO      │
│              │      │ sections         │   │ 2. Simulate     │
└──────┬───────┘      └─────────┬────────┘   │ 3. Save CSV     │
       │                        │             └────────┬────────┘
       │                        │                      │
       ▼                        ▼                      ▼
┌──────────────┐      ┌──────────────────┐   ┌─────────────────┐
│  XML2NC.py   │      │  FullCAM API     │   │ df_{lat}_{lon}  │
│              │      │  Simulator       │   │ .csv            │
│ XML → NetCDF │      │                  │   │ (results)       │
│ XML → GeoTIF │      │ Returns: CSV     │   └─────────────────┘
└──────┬───────┘      └─────────┬────────┘
       │                        │
       ▼                        ▼
┌──────────────────────────────────────────┐
│     data/processed/ Directory            │
│  • NetCDF files (time series grids)      │
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

### get_data.py (Bulk Download)

**Typical Performance:**
- **Coordinates:** ~50,000 Australian locations (5x downsampled)
- **Threads:** 35 concurrent
- **Speed:** ~100-200 downloads/minute (depends on API rate limits)
- **Total Time:** 4-8 hours for full Australia
- **Retry Logic:** Up to 8 attempts with exponential backoff (2^attempt seconds)

**Optimization Strategies:**
1. Cache index lookup: O(n) read at startup, O(1) append per download
2. Parallel execution: 35× faster than sequential
3. Early skip: Don't re-download existing files
4. Exponential backoff: Handle transient network errors gracefully

### XML2NC.py (Batch Processing)

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
