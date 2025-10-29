# PLO File Section Functions

This module provides modular functions for creating FullCAM PLO (Plot) file sections programmatically.

## Overview

The PLO file generation has been refactored into separate functions, each responsible for creating a specific XML section:

- **`create_meta_section()`** - Plot metadata (name, notes, version info)
- **`create_config_section()`** - Simulation configuration
- **`create_timing_section()`** - Timing and simulation period
- **`create_build_section()`** - Geographic location
- **`create_site_section()`** - Site parameters with time series container
- **`create_timeseries()`** - Individual time series data

## Key Design Principles

### 1. Required Parameters First
Functions accept required (non-empty) parameters first, followed by optional parameters with default values.

**Example:**
```python
create_meta_section(
    nmME,                    # Required: Plot name
    savedByResearch="true",  # Optional: defaults to "true"
    savedByVersion="",       # Optional: defaults to ""
    lockTime="",             # Optional: defaults to ""
    # ... more optional params
)
```

### 2. Proper Python Docstrings
All functions include NumPy-style docstrings with:
- Function description
- Parameter documentation (with types, defaults, and valid values)
- Return type documentation
- Usage examples

### 3. HEAD Section Skipped
The XML declaration (`<?xml version="1.0"...?>`) and root `DocumentPlot` wrapper are added automatically by the `assemble_plo_full()` function, so individual section functions don't include them.

## Usage Examples

### Basic Usage

```python
from plo_section_functions import (
    create_meta_section,
    create_config_section,
    create_timing_section,
    create_build_section,
    create_site_section,
    create_timeseries
)

# Create metadata section
meta = create_meta_section("My_Plot_2025", notesME="Test plot")

# Create config section
config = create_config_section(tPlot="CompF", userMulchF="true")

# Create timing section (2020-2050)
timing = create_timing_section(stYrYTZ="2020", enYrYTZ="2050")

# Create build section (location required)
build = create_build_section(lonBL=148.16, latBL=-35.61)
```

### Creating Time Series Data

```python
# Monthly temperature data
temps = [15.68, 17.65, 13.03, 10.66, 5.53, 4.72,
         2.97, 3.65, 4.72, 9.66, 11.96, 15.80]
ts_temp = create_timeseries(
    tInTS="avgAirTemp",
    rawTS_values=temps,
    yr0TS="2020",
    nYrsTS="1",
    dataPerYrTS="12"
)

# Monthly rainfall data
rainfall = [172.91, 42.76, 91.18, 213.70, 130.61, 157.46,
            119.02, 309.44, 264.66, 115.63, 194.56, 89.46]
ts_rain = create_timeseries(
    tInTS="rainfall",
    rawTS_values=rainfall,
    yr0TS="2020",
    nYrsTS="1"
)
```

### Creating Site Section with Multiple Time Series

```python
# Create multiple time series
ts_list = [ts_temp, ts_rain]

# Create site section containing all time series
site = create_site_section(
    count=2,                  # Number of time series
    timeseries_list=ts_list,  # List of TimeSeries XML strings
    maxAbgMF="979.24",        # Optional: max aboveground biomass
    fpiAvgLT="8.85"          # Optional: Forest Productivity Index
)
```

### Assembling Complete PLO File

```python
from get_FullCAM_plo_file import assemble_plo_full, save_plo_file

# Assemble all sections into complete PLO document
plo_content = assemble_plo_full(
    meta=meta,
    config=config,
    timing=timing,
    build=build,
    site_timeseries=site
)

# Save to file
save_plo_file(plo_content, "my_plot.plo")
```

## Function Reference

### create_meta_section()

**Required Parameters:**
- `nmME` (str): Plot name

**Optional Parameters:**
- `savedByResearch` (str): "true" or "false", default "true"
- `savedByVersion` (str): Version string, default ""
- `lockTime` (str): ISO timestamp, default ""
- `lockId` (str): User/system ID, default ""
- `lockOnME` (str): "true" or "false", default ""
- `notesME` (str): Plot notes, default ""

### create_config_section()

**All Parameters Optional (defaults provided):**
- `tPlot` (str): Plot type - "CompF", "SoilF", "CompA", "SoilA", "CompM"
- `userSoilMnrl` (str): "true" or "false"
- `tTreeProd` (str): Tree productivity model
- Plus 19+ additional configuration flags

### create_timing_section()

**All Parameters Optional (defaults provided):**
- `stYrYTZ` (str): Starting year, default "2010"
- `enYrYTZ` (str): Ending year, default "2100"
- `stepsPerYrYTZ` (str): Steps per year, default "110"
- Plus 12+ additional timing parameters

### create_build_section()

**Required Parameters:**
- `lonBL` (str/float): Longitude in decimal degrees
- `latBL` (str/float): Latitude in decimal degrees

