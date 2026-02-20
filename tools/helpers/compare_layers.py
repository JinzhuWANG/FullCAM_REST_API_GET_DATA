import os
import re
import numpy as np
import pandas as pd
import xarray as xr
import rioxarray as rxr
import plotnine as p9
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm

from pathlib import Path
from tqdm.auto import tqdm
from glob import glob
from functools import partial

from tools import get_downloading_coords, get_plot_simulation
from tools.parameter import SPECIES_GEOMETRY


################################################################
#                    Global setup (run once)                   #
################################################################

RES_factor = 1
scrap_coords = get_downloading_coords(resfactor=3, include_region='LUTO')
LUTO_lumap   = rxr.open_rasterio('data/lumap.tif', masked=True)

# 1 000 random sample coords used for violin/scatter comparisons
compare_coords   = scrap_coords.sample(n=1000, random_state=42).set_index(['x', 'y']).index.tolist()
compare_coords_x = xr.DataArray([c[0] for c in compare_coords], dims='points')
compare_coords_y = xr.DataArray([c[1] for c in compare_coords], dims='points')

v2020_path       = Path('N:/Data-Master/FullCAM/Output_layers')
comparison_dir   = Path('data/processed/Compare_API_and_Assemble_Data_Simulations')
download_csv_dir = comparison_dir / 'download_csv'

get_plot_simulation = partial(get_plot_simulation, download_csv_dir=download_csv_dir)

compare_year     = 2100
v2020_extra_case = 'ld'     # 'ld' or 'hd' — applies to Belt categories
CO2_FACTOR       = 44 / 12  # tC/ha → tCO2/ha

# (specId, specCat) → (v2020_name, v2020_cat)
V2020_MAP = {
    (7,  'BeltH'):   ('ep',    f'belt_{v2020_extra_case}'),
    (7,  'BlockES'): ('ep',    'block'),
    (7,  'Water'):   ('ep',    'rip'),
    (8,  'Belt'):    ('eglob', 'lr'),
    (8,  'Block'):   ('eglob', 'lr'),
    (23, 'BeltHW'):  ('mal',   f'belt_{v2020_extra_case}'),
    (23, 'BlockES'): ('mal',   'block'),
}

MAP_COMPONENTS = [
    ('TREE_C_HA',   'Trees'),
    ('DEBRIS_C_HA', 'Debris'),
    ('SOIL_C_HA',   'Soil'),
]


################################################################
#                    Comparison function                       #
################################################################

