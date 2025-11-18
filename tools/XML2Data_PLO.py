import os
import rasterio
import xarray as xr
import numpy as np

from lxml import etree


def parse_siteinfo_data(xml_string: str) -> xr.Dataset:
    """
    Parse PLO XML Site section and return relevant data as xarray Dataset.

    Parameters
    ----------
    xml_string : str
        Raw XML string content from PLO file

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
    # Extract from Site element attributes
    site_elem = site_root.find('.//Site')
    maxAbgMF = float(site_elem.get('maxAbgMF', 0.0))
    fpiAvgLT = float(site_elem.get('fpiAvgLT', 0.0))

    df_arr['maxAbgMF'] = xr.DataArray(maxAbgMF)
    df_arr['fpiAvgLT'] = xr.DataArray(fpiAvgLT)

    return df_arr


def get_siteinfo_data(plo_file: str) -> xr.Dataset:
    """
    Load and parse Site section from PLO XML file.

    Parameters
    ----------
    plo_file : str
        Path to PLO file

    Returns
    -------
    xr.Dataset
        Dataset containing siteInfo data with spatial dimensions (y, x) from Build section coordinates
    """
    # Check if file exists
    if not os.path.exists(plo_file):
        print(f"File not found: {plo_file}. Returning None.")
        return None

    # Read XML file as string
    with open(plo_file, 'r', encoding='utf-8') as f:
        xml_string = f.read()

    # Extract coordinates from Build section
    site_root = etree.fromstring(xml_string.encode('utf-8'))
    build_elem = site_root.find('.//Build')
    lat = float(build_elem.get('latBL'))
    lon = float(build_elem.get('lonBL'))

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


def parse_soilbase_data(xml_string: str) -> dict:
    """
    Parse SoilBase information from PLO XML string and return as xarray DataArray.

    In PLO files, the Soil section contains only SoilBase/SoilOther element with basic soil properties.
    Unlike siteInfo API responses, PLO files do not contain SoilZap elements for forest/agriculture.

    Parameters
    ----------
    xml_string : str
        Raw XML string content from PLO file

    Returns
    -------
    dict
        Dictionary containing one xarray DataArray:
        - 'SoilOther': Common soil properties (band) where band contains attribute names
          Includes: clayFrac, bulkDensity, maxASW (numeric attributes only)

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

    # Extract SoilOther[@id='other']
    soilother_elem = soilbase.find("./SoilOther[@id='other']")
    if soilother_elem is None:
        print(f"SoilOther element not found in SoilBase. Returning None.")
        return None

    soilother_attrs = list(soilother_elem.attrib.keys())
    # Remove 'id' and 'tSoil' attributes (non-numeric)
    soilother_attrs = [attr for attr in soilother_attrs if attr not in ['id', 'tSoil']]

    # Initialize array with np.nan
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

    # Fill SoilOther data (only numeric attributes)
    for i, attr in enumerate(soilother_attrs):
        val = soilother_elem.get(attr, '')
        if val != '':
            soilother_data[i] = convert_to_float(val)

    # Create DataArray with attribute names as band coordinates (no spatial dimensions)
    soilother_da = xr.DataArray(
        soilother_data,
        dims=['band'],
        coords={'band': soilother_attrs}
    )

    return {
        'SoilOther': soilother_da
    }


def get_soilbase_data(plo_file: str) -> dict:
    """
    Load and parse SoilBase information from PLO XML file.

    Parameters
    ----------
    plo_file : str
        Path to PLO file

    Returns
    -------
    dict
        Dictionary containing one xarray DataArray with spatial dimensions (y, x, band)
        from Build section coordinates

    """

    # Check if file exists
    if not os.path.exists(plo_file):
        print(f"File not found: {plo_file}. Returning None.")
        return None

    # Read XML file as string
    with open(plo_file, 'r', encoding='utf-8') as f:
        xml_string = f.read()

    # Extract coordinates from Build section
    site_root = etree.fromstring(xml_string.encode('utf-8'))
    build_elem = site_root.find('.//Build')
    lat = float(build_elem.get('latBL'))
    lon = float(build_elem.get('lonBL'))

    # Parse XML to xr data
    soil_data = parse_soilbase_data(xml_string)

    # Add spatial dimensions to DataArray
    for key in soil_data:
        soil_data[key] = soil_data[key].expand_dims(y=[lat], x=[lon])

    return soil_data


