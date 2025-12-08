import leafmap as leafmap
# import leafmap.maplibregl as leafmap

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
                        
    def add_choropleth(
        self,
        data,
        column,
        cmap=None,
        colors=None,
        labels=None,
        scheme="Quantiles",
        k=5,
        add_legend=True,
        legend_title=None,
        legend_position="bottomright",
        legend_kwds=None,
        classification_kwds=None,
        style_function=None,
        highlight_function=None,
        layer_name="Choropleth",
        info_mode="on_hover",
        encoding="utf-8",
        **kwargs,
        ):
        self.clear_choropleth_layers()
        self.add_data(
            data=data,
            column=column,
            cmap=cmap,
            colors=colors,
            labels=labels,
            scheme=scheme,
            k=k,
            add_legend=add_legend,
            legend_title=legend_title,
            legend_position=legend_position,
            legend_kwds=legend_kwds,
            classification_kwds=classification_kwds,
            style_function=style_function,
            highlight_function=highlight_function,
            layer_name=layer_name,
            info_mode=info_mode,
            encoding=encoding,
            **kwargs,
        )
        self._current_choropleth_layers = [layer_name]

    def clear_choropleth_layers(self):
        if hasattr(self, 'layers') and self.layers and hasattr(self, '_current_choropleth_layers'):
            layers_to_remove = []
            for layer in self.layers:
                if hasattr(layer, 'name') and layer.name in self._current_choropleth_layers:
                    layers_to_remove.append(layer)
            for layer in layers_to_remove:
                try:
                    self.remove_layer(layer)
                except Exception as e:
                    print(f"Error removing choropleth layer: {e}")
        self._current_choropleth_layers = []
        self.legend_url = None
        # Remove the choropleth legend control if present
        if hasattr(self, "controls") and hasattr(self, "remove_control"):
            # Try to find a legend control in self.controls
            for info_control in self.controls:
                try:
                    self.remove_control(info_control)
                except Exception as e:
                    print(f"Error removing choropleth legend control: {e}")
