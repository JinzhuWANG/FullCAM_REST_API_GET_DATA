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

def load_cache(cache_file: str = 'downloaded/successful_downloads.txt') -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]], List[Tuple[float, float]]]:
    """
    Load existing downloads from cache file.

    Parameters
    ----------
    cache_file : str, optional
        Path to cache file (default: 'downloaded/successful_downloads.txt')

    Returns
    -------
    existing_siteinfo : List[Tuple[float, float]]
        List of (lat, lon) tuples for existing siteInfo files
    existing_species : List[Tuple[float, float]]
        List of (lat, lon) tuples for existing species files
    existing_dfs : List[Tuple[float, float]]
        List of (lat, lon) tuples for existing simulation dataframe files
    """
    lon_lat_reg_xml = re.compile(r'.*_(-?\d+\.\d+)_(-?\d+\.\d+)\.xml')
    lon_lat_reg_csv = re.compile(r'df_(-?\d+\.\d+)_(-?\d+\.\d+)\.csv')

    existing_siteinfo = []
    existing_species = []
    existing_dfs = []

    if not os.path.exists(cache_file):
        print(f"Cache file not found: {cache_file}")
        return existing_siteinfo, existing_species, existing_dfs

    print(f"Loading cache from {cache_file}...")

    with open(cache_file, 'r', encoding='utf-8') as f:
        for line in f:

            if line.startswith('siteInfo_'):
                match = lon_lat_reg_xml.findall(line)
                if match:
                    lon, lat = match[0]
                    existing_siteinfo.append((float(lat), float(lon)))
            elif line.startswith('species_'):
                match = lon_lat_reg_xml.findall(line)
                if match:
                    lon, lat = match[0]
                    existing_species.append((float(lat), float(lon)))
            elif line.startswith('df_'):
                match = lon_lat_reg_csv.findall(line)
                if match:
                    lat, lon = match[0]
                    existing_dfs.append((float(lat), float(lon)))

    print(f"Loaded {len(existing_siteinfo):,} siteInfo, {len(existing_species):,} species, and {len(existing_dfs):,} df entries from cache")

    return existing_siteinfo, existing_species, existing_dfs


def rebuild_cache(downloaded_dir: str = 'downloaded',
                  cache_file: str = 'downloaded/successful_downloads.txt',
                 ) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]], List[Tuple[float, float]]]:
    """
    Rebuild cache by scanning downloaded/ directory.

    This is a slow operation for large directories (~40M files).
    Only use when cache file is missing or corrupted.

    Parameters
    ----------
    downloaded_dir : str, optional
        Directory containing downloaded XML files (default: 'downloaded')
    cache_file : str, optional
        Path to cache file to create (default: 'downloaded/successful_downloads.txt')
    verbose : bool, optional
        Print progress messages (default: True)

    Returns
    -------
    existing_siteinfo : List[Tuple[float, float]]
        List of (lat, lon) tuples for existing siteInfo files
    existing_species : List[Tuple[float, float]]
        List of (lat, lon) tuples for existing species files
    existing_dfs : List[Tuple[float, float]]
        List of (lat, lon) tuples for existing simulation dataframe files
    """


    if not os.path.exists(downloaded_dir):
        print(f"Error: {downloaded_dir} directory not found!")
        return [], [], []

    print(f"Rebuilding cache by scanning {downloaded_dir} directory...")
    print("This is a one-time slow operation for large directories.")

    files = [entry.path for entry in Scandir(downloaded_dir)]
    lon_lat_reg_xml = re.compile(r'.*_(-?\d+\.\d+)_(-?\d+\.\d+)\.xml')
    lon_lat_reg_csv = re.compile(r'df_(-?\d+\.\d+)_(-?\d+\.\d+)\.csv')

    siteinfo_files = []
    species_files = []
    df_files = []
    existing_siteinfo = []
    existing_species = []
    existing_dfs = []

    # Collect filenames and coordinates
    iterator = tqdm(files, desc="Scanning files")
    for filepath in iterator:
        filename = os.path.basename(filepath)

        if filename.startswith('siteInfo_'):
            match = lon_lat_reg_xml.match(filename)
            if match:
                lon, lat = match.groups()
                siteinfo_files.append(filename)
                existing_siteinfo.append((float(lat), float(lon)))
        elif filename.startswith('species_'):
            match = lon_lat_reg_xml.match(filename)
            if match:
                lon, lat = match.groups()
                species_files.append(filename)
                existing_species.append((float(lat), float(lon)))
        elif filename.startswith('df_'):
            match = lon_lat_reg_csv.match(filename)
            if match:
                lat, lon = match.groups()
                df_files.append(filename)
                existing_dfs.append((float(lat), float(lon)))


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

    return existing_siteinfo, existing_species, existing_dfs


def get_existing_downloads(cache_file: str = 'downloaded/successful_downloads.txt',
                           downloaded_dir: str = 'downloaded',
                           auto_rebuild: bool = True) -> Tuple[List[Tuple[float, float]], List[Tuple[float, float]], List[Tuple[float, float]]]:
    """
    Get existing downloads from cache, rebuilding if necessary.

    This is the main entry point for getting existing downloads.
    - If cache file exists: load from cache (fast)
    - If cache file missing and auto_rebuild=True: rebuild from directory scan (slow)
    - If cache file missing and auto_rebuild=False: return empty lists

    Parameters
    ----------
    cache_file : str, optional
        Path to cache file (default: 'downloaded/successful_downloads.txt')
    downloaded_dir : str, optional
        Directory containing downloaded XML files (default: 'downloaded')
    auto_rebuild : bool, optional
        Automatically rebuild cache if missing (default: True)

    Returns
    -------
    existing_siteinfo : List[Tuple[float, float]]
        List of (lat, lon) tuples for existing siteInfo files
    existing_species : List[Tuple[float, float]]
        List of (lat, lon) tuples for existing species files
    existing_dfs : List[Tuple[float, float]]
        List of (lat, lon) tuples for existing simulation dataframe files

    """
    # Try to load from cache first
    if os.path.exists(cache_file):
        return load_cache(cache_file)

    # Cache doesn't exist
    print(f"Cache file not found: {cache_file}")

    if auto_rebuild:
        # Check if downloaded directory has files
        if os.path.exists(downloaded_dir):
            file_count = len([f for f in os.listdir(downloaded_dir) if f.endswith('.xml') or f.endswith('.csv')])

            if file_count > 0:
                print(f"Found {file_count:,} files in {downloaded_dir}")
                response = input("Rebuild cache from existing files? This may take a while. (y/n): ")

                if response.lower() == 'y':
                    return rebuild_cache(downloaded_dir, cache_file)
                else:
                    print("Skipping cache rebuild. Starting fresh.")
                    # Create empty cache file
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        pass
                    return [], [], []
            else:
                print(f"No files found in {downloaded_dir}. Starting fresh.")
                # Create empty cache file
                with open(cache_file, 'w', encoding='utf-8') as f:
                    pass
                return [], [], []
        else:
            print(f"Directory {downloaded_dir} not found. Creating empty cache.")
            os.makedirs(downloaded_dir, exist_ok=True)
            with open(cache_file, 'w', encoding='utf-8') as f:
                pass
            return [], [], []
    else:
        print("Auto-rebuild disabled. Starting fresh.")
        # Create empty cache file
        with open(cache_file, 'w', encoding='utf-8') as f:
            pass
        return [], [], []