**Optional Parameters:**
- `frCat` (str): Forest category, default "null"
- `applyDownloadedData` (str): "true" or "false", default "true"
- `areaBL` (str): Spatial averaging area, default "OneKm"
- `frFracBL` (str): Forest fraction, default ""

### create_site_section()

**Required Parameters:**
- `count` (str/int): Number of time series
- `timeseries_list` (list): List of TimeSeries XML strings

**Optional Parameters:**
- `tAirTemp` (str): Air temp input type, default "Direct"
- `maxAbgMF` (str): Max aboveground biomass for forest
- `fpiAvgLT` (str): Average Forest Productivity Index
- Plus 20+ additional site parameters

### create_timeseries()

**Required Parameters:**
- `tInTS` (str): Time series type (e.g., "avgAirTemp", "rainfall")
- `rawTS_values` (list): List of numeric values

**Optional Parameters:**
- `yr0TS` (str): Starting year, default "2010"
- `nYrsTS` (str): Number of years, default "1"
- `dataPerYrTS` (str): Data points per year, default "12"
- `tExtrapTS` (str): Extrapolation method, default "AvgYr"
- `tOriginTS` (str): Time reference, default "Calendar"
- Plus 10+ additional time series parameters

## Common Time Series Types

| Type | Description | Unit | Typical Frequency |
|------|-------------|------|-------------------|
| `avgAirTemp` | Average air temperature | °C | Monthly (12) |
| `rainfall` | Precipitation | mm | Monthly (12) |
| `openPanEvap` | Pan evaporation | mm | Monthly (12) |
| `forestProdIx` | Forest Productivity Index | unitless | Annual (1) |
| `defnitIrrigA` | Definite irrigation (ag) | mm | Monthly (12) |
| `conditIrrigF` | Conditional irrigation (forest) | mm | Monthly (12) |
| `soilTemp` | Soil temperature | °C | Monthly (12) |
| `VPD` | Vapor Pressure Deficit | kPa | Monthly (12) |
| `solarRad` | Solar radiation | MJ/m² | Monthly (12) |
| `fertility` | Soil fertility modifier | unitless | Monthly (12) |

## Complete Example

```python
from plo_section_functions import *
from get_FullCAM_plo_file import assemble_plo_full, save_plo_file

# 1. Create metadata
meta = create_meta_section(
    "Eucalyptus_Trial_2025",
    notesME="Trial plot for E. globulus in Tasmania"
)

# 2. Create configuration (Forest composite)
config = create_config_section(tPlot="CompF")

# 3. Set timing (30-year simulation)
timing = create_timing_section(stYrYTZ="2020", enYrYTZ="2050")

# 4. Set location (Tasmania)
build = create_build_section(
    lonBL=147.33,
    latBL=-42.88,
    frCat="Plantation",
    areaBL="OneKm"
)

# 5. Create climate time series
monthly_temps = [15.5, 16.8, 14.2, 11.5, 8.3, 6.1,
                 5.2, 6.4, 8.1, 10.9, 12.7, 14.3]
ts_temp = create_timeseries("avgAirTemp", monthly_temps,
                            yr0TS="2020", nYrsTS="1")

monthly_rain = [45.2, 38.7, 52.3, 61.8, 73.4, 82.1,
                91.5, 78.2, 65.4, 55.9, 48.3, 41.7]
ts_rain = create_timeseries("rainfall", monthly_rain,
                            yr0TS="2020", nYrsTS="1")

# 6. Create site section
site = create_site_section(
    count=2,
    timeseries_list=[ts_temp, ts_rain],
    maxAbgMF="850.5",
    fpiAvgLT="9.2"
)

# 7. Assemble and save
plo = assemble_plo_full(
    meta=meta,
    config=config,
    timing=timing,
    build=build,
    site_timeseries=site
)

save_plo_file(plo, "eucalyptus_trial_2025.plo")
```

## Testing

Run the test script to see example output:

```bash
python plo_section_functions.py
```

This will print formatted examples of each section type.

## Files

- **`plo_section_functions.py`** - Modular section creation functions (NEW)
- **`get_FullCAM_plo_file.py`** - Main assembler with raw templates (LEGACY)
- **`CLAUDE.md`** - Complete documentation of PLO file format

## Benefits

1. **Type Safety**: Function signatures make required vs optional parameters clear
2. **Documentation**: Full docstrings explain each parameter
3. **Flexibility**: Mix and match sections or use templates
4. **Maintainability**: Each section isolated in its own function
5. **Testability**: Easy to test individual sections

## Migration Guide

**Old approach (raw templates):**
```python
PLO_META = r'<Meta nmME="My_Plot" savedByResearch="true" .../>'
plo = assemble_plo_full()  # Uses defaults
```

**New approach (modular functions):**
```python
meta = create_meta_section("My_Plot")
plo = assemble_plo_full(meta=meta)
```

Both approaches work and can be mixed as needed!
