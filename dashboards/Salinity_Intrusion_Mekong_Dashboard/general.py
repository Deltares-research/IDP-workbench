from pystac_client import Client

# Open catalog
catalog = Client.open(
    "https://storage.googleapis.com/gca-data-public/gca/gca-stac-v7/catalog.json"
)
# Choose a collection
collection_id = "Salinity" 
collection = catalog.get_collection(collection_id)

# Configuration variables for input options
RCP_OPTIONS = ["RCP 4.5", "RCP 8.5"]
YEAR_OPTIONS = ["2030", "2040", "2050"]

# Scenario names and descriptions
CLIMATE_SCENARIOS = {
    "RCP 4.5": {
        "name": "Moderate scenario",
        "description": "**Moderate scenario (1.5–2°C global temperature rise)**: Effects of sea level rise and upstream discharge anomalies under moderate warming conditions.",
        "scenario_str": "cc45"
    },
    "RCP 8.5": {
        "name": "Extreme scenario", 
        "description": "**Extreme scenario (3–4°C global temperature rise)**: Effects of sea level rise and upstream discharge anomalies under higher warming conditions.",
        "scenario_str": "cc85"
    }
}

GROUNDWATER_SCENARIOS = {
    "RCP 4.5": {
        "code": "M2",
        "name": "M2 scenario",
        "description": "**M2 Groundwater Extraction Scenario**: 5% annual reduction in groundwater extraction leading to stable 50% of 2018 extraction volume, reflecting rising awareness of consequences. Results in reduced land subsidence due to aquifer-system compaction.",
        "scenario_str": "sm2"
    },
    "RCP 8.5": {
        "code": "B2", 
        "name": "B2 scenario",
        "description": "**B2 Groundwater Extraction Scenario**: Business-as-usual with 4% annual increase in groundwater extraction (similar to highest rates in last 25 years), leading to continued land subsidence due to aquifer-system compaction.",
        "scenario_str": "sb2"  
    }
}

RIVERBED_SCENARIOS = {
    "RCP 4.5": {
        "code": "RB1",
        "name": "RB1 scenario",
        "description": "**RB1 Riverbed Scenario**: Significantly lower erosion rate (one-third of past 20 years) until 2040, motivated by rising awareness, shortage of erodible material, and potential policy changes. Accounts for 1 G m³ sand demand until 2040.",
        "scenario_str": "rb1"      
    },
    "RCP 8.5": {
        "code": "RB3",
        "name": "RB3 scenario", 
        "description": "**RB3 Riverbed Scenario**: Business-as-usual with identical erosion rates as past 20 years. The estuarine system continues deepening 2-3m (losing ~2-3 G m³) due to sediment starvation from upstream trapping and downstream sand mining.",
        "scenario_str": "rb3"      
    }
}

# UI Labels
SWITCH_LABELS = {
    "groundwater": "Groundwater Extraction (Subsidence)",
    "riverbed": "Sediment Starvation (Riverbed Level Incision)",
    "riverbed_disabled": "Sediment Starvation (Riverbed Level Incision) - {} (requires groundwater extraction)"
}

DEFAULT_TEXT = {
    "no_anthropogenic": "No anthropogenic changes selected. Climate-only scenario considers sea level rise and discharge variations without human-induced modifications."
}
