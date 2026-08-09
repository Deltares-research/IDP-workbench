This is a dashboard for visualizing salinity intrusion data in the Mekong region.
It provides interactive maps and charts to help users understand the extent and
impact of salinity intrusion on local communities and ecosystems.

## Setup (conda / venv)

From the IDP-workbench repo root:

  conda create -n solara_mekong python=3.10 -y
  conda activate solara_mekong
  pip install -r dashboards/requirements.txt
  pip install -e dashboards/Salinity_Intrusion_Mekong_Dashboard

  # Register the env as a Jupyter kernel (needed in VS Code / Cursor)
  python -m ipykernel install --user --name solara_mekong --display-name "Python (solara_mekong)"

## Run the Solara app

  cd dashboards/Salinity_Intrusion_Mekong_Dashboard/solara_mekong
  solara run app.py

Then open http://localhost:8765

Alternatively from the dashboard package root:

  cd dashboards/Salinity_Intrusion_Mekong_Dashboard
  solara run solara_mekong.app --host=0.0.0.0 --port=8765

## Notebooks (run in VS Code / Cursor)

Open either notebook in VS Code (or Cursor):

  solara_mekong/notebooks/view_salinity_intrution.ipynb
  solara_mekong/notebooks/view_crop_productivity.ipynb

Then:
  1. Select kernel: Python (solara_mekong)
  2. Connect Deltares VPN (remote GeoServer / WMS)
  3. Run cells top to bottom (Run All)

Notes:
  - Hazard WMS uses remote Deltares GeoServer via STAC visual assets.
  - For the crop notebook, local parquet under
    ...\IDP\Data\stac_folder\crop_productivity_correction\ is preferred;
    otherwise a public GCS fallback is used.
