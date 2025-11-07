import shutil

from scandir_rs import Scandir
from pathlib import Path
from joblib import Parallel, delayed
from tqdm.auto import tqdm

dir_from = "N:/Data-Master/FullCAM/FullCAM_REST_API_GET_DATA_2025/downloaded"
dir_to = "F:/jinzhu/FullCAM_REST_API_GET_DATA_2025/downloaded"

# Create destination directory if it doesn't exist
Path(dir_to).mkdir(parents=True, exist_ok=True)

def copy_file_if_not_exists(file_path, source_dir, dest_dir):
    """Copy a single file if it doesn't exist in destination."""
    try:
        source_file = Path(file_path)
        dest_file = Path(dest_dir) / source_file.name

        if dest_file.exists():
            return ('skipped', source_file.name)
        else:
            shutil.copy2(source_file, dest_file)
            return ('copied', source_file.name)
    except Exception as e:
        return ('error', f"{source_file.name}: {str(e)}")

# Use scandir_rs to get all files
source_path = Path(dir_from)
files = [entry.path for entry in Scandir(str(source_path)) if entry.is_file()]

print(f"Found {len(files)} files in source directory")

# Parallel copy with progress bar
tasks = [delayed(copy_file_if_not_exists)(file_path, dir_from, dir_to) for file_path in files]

results = []
for result in tqdm(Parallel(n_jobs=-1, backend='threading', return_as='generator')(tasks),
                   total=len(tasks), desc="Copying files"):
    results.append(result)

# Summary
copied = sum(1 for status, _ in results if status == 'copied')
skipped = sum(1 for status, _ in results if status == 'skipped')
errors = sum(1 for status, _ in results if status == 'error')

print(f"\n--- Summary ---")
print(f"Copied: {copied} files")
print(f"Skipped: {skipped} files (already exist)")
print(f"Errors: {errors} files")

if errors > 0:
    print("\nErrors:")
    for status, msg in results:
        if status == 'error':
            print(f"  {msg}")