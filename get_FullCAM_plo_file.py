"""
FullCAM PLO File Assembler - Based on Real PLO File Structure
Constructs FullCAM plot files by combining XML sections.
Based on FullCAM PR External API Databuilder API v0.1 and real example file.

NOTE: Modular section functions are now available in plo_section_functions.py
      Use those functions for creating individual sections programmatically.
"""

from plo_section_functions import (
    create_meta_section,
    create_config_section,
    create_timing_section,
    create_build_section,
    create_site_section,
    create_timeseries
)

# ============================================================================
# ---- HEAD ----
# ============================================================================
PLO_HEAD = r'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
"""
XML declaration header. Fixed for all PLO files.
- Required XML header
- Specifies UTF-8 encoding
- Standalone="yes" indicates no external DTD
"""

# ============================================================================
# ---- META ----
# ============================================================================

PLO_META = r'<Meta nmME="My_Plot_09_10_2025_10_00_33" savedByResearch="true" savedByVersion="" lockTime="" lockId="" lockOnME=""><notesME/></Meta>'
"""
File metadata about the plot file.

Arguments:
    - `nmME` (string): Plot name shown in FullCAM UI
      * Example: "My_Plot_09_10_2025_10_00_33"
      * Use descriptive names with dates for tracking
    
    - `savedByResearch` (boolean: "true"/"false") 
      * "true" = Simulates creation from FullCAM web-UI
      * "false" = Created by desktop application
    
    - `savedByVersion` (string): Version of FullCAM that saved it
      * Empty string "" when created programmatically
      * Example: "8.24.01.0000" if from FullCAM application
    
    - `lockTime` (string): ISO timestamp of last modification
      * Empty string "" if not locked
      * Tracks when file was last edited
    
    - `lockId` (string): User/system ID that locked the file
      * Empty string "" if not locked
    
    - `lockOnME` (boolean: "true"/"false"): Is file currently locked?
      * "false" for newly created files
      * "true" when file is in use
    
    - `notesME` (XML element): Optional plot notes/description
      * <notesME/> for no notes
      * <notesME>Your description here</notesME> with content
"""

# ============================================================================
# ---- CONFIG ----
# ============================================================================
"""
Simulation configuration controlling calculation modules and parameters.

Arguments:
    - `tPlot` (string): Plot type - determines analysis type
      * "CompF" = Forest system (comprehensive forest)
      * "SoilF" = Forest soil analysis only
      * "CompA" = Agricultural system
      * "SoilA" = Agricultural soil analysis only
      * "CompM" = Mixed (forest and agricultural) system
    
    - `userSoilMnrl` (boolean): Enable user-defined soil mineral parameters
      * "true" = Allow manual soil input
      * "false" = Use default soil properties
    
    - `userMulchF` (boolean): Enable forest mulch customization
    - `userMulchA` (boolean): Enable agricultural mulch customization
    
    - `tTreeProd` (string): Tree productivity model
      * "TYF" = Timber Yield Formula (standard for forests)
    
    - `userCalcFPI` (boolean): Enable custom Forest Productivity Index
    - `userCalcModTemp` (boolean): Enable custom temperature modifier
    - `userCalcModASW` (boolean): Enable custom available soil water modifier
    - `userCalcModFrost` (boolean): Enable custom frost modifier
    
    - `userN` (boolean): Enable nitrogen cycle calculations
    - `userDispEner` (boolean): Enable energy disposition
    - `userDispProd` (boolean): Enable productivity disposition
    
    - `userEventIrrF` (boolean): Enable forest irrigation events
    - `userEventIrrA` (boolean): Enable agricultural irrigation events
    - `userEventNFeF` (boolean): Enable forest fertilization events
      * "true" = Include nitrogen fertilizer applications
    - `userEventNFeA` (boolean): Enable agricultural fertilization events
      * "true" = Include nitrogen fertilizer for crops
    
    - `userEventManF` (boolean): Enable forest management events
    - `userEventManA` (boolean): Enable agricultural management events
    
    - `rothCVers` (string): Carbon calculation version
      * "Vers263" = Version 2.6.3 (current standard)
    
    - `userSens` (boolean): Enable sensitivity analysis mode
    - `userOpti` (boolean): Enable optimization mode
    - `userEcon` (boolean): Enable economic analysis
    - `userLogGrade` (boolean): Enable log grading
    - `userCropGrade` (boolean): Enable crop grading
"""
PLO_CONFIG = r'<Config tPlot="CompF" userSoilMnrl="true" userMulchF="false" userMulchA="false" tTreeProd="TYF" userCalcFPI="false" userCalcModTemp="false" userCalcModASW="false" userCalcModFrost="false" userN="false" userDispEner="false" userDispProd="false" userEventIrrF="false" userEventIrrA="false" userEventNFeF="true" userEventNFeA="true" userEventManF="false" userEventManA="false" rothCVers="Vers263" userSens="false" userOpti="false" userEcon="false" userLogGrade="false" userCropGrade="false"/>'


