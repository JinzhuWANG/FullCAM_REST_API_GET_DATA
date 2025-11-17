import os
import pandas as pd
import rasterio
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
    filepath = f'downloaded/df_{lon}_{lat}.csv'
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
        pd.read_csv(filepath)
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



def get_soilbase_data(lon: float, lat: float) -> dict:
    """
    Extract SoilBase information from siteInfo XML file and return as three xarray DataArrays.

    This function extracts soil parameters from the SoilBase section of FullCAM siteInfo XML files.
    The SoilBase contains three child elements:
    - SoilZap[@id='forest']: Forest soil parameters (49 numeric attributes)
    - SoilZap[@id='agriculture']: Agriculture soil parameters (49 numeric attributes)
    - SoilOther[@id='other']: Common soil properties (3 numeric attributes: clayFrac, bulkDensity, maxASW)

    Note: The tSoil attribute (soil texture type string) is excluded as it's non-numeric.

    Parameters
    ----------
    lon : float
        Longitude coordinate
    lat : float
        Latitude coordinate

    Returns
    -------
    dict
        Dictionary containing three xarray DataArrays:
        - 'forest': Forest soil parameters (y, x, band) where band contains attribute names
        - 'agriculture': Agriculture soil parameters (y, x, band) where band contains attribute names
        - 'SoilOther': Common soil properties (y, x, band) where band contains attribute names

        All attributes are numeric (float). Empty string attributes are stored as np.nan.
        Boolean attributes are converted to 1.0 (true) or 0.0 (false).

    Examples
    --------
    >>> soil_data = get_soilbase_data(148.16, -35.61)
    >>> # Direct access by attribute name
    >>> clay = soil_data['SoilOther'].sel(band='clayFrac')
    >>> ph = soil_data['forest'].sel(band='pH')
    """

    # Check if file exists
    filepath = f'downloaded/siteinfo_{lon}_{lat}.xml'
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}. Returning None.")
        return None

    # Parse XML file
    site_root = etree.parse(filepath).getroot()

    # Get SoilBase element
    soilbase = site_root.find('.//SoilBase')
    if soilbase is None:
        print(f"SoilBase element not found in {filepath}. Returning None.")
        return None

    # Extract SoilZap[@id='forest']
    forest_elem = soilbase.find("./SoilZap[@id='forest']")
    forest_attrs = list(forest_elem.attrib.keys()) if forest_elem is not None else []
    forest_attrs = [attr for attr in forest_attrs if attr != 'id']  # Remove 'id' attribute

    # Extract SoilZap[@id='agriculture']
    agriculture_elem = soilbase.find("./SoilZap[@id='agriculture']")
    agriculture_attrs = list(agriculture_elem.attrib.keys()) if agriculture_elem is not None else []
    agriculture_attrs = [attr for attr in agriculture_attrs if attr != 'id']  # Remove 'id' attribute

    # Extract SoilOther[@id='other']
    soilother_elem = soilbase.find("./SoilOther[@id='other']")
    soilother_attrs = list(soilother_elem.attrib.keys()) if soilother_elem is not None else []
    soilother_attrs = [attr for attr in soilother_attrs if attr not in ['id', 'tSoil']]  # Remove 'id' and 'tSoil' attributes

    # Initialize arrays with np.nan
    forest_data = np.full((1, 1, len(forest_attrs)), np.nan).astype(np.float32)
    agriculture_data = np.full((1, 1, len(agriculture_attrs)), np.nan).astype(np.float32)
    soilother_data = np.full((1, 1, len(soilother_attrs)), np.nan).astype(np.float32)

    # Helper function to convert attribute value to float
    def convert_to_float(val):
        """Convert attribute value to float, handling boolean strings."""
        if val == '':
            return np.nan
        elif val.lower() == 'true':
            return 1.0
        elif val.lower() == 'false':
            return 0.0
        else:
            try:
                return float(val)
            except ValueError:
                return np.nan

    # Fill forest data
    if forest_elem is not None:
        for i, attr in enumerate(forest_attrs):
            val = forest_elem.get(attr, '')
            if val != '':
                forest_data[0, 0, i] = convert_to_float(val)

    # Fill agriculture data
    if agriculture_elem is not None:
        for i, attr in enumerate(agriculture_attrs):
            val = agriculture_elem.get(attr, '')
            if val != '':
                agriculture_data[0, 0, i] = convert_to_float(val)

    # Fill SoilOther data (only numeric attributes now)
    if soilother_elem is not None:
        for i, attr in enumerate(soilother_attrs):
            val = soilother_elem.get(attr, '')
            if val != '':
                soilother_data[0, 0, i] = convert_to_float(val)

    # Create DataArrays with attribute names as band coordinates
    forest_da = xr.DataArray(
        forest_data,
        dims=['y', 'x', 'band'],
        coords={
            'y': [lat],
            'x': [lon],
            'band': forest_attrs
        }
    )

    agriculture_da = xr.DataArray(
        agriculture_data,
        dims=['y', 'x', 'band'],
        coords={
            'y': [lat],
            'x': [lon],
            'band': agriculture_attrs
        }
    )

    soilother_da = xr.DataArray(
        soilother_data,
        dims=['y', 'x', 'band'],
        coords={
            'y': [lat],
            'x': [lon],
            'band': soilother_attrs
        }
    )

    return {
        'forest': forest_da,
        'agriculture': agriculture_da,
        'SoilOther': soilother_da
    }


