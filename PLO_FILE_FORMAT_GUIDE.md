# FullCAM PLO File Assembler - Complete Guide

## Overview

This Python module provides a comprehensive toolkit for programmatically assembling FullCAM PLO (Plot) files. PLO files are XML-based documents used by FullCAM (Full Carbon Accounting Model) for carbon accounting simulations in forestry and land use sectors.

### What is a PLO File?

A PLO file contains all the necessary data for FullCAM to simulate carbon dynamics in a forest or agricultural system:
- **Metadata**: Plot name, creation info, notes
- **Configuration**: Simulation settings and parameters
- **Timing**: Simulation period and time steps
- **Location Data**: Geographic coordinates and spatial parameters
- **Site Data**: Climate, soil, and environmental conditions (via time series)
- **Species Information**: Forest species parameters and growth models
- **Management Regimes**: Harvesting, thinning, and other management events

## Module Structure

### Main Class: `PLOBuilder`

The `PLOBuilder` class provides a fluent API for constructing PLO files using the builder pattern.

```python
from plo_assembler import PLOBuilder

# Create builder instance
builder = PLOBuilder(
    plot_name="My_Plot",
    plot_type="CompF",
    latitude=-35.61,
    longitude=148.16,
    version="5009"  # FullCAM 2024
)
```

### Key Parameters

| Parameter   | Type  | Description               | Valid Values                      |
| ----------- | ----- | ------------------------- | --------------------------------- |
| `plot_name` | str   | Display name for the plot | Any string                        |
| `plot_type` | str   | Type of analysis          | CompF, SoilF, CompA, SoilA, CompM |
| `latitude`  | float | Location latitude         | -90 to 90                         |
| `longitude` | float | Location longitude        | -180 to 180                       |
| `version`   | str   | FullCAM version           | "5007" (2020), "5009" (2024)      |

### Plot Types

- **CompF**: Forest Composite (above and below ground biomass)
- **SoilF**: Soil Only (forest soil analysis)
- **CompA**: Agricultural Composite
- **SoilA**: Soil Only (agricultural)
- **CompM**: Mixed system (forest and agricultural)

## Usage Examples

### Basic Usage

```python
from plo_assembler import PLOBuilder

# Initialize builder
builder = PLOBuilder(
    plot_name="Eucalyptus Plot",
    plot_type="CompF",
    latitude=-35.61,
    longitude=148.16
)

# Set metadata
builder.set_meta(
    name="My_Plot_Name",
    saved_by_research=True,
    notes="This is a sample plot"
)

# Configure plot
builder.set_config(
    tPlot="CompF",
    userSoilMnrl=True,
    tTreeProd="TYF"
)

# Set timing
builder.set_timing(
    start_year=2010,
    end_year=2100,
    steps_per_year=110,
    days_per_step=1
)

# Set location and build parameters
builder.set_build_location(
    latitude=-35.61,
    longitude=148.16,
    frCat="null",
    areaBL="OneKm",
    apply_downloaded_data=True
)

# Set site parameters
builder.set_site_parameters(
    tAirTemp="Direct",
    count=21,
    siteMultStemF=1.0,
    siteMultBranF=1.0,
    maxAbgMF=979.24
)

# Save the file
builder.save_plo_file("my_plot.plo")
```

### Adding Time Series Data

Time series data represents temporal variation in climate and environmental parameters:

```python
# Create time series for average air temperature (monthly values)
avg_temp = [15.68, 17.65, 13.03, 10.66, 5.53, 4.72,
            2.97, 3.65, 4.72, 9.66, 11.96, 15.80]

ts_temp = builder.add_timeseries(
    name="avgAirTemp",
    values=avg_temp,
    tInTS="avgAirTemp",
    yr0TS=1970,
    nYrsTS=54,
    dataPerYrTS=12
)

# Create time series for rainfall
rainfall = [172.91, 42.76, 91.18, 213.70, 130.61, 157.46,
            119.02, 309.44, 264.66, 115.63, 194.56, 89.46]

ts_rainfall = builder.add_timeseries(
    name="rainfall",
    values=rainfall,
    tInTS="rainfall",
    yr0TS=1970,
    nYrsTS=54,
    dataPerYrTS=12
)

# Build file with time series
builder.save_plo_file(
    "my_plot.plo",
    timeseries_list=[ts_temp, ts_rainfall]
)
```

### Method Chaining

