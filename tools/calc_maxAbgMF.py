import io
import zipfile
import numpy as np
import xarray as xr
import rioxarray as rio
import plotnine as p9

from tools.cache_manager import get_existing_downloads



# Config
RES_factor = 10

# Get resfactored coords
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads()

Aus_xr = rio.open_rasterio("data/lumap.tif").sel(band=1, drop=True) >= -1 # >=-1 means all Australia continent
lon_lat = Aus_xr.to_dataframe(name='mask').reset_index()[['y', 'x', 'mask']].round({'x':2, 'y':2})
lon_lat['cell_idx'] = range(len(lon_lat))

Aus_cell = xr.DataArray(np.arange(Aus_xr.size).reshape(Aus_xr.shape), coords=Aus_xr.coords, dims=Aus_xr.dims)
Aus_cell_RES = Aus_cell.coarsen(x=RES_factor, y=RES_factor, boundary='trim').max()
Aus_cell_RES_df = Aus_cell_RES.to_dataframe(name='cell_idx').reset_index()['cell_idx']

RES_df = lon_lat.query('mask == True').loc[lon_lat['cell_idx'].isin(Aus_cell_RES_df)].reset_index(drop=True)
RES_coords = RES_df.set_index(['x', 'y']).index.tolist()

res_coords = set(existing_siteinfo).intersection(set(RES_coords))
res_coords_x = xr.DataArray([coord[0] for coord in res_coords], dims=['cell'])
res_coords_y = xr.DataArray([coord[1] for coord in res_coords], dims=['cell'])



# Get data
with zipfile.ZipFile("data/maxAbgMF/Site potential and FPI version 2_0/New_M_2019.zip", 'r') as zip_ref:
    maxAbgMF_data = xr.open_dataarray(
        io.BytesIO(zip_ref.read('New_M_2019.tif')), 
        engine='rasterio'
    ).sel(band=1, drop=True)


# Check if maxAbgMF_data is the same as we downloaded before
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
    + p9.geom_point(alpha=0.05, size=0.5)
    + p9.geom_abline(slope=1, intercept=0, linetype='dashed', color='red')
    + p9.labs(
        title='Forest Productivity Index (FPI) Comparison: FullCAM vs SoilLandscape',
        x='FPI from FullCAM SiteInfo',
        y='FPI from SoilLandscape'
    )
)





