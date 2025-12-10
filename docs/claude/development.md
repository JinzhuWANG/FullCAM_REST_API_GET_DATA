# Development Guide

Common workflows, code patterns, and examples for working with the FullCAM REST API toolkit.

## Table of Contents

- [Quick Start Workflows](#quick-start-workflows)
- [Common Patterns](#common-patterns)
- [Data Processing Workflows](#data-processing-workflows)
- [Batch Operations](#batch-operations)
- [Troubleshooting](#troubleshooting)

## Quick Start Workflows

### Workflow 1: Generate Single PLO File

**Use case:** Generate PLO for one location using cached data

```python
from tools import assemble_plo_sections

# Specify location and start year
lon, lat = 148.16, -35.61  # Canberra region
year_start = 2010

# Generate complete PLO file
# (automatically loads from downloaded/siteInfo_*.xml or downloads if missing)
plo_xml = assemble_plo_sections(lon, lat, year_start=year_start)

# Save to file
with open("canberra_plot.plo", "w", encoding="utf-8") as f:
    f.write(plo_xml)

print("PLO file generated successfully!")
```

**Note:** Data will be auto-downloaded if not cached. Species template is loaded from `data/dataholder_species_*.xml`.

### Workflow 2: Generate PLO and Run Simulation

**Use case:** Complete workflow from coordinates to simulation results

```python
import requests
import pandas as pd
from io import StringIO
import os
from tools import assemble_plo_sections, get_plot_simulation

# Configuration
API_KEY = os.getenv("FULLCAM_API_KEY")
SIMULATOR_URL = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1"

# Step 1: Generate PLO file
lon, lat = 148.16, -35.61
year_start = 2010
plo_xml = assemble_plo_sections(lon, lat, year_start)

# Step 2: Submit to FullCAM Simulator
response = requests.post(
    f"{SIMULATOR_URL}/2024/fullcam-simulator/run-plotsimulation",
    files={'file': ('plot.plo', plo_xml)},
    headers={"Ocp-Apim-Subscription-Key": API_KEY},
    timeout=30
)

# Step 3: Parse CSV results
if response.status_code == 200:
    results_df = pd.read_csv(StringIO(response.text))

    # Save results
    results_df.to_csv(f'results_{lon}_{lat}.csv', index=False)

    # Display summary
    print(f"✓ Simulation complete")
    print(f"Years simulated: {results_df['Year'].min()} - {results_df['Year'].max()}")
    print(f"Final total carbon: {results_df.iloc[-1]['TotalC_tCha']:.2f} tC/ha")
    print(results_df[['Year', 'TotalC_tCha', 'AboveGround_tCha']].head(10))
else:
    print(f"✗ Simulation failed: {response.status_code}")
    print(response.text)
```

**See:** [RUN_FullCAM2024.py](../../RUN_FullCAM2024.py) for complete working example

### Workflow 3: Batch Process Multiple Locations

**Use case:** Generate PLO files for multiple locations

```python
import pandas as pd
from tools import assemble_plo_sections

# Load locations from CSV
locations = pd.DataFrame({
    'name': ['Plot_A', 'Plot_B', 'Plot_C'],
    'lat': [-35.61, -36.12, -34.89],
    'lon': [148.16, 149.23, 147.45],
    'year_start': [2010, 2010, 2010]
})

# Generate PLO files
success_count = 0
for idx, row in locations.iterrows():
    try:
        # Generate PLO from cached data
        plo_xml = assemble_plo_sections(
            lon=row['lon'],
            lat=row['lat'],
            year_start=row['year_start']
        )

        # Save to file
        filename = f"{row['name']}.plo"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(plo_xml)

        print(f"✓ Created {filename}")
        success_count += 1

    except FileNotFoundError as e:
        print(f"✗ Skipping {row['name']}: {e}")

print(f"\n✓ Generated {success_count}/{len(locations)} PLO files")
```

### Workflow 4: Download Data for New Location

**Use case:** Download API data for a location not in cache

```python
import requests
import os

API_KEY = os.getenv("FULLCAM_API_KEY")
BASE_URL = "https://api.dcceew.gov.au/climate/carbon-accounting/2024/data/v1"

lon, lat = 150.5, -33.8  # New location

# Download siteInfo
params = {
    "latitude": lat,
    "longitude": lon,
    "area": "OneKm",
    "plotT": "CompF",
    "frCat": "Plantation",
    "incGrowth": "false",
    "version": 2024
}

response = requests.get(
    f"{BASE_URL}/2024/data-builder/siteinfo",
    params=params,
    headers={"Ocp-Apim-Subscription-Key": API_KEY},
    timeout=30
)

if response.status_code == 200:
    # Save to cache
    with open(f'downloaded/siteInfo_{lon}_{lat}.xml', 'wb') as f:
        f.write(response.content)
    print(f"✓ Downloaded siteInfo for ({lon}, {lat})")
else:
    print(f"✗ Failed to download: {response.status_code}")

# Download species data (Eucalyptus globulus, specId=8)
params = {
    "latitude": lat,
    "longitude": lon,
    "area": "OneKm",
    "specId": 8,
    "frCat": "Plantation",
    "version": 2024
}

response = requests.get(
    f"{BASE_URL}/2024/data-builder/species",
    params=params,
    headers={"Ocp-Apim-Subscription-Key": API_KEY},
    timeout=30
)

if response.status_code == 200:
    with open(f'downloaded/species_{lon}_{lat}.xml', 'wb') as f:
        f.write(response.content)
    print(f"✓ Downloaded species data for ({lon}, {lat})")

# Update cache index
with open('downloaded/successful_downloads.txt', 'a', encoding='utf-8') as f:
    f.write(f"siteInfo_{lon}_{lat}.xml\n")
    f.write(f"species_{lon}_{lat}.xml\n")
```

## Common Patterns

### Pattern: Customize PLO Sections

**Use case:** Override specific sections with custom parameters

```python
from tools.plo_section_functions import (
    create_meta_section,
    create_config_section,
    create_timing_section,
    create_build_section,
    create_site_section,
    create_species_section,
    create_soil_section,
    create_init_section,
    create_event_section,
    create_outwinset_section,
    create_logentryset_section,
    create_mnrl_mulch_section,
    create_other_info_section
)

lon, lat = 148.16, -35.61
year_start = 2010

# Customize sections
meta = create_meta_section("Custom_Plot", notesME="Research trial plot")
config = create_config_section(tPlot="CompF", userN=True)  # Enable nitrogen cycling
timing = create_timing_section(stYrYTZ=str(year_start), enYrYTZ="2050",
                                stepsPerYrYTZ="12", stepsPerOutYTZ="12")  # Monthly sim, annual outputs
build = create_build_section(lon, lat, frCat="Plantation", areaBL="OneKm")

# Load data-driven sections from cache
site = create_site_section(lon, lat)
species = create_species_section(lon, lat)
soil = create_soil_section(lon, lat, yr0TS=year_start)
init = create_init_section(lon, lat, tsmd_year=year_start)

# Load template sections
events = create_event_section()
outwinset = create_outwinset_section()
logentryset = create_logentryset_section()
mnrl_mulch = create_mnrl_mulch_section()
other_info = create_other_info_section()

# Assemble complete PLO
plo_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<DocumentPlot version="5009">
{meta}
{config}
{timing}
{build}
{site}
{species}
{soil}
{init}
{events}
{outwinset}
{logentryset}
{mnrl_mulch}
{other_info}
</DocumentPlot>'''

# Save
with open("custom_plot.plo", "w", encoding="utf-8") as f:
    f.write(plo_xml)
```

### Pattern: Extract Data from XML Cache

**Use case:** Load and analyze cached API data

```python
from tools.XML2Data import get_siteinfo_data, get_soilbase_data, get_carbon_data
import matplotlib.pyplot as plt

lon, lat = 148.16, -35.61

# Load climate data
climate_ds = get_siteinfo_data(lat, lon, year=2020)

# Plot temperature over months
temp_2020 = climate_ds.avgAirTemp.sel(year=2020)
plt.plot(range(1, 13), temp_2020.values, marker='o')
plt.xlabel('Month')
plt.ylabel('Temperature (°C)')
plt.title(f'Temperature 2020 - Lat: {lat}, Lon: {lon}')
plt.savefig('temperature_2020.png')

# Load soil data
soil = get_soilbase_data(lat, lon)
print(f"Soil texture:")
print(f"  Clay: {soil['clay_content']:.1%}")
print(f"  Silt: {soil['silt_content']:.1%}")
print(f"  Sand: {soil['sand_content']:.1%}")

# Load simulation results (if exists)
try:
    results = get_carbon_data(lat, lon)
    print(f"\nSimulation results available: {len(results)} years")
    print(results[['Year', 'TotalC_tCha']].head())
except FileNotFoundError:
    print("\nNo simulation results found")
```

### Pattern: Parallel API Downloads

**Use case:** Download data for multiple locations in parallel

```python
import requests
import os
from joblib import Parallel, delayed
from tqdm.auto import tqdm
import time

API_KEY = os.getenv("FULLCAM_API_KEY")
BASE_URL = "https://api.dcceew.gov.au/climate/carbon-accounting/2024/data/v1"

def download_siteinfo(lon, lat, try_number=8):
    """Download siteInfo with retry logic"""
    params = {
        "latitude": lat,
        "longitude": lon,
        "area": "OneKm",
        "plotT": "CompF",
        "frCat": "Plantation",
        "incGrowth": "false",
        "version": 2024
    }

    for attempt in range(try_number):
        try:
            response = requests.get(
                f"{BASE_URL}/2024/data-builder/siteinfo",
                params=params,
                headers={"Ocp-Apim-Subscription-Key": API_KEY},
                timeout=100
            )

            if response.status_code == 200:
                # Save to cache
                with open(f'downloaded/siteInfo_{lon}_{lat}.xml', 'wb') as f:
                    f.write(response.content)

                # Log success
                with open('downloaded/successful_downloads.txt', 'a', encoding='utf-8') as f:
                    f.write(f"siteInfo_{lon}_{lat}.xml\n")

                return "Success"
            else:
                if attempt < try_number - 1:
                    time.sleep(2**attempt)  # Exponential backoff
        except requests.RequestException:
            if attempt < try_number - 1:
                time.sleep(2**attempt)

    return "Failed"

# Define locations
locations = [
    (148.16, -35.61),
    (149.23, -36.12),
    (147.45, -34.89),
    # ... more locations
]

# Download in parallel (35 threads)
tasks = [delayed(download_siteinfo)(lon, lat) for lon, lat in locations]

results = []
for result in tqdm(Parallel(n_jobs=35, backend='threading', return_as='generator')(tasks),
                   total=len(tasks)):
    results.append(result)

success_count = sum(1 for r in results if r == "Success")
print(f"✓ Downloaded {success_count}/{len(locations)} locations")
```

**See:** [RUN_FullCAM2024.py](../../RUN_FullCAM2024.py) for production-ready implementation

### Pattern: Convert XML to NetCDF/GeoTIFF

**Use case:** Create spatial rasters from XML cache data

```python
import numpy as np
import xarray as xr
import rioxarray as rio
from affine import Affine
from tools.XML2Data import get_siteinfo_data, export_to_geotiff_with_band_names
from tools.helpers.cache_manager import get_existing_downloads

# Load cache index
existing_siteinfo, _, _ = get_existing_downloads()

# Extract coordinates from filenames
import re
coord_pattern = re.compile(r'siteInfo_(-?\d+\.\d+)_(-?\d+\.\d+)\.xml')

coords = []
for filename in existing_siteinfo:
    match = coord_pattern.match(filename)
    if match:
        lon = float(match.group(1))
        lat = float(match.group(2))
        coords.append((lon, lat))

# Create spatial grid
lons = sorted(set(lon for lon, lat in coords))
lats = sorted(set(lat for lon, lat in coords), reverse=True)

# Extract avgAirTemp for year 2020
data_2020 = np.full((len(lats), len(lons), 12), np.nan)  # (lat, lon, month)

for i, lat in enumerate(lats):
    for j, lon in enumerate(lons):
        if (lon, lat) in coords:
            try:
                ds = get_siteinfo_data(lat, lon, year=2020)
                data_2020[i, j, :] = ds.avgAirTemp.sel(year=2020).values
            except:
                pass  # Keep NaN for failed loads

# Create DataArray
temp_arr = xr.DataArray(
    data_2020,
    dims=['lat', 'lon', 'month'],
    coords={
        'lat': lats,
        'lon': lons,
        'month': range(1, 13)
    },
    attrs={'units': '°C', 'long_name': 'Average Air Temperature 2020'}
)

# Save as NetCDF
temp_arr.to_netcdf('avgAirTemp_2020.nc')

# Save as GeoTIFF (annual average)
temp_annual = temp_arr.mean(dim='month')
transform = Affine(0.01, 0, min(lons), 0, -0.01, max(lats))  # 0.01° resolution
export_to_geotiff_with_band_names(temp_annual, 'avgAirTemp_2020_annual.tif', transform)

print("✓ Exported NetCDF and GeoTIFF")
```

**See:** [FullCAM2NC.py](../../FullCAM2NC.py) for production-ready implementation

## Data Processing Workflows

### Workflow: Process Simulation Results

**Use case:** Analyze carbon stock time series from simulation

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load simulation results
df = pd.read_csv('downloaded/df_-35.61_148.16.csv')

# Plot total carbon over time
plt.figure(figsize=(10, 6))
plt.plot(df['Year'], df['TotalC_tCha'], label='Total Carbon', linewidth=2)
plt.plot(df['Year'], df['AboveGround_tCha'], label='Aboveground', linestyle='--')
plt.plot(df['Year'], df['BelowGround_tCha'], label='Belowground', linestyle='--')
plt.plot(df['Year'], df['Soil_tCha'], label='Soil', linestyle=':')

plt.xlabel('Year')
plt.ylabel('Carbon Stock (tC/ha)')
plt.title('Carbon Stocks Over Time')
plt.legend()
plt.grid(True)
plt.savefig('carbon_stocks.png', dpi=300)

# Calculate carbon sequestration rate
df['Sequestration_tCha_yr'] = df['TotalC_tCha'].diff()

# Summary statistics
print(f"Initial carbon stock (year {df['Year'].min()}): {df.iloc[0]['TotalC_tCha']:.2f} tC/ha")
print(f"Final carbon stock (year {df['Year'].max()}): {df.iloc[-1]['TotalC_tCha']:.2f} tC/ha")
print(f"Total sequestration: {df.iloc[-1]['TotalC_tCha'] - df.iloc[0]['TotalC_tCha']:.2f} tC/ha")
print(f"Average sequestration rate: {df['Sequestration_tCha_yr'].mean():.2f} tC/ha/yr")
```

### Workflow: Compare Scenarios

**Use case:** Generate and compare multiple PLO scenarios

```python
from tools import assemble_plo_sections
import requests
import pandas as pd
from io import StringIO
import os

API_KEY = os.getenv("FULLCAM_API_KEY")
SIMULATOR_URL = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1"

lon, lat = 148.16, -35.61

# Scenario 1: Start year 2010
plo_2010 = assemble_plo_sections(lon, lat, year_start=2010)

# Scenario 2: Start year 2020
plo_2020 = assemble_plo_sections(lon, lat, year_start=2020)

# Run simulations
scenarios = {
    '2010': plo_2010,
    '2020': plo_2020
}

results = {}
for scenario_name, plo_xml in scenarios.items():
    response = requests.post(
        f"{SIMULATOR_URL}/2024/fullcam-simulator/run-plotsimulation",
        files={'file': ('plot.plo', plo_xml)},
        headers={"Ocp-Apim-Subscription-Key": API_KEY},
        timeout=30
    )

    if response.status_code == 200:
        df = pd.read_csv(StringIO(response.text))
        results[scenario_name] = df
        print(f"✓ Scenario '{scenario_name}' complete")

# Compare results
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
for scenario_name, df in results.items():
    plt.plot(df['Year'], df['TotalC_tCha'], label=f'Start year {scenario_name}', linewidth=2)

plt.xlabel('Year')
plt.ylabel('Total Carbon (tC/ha)')
plt.title('Scenario Comparison: Start Year Impact')
plt.legend()
plt.grid(True)
plt.savefig('scenario_comparison.png', dpi=300)
```

## Batch Operations

### Batch: Generate PLO Files from Grid

**Use case:** Generate PLO files for all locations in a gridded region

```python
import numpy as np
from tools import assemble_plo_sections

# Define grid
lat_min, lat_max = -37.0, -34.0
lon_min, lon_max = 147.0, 150.0
resolution = 0.1  # 0.1 degree spacing

lats = np.arange(lat_max, lat_min - resolution, -resolution)
lons = np.arange(lon_min, lon_max + resolution, resolution)

# Generate PLO for each grid cell
year_start = 2010
success_count = 0
skip_count = 0

for lat in lats:
    for lon in lons:
        # Round to 2 decimals (matches cache filename format)
        lat_r = round(lat, 2)
        lon_r = round(lon, 2)

        try:
            plo_xml = assemble_plo_sections(lon_r, lat_r, year_start)

            # Save with grid coordinates in filename
            filename = f"plo_{lon_r}_{lat_r}.plo"
            with open(f"plo_outputs/{filename}", "w", encoding="utf-8") as f:
                f.write(plo_xml)

            success_count += 1
        except FileNotFoundError:
            skip_count += 1
            # Cache data doesn't exist for this location
            pass

print(f"✓ Generated {success_count} PLO files")
print(f"✗ Skipped {skip_count} locations (no cache data)")
```

### Batch: Run Simulations for All PLO Files

**Use case:** Submit all PLO files in directory to simulator

```python
import os
import requests
import pandas as pd
from io import StringIO
from pathlib import Path
from tqdm.auto import tqdm

API_KEY = os.getenv("FULLCAM_API_KEY")
SIMULATOR_URL = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1"

# Find all PLO files
plo_dir = Path("plo_outputs")
plo_files = list(plo_dir.glob("*.plo"))

print(f"Found {len(plo_files)} PLO files")

# Run simulations
success_count = 0
for plo_path in tqdm(plo_files):
    with open(plo_path, 'r', encoding='utf-8') as f:
        plo_xml = f.read()

    # Submit to simulator
    response = requests.post(
        f"{SIMULATOR_URL}/2024/fullcam-simulator/run-plotsimulation",
        files={'file': (plo_path.name, plo_xml)},
        headers={"Ocp-Apim-Subscription-Key": API_KEY},
        timeout=30
    )

    if response.status_code == 200:
        # Save results with matching filename
        df = pd.read_csv(StringIO(response.text))
        csv_path = plo_path.with_suffix('.csv')
        df.to_csv(csv_path, index=False)
        success_count += 1
    else:
        print(f"✗ Failed: {plo_path.name} - {response.status_code}")

print(f"✓ Completed {success_count}/{len(plo_files)} simulations")
```

## Troubleshooting

### Issue: FileNotFoundError when generating PLO

**Error:**
```
FileNotFoundError: Site info not found: downloaded/siteInfo_148.16_-35.61.xml
Run get_data.py first to download cache data
```

**Solution:**
1. Check cache index:
   ```python
   from tools.helpers.cache_manager import get_existing_downloads
   siteinfo, species, _ = get_existing_downloads()
   print(f"siteInfo_148.16_-35.61.xml in cache: {'siteInfo_148.16_-35.61.xml' in siteinfo}")
   ```

2. Data will be auto-downloaded when you call `assemble_plo_sections()`, or you can download manually:
   ```python
   from tools import get_siteinfo
   get_siteinfo(lat=-35.61, lon=148.16)
   ```

### Issue: Time series count mismatch in PLO

**Error from FullCAM simulator:**
```
Error: Time series count mismatch in avgAirTemp
Expected 2412 values, found 2400
```

**Solution:**
Check `rawTS` count attribute matches actual values:

```python
from lxml import etree

# Parse PLO file
root = etree.parse('plot.plo')

# Check all time series
for ts in root.findall('.//TimeSeries'):
    nYrs = int(ts.get('nYrsTS'))
    dataPerYr = int(ts.get('dataPerYrTS'))
    expected = nYrs * dataPerYr

    raw_ts = ts.find('rawTS')
    count_attr = int(raw_ts.get('count'))
    actual_values = len([v for v in raw_ts.text.split(',') if v.strip()])

    if count_attr != expected or actual_values != expected:
        print(f"✗ Mismatch in {ts.get('tInTS')}:")
        print(f"  Expected: {expected}")
        print(f"  count attribute: {count_attr}")
        print(f"  Actual values: {actual_values}")
```

### Issue: API authentication failed

**Error:**
```
401 Unauthorized: Invalid API key
```

**Solution:**
1. Check environment variable is set:
   ```bash
   # Windows Command Prompt
   echo %FULLCAM_API_KEY%

   # PowerShell
   $env:FULLCAM_API_KEY

   # Linux/Mac
   echo $FULLCAM_API_KEY
   ```

2. Set environment variable:
   ```bash
   # Windows (User variable - permanent)
   setx FULLCAM_API_KEY "your_key_here"

   # Linux/Mac (add to .bashrc or .zshrc for persistence)
   export FULLCAM_API_KEY="your_key_here"
   ```

3. Restart terminal/IDE after setting variable

### Issue: Slow cache operations

**Problem:** `get_data.py` takes minutes to start

**Solution:** Rebuild cache index:

```python
from tools.helpers.cache_manager import rebuild_cache
rebuild_cache()
```

**Explanation:** Cache file may be corrupted or out of sync. Rebuilding scans `downloaded/` directory and recreates `successful_downloads.txt`.

### Issue: Wrong forest category produces incorrect results

**Problem:** Carbon predictions seem too low/high

**Check forest category consistency:**

```python
from lxml import etree

# Parse PLO file
root = etree.parse('plot.plo')

# Check Build section forest category
build = root.find('.//Build')
fr_cat = build.get('frCat')
print(f"Forest category: {fr_cat}")

# Check species calibrations match category
species = root.find('.//SpeciesForest')
if species is not None:
    species_name = species.get('speciesNm')
    print(f"Species: {species_name}")

    # For Eucalyptus plantations, should use frCat="Plantation"
    if "Eucalyptus" in species_name and fr_cat != "Plantation":
        print("⚠ WARNING: Using Eucalyptus with non-Plantation category")
        print("  This may cause 20-50% errors in carbon predictions")
        print("  Recommendation: Use frCat='Plantation' for commercial eucalyptus")
```

**Solution:** Regenerate PLO with correct forest category:

```python
from tools import assemble_plo_sections

# Correct: Use appropriate species template
plo_xml = assemble_plo_sections(lon, lat, species='Eucalyptus_globulus', year_start=year_start)
# Available species: Eucalyptus_globulus, Mallee_eucalypt, Environmental_plantings
```

### Issue: Missing required time series

**Error from simulator:**
```
Error: Required time series missing: forestProdIx
```

**Solution:**
Check Site section has all required time series:

```python
from lxml import etree

root = etree.parse('plot.plo')
required_ts = ['avgAirTemp', 'rainfall', 'openPanEvap', 'forestProdIx']

site = root.find('.//Site')
found_ts = [ts.get('tInTS') for ts in site.findall('TimeSeries')]

missing = set(required_ts) - set(found_ts)
if missing:
    print(f"✗ Missing required time series: {missing}")
else:
    print(f"✓ All required time series present")
```

If missing, regenerate PLO (check cache files have complete data).

## Best Practices

### Code Organization

1. **Use assemble_plo_sections() for PLO generation**
   - Data is auto-downloaded when missing
   - Use `get_existing_downloads()` to check cached data

2. **Use cache management utilities**
   - Don't scan `downloaded/` directory directly
   - Use `get_existing_downloads()` for fast lookups

3. **Handle errors gracefully**
   - Always use try/except for file operations
   - Check API response status codes
   - Validate PLO files before simulation

### Performance Tips

1. **Parallel processing**
   - Use `joblib.Parallel` for batch operations
   - Limit threads to avoid rate limits (35 recommended)

2. **Cache optimization**
   - Keep cache index up to date
   - Rebuild cache after manual file operations

3. **Memory management**
   - Process large datasets in chunks
   - Use xarray lazy loading for NetCDF operations

### Security

1. **API key protection**
   - Never hardcode API keys
   - Use environment variables
   - Don't commit keys to git

2. **Input validation**
   - Validate coordinate ranges
   - Check file paths for directory traversal
   - Sanitize user inputs

## Related Documentation

- **[Architecture Guide](architecture.md)** - System design and data flow
- **[API Reference](api-reference.md)** - Functions and API endpoints
- **[PLO Files Guide](plo-files.md)** - XML structure and validation
