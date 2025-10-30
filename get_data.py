import os,time
import requests
import pandas as pd
import rioxarray as rio

from lxml import etree
from io import StringIO
from joblib import Parallel, delayed
from tqdm.auto import tqdm



# Configuration
API_KEY = os.getenv("FULLCAM_API_KEY")
if not API_KEY: raise ValueError("`FULLCAM_API_KEY`environment variable not set!")

BASE_URL_DATA = "https://api.dcceew.gov.au/climate/carbon-accounting/2024/data/v1"
HEADERS = {
    "Host": "api.dcceew.gov.au",
    "Ocp-Apim-Subscription-Key": API_KEY,
    "Content-Type": "application/json"
}

# Get all lon/lat for Australia; the raster used is taken from the template of LUTO
Aus_xr = rio.open_rasterio("data/NLUM_2010-11_clip.tif").sel(band=1, drop=True).compute() > 0
lon_lat = Aus_xr.to_dataframe(name='mask').reset_index().query('mask == True')[['x', 'y']].round({'x':2, 'y':2})

lon_lat['idx'] = range(len(lon_lat))
lon_lat['site_fetch'] = False
lon_lat['species_fetch'] = False


# ----------------------- SiteInfo --------------------------
def get_siteinfo(idx, lat, lon, try_number=10):
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
                return idx, 'Success'
            else:
                # HTTP error - apply backoff before retry
                if attempt < try_number - 1:  # Don't sleep on last attempt
                    time.sleep(2**attempt)

        except requests.RequestException as e:
            if attempt < try_number - 1:  # Don't sleep on last attempt
                time.sleep(2**attempt)

    return idx, "Failed"


# Create tasks for parallel processing
tasks = [delayed(get_siteinfo)(idx, lat, lon) 
         for idx, lat, lon in tqdm(zip(lon_lat['idx'], lon_lat['y'], lon_lat['x']), total=len(lon_lat))
]


status = []
for rtn in tqdm(Parallel(n_jobs=50,  backend='threading', return_as='generator')(tasks), total=len(tasks)):
    idx, msg = rtn
    if msg != 'Success':
        print(idx, msg)
    status.append(rtn)
    



# ----------------------- Species --------------------------
def get_species(idx, lat, lon, try_number=10):
    
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
                return idx, 'Success'
            else:
                # HTTP error - apply backoff before retry
                if attempt < try_number - 1:  # Don't sleep on last attempt
                    time.sleep(2**attempt)

        except requests.RequestException as e:
            if attempt < try_number - 1:  # Don't sleep on last attempt
                time.sleep(2**attempt)
                
    return idx, "Failed"
    
# Create tasks for parallel processing
tasks = [delayed(get_species)(idx, lat, lon)
            for idx, lat, lon in tqdm(zip(lon_lat['idx'], lon_lat['y'], lon_lat['x']), total=len(lon_lat))
        ]

status = []
for rtn in tqdm(Parallel(n_jobs=50,  backend='threading', return_as='generator')(tasks), total=len(tasks)):
    idx, msg = rtn
    if msg != 'Success':
        print(idx, msg)
    status.append(rtn)
    
    
    
    
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



# ----------------------- Templates --------------------------
ENDPOINT = "/2024/data-builder/templates"
ARGUMENTS = {
    'version' : 2024
}
url = f"{BASE_URL_DATA}{ENDPOINT}"
response = requests.get(url, params=ARGUMENTS, headers=HEADERS, timeout=10)

with open('data/templates_response.xml', 'wb') as f:
    f.write(response.content)


# ----------------------- Template --------------------------
ENDPOINT = "/2024/data-builder/template"
ARGUMENTS = {
    'templateName' : r"ERF\Environmental Plantings Method.plo",
    'version' : 2024
}
url = f"{BASE_URL_DATA}{ENDPOINT}"

response = requests.get(url, params=ARGUMENTS, headers=HEADERS, timeout=10)
response.content


with open('data/single_template_response.xml', 'wb') as f:
    root = etree.fromstring(response.content)
    document_plot = root.find('DocumentPlot')
    f.write(etree.tostring(document_plot, pretty_print=True, xml_declaration=True, encoding='utf-8'))
    


# ----------------------- Update data --------------------------  
ENDPOINT = "/2024/data-builder/convert-plotfile"
url = f"{BASE_URL_DATA}{ENDPOINT}"

with open("data/E_globulus_2024.plo", 'rb') as file:
    file_data = file.read()

response = requests.post(url, files={'file': ('test.plo', file_data)}, headers={"Ocp-Apim-Subscription-Key": API_KEY},  timeout=30)

with open('data/updated_plotfile_response.xml', 'wb') as f:
    f.write(response.content)




# ----------------------- Plot simulation --------------------------
BASE_URL_SIM = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1"
ENDPOINT = "/2024/fullcam-simulator/run-plotsimulation"
url = f"{BASE_URL_SIM}{ENDPOINT}"

with open("data/E_globulus_2024.plo", 'rb') as file:
    file_data = file.read()

response = requests.post(url, files={'file': ('test.plo', file_data)}, headers={"Ocp-Apim-Subscription-Key": API_KEY},  timeout=30)
response_df = pd.read_csv(StringIO(response.text))



