import os
import requests
import pandas as pd

from lxml import etree
from io import StringIO


# Configuration
API_KEY = os.getenv("FULLCAM_API_KEY")
if not API_KEY: raise ValueError("`FULLCAM_API_KEY`environment variable not set!")

BASE_URL_DATA = "https://api.dcceew.gov.au/climate/carbon-accounting/2024/data/v1"
HEADERS = {
    "Host": "api.dcceew.gov.au",
    "Ocp-Apim-Subscription-Key": API_KEY,
    "Content-Type": "application/json"
}


# ----------------------- SiteInfo --------------------------
ENDPOINT = "/2024/data-builder/siteinfo"
# Request parameters
PARAMS = {
    "latitude": -35.61,
    "longitude": 148.16,
    "area": "OneKm",
    "plotT": "CompF",
    "frCat": "All",
    "incGrowth": "false",
    "version": 2024
}
url = f"{BASE_URL_DATA}{ENDPOINT}"
response = requests.get(url, params=PARAMS, headers=HEADERS, timeout=10)

with open('data/siteinfo_response.xml', 'wb') as f:
    f.write(response.content)


# ----------------------- Species --------------------------
ENDPOINT = "/2024/data-builder/species"
PARAMS = {
    "latitude": -35.61,
    "longitude": 148.16,
    "area": "OneKm",
    "frCat": "Plantation",
    "specId": 8,            # Eucalyptus globulus, used as Carbon Plantations in LUTO
    "version": 2024
}
url = f"{BASE_URL_DATA}{ENDPOINT}"
response = requests.get(url, params=PARAMS, headers=HEADERS, timeout=10)
with open('data/species_response.xml', 'wb') as f:
    f.write(response.content)
    
    
# ----------------------- Regimes --------------------------
ENDPOINT = "/2024/data-builder/regimes"
PARAMS = {
    "latitude": -35.61,
    "longitude": 148.16,
    "specId": 1,            # Eucalyptus globulus, used as Carbon Plantations in LUTO
    "frCat": "All"
}
url = f"{BASE_URL_DATA}{ENDPOINT}"
response = requests.get(url, params=PARAMS, headers=HEADERS, timeout=10)
with open('data/regimes_response.xml', 'wb') as f:
    f.write(response.content)



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



