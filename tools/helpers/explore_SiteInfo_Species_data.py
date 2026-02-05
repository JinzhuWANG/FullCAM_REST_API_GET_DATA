
import xarray as xr
import geopandas as gpd


# Get data without consensus checking
siteinfo_noChecking = xr.open_dataset('N:/Data-Master/FullCAM/FullCAM_REST_API_GET_DATA_2025/data/processed/20251117_RES10_Cell/siteinfo_RES.nc')

siteinfo_noChecking['avgAirTemp'].sel(year=2020, month=7).plot()
siteinfo_noChecking['openPanEvap'].sel(year=2020, month=7).plot()
siteinfo_noChecking['rainfall'].sel(year=2020, month=7).plot()
siteinfo_noChecking['forestProdIx'].sel(year=2020).plot()
siteinfo_noChecking['maxAbgMF'].plot()
siteinfo_noChecking['fpiAvgLT'].plot()


soil_noChecking = xr.open_dataset('N:/Data-Master/FullCAM/FullCAM_REST_API_GET_DATA_2025/data/processed/20251117_RES10_Cell/soilbase_soilother_RES.nc')['data']
soil_noChecking.sel(band='clayFrac').plot(vmin=0, vmax=0.6)


init_noChecking = xr.open_dataset('N:/Data-Master/FullCAM/FullCAM_REST_API_GET_DATA_2025/data/processed/20251117_RES10_Cell/soilInit_RES.nc')['data']
init_noChecking.sel(band='TSMDInitF').plot()
init_noChecking.sel(band='humsCMInitF').plot(vmax=70, vmin=0)
init_noChecking.sel(band='inrtCMInitF').plot(vmax=70, vmin=0)
init_noChecking.sel(band='rpmaCMInitF').plot(vmax=70, vmin=0)



# Get data with consensus=3 checking
siteinfo_Checking = xr.open_dataset('N:/Data-Master/FullCAM/FullCAM_REST_API_GET_DATA_2025/data/processed/20251117_RES10_Cell/siteinfo_RES.nc')

siteinfo_Checking['avgAirTemp'].sel(year=2020, month=7).plot()
siteinfo_Checking['openPanEvap'].sel(year=2020, month=7).plot()
siteinfo_Checking['rainfall'].sel(year=2020, month=7).plot()
siteinfo_Checking['forestProdIx'].sel(year=2020).plot()
siteinfo_Checking['maxAbgMF'].plot()
siteinfo_Checking['fpiAvgLT'].plot()


soil_Checking = xr.open_dataset('N:/Data-Master/FullCAM/FullCAM_REST_API_GET_DATA_2025/data/processed/20251210_RES10_Consensus_3/soilbase_soilother_RES.nc')['data']
soil_Checking.sel(band='clayFrac').plot(vmax=0.6)

init_Checking = xr.open_dataset('N:/Data-Master/FullCAM/FullCAM_REST_API_GET_DATA_2025/data/processed/20251210_RES10_Consensus_3/soilInit_RES.nc')['data']
init_Checking.sel(band='TSMDInitF').plot()
init_Checking.sel(band='humsCMInitF').plot(vmax=70, vmin=0)
init_Checking.sel(band='inrtCMInitF').plot(vmax=70, vmin=0)
init_Checking.sel(band='rpmaCMInitF').plot(vmax=70, vmin=0)


spec_Checking = xr.open_dataset('N:/Data-Master/FullCAM/FullCAM_REST_API_GET_DATA_2025/data/processed/20251228_RES3_Species/species_RES.nc')

spec_Checking['Block'].sel(TYF_Type='tyf_G').plot()
spec_Checking['Block'].sel(TYF_Type='tyf_r').plot(vmin=0, vmax=50)
spec_Checking['Belt'].sel(TYF_Type='tyf_G').plot()
spec_Checking['Belt'].sel(TYF_Type='tyf_r').plot(vmin=0, vmax=70)


AUS_shp = gpd.read_file('N:/Data-Master/Australian_administrative_boundaries/state_2011_aus/STE11aAust.shp')
tyf_r_gt_100 = (spec_Checking['Belt'].sel(TYF_Type='tyf_r') > 100)
tyf_r_gt_100 = tyf_r_gt_100.rio.write_crs("EPSG:4283")
masked = tyf_r_gt_100.rio.clip(AUS_shp.geometry, AUS_shp.crs, drop=True)

masked.plot()



# Open the completed assembled datasets
data_assembled = xr.open_dataset('data/data_assembled/siteinfo_cache.nc')











