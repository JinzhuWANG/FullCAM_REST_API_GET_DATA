import os
import pandas as pd
import rasterio
import xarray as xr
import numpy as np

from lxml import etree



def parse_siteinfo_data(xml_string: str) -> xr.Dataset:
    """
    Parse siteInfo XML string and return relevant data as xarray Dataset.

    Parameters
    ----------
    xml_string : str
        Raw XML string content from siteInfo API response

    Returns
    -------
    xr.Dataset
        Dataset containing avgAirTemp, openPanEvap, rainfall, forestProdIx, maxAbgMF, and fpiAvgLT
        without spatial dimensions (year, month only)
    """
    # Parse XML string
    site_root = etree.fromstring(xml_string.encode('utf-8'))

    # Get avgAirTemp TimeSeries
    api_avgAirTemp  = site_root.xpath('.//*[@tInTS="avgAirTemp"]')[0]
    year_start      = int(api_avgAirTemp.get('yr0TS'))
    num_per_year    = int(api_avgAirTemp.get('dataPerYrTS'))
    num_years       = int(api_avgAirTemp.get('nYrsTS'))
    raw_values      = np.array(eval(api_avgAirTemp.xpath('.//rawTS')[0].text))

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

    # Append static variables (no spatial dimensions yet)
    maxAbgMF = np.array(eval(site_root.xpath('.//*[@tIn="maxAbgMF"]')[0].get('value')))
    fpiAvgLT = df_arr['forestProdIx'][:48].mean(dim='year').values  # fpiAvgLT from first 48 elements (1970-2017)
    df_arr['maxAbgMF'] = xr.DataArray(maxAbgMF)
    df_arr['fpiAvgLT'] = xr.DataArray(fpiAvgLT)

    return df_arr


def get_siteinfo_data(lon:float, lat:float) -> xr.Dataset:
    """
    Load and parse siteInfo XML file for given coordinates.

    Parameters
    ----------
    lon : float
        Longitude coordinate
    lat : float
        Latitude coordinate

    Returns
    -------
    xr.Dataset
        Dataset containing siteInfo data with spatial dimensions (y, x), or None if file not found
    """
    # Check if file exists
    filepath = f'downloaded/siteinfo_{lon}_{lat}.xml'
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}. Returning None.")
        return None

    # Read XML file as string
    with open(filepath, 'r', encoding='utf-8') as f:
        xml_string = f.read()

    # Parse XML to xr data; add spatial dimensions
    df_arr = parse_siteinfo_data(xml_string).expand_dims(y=[lat], x=[lon])

    df_arr['maxAbgMF'] = xr.DataArray(
        df_arr['maxAbgMF'].values.reshape(1, 1),
        dims=['y', 'x'],
        coords={'y': [lat], 'x': [lon]}
    )
    df_arr['fpiAvgLT'] = xr.DataArray(
        df_arr['fpiAvgLT'].values.reshape(1, 1),
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
        return None

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



def parse_soilbase_data(xml_string: str) -> dict:
    """
    Parse SoilBase information from siteInfo XML string and return as three xarray DataArrays.

    This function extracts soil parameters from the SoilBase section of FullCAM siteInfo XML.
    The SoilBase contains three child elements:
    - SoilZap[@id='forest']: Forest soil parameters (49 numeric attributes)
    - SoilZap[@id='agriculture']: Agriculture soil parameters (49 numeric attributes)
    - SoilOther[@id='other']: Common soil properties (3 numeric attributes: clayFrac, bulkDensity, maxASW)

    Note: The tSoil attribute (soil texture type string) is excluded as it's non-numeric.

    Parameters
    ----------
    xml_string : str
        Raw XML string content from siteInfo API response

    Returns
    -------
    dict
        Dictionary containing three xarray DataArrays:
        - 'forest': Forest soil parameters (band) where band contains attribute names
        - 'agriculture': Agriculture soil parameters (band) where band contains attribute names
        - 'SoilOther': Common soil properties (band) where band contains attribute names

        All attributes are numeric (float). Empty string attributes are stored as np.nan.
        Boolean attributes are converted to 1.0 (true) or 0.0 (false).

    """
    # Parse XML string
    site_root = etree.fromstring(xml_string.encode('utf-8'))

    # Get SoilBase element
    soilbase = site_root.find('.//SoilBase')
    if soilbase is None:
        print(f"SoilBase element not found in XML. Returning None.")
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
    forest_data = np.full(len(forest_attrs), np.nan).astype(np.float32)
    agriculture_data = np.full(len(agriculture_attrs), np.nan).astype(np.float32)
    soilother_data = np.full(len(soilother_attrs), np.nan).astype(np.float32)

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
                forest_data[i] = convert_to_float(val)

    # Fill agriculture data
    if agriculture_elem is not None:
        for i, attr in enumerate(agriculture_attrs):
            val = agriculture_elem.get(attr, '')
            if val != '':
                agriculture_data[i] = convert_to_float(val)

    # Fill SoilOther data (only numeric attributes now)
    if soilother_elem is not None:
        for i, attr in enumerate(soilother_attrs):
            val = soilother_elem.get(attr, '')
            if val != '':
                soilother_data[i] = convert_to_float(val)

    # Create DataArrays with attribute names as band coordinates (no spatial dimensions)
    forest_da = xr.DataArray(
        forest_data,
        dims=['band'],
        coords={'band': forest_attrs}
    )

    agriculture_da = xr.DataArray(
        agriculture_data,
        dims=['band'],
        coords={'band': agriculture_attrs}
    )

    soilother_da = xr.DataArray(
        soilother_data,
        dims=['band'],
        coords={'band': soilother_attrs}
    )

    return {
        'forest': forest_da,
        'agriculture': agriculture_da,
        'SoilOther': soilother_da
    }


def get_soilbase_data(lon: float, lat: float) -> dict:
    """
    Load and parse SoilBase information from siteInfo XML file for given coordinates.

    Parameters
    ----------
    lon : float
        Longitude coordinate
    lat : float
        Latitude coordinate

    Returns
    -------
    dict
        Dictionary containing three xarray DataArrays with spatial dimensions (y, x, band), or None if file not found

    """

    # Check if file exists
    filepath = f'downloaded/siteinfo_{lon}_{lat}.xml'
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}. Returning None.")
        return None

    # Read XML file as string
    with open(filepath, 'r', encoding='utf-8') as f:
        xml_string = f.read()

    # Parse XML to xr data
    soil_data = parse_soilbase_data(xml_string)

    # Add spatial dimensions to each DataArray
    for key in soil_data:
        soil_data[key] = soil_data[key].expand_dims(y=[lat], x=[lon])

    return soil_data


