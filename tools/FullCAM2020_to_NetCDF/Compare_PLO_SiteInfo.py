
import numpy as np
import pandas as pd
import xarray as xr
import rioxarray as rio
import plotnine as p9

from pathlib import Path
from tools import get_downloading_coords
from tools.helpers.cache_manager import get_existing_downloads

# ===================== Configuration =====================

# Resolution factor for downsampling (10 = 0.1° grid spacing)
RES_factor = 10
PLO_data_path = Path('N:/Data-Master/FullCAM/FullCAM_REST_API_GET_DATA_2025/data/processed/BB_PLO_OneKm')
existing_siteinfo, existing_species, existing_dfs = get_existing_downloads()

# Get resfactored coords for downloading
scrap_coords = get_downloading_coords(resfactor=RES_factor).set_index(['x', 'y']).index.tolist()
res_coords = set(existing_siteinfo).intersection(set(scrap_coords))
res_coords_x = xr.DataArray([coord[0] for coord in res_coords], dims=['cell']).astype('float32')
res_coords_y = xr.DataArray([coord[1] for coord in res_coords], dims=['cell']).astype('float32')

# Save the PLO_RES data if not already saved
if not (PLO_data_path / f'siteinfo_PLO_RES_{RES_factor}.nc').exists():
    siteinfo_PLO_Full = xr.open_dataset(PLO_data_path / 'siteinfo_PLO_RES.nc').compute()
    siteinfo_PLO_RESed = siteinfo_PLO_Full.sel(x=res_coords_x, y=res_coords_y)
    siteinfo_PLO_RESed.to_netcdf(PLO_data_path / f'siteinfo_PLO_RES_{RES_factor}.nc')


# ===================== Helper Functions =====================

def compare_variable(
    dataset_restfull: xr.Dataset,
    dataset_plo: xr.Dataset,
    variable_name: str,
    subsample: int = 100,
    alpha: float = 0.05,
    point_size: float = 0.05
):

    # Extract variable data
    var_restfull = dataset_restfull[variable_name]
    var_plo = dataset_plo[variable_name]

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
siteInfo_restfull = xr.open_dataset('data/processed/siteinfo_RES.nc').compute().sel(x=res_coords_x, y=res_coords_y, drop=True)
siteInfo_PLO = xr.open_dataset(PLO_data_path / f'siteinfo_PLO_RES_{RES_factor}.nc').compute()

# avgAirTemp
fig_avgAirTemp = compare_variable(
    siteInfo_restfull,
    siteInfo_PLO,
    'avgAirTemp',
) + p9.labs(
    title='Comparison of avgAirTemp',
    x='FullCAM Data-API (°C)',
    y='Brett`s archive (°C)'
)

# openPanEvap
fig_openPanEvap = compare_variable(
    siteInfo_restfull,
    siteInfo_PLO,
    'openPanEvap',
) + p9.labs(
    title='Comparison of openPanEvap',
    x='FullCAM Data-api (mm)',
    y='Brett`s archive (mm)'
)

# rainfall
fig_rainfall = compare_variable(
    siteInfo_restfull,
    siteInfo_PLO,
    'rainfall',
) + p9.labs(
    title='Comparison of rainfall',
    x='FullCAM Data-api (mm)',
    y='Brett`s archive (mm)'
)

# forestProdIx
fig_forestProdIx = compare_variable(
    siteInfo_restfull,
    siteInfo_PLO,
    'forestProdIx',
    subsample=10
) + p9.labs(
    title='Comparison of forestProdIx',
    x='FullCAM Data-api',
    y='Brett`s archive'
)

# maxAbgMF
fig_maxAbgMF = compare_variable(
    siteInfo_restfull,
    siteInfo_PLO,
    'maxAbgMF',
    subsample=1
) + p9.labs(
    title='Comparison of maxAbgMF',
    x='FullCAM Data-api ',
    y='Brett`s archive'
)

# fpiAvgLT
fig_fpiAvgLT = compare_variable(
    siteInfo_restfull,
    siteInfo_PLO,
    'fpiAvgLT',
    subsample=1
) + p9.labs(
    title='Comparison of fpiAvgLT',
    x='FullCAM Data-api',
    y='Brett`s archive '
)



# ---------------------- Compare SoilBase data ------------------------
soilBase_restfull = xr.open_dataset('data/processed/soilbase_soilother_RES.nc')['data'].compute()
soilBase_PLO = xr.open_dataset(PLO_data_path / 'soilbase_PLO_soilother_RES.nc')['data'].compute()

soilClary_landscape_grid = xr.open_dataarray('data/Soil_landscape_AUS/ClayContent/clayFrac_00_30cm_RES.tif').compute()
soilClary_landscape_grid['x'] = soilClary_landscape_grid['x'].astype('float32')
soilClary_landscape_grid['y'] = soilClary_landscape_grid['y'].astype('float32')

# bulkDensity
soilBase_restfull.sel(band='bulkDensity').plot()
soilBase_PLO.sel(band='bulkDensity').plot()

# maxASW
soilBase_restfull.sel(band='maxASW').plot()
soilBase_PLO.sel(band='maxASW').plot()

# clayFrac (FullCAM Data-api vs Archived PLO)
plt_data_clayFrac = xr.merge([
    soilBase_restfull.sel(band='clayFrac').rename('restfull'),
    soilBase_PLO.sel(band='clayFrac').rename('PLO')
], join='inner').to_dataframe().reset_index().dropna()


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
        title='Comparison of clayFrac',
        x='FullCAM Data-api',
        y='Brett`s archive'
    )
)

# clayFrac (FullCAM Data-api vs Soil Landscape)
plt_data_clayFrac_SL = xr.merge([
    soilBase_restfull.sel(band='clayFrac').rename('restfull'),
    soilClary_landscape_grid.rename('SoilLandscape')
], join='inner').to_dataframe().reset_index().dropna()

fig_clayFrac_SL = (
    p9.ggplot() +
    p9.geom_point(
        p9.aes(
            x=plt_data_clayFrac_SL['restfull'],
            y=plt_data_clayFrac_SL['SoilLandscape']
        ),
        alpha=0.1,
        size=0.05
    ) +
    p9.geom_abline(slope=1, intercept=0, color='red', linetype='dashed') +
    p9.theme_bw() +
    p9.labs(
        title='Comparison of clayFrac: REST-Full vs Soil Landscape',
        x='REST-Full clayFrac',
        y='Soil Landscape clayFrac'
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
        title='Comparison of rpmaCMInitF',
        x='FullCAM rpmaCMInitF',
        y='Brett`s archive'
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
        title='Comparison of humsCMInitF',
        x='FullCAM humsCMInitF',
        y='Brett`s archive'
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
        title='Comparison of inrtCMInitF',
        x='FullCAM inrtCMInitF',
        y='Brett`s archive'
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
        title='Comparison of TSMDInitF',
        x='FullCAM TSMDInitF',
        y='Brett`s archive'
    )
)