# ============================================================================
# ---- TIMING ----
# ============================================================================
"""
Simulation timing and output frequency configuration.

Arguments:
    - `dailyTimingTZ` (boolean): Use daily time stepping
      * "false" = Don't use daily steps (use yearly)
    
    - `useDaysPerStepDTZ` (boolean): Define days per simulation step
      * "true" = Specify daysPerStepDTZ value
    
    - `daysPerStepDTZ` (integer): Number of days per step
      * 1 = Daily simulation steps
    
    - `stepsPerDayDTZ` (integer): Number of steps per day
      * 1 = One step per day
    
    - `outputFreqDTZ` (string): Output frequency
      * "Daily" = Output daily results
      * "Monthly" = Output monthly aggregates
      * "Yearly" = Output yearly results
    
    - `stepsPerOutDTZ` (integer): Steps between outputs
      * 1 = Output every step
    
    - `firstOutStepDTZ` (integer): First step to output
      * 1 = Start output from first step
    
    - `tStepsYTZ` (string): Time steps per year
      * "Yearly" = Single annual timestep
      * "Monthly" = 12 monthly timesteps
    
    - `stepsPerYrYTZ` (integer): Steps per year for yearly calculation
      * 110 = Number of internal calculation steps per year
    
    - `stYrYTZ` (string): Starting year for simulation
      * "2010" = Start from 2010
    
    - `stStepInStYrYTZ` (string): Starting step in year
      * "" = Start from beginning of year
    
    - `enYrYTZ` (string): Ending year for simulation
      * "2100" = End at year 2100
    
    - `enStepInEnYrYTZ` (string): Ending step in final year
      * "" = Run through end of year
    
    - `stepsPerOutYTZ` (integer): Yearly output interval
      * 1 = Output every year
    
    - `firstOutStepYTZ` (integer): First year to output
      * 1 = Output from first year
"""
PLO_TIMING = r'<Timing dailyTimingTZ="false" useDaysPerStepDTZ="true" daysPerStepDTZ="1" stepsPerDayDTZ="1" outputFreqDTZ="Daily" stepsPerOutDTZ="1" firstOutStepDTZ="1" tStepsYTZ="Yearly" stepsPerYrYTZ="110" stYrYTZ="2010" stStepInStYrYTZ="" enYrYTZ="2100" enStepInEnYrYTZ="" stepsPerOutYTZ="1" firstOutStepYTZ="1"/>'


