import solara
import leafmap as leafmap
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from general import (
    get_wms_config,
    get_isoline_gdf,
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
        self._current_wms_layers = []  # Store names, not objects
        self._current_gdf_layers = []
        self.legend_url = None

    def add_wms_layer_general(self, config, layer_name=None, opacity_value=0.8):
        """
        Add a WMS layer using a config dict (from get_scenario or similar).
        Expects config to have at least: url, layer, legend_url (optional).
        """
        self.clear_wms_layers()
        if config is not None:
            name = layer_name or config.get('layer', 'WMS Layer')
            self.add_wms_layer(
                url=config['url'],
                layers=config['layer'],
                name=name,
                format="image/png",
                transparent=True,
                opacity=opacity_value,
                attribution=config.get('attribution', "Deltares IDP"),
            )
            self._current_wms_layers = [name]
            self.legend_url = config.get('legend_url')
        else:
            self._current_wms_layers = []
            self.legend_url = None

    def add_gdf_layer_general(self, gdf, layer_name="GDF Layer", style=None, hover_style=None, info_mode=None):
        """
        Add a GeoDataFrame layer in a general way.
        """
        self.clear_gdf_layers()
        if gdf is not None:
            self.add_gdf(
                gdf,
                layer_name=layer_name,
                info_mode=info_mode,
                style=style,
                hover_style=hover_style
            )
            self._current_gdf_layers = [layer_name]
        else:
            self._current_gdf_layers = []

    def clear_wms_layers(self):
        if hasattr(self, 'layers') and self.layers:
            layers_to_remove = []
            for layer in self.layers:
                if hasattr(layer, 'name') and layer.name and 'WMS' in layer.name or (hasattr(layer, 'source') and getattr(layer, 'source', None) == 'wms'):
                    layers_to_remove.append(layer)
            for layer in layers_to_remove:
                try:
                    self.remove_layer(layer)
                except Exception as e:
                    print(f"Error removing WMS layer: {e}")
        self._current_wms_layers = []
        self.legend_url = None

    def clear_gdf_layers(self):
        if hasattr(self, 'layers') and self.layers and self._current_gdf_layers:
            layers_to_remove = []
            for layer in self.layers:
                if hasattr(layer, 'name') and layer.name in self._current_gdf_layers:
                    layers_to_remove.append(layer)
            for layer in layers_to_remove:
                try:
                    self.remove_layer(layer)
                except Exception as e:
                    print(f"Error removing GDF layer: {e}")
        self._current_gdf_layers = []

    def set_layer_opacity(self, opacity_value):
        # Set opacity for all current WMS layers by name
        if hasattr(self, 'layers') and self._current_wms_layers:
            for map_layer in self.layers:
                if hasattr(map_layer, 'name') and map_layer.name in self._current_wms_layers:
                    if hasattr(map_layer, 'opacity'):
                        map_layer.opacity = opacity_value
                    elif hasattr(map_layer, 'set_opacity'):
                        map_layer.set_opacity(opacity_value)


                        
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
        # Get config for WMS
        config = get_wms_config(climate_rcp.value, year.value, subsidence_enabled.value, riverbed_enabled.value)
        new_map.add_wms_layer_general(config, layer_name="Salinity WMS", opacity_value=opacity.value)
        # Get isoline (if enabled)
        if show_isoline.value:
            isoline_gdf = get_isoline_gdf(climate_rcp.value, year.value, subsidence_enabled.value, riverbed_enabled.value)
            if isoline_gdf is not None:
                new_map.add_gdf_layer_general(
                    isoline_gdf,
                    layer_name="2 PSU Isoline",
                    style=ISOLINE_STYLE,
                    hover_style=ISOLINE_STYLE
                )
        map_instance.set(new_map)
        # Set legend_url reactive
        legend_url.set(new_map.legend_url)

    # Update map when any scenario parameter changes (not opacity)
    def update_map_layer():
        if map_instance.value:
            is_updating.set(True)  # Show loading
            try:
                # Update WMS layer
                config = get_wms_config(climate_rcp.value, year.value, subsidence_enabled.value, riverbed_enabled.value)
                map_instance.value.add_wms_layer_general(config, layer_name="Salinity WMS", opacity_value=opacity.value)
                # Update isoline layer
                map_instance.value.clear_gdf_layers()
                if show_isoline.value:
                    isoline_gdf = get_isoline_gdf(climate_rcp.value, year.value, subsidence_enabled.value, riverbed_enabled.value)
                    if isoline_gdf is not None:
                        map_instance.value.add_gdf_layer_general(
                            isoline_gdf,
                            layer_name="2 PSU Isoline",
                            style=ISOLINE_STYLE,
                            hover_style=ISOLINE_STYLE
                        )
                # Set legend_url reactive
                legend_url.set(map_instance.value.legend_url)
            finally:
                is_updating.set(False)  # Hide loading
    # Watch for changes in scenario (not opacity)
    solara.use_effect(update_map_layer, [climate_rcp.value, year.value, subsidence_enabled.value, riverbed_enabled.value, show_isoline.value])

    # Only update opacity when slider changes
    def update_opacity():
        if map_instance.value:
            map_instance.value.set_layer_opacity(opacity.value)
            # Force Solara to re-render the map by updating the reactive value
            map_instance.set(map_instance.value)
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