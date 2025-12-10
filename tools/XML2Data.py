import os
import pandas as pd
import rasterio
import xarray as xr
import numpy as np

from lxml import etree


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



def parse_site_data(xml_string: str) -> xr.Dataset:
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
    

    # Initialize xarray Dataset
    site_arr = xr.Dataset(
        coords={
            'year': np.arange(year_start, year_start + num_years),
            'month': np.arange(1, num_per_year + 1)
        }
    )

    # Add avgAirTemp DataArray
    raw_values = np.fromstring(api_avgAirTemp.xpath('.//rawTS')[0].text, sep=',')
    site_arr['avgAirTemp'] = xr.DataArray(
        raw_values.reshape(num_years, num_per_year),
        coords=site_arr.coords,
        dims=site_arr.dims
    )

    # Get openPanEvap TimeSeries
    api_openPanEvap = site_root.xpath('.//*[@tInTS="openPanEvap"]')[0]
    raw_values = np.fromstring(api_openPanEvap.xpath('.//rawTS')[0].text, sep=',')
    site_arr['openPanEvap'] = xr.DataArray(
        raw_values.reshape(num_years, num_per_year),
        coords=site_arr.coords,
        dims=site_arr.dims
    )

    # Get rainfall TimeSeries
    api_rainfall = site_root.xpath('.//*[@tInTS="rainfall"]')[0]
    raw_values = np.fromstring(api_rainfall.xpath('.//rawTS')[0].text, sep=',')
    site_arr['rainfall'] = xr.DataArray(
        raw_values.reshape(num_years, num_per_year),
        coords=site_arr.coords,
        dims=site_arr.dims
    )

    # Get forestProdIx TimeSeries
    api_forestProdIx = site_root.xpath('.//*[@tInTS="forestProdIx"]')[0]
    year_start = int(api_forestProdIx.get('yr0TS'))
    num_per_year = int(api_forestProdIx.get('dataPerYrTS')) # 1, means its annual data
    num_years = int(api_forestProdIx.get('nYrsTS'))
    raw_values = np.fromstring(api_forestProdIx.xpath('.//rawTS')[0].text, sep=',')
    site_arr['forestProdIx'] = xr.DataArray(
        raw_values.reshape(num_years),
        dims=['year'],
        coords={'year': np.arange(year_start, year_start + num_years)}
    )

    # Append static variables (no spatial dimensions yet)
    maxAbgMF = float(site_root.xpath('.//*[@tIn="maxAbgMF"]')[0].get('value'))
    fpiAvgLT = site_arr['forestProdIx'][:48].mean(dim='year').values  # fpiAvgLT from first 48 elements (1970-2017)
    site_arr['maxAbgMF'] = xr.DataArray(maxAbgMF)
    site_arr['fpiAvgLT'] = xr.DataArray(fpiAvgLT)

    return site_arr



def parse_soil_data(xml_string: str) -> xr.Dataset:
    
    # Parse the siteinfo XML
    site_root = etree.fromstring(xml_string.encode('utf-8'))
    
    # Get soil data
    soil_clayFrac = float(site_root.xpath('.//SoilOther')[0].get('clayFrac'))
    
    return xr.Dataset({ 
        'clayFrac': xr.DataArray(soil_clayFrac)
    })

        
        
def parse_init_data(xml_string: str, tsmd_year: int) -> xr.DataArray:
    """
    Parse soil initialization data from siteInfo XML string and return as xarray DataArray.

    Parameters
    ----------
    xml_string : str
        Raw XML string content from siteInfo API response
        
    tsmd_year : int
        Year for which to extract TSMD initialization value
        
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
    tsmd_values = np.fromstring(rawTS, sep=',').astype(np.float32)

    # Calculate index for the requested year
    tsmd_index = tsmd_year - yr0TS
    TSMDInitF = tsmd_values[tsmd_index]

    return xr.Dataset({
        # 'biofCMInitF': biofCMInitF,   # skipping biof as it is a constant 0
        # 'biosCMInitF': biosCMInitF,   # skipping bios as it is a constant 0
        # 'dpmaCMInitF': dpmaCMInitF,   # skipping dpma as it is a constant 0
        'rpmaCMInitF': rpmaCMInitF,
        'humsCMInitF': humsCMInitF,
        'inrtCMInitF': inrtCMInitF,
        'TSMDInitF': TSMDInitF
    })
    


def get_siteinfo_data(lon:float, lat:float, tsmd_year:int) -> xr.Dataset:
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
    site_arr = parse_site_data(xml_string)
    soil_arr = parse_soil_data(xml_string)
    init_arr = parse_init_data(xml_string, tsmd_year)

    return xr.merge([site_arr, soil_arr, init_arr]).expand_dims(y=[lat], x=[lon])





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


def export_to_geotiff_with_band_names(
    xarry:xr.DataArray, 
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
