import pandas as pd
from pathlib import Path
import solara
import matplotlib.pyplot as plt
import folium
import folium.plugins
import solara
import leafmap
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

value_subsidence = solara.reactive(-20)
scenarios = solara.reactive(["2-45"])
scenarios_ipcc = ["1-26", "2-45", "5-85"]
scenario_ipcc= solara.reactive("1-26")
# value_slr = solara.reactive(-2)
year_value = solara.reactive(2020)
value_slr = solara.reactive((-10, 10))
value_glob_pop = solara.reactive(0)
value_future_shoreline = solara.reactive(0)
name_layer = solara.reactive("Layer")
opacity = solara.reactive(10)



# RCP Scenarios data
rcp_data = [
    {
        "short_name": "1-26",
        "description": "RCP2.6. A pathway that aims to limit global warming to below 2°C above pre-industrial levels, with significant reductions in greenhouse gas emissions."
    },
    {
        "short_name": "2-45",
        "description": "RCP4.5. A stabilization scenario where greenhouse gas emissions peak around 2040 and then decline, leading to a moderate level of warming."
    },
    {
        "short_name": "5-85",
        "description": "RCP8.5. A high greenhouse gas emissions scenario with continued reliance on fossil fuels, leading to significant global warming (potentially exceeding 4°C)."
    }
]

# Create a DataFrame
rcp_df = pd.DataFrame(rcp_data)

@solara.component
def Page():

    def Controls():
        # solara.Markdown(r'''
        #     # International Delta Platform

        #     ## Dashboard
        #     This is a markdown text, **bold** and *italic* text is supported.

        #     ## Expressions
        #     Also, $x^2$ is rendered as math.

        #     Or multiline math:
        #     $$
        #     \int_0^1 x^2 dx = \frac{1}{3}
        #     $$

        #     ''')

        solara.Markdown(r'''
            # International Delta Platform

            ## Subsidence

            ''')

        solara.SliderFloat("", value=value_subsidence, min=-20, max=0)
        solara.Markdown(r'''## Sea Level Rise (SLR)''')
        solara.SliderInt("Select a year:", value=year_value, min=2020, max=2130, step=10)
        solara.Markdown(f"**Selected Year**:  {year_value.value}")

        solara.SelectMultiple("Select multiple scenarios", all_values=[str(k) for k in rcp_df["short_name"].unique().tolist()], values=scenarios)
        solara.Select(label="Select an scenario", value=scenario_ipcc, values=scenarios_ipcc)
        # solara.SliderInt("", value=value_slr, min=-2, max=2)
        solara.SliderRangeInt("Select a SLR range", value=value_slr, min=-100, max=150)
        solara.Markdown(f"**SLR range value**: {value_slr}")
        with solara.Row():
            solara.Button("Reset values", on_click=lambda: value_slr.set((-100, 150)))
        solara.SliderInt("Select a opacity:", value=opacity, min=0, max=100, step=1)
        solara.InputText(label="Layer name", value= name_layer, continuous_update=True)
        solara.Markdown(f"**Stac product**: 'https://storage.googleapis.com/dgds-data-public/coclico/ar6_slr/ssp={scenario_ipcc.value}/slr_ens50.0/{str(year_value.value)}.tif'")

        solara.Markdown(r'''## Glob-pop''')
        solara.SliderInt("", value=value_glob_pop, min=0, max=3)

        solara.Markdown(r'''## Future shoreline''')
        solara.SliderFloat("", value=value_future_shoreline, min=1, max=100)


    def View():
        def create_map(latitude, longitude):
            map = folium.Map(location=[latitude, longitude], zoom_start=12)
            display(map)
        latitude = 52.01  # Latitude for Delft
        longitude = 4.36   # Longitude for Delft
        create_map(latitude, longitude)


    def View_leaf():
        def add_map():
            Map = leafmap.Map()
            return Map

        def load_stac(Map, url, name_cog):
            leafmap.cog_bounds(url)
            leafmap.cog_center(url)
            leafmap.cog_bands(url)
            leafmap.cog_tile(url)

            vmin = value_slr.value[0]
            vmax = value_slr.value[1]
            cmap = plt.get_cmap("viridis")  # Replace "viridis" with any other colormap name
            norm = mcolors.Normalize(vmin=vmin, vmax=vmax)  # Adjust range based on raster data values

            # Convert the colormap to a dictionary for leafmap
            custom_cmap = {i: mcolors.to_hex(cmap(norm(i))) for i in range(vmin, vmax)}
            opacity_value = opacity.value/100
            Map.add_cog_layer(url, colormap=custom_cmap, name=name_cog, opacity=opacity_value)
            return Map
        
        def display_map(Map):
            display(Map)
        
        url = f'https://storage.googleapis.com/dgds-data-public/coclico/ar6_slr/ssp={scenario_ipcc.value}/slr_ens50.0/{str(year_value.value)}.tif'
        Map = add_map()
        load_stac(Map, url, name_layer.value)
        display_map(Map)


    with solara.Sidebar():
        Controls()
    # View()
    View_leaf()