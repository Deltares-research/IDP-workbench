# %%
import tempfile
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pystac_client
import rasterio
import rioxarray
import xarray
from azure.storage.blob import BlobServiceClient
from geopandas import GeoDataFrame
from pystac import Collection, Item, read_file
from rioxarray.merge import merge_arrays
from shapely.geometry import LineString
from xarray import DataArray

# %%

points = [
    [-8.479004110660412, 41.27742545279088],
    [-8.532264015728288, 42.28418912902353],
]

# bangladesh
# points = [
#     [91.89909204070477, 22.530918271554796],
#     [92.13984651040869, 21.21524392195687],
# ]

line = LineString(points)

# %%

stac_catalog_location = (
    Path(__file__).parent / "data" / "coclicodata" / "current" / "catalog.json"
)
delta_dtm_collection_id = "deltares-delta-dtm"
delta_dtm_collection_location = (
    stac_catalog_location.parent / delta_dtm_collection_id / "collection.json"
)
stac_catalog = pystac_client.Client.open(stac_catalog_location)
delta_dtm_collection: Collection = read_file(delta_dtm_collection_location)
all_delta_dtm_items = [item for item in delta_dtm_collection.get_all_items()]


# %%


def from_items(item_collection: list[Item]) -> GeoDataFrame:
    gdf = GeoDataFrame.from_features(item_collection).set_crs(epsg=9518)
    gdf["datetime"] = pd.to_datetime(gdf.datetime)
    gdf["id"] = [x.id for x in item_collection]
    return gdf


gdf: GeoDataFrame = from_items(all_delta_dtm_items)


def filter_geometry(gdf: GeoDataFrame, geometry: LineString):
    return gdf[gdf.intersects(geometry)]


# %%


filtered_gdf = filter_geometry(gdf, line)
print(filtered_gdf.id.values)
# %%
items = [delta_dtm_collection.get_item(id) for id in filtered_gdf.id.values]
assets = [item.get_assets(role="data")["data"].href for item in items]

# %%

# download assets
account_name = delta_dtm_collection.to_dict()["item_assets"]["data"][
    "xarray:storage_options"
]["account_name"]
account_url = f"https://{account_name}.blob.core.windows.net"
blob_service_client = BlobServiceClient(account_url)

# %%

temp_files = []
datasets = []
for asset in assets:
    container, *blob = asset.removeprefix("az://").split("/")
    blob = "/".join(blob)
    blob_client = blob_service_client.get_blob_client(container=container, blob=blob)

    # Create a temporary file
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".tiff")
    blob_client.download_blob().readinto(temp_file)
    temp_file.close()

    temp_files.append(temp_file.name)
    datasets.append(rioxarray.open_rasterio(rasterio.open(temp_file.name)))
# %%


merged = merge_arrays(datasets)
masked_merged = merged.where(merged != -9999.0)  # mask non valid values


# %%
def extract_along_line(xarr: DataArray, line: LineString, n_samples=256):
    tgt_x = xarray.DataArray(
        np.linspace(line.coords[0][0], line.coords[1][0], num=n_samples),
        dims="points",
    )
    tgt_y = xarray.DataArray(
        np.linspace(line.coords[0][1], line.coords[1][1], num=n_samples),
        dims="points",
    )

    values: np.ndarray = xarr.sel(x=tgt_x, y=tgt_y, method="nearest").data
    return values


# %%


# use the method from above to extract the profile
profile = extract_along_line(masked_merged.squeeze(), line)
plt.plot(profile)
plt.show()

# %%
