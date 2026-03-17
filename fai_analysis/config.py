# Configuration for FAI Analysis

# Horizon Colors
HORIZON_COLORS = {
    'Surface': 'black',
    'Quaternary_Base': '#8c564b',
    'Quaternary Base': '#8c564b',
    'JTII_Top': '#1b9e77',
    'JTII Top': '#1b9e77',
    'JT_II_+_Pliocene_+_Quaternary': 'gray',
    'JTI_Top': '#d95f02',
    'JTI Top': '#d95f02',
    'OHY_Top': '#7570b3',
    'OHY Top': '#7570b3',
    'UHY_Top': '#e7298a',
    'UHY Top': '#e7298a',
    'CBS_Top': '#66a61e',
    'CBS Top': '#66a61e',
    'BNS_Top': '#e6ab02',
    'BNS Top': '#e6ab02',
    'RT_Top': '#a6761d',
    'RT Top': '#a6761d',
    'Tertiary_Base': '#666666',
    'Tertiary Base': '#666666'
}

# Horizon Display Names (for Legend - Units)
HORIZON_DISPLAY_NAMES = {
    'Surface': 'Surface to JT I',
    'Quaternary_Base': 'Quaternary Base',
    'Quaternary Base': 'Quaternary Base',
    'JTII_Top': 'JTII',
    'JTII Top': 'JTII',
    'JTI_Top': 'JTI',
    'JTI Top': 'JTI',
    'OHY_Top': 'OHY',
    'OHY Top': 'OHY',
    'UHY_Top': 'UHY',
    'UHY Top': 'UHY',
    'CBS_Top': 'CBS',
    'CBS Top': 'CBS',
    'BNS_Top': 'BNS',
    'BNS Top': 'BNS',
    'RT_Top': 'RT to Tertiary Base',
    'RT Top': 'RT to Tertiary Base',
    'Tertiary_Base': 'Tertiary Base',
    'Tertiary Base': 'Tertiary Base'
}

# Horizon Display Names (for Legend - Tops)
HORIZON_TOPS_DISPLAY_NAMES = {
    'Surface': 'Surface',
    'Quaternary_Base': 'Quaternary Base',
    'Quaternary Base': 'Quaternary Base',
    'JTII_Top': 'JTII Top',
    'JTII Top': 'JTII Top',
    'JTI_Top': 'JTI Top',
    'JTI Top': 'JTI Top',
    'OHY_Top': 'OHY Top',
    'OHY Top': 'OHY Top',
    'UHY_Top': 'UHY Top',
    'UHY Top': 'UHY Top',
    'CBS_Top': 'CBS Top',
    'CBS Top': 'CBS Top',
    'BNS_Top': 'BNS Top',
    'BNS Top': 'BNS Top',
    'RT_Top': 'RT Top',
    'RT Top': 'RT Top',
    'Tertiary_Base': 'Tertiary Base',
    'Tertiary Base': 'Tertiary Base'
}

# Horizon Ages (Ma)
HORIZON_AGES = {
    'Surface': 0,
    'Q_Base': 2.6,
    'Quaternary_Base': 2.58,
    'JTII_Top': 5,
    'JTI_Top': 14,
    'OHY_Top': 18,
    'UHY_Top': 21,
    'CBS_Top': 24,
    'BNS_Top': 26.5,
    'RT_Top': 30.5,
    'Tertiary_Base': 45.0
}

# Default Input Files (stored in Data/)
DATA_DIR = 'Data'
DEFAULT_FAULT_FILES = [
    '1A.xlsx', '1B.xlsx', '1C.xlsx', '1D.xlsx', '1E.xlsx', 
    '2A.xlsx', '2B.xlsx'
]
COMBINED_DATA_FILE = 'all_faults_combined_noqb.csv'

# Plotting Configuration
FIGURE_SIZE_A4_WIDTH = 11.69
FIGURE_SIZE_HALF_HEIGHT = 5.84

# Solid Earth Journal Guidelines
FIGURE_WIDTH_2COL_CM = 17.7
FIGURE_WIDTH_2COL_INCH = 17.7 / 2.54