# ============================================================================
# ---- BUILD ----
# ============================================================================
"""
Geographic location and data source configuration.

Arguments:
    - `lonBL` (float): Longitude in decimal degrees
      * Example: "148.16" = ~148°E Australia
      * Negative = Western hemisphere
    
    - `latBL` (float): Latitude in decimal degrees
      * Example: "-35.61" = ~35.6°S Australia
      * Negative = Southern hemisphere
    
    - `frCat` (string): Forest category
      * "null" = All categories
      * "Plantation" = Commercial plantation
      * "EnvMallee" = Environmental plantings
      * "ERF" = Emissions Reduction Fund method
    
    - `applyDownloadedData` (boolean): Use downloaded spatial data
      * "true" = Apply API-downloaded data
      * "false" = Use manual/default values
    
    - `areaBL` (string): Spatial averaging area
      * "Cell" = Single grid cell (no averaging)
      * "Hectare" = 1 hectare
      * "OneKm" = 1 km² (100 hectare)
      * "TwoKm" = 4 km² (400 hectare)
      * "ThreeKm" = 9 km² (900 hectare)
      * "FiveKm" = 25 km² (2500 hectare)
    
    - `frFracBL` (string): Forest fraction
      * "" = Calculated from data
      * "0.5" = 50% forest coverage
"""
PLO_BUILD = r'<Build lonBL="148.16" latBL="-35.61" frCat="null" applyDownloadedData="true" areaBL="OneKm" frFracBL=""/>'


# ============================================================================
# ---- SITE (Container for time series data) ----
# ============================================================================
"""
Site-level parameters and multiple time series datasets.

Site container attributes:
    - `count` (integer): Number of time series included
      * "21" = Contains 21 different time series
    
    - `tAirTemp` (string): Air temperature input type
      * "Direct" = Use direct temperature measurements
    
    - `tVPD` (string): Vapor Pressure Deficit input type
      * "" = Not specified/not used
    
    - `tSoilTemp` (string): Soil temperature input type
      * "" = Not specified/not used
    
    - `hasArea` (boolean): Site has area defined
      * "false" = No specific area value
    
    - `userHasArea` (boolean): User-specified area
      * "false" = Using default/calculated area
    
    - `siteArea` (string): Site area in hectares
      * "" = Not specified
    
    - `conditIrrigOnF` (boolean): Conditional irrigation for forest
      * "false" = No conditional irrigation
    
    - `conditIrrigOnA` (boolean): Conditional irrigation for agriculture
      * "false" = No conditional irrigation
    
    - `siteMultStemF` (float): Multiplier for stem carbon fraction
      * 1.0 = Use standard value
      * >1.0 = Increase carbon allocation to stems
    
    - `siteMultBranF` (float): Multiplier for branch carbon
    - `siteMultBarkF` (float): Multiplier for bark carbon
    - `siteMultLeafF` (float): Multiplier for leaf carbon
    - `siteMultCortF` (float): Multiplier for cortex carbon
    - `siteMultFirtF` (float): Multiplier for fine root carbon
    
    - `maxAbgMF` (float): Maximum aboveground biomass for forest
      * Units: Mg/ha (megagrams per hectare)
      * ~979 = Upper biomass limit
    
    - `fpiAvgLT` (float): Average Forest Productivity Index
      * "8.85" = Long-term average FPI
      * Higher = More productive site
"""
PLO_SITE_OPEN = r'''<Site count="21" tAirTemp="Direct" tVPD="" tSoilTemp="" hasArea="false" userHasArea="false" siteArea="" conditIrrigOnF="false" conditIrrigOnA="false" siteMultStemF="1.0" siteMultBranF="1.0" siteMultBarkF="1.0" siteMultLeafF="1.0" siteMultCortF="1.0" siteMultFirtF="1.0" siteMultGbfrA="1.0" siteMultStlkA="1.0" siteMultLeafA="1.0" siteMultCortA="1.0" siteMultFirtA="1.0" maxAbgMF="979.239196777344" maxAbgMA="" latitude3PG="" molPARPerMJRad="" plantMPerMolC="" upstreamCRatio="" fpiAvgLT="8.848524500926347">'''
PLO_SITE_CLOSE = r'</Site>'


