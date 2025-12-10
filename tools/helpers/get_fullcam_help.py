import time
import requests

from bs4 import BeautifulSoup
from joblib import Parallel, delayed

# URL to title mapping from the Table of Contents
url_titles = {
    "172_Overview of FullCAM.htm": "Overview of FullCAM",
    "1_Introduction to Using FullCAM.htm": "Introduction to Using FullCAM",
    "268_Whats New.htm": "What's New?",
    "10_Documents and Files.htm": "Documents and Files",
    "20_General Features.htm": "General Features",
    "15_Special Keys.htm": "Special Keys",
    "217_Main Window.htm": "Main Window",
    "127_Simulate Menu.htm": "Simulate Menu",
    "11_About.htm": "About",
    "135_Time-Series Window.htm": "Time Series Window",
    "86_Decay Rate Window.htm": "Decay Rate Window",
    "23_Table Window.htm": "Table Window",
    "57_Plots, Systems, Layers, and Pools.htm": "Plots, Systems, Layers, and Pools",
    "58_Processes and Events.htm": "Processes and Events",
    "234_Explorer.htm": "Explorer",
    "283_FullCAM Command Line Utility.htm": "Command Line Utility",
    "177_Plot Simulation.htm": "Plot Simulation",
    "150_Configuration.htm": "Configuration",
    "6_Configure the Plot.htm": "Configure the Plot",
    "108_Configure Tree Production.htm": "Configure Tree Production",
    "138_Configure Other Options.htm": "Configure Other Options",
    "195_Configure Event Or Time-Series.htm": "Configure event or time-series",
    "141_Models and Inputs Window.htm": "Models and Inputs Window",
    "50_Diagrams Window.htm": "Diagrams Window",
    "206_Forest Percentage.htm": "Forest Percentage",
    "180_Latitude and Longitude.htm": "Latitude and Longitude",
    "281_Plot Digest.htm": "Plot Digest",
    "282_Templates.htm": "Plot Templates",
    "286_XML Copy.htm": "XML Copy",
    "199_Timing.htm": "Timing",
    "267_Simulation Timing.htm": "Simulation Timing and Steps",
    "26_Start and End of Simulation.htm": "Start and End of Simulation",
    "27_Output Steps.htm": "Output Steps",
    "132_Data Builder.htm": "Data Builder",
    "207_Downloading Spatial Data.htm": "Downloading Spatial Data",
    "228_Pasture to Plantation Forest.htm": "Pasture to Plantation Forest",
    "229_Plantation Forest to Plantation Forest.htm": "Plantation Forest to Plantation Forest",
    "230_Native Forest to Plantation Forest.htm": "Native Forest to Plantation Forest",
    "231_Native Forest to Pasture.htm": "Native Forest to Pasture",
    "232_Grazed Woodland.htm": "Grazed Woodland",
    "233_Crop and Pasture Management.htm": "Crop and Pasture Management",
    "235_Regimes.htm": "Forest Regimes",
    "200_Site.htm": "Site",
    "12_Site_Water.htm": "Water",
    "88_Rainfall.htm": "Rainfall",
    "98_Open-Pan Evaporation.htm": "Open-Pan Evaporation",
    "97_Vapour Pressure Deficit.htm": "Vapour Pressure Deficit",
    "183_Soil Water Modifier.htm": "Soil Water Modifier",
    "194_Vapour Pressure Deficit Modifier.htm": "Vapour Pressure Deficit Modifier",
    "92_Definite Irrigation.htm": "Definite Irrigation",
    "91_Conditional Irrigation.htm": "Conditional Irrigation",
    "13_Site_Temperature.htm": "Temperature",
    "89_Average Air Temperature.htm": "Average Air Temperature",
    "94_Frost Nights.htm": "Frost Nights",
    "178_Frost Modifier.htm": "Frost Modifier",
    "93_Solar Radiation.htm": "Solar Radiation",
    "64_Site_Productivity.htm": "Productivity",
    "188_Forest Productivity Index.htm": "Forest Productivity Index",
    "181_Soil Nutrition Modifier.htm": "Soil Nutrition Modifier",
    "39_Site_Growth Multipliers.htm": "Growth Multipliers",
    "157_Site_Area.htm": "Area",
    "36_Site_Maximum Aboveground Biomass.htm": "Maximum Aboveground Biomass",
    "96_Air Temperature.htm": "Air Temperature",
    "201_Plants.htm": "Plants",
    "215_Trees.htm": "Trees",
    "216_Crops.htm": "Crops",
    "56_Select a Species.htm": "Select a Species",
    "145_Properties of the Species.htm": "Properties of the Species",
    "123_Notes on a Plant Species.htm": "Notes on a Plant Species",
    "42_Growth Properties.htm": "Growth Properties",
    "131_Yield and Net Primary Production.htm": "Yield and Net Primary Production",
    "130_Tree Yield Formula.htm": "Tree Yield Formula",
    "112_Tree Growth Allocations.htm": "Tree Growth Allocations",
    "124_Crop Growth Allocations.htm": "Crop Growth Allocations",
    "110_Tree Growth Increments.htm": "Tree Growth Increments",
    "118_Crop Growth Increments.htm": "Crop Growth Increments",
    "43_Plant Properties.htm": "Plant Properties",
    "285_StandingDead.htm": "Standing Dead",
    "9_Stem Density.htm": "Stem Density",
    "121_Mortality.htm": "Mortality",
    "19_Stem Loss and Stalk Loss.htm": "Stem Loss and Stalk Loss",
    "45_Debris Properties.htm": "Debris Properties",
    "122_Sensitivity of Debris Breakdown to Temperature and Water.htm": "Sensitivity of Debris Breakdown to Temperature and Water",
    "47_Product Properties.htm": "Product Properties",
    "142_Standard Events of a Species.htm": "Standard Events of a Species",
    "203_Soil.htm": "Soil",
    "193_Soil Inputs.htm": "Soil Inputs",
    "101_Manure Inputs to Soil from Offsite.htm": "Manure Inputs to Soil from Offsite",
    "99_Plant Residue Inputs to Soil.htm": "Plant Residue Inputs to Soil",
    "3_Soil Properties.htm": "Soil Properties",
    "44_Soil Water.htm": "Soil Water",
    "102_Soil Cover.htm": "Soil Cover",
    "46_Soil for the Whole Plot.htm": "Soil for the Whole Plot",
    "205_Initial Conditions.htm": "Initial Conditions",
    "185_Initial Trees.htm": "Initial Trees",
    "184_Initial Crops.htm": "Initial Crops",
    "31_Initial Debris.htm": "Initial Debris",
    "284_Initial StandingDead.htm": "Initial Standing Dead",
    "32_Initial Soil.htm": "Initial Soil",
    "33_Initial Products.htm": "Initial Products",
    "197_Initial Conditions For the Whole Plot.htm": "Initial Conditions For the Whole Plot",
    "136_Events.htm": "Events",
    "137_Event Window.htm": "Event Window",
    "143_Event Timing.htm": "Event Timing",
    "248_Event Update.htm": "Event Update",
    "274_New Regime.htm": "New Regime",
    "276_Editing Regimes.htm": "Editing Regimes",
    "280_Edit Regime.htm": "Edit Regime",
    "278_Regime Update.htm": "Regime Update",
    "158_Plant Trees.htm": "Plant Trees",
    "161_Plant Crop.htm": "Plant Crop",
    "140_Thin.htm": "Thin",
    "154_Post-Thin Period.htm": "Post-Thin Period",
    "153_Harvest.htm": "Harvest",
    "120_Plant Removal and Replacement.htm": "Thin or Harvest - Plant Removal and Replacement",
    "144_Forest Fire.htm": "Forest Fire",
    "149_Agricultural Fire.htm": "Agricultural Fire",
    "164_Plough.htm": "Plough",
    "163_Herbicide.htm": "Herbicide",
    "196_Grazing Change.htm": "Grazing Change",
    "51_Forest Treatment.htm": "Forest Treatment",
    "52_Chopper Roller.htm": "Chopper Roller",
    "53_Termite Change.htm": "Termite Change",
    "54_Irrigation Change.htm": "Irrigation Change",
    "62_Manure-From-Offsite Change.htm": "Manure-From-Offsite Change",
    "116_Forest Percentage Change.htm": "Forest Percentage Change",
    "171_Select A Standard Event.htm": "Select A Standard Event",
    "25_Output Windows.htm": "View Output Windows",
    "168_Output Window.htm": "Output Window",
    "169_Select Outputs.htm": "Select Outputs",
    "170_Graph Lines.htm": "Graph Lines",
    "175_Graph Axes.htm": "Graph Axes",
    "72_Estate Simulation.htm": "Estate Simulation",
    "166_Plot Files.htm": "Plot Files",
    "167_Plots in the Estate.htm": "Plots in the Estate",
    "186_One Plot in the Estate.htm": "One Plot in the Estate",
    "269_Generate Estate.htm": "Generate Estate",
    "198_Constituent Models In FullCAM.htm": "Constituent Models In FullCAM",
    "77_CAMFor.htm": "CAMFor",
    "78_CAMAg.htm": "CAMAg",
    "114_RothC.htm": "RothC",
    "247_Proxy Settings.htm": "Proxy Settings",
    "266_Server Settings.htm": "Server Settings",
    "49_Further Documentation.htm": "Further Documentation",
    "48_Research Edition.htm": "Research Edition",
    "190_Contact Us.htm": "Contact Us",
    "14_Credits.htm": "Credits",
}

