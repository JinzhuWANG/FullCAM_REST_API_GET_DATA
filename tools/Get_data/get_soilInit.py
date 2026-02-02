
import os
import re
import pandas as pd
import xarray as xr
import plotnine as p9

from glob import glob
from tqdm.auto import tqdm

from tools.XML2Data import parse_init_data



'''
These soil init data comes from Brett's assembled PLO files.
Which were processed using FullCAMv2020 at 2020 at 1km resolution.
'''


# ---------------------------- Plot comparison -------------------------------------

# Load existing soil init data
soil_init = (
    xr.open_dataset("data/processed/BB_PLO_OneKm/soilInit_PLO_RES.nc")
    .isel(band=range(0,7))
    .sel(band=['rpmaCMInitF','humsCMInitF','inrtCMInitF','TSMDInitF'])
    .compute()
    .drop_vars('spatial_ref')
)


# Get downloaded carbon data CSV files; does not matter which species because SiteInfo is the same for all species
FullCAM_retrive_dir ='data/processed/Compare_API_and_Assemble_Data_Simulations/download_csv'
csv_files = [i for i in glob(f'{FullCAM_retrive_dir}/*.csv') if f'specId_8_specCat_Block' in i]

data_compare = pd.DataFrame()
for f in tqdm(csv_files):
    # Get Cache data
    #   The SiteInfo data for the FullCAM carbon df at lon/lat already downloaded
    lon, lat  = re.findall(r'df_(-?\d+\.\d+)_(-?\d+\.\d+)_specId_', os.path.basename(f))[0]
    with open(f'downloaded/siteInfo_{lon}_{lat}.xml', 'r') as file:
        FullCAM_soil = parse_init_data(file.read(), tsmd_year=2010)
        FullCAM_soil = pd.DataFrame({
            'Variable': list(FullCAM_soil.keys()),
            'SoilInit': [FullCAM_soil[k].data.item() for k in FullCAM_soil.keys()]
        })
    # Get SoilInit from Brett's assembled PLO data at the lon/lat
    soil_init_pt = (
        soil_init
        .sel(x=float(lon), y=float(lat), method='nearest')
        .to_dataframe()
        .reset_index()
        .rename(columns={'band':'Variable', 'data':'SoilInit'})
    )
    # Merge FullCAM and assembled PLO SoilInit data, then append to main dataframe
    soil_init_merged = pd.merge(
        FullCAM_soil,
        soil_init_pt,
        on='Variable',
        suffixes=('_FullCAM', '_AssembledPLO')
    )
    soil_init_merged[['x', 'y']] = float(lon), float(lat)
    data_compare = pd.concat([data_compare, soil_init_merged], ignore_index=True)
    
    
# Plot comparison
p9.options.figure_size = (6, 6)
p9.options.dpi = 150

fig = (
    p9.ggplot(data_compare) +
    p9.aes(x='SoilInit_FullCAM', y='SoilInit_AssembledPLO') +
    p9.geom_point(alpha=0.5) +
    p9.geom_abline(slope=1, intercept=0, linetype='dashed', color='red') +
    p9.theme_bw() +
    p9.facet_wrap('~Variable', scales='free', ncol=2) +
    p9.labs(
        title='Soil Initial Fraction Comparison (FullCAM v2020 vs v2024)',
        x='Soil Initial Fraction v2020',
        y='Soil Initial Fraction v2024'
    )
)

fig.save('data/processed/Compare_API_and_Assemble_Data_Simulations/Data_compare_SiteInfo_soilInit.svg', dpi=150)