# ============================================================================
# ---- TIMESERIES (sub-elements of Site) ----
# ============================================================================
"""
Individual time series data for climate, productivity, and management.

TimeSeries attributes:
    - `tInTS` (string): Time series input type
      * "avgAirTemp" = Average air temperature (°C monthly)
      * "openPanEvap" = Open pan evaporation (mm monthly)
      * "rainfall" = Rainfall (mm monthly)
      * "forestProdIx" = Forest Productivity Index (annual)
      * "defnitIrrigA" = Definite irrigation for agriculture (mm)
      * "conditIrrigA" = Conditional irrigation (mm)
      * "soilTemp" = Soil temperature (°C)
      * "APAR" = Absorbed Photosynthetically Active Radiation
      * "modNutrTS" = Nutrition modifier
      * "modASWTS" = Available Soil Water modifier
      * "modVPDTS" = Vapor Pressure Deficit modifier
      * "eqmEvap" = Equilibrium evaporation
      * "fertility" = Soil fertility modifier
      * "conditIrrigF" = Conditional irrigation for forest
      * "defnitIrrigF" = Definite irrigation for forest
      * "solarRad" = Solar radiation
      * "frostNights" = Frost night frequency
      * "rangeAirTemp" = Temperature range
      * "minAirTemp" = Minimum air temperature
      * "VPD" = Vapor Pressure Deficit
      * "modFrostTS" = Frost modifier
    
    - `tExtrapTS` (string): Extrapolation method
      * "AvgYr" = Average year (long-term mean)
      * "HotYr" = Hot year scenario
      * "WetYr" = Wet year scenario
      * "DryYr" = Dry year scenario
    
    - `tOriginTS` (string): Time reference system
      * "Calendar" = Calendar year (Jan-Dec)
      * "Water" = Water year (varies by region)
    
    - `yr0TS` (string): Starting year
      * "1970" = Data starts from 1970
      * "2010" = Data starts from 2010
    
    - `nYrsTS` (string): Number of years in time series
      * "54" = 54 years of historical data
      * "1" = Single year of data
    
    - `dataPerYrTS` (string): Data points per year
      * "12" = Monthly data (12 values per year)
      * "1" = Annual data (1 value per year)
    
    - `nDecPlacesTS` (string): Decimal places in data
      * "1" = One decimal place
    
    - `multTS` (float): Multiplier for values
      * "1.0" = Use values as-is
      * "0.1" = Multiply values by 0.1
    
    - `showGraphTS` (boolean): Display graph in UI
      * "true" = Show graph
      * "false" = Don't show
    
    - rawTS element:
      * `count` (string): Number of values
        "12" = 12 monthly values
        "648" = 648 values (54 years x 12 months)
      * Comma-separated values (empty cells shown as ",")
"""

# Example temperature time series
PLO_TIMESERIES_AVGAIRTEMP = r'''<TimeSeries tInTS="avgAirTemp" tExtrapTS="AvgYr" tOriginTS="Calendar" yr0TS="1970" nYrsTS="54" dataPerYrTS="12" nDecPlacesTS="1" colWidthTS="50" multTS="1.0" showGraphTS="true">
<WinState L="10" T="120" clientW="702" clientH="450" ws="Normal"/>
<rawTS count="648">15.6766939163208,17.6457004547119,13.0314788818359,10.6618328094482,5.5325779914856,4.7167043685913,2.9683372974396,3.6464684009552,4.7204561233521,9.6593341827393,11.9635801315308,15.797492980957,16.9697036743164,17.1419982910156,16.1196765899658,11.215518951416,6.345778465271,3.344645023346,2.5280451774597,3.4042108058929,6.3536086082459,8.2175245285034,10.9185342788696,15.3036861419678</rawTS>
</TimeSeries>'''

