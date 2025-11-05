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
    nmME: str = 'New_Plot',
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
    tPlot: str              = "CompF",
    userSoilMnrl: bool      = True,
    userMulchF: bool        = False,
    userMulchA: bool        = False,
    tTreeProd: str          = "TYF",
    userCalcFPI: bool       = False,
    userCalcModTemp: bool   = False,
    userCalcModASW: bool    = False,
    userCalcModFrost: bool  = False,
    userN: bool             = False,
    userDispEner: bool      = False,
    userDispProd: bool      = False,
    userEventIrrF: bool     = False,
    userEventIrrA: bool     = False,
    userEventNFeF: bool     = True,
    userEventNFeA: bool     = True,
    userEventManF: bool     = False,
    userEventManA: bool     = False,
    rothCVers: str          = "Vers263",
    userSens: bool          = False,
    userOpti: bool          = False,
    userEcon: bool          = False,
    userLogGrade: bool      = False,
    userCropGrade: bool     = False
) -> str:
    """
    Create Config section for PLO file with simulation configuration.

    The Config section controls calculation modules, parameters, and the type
    of analysis to be performed.
    

    Parameters
    ----------
    tPlot : str, optional
        Plot type determining analysis type (default: "CompF").

        - "CompF" : Comprehensive Forest System
            Complete multilayer forest simulation with trees, debris, mulch, soil, and products.
            Models: CAMFor (trees), GENDEC (debris), RothC (soil).
            Use for: Full carbon accounting in forestry projects with above/belowground biomass.

        - "SoilF" : Forest Soil Only
            Forest soil analysis without tree/debris layers. RothC runs in standalone mode.
            Use for: Soil carbon dynamics in forested systems without modeling tree growth.

        - "CompA" : Comprehensive Agricultural System
            Complete multilayer agricultural simulation with crops, debris, mulch, soil, and products.
            Models: CAMAg (crops), GENDEC (debris), RothC (soil).
            Use for: Agricultural carbon accounting including crop residues and soil.

        - "SoilA" : Agricultural Soil Only
            Agricultural soil analysis without crop/debris layers. RothC runs in standalone mode.
            Use for: Soil carbon under agricultural management without modeling crops.

        - "CompM" : Mixed/Multilayer System
            Combined forest and agricultural systems with variable mixing over time.
            Use for: Woodland grazing, deforestation/reforestation transitions, agroforestry.
            Note: Forest percentage can vary; systems share climate but have separate irrigation.

    userSoilMnrl : bool, optional
        Enable mineral nitrogen layer simulation (default: True).

        **CRITICAL - REQUIRED FOR SOIL CARBON SIMULATION:**
        Despite its name suggesting "mineral nitrogen", this parameter is REQUIRED to simulate
        soil carbon in forest composite plots (tPlot="CompF"). The RothC soil model requires
        the mineral nitrogen pool to be enabled to run properly.

        When True: Enables mineral nitrogen pool; allows RothC soil model to run.
                   - Soil carbon (tC/ha) WILL appear in simulation outputs
                   - Mnrl section and TimeSeries exist in PLO file
                   - Enables nitrogen limitation on decomposition/growth (even if userN="false")
                   - Allows editing fertilization, N deposition, nitrification parameters

        When False: Disables mineral nitrogen pool; prevents RothC from running.
                    - Soil carbon (tC/ha) will be MISSING from simulation outputs
                    - Only plant and debris carbon will be tracked
                    - Cannot model soil carbon dynamics or accumulation

        Use for: **ALWAYS set True for forest carbon accounting that includes soil carbon.**
                 Only set False for specialized cases where soil layer not needed (rare).

        Relationship with userN:
        - userSoilMnrl="true" + userN="false": Soil carbon simulated WITHOUT full N cycling
          (nitrogen structure exists but N limitation/tracking disabled; typical use case)
        - userSoilMnrl="true" + userN="true": Soil carbon simulated WITH full N cycling
          (includes N₂O emissions, nitrogen limitation, full N budget; advanced use)
        - userSoilMnrl="false": Soil carbon NOT simulated regardless of userN setting

        Note: Required True if userEventNFeA or userEventNFeF is True (fertilizer tracking).

    userMulchF : bool, optional
        Enable mulch layer simulation for forest system (default: False).
        When True: Models explicit forest floor mulch layer with microbial processes.
                   Carbon flow: Litter → Mulch → Soil (3-stage decomposition).
        When False: Litter breaks down directly to soil (2-stage decomposition).
                    Carbon flow: Litter → Soil (bypasses mulch layer).
        Use for: Forests with thick organic floor layers or explicit litter layer management.
        Note: Mulch section must exist in PLO file regardless; parameters are empty when False.

    userMulchA : bool, optional
        Enable mulch layer simulation for agricultural system (default: False).
        When True: Models explicit surface mulch layer with microbial decomposition.
                   Carbon flow: Debris → Mulch → Soil (3-stage decomposition).
        When False: Debris breaks down directly to soil (2-stage decomposition).
                    Carbon flow: Debris → Soil (bypasses mulch layer).
        Use for: Conservation agriculture with stubble retention, crop residue management.
        Note: Mulch section must exist in PLO file regardless; parameters are empty when False.

    tTreeProd : str, optional
        Tree productivity/growth model (default: "TYF").

        - "TYF" : Tree Yield Formula (standard empirical model)
            Sigmoidal biomass accumulation curve adjusted annually by Forest Productivity Index.
            Formula: ΔY = f(M, k, Age, FPIt/FPIave) where M=max biomass, k=shape parameter.
            Use for: Plantation and native forest growth modeling.

    userCalcFPI : bool, optional
        Enable custom Forest Productivity Index calculation (default: False).
        When True: User provides FPI time series or calculates using 3PG-lite.
        When False: Use downloaded FPI data from Data Builder.
        Use for: Site-specific FPI calibration or when downloaded data inadequate.

    userCalcModTemp : bool, optional
        Enable custom temperature modifier for tree growth (default: False).
        When True: User provides temperature modifier time series.
        When False: Use standard temperature response curves.
        Use for: Species with non-standard temperature responses requiring custom calibration.

    userCalcModASW : bool, optional
        Enable custom available soil water modifier (default: False).
        When True: User overrides RothC default soil water modifier affecting decomposition.
        When False: Use standard RothC soil water calculations.
        Use for: Advanced users with detailed soil moisture data or site-specific calibrations.

    userCalcModFrost : bool, optional
        Enable custom frost modifier time series (default: False).
        When True: User provides frost modifier time series affecting growth.
        When False: No frost effects or use defaults.
        Use for: High-elevation or frost-prone sites where frost significantly limits growth.

    userN : bool, optional
        Enable full nitrogen cycle simulation (default: False).
        When True: Tracks nitrogen in all pools, calculates N₂O/N₂ emissions, nitrification,
                   denitrification, N fixation, and nitrogen limitation on growth.
        When False: Carbon-only simulation (faster, simpler). Nitrogen cycling disabled.
        Use for: N₂O greenhouse gas accounting, nitrogen budget studies, nutrient cycling.
        Note: Significantly increases computational time. Independent of userSoilMnrl;
              you can have userSoilMnrl="true" with userN="false" (structure exists but unused).

    userDispEner : bool, optional
        Enable energy disposition tracking (default: False).
        When True: Tracks energy content of biomass and products.
        When False: No energy tracking (carbon only).
        Use for: Bioenergy projects or full lifecycle energy analysis.

    userDispProd : bool, optional
        Enable detailed productivity output displays (default: False).
        When True: Additional growth and productivity outputs generated.
        When False: Standard outputs only.
        Use for: Detailed growth analysis, research, or model calibration.

    userEventIrrF : bool, optional
        Control irrigation input method for forest system (default: False).

        **Data Source Selector:**
        This flag controls the data SOURCE for irrigation inputs.

        When False: Use TIME SERIES data source
                    - Data specified in <TimeSeries/> elements 'defnitIrrigF' or 'conditIrrigF'
                    - Continuous irrigation schedule (e.g., monthly mm values)
                    - **REQUIRES irrigation <TimeSeries/> to exist in PLO file**
                    - Even for "no irrigation", must include <TimeSeries/> with all zeros

        When True: Use EVENTS data source (RECOMMENDED for no irrigation)
                   - Data specified in <Event/> elements with specific dates/amounts
                   - Discrete irrigation applications at specific points in time
                   - **For NO irrigation: Set True and simply don't create irrigation events**
                   - Cleaner approach: no <TimeSeries/> sections needed

        **IMPORTANT - How to Configure "No Irrigation" (Dryland Plantations):**

        Option 1 - Event Mode (RECOMMENDED):
            - Set userEventIrrF="true" in <Config/>
            - Remove all irrigation <TimeSeries/> (defnitIrrigF, conditIrrigF) from PLO file
            - Don't add any irrigation change events to <RegimeSet/>
            - Result: No irrigation applied; cleanest approach

        Option 2 - Time Series Mode with Zeros:
            - Set userEventIrrF="false" in <Config/>
            - Include defnitIrrigF <TimeSeries/> with all zeros (e.g., 0.0,0.0,0.0,...,0.0)
            - Set conditIrrigOnF="false" in <Site/> section
            - Result: No irrigation applied; explicit about absence of irrigation

        According to FullCAM documentation:
        "If you do not want any of a particular input (for example, there is no irrigation
        in your simulation), it is easiest to set its input type to Events, but do not
        create any events of that type. This way you will not be asked for the time
        series input."

        **Schema Requirements:**
        - userEventIrrF="false" → defnitIrrigF <TimeSeries/> MUST exist (even if all zeros)
        - userEventIrrF="true" → defnitIrrigF <TimeSeries/> should be REMOVED from file
        - Mismatch causes validation errors or undefined behavior

        Note: "There is no irrigation at the beginning of a simulation. Irrigation begins
              with the first irrigation event." So with no events, there's never irrigation.

        Use for: Set True for dryland systems or supplemental irrigation at specific dates.
                 Set False only when you have regular irrigation schedules to specify.

    userEventIrrA : bool, optional
        Control irrigation input method for agricultural system (default: False).

        **Data Source Selector:**
        This flag controls the data SOURCE for irrigation inputs.

        When False: Use TIME SERIES data source
                    - Data specified in <TimeSeries/> elements 'defnitIrrigA' or 'conditIrrigA'
                    - Continuous irrigation schedule (e.g., monthly mm values)
                    - **REQUIRES irrigation <TimeSeries/> to exist in PLO file**
                    - Even for "no irrigation", must include <TimeSeries/> with all zeros

        When True: Use EVENTS data source (RECOMMENDED for no irrigation)
                   - Data specified in <Event/> elements with specific dates/amounts
                   - Discrete irrigation applications at specific points in time
                   - **For NO irrigation: Set True and simply don't create irrigation events**
                   - Cleaner approach: no <TimeSeries/> sections needed

        **IMPORTANT - How to Configure "No Irrigation" (Dryland Agriculture):**

        Option 1 - Event Mode (RECOMMENDED):
            - Set userEventIrrA="true" in <Config/>
            - Remove all irrigation <TimeSeries/> (defnitIrrigA, conditIrrigA) from PLO file
            - Don't add any irrigation change events to <RegimeSet/>
            - Result: No irrigation applied; cleanest approach

        Option 2 - Time Series Mode with Zeros:
            - Set userEventIrrA="false" in <Config/>
            - Include defnitIrrigA <TimeSeries/> with all zeros (e.g., 0.0,0.0,0.0,...,0.0)
            - Set conditIrrigOnA="false" in <Site/> section
            - Result: No irrigation applied; explicit about absence of irrigation

        **Schema Requirements:**
        - userEventIrrA="false" → defnitIrrigA <TimeSeries/> MUST exist (even if all zeros)
        - userEventIrrA="true" → defnitIrrigA <TimeSeries/> should be REMOVED from file
        - Mismatch causes validation errors or undefined behavior

        Use for: Set True for irregular irrigation schedules or precisely scheduled applications.
                 Set False for regular irrigation schedules (weekly/monthly patterns).

    userEventNFeF : bool, optional
        Control nitrogen fertilizer input method for forest system (default: True).

        **IMPORTANT - Data Source Selector, NOT On/Off Switch:**
        This flag controls the data SOURCE for nitrogen fertilizer inputs.

        When False: Use TIME SERIES data source
                    - Fertilizer data specified in <TimeSeries/> element 'mnrlNMFromOffsF' (tN/ha per timestep)
                    - Continuous application over time based on time series values
                    - Example: Annual fertilizer application schedule

        When True: Use EVENTS data source
                   - Fertilizer data specified in <Event/> elements with specific dates/amounts
                   - Discrete applications at specific points in time
                   - Example: Single 100 tN/ha application at year 5 after planting

        **CRITICAL - Requires Nitrogen Cycling to be Enabled:**
        This flag only affects simulations when userN="true" (nitrogen cycling enabled).
        If userN="false" (carbon-only mode), fertilizer inputs are COMPLETELY IGNORED regardless
        of this setting. The model will produce identical results whether userEventNFeF is true
        or false when nitrogen cycling is disabled.

        Requirements:
        - userSoilMnrl="true" (mineral nitrogen pool must exist)
        - userN="true" for fertilizer to actually affect results
        - Either time series data (mnrlNMFromOffsF) OR event data must contain non-zero values

        Use for: Plantation forests with fertilization programs where nitrogen limitation affects
                 growth or N₂O emissions tracking is required. Rarely used for natural forests.

    userEventNFeA : bool, optional
        Control nitrogen fertilizer input method for agricultural system (default: True).

        **IMPORTANT - Data Source Selector, NOT On/Off Switch:**
        This flag controls the data SOURCE for nitrogen fertilizer inputs.

        When False: Use TIME SERIES data source
                    - Fertilizer data specified in <TimeSeries/> element 'mnrlNMFromOffsA' (tN/ha per timestep)
                    - Continuous application over time based on time series values
                    - Example: Monthly fertilizer schedule with varying rates

        When True: Use EVENTS data source
                   - Fertilizer data specified in <Event/> elements with specific dates/amounts
                   - Discrete applications at specific points in time
                   - Example: Single 50 tN/ha application on 2020-06-15

        **CRITICAL - Requires Nitrogen Cycling to be Enabled:**
        This flag only affects simulations when userN="true" (nitrogen cycling enabled).
        If userN="false" (carbon-only mode), fertilizer inputs are COMPLETELY IGNORED regardless
        of this setting. The model will produce identical results whether userEventNFeA is true
        or false when nitrogen cycling is disabled.

        Requirements:
        - userSoilMnrl="true" (mineral nitrogen pool must exist)
        - userN="true" for fertilizer to actually affect results
        - Either time series data (mnrlNMFromOffsA) OR event data must contain non-zero values

        Use for: Agricultural systems with synthetic nitrogen fertilizer applications where
                 nitrogen limitation affects crop growth or N₂O emissions tracking is required.

    userEventManF : bool, optional
        Control manure-from-offsite input method for forest system (default: False).

        **Data Source Selector:**
        This flag controls the data SOURCE for manure-from-offsite inputs.

        When False: Use TIME SERIES data source
                    - Data specified in <TimeSeries/> element 'manuCMFromOffsF' (tC/ha per year)
                    - Continuous manure application schedule over time

        When True: Use EVENTS data source
                   - Data specified in <Event/> elements with specific dates/amounts
                   - Discrete manure applications at specific points in time

        **Important - "From Offsite" Means External Sources:**
        "Offsite" means manure or organic amendments brought FROM OUTSIDE THE PLOT:
        - Biosolids from wastewater treatment applied to forestry
        - Compost applications in urban forestry
        - Paper mill sludge applied to plantation forests
        - Poultry litter applied to eucalyptus plantations (some regions)

        Manure Properties:
        - Manure carbon enters RothC soil pools (typically 49% DPM, 49% RPM, 2% HUM)
        - Can include both carbon and nitrogen components
        - Requires RothC soil model to be active (CompF plot type)

        Note: Switching between true/false has no effect if manure data is zero or missing
              in both time series AND events. Only affects results when manure data exists.

        Use for: RARE in forest systems. Primarily used for:
                 - Biosolids application programs in commercial plantations
                 - Urban forestry with compost amendments
                 - Agroforestry systems with livestock integration
                 - Research trials with organic amendment treatments

    userEventManA : bool, optional
        Control manure-from-offsite input method for agricultural system (default: False).

        **Data Source Selector:**
        This flag controls the data SOURCE for manure-from-offsite inputs.

        When False: USE TIME SERIES data source
                    - Data specified in <TimeSeries/> element 'manuCMFromOffsA' (tC/ha per year)
                    - Continuous manure application schedule over time

        When True: Use EVENTS data source
                   - Data specified in <Event/> elements with specific dates/amounts
                   - Discrete manure applications at specific points in time

        **Important - "From Offsite" Means External Sources:**
        "Offsite" means manure brought FROM OUTSIDE THE PLOT, such as:
        - Imported animal manure from external farms/feedlots
        - Biosolids from wastewater treatment
        - Compost from external composting facilities
        - Green waste amendments from offsite sources

        This is SEPARATE from manure produced by grazing animals ON the plot:
        - On-plot grazing manure is handled automatically through grazing events
        - Fodder eaten by grazers → manure destinations (DPM/RPM soil pools, atmosphere)
        - No manual input needed for on-plot grazing manure

        Manure Properties:
        - Manure carbon enters RothC soil pools (typically 49% DPM, 49% RPM, 2% HUM)
        - Can include both carbon and nitrogen components
        - Requires RothC soil model to be active (CompF or CompA plot types)

        Note: Switching between true/false has no effect if manure data is zero or missing
              in both time series AND events. Only affects results when manure data exists.

        Use for: Agricultural systems receiving external organic amendments, municipal biosolids
                 applications, or compost additions. Common in intensive horticulture or when
                 modeling nutrient management with imported organic matter.

    rothCVers : str, optional
        RothC soil carbon model version (default: "Vers263").

        - "Vers263" : RothC Version 2.6.3 (current standard for Australian National Inventory)
            Features: 5-pool model (DPM, RPM, BIO, HUM, IOM), monthly/finer timesteps,
            temperature and moisture modifiers, clay content effects.

    userSens : bool, optional
        Enable sensitivity analysis mode (default: False).
        When True: Runs multiple simulations varying parameters systematically.
        When False: Single simulation run.
        Use for: Uncertainty analysis and parameter importance assessment.

    userOpti : bool, optional
        Enable optimization mode for parameter fitting (default: False).
        When True: FullCAM performs automated parameter optimization.
        When False: Standard simulation mode.
        Use for: Calibration of model parameters to match observed data.

    userEcon : bool, optional
        Enable economic analysis module (default: False).

        When True: Calculates net present value (NPV), costs, revenues for the project.
                   - All economic modeling in constant dollars
                   - Costs and incomes added to various management events
                   - Per-hectare costs combined with fixed costs for total project cost
                   - Requires site area to be specified (cannot be blank)

        When False: No economic calculations (carbon accounting only).
                    - Carbon and biomass tracking without financial metrics

        **Requirements when True:**
        - Site must have defined area (see siteArea parameter in Site section)
        - Forest: userLogGrade must be True (harvests require log grade pricing)
        - Agriculture: userCropGrade must be True (harvests require crop grade pricing)
        - All thin/harvest events must specify grades (0% grade still allowed for pruning)

        **Automatic Implications:**
        Setting userEcon="true" automatically forces:
        - userLogGrade="true" for forest systems
        - userCropGrade="true" for agricultural systems
        (Because only grades include pricing information needed for economics)

        Use for: Financial feasibility analysis, investment decisions, cost-benefit analysis
                 for forestry or agricultural projects. Essential for commercial plantation
                 financial modeling and carbon project economics.

    userLogGrade : bool, optional
        Enable log quality grading for forest products (default: False).

        When True: Forest thinning/harvest must specify products by log grade (quality classes).
                   - Enables size/quality-dependent pricing and tracking
                   - Each log grade has associated pricing information (sawlog, pulpwood, etc.)
                   - Allows detailed product quality tracking over time
                   - Even with 0% log grade, can still specify material moving to debris (pruning)

        When False: All harvested wood treated uniformly without quality differentiation.
                    - Single product class for all timber
                    - No quality-based pricing

        Requirements when True:
        - Thinning and harvest events must specify log grades (cannot use simple harvest)
        - Compatible with userEcon="true" for economic analysis
        - Required when userEcon="true" (economic modeling forces log grades)

        Use for: Commercial forestry operations with quality-dependent markets, sawlog vs
                 pulpwood differentiation, log grading standards (e.g., A, B, C grades).
                 Essential for realistic timber economics in plantation forestry.

    userCropGrade : bool, optional
        Enable crop quality grading/classification (default: False).

        When True: Crop harvests must specify product by grade (quality classes).
                   - Enables quality-dependent pricing and tracking
                   - Each crop grade has associated pricing information
                   - Allows detailed product quality tracking over time

        When False: All crop output treated uniformly without quality differentiation.
                    - Single product class for all harvested crops
                    - No quality-based pricing

        Requirements when True:
        - Harvest events must specify crop grades (cannot use simple harvest)
        - Compatible with userEcon="true" for economic analysis

        Use for: Agricultural systems with quality-dependent pricing, premium/standard grain
                 classifications, or when modeling markets with quality premiums.
                 Common in grain cropping (wheat grades), horticultural products.

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
    stepsPerYrYTZ: str = "1",
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
        Must be 4-digit year string. Simulation begins January 1 (or first timestep) of this year.
        Note: Climate time series should cover at least this year (or use extrapolation).

    enYrYTZ : str, optional
        Ending year for simulation (default: "2100").
        Must be 4-digit year string. Simulation ends December 31 (or last timestep) of this year.
        Typical range: 30-90 years for forestry (one rotation to maturity), 10-30 years for agriculture.

    stepsPerYrYTZ : str, optional
        Number of simulation timesteps per year (default: "110").
        Valid values: 1 to 8760 (annual to hourly).
        Common values:
        - "1" = Annual timesteps (fastest; long-term forest projections)
        - "12" = Monthly timesteps (most common for carbon accounting; adequate for most purposes)
        - "52" = Weekly timesteps (detailed crop growth)
        - "110" = ~3.3 day resolution (typical for FullCAM E_globulus simulations)
        - "365" = Daily timesteps (detailed soil moisture/crop modeling)
        - "8760" = Hourly timesteps (research/detailed process studies)

        IMPORTANT - Convergence and Limiting Values:
        This parameter controls INTERNAL SIMULATION RESOLUTION (how many times per year carbon
        moves between pools), not necessarily output resolution. As you increase stepsPerYrYTZ,
        simulation results gradually approach "limiting values" where further increases produce
        identical outputs. For typical forest carbon accounting with annual/monthly input data,
        stepsPerYrYTZ="1" vs stepsPerYrYTZ="110" often produce the same annual carbon stocks
        because:
        - Input climate data (annual/monthly) gets interpolated equally across all steps
        - Carbon pool dynamics converge to the same annual totals
        - No sub-annual events (thinning, fire) occur that depend on specific step timing

        To see different outputs with higher stepsPerYrYTZ values, you must ALSO adjust
        stepsPerOutYTZ to control output frequency (e.g., stepsPerOutYTZ="1" outputs every
        step; with stepsPerYrYTZ="110", this gives ~3.3-day resolution output).

        Note: Shorter timesteps increase computation time proportionally. Time series data
        automatically interpolated to match simulation timesteps.

    dailyTimingTZ : bool, optional
        Enable daily timing precision for events (default: False).
        When True: Management events can be specified to exact calendar day within year.
        When False: Events occur at timestep boundaries (e.g., beginning of month for monthly steps).
        Use for: Set True when precise timing of operations critical (e.g., irrigation scheduling).

    useDaysPerStepDTZ : bool, optional
        Define timesteps by days per step rather than steps per day (default: True).
        When True: Use daysPerStepDTZ parameter.
        When False: Use stepsPerDayDTZ parameter.
        Note: Only relevant when dailyTimingTZ is True.

    daysPerStepDTZ : str, optional
        Number of days per simulation timestep for daily timing mode (default: "1").
        Valid when useDaysPerStepDTZ=True and dailyTimingTZ=True.
        Example: "1" = daily timesteps, "7" = weekly timesteps.

    stepsPerDayDTZ : str, optional
        Number of simulation timesteps per day for daily timing mode (default: "1").
        Valid when useDaysPerStepDTZ=False and dailyTimingTZ=True.
        Example: "1" = daily, "24" = hourly, "48" = half-hourly.

    outputFreqDTZ : str, optional
        Output frequency descriptor for daily timing mode (default: "Daily").
        Values: "Daily", "Monthly", "Yearly", or custom.
        Note: Descriptive only; actual output frequency controlled by stepsPerOutDTZ.
        Only relevant when dailyTimingTZ=True.

    stepsPerOutDTZ : str, optional
        Number of timesteps between outputs in daily timing mode (default: "1").
        Valid values: 1 to stepsPerYrYTZ.
        Use for: Reduce output file size by outputting less frequently than simulation runs.
        Example: With daily timesteps (365), set to "30" for ~monthly output.
        Only relevant when dailyTimingTZ=True.

    firstOutStepDTZ : str, optional
        First timestep to include in output for daily timing mode (default: "1").
        Use for: Skip initial spin-up period in outputs.
        Only relevant when dailyTimingTZ=True.

    tStepsYTZ : str, optional
        Time step structure within year (default: "Yearly").
        Values:
        - "Yearly" = Single annual timestep (use with stepsPerYrYTZ="1")
        - "Monthly" = 12 monthly timesteps (use with stepsPerYrYTZ="12")
        - "Weekly" = 52 weekly timesteps (use with stepsPerYrYTZ="52")
        Note: Should match stepsPerYrYTZ value for consistency.

    stStepInStYrYTZ : str, optional
        Starting timestep number within starting year (default: "").
        Empty string ("") = Start from first timestep of year.
        Use for: Start simulation mid-year (e.g., "7" for July with monthly steps).
        Rarely used; most simulations start January 1.

    enStepInEnYrYTZ : str, optional
        Ending timestep number within ending year (default: "").
        Empty string ("") = End at last timestep of year.
        Use for: End simulation mid-year (e.g., "6" for June with monthly steps).
        Rarely used; most simulations end December 31.

    stepsPerOutYTZ : str, optional
        Number of yearly timesteps between outputs (default: "1").
        Valid values: 1 to stepsPerYrYTZ.
        "1" = Output every timestep (most common).
        "12" = With monthly timesteps, outputs annually.

        IMPORTANT - Relationship with stepsPerYrYTZ:
        This parameter controls OUTPUT FREQUENCY independently from simulation resolution.
        Examples:
        - stepsPerYrYTZ="12", stepsPerOutYTZ="1" → Simulate monthly, output monthly (12 rows/year)
        - stepsPerYrYTZ="12", stepsPerOutYTZ="12" → Simulate monthly, output annually (1 row/year)
        - stepsPerYrYTZ="110", stepsPerOutYTZ="1" → Simulate 110 steps/year, output every step (110 rows/year)
        - stepsPerYrYTZ="110", stepsPerOutYTZ="110" → Simulate 110 steps/year, output annually (1 row/year)

        Use for: Reduce output file size for long simulations while maintaining fine simulation resolution.
        Example: 90-year simulation with monthly steps produces 1,080 output rows; set to "12" for 90 rows.

    firstOutStepYTZ : str, optional
        First timestep to include in yearly output (default: "1").
        "1" = Include first timestep (most common).
        Use for: Skip initial equilibration period in outputs.
        Example: "121" skips first 10 years with monthly timesteps (10 x 12 = 120).

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
        Forest category controlling species availability and calibrations (default: "null").

        IMPORTANT - What Are Calibrations?
        Calibrations are statistically fitted parameters that control how trees grow and allocate
        biomass. They are the "recipe" for species behavior under specific conditions, including:
        - Growth rates (M = max biomass, G = age at peak growth, r = species adjustment)
        - Biomass allocation ratios (stems vs branches vs roots - affects carbon storage)
        - Turnover rates (how fast leaves/branches die and enter debris/soil pools)

        Why Calibrations Matter:
        Different forest categories use fundamentally different calibrations fitted to real data:
        - Plantation calibrations: Fitted to commercial forestry (intensive management, fast
          growth, high stem allocation, optimized spacing, 100% light capture)
        - MVG calibrations: Fitted to native forests (natural competition, slower growth,
          lower stem allocation, endemic canopy cover)

        Using wrong calibrations = systematically biased carbon predictions (20-50% errors).
        Example: Using native forest calibrations for commercial eucalyptus plantation
        underestimates biomass by ~30% over the rotation period.

        **For Commercial Eucalyptus globulus plantations → Use "Plantation"**
        - Provides hardwood plantation-specific growth calibrations
        - Ensures species list appropriate for commercial forestry
        - Optimized for timber/pulp plantation management scenarios
        - Essential for accurate carbon accounting in managed eucalyptus systems

        - "null" or "All" : All Categories (DEFAULT for E_globulus_2024.plo)
            No filtering; all species and data types available.
            Use for: Exploration, research, or when unsure about land type.
            Warning: May provide generic calibrations less accurate than category-specific ones.

        - "Plantation" : Commercial Plantation Species
            Commercial forestry species filtered by National Plantation Inventory (NPI) region.
            Provides plantation-specific growth calibrations (hardwood/softwood).
            Examples: Eucalyptus globulus (hardwood), Pinus radiata (softwood).
            Use for: Commercial timber/pulp plantations managed for harvest.
            Best for: Standard carbon accounting for commercial forestry operations.

        - "MVG" : Major Vegetation Groups
            Native vegetation classified by structure/species (17 NVIS classes).
            Examples: Rainforest, Eucalyptus Tall Open Forests, Eucalyptus Open Forest.
            Use for: Native forest and woodland simulations.
            Note: Species identified by MVG number during spatial simulations.

        - "EnvMallee" : Environmental Plantings (including Mallee)
            Environmental restoration plantings and mallee species for ecological purposes.
            Use for: Ecological restoration, carbon plantings, mallee belt plantings for salinity control.
            Note: Species availability filtered by Growth Region.

        - "ERF" : Emissions Reduction Fund Methods
            Species and calibrations eligible for ERF (ACCU) carbon crediting.
            Methods: Reforestation, Environmental Plantings, Native Forest Management.
            Use for: Projects seeking Australian Carbon Credit Units under ERF.
            Note: Uses calibrated parameters meeting ERF methodology requirements.

        - "ERFH" : ERF with HIR/EMP Calibrations
            ERF methods with Human-Induced Regeneration (HIR) or Enhanced Measurement
            Procedure (EMP) site-specific calibrations.
            Use for: ERF projects using site-specific parameter sets.
            Note: More detailed calibrations than standard ERF.

    applyDownloadedData : bool, optional
        Whether to apply spatial data downloaded from Data Builder API (default: True).
        When True: Use API-downloaded climate, soil, and species data for this location.
        When False: Use manual values or defaults; ignore downloaded data.
        Use for: Set False when using entirely custom/manual data inputs.

    areaBL : str, optional
        Spatial averaging area for climate and soil data (default: "OneKm").

        - "Cell" : Single Grid Cell
            Single cell from spatial data (~100m x 100m, ~1 ha depending on resolution).
            Use for: Precise location data; minimal spatial averaging.
            Note: Uses data from exact coordinates; sensitive to local anomalies.

        - "Hectare" : One Hectare
            1 hectare (10,000 m², 0.01 km²) centered on coordinates.
            Use for: Small plots or trial sites.

        - "OneKm" : One Square Kilometer (DEFAULT, RECOMMENDED)
            100 hectares (1 km²) centered on plot coordinates.
            Use for: Most applications; good balance between representativeness and site-specificity.
            Note: Recommended default for standard carbon accounting projects.

        - "TwoKm" : Two Square Kilometers
            2 km² area for broader spatial averaging.
            Use for: When larger spatial averaging desired to reduce local variability.

        - "ThreeKm" : Three Square Kilometers
            3 km² area for regional-scale averaging.

        - "FiveKm" : Five Square Kilometers
            5 km² area for regional-scale analysis.
            Use for: Regional analysis where fine spatial detail not required.
            Note: Smooths out local variability; more representative of regional conditions.

        **Purpose:** Climate data (rainfall, temperature) and soil carbon initial conditions
        are averaged over this area. Larger areas are more representative of regional
        conditions but less site-specific.

    frFracBL : str, optional
        Forest fraction of the plot area (default: "").
        Empty string ("") = Automatically calculated from spatial data.
        Value range: "0.0" to "1.0" (0% to 100% forest cover).
        Use for: Mixed systems (CompM) where forest/agricultural proportions need specification.
        Note: Rarely needs manual specification; use default for most cases.

    Returns
    -------
        XML string for Build section.
    """
    return (f'<Build lonBL="{lonBL}" latBL="{latBL}" frCat="{frCat}" '
            f'applyDownloadedData="{_bool_to_xml(applyDownloadedData)}" '
            f'areaBL="{areaBL}" frFracBL="{frFracBL}"/>')


