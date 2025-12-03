import solara
import leafmap as leafmap
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from general import (
    get_scenario,
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


# Reactive variable for opacity slider
opacity = solara.reactive(0.8)

# General configuration for isoline style
ISOLINE_STYLE = {
    "color": "red",
    "weight": 2
}


class Map(leafmap.Map):
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Add what you want below
        self.add_basemap("Esri.WorldImagery")
        self.current_salinity_layer = None  # Track current salinity layer
        
    def update_salinity_layer(self, rcp, year_val, subsidence, riverbed):
        """Update the salinity WMS layer based on scenario parameters"""
        # Remove all existing salinity layers
        self.clear_salinity_layers()
        
        # Generate new WMS configuration
        config = get_scenario(rcp, year_val, subsidence, riverbed)
        
        # Create layer name based on scenario
        scenario_desc = f"{rcp} - {year_val}"
        if subsidence and riverbed:
            scenario_desc += " (Subsidence + Riverbed)"
        elif subsidence:
            scenario_desc += " (Subsidence)"
        else:
            scenario_desc += " (Climate only)"
        
        layer_name = f"Salinity Increase: {scenario_desc}"

        if config is not None:
            # Add new WMS layer
            self.add_wms_layer(
                url=config['url'],
                layers=config['layer'],
                name=layer_name,
                format="image/png",
                transparent=True,
                opacity=opacity.value,
                attribution="Deltares IDP",
            )
            self.current_salinity_layer = layer_name
            print(f"Added WMS layer: {layer_name}")
            self.add_gdf(
                config['isoline'],
                layer_name=f"{layer_name} 2 PSU Isoline",
                info_mode=None,
                style=ISOLINE_STYLE,
                hover_style=ISOLINE_STYLE
            )
            # print(f"URL: {config['url']}")
            # print(f"Layer: {config['layer']}")
            error_message.set(None)
            # Set reactive legend URL for colorbar
            legend_url.set(f"{config['url'].split('?')[0]}?REQUEST=GetLegendGraphic&VERSION=1.0.0&FORMAT=image/png&LAYER={config['layer']}")
        else:
            error_message.set("Layer is not available for the selected scenario.")
            self.clear_salinity_layers()
            
    
    def clear_salinity_layers(self):
        """Remove all salinity layers from the map"""

        # Alternative approach: remove all layers that contain "Salinity" in the name
        if hasattr(self, 'layers') and self.layers:
            layers_to_remove = []
            for layer in self.layers:
                if hasattr(layer, 'name') and layer.name and 'Salinity' in layer.name:
                    layers_to_remove.append(layer)
                    layers_to_remove.append(f"{layer} 2 PSU Isoline")
            
            for layer in layers_to_remove:
                try:
                    self.remove_layer(layer)
                except Exception as e:
                    print(f"Error removing layer object: {e}")
        
        # Clear tracking variables
        self.current_salinity_layer = None
        self.salinity_layers = []
    
    def set_salinity_opacity(self, opacity_value):
        """Update opacity of the current salinity layer only"""
        # Try to find the layer by name and set its opacity
        if hasattr(self, 'layers') and self.current_salinity_layer:
            for layer in self.layers:
                if hasattr(layer, 'name') and layer.name == self.current_salinity_layer:
                    if hasattr(layer, 'opacity'):
                        layer.opacity = opacity_value
                    elif hasattr(layer, 'set_opacity'):
                        layer.set_opacity(opacity_value)
                        
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
            width="100%",
            draw_control=False,
            fullscreen_control=False,
            toolbar_control=False,
        )
        # Add initial salinity layer using WMS
        new_map.update_salinity_layer(
            climate_rcp.value,
            year.value, 
            subsidence_enabled.value,
            riverbed_enabled.value
        )
        map_instance.set(new_map)
    
    # Update map when any scenario parameter changes (not opacity)
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
    # Watch for changes in scenario (not opacity)
    solara.use_effect(update_map_layer, [climate_rcp.value, year.value, subsidence_enabled.value, riverbed_enabled.value])

    # Only update opacity when slider changes
    def update_opacity():
        if map_instance.value:
            map_instance.value.set_salinity_opacity(opacity.value)
    solara.use_effect(update_opacity, [opacity.value])
    
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
                                # Opacity slider above the map
                    with solara.Row():
                        solara.SliderFloat(
                            label="Map Layer Opacity",
                            value=opacity.value,
                            on_value=opacity.set,
                            min=0.0,
                            max=1.0,
                            step=0.01,
                            # style={"width": "300px"}
                        )
            with solara.Column(style={"width": "120px", "flex": "none", "padding-left": "10px"}):
                # Add custom legend for the 2 PSU isoline using Markdown for SVG and label
                solara.Markdown(
                    f'''<span style="display:flex;align-items:center;margin-top:16px;">
                <svg width="32" height="12" style="vertical-align:middle;"><line x1="2" y1="6" x2="30" y2="6" stroke="{ISOLINE_STYLE['color']}" stroke-width="{ISOLINE_STYLE['weight']}"/></svg>
                <span style="font-size:13px;vertical-align:middle;margin-left:6px;">2 PSU Isoline</span>
                </span>''',
                )
                if legend_url.value:
                    solara.Image(legend_url.value)
        if error_message.value:
            solara.Error(error_message.value)