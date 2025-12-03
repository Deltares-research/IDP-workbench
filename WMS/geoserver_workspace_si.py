# Import the library
from geo.Geoserver import Geoserver
import requests
import urllib3
import time

# Disable SSL verification warnings (for self-signed certificates)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Monkey-patch requests to disable SSL verification by default
original_request = requests.Session.request
def patched_request(self, method, url, **kwargs):
    kwargs.setdefault('verify', False)
    return original_request(self, method, url, **kwargs)
requests.Session.request = patched_request

# Connect to GeoServer
geo = Geoserver(
    "https://international-delta-platform.avi.directory.intra/geoserver",
    username="admin",
    password="1'46L!:7#y^n9u3sAJw}LQ&$MIqI4w",
)

# --- Configuration ---
WORKSPACE = "salinity_increase"
VARIABLES = ["salinity_increase"]
SCENARIOS = ["baseline", "cc45y", "cc85y", "cc85sb2y", "cc45sm2y", "cc45sm2rb1y", "cc85sb2rb3y"]
YEARS = ["2018", "2030", "2040", "2050"]
LAYER_STYLE = "salinity_increase"
PROBABILITY = "p50"

# --- Helper function to set style ---
def set_default_style(base_url, workspace, layer_name, style_name, user, pwd):
    """
    Update the default style of a published layer via GeoServer REST API.
    """
    rest_url = f"{base_url}/rest/layers/{workspace}:{layer_name}.json"
    headers = {"Content-Type": "application/json"}
    data = {
        "layer": {
            "defaultStyle": {"name": style_name},
        }
    }
    response = requests.put(
        rest_url,
        auth=(user, pwd),
        json=data,
        verify=False,
        headers=headers,
    )
    if response.status_code in [200, 201]:
        print(f"      🎨 Default style set to '{style_name}' for {layer_name}")
    else:
        print(f"      ⚠️ Could not set style for {layer_name}: {response.status_code} {response.text}")


# --- Create workspace if it doesn't exist (will fail silently if it already exists) ---
try:
    geo.create_workspace(workspace=WORKSPACE)
    print(f"Workspace '{WORKSPACE}' created successfully")
except Exception as e:
    if "already exists" in str(e).lower() or "409" in str(e):
        print(f"Workspace '{WORKSPACE}' already exists, skipping creation")
    else:
        print(f"Error creating workspace: {e}")
        raise e

# --- Loop through all combinations ---
for var in VARIABLES:
    print(f"\nProcessing variable: {var}")
    for scen in SCENARIOS:
        print(f"  Scenario: {scen}")
        for year in YEARS:
            print(f"    Year: {year}")

            layer_name = f"{scen}_{PROBABILITY}_{year}"
            tif_path = f"/opt/gca-data-public/gca/{var}/{scen}/{PROBABILITY}_{year}.tif"

            try:
                # Optional: delete existing layer/store if needed
                try:
                    geo.delete_layer(workspace=WORKSPACE, layer_name=layer_name)
                    geo.delete_coveragestore(workspace=WORKSPACE, store_name=layer_name)
                    print(f"      ℹ️ Old layer/store removed: {layer_name}")
                except Exception:
                    pass

                # --- Create coverage store (publishes the layer automatically) ---
                geo.create_coveragestore(
                    layer_name=layer_name,
                    path=tif_path,
                    workspace=WORKSPACE,
                    method="external"
                )
                print(f"      ✅ Coverage store + layer created: {WORKSPACE}:{layer_name}")

                # --- Apply style using REST API ---
                set_default_style(
                    base_url="https://international-delta-platform.avi.directory.intra/geoserver",
                    workspace=WORKSPACE,
                    layer_name=layer_name,
                    style_name=LAYER_STYLE,
                    user="admin",
                    pwd="1'46L!:7#y^n9u3sAJw}LQ&$MIqI4w"
                )

                time.sleep(1)

            except Exception as e:
                print(f"      ❌ Error for {layer_name}: {e}")