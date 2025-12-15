"""
Download cache management for FullCAM API data.

Provides functions to:
- Load existing downloads from cache file (fast)
- Rebuild cache from directory scan (slow, one-time)
- Automatically use cache or rebuild if missing
"""

import os
import re
from typing import Tuple, List
from scandir_rs import Scandir
from tqdm.auto import tqdm
from joblib import Parallel, delayed



def get_existing_downloads(
    specId: int,
    specCat: str,
    cache_file: str = 'downloaded/successful_downloads.txt',
    downloaded_dir: str = 'downloaded'
) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]], List[Tuple[float, float]]]:
    """
    Get existing downloads from cache, rebuilding if necessary.

    This is the main entry point for getting existing downloads.
    - If cache file exists: load from cache (fast)
    - If cache file missing: rebuild from directory scan (slow)

    Parameters
    ----------
    specId : int
        Species ID to filter species and df files.
    specCat : str
        Species category ('Block' or 'Belt') to filter df files.
    cache_file : str, optional
        Path to cache file (default: 'downloaded/successful_downloads.txt')
    downloaded_dir : str, optional
        Directory containing downloaded XML files (default: 'downloaded')

    Returns
    -------
    existing_siteinfo : List[Tuple[float, float]]
        List of (lon, lat) tuples for existing siteInfo files
    existing_species : List[Tuple[float, float]]
        List of (lon, lat) tuples for existing species files (filtered by specId)
    existing_dfs : List[Tuple[float, float]]
        List of (lon, lat) tuples for existing simulation dataframe files (filtered by specId and specCat)

    """
    # Try to load from cache first
    if os.path.exists(cache_file):
        return load_cache(specId, specCat, cache_file)

    # Cache doesn't exist - rebuild it (rebuilds ALL records)
    print(f"Cache file not found: {cache_file}"
            " - rebuilding cache from downloaded directory...")
    rebuild_cache(downloaded_dir, cache_file)

    # Now load from the rebuilt cache with filtering
    return load_cache(specId, specCat, cache_file)



