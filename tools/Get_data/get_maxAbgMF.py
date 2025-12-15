import io
import zipfile
import numpy as np
import xarray as xr
import rioxarray as rio
import plotnine as p9

from tools import get_downloading_coords
from tools.helpers.cache_manager import get_existing_downloads




# Get resfactored coords for downloading
SPECIES_ID = 8  # Eucalyptus globulus
scrap_coords = get_downloading_coords(resfactor=10).set_index(['x', 'y']).index.tolist()
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads(SPECIES_ID)

res_coords = set(existing_siteinfo).intersection(set(scrap_coords))
res_coords_x = xr.DataArray([coord[0] for coord in res_coords], dims=['cell'])
res_coords_y = xr.DataArray([coord[1] for coord in res_coords], dims=['cell'])



# Get data
with zipfile.ZipFile("data/maxAbgMF/Site potential and FPI version 2_0/New_M_2019.zip", 'r') as zip_ref:
    maxAbgMF_data = xr.open_dataarray(
        io.BytesIO(zip_ref.read('New_M_2019.tif')), 
        engine='rasterio'
    ).sel(band=1, drop=True)

maxAbgMF_data.name = 'data'
maxAbgMF_data.to_netcdf('data/maxAbgMF/maxAbgMF.nc', encoding={'data': {'zlib': True, 'complevel': 5}})




# -------------------------------- Plot comparison -------------------------------- 
maxAbgMF_restfull = (
    xr.open_dataset('data/processed/siteinfo_RES.nc')['maxAbgMF']
    .compute()
    .sel(x=res_coords_x, y=res_coords_y)
)


maxAbgMF_downloaded = maxAbgMF_data.sel(
    x=res_coords_x, 
    y=res_coords_y, 
    method='nearest'
).compute()


plot_data = (
    xr.concat([maxAbgMF_restfull, maxAbgMF_downloaded], dim='source', join ='inner')
    .assign_coords(source=['FullCAM', 'Downloaded'])
    .to_dataframe()
    .reset_index()
    .round({'x':3, 'y':3})
    .pivot(index=['x', 'y'], columns=['source'], values='maxAbgMF')
    .reset_index()
    .dropna()
)

fig = (
    p9.ggplot()
    + p9.aes(x=plot_data[::100]['FullCAM'], y=plot_data[::100]['Downloaded'])
    + p9.geom_point(alpha=0.3, size=0.5)
    + p9.geom_abline(slope=1, intercept=0, linetype='dashed', color='red')
    + p9.theme_bw()
    + p9.labs(
        title='Forest Productivity Index (FPI) Comparison: FullCAM vs SoilLandscape',
        x='FPI from FullCAM',
        y='FPI from Downloaded'
    )
)