All `set_*` methods support fluent interface (method chaining):

```python
builder = PLOBuilder(plot_name="Plot1", latitude=-35.61, longitude=148.16)
builder \
    .set_meta("My Plot", notes="Example") \
    .set_config(tPlot="CompF") \
    .set_timing(start_year=2010, end_year=2100) \
    .set_build_location(latitude=-35.61, longitude=148.16) \
    .set_site_parameters(tAirTemp="Direct")

builder.save_plo_file("output.plo")
```

## API Reference

### PLOBuilder Methods

#### `__init__(...)`
Initialize a new PLO builder instance.

**Parameters:**
- `plot_name` (str): Display name for the plot
- `plot_type` (str): Type of plot (default: "CompF")
- `latitude` (float): Location latitude (default: -35.61)
- `longitude` (float): Location longitude (default: 148.16)
- `version` (str): FullCAM version (default: "5009")
- `fileType` (str): File type identifier (default: "FullCAM Plot ")

#### `set_meta(name, saved_by_research=True, notes="")`
Set plot metadata.

**Parameters:**
- `name` (str): Plot name shown in FullCAM UI
- `saved_by_research` (bool): Mark as saved by research UI
- `notes` (str): Optional notes about the plot

**Returns:** Self (for method chaining)

#### `set_config(tPlot="CompF", userSoilMnrl=True, ...)`
Set plot configuration parameters.

**Parameters:**
- `tPlot` (str): Plot type (CompF, SoilF, CompA, SoilA, CompM)
- `userSoilMnrl` (bool): Use soil mineral data
- `userMulchF` (bool): User mulch for forest
- `userMulchA` (bool): User mulch for agriculture
- `tTreeProd` (str): Tree production type (default: "TYF")
- `**kwargs`: Additional configuration parameters

**Returns:** Self

#### `set_timing(start_year=2010, end_year=2100, steps_per_year=110, days_per_step=1)`
Configure simulation timing.

**Parameters:**
- `start_year` (int): Simulation start year
- `end_year` (int): Simulation end year
- `steps_per_year` (int): Number of steps per year (default: 110)
- `days_per_step` (int): Days per step (default: 1)

**Returns:** Self

#### `set_build_location(latitude=None, longitude=None, frCat="null", areaBL="OneKm", apply_downloaded_data=True)`
Set geographic location and spatial parameters.

**Parameters:**
- `latitude` (float): Location latitude (-90 to 90)
- `longitude` (float): Location longitude (-180 to 180)
- `frCat` (str): Forest category (null, MVG, Plantation, EnvMallee, ERF, ERFH)
- `areaBL` (str): Spatial averaging (Cell, Hectare, OneKm, TwoKm, ThreeKm, FiveKm)
- `apply_downloaded_data` (bool): Apply spatial data from API

**Returns:** Self

#### `set_site_parameters(tAirTemp="Direct", count=21, siteMultStemF=1.0, ...)`
Configure site-level parameters.

**Parameters:**
- `tAirTemp` (str): Air temperature data source
- `tVPD` (str): Vapor pressure deficit source
- `tSoilTemp` (str): Soil temperature source
- `count` (int): Number of time series
- `siteMultStemF` (float): Stem biomass multiplier
- `siteMultBranF` (float): Branch biomass multiplier
- `siteMultBarkF` (float): Bark biomass multiplier
- `siteMultLeafF` (float): Leaf biomass multiplier
- `siteMultCortF` (float): Cork/cortex multiplier
- `siteMultFirtF` (float): First growth multiplier
- `maxAbgMF` (float): Maximum aboveground biomass
- `fpiAvgLT` (float): Forest Productivity Index

**Returns:** Self

#### `add_timeseries(name, values, tInTS, ...)`
Create a time series data element.

**Parameters:**
- `name` (str): Time series name/key
- `values` (list): List of numeric values or empty strings for missing data
- `tInTS` (str): Type identifier (avgAirTemp, rainfall, etc.)
- `tExtrapTS` (str): Extrapolation type (default: "AvgYr")
- `tOriginTS` (str): Time origin (default: "Calendar")
- `yr0TS` (int): Starting year (default: 2010)
- `nYrsTS` (int): Number of years (default: 1)
- `dataPerYrTS` (int): Data points per year (default: 12)

**Returns:** Dictionary representation of TimeSeries

#### `save_plo_file(filename, timeseries_list=None, species_data="", regime_data="", pretty_print=True)`
Generate and save the PLO file.

