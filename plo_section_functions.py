"""
FullCAM PLO File Section Functions
Modular functions for creating individual sections of PLO files.
Each function generates XML for a specific section with proper Python docstrings.
"""

from typing import List

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _bool_to_xml(value: bool) -> str:
    """Convert Python bool to XML string format ('true'/'false')."""
    return "true" if value else "false"

# ============================================================================
# SECTION CREATION FUNCTIONS
# ============================================================================

def create_meta_section(
    nmME: str,
    savedByResearch: bool = True,
    savedByVersion: str = "",
    lockTime: str = "",
    lockId: str = "",
    lockOnME: str = "",
    notesME: str = ""
) -> str:
    """
    Create Meta section for PLO file with plot metadata.

    The Meta section contains file metadata about the plot including name,
    version information, locking status, and optional notes.

    Parameters
    ----------
    nmME : str
        Plot name shown in FullCAM UI. Required parameter.
        Use descriptive names with dates for tracking.

    savedByResearch : bool, optional
        Whether saved from research UI (default: True).
        - True = Simulates creation from FullCAM web-UI
        - False = Created by desktop application

    savedByVersion : str, optional
        Version of FullCAM that saved it (default: "").
        Empty string "" when created programmatically.

    lockTime : str, optional
        ISO timestamp of last modification (default: "").
        Empty string "" if not locked.

    lockId : str, optional
        User/system ID that locked the file (default: "").
        Empty string "" if not locked.

    lockOnME : str, optional
        Is file currently locked (default: "").
        - "false" or "" for newly created files
        - "true" when file is in use

    notesME : str, optional
        Optional plot notes/description (default: "").
        Empty string or text content.

    Returns
    -------
        XML string for Meta section.
    """
    notes_element = f"<notesME>{notesME}</notesME>" if notesME else "<notesME/>"

    savedByResearch_xml = _bool_to_xml(savedByResearch)

    return (f'<Meta nmME="{nmME}" savedByResearch="{savedByResearch_xml}" '
            f'savedByVersion="{savedByVersion}" lockTime="{lockTime}" '
            f'lockId="{lockId}" lockOnME="{lockOnME}">{notes_element}</Meta>')


