
import numpy as np
import pandas as pd
import xarray as xr
import rioxarray as rio
import plotnine as p9

from pathlib import Path
from tools.cache_manager import get_existing_downloads

# ===================== Configuration =====================

# Resolution factor for downsampling (10 = 0.1° grid spacing)
RES_factor = 10
PLO_data_path = Path('N:/Data-Master/FullCAM/FullCAM_REST_API_GET_DATA_2025/data/processed/BB_PLO_OneKm')
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads()


# Get the RES coords
Aus_xr = rio.open_rasterio("data/lumap.tif").sel(band=1, drop=True) >= -1 # >=-1 means all Australia continent
lon_lat = Aus_xr.to_dataframe(name='mask').reset_index()[['y', 'x', 'mask']].round({'x':2, 'y':2})
lon_lat['cell_idx'] = range(len(lon_lat))

Aus_cell = xr.DataArray(np.arange(Aus_xr.size).reshape(Aus_xr.shape), coords=Aus_xr.coords, dims=Aus_xr.dims)
Aus_cell_RES = Aus_cell.coarsen(x=RES_factor, y=RES_factor, boundary='trim').max()
Aus_cell_RES_df = Aus_cell_RES.to_dataframe(name='cell_idx').reset_index()['cell_idx']

RES_df = lon_lat.query('mask == True').loc[lon_lat['cell_idx'].isin(Aus_cell_RES_df)].reset_index(drop=True)
RES_coords = RES_df.set_index(['x', 'y']).index.tolist()

# Get valid RES coords
res_coords = set(existing_siteinfo).intersection(set(RES_coords))
res_coords_x = xr.DataArray([coord[0] for coord in res_coords], dims=['cell'])
res_coords_y = xr.DataArray([coord[1] for coord in res_coords], dims=['cell'])


# ===================== Helper Functions =====================

def compare_variable(
    dataset_restfull: xr.Dataset,
    dataset_plo: xr.Dataset,
    variable_name: str,
    coords_x: xr.DataArray,
    coords_y: xr.DataArray,
    subsample: int = 100,
    alpha: float = 0.05,
    point_size: float = 0.05
):

    # Extract variable data
    var_restfull = dataset_restfull[variable_name].sel(x=coords_x, y=coords_y, drop=True)
    var_plo = dataset_plo[variable_name].sel(x=coords_x, y=coords_y, drop=True)

    # Merge and prepare data
    plot_data = xr.merge([
        var_restfull.rename('restfull'),
        var_plo.rename('PLO')
    ], join='inner').to_dataframe().reset_index().dropna()

    # Create base plot
    fig = (
        p9.ggplot() +
        p9.geom_point(
            p9.aes(
                x=plot_data['restfull'][::subsample],
                y=plot_data['PLO'][::subsample]
            ),
            alpha=alpha,
            size=point_size
        ) +
        p9.geom_abline(slope=1, intercept=0, color='red', linetype='dashed') +
        p9.theme_bw()
    )

    return fig


# ---------------------- Compare SiteInfo data ------------------------
siteInfo_restfull = xr.open_dataset('data/processed/siteinfo_RES.nc').compute()
siteInfo_PLO = xr.open_dataset(PLO_data_path / 'siteinfo_PLO_RES.nc').compute()


# avgAirTemp
fig_avgAirTemp = compare_variable(
    siteInfo_restfull,
    siteInfo_PLO,
    'avgAirTemp',
    res_coords_x,
    res_coords_y
) + p9.labs(
    title='Comparison of avgAirTemp: REST-Full vs PLO',
    x='REST-Full avgAirTemp (°C)',
    y='PLO avgAirTemp (°C)'
)

# openPanEvap
fig_openPanEvap = compare_variable(
    siteInfo_restfull,
    siteInfo_PLO,
    'openPanEvap',
    res_coords_x,
    res_coords_y
) + p9.labs(
    title='Comparison of openPanEvap: REST-Full vs PLO',
    x='REST-Full openPanEvap (mm)',
    y='PLO openPanEvap (mm)'
)

