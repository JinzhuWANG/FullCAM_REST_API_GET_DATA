# Download Cache System

## Overview

The caching system eliminates the need to scan ~40 million XML files on every run by maintaining a text file that logs all successful downloads. This dramatically improves startup time from minutes/hours to seconds.

## How It Works

### Cache File: `downloaded/successful_downloads.txt`

This file contains one filename per line for every successfully downloaded file (XML and CSV):

```
siteInfo_148.16_-35.61.xml
species_148.16_-35.61.xml
df_-35.61_148.16.csv
siteInfo_148.18_-35.61.xml
species_148.18_-35.61.xml
df_-35.61_148.18.csv
...
```

### Automatic Logging

When `get_siteinfo()`, `get_species()`, or `get_plot_simulation()` successfully downloads a file (HTTP 200 response), it:

1. Saves the file to:
   - `downloaded/siteInfo_{lon}_{lat}.xml` (site data)
   - `downloaded/species_{lon}_{lat}.xml` (species parameters)
   - `downloaded/simulation/df_{lat}_{lon}.csv` (simulation results)
2. **Immediately appends** the filename to `downloaded/successful_downloads.txt`

This append operation is:
- **Thread-safe**: File is opened in append mode (`'a'`) which is atomic on most systems
- **Automatic**: No manual intervention needed
- **Crash-resistant**: Each successful download is logged immediately

### Fast Startup

When `get_data.py` runs:

1. Loads `downloaded/successful_downloads.txt` (fast text file read)
2. Parses lon/lat coordinates from filenames using regex
3. Skips already-downloaded coordinates
4. Resumes downloading missing coordinates

**Performance:**
- Old method (scandir): Minutes to hours for 40M files
- New method (cache file): Seconds to load text file

## Usage

### Normal Operation

Just run the script normally:

```bash
python get_data.py
```

The script will:
- Load existing downloads from cache (if exists)
- Skip already-downloaded coordinates
- Log new successful downloads automatically

### First Run

If `downloaded/successful_downloads.txt` doesn't exist:
- Script creates an empty cache file
- All coordinates are downloaded
- Each successful download is logged to the cache

### Resume After Interruption

If the download process is interrupted (crash, network failure, Ctrl+C):

1. Simply run `python get_data.py` again
2. The cache already contains all previously successful downloads
3. Script automatically skips completed coordinates
4. Continues downloading remaining coordinates

### Rebuild Cache (if needed)

If the cache file gets corrupted or deleted, but you have existing XML files:

```bash
python tools/rebuild_cache.py
```

This utility:
- Scans the `downloaded/` directory (one-time slow operation)
- Recreates `downloaded/successful_downloads.txt` from existing files
- Shows progress and statistics

**When to rebuild:**
- Cache file accidentally deleted
- Manually copied files from another location
- Cache file corrupted
- Want to verify cache integrity

## Thread Safety

The append operation (`open(file, 'a')`) is thread-safe on most operating systems because:

1. **Atomic writes**: Small writes (<4KB) to append mode are atomic on POSIX systems
2. **Windows buffering**: Windows file system handles concurrent appends
3. **Each thread writes separately**: No shared file handle between threads

With 35 concurrent threads downloading data, multiple threads may write to the cache simultaneously. This is safe because each write is a single line (<100 bytes).

## Cache File Format

```
siteInfo_{lon}_{lat}.xml
species_{lon}_{lat}.xml
df_{lat}_{lon}.csv
```

**Rules:**
- One filename per line
- No path prefix (just filename, not `downloaded/filename` or `downloaded/simulation/filename`)
- Empty lines are ignored
- Order doesn't matter
- Duplicates are harmless (set-based filtering)
- Note: Dataframe files use `df_{lat}_{lon}.csv` format (lat first, lon second)

## Monitoring Progress

The cache file grows as downloads complete. To check progress:

**Line count (number of successful downloads):**
```bash
# Windows (PowerShell)
(Get-Content downloaded\successful_downloads.txt).Count

# Linux/Mac
wc -l downloaded/successful_downloads.txt
```

**Recent downloads (last 10):**
```bash
# Windows (PowerShell)
Get-Content downloaded\successful_downloads.txt -Tail 10

# Linux/Mac
tail -n 10 downloaded/successful_downloads.txt
```

**Search for specific coordinate:**
```bash
# Windows (PowerShell)
Select-String "148.16_-35.61" downloaded\successful_downloads.txt

# Linux/Mac
grep "148.16_-35.61" downloaded/successful_downloads.txt
```

## Benefits

### Speed
- **Old method**: Scan ~40M files every run (minutes to hours)
- **New method**: Read text file once (seconds)

### Simplicity
- No database required
- Plain text file (human-readable, easy to inspect)
- Works with version control (if needed)

### Reliability
- Automatic logging on successful downloads
- Thread-safe append operations
- Resume-friendly (no state loss on crash)

### Flexibility
- Easy to rebuild from existing files
- Can manually edit if needed
- Compatible with file copying utilities

## Troubleshooting

### Cache file very large (>1GB)

This is normal with millions of downloads. Text file loading is still fast even at 1-2GB.

### Duplicate entries in cache

Harmless. The filtering uses set-based operations, so duplicates are automatically ignored.

### Cache out of sync with actual files

Run `python tools/rebuild_cache.py` to rescan and rebuild.

### Slow performance even with cache

Check that:
1. Cache file exists: `downloaded/successful_downloads.txt`
2. Script is loading from cache (look for "Loading cache from..." message)
3. You're not accidentally running `rebuild_cache.py` every time

## Advanced: Multiple Download Directories

If you need to merge downloads from multiple sources:

```bash
# Combine multiple cache files
cat source1/successful_downloads.txt source2/successful_downloads.txt > combined_cache.txt

# Remove duplicates (optional)
sort combined_cache.txt | uniq > downloaded/successful_downloads.txt
```

Or rebuild from combined directories:

```python
# Modify rebuild_cache.py to scan multiple directories
# Or copy all XML files to one directory, then rebuild
```