**Parameters:**
- `filename` (str): Output filename (.plo)
- `timeseries_list` (list): List of time series dictionaries
- `species_data` (str): XML for species forest set
- `regime_data` (str): XML for regime set
- `pretty_print` (bool): Format XML nicely (default: True)

**Returns:** None (saves file to disk)

#### `build_plo_xml(...)`
Generate complete PLO XML string without saving.

**Returns:** String containing full PLO XML document

## Common Time Series Types

The following time series types are commonly used in FullCAM PLO files:

| Type         | Description                     | Unit     | Frequency |
| ------------ | ------------------------------- | -------- | --------- |
| avgAirTemp   | Average air temperature         | °C       | Monthly   |
| rainfall     | Precipitation                   | mm       | Monthly   |
| openPanEvap  | Pan evaporation                 | mm       | Monthly   |
| VPD          | Vapor pressure deficit          | kPa      | Monthly   |
| soilTemp     | Soil temperature                | °C       | Monthly   |
| solarRad     | Solar radiation                 | MJ/m²    | Monthly   |
| avgAge       | Average age of forest           | years    | Yearly    |
| fertility    | Soil fertility index            | unitless | Monthly   |
| conditIrrigF | Conditional irrigation (forest) | mm       | Monthly   |
| defnitIrrigF | Deficit irrigation (forest)     | mm       | Monthly   |

## Forest Category Values

- **null**: All categories
- **MVG**: Native Vegetation Groups
- **Plantation**: Plantation Species
- **EnvMallee**: Environmental and Mallees
- **ERF**: Emissions Reduction Fund Methods
- **ERFH**: ERF Methods with EMP-specific calibrations

## Spatial Averaging Areas

| Value   | Averaging Size                  | Use Case                           |
| ------- | ------------------------------- | ---------------------------------- |
| Cell    | Single grid cell (~100m × 100m) | High resolution, specific location |
| Hectare | 1 hectare (100m × 100m)         | Local site analysis                |
| OneKm   | 1 km² (1000m × 1000m)           | Regional small-scale               |
| TwoKm   | 2 km² (2000m × 2000m)           | Regional medium-scale              |
| ThreeKm | 3 km² (3000m × 3000m)           | Regional larger area               |
| FiveKm  | 5 km² (5000m × 5000m)           | Broad regional analysis            |

## Advanced Usage

### Working with API Data

To create a PLO file using FullCAM API data:

```python
import requests
from plo_assembler import PLOBuilder

# Fetch site info from FullCAM API
api_key = "YOUR_SUBSCRIPTION_KEY"
headers = {"Ocp-Apim-Subscription-Key": api_key}

response = requests.get(
    "https://api.dcceew.gov.au/climate/carbon-accounting/2024/data/v1/2024/data-builder/siteinfo",
    params={
        "latitude": -35.61,
        "longitude": 148.16,
        "area": "OneKm",
        "plotT": "CompF",
        "frCat": "null",
        "incGrowth": "true",
        "version": "2024"
    },
    headers=headers
)

# Use API data to build PLO
site_data = response.json()
builder = PLOBuilder(latitude=-35.61, longitude=148.16, version="5009")
# ... configure builder with API data ...
```

### Creating Multiple Plots

```python
from plo_assembler import PLOBuilder

locations = [
    {"name": "Plot1", "lat": -35.61, "lon": 148.16},
    {"name": "Plot2", "lat": -37.81, "lon": 144.96},
    {"name": "Plot3", "lat": -33.87, "lon": 151.21}
]

for loc in locations:
    builder = PLOBuilder(
        plot_name=loc["name"],
        latitude=loc["lat"],
        longitude=loc["lon"]
    )
    
    builder.set_meta(loc["name"]) \
           .set_config(tPlot="CompF") \
           .set_timing(2010, 2100)
    
    builder.save_plo_file(f"{loc['name']}.plo")
    print(f"Created {loc['name']}.plo")
```

### Batch Processing with Pandas

```python
import pandas as pd
from plo_assembler import PLOBuilder

# Load plot specifications from CSV
plots_df = pd.read_csv("plots.csv")

for idx, row in plots_df.iterrows():
    builder = PLOBuilder(
        plot_name=row['plot_name'],
        latitude=row['latitude'],
        longitude=row['longitude']
    )
    
    builder.set_meta(row['plot_name'], notes=row.get('notes', '')) \
           .set_config(tPlot=row.get('plot_type', 'CompF')) \
           .set_timing(
               start_year=int(row['start_year']),
               end_year=int(row['end_year'])
           )
    
    builder.save_plo_file(f"{row['plot_name']}.plo")
```

