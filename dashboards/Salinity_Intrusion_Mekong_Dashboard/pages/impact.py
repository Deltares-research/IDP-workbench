
import solara
import matplotlib.pyplot as plt
import numpy as np
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from general import YEAR_OPTIONS, SWITCH_LABELS, GROUNDWATER_SCENARIOS, RIVERBED_SCENARIOS

year = solara.reactive("2050")
subsidence_name = GROUNDWATER_SCENARIOS["RCP 8.5"]["name"]
riverbed_name = RIVERBED_SCENARIOS["RCP 8.5"]["name"]

# Scenario names and info (copied from hazard.py, but only relevant scenarios)
SCENARIOS = [
    {
        "name": "Baseline (Current Situation)",
        "description": "Present-day baseline scenario. No climate change or anthropogenic impacts are considered."
    },
    {
        "name": "Climate Change (RCP 8.5)",
        "description": "Future scenario with climate change (RCP 8.5) only. Select a year to view projections."
    },
    {
        "name": "Climate Change + Groundwater Extraction",
        "description": "Future scenario with climate change (RCP 8.5) and groundwater extraction impacts."
    },
    {
        "name": "Climate Change + Groundwater Extraction + Sediment Starvation",
        "description": "Future scenario with climate change (RCP 8.5), groundwater extraction, and sediment starvation impacts."
    }
]

# Reactive variables for scenario selection
baseline_enabled = solara.reactive(True)  # Always enabled
climate_enabled = solara.reactive(False)
groundwater_enabled = solara.reactive(False)
sediment_enabled = solara.reactive(False)

# Error message state for GUI alerts
error_message = solara.reactive(None)

regions = [
    "TraVinh", "TienGi", "BenTre", "KienGi", "BacLieu", "SocTrang", "CanTho", "HuaGi", "AnGi", "CaMau", "DongTh", "VinghLn"
]

# Dummy rice yield data for each scenario (values in tons/ha)
dummy_yield = {
    "Baseline": [5.2, 5.5, 5.3, 5.4, 5.1, 5.6, 5.7, 5.3, 5.8, 5.0, 5.2, 5.4],
    "Climate Change": [4.8, 5.0, 4.9, 5.0, 4.7, 5.1, 5.2, 4.9, 5.3, 4.6, 4.8, 5.0],
    "Climate Change + Groundwater Extraction": [4.2, 4.5, 4.3, 4.4, 4.1, 4.6, 4.7, 4.3, 4.8, 4.0, 4.2, 4.4],
    "Climate Change + Groundwater Extraction + Sediment Starvation": [3.7, 4.0, 3.8, 3.9, 3.6, 4.1, 4.2, 3.8, 4.3, 3.5, 3.7, 3.9]
}

def plot_yield(scenario):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar(regions, dummy_yield[scenario], color="#4caf50")
    ax.set_ylabel("Rice Yield (tons/ha)")
    ax.set_title(f"Rice Yield by Region - {scenario}")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    return fig

@solara.component
def Page():
    def get_scenario_description():
        if sediment_enabled.value:
            return f"**{SCENARIOS[3]['name']}**\n\n{SCENARIOS[3]['description']}\n\n**Year:** {year.value}"
        elif groundwater_enabled.value:
            return f"**{SCENARIOS[2]['name']}**\n\n{SCENARIOS[2]['description']}\n\n**Year:** {year.value}"
        elif climate_enabled.value:
            return f"**{SCENARIOS[1]['name']}**\n\n{SCENARIOS[1]['description']}\n\n**Year:** {year.value}"
        else:
            return f"**{SCENARIOS[0]['name']}**\n\n{SCENARIOS[0]['description']}"

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
                                value=groundwater_enabled.value,
                                on_value=lambda v: groundwater_enabled.set(v),
                                disabled=False
                            )
                        else:
                            solara.Switch(
                                label=f"{SWITCH_LABELS['groundwater']} - {subsidence_name} (requires climate change)",
                                value=False,
                                on_value=lambda x: None,
                                disabled=True
                            )
                            if groundwater_enabled.value:
                                groundwater_enabled.set(False)
                        if groundwater_enabled.value:
                            solara.Switch(
                                label=f"{SWITCH_LABELS['riverbed']} - {riverbed_name}",
                                value=sediment_enabled.value,
                                on_value=lambda v: sediment_enabled.set(v),
                                disabled=False
                            )
                        else:
                            solara.Switch(
                                label=SWITCH_LABELS["riverbed_disabled"].format(riverbed_name),
                                value=False,
                                on_value=lambda x: None,
                                disabled=True
                            )
                            if sediment_enabled.value:
                                sediment_enabled.set(False)
                        if not climate_enabled.value and groundwater_enabled.value:
                            groundwater_enabled.set(False)
                        if not groundwater_enabled.value and sediment_enabled.value:
                            sediment_enabled.set(False)
                    with solara.Column(style={"flex": "1", "padding-left": "10px"}):
                        with solara.Card(margin=0, elevation=2):
                            solara.Markdown(get_scenario_description())
            # Right column for graph
            with solara.Column(style={"flex": "1"}):
                # Select scenario for plotting
                if sediment_enabled.value:
                    scenario = "Climate Change + Groundwater Extraction + Sediment Starvation"
                elif groundwater_enabled.value:
                    scenario = "Climate Change + Groundwater Extraction"
                elif climate_enabled.value:
                    scenario = "Climate Change"
                else:
                    scenario = "Baseline"
                solara.FigureMatplotlib(plot_yield(scenario))
        if error_message.value:
            solara.Error(error_message.value)