def parse_soilInit_data(xml_string: str) -> xr.DataArray:
    """
    Parse soil initialization data from PLO XML Init section and return as xarray DataArray.

    IMPORTANT: In PLO files, the Init/InitSoilF element contains ALREADY CALCULATED carbon pool values,
    NOT fractions. This is different from siteInfo API responses which contain initFrac* attributes.

    Parameters
    ----------
    xml_string : str
        Raw XML string content from PLO file

    Returns
    -------
    xr.DataArray
        DataArray containing soil carbon pool values and TSMD initialization values (band dimension only)
        Band coordinates: ['biofCMInitF', 'biosCMInitF', 'dpmaCMInitF', 'rpmaCMInitF',
                          'humsCMInitF', 'inrtCMInitF', 'TSMDInitF', 'ASWInitF']
    """
    # Parse the PLO XML
    site_root = etree.fromstring(xml_string.encode('utf-8'))

    # Extract InitSoilF attributes (already calculated values, not fractions)
    init_soil = site_root.xpath('.//InitSoilF')[0]

    # These are ALREADY in tonnes C/ha (not fractions to multiply by initTotalC)
    biofCMInitF = float(init_soil.get('biofCMInitF', 0.0))
    biosCMInitF = float(init_soil.get('biosCMInitF', 0.0))
    dpmaCMInitF = float(init_soil.get('dpmaCMInitF', 0.0))
    rpmaCMInitF = float(init_soil.get('rpmaCMInitF', 0.0))
    humsCMInitF = float(init_soil.get('humsCMInitF', 0.0))
    inrtCMInitF = float(init_soil.get('inrtCMInitF', 0.0))

    # TSMD and ASW initial values
    TSMDInitF = float(init_soil.get('TSMDInitF', 0.0))
    ASWInitF = init_soil.get('ASWInitF', np.nan)  # May be empty string
    if ASWInitF == '':
        ASWInitF = np.nan

    # return as xarray DataArray (no spatial dimensions)
    return xr.DataArray(
        np.array([
            biofCMInitF, biosCMInitF, dpmaCMInitF, rpmaCMInitF,
            humsCMInitF, inrtCMInitF, TSMDInitF, ASWInitF
        ], dtype=np.float32),
        dims=['band'],
        coords={
            'band': [
                'biofCMInitF', 'biosCMInitF', 'dpmaCMInitF', 'rpmaCMInitF',
                'humsCMInitF', 'inrtCMInitF', 'TSMDInitF', 'ASWInitF'
            ]
        }
    )


def get_soilInit_data(plo_file: str) -> xr.DataArray:
    """
    Load and parse soil initialization data from PLO XML file.

    Parameters
    ----------
    plo_file : str
        Path to PLO file

    Returns
    -------
    xr.DataArray
        DataArray containing soil initialization data with spatial dimensions (y, x, band)
        from Build section coordinates
    """
    # Check if file exists
    if not os.path.exists(plo_file):
        raise FileNotFoundError(f"Required file '{plo_file}' not found!")

    # Read XML file as string
    with open(plo_file, 'r', encoding='utf-8') as f:
        xml_string = f.read()

    # Extract coordinates from Build section
    site_root = etree.fromstring(xml_string.encode('utf-8'))
    build_elem = site_root.find('.//Build')
    lat = float(build_elem.get('latBL'))
    lon = float(build_elem.get('lonBL'))

    # Parse XML to xr data
    soil_init = parse_soilInit_data(xml_string)

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