def parse_soilInit_data(xml_string: str, tsmd_year: int = 2010) -> xr.DataArray:
    """
    Parse soil initialization data from siteInfo XML string and return as xarray DataArray.

    Parameters
    ----------
    xml_string : str
        Raw XML string content from siteInfo API response
    tsmd_year : int, optional
        Year to use for TSMD initial value (default: 2010).
        Must be between 1970 and the last year available in the data.

    Returns
    -------
    xr.DataArray
        DataArray containing soil carbon pool values and TSMD initialization values (band dimension only)
    """
    # Parse the siteinfo XML
    site_root = etree.fromstring(xml_string.encode('utf-8'))

    # Extract LocnSoil attributes
    locn_soil = site_root.xpath('.//LocnSoil')[0]
    initFracBiof = float(locn_soil.get('initFracBiof'))
    initFracBios = float(locn_soil.get('initFracBios'))
    initFracDpma = float(locn_soil.get('initFracDpma'))
    initFracRpma = float(locn_soil.get('initFracRpma'))
    initFracHums = float(locn_soil.get('initFracHums'))
    initFracInrt = float(locn_soil.get('initFracInrt'))
    initTotalC = float(locn_soil.get('initTotalC'))

    # Calculate soil carbon pool values (tonnes C/ha)
    biofCMInitF = initFracBiof * initTotalC
    biosCMInitF = initFracBios * initTotalC
    dpmaCMInitF = initFracDpma * initTotalC
    rpmaCMInitF = initFracRpma * initTotalC
    humsCMInitF = initFracHums * initTotalC
    inrtCMInitF = initFracInrt * initTotalC

    # Extract TSMD time series and get value for specified year
    tsmd_elem = site_root.xpath(".//TimeSeries[@tInTS='initTSMD']")[0]
    yr0TS = int(tsmd_elem.get('yr0TS'))  # Start year (e.g., 1970)

    # Parse TSMD values
    rawTS = tsmd_elem.find('rawTS').text
    tsmd_values = [float(x) for x in rawTS.split(',')]

    # Calculate index for the requested year
    tsmd_index = tsmd_year - yr0TS
    TSMDInitF = tsmd_values[tsmd_index]
    TSMDInitA = TSMDInitF  # Same value for agriculture

    # return as xarray DataArray (no spatial dimensions)
    return xr.DataArray(
        np.array([
            biofCMInitF, biosCMInitF, dpmaCMInitF, rpmaCMInitF,
            humsCMInitF, inrtCMInitF, TSMDInitF, TSMDInitA
        ], dtype=np.float32),
        dims=['band'],
        coords={
            'band': [
                'biofCMInitF', 'biosCMInitF', 'dpmaCMInitF', 'rpmaCMInitF',
                'humsCMInitF', 'inrtCMInitF', 'TSMDInitF', 'TSMDInitA'
            ]
        }
    )


def get_soilInit_data(lon: float, lat: float, tsmd_year: int = 2010) -> xr.DataArray:
    """
    Load and parse soil initialization data from siteInfo XML file for given coordinates.

    Parameters
    ----------
    lon : float
        Longitude coordinate
    lat : float
        Latitude coordinate
    tsmd_year : int, optional
        Year to use for TSMD initial value (default: 2010)

    Returns
    -------
    xr.DataArray
        DataArray containing soil initialization data with spatial dimensions (y, x, band)
    """
    # Construct the siteinfo file path
    file_path = f'downloaded/siteInfo_{lon}_{lat}.xml'
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Required file '{file_path}' not found! "
            f"Run get_data.py to download site data for coordinates ({lat}, {lon})."
        )

    # Read XML file as string
    with open(file_path, 'r', encoding='utf-8') as f:
        xml_string = f.read()

    # Parse XML to xr data
    soil_init = parse_soilInit_data(xml_string, tsmd_year)

    # Add spatial dimensions
    soil_init = soil_init.expand_dims(y=[lat], x=[lon])

    return soil_init


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
