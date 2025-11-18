import solara
import leafmap
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from general import (
    collection,
    RCP_OPTIONS,
    YEAR_OPTIONS,
    CLIMATE_SCENARIOS,
    GROUNDWATER_SCENARIOS,
    RIVERBED_SCENARIOS,
    SWITCH_LABELS,
    DEFAULT_TEXT,
)

zoom = solara.reactive(8)
center = solara.reactive((10, 105.7))  # Mekong Delta coordinates

# Reactive variables for scenario selection
climate_rcp = solara.reactive("RCP 4.5")
year = solara.reactive("2030")
subsidence_enabled = solara.reactive(False)
riverbed_enabled = solara.reactive(False)


# Map instance to track across reactive updates
map_instance = solara.reactive(None)

# Reactive legend URL for WMS colorbar
legend_url = solara.reactive(None)

# Loading state to track when map is updating
is_updating = solara.reactive(False)

# Error message state for GUI alerts
error_message = solara.reactive(None)

# Function to generate WMS configuration based on scenario selection
def get_wms_config(rcp, year_val, subsidence, riverbed):
    """
    Generate the WMS configuration based on scenario parameters.
    
    Args:
        rcp: "RCP 4.5" or "RCP 8.5"
        year_val: "2030", "2040", or "2050"
        subsidence: Boolean indicating if subsidence is enabled
        riverbed: Boolean indicating if riverbed erosion is enabled
    
    Returns:
        Dictionary with 'url' and 'layer' keys for the WMS configuration
    """
    # Map RCP to code
    rcp_code = "cc45" if rcp == "RCP 4.5" else "cc85"
    year_str = str(year_val)

    # Get scenario codes
    subs_code = GROUNDWATER_SCENARIOS[rcp]["scenario_str"] if subsidence else None
    riverbed_code = RIVERBED_SCENARIOS[rcp]["scenario_str"] if riverbed and subsidence else None

    # Build folder and filename
    if subsidence and riverbed:
        folder = f"{rcp_code}{subs_code}{riverbed_code}y"
    elif subsidence:
        folder = f"{rcp_code}{subs_code}y"
    else:
        folder = f"{rcp_code}y"
    
    filename = f"{year_str}.tif"

    item_id = f"{folder}/{filename}"
    try:
        item = collection.get_item(item_id)
        print(f"Getting STAC item: {item_id}")
        visual_asset = item.assets.get("visual")

        base_config = {
            "url": visual_asset.href,
            "layer": visual_asset.title
        }
    except Exception as e:
        print(f"Error getting STAC item {item_id}")
        base_config = None
    return base_config


class Map(leafmap.Map):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Add what you want below
        self.add_basemap("Esri.WorldImagery")
        self.current_salinity_layer = None  # Track current salinity layer
        self.salinity_layers = []  # Track all salinity layers for cleanup
        
    def update_salinity_layer(self, rcp, year_val, subsidence, riverbed):
        """Update the salinity WMS layer based on scenario parameters"""
        # Remove all existing salinity layers
        self.clear_salinity_layers()
        
        # Generate new WMS configuration
        wms_config = get_wms_config(rcp, year_val, subsidence, riverbed)
        
        # Create layer name based on scenario
        scenario_desc = f"{rcp} - {year_val}"
        if subsidence and riverbed:
            scenario_desc += " (Subsidence + Riverbed)"
        elif subsidence:
            scenario_desc += " (Subsidence)"
        else:
            scenario_desc += " (Climate only)"
        
        layer_name = f"Salinity: {scenario_desc}"
        
        # Add new WMS layer

        if wms_config is not None:
            self.add_wms_layer(
                url=wms_config['url'],
                layers=wms_config['layer'],
                name=layer_name,
                format="image/png",
                transparent=True,
                opacity=0.7,
                attribution="Deltares IDP",
            )
            self.current_salinity_layer = layer_name
            self.salinity_layers.append(layer_name)
            print(f"Added WMS layer: {layer_name}")
            print(f"URL: {wms_config['url']}")
            print(f"Layer: {wms_config['layer']}")
            error_message.set(None)
            # Set reactive legend URL for colorbar
            legend_url.set(f"{wms_config['url'].split('?')[0]}?REQUEST=GetLegendGraphic&VERSION=1.0.0&FORMAT=image/png&LAYER={wms_config['layer']}")
        else:
            error_message.set("Layer is not available for the selected scenario.")
            self.clear_salinity_layers()
            
    
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
        # Add initial salinity layer using WMS
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

        # Show loading indicator when map is updating
        if is_updating.value:
            with solara.Row():
                solara.Text("Updating map...")
                solara.ProgressLinear(True)  # Indeterminate progress

        # Main layout: Controls on left, Map on right
        with solara.Row():
            # Left column for controls - 1/2 of screen
            with solara.Column(style={"width": "50%", "padding": "20px"}):
                # ...existing code...
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
            with solara.Column(style={"width": "80px", "flex": "none", "padding-left": "10px"}):
                if legend_url.value:
                    solara.Image(legend_url.value)
        if error_message.value:
            solara.Error(error_message.value)