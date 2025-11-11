import os
import xarray as xr
import numpy as np

from lxml import etree
from tools.plo_section_functions import get_siteinfo



def get_siteinfo_data(lon:float, lat:float) -> dict:
    """
    Parse siteInfo XML file and return relevant data as a dictionary.
    """
    
    # Check if file exists
    filepath = f'downloaded/siteinfo_{lon}_{lat}.xml'
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}. Downloading...")
        get_siteinfo(lat, lon)
    
    
    # Parse DATA-API response to get TimeSeries data
    site_root = etree.parse(filepath).getroot()


    # Get avgAirTemp TimeSeries
    api_avgAirTemp = site_root.xpath('.//*[@tInTS="avgAirTemp"]')[0]
    year_start = int(api_avgAirTemp.get('yr0TS'))
    num_per_year = int(api_avgAirTemp.get('dataPerYrTS'))
    num_years = int(api_avgAirTemp.get('nYrsTS'))
    raw_values = np.array(eval(api_avgAirTemp.xpath('.//rawTS')[0].text))
    
    df_arr = xr.Dataset(
        coords={
            'year': np.arange(year_start, year_start + num_years),
            'month': np.arange(1, num_per_year + 1)
        }
    )
    
    df_arr['avgAirTemp'] = xr.DataArray(
        raw_values.reshape(num_years, num_per_year),
        coords=df_arr.coords,
        dims=df_arr.dims
    )
    
    
    # Get openPanEvap TimeSeries
    api_openPanEvap = site_root.xpath('.//*[@tInTS="openPanEvap"]')[0]
    raw_values = np.array(eval(api_openPanEvap.xpath('.//rawTS')[0].text))
    df_arr['openPanEvap'] = xr.DataArray(
        raw_values.reshape(num_years, num_per_year),
        coords=df_arr.coords,
        dims=df_arr.dims
    )
    
    
    # Get rainfall TimeSeries
    api_rainfall = site_root.xpath('.//*[@tInTS="rainfall"]')[0]
    raw_values = np.array(eval(api_rainfall.xpath('.//rawTS')[0].text))
    df_arr['rainfall'] = xr.DataArray(
        raw_values.reshape(num_years, num_per_year),
        coords=df_arr.coords,
        dims=df_arr.dims
    )
    
    
    # Get forestProdIx TimeSeries
    api_forestProdIx = site_root.xpath('.//*[@tInTS="forestProdIx"]')[0]
    year_start = int(api_forestProdIx.get('yr0TS'))
    num_per_year = int(api_forestProdIx.get('dataPerYrTS')) # 1, means its annual data
    num_years = int(api_forestProdIx.get('nYrsTS'))
    raw_values = np.array(eval(api_forestProdIx.xpath('.//rawTS')[0].text))
    df_arr['forestProdIx'] = xr.DataArray(
        raw_values.reshape(num_years),
        dims=['year'],
        coords={'year': np.arange(year_start, year_start + num_years)}
    )
    
    # Expand coords to match other variables
    df_arr = df_arr.expand_dims(y=[lat], x=[lon])

    # Append static variables
    maxAbgMF = np.array(eval(site_root.xpath('.//*[@tIn="maxAbgMF"]')[0].get('value')))
    fpiAvgLT = df_arr['forestProdIx'][0,0,:48].mean(dim='year').values  # fpiAvgLT from first 48 elements (1970-2017)
    df_arr['maxAbgMF'] = xr.DataArray(
        maxAbgMF.reshape(1, 1),
        dims=['y', 'x'],
        coords={'y': [lat], 'x': [lon]}
    )
    df_arr['fpiAvgLT'] = xr.DataArray(
        np.array(fpiAvgLT).reshape(1, 1),
        dims=['y', 'x'],
        coords={'y': [lat], 'x': [lon]}
    )
    
    return df_arr
    