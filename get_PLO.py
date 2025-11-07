import os
import requests
import pandas as pd

from io import StringIO
from tools.plo_section_functions import assemble_plo_sections



# Configuration
'''
If having issues with API access, try running below snippet to temporarily adding key to current session:

import os
os.environ["FULLCAM_API_KEY"] = "your_api_key_here"

'''
API_KEY = os.getenv("FULLCAM_API_KEY")
if not API_KEY: raise ValueError("`FULLCAM_API_KEY`environment variable not set!")


BASE_URL_SIM = "https://api.climatechange.gov.au/climate/carbon-accounting/2024/plot/v1"
ENDPOINT = "/2024/fullcam-simulator/run-plotsimulation"
HEADERS = {
    "Host": "api.dcceew.gov.au",
    "Ocp-Apim-Subscription-Key": API_KEY,
    "Content-Type": "application/json"
}




# ----------------------- Plot simulation --------------------------
lon, lat = 146.03, -37.75
url = f"{BASE_URL_SIM}{ENDPOINT}"
raw_str = assemble_plo_sections(lon, lat, 2010)

response = requests.post(url, files={'file': ('test.plo', raw_str)}, headers={"Ocp-Apim-Subscription-Key": API_KEY},  timeout=30)
response_df = pd.read_csv(StringIO(response.text))
response_df.to_csv('data/plot_simulation_response.csv', index=False)


