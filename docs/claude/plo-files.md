# PLO Files Guide

Complete guide to PLO (Plot) file structure, XML sections, attributes, and validation rules.

## Table of Contents

- [PLO File Overview](#plo-file-overview)
- [XML Structure](#xml-structure)
- [Section Descriptions](#section-descriptions)
- [Critical Attributes](#critical-attributes)
- [Time Series Format](#time-series-format)
- [Validation Rules](#validation-rules)

## PLO File Overview

PLO files are XML documents representing carbon accounting plots for the FullCAM model.

**File Extension:** `.plo`

**Encoding:** UTF-8

**XML Version:** 1.0

**Document Root:** `<DocumentPlot version="5009">`

**Typical Size:** 50-200 KB per file

**Purpose:** Define plot location, climate, soil, species, and simulation parameters for carbon accounting

## XML Structure

### Complete Structure

```xml
<?xml version="1.0" encoding="UTF-8"?>
<DocumentPlot version="5009">
  <Meta nmME="Plot_Name" notesME="Description"/>
  <Config tPlot="CompF" userN="false" useFSI="true" .../>
  <Timing stYrYTZ="2000" enYrYTZ="2100" stepsPerYrYTZ="1" .../>
  <Build lonBL="148.16" latBL="-35.61" frCat="Plantation" areaBL="OneKm" .../>
  <Site>
    <TimeSeries tInTS="avgAirTemp" yr0TS="1900" nYrsTS="201" dataPerYrTS="12">
      <rawTS count="2412">12.5,13.2,14.8,...</rawTS>
    </TimeSeries>
    <!-- More time series -->
  </Site>
  <Soil initOMF="0.05" .../>
  <Init tsmdInitIN="50.5" .../>
  <SpeciesForestSet>
    <SpeciesForest specId="8" speciesNm="Eucalyptus globulus" .../>
  </SpeciesForestSet>
  <RegimeSet>
    <Regime>
      <Event eventType="Plant" eventYr="2010" .../>
    </Regime>
  </RegimeSet>
  <OutWinSet>...</OutWinSet>
  <LogEntrySet>...</LogEntrySet>
  <Mnrl_Mulch>...</Mnrl_Mulch>
  <other_info>...</other_info>
</DocumentPlot>
```

### Section Hierarchy

1. **Meta** - Plot metadata (name, notes)
2. **Config** - Simulation configuration flags
3. **Timing** - Time parameters (start/end years, timesteps)
4. **Build** - Geographic location and spatial parameters
5. **Site** - Site-level parameters and time series (climate/productivity)
6. **Soil** - Soil carbon pools and cover
7. **Init** - Initial conditions for carbon pools
8. **SpeciesForestSet** (optional) - Species definitions with calibrations
9. **RegimeSet** (optional) - Management events timeline
10. **OutWinSet** - GUI output window settings
11. **LogEntrySet** - Audit log entries
12. **Mnrl_Mulch** - Nitrogen cycling and mulch layer parameters
13. **other_info** - Economic, sensitivity, and optimization settings

## Section Descriptions

### Meta Section

**Purpose:** Plot identification and documentation

**XML:**
```xml
<Meta nmME="Plot_Name" notesME="Plot description and notes"/>
```

**Attributes:**
- `nmME` (string): Plot name (displayed in FullCAM GUI)
- `notesME` (string): Plot notes (optional documentation)

**Validation:**
- `nmME` should be unique within project
- Avoid special characters in `nmME` (use `_` instead of spaces)

### Config Section

**Purpose:** Simulation configuration flags and model options

**XML:**
```xml
<Config
  tPlot="CompF"
  userN="false"
  useFSI="true"
  userFI="false"
  userDeb="false"
  userHum="false"
  userBiomC="false"
  userMulch="false"
  ...
/>
```

**Key Attributes:**

| Attribute | Type | Values | Description |
|-----------|------|--------|-------------|
| `tPlot` | string | `CompF`, `SoilF`, `CompA`, `SoilA`, `CompM` | Plot type (see [Plot Types](#plot-types)) |
| `userN` | bool | `"true"`, `"false"` | Enable nitrogen cycling |
| `useFSI` | bool | `"true"`, `"false"` | Use Forest Succession Index |
| `userFI` | bool | `"true"`, `"false"` | Use Fire Index |
| `userDeb` | bool | `"true"`, `"false"` | User-specified debris pools |
| `userHum` | bool | `"true"`, `"false"` | User-specified humus pools |
| `userBiomC` | bool | `"true"`, `"false"` | User-specified biomass carbon |
| `userMulch` | bool | `"true"`, `"false"` | Enable mulch layer modeling |

**Important:** Boolean values MUST be strings `"true"` or `"false"`, not Python booleans.

#### Plot Types

| Type | Description | Use Case |
|------|-------------|----------|
| `CompF` | Forest Composite | Above & below ground biomass + soil carbon |
| `SoilF` | Forest Soil Only | Soil carbon only (no biomass) |
| `CompA` | Agricultural Composite | Agricultural systems with biomass |
| `SoilA` | Agricultural Soil Only | Agricultural soil carbon only |
| `CompM` | Mixed | Combined forest/agricultural systems |

**Recommendation:** Use `CompF` for forest carbon accounting (most common)

### Timing Section

**Purpose:** Define simulation time parameters and output frequency

**XML:**
```xml
<Timing
  stYrYTZ="2000"
  enYrYTZ="2100"
  stepsPerYrYTZ="1"
  stepsPerOutYTZ="1"
  stYrOutYTZ="2000"
  enYrOutYTZ="2100"
/>
```

**Attributes:**

| Attribute | Type | Description | Common Values |
|-----------|------|-------------|---------------|
| `stYrYTZ` | string | Simulation start year | `"2000"`, `"2010"` |
| `enYrYTZ` | string | Simulation end year | `"2100"`, `"2050"` |
| `stepsPerYrYTZ` | string | Simulation steps per year | `"1"` (annual), `"12"` (monthly), `"110"` (fine) |
| `stepsPerOutYTZ` | string | Output frequency | `"1"` (every step), `"12"` (annual) |
| `stYrOutYTZ` | string | Output start year | Same as `stYrYTZ` |
| `enYrOutYTZ` | string | Output end year | Same as `enYrYTZ` |

#### Simulation Resolution

**Understanding `stepsPerYrYTZ` vs `stepsPerOutYTZ`:**

These are **independent parameters** with different purposes:

1. **`stepsPerYrYTZ`** - **INTERNAL SIMULATION RESOLUTION**
   - Controls how many times per year carbon moves between pools
   - Higher values approach "limiting values" where further increases produce identical results
   - For typical forest carbon accounting, `stepsPerYrYTZ="1"` vs `stepsPerYrYTZ="110"` often produce the same annual stocks

2. **`stepsPerOutYTZ`** - **OUTPUT FREQUENCY**
   - Controls how often results are written to CSV
   - Affects output file size, not simulation accuracy
   - Independent from simulation resolution

**Examples:**

| `stepsPerYrYTZ` | `stepsPerOutYTZ` | Result |
|-----------------|------------------|--------|
| `"12"` | `"1"` | Simulate monthly, output monthly (12 rows/year) |
| `"12"` | `"12"` | Simulate monthly, output annually (1 row/year) |
| `"110"` | `"110"` | Simulate 110 steps/year, output annually (1 row/year) |
| `"1"` | `"1"` | Simulate annually, output annually (1 row/year) |

**Key Insight:** Increasing `stepsPerYrYTZ` without adjusting `stepsPerOutYTZ` may not change outputs because you're only outputting at the same frequency. To see finer-resolution outputs, adjust both parameters.

**Recommendation:**
- For annual outputs: `stepsPerYrYTZ="1"`, `stepsPerOutYTZ="1"`
- For monthly outputs: `stepsPerYrYTZ="12"`, `stepsPerOutYTZ="1"`
- For fine-resolution modeling: `stepsPerYrYTZ="110"`, `stepsPerOutYTZ="110"` (annual outputs)

### Build Section

**Purpose:** Geographic location and spatial averaging parameters

**XML:**
```xml
<Build
  lonBL="148.16"
  latBL="-35.61"
  frCat="Plantation"
  areaBL="OneKm"
  applyDownloadedData="true"
  ...
/>
```

**Critical Attributes:**

| Attribute | Type | Description | Valid Values |
|-----------|------|-------------|--------------|
| `lonBL` | float | Longitude (decimal degrees) | -180 to 180 |
| `latBL` | float | Latitude (decimal degrees) | -90 to 90 |
| `frCat` | string | Forest category | See [Forest Categories](#forest-categories) |
| `areaBL` | string | Spatial averaging area | See [Spatial Averaging](#spatial-averaging) |

#### Forest Categories

**CRITICAL:** Forest category affects which calibrations are used. Using wrong category can cause **20-50% errors** in carbon predictions.

| Category | Description | Use Case |
|----------|-------------|----------|
| `Plantation` | Commercial plantation species | Eucalyptus plantations, intensive forestry |
| `MVG` | Major Vegetation Groups | Native Australian forests |
| `EnvMallee` | Environmental plantings | Environmental restoration, mallee species |
| `ERF` | Emissions Reduction Fund | ERF methodology projects |
| `ERFH` | ERF with EMP calibrations | ERF Human-Induced Regeneration |
| `null` | All categories | Generic (not recommended) |

**Why Category Matters:**

Calibrations are statistically fitted parameters that control tree growth and biomass allocation. Different categories use fundamentally different calibrations:

- **Plantation calibrations**: Fitted to commercial forestry data
  - Intensive management
  - Fast growth rates
  - High stem allocation
  - Optimized spacing
  - 100% light capture

- **MVG (native) calibrations**: Fitted to natural forest data
  - Natural competition
  - Slower growth rates
  - Lower stem allocation
  - Endemic canopy cover
  - Natural mortality

**Example Error:**
Using MVG calibrations for commercial *Eucalyptus globulus* plantation will **systematically underestimate biomass by ~30%** over a 20-year rotation.

**Rule:** For commercial *Eucalyptus globulus* plantations → **Always use `frCat="Plantation"`**

#### Spatial Averaging

| Value | Description | Area | Use Case |
|-------|-------------|------|----------|
| `Cell` | Single grid cell | ~100m × 100m | Fine-scale modeling |
| `Hectare` | 1 hectare | 100m × 100m | Field plots |
| `OneKm` | 1 km² | 1000m × 1000m | **Default (recommended)** |
| `TwoKm` | 4 km² | 2000m × 2000m | Regional averaging |
| `ThreeKm` | 9 km² | 3000m × 3000m | Regional averaging |
| `FiveKm` | 25 km² | 5000m × 5000m | Broad-scale modeling |

**Recommendation:** Use `"OneKm"` for most applications (good balance of spatial detail and computational efficiency)

### Site Section

**Purpose:** Site-level parameters and climate/productivity time series

**XML:**
```xml
<Site>
  <TimeSeries tInTS="avgAirTemp" yr0TS="1900" nYrsTS="201" dataPerYrTS="12">
    <rawTS count="2412">12.5,13.2,14.8,15.6,...</rawTS>
  </TimeSeries>
  <TimeSeries tInTS="rainfall" yr0TS="1900" nYrsTS="201" dataPerYrTS="12">
    <rawTS count="2412">45.2,38.7,52.3,...</rawTS>
  </TimeSeries>
  <TimeSeries tInTS="openPanEvap" yr0TS="1900" nYrsTS="201" dataPerYrTS="12">
    <rawTS count="2412">120.5,110.3,...</rawTS>
  </TimeSeries>
  <TimeSeries tInTS="forestProdIx" yr0TS="1900" nYrsTS="201" dataPerYrTS="1">
    <rawTS count="201">0.85,0.87,0.89,...</rawTS>
  </TimeSeries>
</Site>
```

**See:** [Time Series Format](#time-series-format) section below

### Soil Section

**Purpose:** Soil carbon pools and cover parameters

**XML:**
```xml
<Soil
  initOMF="0.05"
  claySL="0.25"
  siltSL="0.35"
  sandSL="0.40"
  bulkDensSL="1.2"
  pHSL="6.5"
  ...
/>
```

**Key Attributes:**
- `initOMF` (float): Initial organic matter fraction [0-1]
- `claySL` (float): Clay content [0-1]
- `siltSL` (float): Silt content [0-1]
- `sandSL` (float): Sand content [0-1]
- `bulkDensSL` (float): Bulk density [g/cm³]
- `pHSL` (float): Soil pH

**Validation:** `claySL + siltSL + sandSL = 1.0`

### Init Section

**Purpose:** Initial carbon pool values at simulation start

**XML:**
```xml
<Init
  tsmdInitIN="50.5"
  biomCIN="10.2"
  debCIN="5.8"
  humCIN="45.3"
  ...
/>
```

**Key Attributes:**
- `tsmdInitIN` (float): Initial Top Soil Moisture Deficit [mm]
- `biomCIN` (float): Initial biomass carbon [tC/ha]
- `debCIN` (float): Initial debris carbon [tC/ha]
- `humCIN` (float): Initial humus carbon [tC/ha]

**Note:** `tsmdInitIN` is calculated by `create_init_section()` from climate time series for the specified start year.

### SpeciesForestSet Section

**Purpose:** Define species with growth calibrations and parameters

**XML:**
```xml
<SpeciesForestSet>
  <SpeciesForest
    specId="8"
    speciesNm="Eucalyptus globulus"
    a1spc="0.45"
    a2spc="0.023"
    kxspc="0.88"
    foliageTOR="0.5"
    fineRootTOR="0.8"
    ...
  />
</SpeciesForestSet>
```

**Key Calibration Parameters:**
- `a1spc`, `a2spc`, `kxspc`: Growth curve calibrations
- `foliageTOR`: Foliage turnover rate [fraction/year]
- `fineRootTOR`: Fine root turnover rate [fraction/year]
- `stemAlloc`, `branchAlloc`, `foliageAlloc`: Biomass allocation fractions

**Important:** These calibrations are **forest category specific**. Using Plantation calibrations with MVG category (or vice versa) will produce incorrect results.

### RegimeSet Section

**Purpose:** Define management events timeline

**XML:**
```xml
<RegimeSet>
  <Regime>
    <Event eventType="Plant" eventYr="2010" specId="8" stemsDens="1000"/>
    <Event eventType="Thin" eventYr="2020" thinPct="30"/>
    <Event eventType="Harvest" eventYr="2030" harvPct="100"/>
  </Regime>
</RegimeSet>
```

**Event Types:**
- `Plant`: Establish plantation
- `Thin`: Thinning operation
- `Harvest`: Harvest/clear cut
- `Fire`: Fire event
- `Fertilize`: Fertilization
- `Irrigate`: Irrigation

**Common Attributes:**
- `eventYr` (int): Year of event
- `eventType` (string): Event type
- `specId` (int): Species ID (for planting)
- `stemsDens` (float): Stems per hectare (for planting)
- `thinPct` (float): Thinning percentage (for thinning)
- `harvPct` (float): Harvest percentage (for harvest)

## Time Series Format

### Structure

```xml
<TimeSeries tInTS="avgAirTemp" yr0TS="1900" nYrsTS="201" dataPerYrTS="12">
  <rawTS count="2412">12.5,13.2,14.8,15.6,16.8,...</rawTS>
</TimeSeries>
```

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `tInTS` | string | Time series type (see [Time Series Types](#time-series-types)) |
| `yr0TS` | string | Start year |
| `nYrsTS` | string | Number of years |
| `dataPerYrTS` | string | Data points per year (`"12"` for monthly, `"1"` for annual) |

### rawTS Element

**Format:** Comma-separated values in `<rawTS>` element

**Attributes:**
- `count` (int): Total number of values

**Validation Rules:**
1. `count` must equal number of comma-separated values
2. Total values must equal `nYrsTS × dataPerYrTS`
3. Missing data: empty string between commas (e.g., `"1.5,,2.3"`)
4. No spaces after commas
5. Values must be numeric (floats or integers)

**Example (monthly data):**
```xml
<!-- 2 years of monthly data: 2 × 12 = 24 values -->
<TimeSeries tInTS="avgAirTemp" yr0TS="2020" nYrsTS="2" dataPerYrTS="12">
  <rawTS count="24">12.5,13.2,14.8,15.6,16.8,17.2,18.5,17.9,16.2,14.5,13.1,12.3,
                     12.7,13.5,15.1,15.9,17.1,17.5,18.8,18.2,16.5,14.8,13.4,12.6</rawTS>
</TimeSeries>
```

**Example (annual data):**
```xml
<!-- 5 years of annual data: 5 × 1 = 5 values -->
<TimeSeries tInTS="forestProdIx" yr0TS="2020" nYrsTS="5" dataPerYrTS="1">
  <rawTS count="5">0.85,0.87,0.89,0.91,0.93</rawTS>
</TimeSeries>
```

### Time Series Types

| Type | Description | Unit | Frequency | Required |
|------|-------------|------|-----------|----------|
| `avgAirTemp` | Average air temperature | °C | Monthly | ✅ Yes |
| `rainfall` | Precipitation | mm | Monthly | ✅ Yes |
| `openPanEvap` | Pan evaporation | mm | Monthly | ✅ Yes |
| `forestProdIx` | Forest Productivity Index | unitless | Annual | ✅ Yes |
| `VPD` | Vapor Pressure Deficit | kPa | Monthly | ❌ Optional |
| `soilTemp` | Soil temperature | °C | Monthly | ❌ Optional |
| `solarRad` | Solar radiation | MJ/m² | Monthly | ❌ Optional |
| `fertility` | Soil fertility modifier | unitless | Monthly | ❌ Optional |
| `conditIrrigF` | Conditional irrigation (forest) | mm | Monthly | ❌ Optional |
| `defnitIrrigA` | Definite irrigation (agriculture) | mm | Monthly | ❌ Optional |

**Required Time Series:** All PLO files must include `avgAirTemp`, `rainfall`, `openPanEvap`, and `forestProdIx`.

## Critical Attributes

### Boolean Attributes

**IMPORTANT:** All boolean attributes in PLO files MUST be strings `"true"` or `"false"`.

**Correct:**
```xml
<Config userN="true" useFSI="false"/>
```

**Incorrect:**
```xml
<Config userN=true useFSI=false/>  <!-- Python booleans won't work -->
```

**In Python:**
```python
def _bool_to_xml(value):
    """Convert Python bool to XML string"""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)

# Usage
userN = True
xml = f'<Config userN="{_bool_to_xml(userN)}"/>'
```

### Empty Attributes

**Use empty strings for optional attributes:**

**Correct:**
```xml
<Meta nmME="Plot_Name" notesME=""/>
```

**Incorrect:**
```xml
<Meta nmME="Plot_Name" notesME=None/>  <!-- Will cause XML parse error -->
```

### Numeric Precision

**Coordinates:** Use at least 2 decimal places
```xml
<Build lonBL="148.16" latBL="-35.61"/>
```

**Carbon Pools:** Use at least 1 decimal place
```xml
<Init biomCIN="10.2" debCIN="5.8"/>
```

**Fractions:** Use 2-4 decimal places
```xml
<Soil claySL="0.25" initOMF="0.05"/>
```

## Validation Rules

### XML Well-Formedness

1. **Valid XML syntax**
   - All tags properly closed
   - Attribute values in quotes
   - Special characters escaped (`&lt;`, `&gt;`, `&amp;`, `&quot;`, `&apos;`)

2. **Encoding declaration**
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   ```

3. **Single root element**
   ```xml
   <DocumentPlot version="5009">...</DocumentPlot>
   ```

### Required Sections

All PLO files must include:
- `<Meta>`
- `<Config>`
- `<Timing>`
- `<Build>`
- `<Site>` (with required time series)

Optional sections:
- `<SpeciesForestSet>` (required for forest plots with species)
- `<RegimeSet>` (required for plots with events)
- `<Soil>`, `<Init>`, `<OutWinSet>`, `<LogEntrySet>`, `<Mnrl_Mulch>`, `<other_info>`

### Data Consistency

1. **Time series validation**
   - `count` attribute matches number of values
   - Total values = `nYrsTS × dataPerYrTS`
   - Start year (`yr0TS`) ≤ simulation start year (`stYrYTZ`)
   - End year (`yr0TS + nYrsTS`) ≥ simulation end year (`enYrYTZ`)

2. **Coordinate ranges**
   - Latitude: -90 to 90
   - Longitude: -180 to 180

3. **Year ranges**
   - Start year < end year
   - Years within reasonable range (e.g., 1900-2200)

4. **Soil texture**
   - `claySL + siltSL + sandSL = 1.0` (within tolerance)

5. **Forest category consistency**
   - `frCat` in Build must match species calibrations
   - Don't mix Plantation species with MVG category

### Common Validation Errors

**Error:** `Time series count mismatch`
```xml
<!-- WRONG: count=24 but only 12 values -->
<TimeSeries tInTS="avgAirTemp" yr0TS="2020" nYrsTS="2" dataPerYrTS="12">
  <rawTS count="24">12.5,13.2,14.8,15.6,16.8,17.2,18.5,17.9,16.2,14.5,13.1,12.3</rawTS>
</TimeSeries>

<!-- CORRECT: count=24 with 24 values -->
<TimeSeries tInTS="avgAirTemp" yr0TS="2020" nYrsTS="2" dataPerYrTS="12">
  <rawTS count="24">12.5,13.2,14.8,15.6,16.8,17.2,18.5,17.9,16.2,14.5,13.1,12.3,
                     12.7,13.5,15.1,15.9,17.1,17.5,18.8,18.2,16.5,14.8,13.4,12.6</rawTS>
</TimeSeries>
```

**Error:** `Invalid boolean attribute`
```xml
<!-- WRONG: Python boolean -->
<Config userN=True/>

<!-- CORRECT: String boolean -->
<Config userN="true"/>
```

**Error:** `Missing required time series`
```xml
<!-- WRONG: Missing forestProdIx -->
<Site>
  <TimeSeries tInTS="avgAirTemp">...</TimeSeries>
  <TimeSeries tInTS="rainfall">...</TimeSeries>
  <TimeSeries tInTS="openPanEvap">...</TimeSeries>
</Site>

<!-- CORRECT: All required time series -->
<Site>
  <TimeSeries tInTS="avgAirTemp">...</TimeSeries>
  <TimeSeries tInTS="rainfall">...</TimeSeries>
  <TimeSeries tInTS="openPanEvap">...</TimeSeries>
  <TimeSeries tInTS="forestProdIx">...</TimeSeries>
</Site>
```

### Testing PLO Files

**Validate before simulation:**

1. **Parse XML**
   ```python
   from lxml import etree

   try:
       root = etree.parse('plot.plo')
       print("✓ Valid XML syntax")
   except etree.XMLSyntaxError as e:
       print(f"✗ XML parse error: {e}")
   ```

2. **Check required sections**
   ```python
   required = ['Meta', 'Config', 'Timing', 'Build', 'Site']
   for section in required:
       if root.find(f'.//{section}') is None:
           print(f"✗ Missing required section: {section}")
   ```

3. **Validate time series**
   ```python
   for ts in root.findall('.//TimeSeries'):
       nYrs = int(ts.get('nYrsTS'))
       dataPerYr = int(ts.get('dataPerYrTS'))
       expected_count = nYrs * dataPerYr

       raw_ts = ts.find('rawTS')
       count = int(raw_ts.get('count'))
       actual_values = len([v for v in raw_ts.text.split(',') if v.strip()])

       if count != expected_count or actual_values != expected_count:
           print(f"✗ Time series count mismatch: {ts.get('tInTS')}")
   ```

4. **Submit to simulator**
   - The FullCAM simulator performs comprehensive validation
   - Parse error messages to fix issues

## Version Compatibility

### FullCAM Versions

| Version | PLO `version` Attribute | Notes |
|---------|------------------------|-------|
| FullCAM 2020 | `"5007"` | Legacy format |
| FullCAM 2024 | `"5009"` | Current default |

**Setting version:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<DocumentPlot version="5009">
  ...
</DocumentPlot>
```

**Migration:**
- Most PLO files with `version="5007"` work with FullCAM 2024
- Some parameter names changed between versions
- Consult [FullCAM Documentation](../FullCAM_Documentation_Complete.html) for version-specific differences

## Related Documentation

- **[Architecture Guide](architecture.md)** - System design and data flow
- **[API Reference](api-reference.md)** - Functions and API endpoints
- **[Development Guide](development.md)** - Common workflows and patterns
- **[FullCAM Documentation Complete](../FullCAM_Documentation_Complete.html)** - Official parameter specifications
