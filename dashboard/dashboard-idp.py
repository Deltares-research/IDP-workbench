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
import rioxarray as rio
import time
import threading
import asyncio
import geopandas as gpd
from folium import raster_layers
import geemap
import folium
from folium import raster_layers
import numpy as np
import geopandas as gpd
import pandas as pd
import geopandas as gpd
from shapely.geometry import shape
from shapely.geometry import shape, MultiPolygon
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from mpl_toolkits.axes_grid1 import make_axes_locatable
import leafmap
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.cm as cm

# Funcitons
# Function to filter geodatabase by region name (e.g. Ghana)
def delta_filter(df, district_values):
    df_dist = df.loc[df["Location"].isin([district_values])]
    return df_dist

# Data
# RCP description, bounding boxes of deltas, metadata of subsidence stac collection 
rcp_df = pd.read_csv("dashboard/data/rcp_scenarios.csv")
bbox_gd = gpd.read_file("dashboard/data/Deltas.geojson")
gdf_stac = gpd.read_file("dashboard/data/stac_metadata.geojson")

# Static variables
scenarios_ipcc = ["1-26", "2-45", "5-85"]
deltas = bbox_gd["Location"].unique().tolist()

# Dynamic variables. The variables require to be inicialize
# Zone
delta = solara.reactive("Mekong Delta")
# Sea level rise
slr_scenario= solara.reactive("1-26")
slr_year   = solara.reactive(2020)

slr_range = solara.reactive((-90, 90))
slr_opacity = solara.reactive(100)
slr_mean = solara.reactive(0)
slr_max = solara.reactive(0)
slr_min = solara.reactive(0)
# Subsidence
sub_range = solara.reactive((0, 14))
sub_opacity = solara.reactive(100)

# Inicializing variables through dictionary
applied_state = solara.reactive({
"delta": "Mekong Delta",
"slr_range": (-90, 90),
"sub_range": (0, 14),
"slr_opacity": 100,
"sub_opacity": 100,
"slr_year": 2020,
"slr_scenario": "1-26",
"slr_mean": 0,
"slr_max": 0,
"slr_min": 0,
})

