import os
import requests
import pandas as pd

from io import StringIO
from lxml import etree

from tools.plo_section_functions import (
    create_build_section,
    create_config_section,
    create_meta_section,
    create_site_section,
    create_species_section,
    create_timing_section
)



# Configuration
API_KEY = os.getenv("FULLCAM_API_KEY")
if not API_KEY: raise ValueError("`FULLCAM_API_KEY`environment variable not set!")

BASE_URL_SIM = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1"
ENDPOINT = "/2024/fullcam-simulator/run-plotsimulation"
HEADERS = {
    "Host": "api.dcceew.gov.au",
    "Ocp-Apim-Subscription-Key": API_KEY,
    "Content-Type": "application/json"
}


# ----------------------- Assemble PLO files --------------------------
lon, lat = 148.16, -35.61


# 1) --------------- meta  --------------- 
meta = create_meta_section("My_Plot", notesME="")

# 2) --------------- config --------------- 
config = create_config_section()

# 3) --------------- timing --------------- 
timing = create_timing_section()

# 4) --------------- build --------------- 
build = create_build_section(lon, lat)

# 5) --------------- site --------------- 
site = create_site_section(lon, lat)

# 6) --------------- species --------------- 
species_forest = create_species_section(lon, lat)
species_ag = '<SpeciesAgricultureSet count="0" showOnlyInUse="false"/>'
    









# ----------------------- Plot simulation --------------------------

url = f"{BASE_URL_SIM}{ENDPOINT}"

# Parse PLO file
PLO_xml = etree.parse("data/E_globulus_2024.plo").getroot()


with open("data/E_globulus_2024.plo", 'rb') as file:
    file_data = file.read()

response = requests.post(url, files={'file': ('test.plo', file_data)}, headers={"Ocp-Apim-Subscription-Key": API_KEY},  timeout=30)
response_df = pd.read_csv(StringIO(response.text))
response_df.to_csv('data/plot_simulation_response.csv', index=False)


