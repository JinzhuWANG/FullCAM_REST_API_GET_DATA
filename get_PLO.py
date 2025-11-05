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



# 1) meta
meta = create_meta_section("My_Plot", notesME="")

# 2) config
config = create_config_section()

# 3) timing
timing = create_timing_section()

# 4) build
build = create_build_section(148.16, -35.61)

# 5) site
site_root = etree.parse('data/siteinfo_response.xml').getroot()

site_avgAirTemp = etree.tostring(site_root.xpath('.//*[@tInTS="avgAirTemp"]')[0]).decode('utf-8')
site_openPanEvap = etree.tostring(site_root.xpath('.//*[@tInTS="openPanEvap"]')[0]).decode('utf-8')
site_rainfall = etree.tostring(site_root.xpath('.//*[@tInTS="rainfall"]')[0]).decode('utf-8')
site_forestProdIx = etree.tostring(site_root.xpath('.//*[@tInTS="forestProdIx"]')[0]).decode('utf-8')

site_fpiAvgLT = [float(i) for i in site_root.xpath('.//*[@tInTS="forestProdIx"]//rawTS')[0].text.split(',')]
site_fpiAvgLT = sum(site_fpiAvgLT[:48]) / 48    # Should be calculated from the first 48 elements (1970-2017)

with open('data/dataholder_site.xml', 'rb') as f_holder:
    element_holder = f_holder.read().decode('utf-8').replace('\n', '')
    
site_content = element_holder + ''.join([
        site_avgAirTemp,
        site_openPanEvap,
        site_rainfall,
        site_forestProdIx
    ])

siteinfo = create_site_section(21, site_content)
    
with open('PLO_files/dataholder_forest.xml', 'w') as f_plo:
    f_plo.write(siteinfo)
    

    









# ----------------------- Plot simulation --------------------------

url = f"{BASE_URL_SIM}{ENDPOINT}"

with open("data/E_globulus_2024.plo", 'rb') as file:
    file_data = file.read()

response = requests.post(url, files={'file': ('test.plo', file_data)}, headers={"Ocp-Apim-Subscription-Key": API_KEY},  timeout=30)
response_df = pd.read_csv(StringIO(response.text))
response_df.to_csv('data/plot_simulation_response.csv', index=False)