def create_config_section(
    tPlot: str = "CompF",
    rothCVers: str = "Vers263",
    tTreeProd: str = "TYF",
    userCalcFPI: bool       = False,
    userCalcModASW: bool    = False,
    userCalcModFrost: bool  = False,
    userCalcModTemp: bool   = False,
    userCropGrade: bool     = False,
    userDispEner: bool      = False,
    userDispProd: bool      = False,
    userEcon: bool          = False,
    userEventIrrA: bool     = False,
    userEventIrrF: bool     = False,
    userEventManA: bool     = False,
    userEventManF: bool     = False,
    userEventNFeA: bool     = True,
    userEventNFeF: bool     = True,
    userLogGrade: bool      = False,
    userMulchA: bool        = False,
    userMulchF: bool        = False,
    userN: bool             = False,
    userOpti: bool          = False,
    userSens: bool          = False,
    userSoilMnrl: bool      = True
) -> str:
    """
    Create Config section for PLO file with simulation configuration.

    The Config section controls calculation modules, parameters, and the type
    of analysis to be performed.

    Parameters
    ----------
    tPlot : str, optional
        Plot type determining analysis type (default: "CompF").
        - "CompF" = Forest system (comprehensive forest)
        - "SoilF" = Forest soil analysis only
        - "CompA" = Agricultural system
        - "SoilA" = Agricultural soil analysis only
        - "CompM" = Mixed (forest and agricultural) system

    rothCVers : str, optional
        Carbon calculation version (default: "Vers263").
        "Vers263" = Version 2.6.3 (current standard)

    tTreeProd : str, optional
        Tree productivity model (default: "TYF").
        "TYF" = Timber Yield Formula (standard for forests)

    userCalcFPI : bool, optional
        Enable custom Forest Productivity Index (default: False).

    userCalcModASW : bool, optional
        Enable custom available soil water modifier (default: False).

    userCalcModFrost : bool, optional
        Enable custom frost modifier (default: False).

    userCalcModTemp : bool, optional
        Enable custom temperature modifier (default: False).

    userCropGrade : bool, optional
        Enable crop grading (default: False).

    userDispEner : bool, optional
        Enable energy disposition (default: False).

    userDispProd : bool, optional
        Enable productivity disposition (default: False).

    userEcon : bool, optional
        Enable economic analysis (default: False).

    userEventIrrA : bool, optional
        Enable agricultural irrigation events (default: False).

    userEventIrrF : bool, optional
        Enable forest irrigation events (default: False).

    userEventManA : bool, optional
        Enable agricultural management events (default: False).

    userEventManF : bool, optional
        Enable forest management events (default: False).

    userEventNFeA : bool, optional
        Enable agricultural fertilization events (default: True).
        True = Include nitrogen fertilizer for crops

    userEventNFeF : bool, optional
        Enable forest fertilization events (default: True).
        True = Include nitrogen fertilizer applications

    userLogGrade : bool, optional
        Enable log grading (default: False).

    userMulchA : bool, optional
        Enable agricultural mulch customization (default: False).

    userMulchF : bool, optional
        Enable forest mulch customization (default: False).

    userN : bool, optional
        Enable nitrogen cycle calculations (default: False).

    userOpti : bool, optional
        Enable optimization mode (default: False).

    userSens : bool, optional
        Enable sensitivity analysis mode (default: False).

    userSoilMnrl : bool, optional
        Enable user-defined soil mineral parameters (default: True).
        - True = Allow manual soil input
        - False = Use default soil properties

    Returns
    -------
        XML string for Config section.
    """
    return (f'<Config tPlot="{tPlot}" userSoilMnrl="{_bool_to_xml(userSoilMnrl)}" '
            f'userMulchF="{_bool_to_xml(userMulchF)}" userMulchA="{_bool_to_xml(userMulchA)}" '
            f'tTreeProd="{tTreeProd}" userCalcFPI="{_bool_to_xml(userCalcFPI)}" '
            f'userCalcModTemp="{_bool_to_xml(userCalcModTemp)}" userCalcModASW="{_bool_to_xml(userCalcModASW)}" '
            f'userCalcModFrost="{_bool_to_xml(userCalcModFrost)}" userN="{_bool_to_xml(userN)}" '
            f'userDispEner="{_bool_to_xml(userDispEner)}" userDispProd="{_bool_to_xml(userDispProd)}" '
            f'userEventIrrF="{_bool_to_xml(userEventIrrF)}" userEventIrrA="{_bool_to_xml(userEventIrrA)}" '
            f'userEventNFeF="{_bool_to_xml(userEventNFeF)}" userEventNFeA="{_bool_to_xml(userEventNFeA)}" '
            f'userEventManF="{_bool_to_xml(userEventManF)}" userEventManA="{_bool_to_xml(userEventManA)}" '
            f'rothCVers="{rothCVers}" userSens="{_bool_to_xml(userSens)}" '
            f'userOpti="{_bool_to_xml(userOpti)}" userEcon="{_bool_to_xml(userEcon)}" '
            f'userLogGrade="{_bool_to_xml(userLogGrade)}" userCropGrade="{_bool_to_xml(userCropGrade)}"/>')


