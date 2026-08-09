"""Absolute salinity hazard for baseline years 2014–2016 (GeoServer WMS).

Layout and map helpers mirror solara_mekong.pages.hazard (view_dashboard):
uses general.get_baseline_salinity_wms_config + map.Map.add_wms_layer_general.
"""

import solara

from solara_mekong.utils.general import (
    BASELINE_YEAR_OPTIONS,
    get_baseline_salinity_wms_config,
)
from solara_mekong.utils.map import Map

year = solara.reactive("2015")
opacity = solara.reactive(0.85)
map_instance = solara.reactive(None)
legend_url = solara.reactive(None)
error_message = solara.reactive(None)


def update_map():
    if map_instance.value is None:
        return
    try:
        config = get_baseline_salinity_wms_config(year.value)
        map_instance.value.add_wms_layer_general(
            config,
            layer_name=f"Salinity WMS {year.value}",
            opacity_value=opacity.value,
        )
        legend_url.set(map_instance.value.legend_url)
        error_message.set(None)
    except Exception as exc:
        error_message.set(str(exc))


def update_opacity():
    if map_instance.value:
        map_instance.value.set_layer_opacity(opacity.value)
        map_instance.set(map_instance.value)


@solara.component
def Page():
    if map_instance.value is None:
        new_map = Map(
            zoom=8,
            center=(10, 105.7),
            height="600px",
            width="100%",
            draw_control=False,
            fullscreen_control=False,
            toolbar_control=False,
        )
        config = get_baseline_salinity_wms_config(year.value)
        new_map.add_wms_layer_general(
            config,
            layer_name=f"Salinity WMS {year.value}",
            opacity_value=opacity.value,
        )
        map_instance.set(new_map)
        legend_url.set(new_map.legend_url)

    solara.use_effect(update_map, [year.value])
    solara.use_effect(update_opacity, [opacity.value])

    with solara.Column():
        solara.Markdown("## Hazard: Salinity for 2014, 2015 and 2016")
        with solara.Row():
            with solara.Column(style={"width": "50%", "padding": "20px"}):
                solara.Select(
                    label="Year",
                    value=year.value,
                    on_value=year.set,
                    values=BASELINE_YEAR_OPTIONS,
                )
                cfg = get_baseline_salinity_wms_config(year.value) or {}
                with solara.Card(margin=0, elevation=2):
                    solara.Markdown(
                        f'**Layer:** '
                        f'<code style="color:#1565c0;background:#f0f4f8;'
                        f'padding:2px 8px;border-radius:4px;font-size:0.95em;">'
                        f'{cfg.get("layer", "")}</code>'
                    )
                if error_message.value:
                    solara.Error(error_message.value)

            with solara.Column(style={"flex": "1"}):
                if map_instance.value:
                    solara.display(map_instance.value)
                with solara.Row():
                    solara.SliderFloat(
                        label="Map Layer Opacity",
                        value=opacity.value,
                        on_value=opacity.set,
                        min=0.0,
                        max=1.0,
                        step=0.01,
                    )

            with solara.Column(
                style={"width": "120px", "flex": "none", "padding-left": "10px"}
            ):
                if legend_url.value:
                    solara.Image(legend_url.value)

        solara.Info(
            """
            On this page you can explore absolute salinity (PSU) in the Mekong Delta
            for the historical baseline years 2014, 2015 and 2016.
            Use the year selector to switch maps; the layer name and the compact
            right-side legend update with your selection. Adjust opacity to compare
            with the basemap.
            """
        )