@solara.component
def Page():
    def Controls():
        solara.Markdown(r'''
            # International Delta Platform      
            ## Zone 
            ''')
        solara.Select(label="Select a Delta", value=delta, values=deltas)
        solara.Markdown(r'''
            ## Sea Level Rise (SLR)
            ''')
        solara.Select(label="Select an scenario", value=slr_scenario, values=scenarios_ipcc)
        solara.SliderInt("Select a year:", value=slr_year, min=2020, max=2130, step=10, thumb_label= "always")
        solara.SliderRangeInt("Select a SLR range [mm]", value=slr_range, min=-90, max=90, thumb_label= "always")
        solara.SliderInt("Select a opacity:", value=slr_opacity, min=0, max=100, step=1)
        solara.Markdown(r'''
            ## Subsidence
            ''')
        solara.SliderRangeInt("Select a subsidence range [probability]", value=sub_range, min=0, max=14, thumb_label= "always")
        solara.SliderInt("Select a opacity:", value=sub_opacity, min=0, max=100, step=1)

        def update_gdf():
            applied_state.value  = {
                "delta": delta.value,
                "slr_range": slr_range.value,
                "sub_range": sub_range.value,
                "slr_opacity": slr_opacity.value,
                "sub_opacity": sub_opacity.value,
                "slr_year": slr_year.value,
                "slr_scenario": slr_scenario.value,
                "slr_mean": slr_mean.value,
                "slr_max": slr_max.value,
                "slr_min": slr_min.value,
            }
        solara.Markdown(r'''
            ## 
            ''')
        with solara.Row():
            solara.Button("Get statistics", on_click=update_gdf)

    def View_leaf(): 
            
        def load_stac_slr(Map, url, name_cog):
            vmin = applied_state.value.get("slr_range")[0]
            vmax = applied_state.value.get("slr_range")[1]
            cmap = plt.get_cmap("viridis")  
            norm = mcolors.Normalize(vmin=vmin, vmax=vmax)  
            custom_cmap = {i: mcolors.to_hex(cmap(norm(i))) for i in range(vmin, vmax)}
            opacity_value = applied_state.value.get("slr_opacity")/100
            Map.add_cog_layer(url, colormap=custom_cmap, name=name_cog, opacity=opacity_value, nodata=np.nan, zoom_to_layer=False)
            return Map

        def load_stac_sub_list(Map, url_list):
            vmin = applied_state.value.get("sub_range")[0] 
            vmax = applied_state.value.get("sub_range")[1]
            cmap = plt.get_cmap("YlOrRd")  
            norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
            custom_cmap = {i: mcolors.to_hex(cmap(norm(i))) for i in range(vmin, vmax)}
            opacity_value = applied_state.value.get("sub_opacity")/100
            for url in url_list:
                Map.add_cog_layer(url, colormap=custom_cmap, name=url.split('B01_')[1], opacity=opacity_value, zoom_to_layer=False)
            return Map

        def load_gdf(Map, df, district_values):
            df_delta = df.loc[df["Location"].isin([district_values])]
            Map.add_gdf(df_delta, layer_name="Deltas", style={"fillColor": "yellow", "color": "yellow", "weight": 3, "fillOpacity": 0.1})
            Map.zoom_to_gdf(df_delta)
            display(Map)
            return Map
        
        def get_sub_id(gdf):
            bbox_gdf_site = bbox_gd[bbox_gd['Location']==applied_state.value.get("delta")]
            if gdf.crs != bbox_gdf_site.crs:
                gdf = gdf.to_crs(bbox_gdf_site.crs)
            centroids = bbox_gdf_site.geometry.centroid
            selected_geometries = []
            for centroid in centroids:
                overlapping = gdf[gdf.geometry.intersects(centroid)]
                selected_geometries.append(overlapping)
            overlapping_geometries = gpd.GeoDataFrame(pd.concat(selected_geometries, ignore_index=True), crs=gdf.crs)
            return overlapping_geometries['id'].values.tolist()[0]
        
        id = get_sub_id(gdf_stac)

        url_sub = f'https://storage.googleapis.com/dgds-data-public/gca/SOTC/Haz-Land_Sub_2040_COGs/{id}.tif' 
        url_slr = f'https://storage.googleapis.com/dgds-data-public/coclico/ar6_slr/ssp={applied_state.value.get("slr_scenario")}/slr_ens50.0/{str(applied_state.value.get("slr_year"))}.tif'
        
        Map_global = leafmap.Map(zoom_start=15)
        # Map_global = load_stac_slr(Map_global, url_slr, 'SLR')
        Map_global = load_stac_sub_list(Map_global, [url_sub])
        Map_global = load_gdf(Map_global, bbox_gd, applied_state.value.get("delta"))
        return url_slr, url_sub, id
    
    def View_mean(url, var, ranges, unit, full):
        def calculate_mean(url):
            item = rio.open_rasterio(url)
            mean_value = item.mean().item()
            max_value = item.max().item()
            min_value = item.min().item()
            return mean_value, max_value, min_value
        
        def calculate_mean_clipped(url, ranges):
            item = rio.open_rasterio(url)
            item = item.where((item >= applied_state.value.get(ranges)[0]) & (item <= applied_state.value.get(ranges)[1]))
            gdf = bbox_gd.loc[bbox_gd["Location"].isin([applied_state.value.get("delta")])]  
            item = item.rio.clip(gdf.geometry, gdf.crs, drop=True)
            item = item.where(item <= 200) #TODO: This is a hardcoded threshold. This will not be needed when having global coverage in subsidence data
            mean_value = item.mean().item()
            max_value = item.max().item()
            min_value = item.min().item()
            return mean_value, max_value, min_value
        
        if full == True:
            mean, max, min = calculate_mean(url)
        else:
            mean, max, min = calculate_mean_clipped(url, ranges)

        solara.Markdown(f"**Max {var}**:\n  {max:.2f} [{unit}]")
        solara.Markdown(f"**Min {var}**:\n   {min:.2f} [{unit}]")
        solara.Markdown(f"**Mean {var}**:\n {mean:.2f} [{unit}]")


    def View_scale(title, ranges, cmap):
        fig, ax = plt.subplots(figsize=(6, 1))
        fig.subplots_adjust(bottom=0.5)

        norm = mpl.colors.Normalize(vmin=applied_state.value.get(ranges)[0], vmax=applied_state.value.get(ranges)[1])

        cb = mpl.colorbar.ColorbarBase(ax, cmap=cmap, norm=norm, orientation='horizontal')
        cb.set_label(title)

        return plt.show()


    with solara.Sidebar():
        Controls()
        solara.Markdown(r'''####  ''')

    with solara.Columns([1, 0.5]):  

        with solara.Column():   

            url_slr, url_sub, id = View_leaf()
            with solara.Columns([1, 1]):  
                with solara.Column():   
                    View_scale('SLR', 'slr_range', cm.viridis)

                with solara.Column():  
                    View_scale('Subsidence', 'sub_range', cm.YlOrRd)

        with solara.Column():    

            solara.Markdown(r'''# Data analysis''')
            solara.Markdown(r'''#### Global statistics''')
            # with solara.Columns([0.6, 0.6]):  
            #     with solara.Column():   
            #         View_mean(url_slr, 'SLR', 'slr_range', "mm", full=True)
            #     with solara.Column():  
            #         View_mean(url_sub, "Sub", "sub_range", "1", full=True)

            # solara.Markdown(r'''#### Hotspot''')
            # with solara.Columns([0.6, 0.6]):  
            #     with solara.Column():   
            #         View_mean(url_slr, 'SLR', 'slr_range', "mm", full=False)

            #     with solara.Column():  
            #         View_mean(url_sub, "Sub", "sub_range", "1", full=False)