def load_cache(
    specId: int,
    specCat: str,
    cache_file: str = 'downloaded/successful_downloads.txt'
) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]], List[Tuple[float, float]]]:
    """
    Load existing downloads from cache file.

    Parameters
    ----------
    specId : int
        Species ID to filter species and df files.
    specCat : str
        Species category ('Block' or 'Belt') to filter df files.
    cache_file : str, optional
        Path to cache file (default: 'downloaded/successful_downloads.txt')

    Returns
    -------
    existing_siteinfo : List[Tuple[float, float]]
        List of (lon, lat) tuples for existing siteInfo files
    existing_species : List[Tuple[float, float]]
        List of (lon, lat) tuples for existing species files (filtered by specId)
    existing_dfs : List[Tuple[float, float]]
        List of (lon, lat) tuples for existing simulation dataframe files (filtered by specId and specCat)
    """
    lon_lat_reg_xml = re.compile(r'siteInfo_(-?\d+\.\d+)_(-?\d+\.\d+)\.xml')
    lon_lat_reg_species = re.compile(r'species_(-?\d+\.\d+)_(-?\d+\.\d+)_specId_(\d+)\.xml')
    lon_lat_reg_csv = re.compile(r'df_(-?\d+\.\d+)_(-?\d+\.\d+)_specId_(\d+)_specCat_(\w+)\.csv')

    existing_siteinfo = []
    existing_species = []
    existing_dfs = []

    if not os.path.exists(cache_file):
        print(f"Cache file not found: {cache_file}")
        return existing_siteinfo, existing_species, existing_dfs

    print(f"Loading cache from {cache_file}...")
    print(f"Filtering for specId={specId}, specCat={specCat}")

    with open(cache_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()

            if line.startswith('siteInfo_'):
                match = lon_lat_reg_xml.match(line)
                if match:
                    lon, lat = match.groups()
                    existing_siteinfo.append((float(lon), float(lat)))
            elif line.startswith('species_'):
                match = lon_lat_reg_species.match(line)
                if match:
                    lon, lat, file_specId = match.groups()
                    if int(file_specId) == specId:
                        existing_species.append((float(lon), float(lat)))
            elif line.startswith('df_'):
                match = lon_lat_reg_csv.match(line)
                if match:
                    lon, lat, file_specId, file_specCat = match.groups()
                    if int(file_specId) == specId and file_specCat == specCat:
                        existing_dfs.append((float(lon), float(lat)))

    print(f"Loaded {len(existing_siteinfo):,} siteInfo, {len(existing_species):,} species, and {len(existing_dfs):,} df entries from cache")

    return existing_siteinfo, existing_species, existing_dfs


def rebuild_cache(
    downloaded_dir: str = 'downloaded',
    cache_file: str = 'downloaded/successful_downloads.txt'
) -> Tuple[int, int, int]:
    """
    Rebuild cache by scanning downloaded/ directory for ALL records.

    This is a slow operation for large directories (~40M files).
    Only use when cache file is missing or corrupted.

    Scans for all file types:
    - siteInfo_*.xml - Site information files
    - species_*.xml - Species parameter files (all specIds)
    - df_*.csv - Simulation result files (all specIds and specCats)

    Parameters
    ----------
    downloaded_dir : str, optional
        Directory containing downloaded XML files (default: 'downloaded')
    cache_file : str, optional
        Path to cache file to create (default: 'downloaded/successful_downloads.txt')

    Returns
    -------
    Tuple[int, int, int]
        (siteinfo_count, species_count, df_count) - counts of each file type found
    """

    if not os.path.exists(downloaded_dir):
        print(f"Error: {downloaded_dir} directory not found!")
        return 0, 0, 0

    print(f"Rebuilding cache by scanning {downloaded_dir} directory...")
    print("This is a one-time slow operation for large directories.")
    print("Scanning ALL siteInfo, species, and df files...")

    files = [entry.path for entry in Scandir(downloaded_dir)]

    # Regex patterns to match all file types (no filtering by specId/specCat)
    lon_lat_reg_siteinfo = re.compile(r'siteInfo_(-?\d+\.\d+)_(-?\d+\.\d+)\.xml')
    lon_lat_reg_species = re.compile(r'species_(-?\d+\.\d+)_(-?\d+\.\d+)_specId_\d+\.xml')
    lon_lat_reg_df = re.compile(r'df_(-?\d+\.\d+)_(-?\d+\.\d+)_specId_\d+_specCat_\w+\.csv')

    siteinfo_files = []
    species_files = []
    df_files = []

    # Collect all filenames
    for filepath in tqdm(files, desc="Scanning files"):
        filename = os.path.basename(filepath)

        if filename.startswith('siteInfo_'):
            if lon_lat_reg_siteinfo.match(filename):
                siteinfo_files.append(filename)
        elif filename.startswith('species_'):
            if lon_lat_reg_species.match(filename):
                species_files.append(filename)
        elif filename.startswith('df_'):
            if lon_lat_reg_df.match(filename):
                df_files.append(filename)

    with open(cache_file, 'w', encoding='utf-8') as f:
        all_files = sorted(siteinfo_files + species_files + df_files)
        iterator = tqdm(all_files, desc="Writing cache")
        for filename in iterator:
            f.write(f'{filename}\n')

    # Final report
    print(f"\nCache rebuilt successfully!")
    print(f"  - {len(siteinfo_files):,} siteInfo files")
    print(f"  - {len(species_files):,} species files")
    print(f"  - {len(df_files):,} df files")
    print(f"  - Total: {len(siteinfo_files) + len(species_files) + len(df_files):,} files")

    return len(siteinfo_files), len(species_files), len(df_files)


def _remove_single_file(filepath: str) -> Tuple[str, bool, str]:
    """
    Remove a single file.

    Parameters
    ----------
    filepath : str
        Full path to the file to remove

    Returns
    -------
    Tuple[str, bool, str]
        (filepath, success, error_message)
    """
    try:
        os.remove(filepath)
        return (filepath, True, "")
    except Exception as e:
        return (filepath, False, str(e))


def batch_remove_files(
    pattern: str,
    directory: str = 'downloaded',
    n_jobs: int = 100,
) -> Tuple[int, int, List[Tuple[str, str]]]:
    """
    Batch remove files containing a pattern string in their filename.

    Uses joblib with threading backend for fast parallel deletion.

    Parameters
    ----------
    pattern : str
        String pattern to match in filenames. Any file whose name contains
        this string will be removed.
    directory : str, optional
        Directory to search for files (default: 'downloaded')
    n_jobs : int, optional
        Number of parallel threads (default: 100)

    Returns
    -------
    Tuple[int, int, List[Tuple[str, str]]]
        (success_count, failure_count, list of (filepath, error) for failures)
    """
    if not os.path.exists(directory):
        print(f"Error: Directory {directory} not found!")
        return 0, 0, []

    print(f"Scanning {directory} for files containing '{pattern}'...")

    # Scan directory for matching files
    matching_files = []
    files = [entry.path for entry in Scandir(directory)]
    for entry in files:
        filename = os.path.basename(entry)
        if pattern in filename:
            matching_files.append(entry)

    if not matching_files:
        print(f"No files found containing '{pattern}'")
        return 0, 0, []

    print(f"Removing {len(matching_files):,} files using {n_jobs} threads...")

    # Parallel deletion using threading backend
    results = Parallel(n_jobs=n_jobs, backend='threading')(
        delayed(_remove_single_file)(f'{directory}/{filepath}')
        for filepath in tqdm(matching_files, desc="Removing files")
    )

    # Count successes and failures
    success_count = sum(1 for _, success, _ in results if success)
    failures = [(filepath, error) for filepath, success, error in results if not success]

    print(f"\nRemoval complete:")
    print(f"  - Successfully removed: {success_count:,} files")
    print(f"  - Failed: {len(failures):,} files")

    if failures:
        print("\nFailed files:")
        for filepath, error in failures[:10]:
            print(f"  {os.path.basename(filepath)}: {error}")
        if len(failures) > 10:
            print(f"  ... and {len(failures) - 10:,} more failures")

    return success_count, len(failures), failures
