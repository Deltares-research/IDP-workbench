import solara
import leafmap
import os
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap

# Configuration variables for input options
RCP_OPTIONS = ["RCP 4.5", "RCP 8.5"]
YEAR_OPTIONS = ["2030", "2040", "2050"]

# Scenario names and descriptions
CLIMATE_SCENARIOS = {
    "RCP 4.5": {
        "name": "Moderate scenario",
        "description": "**Moderate scenario (1.5–2°C global temperature rise)**: Effects of sea level rise and upstream discharge anomalies under moderate warming conditions."
    },
    "RCP 8.5": {
        "name": "Extreme scenario", 
        "description": "**Extreme scenario (3–4°C global temperature rise)**: Effects of sea level rise and upstream discharge anomalies under higher warming conditions."
    }
}

GROUNDWATER_SCENARIOS = {
    "RCP 4.5": {
        "code": "M2",
        "name": "M2 scenario",
        "description": "**M2 Groundwater Extraction Scenario**: 5% annual reduction in groundwater extraction leading to stable 50% of 2018 extraction volume, reflecting rising awareness of consequences. Results in reduced land subsidence due to aquifer-system compaction."
    },
    "RCP 8.5": {
        "code": "B2", 
        "name": "B2 scenario",
        "description": "**B2 Groundwater Extraction Scenario**: Business-as-usual with 4% annual increase in groundwater extraction (similar to highest rates in last 25 years), leading to continued land subsidence due to aquifer-system compaction."
    }
}