# Example rainfall time series
PLO_TIMESERIES_RAINFALL = r'''<TimeSeries tInTS="rainfall" tExtrapTS="AvgYr" tOriginTS="Calendar" yr0TS="1970" nYrsTS="54" dataPerYrTS="12" nDecPlacesTS="1" colWidthTS="50" multTS="1.0" showGraphTS="true">
<WinState L="10" T="120" clientW="702" clientH="450" ws="Normal"/>
<rawTS count="648">172.907821655273,42.7635383605957,91.1767807006836,213.699859619141,130.612945556641,157.460464477539,119.015716552734,309.438323974609,264.658782958984,115.62580871582,194.557876586914,89.4626770019531</rawTS>
</TimeSeries>'''

# Placeholder for additional time series (monthly irrigation, etc.)
PLO_TIMESERIES_IRRIGATION = r'''<TimeSeries tInTS="defnitIrrigA" tExtrapTS="AvgYr" tOriginTS="Calendar" yr0TS="2010" nYrsTS="1" dataPerYrTS="12" nDecPlacesTS="1" colWidthTS="50" multTS="1.0" showGraphTS="true">
<WinState L="10" T="83" clientW="702" clientH="450" ws="Normal"/>
<rawTS count="12">0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0</rawTS>
</TimeSeries>'''


# ============================================================================
# ---- SPECIESFOREST (within SpeciesForestSet) ----
# ============================================================================
"""
Species-specific carbon partitioning and growth parameters.

Arguments:
    - `idSP` (string): Species ID (e.g., "1")
    
    - `nmSP` (string): Species name
      * "Eucalyptus globulus"
      * "Pinus radiata"
      * "Acacia mangium"
    
    - `grthModeSP` (string): Growth model type
      * "Yield" = Timber Yield Formula
      * "Growth" = Generic growth model
    
    - `tAgeIxSP` (string): Age calculation method
      * "AvgAge" = Use average age
      * "TopHt" = Use top height
    
    - `idRegimeSP` (string): Associated management regime ID
    
    - `mvgTreeId` (string): Major Vegetation Group ID
      * "99" = Eucalyptus type
      * "12" = Pine type
    
    - `pltnType` (string): Plantation type
      * "Hardwood" = Eucalyptus, Acacia
      * "Softwood" = Pine
      * "Other" = Mixed/native species
    
    - `tSpecFrCat` (string): Forest category
      * "Plantation" = Commercial plantation
      * "EnvMallee" = Environmental/native
      * "ERF" = Emissions Reduction Fund
    
    - Carbon fractions (CFrac*) - proportion of biomass that is carbon:
      * `CFracStemF` (float): Stem wood = ~0.5
      * `CFracBranF` (float): Branches = ~0.468
      * `CFracBarkF` (float): Bark = ~0.487
      * `CFracLeafF` (float): Foliage = ~0.529
      * `CFracCortF` (float): Cortex = ~0.492
      * `CFracFirtF` (float): Fine/coarse roots = ~0.461
    
    - Turnover fractions (turnFrac*) - annual loss rate:
      * `turnFracCortF` (float): Annual cortex loss %
      * `turnFracFirtF` (float): Annual root loss %
      * Specified as monthly values (turnFracBranF01-12, etc.)
    
    - Decomposition parameters (bkdnFrac*):
      * Control breakdown rates of different wood types
      * "SDdwd" = Sound dead wood stem
      * "Chwd" = Coarse hardwood
      * "Blit" = Branch litter
      * "Llit" = Leaf litter
      * "Codr" = Coarse deadwood
      * "Fidr" = Fine deadwood
    
    - Atmosphere fractions (atmsFrac*):
      * Proportion released to atmosphere vs. staying in soil
"""
PLO_SPECIESFOREST = r'''<SpeciesForest idSP="1" nmSP="Eucalyptus globulus" grthModeSP="Yield" tAgeIxSP="AvgAge" curEdit="false" idRegimeSP="8" mvgTreeId="99" pltnType="Hardwood" tSpecFrCat="Plantation" CFracStemF="0.5" CFracBranF="0.468" CFracBarkF="0.487" CFracLeafF="0.529" CFracCortF="0.492" CFracFirtF="0.461" turnFracCortF="25.0" turnFracFirtF="1.0">
<notesSP/>
<Products>
<Product pdcmFrac="0" enerFrac="1" fillFrac="0" ldcmFrac="0" effcEner="0.2" effcFoss="0.8" cemrEner="1.0" cemrFoss="" makeProd="0.8" cemrProd="" makeDisp="" cemrDisp="0.8" MDispPerProd="1.0" LProdPerDisp="1.0" CFracProd="0.5" id="fuel"/>
<Product pdcmFrac="0.292893219" enerFrac="0" fillFrac="0" ldcmFrac="0" effcEner="0.2" effcFoss="0.8" cemrEner="1.0" cemrFoss="" makeProd="0.8" cemrProd="" makeDisp="" cemrDisp="0.8" MDispPerProd="1.0" LProdPerDisp="1.0" CFracProd="0.5" id="papr"/>
</Products>
</SpeciesForest>'''


