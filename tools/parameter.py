

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