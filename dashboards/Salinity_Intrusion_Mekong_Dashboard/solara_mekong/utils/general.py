import numpy as np
import pandas as pd
from pystac_client import Client
import geopandas as gpd
import gcsfs
import os 
# Impact data

PROVINCES_SHP = os.path.join(os.path.dirname(__file__), "..", "data", "provc.geojson")
PROVINCES_IMPACTS = os.path.join(os.path.dirname(__file__), "..", "data", "production_value_2050.csv")

gdf = gpd.read_file(PROVINCES_SHP).to_crs("EPSG:4326")
impacts = pd.read_csv(PROVINCES_IMPACTS)
IMPACTS_GDF = gdf.merge(impacts, left_on='Name', right_on='Province', how='left')

# Create GCS filesystem (anonymous for public bucket)
fs = gcsfs.GCSFileSystem(anonymous=True)

# Open catalog
catalog = Client.open(
    "https://storage.googleapis.com/gca-data-public/gca/gca-stac-4/catalog.json"
)
# Choose a collection
sal_collection = catalog.get_collection("Salinity" )
sal_incr_collection = catalog.get_collection("Salinity Increase" )

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

# Baseline scenario for impact page
BASELINE_SCENARIO = {
    "name": "Baseline (Current Situation)",
    "description": "Present-day baseline scenario. No climate change or anthropogenic impacts are considered.",
    "scenario_str": "baseline"
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



# Utility to build item_id for scenario
def _get_item_id(rcp, year_val, subsidence, riverbed):
    year_str = str(year_val)
    rcp_code = CLIMATE_SCENARIOS[rcp]["scenario_str"]
    subs_code = GROUNDWATER_SCENARIOS[rcp]["scenario_str"] if subsidence else None
    riverbed_code = RIVERBED_SCENARIOS[rcp]["scenario_str"] if riverbed and subsidence else None
    if subsidence and riverbed:
        folder = f"{rcp_code}{subs_code}{riverbed_code}y"
    elif subsidence:
        folder = f"{rcp_code}{subs_code}y"
    else:
        folder = f"{rcp_code}y"
    filename = f"p50_{year_str}.tif"
    return f"{folder}/{filename}"

# Get WMS config dict for scenario
def get_wms_config(rcp, year_val, subsidence, riverbed):
    item_id = _get_item_id(rcp, year_val, subsidence, riverbed)
    try:
        item = sal_incr_collection.get_item(item_id)
        visual_asset = item.assets.get("visual")
        url = visual_asset.href
        layer = visual_asset.title
        # Compose legend_url for WMS GetLegendGraphic
        legend_url = None
        if url and layer:
            base_url = url.split('?')[0]
            legend_url = f"{base_url}?REQUEST=GetLegendGraphic&VERSION=1.0.0&FORMAT=image/png&LAYER={layer}"
        config = {
            "url": url,
            "layer": layer,
            "legend_url": legend_url
        }
    except Exception as e:
        print(f"Error getting WMS config for {item_id}: {e}")
        config = None
    return config

# Get isoline GeoDataFrame for scenario
def get_isoline_gdf(rcp, year_val, subsidence, riverbed):
    item_id = _get_item_id(rcp, year_val, subsidence, riverbed)
    try:
        item = sal_incr_collection.get_item(item_id)
        vector_asset = item.assets.get("vector")
        if vector_asset:
            isoline_url = vector_asset.href.replace('https://storage.googleapis.com/', '')
            isoline_url = f"gcs://{isoline_url}"
            isoline = gpd.read_parquet(isoline_url, filesystem=fs)
            return isoline
    except Exception as e:
        print(f"Error getting isoline for {item_id}: {e}")
    return None


# Utility to build item_id for scenario
def _get_impact_col(rcp, subsidence, riverbed):
    rcp_val = "RCP 8.5"
    rcp_code = CLIMATE_SCENARIOS[rcp_val]["scenario_str"]
    subs_code = GROUNDWATER_SCENARIOS[rcp_val]["scenario_str"] if subsidence else None
    riverbed_code = RIVERBED_SCENARIOS[rcp_val]["scenario_str"] if riverbed and subsidence else None
    if rcp:
        if subsidence and riverbed:
            id = f"{rcp_code}{subs_code}{riverbed_code}"
        elif subsidence:
            id = f"{rcp_code}{subs_code}"
        else:
            id = f"{rcp_code}"
    else:
        id = "baseline"
    return id

def get_impact_gdf(rcp, subsidence, riverbed):
    id = _get_impact_col(rcp, subsidence, riverbed)
    impacts = IMPACTS_GDF[[id, 'geometry']].copy()
    if not rcp:
        bins = [0.1, 0.1e3, 0.2e3, 0.5e3, 1.176e3, np.inf]  # in millions USD
        colors = ["#ffffcc", "#a1dab4", "#41b6c4", "#2c7fb8", "#253494"]
        def format_val(val):
            # val is in millions USD
            if val >= 1e3:
                return f"{val/1e3:.2f}B"
            else:
                return f"{val:.0f}M"
        labels = [f"< {format_val(bins[0])}"]
        labels += [f"{format_val(bins[i])}–{format_val(bins[i+1])}" for i in range(len(bins)-2)]
        name = "Baseline Production Value (USD)"
        impacts = impacts.rename(columns={id: name})
    else:
        impacts["value"] = np.where(
            IMPACTS_GDF["baseline"] != 0,
            (impacts[id] - IMPACTS_GDF["baseline"]) / IMPACTS_GDF["baseline"] * -100,
            0
        )        
        bins = [0, 5, 10, 20, 40, np.inf]  # in percentage
        colors = ["#fff5f0", "#fcbba1", "#fc9272", "#fb6a4a", "#cb181d"]
        labels = [f"< {bins[0]}%"]
        labels += [f"{bins[i]}%–{bins[i+1]}%" for i in range(len(bins)-2)]
        name = "Production Value Decrease (%)"
        impacts = impacts.rename(columns={"value": name})
        impacts = impacts[[name, 'geometry']]
    impacts[name] = impacts[name].round(0)
    config = {
        "data_column": name,
        "bins": bins,
        "colors": colors,
        "labels": labels}
    
    return impacts, config

