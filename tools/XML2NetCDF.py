import os
import pandas as pd
import xarray as xr
import numpy as np

from lxml import etree



def get_siteinfo_data(lon:float, lat:float) -> dict:
    """
    Parse siteInfo XML file and return relevant data as a dictionary.
    """
    
    # Check if file exists
    filepath = f'downloaded/siteinfo_{lon}_{lat}.xml'
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}. Returning None.")
        return None
    
    
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



def get_carbon_data(lon:float, lat:float) -> xr.DataArray:
    '''
    Get carbon stock data from CSV file and return as xarray DataArray.
    '''
    
    # Check if file exists
    filepath = f'downloaded/df_{lat}_{lon}.csv'
    if not os.path.exists(filepath):
        return xr.DataArray(
            np.full((91, 3), np.nan),
            dims=['YEAR', 'VARIABLE'],
            coords={
                'YEAR': np.arange(2010, 2101),
                'VARIABLE': ['DEBRIS_C_HA', 'SOIL_C_HA', 'TREE_C_HA']
            }
        ).expand_dims(y=[lat], x=[lon])

    df = ( 
        pd.read_csv(f'downloaded/df_{lat}_{lon}.csv')
        .query('Year >= 2010')
        .drop(columns=['Step In Year', 'Dec. Year'])
        .rename(columns={
            'Year': 'YEAR', 
            'C mass of plants  (tC/ha)': 'TREE_C_HA',
            'C mass of debris  (tC/ha)': 'DEBRIS_C_HA',
            'C mass of soil  (tC/ha)': 'SOIL_C_HA',
        })
        .set_index('YEAR')
        .stack()
        .reset_index(name='value')
        .rename(columns={'level_1': 'VARIABLE'})
        .set_index(['YEAR', 'VARIABLE'])
        .reindex(
            pd.MultiIndex.from_product(
                [np.arange(2010, 2101), 
                 ['DEBRIS_C_HA', 'SOIL_C_HA', 'TREE_C_HA']],
                names=['YEAR', 'VARIABLE']
            ), fill_value=np.nan
        )
        .sort_values(['YEAR', 'VARIABLE'])
        .reset_index()
    )
        
    df_xr = (
        xr.DataArray(
        df['value'].values.astype(np.float32).reshape(
            df['YEAR'].nunique(), 
            df['VARIABLE'].nunique()),
        coords={
            'YEAR': df['YEAR'].unique(),
            'VARIABLE': df['VARIABLE'].unique(),
        },
        dims=['YEAR', 'VARIABLE']
        ).expand_dims(y=[lat], x=[lon])
    )
    
    return df_xr

    