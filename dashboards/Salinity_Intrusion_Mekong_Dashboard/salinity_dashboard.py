import solara
import leafmap
import os

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
    rcp_code = "45" if climate_rcp.value == "RCP 4.5" else "85"
    
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
    
    file_path = os.path.join(BASE_PATH, scenario_folder, f"{year.value}.tif")
    
    # Check if file exists, if not return None
    if os.path.exists(file_path):
        return file_path
    return None

@solara.component
def Page():
    
    # Function to get dynamic description based on current selections
    def get_climate_description():
        if climate_rcp.value == "RCP 4.5":
            return "**Moderate scenario (1.5–2°C global temperature rise)**: Projects sea level rise and upstream discharge anomalies based on downscaled precipitation and temperature data."
        else:
            return "**Extreme scenario (3–4°C global temperature rise)**: Projects sea level rise and upstream discharge anomalies under higher warming conditions."
    
    def get_anthropogenic_description():
        descriptions = []
        
        if subsidence_enabled.value:
            if climate_rcp.value == "RCP 4.5":
                descriptions.append("**M2 Groundwater Scenario**: 5% annual reduction in groundwater extraction leading to stable 50% of 2018 extraction volume, reflecting rising awareness of consequences. Results in reduced land subsidence due to aquifer-system compaction.")
            else:
                descriptions.append("**B2 Groundwater Scenario**: Business-as-usual with 4% annual increase in extraction (similar to highest rates in last 25 years), leading to continued land subsidence due to aquifer-system compaction.")
        
        if riverbed_enabled.value:
            if climate_rcp.value == "RCP 4.5":
                descriptions.append("\n\n**RB1 Riverbed Scenario**: Significantly lower erosion rate (one-third of past 20 years) until 2040, motivated by rising awareness, shortage of erodible material, and potential policy changes. Accounts for 1 G m³ sand demand until 2040.")
            else:
                descriptions.append("\n\n**RB3 Riverbed Scenario**: Business-as-usual with identical erosion rates as past 20 years. The estuarine system continues deepening 2-3m (losing ~2-3 G m³) due to sediment starvation from upstream trapping and downstream sand mining.")
        
        if not descriptions:
            return "No anthropogenic changes selected. Climate-only scenario considers sea level rise and discharge variations without human-induced modifications."
        
        return " ".join(descriptions)
    
    with solara.Column():
        solara.Markdown("# Salinity Intrusion Dashboard for Mekong Delta")
        
        # Main layout: Controls on left, Map on right
        with solara.Row():
            # Left column for controls - 1/2 of screen
            with solara.Column(style={"width": "50%", "padding": "20px"}):
                
                # Climate Change Section
                solara.Markdown("## Climate Change")
                solara.Select(
                    label="RCP Scenario",
                    value=climate_rcp.value,
                    on_value=climate_rcp.set,
                    values=["RCP 4.5", "RCP 8.5"]
                )
                
                # Year selection
                solara.Select(
                    label="Year",
                    value=year.value,
                    on_value=year.set,
                    values=["2030", "2040", "2050"]
                )
                
                # Dynamic climate description - directly under title
                with solara.Card("Climate Change Description", margin=0, elevation=2):
                    solara.Markdown(get_climate_description())
                
                # Anthropogenic Changes Section
                solara.Markdown("## Anthropogenic Changes")
                
                # Subsidence switch with integrated name
                subsidence_name = "M2 scenario" if climate_rcp.value == "RCP 4.5" else "B2 scenario"
                solara.Switch(
                    label=f"Groundwater Extraction (Subsidence) - {subsidence_name}",
                    value=subsidence_enabled.value,
                    on_value=subsidence_enabled.set
                )
                
                # Riverbed switch with integrated name - only available if subsidence is enabled
                riverbed_name = "RB1 scenario" if climate_rcp.value == "RCP 4.5" else "RB3 scenario"
                
                if subsidence_enabled.value:
                    solara.Switch(
                        label=f"Sand Mining (Riverbed Level Incision) - {riverbed_name}",
                        value=riverbed_enabled.value,
                        on_value=riverbed_enabled.set
                    )
                else:
                    # Show disabled switch when subsidence is not enabled
                    solara.Switch(
                        label=f"Sand Mining (Riverbed Level Incision) - {riverbed_name} (requires groundwater extraction)",
                        value=False,
                        on_value=lambda x: None,  # Do nothing when clicked
                        disabled=True
                    )
                    # Reset riverbed if subsidence gets disabled
                    if riverbed_enabled.value:
                        riverbed_enabled.set(False)
                
                # Dynamic anthropogenic description - directly under switches
                with solara.Card("Anthropogenic Changes Description", margin=0, elevation=2):
                    solara.Markdown(get_anthropogenic_description())
                
                # Display current scenario info
                current_file = get_scenario_file_path()
                if current_file:
                    scenario_name = os.path.basename(os.path.dirname(current_file))
                    year_val = os.path.splitext(os.path.basename(current_file))[0]
                    solara.Markdown("### Current Scenario")
                    solara.Info(f"Scenario: {scenario_name}")
                    solara.Info(f"Year: {year_val}")
                    if not os.path.exists(current_file):
                        solara.Warning(f"File not found: {current_file}")
                else:
                    solara.Warning("No valid scenario selected")
            
            # Right column for map - 1/2 of screen
            with solara.Column(style={"flex": "1"}):
                # Simple leafmap without complex features
                leafmap.Map.element(
                    zoom=zoom.value,
                    on_zoom=zoom.set,
                    center=center.value,
                    on_center=center.set,
                    height="600px",
                    width="100%"
                )