import numpy as np
import pandas as pd
from pathlib import Path
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

# Remote Deltares GeoServer (baseline absolute salinity WMS)
REMOTE_GEOSERVER_URL = os.getenv(
    "REMOTE_GEOSERVER_URL",
    "https://international-delta-platform.avi.directory.intra/geoserver",
).rstrip("/")
BASELINE_SALINITY_WORKSPACE = os.getenv("BASELINE_SALINITY_WORKSPACE", "salinity")

# Configuration variables for input options
RCP_OPTIONS = ["RCP 4.5", "RCP 8.5"]
YEAR_OPTIONS = ["2030", "2040", "2050"]
BASELINE_YEAR_OPTIONS = ["2014", "2015", "2016"]

# Crop productivity correction (impact page for historical baseline years)
CROP_SEASON_OPTIONS = [
    "WinterSpring (ha)",
    "SummerAutumn (ha)",
    "AutumnWinter (ha)",
    "MUA (ha)",
]
CROP_METRIC_OPTIONS = [
    "corrected_yield",
    "corrected_yield_pp",
    "hectares",
    "salinity",
    "yield",
]
_CROP_PARQUET_CANDIDATES = [
    Path(
        r"C:\Ocean\Work\Projects\2026\IDP\Data\stac_folder"
        r"\crop_productivity_correction\parquets\baseline\corrected_yield.parquet"
    ),
    Path(
        r"P:\11211454-002-idt\IDP\Vietnam\Mekong\salinity_mekong"
        r"\preprocessed_outputs\stac_folder\crop_productivity_correction"
        r"\parquets\baseline\corrected_yield.parquet"
    ),
]
GCS_CROP_PARQUET_URL = (
    "https://storage.googleapis.com/gca-data-public/gca/"
    "crop_productivity_correction/parquets/baseline/corrected_yield.parquet"
)
_CROP_GDF = None

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


def _make_legend_url(wms_base: str, layer: str) -> str:
    """Build GetLegendGraphic URL (same pattern used by hazard / view_dashboard)."""
    base = wms_base.split("?")[0]
    return (
        f"{base}?REQUEST=GetLegendGraphic&VERSION=1.0.0"
        f"&FORMAT=image/png&LAYER={layer}"
    )


# Get WMS config dict for scenario (remote STAC visual asset -> Deltares GeoServer)
def get_wms_config(rcp, year_val, subsidence, riverbed):
    item_id = _get_item_id(rcp, year_val, subsidence, riverbed)
    try:
        item = sal_incr_collection.get_item(item_id)
        visual_asset = item.assets.get("visual")
        url = visual_asset.href
        layer = visual_asset.title
        legend_url = _make_legend_url(url, layer) if url and layer else None
        config = {
            "url": url,
            "layer": layer,
            "legend_url": legend_url
        }
    except Exception as e:
        print(f"Error getting WMS config for {item_id}: {e}")
        config = None
    return config


def get_baseline_salinity_wms_config(year_val):
    """
    WMS config for absolute baseline salinity (`baseline_p50_{year}`).

    Same return shape as get_wms_config: {url, layer, legend_url}.
    Uses remote Deltares GeoServer under workspace `salinity`.
    """
    layer_name = f"baseline_p50_{year_val}"
    try:
        url = f"{REMOTE_GEOSERVER_URL}/wms/{BASELINE_SALINITY_WORKSPACE}"
        layer = layer_name
        return {
            "url": url,
            "layer": layer,
            "legend_url": _make_legend_url(url, layer),
        }
    except Exception as e:
        print(f"Error getting baseline salinity WMS config for {year_val}: {e}")
        return None

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


def resolve_crop_parquet_path(preferred=None):
    """Return a readable crop Productivity GeoParquet path/URL (local first, then GCS)."""
    if preferred is not None:
        p = Path(preferred)
        if p.exists():
            return str(p)
        raise FileNotFoundError(f"Crop parquet not found: {p}")
    for candidate in _CROP_PARQUET_CANDIDATES:
        if candidate.exists():
            return str(candidate)
    return GCS_CROP_PARQUET_URL


def _load_crop_productivity_gdf():
    """Lazy-load crop productivity GDF (mirrors IMPACTS_GDF for rice production)."""
    global _CROP_GDF
    if _CROP_GDF is None:
        src = resolve_crop_parquet_path()
        gdf = gpd.read_parquet(src)
        if gdf.crs is None:
            gdf = gdf.set_crs(4326)
        else:
            gdf = gdf.to_crs(4326)
        gdf["year"] = pd.to_numeric(gdf["year"], errors="coerce").astype("Int64")
        _CROP_GDF = gdf
    return _CROP_GDF


def get_crop_impact_gdf(year_val, crop_name, metric="corrected_yield"):
    """
    Filter crop productivity to one year + season and build choropleth config.

    Same return shape as get_impact_gdf: (GeoDataFrame, config).
    Uses Quantiles so leafmap/mapclassify bin counts match the color ramp.
    """
    if metric not in CROP_METRIC_OPTIONS:
        raise ValueError(
            f"Unsupported metric '{metric}'. Choose from {CROP_METRIC_OPTIONS}"
        )

    gdf = _load_crop_productivity_gdf()
    year_int = int(year_val)
    subset = gdf[(gdf["year"] == year_int) & (gdf["crop_name"] == crop_name)].copy()
    if subset.empty:
        raise ValueError(
            f"No crop productivity rows for year={year_int}, crop={crop_name}"
        )

    out = subset[[metric, "geometry", "Name", "area_map_name", "zone"]].copy()
    values = out[metric].astype(float).replace([np.inf, -np.inf], np.nan).dropna()
    n_unique = int(values.nunique()) if not values.empty else 0
    # mapclassify needs k <= number of unique values
    k = max(1, min(5, n_unique)) if n_unique else 1
    colors = ["#ffffcc", "#c7e9b4", "#7fcdbb", "#41b6c4", "#2c7fb8"][:k]
    name = f"{metric} · {crop_name} · {year_int}"

    config = {
        "data_column": metric,
        "scheme": "Quantiles" if k > 1 else "EqualInterval",
        "k": k,
        "colors": colors,
        "labels": None,
        "title": name,
    }
    return out, config

