import pandas as pd
from pathlib import Path
import solara
import matplotlib.pyplot as plt
import folium
import folium.plugins
import solara

value_subsidence = solara.reactive(-20)
scenarios = solara.reactive(["RCP4.5"])
value_slr = solara.reactive(-2)
value_glob_pop = solara.reactive(0)
value_future_shoreline = solara.reactive(0)

# RCP Scenarios data
rcp_data = [
    {
        "short_name": "RCP2.6",
        "description": "A pathway that aims to limit global warming to below 2°C above pre-industrial levels, with significant reductions in greenhouse gas emissions."
    },
    {
        "short_name": "RCP4.5",
        "description": "A stabilization scenario where greenhouse gas emissions peak around 2040 and then decline, leading to a moderate level of warming."
    },
    {
        "short_name": "RCP6.0",
        "description": "Similar to RCP4.5 but with less stringent climate policies, leading to higher emissions and a moderate level of warming."
    },
    {
        "short_name": "RCP8.5",
        "description": "A high greenhouse gas emissions scenario with continued reliance on fossil fuels, leading to significant global warming (potentially exceeding 4°C)."
    }
]

# Create a DataFrame
rcp_df = pd.DataFrame(rcp_data)

@solara.component
def Page():

    def Controls():
        solara.Text("Subsidence")
        solara.SliderInt("", value=value_subsidence, min=-20, max=0)

        solara.Text("SLR")
        solara.SelectMultiple("Scenario", all_values=[str(k) for k in rcp_df["short_name"].unique().tolist()], values=scenarios)
        solara.SliderInt("", value=value_slr, min=-2, max=2)

        solara.Text("Glob-pop")
        solara.SliderInt("", value=value_glob_pop, min=0, max=3)

        solara.Text("Future shoreline")
        solara.SliderInt("", value=value_future_shoreline, min=1, max=100)

    def View():
        def create_map(latitude, longitude):
            map = folium.Map(location=[latitude, longitude], zoom_start=12)
            display(map)
        latitude = 52.01  # Latitude for Delft
        longitude = 4.36   # Longitude for Delft
        create_map(latitude, longitude)

    with solara.Sidebar():
        Controls()
    View()
