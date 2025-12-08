import solara
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../utils')))

from general import YEAR_OPTIONS, SWITCH_LABELS, GROUNDWATER_SCENARIOS, RIVERBED_SCENARIOS, CLIMATE_SCENARIOS, BASELINE_SCENARIO, get_impact_gdf


# Only RCP 8.5 and year 2050 for impact page
rcp = solara.reactive("RCP 8.5")
year = solara.reactive("2050")
subsidence_name = GROUNDWATER_SCENARIOS[rcp.value]["name"]
riverbed_name = RIVERBED_SCENARIOS[rcp.value]["name"]


# Build scenarios from general.py
SCENARIOS = [
    BASELINE_SCENARIO,
    {
        "name": f"Climate Change ({rcp.value})",
        "description": CLIMATE_SCENARIOS[rcp.value]["description"],
        "scenario_str": CLIMATE_SCENARIOS[rcp.value]["scenario_str"] + "y"
    },
    {
        "name": f"Climate Change + Groundwater Extraction",
        "description": CLIMATE_SCENARIOS[rcp.value]["description"] + "\n" + GROUNDWATER_SCENARIOS[rcp.value]["description"],
        "scenario_str": CLIMATE_SCENARIOS[rcp.value]["scenario_str"] + GROUNDWATER_SCENARIOS[rcp.value]["scenario_str"] + "y"
    },
    {
        "name": f"Climate Change + Groundwater Extraction + Sediment Starvation",
        "description": CLIMATE_SCENARIOS[rcp.value]["description"] + "\n" + GROUNDWATER_SCENARIOS[rcp.value]["description"] + "\n" + RIVERBED_SCENARIOS[rcp.value]["description"],
        "scenario_str": CLIMATE_SCENARIOS[rcp.value]["scenario_str"] + GROUNDWATER_SCENARIOS[rcp.value]["scenario_str"] + RIVERBED_SCENARIOS[rcp.value]["scenario_str"] + "y"
    }
]


# Only switches for scenario selection
baseline_enabled = solara.reactive(True)  # Always enabled
climate_enabled = solara.reactive(False)
subsidence_enabled = solara.reactive(False)
riverbed_enabled = solara.reactive(False)

# Error message state for GUI alerts
error_message = solara.reactive(None)


# Map plot logic (similar to hazard)
from map import Map
map_instance = solara.reactive(None)


@solara.component
def Page():
    def get_scenario_description():
        if riverbed_enabled.value:
            return f"**{SCENARIOS[3]['name']}**\n\n{SCENARIOS[3]['description']}\n\n**Year:** {year.value}"
        elif subsidence_enabled.value:
            return f"**{SCENARIOS[2]['name']}**\n\n{SCENARIOS[2]['description']}\n\n**Year:** {year.value}"
        elif climate_enabled.value:
            return f"**{SCENARIOS[1]['name']}**\n\n{SCENARIOS[1]['description']}\n\n**Year:** {year.value}"
        else:
            return f"**{SCENARIOS[0]['name']}**\n\n{SCENARIOS[0]['description']}"


    # Create map instance if it doesn't exist
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

    # Directly update map with GDF only (no WMS, no opacity)
    def update_map():
        if map_instance.value:
            map_instance.value.clear_gdf_layers()
            climate = climate_enabled.value
            subs = subsidence_enabled.value
            riverbed = riverbed_enabled.value
            gdf, config = get_impact_gdf(climate, subs, riverbed)
            if gdf is not None:
                map_instance.value.add_choropleth(
                    data=gdf,
                    column=config["data_column"],
                    scheme="UserDefined",
                    colors=config["colors"],
                    labels=config["labels"],
                    classification_kwds={"bins": config["bins"]},
                    info_mode=None,
                    # add_legend=False
                )
                
    solara.use_effect(update_map, [climate_enabled.value, subsidence_enabled.value, riverbed_enabled.value])

    with solara.Column():
        with solara.Row():
            # Left column for controls
            with solara.Column(style={"width": "50%", "padding": "20px"}):
                solara.Markdown("## Scenario Selection")
                with solara.Row():
                    with solara.Column(style={"width": "40%"}):
                        solara.Text("Baseline (Current Situation)")
                        solara.Switch(
                            label=SCENARIOS[1]["name"],
                            value=climate_enabled.value,
                            on_value=lambda v: climate_enabled.set(v),
                            disabled=False
                        )
                        if climate_enabled.value:
                            solara.Switch(
                                label=f"{SWITCH_LABELS['groundwater']} - {subsidence_name}",
                                value=subsidence_enabled.value,
                                on_value=lambda v: subsidence_enabled.set(v),
                                disabled=False
                            )
                        else:
                            solara.Switch(
                                label=f"{SWITCH_LABELS['groundwater']} - {subsidence_name} (requires climate change)",
                                value=False,
                                on_value=lambda x: None,
                                disabled=True
                            )
                            if subsidence_enabled.value:
                                subsidence_enabled.set(False)
                        if subsidence_enabled.value:
                            solara.Switch(
                                label=f"{SWITCH_LABELS['riverbed']} - {riverbed_name}",
                                value=riverbed_enabled.value,
                                on_value=lambda v: riverbed_enabled.set(v),
                                disabled=False
                            )
                        else:
                            solara.Switch(
                                label=SWITCH_LABELS["riverbed_disabled"].format(riverbed_name),
                                value=False,
                                on_value=lambda x: None,
                                disabled=True
                            )
                            if riverbed_enabled.value:
                                riverbed_enabled.set(False)
                        if not climate_enabled.value and subsidence_enabled.value:
                            subsidence_enabled.set(False)
                        if not subsidence_enabled.value and riverbed_enabled.value:
                            riverbed_enabled.set(False)
                    with solara.Column(style={"flex": "1", "padding-left": "10px"}):
                        with solara.Card(margin=0, elevation=2):
                            solara.Markdown(get_scenario_description())
            # Right column for map
            with solara.Column(style={"flex": "1"}):
                # Show map for selected scenario (GDF only)
                if map_instance.value:
                    solara.display(map_instance.value)
        if error_message.value:
            solara.Error(error_message.value)