# List of all URLs in order from the table of contents
urls = [
    # Introduction
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/172_Overview of FullCAM.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/1_Introduction to Using FullCAM.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/268_Whats New.htm",
    
    # Operating FullCAM
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/10_Documents and Files.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/20_General Features.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/15_Special Keys.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/217_Main Window.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/127_Simulate Menu.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/11_About.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/135_Time-Series Window.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/86_Decay Rate Window.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/23_Table Window.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/57_Plots, Systems, Layers, and Pools.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/58_Processes and Events.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/234_Explorer.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/283_FullCAM Command Line Utility.htm",
    
    # Plots
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/177_Plot Simulation.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/150_Configuration.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/6_Configure the Plot.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/108_Configure Tree Production.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/138_Configure Other Options.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/195_Configure Event Or Time-Series.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/141_Models and Inputs Window.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/50_Diagrams Window.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/206_Forest Percentage.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/180_Latitude and Longitude.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/281_Plot Digest.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/282_Templates.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/286_XML Copy.htm",
    
    # Timing
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/199_Timing.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/267_Simulation Timing.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/26_Start and End of Simulation.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/27_Output Steps.htm",
    
    # Data Builder
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/132_Data Builder.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/207_Downloading Spatial Data.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/228_Pasture to Plantation Forest.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/229_Plantation Forest to Plantation Forest.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/230_Native Forest to Plantation Forest.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/231_Native Forest to Pasture.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/232_Grazed Woodland.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/233_Crop and Pasture Management.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/235_Regimes.htm",
    
    # Site
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/200_Site.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/12_Site_Water.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/88_Rainfall.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/98_Open-Pan Evaporation.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/97_Vapour Pressure Deficit.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/183_Soil Water Modifier.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/194_Vapour Pressure Deficit Modifier.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/92_Definite Irrigation.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/91_Conditional Irrigation.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/13_Site_Temperature.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/89_Average Air Temperature.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/94_Frost Nights.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/178_Frost Modifier.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/93_Solar Radiation.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/64_Site_Productivity.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/188_Forest Productivity Index.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/181_Soil Nutrition Modifier.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/39_Site_Growth Multipliers.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/157_Site_Area.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/36_Site_Maximum Aboveground Biomass.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/96_Air Temperature.htm",
    
    # Plants
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/201_Plants.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/215_Trees.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/216_Crops.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/56_Select a Species.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/145_Properties of the Species.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/123_Notes on a Plant Species.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/42_Growth Properties.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/131_Yield and Net Primary Production.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/130_Tree Yield Formula.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/112_Tree Growth Allocations.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/124_Crop Growth Allocations.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/110_Tree Growth Increments.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/118_Crop Growth Increments.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/43_Plant Properties.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/285_StandingDead.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/9_Stem Density.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/121_Mortality.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/19_Stem Loss and Stalk Loss.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/45_Debris Properties.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/122_Sensitivity of Debris Breakdown to Temperature and Water.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/47_Product Properties.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/142_Standard Events of a Species.htm",
    
    # Soil
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/203_Soil.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/193_Soil Inputs.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/101_Manure Inputs to Soil from Offsite.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/99_Plant Residue Inputs to Soil.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/3_Soil Properties.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/44_Soil Water.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/102_Soil Cover.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/46_Soil for the Whole Plot.htm",
    
    # Initial Conditions
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/205_Initial Conditions.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/185_Initial Trees.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/184_Initial Crops.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/31_Initial Debris.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/284_Initial StandingDead.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/32_Initial Soil.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/33_Initial Products.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/197_Initial Conditions For the Whole Plot.htm",
    
    # Events and Regimes
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/136_Events.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/137_Event Window.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/143_Event Timing.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/248_Event Update.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/274_New Regime.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/276_Editing Regimes.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/280_Edit Regime.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/278_Regime Update.htm",
    
    # Event Types
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/158_Plant Trees.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/161_Plant Crop.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/140_Thin.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/154_Post-Thin Period.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/153_Harvest.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/120_Plant Removal and Replacement.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/144_Forest Fire.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/149_Agricultural Fire.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/164_Plough.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/163_Herbicide.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/196_Grazing Change.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/51_Forest Treatment.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/52_Chopper Roller.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/53_Termite Change.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/54_Irrigation Change.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/62_Manure-From-Offsite Change.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/116_Forest Percentage Change.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/171_Select A Standard Event.htm",
    
    # Outputs
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/25_Output Windows.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/168_Output Window.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/169_Select Outputs.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/170_Graph Lines.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/175_Graph Axes.htm",
    
    # Estates
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/72_Estate Simulation.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/166_Plot Files.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/167_Plots in the Estate.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/186_One Plot in the Estate.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/269_Generate Estate.htm",
    
    # Constituent Models
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/198_Constituent Models In FullCAM.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/77_CAMFor.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/78_CAMAg.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/114_RothC.htm",
    
    # Server
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/247_Proxy Settings.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/266_Server Settings.htm",
    
    # About the Software
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/49_Further Documentation.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/48_Research Edition.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/190_Contact Us.htm",
    "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/14_Credits.htm",
]