## PLO File Structure

A complete PLO file has the following structure:

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<DocumentPlot FileType="FullCAM Plot " Version="5009" pageIxDO="10" tDiagram="-1">
  <!-- Metadata about the plot -->
  <Meta nmME="Plot Name" savedByResearch="true" ...>
    <notesME>Plot notes</notesME>
  </Meta>
  
  <!-- Configuration and settings -->
  <Config tPlot="CompF" userSoilMnrl="true" ... />
  
  <!-- Timing and simulation period -->
  <Timing dailyTimingTZ="false" stYrYTZ="2010" enYrYTZ="2100" ... />
  
  <!-- Geographic location and build parameters -->
  <Build lonBL="148.16" latBL="-35.61" frCat="null" ... />
  
  <!-- Site data including climate time series -->
  <Site count="21" tAirTemp="Direct" ... >
    <TimeSeries tInTS="avgAirTemp" ... >
      <WinState L="10" T="83" clientW="702" clientH="450" ws="Normal"/>
      <rawTS count="12">15.68,17.65,13.03,10.66,5.53,4.72,...</rawTS>
    </TimeSeries>
    <!-- More time series ... -->
  </Site>
  
  <!-- Species forest set (optional) -->
  <SpeciesForestSet count="1" showOnlyInUse="false">
    <!-- Species definitions ... -->
  </SpeciesForestSet>
  
  <!-- Regime set (optional) -->
  <!-- Management regimes ... -->
</DocumentPlot>
```

## Troubleshooting

### Issue: "Invalid coordinate values"
**Solution**: Ensure latitude is between -90 and 90, and longitude is between -180 and 180.

### Issue: "XML parsing error"
**Solution**: If pretty_print is enabled, ensure all special characters are properly escaped. Try with `pretty_print=False`.

### Issue: "Time series count mismatch"
**Solution**: The `count` attribute should match the number of values. Use the `add_timeseries` method which handles this automatically.

### Issue: "PLO file not recognized by FullCAM"
**Solution**: 
- Check that version matches your FullCAM installation (5007 for 2020, 5009 for 2024)
- Verify all required sections are present
- Ensure XML is well-formed (use `pretty_print=True` to debug)

## Performance Tips

1. **Use method chaining** for cleaner code
2. **Pre-compute time series data** before creating TimeSeries objects
3. **Cache API responses** if building multiple plots from same location
4. **Use appropriate spatial averaging** (don't use Cell for broad regional analysis)
5. **Batch operations** with pandas for multiple plots

## File Size Considerations

- Basic PLO file: ~5-10 KB
- With 54 years of monthly climate data: ~50-100 KB
- With species details: ~200-500 KB
- Large files with full regime data: 1+ MB

PLO files can handle large time series efficiently. Monthly data for 50+ years typically adds only 50-100 KB.

## Integration with FullCAM API

The PLO Assembler pairs well with the FullCAM Data Builder API:

1. **Fetch site info** from API at specific coordinates
2. **Extract species list** from API response
3. **Build PLO file** using this module
4. **Upload to FullCAM** via web interface or API

Example workflow:
```python
# 1. Get site data from API
site_response = api.get_siteinfo(lat=-35.61, lon=148.16)

# 2. Create PLO using assembler
builder = PLOBuilder(latitude=-35.61, longitude=148.16)
builder.set_meta(name="API-Generated Plot")

# 3. Add API-sourced parameters
# builder.set_site_parameters(...) with data from API

# 4. Save locally
builder.save_plo_file("from_api.plo")
```

## License and Attribution

This PLO Assembler is provided for use with FullCAM, which is part of Australia's Department of Climate Change, Energy, the Environment and Water (DCCEEW).

FullCAM is licensed under Creative Commons Attribution 4.0 International License.

For official FullCAM documentation, visit: https://dcceew.gov.au

## Support

For issues with:
- **PLO Assembler module**: Refer to inline documentation and examples
- **FullCAM API**: See FullCAM_Databuilder_API_Documentation_v0_1_DRAFT.pdf
- **FullCAM itself**: Contact DCCEEW at fullcam@dcceew.gov.au