def export_to_geotiff_with_band_names(
    xarry:xr.DataArray|xr.DataArray, 
    output_path:str, 
    band_dim:str='band', 
    compress:str='lzw'
)->None:
    """
    Export xarray DataArray to GeoTIFF with proper band names/descriptions.

    This function uses rasterio to write GeoTIFF files with band descriptions
    taken from the coordinate values of the band dimension. This ensures that
    multi-band GeoTIFFs have meaningful band names instead of generic Band_1, Band_2, etc.

    Parameters
    ----------
    xarry : xr.DataArray
        Input DataArray with spatial dimensions (y, x) and optional band dimension.
        Must have rio CRS and transform already set via rio.write_crs() and rio.write_transform().
    output_path : str
        Output file path for the GeoTIFF
    band_dim : str, optional
        Name of the band dimension (default: 'band'). If this dimension exists,
        its coordinate values will be used as band descriptions.
    compress : str, optional
        Compression method for GeoTIFF (default: 'lzw'). Common options: 'lzw', 'deflate', 'packbits'

    Returns
    -------
    None
        Writes GeoTIFF to disk
    """

    # Ensure proper dimension order
    if band_dim in xarry.dims:
        # Multi-band: ensure (band, y, x) order
        xarry = xarry.transpose(band_dim, 'y', 'x')
        if len(xarry.coords[band_dim].values.shape) == 1: # band dim is 1D
            band_names = [str(i) for i in xarry.coords[band_dim].values]
        else:
            band_names = ["_".join(map(str, i)) for i in xarry.coords[band_dim].values]
    else:
        # Single band: ensure (y, x) order
        xarry = xarry.transpose('y', 'x')
        band_names = None

    # Get rasterio profile from rioxarray
    profile = {
        'driver': 'GTiff',
        'dtype': xarry.dtype,
        'width': xarry.rio.width,
        'height': xarry.rio.height,
        'count': xarry.shape[0] if band_names else 1,
        'crs': xarry.rio.crs,
        'transform': xarry.rio.transform(),
        'compress': compress,
        'tiled': True,
        'blockxsize': 256,
        'blockysize': 256,
    }

    # Write GeoTIFF with rasterio
    with rasterio.open(output_path, 'w', **profile) as dst:
        if band_names:
            # Multi-band: write each band with description
            for i, band_name in enumerate(band_names, start=1):
                dst.write(xarry.isel({band_dim: i-1}).values, i)
                dst.set_band_description(i, str(band_name))
        else:
            # Single band
            dst.write(xarry.values, 1)
    
    print(f"Exported GeoTIFF to {output_path}")