def create_timing_section(
    stYrYTZ: str = "2010",
    enYrYTZ: str = "2100",
    stepsPerYrYTZ: str = "110",
    dailyTimingTZ: bool = False,
    useDaysPerStepDTZ: bool = True,
    daysPerStepDTZ: str = "1",
    stepsPerDayDTZ: str = "1",
    outputFreqDTZ: str = "Daily",
    stepsPerOutDTZ: str = "1",
    firstOutStepDTZ: str = "1",
    tStepsYTZ: str = "Yearly",
    stStepInStYrYTZ: str = "",
    enStepInEnYrYTZ: str = "",
    stepsPerOutYTZ: str = "1",
    firstOutStepYTZ: str = "1"
) -> str:
    """
    Create Timing section for PLO file with simulation timing configuration.

    The Timing section defines the simulation period, time steps, and output
    frequency for the FullCAM model run.

    Parameters
    ----------
    stYrYTZ : str, optional
        Starting year for simulation (default: "2010").

    enYrYTZ : str, optional
        Ending year for simulation (default: "2100").

    stepsPerYrYTZ : str, optional
        Steps per year for yearly calculation (default: "110").

    dailyTimingTZ : bool, optional
        Use daily time stepping (default: False).

    useDaysPerStepDTZ : bool, optional
        Define days per simulation step (default: True).

    daysPerStepDTZ : str, optional
        Number of days per step (default: "1").

    stepsPerDayDTZ : str, optional
        Number of steps per day (default: "1").

    outputFreqDTZ : str, optional
        Output frequency (default: "Daily").
        - "Daily" = Output daily results
        - "Monthly" = Output monthly aggregates
        - "Yearly" = Output yearly results

    stepsPerOutDTZ : str, optional
        Steps between outputs (default: "1").

    firstOutStepDTZ : str, optional
        First step to output (default: "1").

    tStepsYTZ : str, optional
        Time steps per year (default: "Yearly").
        - "Yearly" = Single annual timestep
        - "Monthly" = 12 monthly timesteps

    stStepInStYrYTZ : str, optional
        Starting step in year (default: "").

    enStepInEnYrYTZ : str, optional
        Ending step in final year (default: "").

    stepsPerOutYTZ : str, optional
        Yearly output interval (default: "1").

    firstOutStepYTZ : str, optional
        First year to output (default: "1").

    Returns
    -------
        XML string for Timing section.
    """
    return (f'<Timing dailyTimingTZ="{_bool_to_xml(dailyTimingTZ)}" '
            f'useDaysPerStepDTZ="{_bool_to_xml(useDaysPerStepDTZ)}" '
            f'daysPerStepDTZ="{daysPerStepDTZ}" '
            f'stepsPerDayDTZ="{stepsPerDayDTZ}" '
            f'outputFreqDTZ="{outputFreqDTZ}" '
            f'stepsPerOutDTZ="{stepsPerOutDTZ}" '
            f'firstOutStepDTZ="{firstOutStepDTZ}" '
            f'tStepsYTZ="{tStepsYTZ}" '
            f'stepsPerYrYTZ="{stepsPerYrYTZ}" '
            f'stYrYTZ="{stYrYTZ}" '
            f'stStepInStYrYTZ="{stStepInStYrYTZ}" '
            f'enYrYTZ="{enYrYTZ}" '
            f'enStepInEnYrYTZ="{enStepInEnYrYTZ}" '
            f'stepsPerOutYTZ="{stepsPerOutYTZ}" '
            f'firstOutStepYTZ="{firstOutStepYTZ}"/>')


def create_build_section(
    lonBL: float,
    latBL: float,
    frCat: str = "null",
    applyDownloadedData: bool = True,
    areaBL: str = "OneKm",
    frFracBL: str = ""
) -> str:
    """
    Create Build section for PLO file with geographic location configuration.

    The Build section defines the geographic location and spatial parameters
    for data retrieval and averaging.

    Parameters
    ----------
    lonBL : float
        Longitude in decimal degrees. Required parameter.
        Negative = Western hemisphere

    latBL : float
        Latitude in decimal degrees. Required parameter.
        Negative = Southern hemisphere

    frCat : str, optional
        Forest category (default: "null").
        - "null" = All categories
        - "Plantation" = Commercial plantation
        - "EnvMallee" = Environmental plantings
        - "ERF" = Emissions Reduction Fund method
        - "ERFH" = ERF with EMP-specific calibrations
        - "MVG" = Major Vegetation Groups

    applyDownloadedData : bool, optional
        Use downloaded spatial data (default: True).
        - True = Apply API-downloaded data
        - False = Use manual/default values

    areaBL : str, optional
        Spatial averaging area (default: "OneKm").
        - "Cell" = Single grid cell (no averaging)
        - "Hectare" = 1 hectare
        - "OneKm" = 1 km² (100 hectare)
        - "TwoKm" = 4 km² (400 hectare)
        - "ThreeKm" = 9 km² (900 hectare)
        - "FiveKm" = 25 km² (2500 hectare)

    frFracBL : str, optional
        Forest fraction (default: "").
        "" = Calculated from data

    Returns
    -------
        XML string for Build section.
    """
    return (f'<Build lonBL="{lonBL}" latBL="{latBL}" frCat="{frCat}" '
            f'applyDownloadedData="{_bool_to_xml(applyDownloadedData)}" '
            f'areaBL="{areaBL}" frFracBL="{frFracBL}"/>')