def extract_content_from_html(html_content, debug=False):
    """Extract main content from HTML page, preserving HTML structure

    These FullCAM help pages have a simple structure - they're HTML fragments
    with Server Side Includes for header/footer. The actual content is everything
    in the HTML, so we just need to get it all and clean it up.
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove script, style, and navigation elements
    for element in soup(['script', 'style', 'nav', 'iframe']):
        element.decompose()

    # Remove HTML comments (including SSI directives)
    for comment in soup.find_all(string=lambda text: isinstance(text, str) and '<!--' in str(text)):
        comment.extract()

    # For these simple HTML files, the body contains everything we need
    # If there's no body tag, the soup itself is the content
    content = soup.find('body') if soup.find('body') else soup

    if content:
        # Convert relative links to absolute URLs
        base_url = "https://www.dcceew.gov.au/themes/custom/awe/fullcam/Help-FullCAM2024/"

        # Fix all <a> tags with href attributes
        for link in content.find_all('a', href=True):
            href = link['href']
            # Only convert relative URLs (not absolute URLs or anchors)
            if not href.startswith(('http://', 'https://', '#', 'mailto:')):
                # Handle relative paths
                if href.startswith('/'):
                    link['href'] = 'https://www.dcceew.gov.au' + href
                else:
                    link['href'] = base_url + href
                # Open external links in new tab
                link['target'] = '_blank'

        # Fix all <img> tags with src attributes
        for img in content.find_all('img', src=True):
            src = img['src']
            # Only convert relative URLs
            if not src.startswith(('http://', 'https://', 'data:')):
                if src.startswith('/'):
                    img['src'] = 'https://www.dcceew.gov.au' + src
                else:
                    img['src'] = base_url + src

        # Get all the HTML content
        result = str(content)

        # If result is too short or empty, it might mean the page structure is different
        if len(result.strip()) < 50:
            # Fall back to getting all HTML
            result = str(soup)

        return result

    return ""

def download_single_page(idx, url, session):
    """Download a single page and return its content"""
    page_data = {
        'idx': idx,
        'url': url,
        'success': False,
        'content': None,
        'error': None
    }

    try:
        response = session.get(url, timeout=15)

        if response.status_code == 200:
            content_html = extract_content_from_html(response.content)

            if content_html.strip():
                # Get the filename from URL
                filename = url.split('/')[-1]

                # Use the proper title from the mapping, or fall back to cleaned filename
                page_title = url_titles.get(filename, filename.replace('_', ' ').replace('.htm', ''))

                section_id = f"page-{idx}"

                page_section = f"""
    <div class="page-section" id="{section_id}">
        <div class="page-number">Page {idx} of {len(urls)}</div>
        <h2 class="page-title">{page_title}</h2>
        {content_html}
    </div>