def create_site_section(
    count: int = 21,
    timeseries_content: str = '',
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

    timeseries_content :  str
        TimeSeries XML strings to include. Required parameter.

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
        Site multiplier for forest stem (wood) biomass allocation (default: "1.0").
        Adjusts default allometric relationship for stem/trunk component.
        Valid range: >0, typically 0.5 to 2.0.
        Use for: Sites with unusually high/low stem allocation vs species average.
        Effect: Values >1 increase stem allocation; <1 decrease it.
        Note: Default 1.0 uses species-specific allometric equations.

    siteMultBranF : str, optional
        Site multiplier for forest branch biomass allocation (default: "1.0").
        Adjusts branch component allocation relative to species default.
        Valid range: >0, typically 0.5 to 2.0.
        Use for: Adjust for site-specific growth form (e.g., wind-pruned sites have less branches).
        Note: Branch allocation varies with stand density and management.

    siteMultBarkF : str, optional
        Site multiplier for forest bark biomass allocation (default: "1.0").
        Adjusts bark thickness/mass relative to species default.
        Valid range: >0, typically 0.8 to 1.2.
        Note: Bark typically smaller component; less variable than stems/branches.

    siteMultLeafF : str, optional
        Site multiplier for forest leaf/foliage biomass allocation (default: "1.0").
        Adjusts leaf area index and foliar biomass.
        Valid range: >0, typically 0.5 to 2.0.
        Use for: High fertility sites may have elevated leaf area indices.
        Note: Affects photosynthesis and thus overall productivity.

    siteMultCortF : str, optional
        Site multiplier for forest coarse root biomass allocation (default: "1.0").
        Adjusts belowground coarse root (>2mm diameter) allocation.
        Valid range: >0, typically 0.5 to 2.0.
        Use for: Adjust for soil depth, water table, or root restriction effects.
        Note: Coarse roots typically scale with aboveground biomass but can vary with site.

    siteMultFirtF : str, optional
        Site multiplier for forest fine root biomass allocation (default: "1.0").
        Adjusts fine root (<2mm diameter) biomass allocation.
        Valid range: >0, typically 0.5 to 2.0.
        Use for: Sites with variable soil fertility/moisture affecting fine root production.
        Note: Fine roots highly variable; increase with low fertility or water stress.

    siteMultGbfrA : str, optional
        Site multiplier for agricultural grain/berry/fruit biomass (default: "1.0").
        Adjusts harvestable product allocation for crops.
        Valid range: >0, typically 0.5 to 2.0.
        Use for: Site-specific harvest index adjustments.
        Note: Equivalent to stem for agricultural system; represents economic yield.

    siteMultStlkA : str, optional
        Site multiplier for agricultural stalk/stem biomass (default: "1.0").
        Adjusts crop residue (stalk/straw) allocation.
        Valid range: >0, typically 0.5 to 2.0.
        Note: Stalk-to-grain ratio varies with fertility and management.

    siteMultLeafA : str, optional
        Site multiplier for agricultural leaf biomass (default: "1.0").
        Adjusts crop foliage allocation.
        Valid range: >0, typically 0.5 to 2.0.
        Note: Affects photosynthetic capacity during growing season.

    siteMultCortA : str, optional
        Site multiplier for agricultural coarse root biomass (default: "1.0").
        Adjusts belowground coarse root allocation for crops.
        Valid range: >0, typically 0.5 to 2.0.
        Note: Root crops (e.g., sugar beet, cassava) have high coarse root allocation.

    siteMultFirtA : str, optional
        Site multiplier for agricultural fine root biomass (default: "1.0").
        Adjusts fine root allocation for crops.
        Valid range: >0, typically 0.5 to 2.0.
        Note: Fine root allocation increases with low soil fertility.

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


    return f"{site_open}\n{timeseries_content}\n</Site>"


def create_timeseries(
    tInTS: str,
    rawTS_values: List[float],
    yr0TS: str = "1970",
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
    irrigation, or other time-varying parameters. Each time series type affects
    specific model components (RothC for soil, CAMFor/CAMAg for biomass, 3PG for productivity).

    Parameters
    ----------
    tInTS : str
        Time series input type. Required parameter.

        **Climate/Environmental Types:**

        - "avgAirTemp" : Average air temperature (°C, typically monthly)
            Used by RothC, CAMFor, and CAMAg for soil decomposition and tree growth.
            Valid range: -50°C to 50°C for Australia.

        - "rainfall" : Total rainfall/precipitation (mm, typically monthly)
            Required by RothC for topsoil moisture deficit calculation.
            100 mm = 1 megalitre per hectare. Range: 0 to ~2000 mm/month.

        - "openPanEvap" : Open-pan evaporation (mm, typically monthly)
            RothC uses this to calculate evapotranspiration and topsoil moisture deficit.
            Evapotranspiration = openPanEvap x ratio (typically 0.75).

        - "VPD" : Vapour Pressure Deficit (kPa, typically monthly)
            Used by 3PG-lite for tree productivity; affects transpiration and growth.
            Range: 0 to ~5 kPa (arid regions can exceed 3 kPa).

        - "soilTemp" : Soil temperature (°C, typically monthly)
            Affects decomposition rates in RothC; influences nutrient cycling.
            Often derived from air temperature if direct measurements unavailable.

        - "solarRad" : Mean daily solar radiation (MJ/m², typically monthly)
            Used by 3PG-lite for photosynthesis and growth calculations.
            Range: ~5 to 35 MJ/m²/day depending on latitude and season.

        - "fertility" : Soil fertility modifier (dimensionless, monthly or annual)
            Time-varying modifier for soil nutrient availability.
            Range: >0, typically 0.5 to 1.5. Values >1 indicate enhanced fertility.

        **Productivity Types:**

        - "forestProdIx" : Forest Productivity Index (dimensionless, annual)
            Annual forest productivity combining soil, sunlight, rainfall, evaporation, and frost.
            Range: 0 to ~20 (higher = more productive). Used by Tree Yield Formula (TYF).
            Growth multiplier = FPIt / FPIave. Described in NCAS Technical Report No.27.

        **Irrigation Types:**

        - "conditIrrigF" : Conditional irrigation for forest (%, varies)
            Percentage of soil water capacity guaranteed by irrigation.
            Range: 0-100%. Applied after rainfall and definite irrigation.
            Only required when <Config/> userEventIrrF="false" AND <Site/> conditIrrigOnF="true".

        - "defnitIrrigF" : Definite irrigation for forest (mm, typically monthly)
            Irrigation that definitely occurs regardless of conditions.
            Use for known irrigation schedules; applied before conditional irrigation.

            **IMPORTANT - When is this <TimeSeries/> required?**
            - REQUIRED when <Config/> userEventIrrF="false" (time series data source)
            - NOT NEEDED when <Config/> userEventIrrF="true" (event data source)
            - For "no irrigation" dryland forests: Use event mode (userEventIrrF="true")
              and omit this <TimeSeries/> entirely, OR use time series mode with all zeros.

        - "defnitIrrigA" : Definite irrigation for agriculture (mm, typically monthly)
            Same as defnitIrrigF but for agricultural system.

            **IMPORTANT - When is this <TimeSeries/> required?**
            - REQUIRED when <Config/> userEventIrrA="false" (time series data source)
            - NOT NEEDED when <Config/> userEventIrrA="true" (event data source)
            - For "no irrigation" dryland agriculture: Use event mode (userEventIrrA="true")
              and omit this <TimeSeries/> entirely, OR use time series mode with all zeros.

        - "conditIrrigA" : Conditional irrigation for agriculture (%, varies)
            Same as conditIrrigF but for agricultural system.
            Only required when <Config/> userEventIrrA="false" AND <Site/> conditIrrigOnA="true".

    rawTS_values : list
        List of numeric values or empty strings. Required parameter.
        Total count must equal nYrsTS x dataPerYrTS.
        Use empty string "" for missing data (e.g., [1.5, "", 2.3]).
        FullCAM automatically interpolates to match simulation timesteps.

    yr0TS : str, optional
        Starting year for the time series (default: "1970").
        Must be a 4-digit year string.
        E_globulus_2024.plo uses 1970 as baseline for climate data extrapolation.

    nYrsTS : str, optional
        Number of years in time series (default: "1").
        Must satisfy: len(rawTS_values) == int(nYrsTS) x int(dataPerYrTS).

    dataPerYrTS : str, optional
        Data points per year (default: "12").
        - "12" = Monthly data (most common for climate)
        - "1" = Annual data (common for forestProdIx)
        - "52" = Weekly data
        - "365" = Daily data

    tExtrapTS : str, optional
        Extrapolation method for years outside data range (default: "AvgYr").

        - "AvgYr" : Uses nearest available year (first year before data, last year after data).
            Most common for climate data.

        - "CycYr" : Cycles through available years repeatedly.
            Maintains year-to-year variability pattern.

        - "HotYr" : Uses warmest year from dataset repeatedly.
            For climate sensitivity analysis.

        - "WetYr" : Uses wettest year from dataset repeatedly.
            For wet year scenario analysis.

        - "DryYr" : Uses driest year from dataset repeatedly.
            For drought scenario analysis.

    tOriginTS : str, optional
        Time reference system (default: "Calendar").
        - "Calendar" = Calendar year (Jan-Dec)
        - "Water" = Water year (varies by region, e.g., Jul-Jun)

    nDecPlacesTS : str, optional
        Number of decimal places for data precision (default: "1").
        Affects display and output formatting.

    colWidthTS : str, optional
        Column width for UI display in pixels (default: "50").

    multTS : str, optional
        Multiplier applied to all values (default: "1.0").
        Useful for unit conversions or scaling adjustments.

    showGraphTS : bool, optional
        Whether to display graph in FullCAM UI (default: True).

    winstate_L : str, optional
        Window left position in pixels for UI (default: "10").

    winstate_T : str, optional
        Window top position in pixels for UI (default: "120").

    winstate_clientW : str, optional
        Window client width in pixels for UI (default: "702").

    winstate_clientH : str, optional
        Window client height in pixels for UI (default: "450").

    winstate_ws : str, optional
        Window state for UI (default: "Normal").
        Values: "Normal", "Minimized", "Maximized".

    Returns
    -------
    str
        XML string for TimeSeries element formatted for FullCAM PLO file.

    Notes
    -----
    - All temperature units in Celsius (°C)
    - All water/precipitation units in millimeters (mm)
    - All radiation units in MJ/m²
    - All pressure units in kPa
    - Time series data can be downloaded from Data Builder API for Australian locations
    - Manual entry required for non-Australian locations or detailed site data

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

    # ----------------------------------------------------------------------------
    # Step 1: Create Meta section
    # ----------------------------------------------------------------------------
    meta = create_meta_section("My_Plot", notesME="")
    

    # ----------------------------------------------------------------------------
    # Step 2: Create Config section
    # Note: E_globulus_2024.plo uses userEventIrrF=False (irrigation via time series)
    #       and userEventNFeF=True, userEventNFeA=True (fertilizer via events)
    # ----------------------------------------------------------------------------
    config = create_config_section(
        tPlot="CompF",
        userSoilMnrl=True,
        userMulchF=False,
        userEventIrrF=False,  # Time series-based irrigation (requires defnitIrrigF time series)
        userEventNFeF=True,   # Event-based nitrogen fertilizer for forest
        userEventNFeA=True,   # Event-based nitrogen fertilizer for agriculture
        userN=False
    )
    

    # ----------------------------------------------------------------------------
    # Step 3: Create Timing section
    # ----------------------------------------------------------------------------
    timing = create_timing_section(
        stYrYTZ="2010",
        enYrYTZ="2100",
        stepsPerYrYTZ="110",
        tStepsYTZ="Yearly",
        stepsPerOutYTZ="1"
    )

    # ----------------------------------------------------------------------------
    # Step 4: Create Build section
    # Note: E_globulus_2024.plo uses coordinates 148.16, -35.61 (Canberra region)
    # ----------------------------------------------------------------------------
    build = create_build_section(
        lonBL=148.16,
        latBL=-35.61,
        frCat="null",  # E_globulus_2024.plo uses "null" - change to "Plantation" for commercial forestry
        applyDownloadedData=True,
        areaBL="OneKm"
    )

    # ----------------------------------------------------------------------------
    # Step 5: Create Site section with time series matching E_globulus_2024.plo
    # ----------------------------------------------------------------------------
    # E_globulus_2024.plo includes these time series:
    #   - avgAirTemp (monthly average air temperature) - 54 years from 1970
    #   - openPanEvap (monthly open-pan evaporation) - 54 years from 1970
    #   - forestProdIx (annual forest productivity index) - 53 years from 1970
    #   - rainfall (monthly total rainfall) - calculated from climate data
    #   - defnitIrrigF (definite irrigation - forest) - 12 zeros (no irrigation)
    #   - conditIrrigF (conditional irrigation - forest) - 12 zeros (no irrigation)
    #   - defnitIrrigA (definite irrigation - agriculture) - 12 zeros
    #   - conditIrrigA (conditional irrigation - agriculture) - 12 zeros
    #
    # IMPORTANT: Since userEventIrrF=False in Config, we MUST include
    # defnitIrrigF and conditIrrigF time series even if all zeros (no irrigation).
    # This is a requirement when using time series data source for irrigation.
    # ----------------------------------------------------------------------------

    # 5-1: Average air temperature (12 monthly values for 1 year, 1970 baseline)
    temps = [15.68, 17.65, 13.03, 10.66, 5.53, 4.72,
             2.97, 3.65, 4.72, 9.66, 11.96, 15.80]
    ts_temp = create_timeseries(
        tInTS="avgAirTemp",
        rawTS_values=temps,
        yr0TS="1970",
        nYrsTS="1",
        dataPerYrTS="12"
    )

    # 5-2: Open pan evaporation (12 monthly values for 1 year, 1970 baseline)
    evap = [185.38, 182.03, 146.66, 81.78, 46.14, 33.41,
            38.86, 49.45, 62.64, 113.40, 157.43, 213.62]
    ts_evap = create_timeseries(
        tInTS="openPanEvap",
        rawTS_values=evap,
        yr0TS="1970",
        nYrsTS="1",
        dataPerYrTS="12"
    )

    # 5-3: Forest Productivity Index (1 annual value for 1 year, 1970 baseline)
    fpi = [9.52]
    ts_fpi = create_timeseries(
        tInTS="forestProdIx",
        rawTS_values=fpi,
        yr0TS="1970",
        nYrsTS="1",
        dataPerYrTS="1"
    )

    # 5-4: Rainfall (12 monthly values for 1 year)
    rainfall = [172.91, 42.76, 91.18, 213.70, 130.61, 157.46,
                119.02, 309.44, 264.66, 115.63, 194.56, 89.46]
    ts_rain = create_timeseries(
        tInTS="rainfall",
        rawTS_values=rainfall,
        yr0TS="1970",
        nYrsTS="1",
        dataPerYrTS="12"
    )

    # 5-5: Definite irrigation for forest (12 zeros - no irrigation)
    # REQUIRED when userEventIrrF=False (time series mode)
    irrig_f = [0.0] * 12
    ts_irrig_f = create_timeseries(
        tInTS="defnitIrrigF",
        rawTS_values=irrig_f,
        yr0TS="2010",  # E_globulus uses 2010 for irrigation time series
        nYrsTS="1",
        dataPerYrTS="12"
    )

    # 5-6: Conditional irrigation for forest (12 zeros - no irrigation)
    cond_irrig_f = [0.0] * 12
    ts_cond_irrig_f = create_timeseries(
        tInTS="conditIrrigF",
        rawTS_values=cond_irrig_f,
        yr0TS="2010",
        nYrsTS="1",
        dataPerYrTS="12"
    )

    # Assemble Site section with all time series
    timeseries_content = [ts_temp, ts_evap, ts_fpi, ts_rain, ts_irrig_f, ts_cond_irrig_f]
    site = create_site_section(
        count=len(timeseries_content),
        timeseries_content=timeseries_content,
        tAirTemp="Direct",
        conditIrrigOnF=False,
        maxAbgMF="0",  # Should be extracted from 'maxAbgMF' in the siteinfo xml
        fpiAvgLT="0"   # Should be calculated from 'forestProdIx' using the first 48 elements (1970-2017)
    )

    # ----------------------------------------------------------------------------
    # FINAL ASSEMBLY:
    # To create a complete PLO file, wrap these sections in:
    #
    # <?xml version="1.0" encoding="UTF-8"?>
    # <DocumentPlot version="5009">
    #   [Meta section]
    #   [Config section]
    #   [Timing section]
    #   [Build section]
    #   [Site section]
    # </DocumentPlot>
    #
    # Note: SpeciesForestSet and RegimeSet sections can be added after Site
    # for species definitions and management events (thinning, harvest, etc.)
    # ----------------------------------------------------------------------------
