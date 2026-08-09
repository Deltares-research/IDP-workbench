"""Crop productivity correction impact (2014–2016 freshwater zones).

Mirrors solara_mekong.pages.impact: data via general.get_crop_impact_gdf,
rendering via map.Map.add_choropleth / add_gdf_layer_general.
"""

import solara

from solara_mekong.utils.general import (
    BASELINE_YEAR_OPTIONS,
    CROP_METRIC_OPTIONS,
    CROP_SEASON_OPTIONS,
    get_crop_impact_gdf,
)
from solara_mekong.utils.map import Map

year = solara.reactive("2016")
crop_name = solara.reactive("WinterSpring (ha)")
metric = solara.reactive("corrected_yield")
map_instance = solara.reactive(None)
error_message = solara.reactive(None)


def update_map():
    if map_instance.value is None:
        return
    try:
        gdf, config = get_crop_impact_gdf(
            year.value, crop_name.value, metric.value
        )
        # Constant columns (e.g. all-zero salinity) cannot be classified by mapclassify.
        if config["k"] <= 1:
            color = config["colors"][0] if config["colors"] else "#41b6c4"
            map_instance.value.clear_choropleth_layers()
            map_instance.value.add_gdf_layer_general(
                gdf,
                layer_name="Crop productivity",
                style={
                    "fillColor": color,
                    "color": "#333333",
                    "weight": 1,
                    "fillOpacity": 0.7,
                },
                info_mode="on_hover",
            )
        else:
            map_instance.value.clear_gdf_layers()
            map_instance.value.add_choropleth(
                data=gdf,
                column=config["data_column"],
                scheme=config["scheme"],
                k=config["k"],
                colors=config["colors"],
                labels=config.get("labels"),
                legend_title=config["title"],
                layer_name="Crop productivity",
            )
        error_message.set(None)
    except Exception as exc:
        error_message.set(str(exc))


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
        map_instance.set(new_map)

    solara.use_effect(
        update_map,
        [year.value, crop_name.value, metric.value],
    )

    with solara.Column():
        solara.Markdown("## Impact: Crop Productivity Correction")
        with solara.Row():
            with solara.Column(style={"width": "50%", "padding": "20px"}):
                solara.Select(
                    label="Year",
                    value=year.value,
                    on_value=year.set,
                    values=BASELINE_YEAR_OPTIONS,
                )
                solara.Select(
                    label="Rice season",
                    value=crop_name.value,
                    on_value=crop_name.set,
                    values=CROP_SEASON_OPTIONS,
                )
                solara.Select(
                    label="Metric",
                    value=metric.value,
                    on_value=metric.set,
                    values=CROP_METRIC_OPTIONS,
                )
                with solara.Card(margin=0, elevation=2):
                    solara.Markdown(
                        f'**Layer:** '
                        f'<code style="color:#1565c0;background:#f0f4f8;'
                        f'padding:2px 8px;border-radius:4px;font-size:0.95em;">'
                        f'{metric.value} · {crop_name.value} · {year.value}</code>'
                    )
                if error_message.value:
                    solara.Error(error_message.value)

            with solara.Column(style={"flex": "1"}):
                if map_instance.value:
                    solara.display(map_instance.value)

        solara.Info(
            """
            On this page you can explore crop productivity correction over freshwater
            zones for 2014, 2015 and 2016. Choose a year, rice season, and metric
            (e.g. corrected yield, hectares, salinity); the choropleth map updates
            to show how productivity varies across zones.
            """
        )
