import numpy as np
import pandas as pd
import xarray as xr
import rioxarray as rxr

import plotnine as p9



################################################################
#               Compare FullCAM  Cache v.s API                 #
################################################################

# Get FullCAM API results
ds_api = (
    xr.open_dataset("data/processed/20251212_2_API_site_API_species/carbonstock_RES_10.nc")['data']
    .sel(VARIABLE='TREE_C_HA', drop=True)
    .compute()
)
ds_api_vals = ds_api.stack(z=('y', 'x')).dropna(dim='z')


# Get valid coords from API dataset
y_coords = xr.DataArray(ds_api_vals['y'].values, dims='cell')
x_coords = xr.DataArray(ds_api_vals['x'].values, dims='cell')



# Get FullCAM Cache results
ds_cache = (
    rxr.open_rasterio("data/processed/20251216_RES3_Cache_site_Cache_species/carbonstock_TREE_C_HA_RES_3_multiband.tif", masked=True)
    .compute()
)

ds_cache_vals = ds_cache.sel(x=x_coords, y=y_coords, method='nearest')


# Combine dataset to dataframe for comparison
combined_df = pd.DataFrame({
    'FullCAM_Cache_TREE_C_HA': ds_cache_vals.values.flatten(),
    'FullCAM_API_TREE_C_HA': ds_api_vals.values.flatten(),
}).dropna()

combined_df['ratio'] = combined_df['FullCAM_Cache_TREE_C_HA'] / combined_df['FullCAM_API_TREE_C_HA']



# Plot comparison
fig = (
    p9.ggplot(combined_df[::10])
    + p9.geom_point(
        p9.aes(x='FullCAM_Cache_TREE_C_HA', y='FullCAM_API_TREE_C_HA'),
        alpha=0.05,
    )
    + p9.geom_abline(slope=1, intercept=0, color='red', linetype='dashed')
    + p9.labs(
        title='FullCAM Cache vs FullCAM API: TREE_C_HA',
        x='FullCAM Cache (TREE_C_HA)',
        y='FullCAM API (TREE_C_HA)',
        fill='Count'
    )
)