def create_site_section(
    count: int,
    timeseries_list: List[str],
    tAirTemp: str = "Direct",
    tVPD: str = "",
    tSoilTemp: str = "",
    hasArea: bool = False,
    userHasArea: bool = False,
    siteArea: str = "",
    conditIrrigOnF: bool = False,
    conditIrrigOnA: bool = False,
    siteMultStemF: str = "1.0",
    siteMultBranF: str = "1.0",
    siteMultBarkF: str = "1.0",
    siteMultLeafF: str = "1.0",
    siteMultCortF: str = "1.0",
    siteMultFirtF: str = "1.0",
    siteMultGbfrA: str = "1.0",
    siteMultStlkA: str = "1.0",
    siteMultLeafA: str = "1.0",
    siteMultCortA: str = "1.0",
    siteMultFirtA: str = "1.0",
    maxAbgMF: str = "",
    maxAbgMA: str = "",
    latitude3PG: str = "",
    molPARPerMJRad: str = "",
    plantMPerMolC: str = "",
    upstreamCRatio: str = "",
    fpiAvgLT: str = ""
) -> str:
    """
    Create Site section for PLO file with site parameters and time series.

    The Site section is a container for site-level parameters and multiple
    time series datasets for climate, productivity, and management.

    Parameters
    ----------
    count : int
        Number of time series included. Required parameter.

    timeseries_list : list of str
        List of TimeSeries XML strings to include. Required parameter.
        Each element should be a complete TimeSeries XML element.

    tAirTemp : str, optional
        Air temperature input type (default: "Direct").

    tVPD : str, optional
        Vapor Pressure Deficit input type (default: "").

    tSoilTemp : str, optional
        Soil temperature input type (default: "").

    hasArea : bool, optional
        Site has area defined (default: False).

    userHasArea : bool, optional
        User-specified area (default: False).

    siteArea : str, optional
        Site area in hectares (default: "").

    conditIrrigOnF : bool, optional
        Conditional irrigation for forest (default: False).

    conditIrrigOnA : bool, optional
        Conditional irrigation for agriculture (default: False).

    siteMultStemF : str, optional
        Multiplier for stem carbon fraction (default: "1.0").

    siteMultBranF : str, optional
        Multiplier for branch carbon (default: "1.0").

    siteMultBarkF : str, optional
        Multiplier for bark carbon (default: "1.0").

    siteMultLeafF : str, optional
        Multiplier for leaf carbon (default: "1.0").

    siteMultCortF : str, optional
        Multiplier for cortex carbon (default: "1.0").

    siteMultFirtF : str, optional
        Multiplier for fine root carbon (default: "1.0").

    siteMultGbfrA : str, optional
        Multiplier for agricultural grain/fruit (default: "1.0").

    siteMultStlkA : str, optional
        Multiplier for agricultural stalk (default: "1.0").

    siteMultLeafA : str, optional
        Multiplier for agricultural leaf (default: "1.0").

    siteMultCortA : str, optional
        Multiplier for agricultural cortex (default: "1.0").

    siteMultFirtA : str, optional
        Multiplier for agricultural fine root (default: "1.0").

    maxAbgMF : str, optional
        Maximum aboveground biomass for forest in Mg/ha (default: "").

    maxAbgMA : str, optional
        Maximum aboveground biomass for agriculture (default: "").

    latitude3PG : str, optional
        Latitude for 3PG model (default: "").

    molPARPerMJRad : str, optional
        Moles PAR per MJ radiation (default: "").

    plantMPerMolC : str, optional
        Plant mass per mole carbon (default: "").

    upstreamCRatio : str, optional
        Upstream carbon ratio (default: "").

    fpiAvgLT : str, optional
        Average Forest Productivity Index (default: "").

    Returns
    -------
        XML string for complete Site section including all TimeSeries.
    """
    site_open = (f'<Site count="{count}" tAirTemp="{tAirTemp}" '
                 f'tVPD="{tVPD}" tSoilTemp="{tSoilTemp}" '
                 f'hasArea="{_bool_to_xml(hasArea)}" userHasArea="{_bool_to_xml(userHasArea)}" '
                 f'siteArea="{siteArea}" '
                 f'conditIrrigOnF="{_bool_to_xml(conditIrrigOnF)}" '
                 f'conditIrrigOnA="{_bool_to_xml(conditIrrigOnA)}" '
                 f'siteMultStemF="{siteMultStemF}" '
                 f'siteMultBranF="{siteMultBranF}" '
                 f'siteMultBarkF="{siteMultBarkF}" '
                 f'siteMultLeafF="{siteMultLeafF}" '
                 f'siteMultCortF="{siteMultCortF}" '
                 f'siteMultFirtF="{siteMultFirtF}" '
                 f'siteMultGbfrA="{siteMultGbfrA}" '
                 f'siteMultStlkA="{siteMultStlkA}" '
                 f'siteMultLeafA="{siteMultLeafA}" '
                 f'siteMultCortA="{siteMultCortA}" '
                 f'siteMultFirtA="{siteMultFirtA}" '
                 f'maxAbgMF="{maxAbgMF}" maxAbgMA="{maxAbgMA}" '
                 f'latitude3PG="{latitude3PG}" '
                 f'molPARPerMJRad="{molPARPerMJRad}" '
                 f'plantMPerMolC="{plantMPerMolC}" '
                 f'upstreamCRatio="{upstreamCRatio}" '
                 f'fpiAvgLT="{fpiAvgLT}">')

    timeseries_content = "\n".join(timeseries_list)

    return f"{site_open}\n{timeseries_content}\n</Site>"