"""
                page_data['content'] = page_section
                page_data['success'] = True
            else:
                page_data['error'] = 'Empty content'
        else:
            page_data['error'] = f'Status: {response.status_code}'

    except requests.exceptions.Timeout:
        page_data['error'] = 'Timeout'
    except requests.exceptions.ConnectionError:
        page_data['error'] = 'Connection error'
    except Exception as e:
        page_data['error'] = f'Error: {str(e)[:30]}'

    return page_data


def download_and_merge_html(max_workers=100):
    """Download all URLs concurrently and merge into a single HTML file

    Args:
        max_workers (int): Maximum number of concurrent downloads (default: 10)
    """
    print(f"Starting batch download of {len(urls)} pages with {max_workers} concurrent workers...")
    start_time = time.time()

    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })

    # HTML header template
    html_header = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FullCAM Documentation - Complete Reference</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .page-section {
            background: white;
            margin: 20px 0;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .page-title {
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
            font-size: 24px;
        }
        .page-number {
            color: #7f8c8d;
            font-size: 14px;
            margin-bottom: 5px;
        }
        h1, h2, h3, h4, h5, h6 {
            color: #2c3e50;
            margin-top: 20px;
        }
        a {
            color: #3498db;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #3498db;
            color: white;
        }
        code {
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        pre {
            background-color: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .toc {
            background: #ecf0f1;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }
        .toc h2 {
            margin-top: 0;
        }
        .toc ul {
            list-style-type: none;
            padding-left: 0;
        }
        .toc li {
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <h1 style="text-align: center; color: #2c3e50; margin-bottom: 10px;">FullCAM Documentation</h1>
    <p style="text-align: center; color: #7f8c8d; margin-bottom: 40px;">Complete Reference Guide - All Pages Merged</p>
"""

    # Download pages concurrently using joblib
    # Create tasks for parallel execution
    tasks = [delayed(download_single_page)(idx, url, session)
             for idx, url in enumerate(urls, 1)]

    # Execute downloads in parallel
    page_results_list = Parallel(n_jobs=max_workers, backend='threading', verbose=10)(tasks)

    # Convert list results to dictionary keyed by idx
    page_results = {result['idx']: result for result in page_results_list}

    # Print summary of results
    for result in page_results_list:
        status = "✓" if result['success'] else f"✗ ({result['error']})"
        print(f"[{result['idx']}/{len(urls)}] {urls[result['idx']-1].split('/')[-1]} ... {status}")

    # Sort results by index and build HTML
    successful_downloads = 0
    failed_downloads = 0
    html_parts = [html_header]

    for idx in sorted(page_results.keys()):
        result = page_results[idx]
        if result['success']:
            html_parts.append(result['content'])
            successful_downloads += 1
        else:
            failed_downloads += 1

    # HTML footer
    elapsed_time = time.time() - start_time
    html_parts.append(f"""
    <footer style="text-align: center; margin-top: 50px; padding: 20px; color: #7f8c8d; border-top: 1px solid #ddd;">
        <p>FullCAM Documentation compiled from dcceew.gov.au</p>
        <p>Pages successfully downloaded: {successful_downloads} / {len(urls)}</p>
        <p>Download time: {elapsed_time:.2f} seconds</p>
    </footer>
</body>
</html>""")

    # Write the combined HTML file
    html_filename = "FullCAM_Documentation_Complete.html"
    try:
        with open(f'tools/{html_filename}', 'w', encoding='utf-8') as f:
            f.write('\n'.join(html_parts))
        print(f"\n✓ HTML file created: {html_filename}")
        print(f"Summary: {successful_downloads} successful, {failed_downloads} failed")
        print(f"Total time: {elapsed_time:.2f} seconds ({elapsed_time/len(urls):.2f}s per page)")
    except Exception as e:
        print(f"Error writing HTML file: {e}")

if __name__ == "__main__":
    download_and_merge_html()