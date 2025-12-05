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
show_isoline = solara.reactive(False)


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
        self.add_basemap("Esri.WorldImagery")
        self.current_salinity_layer = None  # Track current salinity layer
        self.current_isoline_layer = None   # Track current isoline layer

    def set_wms_layer(self, rcp, year_val, subsidence, riverbed):
        config = get_scenario(rcp, year_val, subsidence, riverbed, show_isoline=False)
        scenario_desc = f"{rcp} - {year_val}"
        if subsidence and riverbed:
            scenario_desc += " (Subsidence + Riverbed)"
        elif subsidence:
            scenario_desc += " (Subsidence)"
        else:
            scenario_desc += " (Climate only)"
        layer_name = f"Salinity Increase: {scenario_desc}"
        self.clear_wms_layer()
        if config is not None:
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
            legend_url.set(f"{config['url'].split('?')[0]}?REQUEST=GetLegendGraphic&VERSION=1.0.0&FORMAT=image/png&LAYER={config['layer']}")
        else:
            self.current_salinity_layer = None
            legend_url.set(None)

    def set_isoline_layer(self, rcp, year_val, subsidence, riverbed, show_isoline):
        config = get_scenario(rcp, year_val, subsidence, riverbed, show_isoline=show_isoline)
        scenario_desc = f"{rcp} - {year_val}"
        if subsidence and riverbed:
            scenario_desc += " (Subsidence + Riverbed)"
        elif subsidence:
            scenario_desc += " (Subsidence)"
        else:
            scenario_desc += " (Climate only)"
        layer_name = f"Salinity Increase: {scenario_desc} 2 PSU Isoline"
        self.clear_isoline_layer()
        if show_isoline and config is not None and 'isoline' in config:
            self.add_gdf(
                config['isoline'],
                layer_name=layer_name,
                info_mode=None,
                style=ISOLINE_STYLE,
                hover_style=ISOLINE_STYLE
            )
            self.current_isoline_layer = layer_name
        else:
            self.current_isoline_layer = None

    def clear_wms_layer(self):
        if hasattr(self, 'layers') and self.layers:
            layers_to_remove = []
            for layer in self.layers:
                if hasattr(layer, 'name') and layer.name and 'Salinity Increase' in layer.name and '2 PSU Isoline' not in layer.name:
                    layers_to_remove.append(layer)
            for layer in layers_to_remove:
                try:
                    self.remove_layer(layer)
                except Exception as e:
                    print(f"Error removing WMS layer: {e}")
        self.current_salinity_layer = None

    def clear_isoline_layer(self):
        if hasattr(self, 'layers') and self.layers:
            layers_to_remove = []
            for layer in self.layers:
                if hasattr(layer, 'name') and layer.name and '2 PSU Isoline' in layer.name:
                    layers_to_remove.append(layer)
            for layer in layers_to_remove:
                try:
                    self.remove_layer(layer)
                except Exception as e:
                    print(f"Error removing isoline layer: {e}")
        self.current_isoline_layer = None

    def set_salinity_opacity(self, opacity_value):
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
        new_map.set_wms_layer(
            climate_rcp.value,
            year.value,
            subsidence_enabled.value,
            riverbed_enabled.value
        )
        new_map.set_isoline_layer(
            climate_rcp.value,
            year.value,
            subsidence_enabled.value,
            riverbed_enabled.value,
            show_isoline.value
        )
        map_instance.set(new_map)

    # Update map when any scenario parameter changes (not opacity)
    def update_map_layer():
        if map_instance.value:
            is_updating.set(True)  # Show loading
            try:
                map_instance.value.set_wms_layer(
                    climate_rcp.value,
                    year.value,
                    subsidence_enabled.value,
                    riverbed_enabled.value
                )
                map_instance.value.set_isoline_layer(
                    climate_rcp.value,
                    year.value,
                    subsidence_enabled.value,
                    riverbed_enabled.value,
                    show_isoline.value
                )
            finally:
                is_updating.set(False)  # Hide loading
    # Watch for changes in scenario (not opacity)
    solara.use_effect(update_map_layer, [climate_rcp.value, year.value, subsidence_enabled.value, riverbed_enabled.value, show_isoline.value])

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
                # Show Isoline toggle above the legend
                solara.Switch(
                    label="Show Isoline",
                    value=show_isoline.value,
                    on_value=show_isoline.set
                )
                # Add custom legend for the 2 PSU isoline only if toggled
                if show_isoline.value:
                    solara.Markdown(
                        f'''<span style="display:flex;align-items:center;margin-top:16px;">
                        <svg width="32" height="12" style="vertical-align:middle;"><line x1="2" y1="6" x2="30" y2="6" stroke="{ISOLINE_STYLE['color']}" stroke-width="{ISOLINE_STYLE['weight']}"/></svg>
                        <span style="font-size:13px;vertical-align:middle;margin-left:6px;">2 PSU Isoline</span>
                        </span>''',
                    )
                # Always show raster legend image if available
                if legend_url.value:
                    solara.Image(legend_url.value)
        if error_message.value:
            solara.Error(error_message.value)