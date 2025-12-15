import os
import shutil

from scandir_rs import Scandir
from pathlib import Path
from joblib import Parallel, delayed
from tqdm.auto import tqdm
from tools.helpers.cache_manager import get_existing_downloads




# ------------------- Copy files --------------------------
dir_from = "N:/Data-Master/FullCAM/FullCAM_REST_API_GET_DATA_2025/downloaded"
dir_to = "F:/jinzhu/FullCAM_REST_API_GET_DATA_2025/downloaded"

# Create destination directory if it doesn't exist
Path(dir_to).mkdir(parents=True, exist_ok=True)

def copy_file_if_not_exists(file, source_dir, dest_dir):
    """Copy a single file if it doesn't exist in destination."""
    try:
        source_file = Path(source_dir) / file
        dest_file = Path(dest_dir) / file

        if dest_file.exists():
            return ('skipped', source_file.name)
        else:
            shutil.copy2(source_file, dest_file)
            return ('copied', source_file.name)
    except Exception as e:
        return ('error', f"{source_file.name}: {str(e)}")

# Use scandir_rs to get all files
files = [entry.path for entry in Scandir(str(Path(dir_from))) if entry.is_file]

# with open('files.pkl', 'wb') as log_file:
#     pickle.dump(files, log_file)

print(f"Found {len(files)} files in source directory")

# Parallel copy with progress bar
tasks = [delayed(copy_file_if_not_exists)(file, dir_from, dir_to) for file in files]

results = []
for result in tqdm(Parallel(n_jobs=-1, backend='threading', return_as='generator')(tasks),
                   total=len(tasks), desc="Copying files"):
    results.append(result)
    
    
# ------------------- Delete files --------------------------
SPECIES_ID = 8          # Eucalyptus globulus
SPECIES_CAT = 'Block'   # Block or Belt; need to confirm with individual species
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads(SPECIES_ID, SPECIES_CAT)

files_siteinfo = [f'downloaded/siteInfo_{lon}_{lat}.xml' for lon,lat in existing_siteinfo] 
files_species = [f'downloaded/species_{lon}_{lat}.xml' for lon,lat in existing_species] 
files_dfs = [f'downloaded/df_{lon}_{lat}.csv' for lon,lat in existing_dfs]
files_record = ['downloaded/successful_downloads.txt']

rm_files = files_siteinfo + files_dfs + files_record

def rm_file(file:str):
    try:
        if os.path.exists(file):
            os.remove(file)
    except Exception as e:
        pass  # Silently ignore errors if file doesn't exist or can't be deleted

tasks = [delayed(rm_file)(file) for file in rm_files]
for _ in tqdm(Parallel(n_jobs=-1, backend='threading', return_as='generator')(tasks),total=len(tasks), desc="Deleting files"):
    pass