# ============================================================================
# ---- DOCUMENTPLOT (Root element) ----
# ============================================================================
"""
Root XML element for complete plot document files.

Attributes:
    - `FileType` (string): Type of file
      * "FullCAM Plot" = Complete plot file
    
    - `Version` (string): Document format version
      * "5007" = FullCAM 2020 PR format
      * "5009" = FullCAM 2024 PR format (current)
    
    - `pageIxDO` (string): Page index
      * "1" through "10" = Page number for large documents
      * "10" = Page 10 in example file
    
    - `tDiagram` (string): Diagram type
      * "-1" = No specific diagram
"""
PLO_DOCUMENTPLOT_OPEN = r'<DocumentPlot FileType="FullCAM Plot " Version="5009" pageIxDO="10" tDiagram="-1">'
PLO_DOCUMENTPLOT_CLOSE = r'</DocumentPlot>'


# ============================================================================
# ---- SPECIESFORESTSET (Container) ----
# ============================================================================
"""
Container for one or more SpeciesForest elements.

Attributes:
    - `count` (string): Number of species included
      * "1" = Single species
      * "2+" = Multiple species options
    
    - `showOnlyInUse` (boolean): Show only active species
      * "false" = Show all species
      * "true" = Show only those in use
"""
PLO_SPECIESFORESTSET_OPEN = r'<SpeciesForestSet count="1" showOnlyInUse="false">'
PLO_SPECIESFORESTSET_CLOSE = r'</SpeciesForestSet>'


# ============================================================================
# ASSEMBLY FUNCTIONS
# ============================================================================

def assemble_plo_full(meta=None, config=None, timing=None, build=None, 
                      site_timeseries=None, speciesforest=None, 
                      additional_data=None):
    """
    Assemble a complete PLO plot document using DocumentPlot root element.
    
    Args:
        meta (str, optional): Custom meta section
        config (str, optional): Custom config section
        timing (str, optional): Custom timing section
        build (str, optional): Custom build section
        site_timeseries (str, optional): Site and TimeSeries sections
        speciesforest (str, optional): SpeciesForest and Product sections
        additional_data (str, optional): Other data sections
    
    Returns:
        str: Complete PLO XML document as string
    """
    # Use defaults if not provided
    meta = meta or PLO_META
    config = config or PLO_CONFIG
    timing = timing or PLO_TIMING
    build = build or PLO_BUILD
    
    if site_timeseries is None:
        site_timeseries = f"{PLO_SITE_OPEN}\n{PLO_TIMESERIES_AVGAIRTEMP}\n{PLO_TIMESERIES_RAINFALL}\n{PLO_TIMESERIES_IRRIGATION}\n{PLO_SITE_CLOSE}"
    
    if speciesforest is None:
        speciesforest = f"{PLO_SPECIESFORESTSET_OPEN}\n{PLO_SPECIESFOREST}\n{PLO_SPECIESFORESTSET_CLOSE}"
    
    # Assemble complete document
    plo_content = f"""{PLO_HEAD}
{PLO_DOCUMENTPLOT_OPEN}
  {meta}
  {config}
  {timing}
  {build}
  {site_timeseries}
  {speciesforest}
{additional_data or ''}
{PLO_DOCUMENTPLOT_CLOSE}"""
    
    return plo_content


