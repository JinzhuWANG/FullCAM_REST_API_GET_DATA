import os,time,re
import requests
import rioxarray as rio
import xarray as xr
import numpy as np
from scandir_rs import Scandir

from joblib import Parallel, delayed
from tqdm.auto import tqdm



# Configuration
#   If having issues with API access, try running below snippet to temporarily adding key to current session:
#   WARNING: Do not hardcode API keys in production code!

'''
import os
os.environ["FULLCAM_API_KEY"] = "your_api_key_here"
'''

API_KEY = os.getenv("FULLCAM_API_KEY")
if not API_KEY: raise ValueError("`FULLCAM_API_KEY`environment variable not set!")

BASE_URL_DATA = "https://api.dcceew.gov.au/climate/carbon-accounting/2024/data/v1"
HEADERS = {
    "Host": "api.dcceew.gov.au",
    "Ocp-Apim-Subscription-Key": API_KEY,
    "Content-Type": "application/json"
}

# Create downloaded folder if not exists
if not os.path.exists('downloaded'):
    os.makedirs('downloaded')


# Get all lon/lat for Australia; the raster used is taken from the template of LUTO
Aus_xr = rio.open_rasterio("data/lumap.tif").sel(band=1, drop=True).compute() >= 0 # >=0 only includes LUTO study area
lon_lat = Aus_xr.to_dataframe(name='mask').reset_index()[['y', 'x', 'mask']].round({'x':2, 'y':2})
lon_lat['cell_idx'] = range(len(lon_lat))
lon_lat['site_fetch'] = 'Untried'
lon_lat['species_fetch'] = 'Untried'


Aus_cell = xr.DataArray(np.arange(Aus_xr.size).reshape(Aus_xr.shape), coords=Aus_xr.coords, dims=Aus_xr.dims)
Aus_cell_RES5 = Aus_cell.coarsen(x=5, y=5, boundary='trim').max()
Aus_cell_RES5_df = Aus_cell_RES5.to_dataframe(name='cell_idx').reset_index()[['y', 'x', 'cell_idx']]


scrap_coords = lon_lat\
    .query('mask == True')\
    .loc[lon_lat['cell_idx'].isin(Aus_cell_RES5_df['cell_idx'])]
    



# Remove existing downloaded files
lon_lat_reg = re.compile(r'.*_(-?\d+\.\d+)_(-?\d+\.\d+)\.xml')

existing_siteinfo = []
existing_species = []

# Scan directory once using scandir_rs
for entry in Scandir('downloaded'):
    filename = entry.path
    if filename.startswith('siteInfo_'):
        lon, lat = lon_lat_reg.findall(filename)[0]
        existing_siteinfo.append((float(lat), float(lon)))
    elif filename.startswith('species_'):
        lon, lat = lon_lat_reg.findall(filename)[0]
        existing_siteinfo.append((float(lat), float(lon)))


scrap_coords_siteinfo = scrap_coords[~scrap_coords.set_index(['y', 'x']).index.isin(existing_siteinfo)].reset_index(drop=True)
scrap_coords_species = scrap_coords[~scrap_coords.set_index(['y', 'x']).index.isin(existing_species)].reset_index(drop=True)


# ----------------------- SiteInfo --------------------------
def get_siteinfo(lat, lon, try_number=8):
    PARAMS = {
        "latitude": lat,
        "longitude": lon,
        "area": "OneKm",
        "plotT": "CompF",
        "frCat": "All",
        "incGrowth": "false",
        "version": 2024
    }
    url = f"{BASE_URL_DATA}/2024/data-builder/siteinfo"
    
    for attempt in range(try_number):
        
        try:
            response = requests.get(url, params=PARAMS, headers=HEADERS, timeout=100)

            if response.status_code == 200:
                with open(f'downloaded/siteInfo_{lon}_{lat}.xml', 'wb') as f:
                    f.write(response.content)
                return
            else:
                # HTTP error - apply backoff before retry
                if attempt < try_number - 1:  
                    time.sleep(2**attempt)

        except requests.RequestException as e:
            if attempt < try_number - 1:  
                time.sleep(2**attempt)

    return f'{lon},{lat}', "Failed"