def create_timeseries(
    tInTS: str,
    rawTS_values: List[float],
    yr0TS: str = "2010",
    nYrsTS: str = "1",
    dataPerYrTS: str = "12",
    tExtrapTS: str = "AvgYr",
    tOriginTS: str = "Calendar",
    nDecPlacesTS: str = "1",
    colWidthTS: str = "50",
    multTS: str = "1.0",
    showGraphTS: bool = True,
    winstate_L: str = "10",
    winstate_T: str = "120",
    winstate_clientW: str = "702",
    winstate_clientH: str = "450",
    winstate_ws: str = "Normal"
) -> str:
    """
    Create TimeSeries element for climate, productivity, or management data.

    TimeSeries elements contain temporal data such as temperature, rainfall,
    irrigation, or other time-varying parameters.

    Parameters
    ----------
    tInTS : str
        Time series input type. Required parameter.
        Common types:
        - "avgAirTemp" = Average air temperature (°C monthly)
        - "rainfall" = Rainfall (mm monthly)
        - "openPanEvap" = Open pan evaporation (mm monthly)
        - "forestProdIx" = Forest Productivity Index (annual)
        - "defnitIrrigA" = Definite irrigation for agriculture (mm)
        - "conditIrrigA" = Conditional irrigation (mm)
        - "soilTemp" = Soil temperature (°C)
        - "VPD" = Vapor Pressure Deficit
        - "solarRad" = Solar radiation
        - "fertility" = Soil fertility modifier

    rawTS_values : list
        List of numeric values or empty strings. Required parameter.
        Empty cells shown as empty string "".

    yr0TS : str, optional
        Starting year (default: "2010").

    nYrsTS : str, optional
        Number of years in time series (default: "1").

    dataPerYrTS : str, optional
        Data points per year (default: "12").
        - "12" = Monthly data (12 values per year)
        - "1" = Annual data (1 value per year)

    tExtrapTS : str, optional
        Extrapolation method (default: "AvgYr").
        - "AvgYr" = Average year (long-term mean)
        - "HotYr" = Hot year scenario
        - "WetYr" = Wet year scenario
        - "DryYr" = Dry year scenario

    tOriginTS : str, optional
        Time reference system (default: "Calendar").
        - "Calendar" = Calendar year (Jan-Dec)
        - "Water" = Water year (varies by region)

    nDecPlacesTS : str, optional
        Decimal places in data (default: "1").

    colWidthTS : str, optional
        Column width for UI display (default: "50").

    multTS : str, optional
        Multiplier for values (default: "1.0").

    showGraphTS : bool, optional
        Display graph in UI (default: True).

    winstate_L : str, optional
        Window left position (default: "10").

    winstate_T : str, optional
        Window top position (default: "120").

    winstate_clientW : str, optional
        Window client width (default: "702").

    winstate_clientH : str, optional
        Window client height (default: "450").

    winstate_ws : str, optional
        Window state (default: "Normal").

    Returns
    -------
        XML string for TimeSeries element.
    """
    # Convert values list to comma-separated string
    rawTS_str = ",".join(str(v) if v != "" else "" for v in rawTS_values)
    count = len(rawTS_values)

    return (f'<TimeSeries tInTS="{tInTS}" tExtrapTS="{tExtrapTS}" '
            f'tOriginTS="{tOriginTS}" yr0TS="{yr0TS}" nYrsTS="{nYrsTS}" '
            f'dataPerYrTS="{dataPerYrTS}" nDecPlacesTS="{nDecPlacesTS}" '
            f'colWidthTS="{colWidthTS}" multTS="{multTS}" '
            f'showGraphTS="{_bool_to_xml(showGraphTS)}">\n'
            f'<WinState L="{winstate_L}" T="{winstate_T}" '
            f'clientW="{winstate_clientW}" clientH="{winstate_clientH}" '
            f'ws="{winstate_ws}"/>\n'
            f'<rawTS count="{count}">{rawTS_str}</rawTS>\n'
            f'</TimeSeries>')


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    # Example: Create Meta section
    meta = create_meta_section("My_Test_Plot_2025", notesME="Example plot for testing")
    print("Meta Section:")
    print(meta)
    print("\n" + "="*80 + "\n")

    # Example: Create Config section
    config = create_config_section(tPlot="CompF", userMulchF="true")
    print("Config Section:")
    print(config)
    print("\n" + "="*80 + "\n")

    # Example: Create Timing section
    timing = create_timing_section(stYrYTZ="2020", enYrYTZ="2050")
    print("Timing Section:")
    print(timing)
    print("\n" + "="*80 + "\n")

    # Example: Create Build section
    build = create_build_section(148.16, -35.61, frCat="Plantation")
    print("Build Section:")
    print(build)
    print("\n" + "="*80 + "\n")

    # Example: Create TimeSeries
    temps = [15.68, 17.65, 13.03, 10.66, 5.53, 4.72,
             2.97, 3.65, 4.72, 9.66, 11.96, 15.80]
    ts1 = create_timeseries("avgAirTemp", temps, yr0TS="2020", nYrsTS="1")
    print("TimeSeries Section:")
    print(ts1)
    print("\n" + "="*80 + "\n")

    # Example: Create Site section with TimeSeries
    rainfall = [172.91, 42.76, 91.18, 213.70, 130.61, 157.46,
                119.02, 309.44, 264.66, 115.63, 194.56, 89.46]
    ts2 = create_timeseries("rainfall", rainfall, yr0TS="2020", nYrsTS="1")

    site = create_site_section(2, [ts1, ts2], maxAbgMF="979.24",
                              fpiAvgLT="8.85")
    print("Site Section (with TimeSeries):")
    print(site)