def save_plo_file(content, filepath):
    """
    Save assembled PLO content to file.
    
    Args:
        content (str): Assembled PLO XML content
        filepath (str): Output file path (typically ends with .plo)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error saving PLO file: {e}")
        return False


# ============================================================================
# USAGE EXAMPLES
# ============================================================================
"""
Example 1: Create a basic PLO with defaults
    plo = assemble_plo_full()
    save_plo_file(plo, "output.plo")

Example 2: Create with custom location and species
    custom_build = r'<Build lonBL="151.2093" latBL="-33.8688" frCat="null" 
                    applyDownloadedData="true" areaBL="OneKm" frFracBL=""/>'
    custom_species = r'<SpeciesForest idSP="16" nmSP="Eucalyptus globulus" 
                     grthModeSP="Yield" ... CFracStemF="0.505"/>'
    
    plo = assemble_plo_full(build=custom_build, speciesforest=custom_species)
    save_plo_file(plo, "sydney_plot.plo")

Example 3: Create agricultural plot
    custom_config = r'<Config tPlot="CompA" userSoilMnrl="true" 
                    userMulchA="true" ... userEventNFeA="true" ... />'
    plo = assemble_plo_full(config=custom_config)
    save_plo_file(plo, "agriculture_plot.plo")
"""

if __name__ == "__main__":
    # Generate example PLO file
    print("Generating example PLO file based on real structure...\n")

    # Method 1: Using raw string templates (old way)
    print("Method 1: Using default templates...")
    plo_full = assemble_plo_full()
    if save_plo_file(plo_full, "/mnt/user-data/outputs/example_eucalyptus_old.plo"):
        print("✓ Created example_eucalyptus_old.plo")

    # Method 2: Using modular section functions (new way)
    print("\nMethod 2: Using modular section functions...")

    # Create each section using the new functions
    meta = create_meta_section("Example_Plot_2025", notesME="Created with modular functions")
    config = create_config_section(tPlot="CompF")
    timing = create_timing_section(stYrYTZ="2020", enYrYTZ="2050")
    build = create_build_section(lonBL=148.16, latBL=-35.61)

    # Create time series
    temps = [15.68, 17.65, 13.03, 10.66, 5.53, 4.72,
             2.97, 3.65, 4.72, 9.66, 11.96, 15.80]
    ts1 = create_timeseries("avgAirTemp", temps, yr0TS="2020", nYrsTS="1")

    rainfall = [172.91, 42.76, 91.18, 213.70, 130.61, 157.46,
                119.02, 309.44, 264.66, 115.63, 194.56, 89.46]
    ts2 = create_timeseries("rainfall", rainfall, yr0TS="2020", nYrsTS="1")

    irrigation = [0.0] * 12
    ts3 = create_timeseries("defnitIrrigA", irrigation, yr0TS="2020", nYrsTS="1")

    # Create site section with time series
    site = create_site_section(3, [ts1, ts2, ts3],
                              maxAbgMF="979.24", fpiAvgLT="8.85")

    # Assemble full document with custom sections
    plo_custom = assemble_plo_full(
        meta=meta,
        config=config,
        timing=timing,
        build=build,
        site_timeseries=site
    )

    if save_plo_file(plo_custom, "/mnt/user-data/outputs/example_eucalyptus_new.plo"):
        print("✓ Created example_eucalyptus_new.plo with modular functions")

    print("\nExample files generated successfully!")
    print("Old method: Uses raw templates")
    print("New method: Uses create_*_section() functions from plo_section_functions.py")