RIVERBED_SCENARIOS = {
    "RCP 4.5": {
        "code": "RB1",
        "name": "RB1 scenario",
        "description": "**RB1 Riverbed Scenario**: Significantly lower erosion rate (one-third of past 20 years) until 2040, motivated by rising awareness, shortage of erodible material, and potential policy changes. Accounts for 1 G m³ sand demand until 2040."
    },
    "RCP 8.5": {
        "code": "RB3",
        "name": "RB3 scenario", 
        "description": "**RB3 Riverbed Scenario**: Business-as-usual with identical erosion rates as past 20 years. The estuarine system continues deepening 2-3m (losing ~2-3 G m³) due to sediment starvation from upstream trapping and downstream sand mining."
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

zoom = solara.reactive(8)
center = solara.reactive((10, 105.7))  # Mekong Delta coordinates

# Reactive variables for scenario selection
climate_rcp = solara.reactive("RCP 4.5")
year = solara.reactive("2030")
subsidence_enabled = solara.reactive(False)
riverbed_enabled = solara.reactive(False)

# Map instance to track across reactive updates
map_instance = solara.reactive(None)

# Loading state to track when map is updating
is_updating = solara.reactive(False)

# Function to generate Cloud Optimized GeoTIFF URL based on scenario selection
def get_cog_url(rcp, year_val, subsidence, riverbed):
    """
    Generate the COG URL based on scenario parameters.
    
    Args:
        rcp: "RCP 4.5" or "RCP 8.5"
        year_val: "2030", "2040", or "2050"
        subsidence: Boolean indicating if subsidence is enabled
        riverbed: Boolean indicating if riverbed erosion is enabled
    
    Returns:
        String URL for the corresponding COG file
    """
    # Base URL pattern
    base_url = "https://storage.googleapis.com/dgds-data-public/gca/salinity/cogs"
    
    # Map RCP to climate code
    climate_code = "cc45" if rcp == "RCP 4.5" else "cc85"
    
    # Build scenario code based on enabled features
    scenario_parts = [climate_code]
    
    if subsidence and riverbed:
        # Both subsidence and riverbed enabled
        if rcp == "RCP 4.5":
            scenario_parts.append("sm2rb1")  # M2 + RB1 for RCP 4.5
        else:
            scenario_parts.append("sb2rb3")  # B2 + RB3 for RCP 8.5
    elif subsidence:
        # Only subsidence enabled
        if rcp == "RCP 4.5":
            scenario_parts.append("sm2")  # M2 for RCP 4.5
        else:
            scenario_parts.append("sb2")  # B2 for RCP 8.5
    
    # Add year indicator
    scenario_parts.append("y")
    
    scenario_code = "".join(scenario_parts)
    
    return f"{base_url}/{scenario_code}/{year_val}.tif"


class Map(leafmap.Map):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Add what you want below
        self.add_basemap("Esri.WorldImagery")
        self.current_salinity_layer = None  # Track current salinity layer
        self.salinity_layers = []  # Track all salinity layers for cleanup
        
    def update_salinity_layer(self, rcp, year_val, subsidence, riverbed):
        """Update the salinity COG layer based on scenario parameters"""
        # Remove all existing salinity layers
        self.clear_salinity_layers()
        
        # Generate new COG URL
        cog_url = get_cog_url(rcp, year_val, subsidence, riverbed)
        
        # Create layer name based on scenario
        scenario_desc = f"{rcp} - {year_val}"
        if subsidence and riverbed:
            scenario_desc += " (Subsidence + Riverbed)"
        elif subsidence:
            scenario_desc += " (Subsidence)"
        else:
            scenario_desc += " (Climate only)"
        
        layer_name = f"Salinity: {scenario_desc}"
        
        # Add new COG layer
        try:
            # Use add_cog_layer with custom colormap
            self.add_cog_layer(
                url=cog_url,
                name=layer_name,
                palette="Reds",
                opacity=0.7,
                zoom_to_layer=False
            )
            self.current_salinity_layer = layer_name
            self.salinity_layers.append(layer_name)
            print(f"Added COG layer: {layer_name}")
            print(f"URL: {cog_url}")
        except Exception as e:
            print(f"Error with add_cog_layer: {e}")
    
    def clear_salinity_layers(self):
        """Remove all salinity layers from the map"""
        # Try to remove layers by name
        for layer_name in self.salinity_layers[:]:  # Copy list to avoid modification during iteration
            try:
                self.remove_layer(layer_name)
                self.salinity_layers.remove(layer_name)
                print(f"Removed layer: {layer_name}")
            except Exception as e:
                print(f"Could not remove layer {layer_name}: {e}")
        
        # Alternative approach: remove all layers that contain "Salinity" in the name
        try:
            if hasattr(self, 'layers') and self.layers:
                layers_to_remove = []
                for layer in self.layers:
                    if hasattr(layer, 'name') and layer.name and 'Salinity' in layer.name:
                        layers_to_remove.append(layer)
                
                for layer in layers_to_remove:
                    try:
                        self.remove_layer(layer)
                        print(f"Removed layer object: {layer.name if hasattr(layer, 'name') else 'unknown'}")
                    except Exception as e:
                        print(f"Error removing layer object: {e}")
        except Exception as e:
            print(f"Error in alternative layer removal: {e}")
        
        # Clear tracking variables
        self.current_salinity_layer = None
        self.salinity_layers = []

@solara.component
def Page():
    
    # Function to get dynamic description based on current selections
    def get_climate_description():
        return CLIMATE_SCENARIOS[climate_rcp.value]["description"]
    
    def get_anthropogenic_description():
        descriptions = []
        
        if subsidence_enabled.value:
            descriptions.append(GROUNDWATER_SCENARIOS[climate_rcp.value]["description"])
        
        if riverbed_enabled.value:
            descriptions.append("\n\n" + RIVERBED_SCENARIOS[climate_rcp.value]["description"])
        
        if not descriptions:
            return DEFAULT_TEXT["no_anthropogenic"]
        
        return " ".join(descriptions)
    
    # Create map instance if it doesn't exist
    if map_instance.value is None:
        new_map = Map(
            zoom=zoom.value,
            center=center.value,
            height="600px",
            width="100%"
        )
        # Add initial salinity layer
        new_map.update_salinity_layer(
            climate_rcp.value,
            year.value, 
            subsidence_enabled.value,
            riverbed_enabled.value
        )
        map_instance.set(new_map)
    
    # Update map when any scenario parameter changes
    def update_map_layer():
        if map_instance.value:
            is_updating.set(True)  # Show loading
            try:
                map_instance.value.update_salinity_layer(
                    climate_rcp.value,
                    year.value,
                    subsidence_enabled.value,
                    riverbed_enabled.value
                )
            finally:
                is_updating.set(False)  # Hide loading
    
    # Watch for changes in reactive variables
    solara.use_effect(update_map_layer, [climate_rcp.value, year.value, subsidence_enabled.value, riverbed_enabled.value])
    
    with solara.Column():
        solara.Markdown("# Salinity Intrusion Dashboard for Mekong Delta")
        
        # Show loading indicator when map is updating
        if is_updating.value:
            with solara.Row():
                solara.Text("Updating map...")
                solara.ProgressLinear(True)  # Indeterminate progress
        
        # Main layout: Controls on left, Map on right
        with solara.Row():
            # Left column for controls - 1/2 of screen
            with solara.Column(style={"width": "50%", "padding": "20px"}):
                
                # Climate Change Section
                solara.Markdown("## Climate Change")
                
                with solara.Row():
                    # Left side: Controls
                    with solara.Column(style={"width": "40%"}):
                        solara.Select(
                            label="RCP Scenario",
                            value=climate_rcp.value,
                            on_value=climate_rcp.set,
                            values=RCP_OPTIONS
                        )
                        
                        # Year selection
                        solara.Select(
                            label="Year",
                            value=year.value,
                            on_value=year.set,
                            values=YEAR_OPTIONS
                        )
                    
                    # Right side: Description
                    with solara.Column(style={"flex": "1", "padding-left": "10px"}):
                        with solara.Card(margin=0, elevation=2):
                            solara.Markdown(get_climate_description())
                
                # Anthropogenic Changes Section
                solara.Markdown("## Anthropogenic Changes")
                
                with solara.Row():
                    # Left side: Controls
                    with solara.Column(style={"width": "40%"}):
                        # Subsidence switch with integrated name
                        subsidence_name = GROUNDWATER_SCENARIOS[climate_rcp.value]["name"]
                        solara.Switch(
                            label=f"{SWITCH_LABELS['groundwater']} - {subsidence_name}",
                            value=subsidence_enabled.value,
                            on_value=subsidence_enabled.set
                        )
                        
                        # Riverbed switch with integrated name - only available if subsidence is enabled
                        riverbed_name = RIVERBED_SCENARIOS[climate_rcp.value]["name"]
                        
                        if subsidence_enabled.value:
                            solara.Switch(
                                label=f"{SWITCH_LABELS['riverbed']} - {riverbed_name}",
                                value=riverbed_enabled.value,
                                on_value=riverbed_enabled.set
                            )
                        else:
                            # Show disabled switch when subsidence is not enabled
                            solara.Switch(
                                label=SWITCH_LABELS["riverbed_disabled"].format(riverbed_name),
                                value=False,
                                on_value=lambda x: None,  # Do nothing when clicked
                                disabled=True
                            )
                            # Reset riverbed if subsidence gets disabled
                            if riverbed_enabled.value:
                                riverbed_enabled.set(False)
                    
                    # Right side: Description
                    with solara.Column(style={"flex": "1", "padding-left": "10px"}):
                        with solara.Card(margin=0, elevation=2):
                            solara.Markdown(get_anthropogenic_description())
            
            # Right column for map - 1/2 of screen
            with solara.Column(style={"flex": "1"}):
                # Use the map instance
                if map_instance.value:
                    solara.display(map_instance.value)