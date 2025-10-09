import solara
import leafmap
import os

# Configuration variables for input options
RCP_OPTIONS = ["RCP 4.5", "RCP 8.5"]
YEAR_OPTIONS = ["2030", "2040", "2050"]

# Scenario names and descriptions
CLIMATE_SCENARIOS = {
    "RCP 4.5": {
        "name": "Moderate scenario",
        "description": "**Moderate scenario (1.5–2°C global temperature rise)**: Projects sea level rise and upstream discharge anomalies based on downscaled precipitation and temperature data."
    },
    "RCP 8.5": {
        "name": "Extreme scenario", 
        "description": "**Extreme scenario (3–4°C global temperature rise)**: Projects sea level rise and upstream discharge anomalies under higher warming conditions."
    }
}

GROUNDWATER_SCENARIOS = {
    "RCP 4.5": {
        "code": "M2",
        "name": "M2 scenario",
        "description": "**M2 Groundwater Scenario**: 5% annual reduction in groundwater extraction leading to stable 50% of 2018 extraction volume, reflecting rising awareness of consequences. Results in reduced land subsidence due to aquifer-system compaction."
    },
    "RCP 8.5": {
        "code": "B2", 
        "name": "B2 scenario",
        "description": "**B2 Groundwater Scenario**: Business-as-usual with 4% annual increase in extraction (similar to highest rates in last 25 years), leading to continued land subsidence due to aquifer-system compaction."
    }
}

RIVERBED_SCENARIOS = {
    "RCP 4.5": {
        "code": "RB1",
        "name": "RB1 scenario",
        "description": "**RB1 Riverbed Scenario**: Significantly lower erosion rate (one-third of past 20 years) until 2040, motivated by rising awareness, shortage of erodible material, and potential policy changes. Accounts for 1 G m³ sand demand until 2040."
    },
    "RCP 8.5": {
        "code": "RB3",
        "name": "RB3 scenario", 
        "description": "**RB3 Riverbed Scenario**: Business-as-usual with identical erosion rates as past 20 years. The estuarine system continues deepening 2-3m (losing ~2-3 G m³) due to sediment starvation from upstream trapping and downstream sand mining."
    }
}

# UI Labels
SWITCH_LABELS = {
    "groundwater": "Groundwater Extraction (Subsidence)",
    "riverbed": "Sand Mining (Riverbed Level Incision)",
    "riverbed_disabled": "Sand Mining (Riverbed Level Incision) - {} (requires groundwater extraction)"
}

DEFAULT_TEXT = {
    "no_anthropogenic": "No anthropogenic changes selected. Climate-only scenario considers sea level rise and discharge variations without human-induced modifications."
}

zoom = solara.reactive(8)
center = solara.reactive((10.8, 106.7))  # Mekong Delta coordinates

# Reactive variables for scenario selection
climate_rcp = solara.reactive("RCP 4.5")
year = solara.reactive("2030")
subsidence_enabled = solara.reactive(False)
riverbed_enabled = solara.reactive(False)

# Base path for scenario data
BASE_PATH = r"C:\Users\athanasi\Project_files\1_Projects_SITO\IDP\Data\salinity_mekong\scenarios"

def get_scenario_file_path():
    """Generate the file path based on current scenario selections."""
    rcp_code = "45" if climate_rcp.value == RCP_OPTIONS[0] else "85"
    
    # Determine scenario folder based on enabled options
    if subsidence_enabled.value and riverbed_enabled.value:
        # Both subsidence and riverbed - only cc45sm2rb1y is available
        if rcp_code == "45":
            scenario_folder = "cc45sm2rb1y"
        else:
            # RCP 8.5 combination not available, fallback to subsidence only
            scenario_folder = "cc85sb2y"
    elif subsidence_enabled.value:
        # Only subsidence
        if rcp_code == "45":
            scenario_folder = "cc45sm2y"  # M2 scenario
        else:
            scenario_folder = "cc85sb2y"  # B2 scenario
    else:
        # Only climate change (no anthropogenic changes)
        scenario_folder = f"cc{rcp_code}y"
    
    # Use online file URL format for now
    file_url = f"https://storage.cloud.google.com/dgds-data-public/gca/salinity/{scenario_folder}/{year.value}.tif"
    return file_url

class Map(leafmap.Map):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Add what you want below
        self.add_basemap("Esri.WorldImagery")
        self.scenario_layer = None
    
    def update_scenario_layer(self, file_url):
        """Update the scenario layer with a new COG file."""
        # Remove existing scenario layer if it exists
        if self.scenario_layer is not None:
            try:
                # Remove layer by name
                layers_to_remove = [layer for layer in self.layers if hasattr(layer, 'name') and layer.name == "Salinity Scenario"]
                for layer in layers_to_remove:
                    self.remove_layer(layer)
            except Exception as e:
                print(f"Error removing layer: {e}")
        
        # Add new layer if file URL is provided
        if file_url:
            try:
                # Try to add COG layer using the online URL
                self.add_cog_layer(
                    url=file_url,
                    name="Salinity Scenario",
                    opacity=0.7,
                    zoom_to_layer=False
                )
                self.scenario_layer = "Salinity Scenario"
                print(f"Successfully loaded COG: {file_url}")
            except Exception as e:
                print(f"Error loading COG: {e}")
                self.scenario_layer = None
        else:
            self.scenario_layer = None

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
    
    # Create a persistent map instance
    map_instance = solara.use_memo(lambda: Map(
        zoom=zoom.value,
        center=center.value,
        scroll_wheel_zoom=True,
        toolbar_ctrl=False,
        data_ctrl=False,
    ), [])
    
    # Effect to update COG layer when scenario changes
    def update_cog_layer():
        file_url = get_scenario_file_path()
        if map_instance and hasattr(map_instance, 'update_scenario_layer'):
            map_instance.update_scenario_layer(file_url)
    
    solara.use_effect(update_cog_layer, [climate_rcp.value, year.value, subsidence_enabled.value, riverbed_enabled.value])
    
    with solara.Column():
        solara.Markdown("# Salinity Intrusion Dashboard for Mekong Delta")
        
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
                # Use the persistent map instance
                Map.element(
                    zoom=zoom.value,
                    on_zoom=zoom.set,
                    center=center.value,
                    on_center=center.set,
                    height="600px",
                    width="100%"
                )