def run_species_comparison(spec_id, spec_cat):
    """Run all v2020-vs-v2024 comparisons for one (specId, specCat) pair.

    Produces:
      - fig1: API vs Cache scatter (only if CSV downloads exist)
      - fig2: Cache vs v2020 scatter (only if CSV downloads exist)
      - ratio_layer_*.tif: per-variable v2024/v2020 ratio rasters
      - fig3: v2024 component violin/box
      - componet_layer_*.tif: per-component fraction rasters
      - fig6: 3x3 spatial CO2 map (v2020 | v2024 | Difference)
    """
    if (spec_id, spec_cat) not in V2020_MAP:
        print(f"Skipping specId={spec_id}, specCat={spec_cat} — no v2020 mapping.")
        return

    v2020_name, v2020_cat = V2020_MAP[(spec_id, spec_cat)]
    v2020_debris_layer = v2020_path / f'{v2020_name}_{v2020_cat}_c_debris.tif'
    v2020_tree_layer   = v2020_path / f'{v2020_name}_{v2020_cat}_c_trees.tif'
    v2020_soil_layer   = v2020_path / f'{v2020_name}_{v2020_cat}_c_soil.tif'

    print(f"\n{'='*60}")
    print(f"specId={spec_id}  specCat={spec_cat}  →  v2020: {v2020_name}_{v2020_cat}")
    print(f"{'='*60}")

    # ── Load v2024 cache ──────────────────────────────────────────────
    cache_path = f"data/processed/Output_GeoTIFFs/carbonstock_RES_{RES_factor}_specId_{spec_id}_specCat_{spec_cat}.nc"
    if not Path(cache_path).exists():
        print(f"  Cache not found: {cache_path} — skipping.")
        return
    ds_cache = (
        xr.open_dataset(cache_path, chunks={})['data']
        .sel(YEAR=compare_year, drop=True)
        .compute()
    )

    # ── Load v2020 layers ─────────────────────────────────────────────
    if not all(p.exists() for p in [v2020_debris_layer, v2020_tree_layer, v2020_soil_layer]):
        print(f"  v2020 layer(s) missing for {v2020_name}_{v2020_cat} — skipping.")
        return

    Debries_C = rxr.open_rasterio(v2020_debris_layer, masked=True, chunks={})
    Trees_C   = rxr.open_rasterio(v2020_tree_layer,   masked=True, chunks={})
    Soil_C    = rxr.open_rasterio(v2020_soil_layer,   masked=True, chunks={})

    Debries_C_sel = Debries_C.sel(band=91, drop=True).compute()  # band 91 = year 2100
    Trees_C_sel   = Trees_C.sel(band=91, drop=True).compute()
    Soil_C_sel    = Soil_C.sel(band=91, drop=True).compute()

    ds_v2020 = xr.DataArray(
        data=np.stack([Debries_C_sel.data, Trees_C_sel.data, Soil_C_sel.data], axis=0),
        dims=['VARIABLE', 'y', 'x'],
        coords={
            'VARIABLE': ['DEBRIS_C_HA', 'TREE_C_HA', 'SOIL_C_HA'],
            'y': Trees_C_sel.y,
            'x': Soil_C_sel.x,
        },
    )

    # ── API vs Cache vs v2020 scatter (fig1, fig2) ────────────────────
    csv_files = [
        f for f in glob(f'{download_csv_dir}/*.csv')
        if f'specId_{spec_id}_specCat_{spec_cat}' in f
    ]
    df_comparison = pd.DataFrame()
    for f in tqdm(csv_files, desc='Reading CSVs', leave=False):
        df_api = pd.read_csv(f)[['Year', 'C mass of plants  (tC/ha)', 'C mass of debris  (tC/ha)', 'C mass of soil  (tC/ha)']]
        df_api = df_api.rename(columns={
            'C mass of plants  (tC/ha)': 'TREE_C_HA',
            'C mass of debris  (tC/ha)': 'DEBRIS_C_HA',
            'C mass of soil  (tC/ha)':   'SOIL_C_HA',
        })
        df_api = df_api.query(f'Year == {compare_year}').melt(
            id_vars=['Year'], var_name='VARIABLE', value_name='data_api'
        )
        lon, lat = re.findall(r'df_(-?\d+\.\d+)_(-?\d+\.\d+)_specId_', os.path.basename(f))[0]
        lon, lat = float(lon), float(lat)
        df_cache_pt = (
            ds_cache.sel(x=lon, y=lat, method='nearest')
            .to_dataframe().reset_index()
            .rename(columns={'YEAR': 'Year', 'data': 'data_cache'})[['VARIABLE', 'data_cache']]
        )
        df_v2020_pt = (
            ds_v2020.sel(x=lon, y=lat, method='nearest')
            .to_dataframe('data_v2020').reset_index()[['VARIABLE', 'data_v2020']]
        )
        df_combine = df_api.merge(df_cache_pt, on='VARIABLE').merge(df_v2020_pt, on='VARIABLE')
        df_combine[['lon', 'lat']] = lon, lat
        df_comparison = pd.concat([df_comparison, df_combine], ignore_index=True)

    if not df_comparison.empty:
        p9.options.figure_size = (10, 6)
        p9.options.dpi = 100

        fig1 = (
            p9.ggplot(df_comparison)
            + p9.geom_point(p9.aes(x='data_api', y='data_cache'), size=0.5, alpha=0.3)
            + p9.facet_wrap('~VARIABLE', scales='free')
            + p9.geom_abline(slope=1, intercept=0, color='red', linetype='dashed')
            + p9.labs(
                title=f'Carbon Comparison at Year {compare_year} (API vs Cache)',
                x='Carbon from API (tC/ha)', y='Carbon from Cache (tC/ha)',
            )
        )
        fig1.save(comparison_dir / f'{v2020_name}_{spec_cat}_Compare_API_V.S_Cache.svg', dpi=300)

        fig2 = (
            p9.ggplot(df_comparison)
            + p9.geom_point(p9.aes(x='data_cache', y='data_v2020'), size=0.5, alpha=0.3)
            + p9.facet_wrap('~VARIABLE', scales='free')
            + p9.geom_abline(slope=1, intercept=0, color='red', linetype='dashed')
            + p9.labs(
                title=f'Carbon Comparison at Year {compare_year} (Cache vs v2020)',
                x='FullCam v2024 (tC/ha)', y='FullCam v2020 (tC/ha)',
            )
        )
        fig2.save(comparison_dir / f'{v2020_name}_{spec_cat}_v2024_V.S_{v2020_name}_{v2020_cat}_v2020.svg', dpi=300)

    # ── Align coords then compute ratio rasters ───────────────────────
    ds_v2020['x'] = ds_cache['x']
    ds_v2020['y'] = ds_cache['y']

    diff_ratio = ds_cache / ds_v2020
    diff_ratio.rio.write_crs(Debries_C.rio.crs, inplace=True)
    diff_ratio.rio.write_transform(Debries_C.rio.transform(), inplace=True)
    for var in diff_ratio['VARIABLE'].values:
        diff_ratio.sel(VARIABLE=var).rio.to_raster(
            comparison_dir / f'ratio_layer_{v2020_name}_{spec_cat}_v2024_V.S_{v2020_name}_{v2020_cat}_v2020_{var}.tif',
            compress='LZW',
        )

    # ── Component violin/box + fraction rasters (fig3) ───────────────
    ds_cache_sel = ds_cache.sel(x=compare_coords_x, y=compare_coords_y).to_dataframe().reset_index()

    p9.options.figure_size = (10, 6)
    fig3 = (
        p9.ggplot(ds_cache_sel)
        + p9.geom_violin(p9.aes(x='VARIABLE', y='data'), fill='lightblue', alpha=0.7)
        + p9.geom_boxplot(p9.aes(x='VARIABLE', y='data'), width=0.1, fill='white', outlier_size=0.5)
        + p9.labs(
            title=f'Carbon Component Distribution at Year {compare_year} (Cache Data)',
            x='Carbon Component', y='Carbon Stock (tC/ha)',
        )
    )
    fig3.save(comparison_dir / f'{v2020_name}_{spec_cat}_Componet_Boxplot_Year_{compare_year}.svg', dpi=300)

    total_carbon = ds_cache.sum(dim='VARIABLE', skipna=False)
    for ratio_da, name in zip(
        [ds_cache.sel(VARIABLE='TREE_C_HA')   / total_carbon * 100,
         ds_cache.sel(VARIABLE='DEBRIS_C_HA') / total_carbon * 100,
         ds_cache.sel(VARIABLE='SOIL_C_HA')   / total_carbon * 100],
        ['Tree', 'Debris', 'Soil'],
    ):
        ratio_da.rio.write_crs(LUTO_lumap.rio.crs, inplace=True)
        ratio_da.rio.write_transform(LUTO_lumap.rio.transform(), inplace=True)
        ratio_da.rio.to_raster(
            comparison_dir / f'componet_layer_{v2020_name}_{spec_cat}_Componet_ratio_{name}_Year_{compare_year}.tif',
            compress='LZW',
        )

    # ── Spatial CO2 maps: v2020 | v2024 | Difference (fig6) ──────────
    fig6, axes = plt.subplots(3, 3, figsize=(18, 13), constrained_layout=True)

    for row_idx, (var, comp_label) in enumerate(MAP_COMPONENTS):
        da_v2020_co2 = ds_v2020[:, ::5, ::5].sel(VARIABLE=var) * CO2_FACTOR
        da_v2024_co2 = ds_cache[::5, ::5, :].sel(VARIABLE=var) * CO2_FACTOR

        da_diff_co2 = da_v2020_co2 * np.nan
        da_diff_co2.values = da_v2024_co2.values - da_v2020_co2.values

        all_vals = np.concatenate([
            da_v2020_co2.values[np.isfinite(da_v2020_co2.values)],
            da_v2024_co2.values[np.isfinite(da_v2024_co2.values)],
        ])
        vmax = float(np.nanpercentile(all_vals, 95))

        ax = axes[row_idx, 0]
        da_v2020_co2.plot(ax=ax, cmap='YlOrRd', vmin=0, vmax=vmax,
                          add_labels=False, cbar_kwargs={'label': 'tCO2/ha', 'shrink': 0.8})
        if row_idx == 0:
            ax.set_title('v2020', fontsize=12, fontweight='bold')
        ax.set_ylabel(comp_label, fontsize=11, fontweight='bold')
        ax.set_xlabel('')

        ax = axes[row_idx, 1]
        da_v2024_co2.plot(ax=ax, cmap='YlOrRd', vmin=0, vmax=vmax,
                          add_labels=False, cbar_kwargs={'label': 'tCO2/ha', 'shrink': 0.8})
        if row_idx == 0:
            ax.set_title('v2024', fontsize=12, fontweight='bold')
        ax.set_ylabel('')
        ax.set_xlabel('')

        ax = axes[row_idx, 2]
        diff_vals    = da_diff_co2.values[np.isfinite(da_diff_co2.values)]
        diff_abs_max = float(np.nanpercentile(np.abs(diff_vals), 95))
        norm = TwoSlopeNorm(vmin=-diff_abs_max, vcenter=0, vmax=diff_abs_max)
        da_diff_co2.plot(ax=ax, cmap='RdBu_r', norm=norm,
                         add_labels=False, cbar_kwargs={'label': 'Δ tCO2/ha', 'shrink': 0.8})
        if row_idx == 0:
            ax.set_title('Difference  (v2024 − v2020)\nred = v2024 higher  |  blue = v2020 higher',
                         fontsize=10, fontweight='bold')
        ax.set_ylabel('')
        ax.set_xlabel('')

    fig6.suptitle(
        f'CO2 Stock Maps: v2020 vs v2024  —  {v2020_name} ({spec_cat})  |  Year {compare_year}\n'
        f'Units: tCO2/ha  (C converted using 44/12)',
        fontsize=13, fontweight='bold',
    )
    fig6.savefig(
        comparison_dir / f'{v2020_name}_{spec_cat}_Map_SideBySide_CO2_v2020_v2024_Year_{compare_year}.png',
        dpi=150, bbox_inches='tight',
    )
    plt.close(fig6)
    print(f"  Saved: {v2020_name}_{spec_cat}_Map_SideBySide_CO2_v2020_v2024_Year_{compare_year}.png")


################################################################
#            Loop over all species and categories              #
################################################################

for SPECIES_ID, specCats in SPECIES_GEOMETRY.items():
    for SPECIES_CAT in specCats:
        run_species_comparison(SPECIES_ID, SPECIES_CAT)
