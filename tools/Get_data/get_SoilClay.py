
import rioxarray as rio
import xarray as xr
import rioxarray as rxr
import numpy as np
import plotnine as p9

from pathlib import Path
from affine import Affine
from tools.cache_manager import get_existing_downloads


# Config
RES_factor = 10
soil_path = Path('data/Soil_landscape_AUS/ClayContent/000055684v002/data')

# --------------- Get valid coords ---------------
PLO_data_path = Path('N:/Data-Master/FullCAM/FullCAM_REST_API_GET_DATA_2025/data/processed/BB_PLO_OneKm')
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



# --------------- Load Soil Clay Data ---------------
clay_FULLCAM_ds = (
    xr.open_dataset('data/processed/soilbase_soilother_RES.nc')['data']
    .sel(band='clayFrac', drop=True)
)

soil_00_05 = (
    rio.open_rasterio(soil_path / '000-005cm/CLY_000_005_EV_N_P_AU_TRN_N_20210902.tif')
    .sel(band=1, drop=True)
)
soil_05_15 = (
    rio.open_rasterio(soil_path / '005-015cm/CLY_005_015_EV_N_P_AU_TRN_N_20210902.tif')
    .sel(band=1, drop=True)
)
soil_15_30 = (
    rio.open_rasterio(soil_path / '015-030cm/CLY_015_030_EV_N_P_AU_TRN_N_20210902.tif')
    .sel(band=1, drop=True)
)

soil_00_30 = (soil_00_05 + soil_05_15  + soil_15_30) / 3 / 100

soil_00_30.rio.write_crs("EPSG:4326", inplace=True)
soil_00_30.rio.write_transform(clay_FULLCAM_ds.rio.transform(), inplace=True)
soil_00_30.rio.to_raster(
    'data/Soil_landscape_AUS/ClayContent/clayFrac_00_30cm.tif',
    compress='LZW'
)



# ---------------------------- Plot comparison -------------------------------------
clay_FULLCAM_arr = clay_FULLCAM_ds.sel(x=res_coords_x, y=res_coords_y, method='nearest').compute()

soil_00_30 = (
    rxr.open_rasterio('data/Soil_landscape_AUS/ClayContent/clayFrac_00_30cm.tif')
    .sel(band=1, drop=True)
    .compute()
    .sel(x=res_coords_x, y=res_coords_y, method='nearest')
)

plt_data = (
    xr.concat([clay_FULLCAM_arr, soil_00_30], dim='source').assign_coords(source=['FullCAM', 'Downloaded'])
    .to_dataframe()
    .reset_index()
    .dropna()
    .round({'x':3, 'y':3})
    .pivot(index=['x', 'y'], columns='source', values='data')
    .reset_index()
    .dropna()
)

fig = (
    p9.ggplot(plt_data[::10])
    + p9.aes(x='FullCAM', y='Downloaded')
    + p9.geom_point(alpha=0.3, size=0.5)
    + p9.geom_abline(slope=1, intercept=0, color='red', linetype='dashed')
    + p9.labs(
        title='Soil Clay Fraction (0-30cm) Comparison',
        x='FullCAM Clay-Fraction',
        y='Jinzhu calculated Clay-Fraction'
    )
    + p9.theme_bw()
)