# rainfall
fig_rainfall = compare_variable(
    siteInfo_restfull,
    siteInfo_PLO,
    'rainfall',
    res_coords_x,
    res_coords_y
) + p9.labs(
    title='Comparison of rainfall: REST-Full vs PLO',
    x='REST-Full rainfall (mm)',
    y='PLO rainfall (mm)'
)

# forestProdIx
fig_forestProdIx = compare_variable(
    siteInfo_restfull,
    siteInfo_PLO,
    'forestProdIx',
    res_coords_x,
    res_coords_y,
    subsample=10
) + p9.labs(
    title='Comparison of forestProdIx: REST-Full vs PLO',
    x='REST-Full forestProdIx',
    y='PLO forestProdIx'
)

# maxAbgMF
fig_maxAbgMF = compare_variable(
    siteInfo_restfull,
    siteInfo_PLO,
    'maxAbgMF',
    res_coords_x,
    res_coords_y,
    subsample=1
) + p9.labs(
    title='Comparison of maxAbgMF: REST-Full vs PLO',
    x='REST-Full maxAbgMF',
    y='PLO maxAbgMF',
)

# fpiAvgLT
fig_fpiAvgLT = compare_variable(
    siteInfo_restfull,
    siteInfo_PLO,
    'fpiAvgLT',
    res_coords_x,
    res_coords_y,
    subsample=1
) + p9.labs(
    title='Comparison of fpiAvgLT: REST-Full vs PLO',
    x='REST-Full fpiAvgLT',
    y='PLO fpiAvgLT',
)



# ---------------------- Compare SoilBase data ------------------------
soilBase_restfull = xr.open_dataset('data/processed/soilbase_soilother_RES.nc')['data'].compute()
soilBase_PLO = xr.open_dataset(PLO_data_path / 'soilbase_PLO_soilother_RES.nc')['data'].compute()

# bulkDensity
soilBase_restfull.sel(band='bulkDensity').plot()
soilBase_PLO.sel(band='bulkDensity').plot()

# maxASW
soilBase_restfull.sel(band='maxASW').plot()
soilBase_PLO.sel(band='maxASW').plot()

# clayFrac
plt_data_clayFrac = xr.merge([
    soilBase_restfull.sel(band='clayFrac').rename('restfull'),
    soilBase_PLO.sel(band='clayFrac').rename('PLO')
], join='inner').to_dataframe().reset_index().dropna()


import matplotlib.pyplot as plt
soilBase_restfull.sel(band='clayFrac').plot()
plt.show()

soilBase_PLO.sel(band='clayFrac').plot()
plt.show()


fig_clayFrac = (
    p9.ggplot() +
    p9.geom_point(
        p9.aes(
            x=plt_data_clayFrac['restfull'],
            y=plt_data_clayFrac['PLO']
        ),
        alpha=0.1,
        size=0.05
    ) +
    p9.geom_abline(slope=1, intercept=0, color='red', linetype='dashed') +
    p9.theme_bw() +
    p9.labs(
        title='Comparison of clayFrac: REST-Full vs PLO',
        x='REST-Full clayFrac',
        y='PLO clayFrac'
    )
)


# ---------------------- Compare SoilInit data ------------------------
soilOther_restfull = xr.open_dataset('data/processed/soilInit_RES.nc')['data'].compute()
soilOther_PLO = xr.open_dataset(PLO_data_path / 'soilInit_PLO_RES.nc')['data'].compute()

# biofCMInitF, biosCMInitF, dpmaCMInitF are empty in both datasets
soilOther_restfull.sel(band='biofCMInitF').plot()
soilOther_PLO.sel(band='biofCMInitF').plot()

soilOther_restfull.sel(band='biosCMInitF').plot()
soilOther_PLO.sel(band='biosCMInitF').plot()

soilOther_restfull.sel(band='dpmaCMInitF').plot()
soilOther_PLO.sel(band='dpmaCMInitF').plot()

# rpmaCMInitF
plt_data_rpmaCMInitF = xr.merge([
    soilOther_restfull.sel(band='rpmaCMInitF').rename('restfull'),
    soilOther_PLO.sel(band='rpmaCMInitF').rename('PLO')
], join='inner').to_dataframe().reset_index().dropna()