if __name__ == "__main__":
    # Create tasks for parallel processing
    tasks = [delayed(get_siteinfo)(lat, lon) 
            for lat, lon in tqdm(zip(scrap_coords_siteinfo['y'], scrap_coords_siteinfo['x']), total=len(scrap_coords_siteinfo))
    ]

    for rtn in tqdm(Parallel(n_jobs=35,  backend='threading', return_as='generator_unordered')(tasks), total=len(tasks)):
        if rtn is not None:
            print(rtn)
    



# ----------------------- Species --------------------------
def get_species(lat, lon, try_number=8):
    
    url = f"{BASE_URL_DATA}/2024/data-builder/species"
    PARAMS = {
        "latitude": lat,
        "longitude": lon,
        "area": "OneKm",
        "frCat": "Plantation",
        "specId": 8,            # Eucalyptus globulus, used as Carbon Plantations in LUTO
        "version": 2024
    }
    
    for attempt in range(try_number):
        
        try:
            response = requests.get(url, params=PARAMS, headers=HEADERS, timeout=100)

            if response.status_code == 200:
                with open(f'downloaded/species_{lon}_{lat}.xml', 'wb') as f:
                    f.write(response.content)
                return
            else:
                # HTTP error - apply backoff before retry
                if attempt < try_number - 1:  
                    time.sleep(2**attempt)

        except requests.RequestException as e:
            if attempt < try_number - 1:  
                time.sleep(2**attempt)
                
    return f'{lon},{lat}', "Failed"


if __name__ == "__main__":
    # Create tasks for parallel processing
    tasks = [delayed(get_species)(lat, lon)
                for lat, lon in tqdm(zip(scrap_coords_species['y'], scrap_coords_species['x']), total=len(scrap_coords_species))
            ]

    for rtn in tqdm(Parallel(n_jobs=35,  backend='threading', return_as='generator_unordered')(tasks), total=len(tasks)):
        if rtn is not None:
            print(rtn)

    
    
    
    
# # ----------------------- Regimes --------------------------
# ENDPOINT = "/2024/data-builder/regimes"
# PARAMS = {
#     "latitude": -35.61,
#     "longitude": 148.16,
#     "specId": 1,            # Eucalyptus globulus, used as Carbon Plantations in LUTO
#     "frCat": "All"
# }
# url = f"{BASE_URL_DATA}{ENDPOINT}"
# response = requests.get(url, params=PARAMS, headers=HEADERS, timeout=10)
# with open('data/regimes_response.xml', 'wb') as f:
#     f.write(response.content)



# # ----------------------- Templates --------------------------
# ENDPOINT = "/2024/data-builder/templates"
# ARGUMENTS = {
#     'version' : 2024
# }
# url = f"{BASE_URL_DATA}{ENDPOINT}"
# response = requests.get(url, params=ARGUMENTS, headers=HEADERS, timeout=10)

# with open('data/templates_response.xml', 'wb') as f:
#     f.write(response.content)


# # ----------------------- Template --------------------------
# ENDPOINT = "/2024/data-builder/template"
# ARGUMENTS = {
#     'templateName' : r"ERF\Environmental Plantings Method.plo",
#     'version' : 2024
# }
# url = f"{BASE_URL_DATA}{ENDPOINT}"

# response = requests.get(url, params=ARGUMENTS, headers=HEADERS, timeout=10)
# response.content


# with open('data/single_template_response.xml', 'wb') as f:
#     root = etree.fromstring(response.content)
#     document_plot = root.find('DocumentPlot')
#     f.write(etree.tostring(document_plot, pretty_print=True, xml_declaration=True, encoding='utf-8'))
    


# # ----------------------- Update PLO --------------------------  
# ENDPOINT = "/2024/data-builder/convert-plotfile"
# url = f"{BASE_URL_DATA}{ENDPOINT}"

# with open("data/E_globulus_2024.plo", 'rb') as file:
#     file_data = file.read()

# response = requests.post(url, files={'file': ('test.plo', file_data)}, headers={"Ocp-Apim-Subscription-Key": API_KEY},  timeout=30)

# with open('data/updated_plotfile_response.xml', 'wb') as f:
#     f.write(response.content)




