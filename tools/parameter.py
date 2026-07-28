

RES_FACTOR = 10
'''
Resolution factor applied to LUTO's spatial template (`data/lumap.tif`, 0.01 deg ~ 1.1 km):
1 keeps every cell (~1.1 km), 10 samples every tenth (~11 km).

Shared by the run and the conversion scripts. They must agree, otherwise the conversion
builds a grid at one resolution and looks for points simulated at another.
'''


SIM_LENGTH = 100
'''
Length of a future-scenario simulation in years; its start year comes from
`FUTURE_DATA_YR_RANGES`.
'''


HIST_SIM_YEAR_START = 2010
HIST_SIM_YEAR_END = 2100
'''
Simulation period of the historical runs. Note this is 90 years rather than `SIM_LENGTH`,
so it cannot be derived from it.

Shared by the run and the conversion scripts, since the period is part of the result
filename and therefore has to match on both sides.
'''


SSPS = ['historical', 'SSP126', 'SSP245', 'SSP370', 'SSP585']
'''
Valid `ssp` values. 'historical' is the observed climate held in
`data/data_assembled/siteinfo_cache.nc`; the others are the future scenarios whose layers
live in `data/future_climate_data/{var}/{ssp}/`.

`historical` is the only scenario that can be used with the FullCAM REST API, because it is 
the only one that has been run and cached. The future scenarios are used to assemble site 
datasets for running FullCAM locally.
'''


FUTURE_DATA_YR_RANGES = {
    2030: '2021_2040',
    2050: '2041_2060',
    2070: '2061_2080',
    2090: '2081_2100',
}
'''
Maps a simulation start year to the 20-year future-climate window it is driven by.
The values match the year postfix of the files in `data/future_climate_data/`.

These ranges are determined by the CMIP6 future-climate data available at 2025, which is at most 2100.
The ranges may be updated in the future if more recent data is added to the cache.
'''


def carbon_csv_name(
    lon,
    lat,
    specId: int,
    specCat: str,
    ssp: str,
    data_year_range: str,
    sim_year_start: int,
    sim_year_end: int
) -> str:
    '''
    Filename of the simulation result CSV for one location/species/scenario/period.

    Every run is tagged with both the climate data it was driven by and the period it was
    simulated over, so no two runs collide. Historical runs use ssp='historical' with the
    year span held in `siteinfo_cache.nc`, e.g. '1970_2023'.

    Parameters
    ----------
    lon, lat : float
        Coordinates of the site.
    specId : int
        Species ID; see `SPECIES_MAP`.
    specCat : str
        Planting category; see `SPECIES_GEOMETRY`.
    ssp : str
        Climate scenario driving the run; one of `SSPS`.
    data_year_range : str
        Year span of the input climate data, e.g. '1970_2023' or '2021_2040'.
    sim_year_start, sim_year_end : int
        First and last year of the simulation itself, e.g. 2050 and 2150.

    Returns
    -------
        The CSV basename (no directory).
    '''
    return (
        f'df_{lon}_{lat}_specId_{specId}_specCat_{specCat}'
        f'_ssp_{ssp}_InData_{data_year_range}_SIM_YR_{sim_year_start}_{sim_year_end}.csv'
    )


SPECIES_GEOMETRY = {
    7:  ['BeltH', 'BlockES', 'Water'],        # 'BeltL' is excluded because LUTO not considering low density belts
    8:  ['Belt', 'Block'],
    23: ['BeltHW', 'BlockES'],                # 'BeltL' is excluded; 'BeltHW' is the same as 'BeltH' for Mallee species
}
'''
This dictionary maps SPECIES_ID to a list of valid SPECIES_CAT values.
Used for downloading data from the FullCAM REST API for multiple species categories.
'''



SPECIES_MAP = {
    0: "Acacia Forest and Woodlands",
    1: "Acacia mangium",
    2: "Acacia Open Woodland",
    3: "Acacia Shrubland",
    4: "Callitris Forest and Woodlands",
    5: "Casuarina Forest and Woodland",
    6: "Chenopod Shrub; Samphire Shrub and Forbland",
    7: "Environmental plantings",
    8: "Eucalyptus globulus",
    9: "Eucalyptus grandis",
    10: "Eucalyptus Low Open Forest",
    11: "Eucalyptus nitens",
    12: "Eucalyptus Open Forest",
    13: "Eucalyptus Open Woodland",
    14: "Eucalyptus Tall Open Forest",
    15: "Eucalyptus urophylla or pellita",
    16: "Eucalyptus Woodland",
    17: "Heath",
    22: "Low Closed Forest and Closed Shrublands",
    23: "Mallee eucalypt species",
    24: "Mallee Woodland and Shrubland",
    25: "Mangrove",
    27: "Melaleuca Forest and Woodland",
    31: "Native species and revegetation <500mm rainfall",
    32: "Native species and revegetation >=500mm rainfall",
    33: "Native Species Regeneration <500mm rainfall",
    34: "Native Species Regeneration >=500mm rainfall",
    38: "Other acacia",
    39: "Other eucalypts",
    40: "Other Forests and Woodlands",
    41: "Other non-eucalypts hardwoods",
    42: "Other Shrublands",
    43: "Other softwoods",
    45: "Pinus hybrids",
    46: "Pinus pinaster",
    47: "Pinus radiata",
    48: "Rainforest and vine thickets",
    49: "Tropical Eucalyptus woodlands/grasslands",
    51: "Unclassified Native vegetation",
}
'''
This dictionary maps SPECIES_ID to human-readable species names.
Used for labeling and interpreting species data in FullCAM analyses.
'''