fig_rpmaCMInitF = (
    p9.ggplot() +
    p9.geom_point(
        p9.aes(
            x=plt_data_rpmaCMInitF['restfull'],
            y=plt_data_rpmaCMInitF['PLO']
        ),
        alpha=0.1,
        size=0.05
    ) +
    p9.geom_abline(slope=1, intercept=0, color='red', linetype='dashed') +
    p9.theme_bw() +
    p9.labs(
        title='Comparison of rpmaCMInitF: REST-Full vs PLO',
        x='REST-Full rpmaCMInitF',
        y='PLO rpmaCMInitF'
    )
)

# humsCMInitF
plt_data_humsCMInitF = xr.merge([
    soilOther_restfull.sel(band='humsCMInitF').rename('restfull'),
    soilOther_PLO.sel(band='humsCMInitF').rename('PLO')
], join='inner').to_dataframe().reset_index().dropna()

fig_humsCMInitF = (
    p9.ggplot() +
    p9.geom_point(
        p9.aes(
            x=plt_data_humsCMInitF['restfull'],
            y=plt_data_humsCMInitF['PLO']
        ),
        alpha=0.1,
        size=0.05
    ) +
    p9.geom_abline(slope=1, intercept=0, color='red', linetype='dashed') +
    p9.theme_bw() +
    p9.labs(
        title='Comparison of humsCMInitF: REST-Full vs PLO',
        x='REST-Full humsCMInitF',
        y='PLO humsCMInitF'
    )
)

# inrtCMInitF
plt_data_inrtCMInitF = xr.merge([
    soilOther_restfull.sel(band='inrtCMInitF').rename('restfull'),
    soilOther_PLO.sel(band='inrtCMInitF').rename('PLO')
], join='inner').to_dataframe().reset_index().dropna()

fig_inrtCMInitF = (
    p9.ggplot() +
    p9.geom_point(
        p9.aes(
            x=plt_data_inrtCMInitF['restfull'],
            y=plt_data_inrtCMInitF['PLO']
        ),
        alpha=0.1,
        size=0.05
    ) +
    p9.geom_abline(slope=1, intercept=0, color='red', linetype='dashed') +
    p9.theme_bw() +
    p9.labs(
        title='Comparison of inrtCMInitF: REST-Full vs PLO',
        x='REST-Full inrtCMInitF',
        y='PLO inrtCMInitF'
    )
)

# TSMDInitF
plt_data_TSMDInitF = xr.merge([
    soilOther_restfull.sel(band='TSMDInitF').rename('restfull'),
    soilOther_PLO.sel(band='TSMDInitF').rename('PLO')
], join='inner').to_dataframe().reset_index().dropna()

fig_TSMDInitF = (
    p9.ggplot() +
    p9.geom_point(
        p9.aes(
            x=plt_data_TSMDInitF['restfull'],
            y=plt_data_TSMDInitF['PLO']
        ),
        alpha=0.1,
        size=0.05
    ) +
    p9.geom_abline(slope=1, intercept=0, color='red', linetype='dashed') +
    p9.theme_bw() +
    p9.labs(
        title='Comparison of TSMDInitF: REST-Full vs PLO',
        x='REST-Full TSMDInitF',
        y='PLO TSMDInitF'
    )
)


# TSMDInitF 
plt_data_TSMDInitF = xr.merge([
    soilOther_restfull.sel(band='TSMDInitF').rename('restfull'),
    soilOther_PLO.sel(band='TSMDInitF').rename('PLO')
], join='inner').to_dataframe().reset_index().dropna()

fig_TSMDInitF = (
    p9.ggplot() +
    p9.geom_point(
        p9.aes(
            x=plt_data_TSMDInitF['restfull'],
            y=plt_data_TSMDInitF['PLO']
        ),
        alpha=0.1,
        size=0.05
    ) +
    p9.geom_abline(slope=1, intercept=0, color='red', linetype='dashed') +
    p9.theme_bw() +
    p9.labs(
        title='Comparison of TSMDInitF: REST-Full vs PLO',
        x='REST-Full TSMDInitF',
        y='PLO TSMDInitF'
    )
)