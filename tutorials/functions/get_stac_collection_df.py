from copy import deepcopy
from typing import List, Dict
import pandas as pd

def items_to_dataframe(items: List[Dict]) -> pd.DataFrame:
    """STAC items to Pandas dataframe.
    Args:
        items (List[Dict]): _description_
    Returns:
        pd.DataFrame: _description_
    """
    _items = []
    for i in items:
        _i = deepcopy(i)
        _items.append(_i)
    df = pd.DataFrame(pd.json_normalize(_items))
    return df

def get_all_items(collection, batch_size=100):
    """
    Get all items from a collection with progress tracking.
    This works even when the collection doesn't support search API.
    """
    print(f"Loading items from collection: {collection.id}")
    
    try:
        # Get the item iterator
        items_iter = collection.get_items()
        
        all_items = []
        batch = []
        
        for i, item in enumerate(items_iter, 1):
            batch.append(item)
            
            # Process in batches to show progress and manage memory
            if len(batch) >= batch_size:
                all_items.extend(batch)
                print(f"Loaded {len(all_items)} items...")
                batch = []
        
        # Add remaining items
        if batch:
            all_items.extend(batch)
            
        print(f"Finished loading {len(all_items)} total items")
        return all_items
        
    except Exception as e:
        print(f"Error loading items: {e}")
        return []
    
def get_collection_df(collection):
    name = "name"#collection
    print("Available assets in collection:")
    for asset_name, asset in collection.get_assets().items():
        print(f"  - {asset_name}: {asset.href}")

    # Try to find a parquet asset first, fallback to item loading
    if "geoparquet-stac-items" in collection.get_assets():
        print(f"Using fast parquet method for {name}...")
        items_df = pd.read_parquet(collection.get_assets()["geoparquet-stac-items"].href)
        print(f"Loaded {len(items_df)} items from parquet")
    else:
        print("\nNo parquet asset found, using get_items() with progress tracking...")
        items = get_all_items_with_progress(collection, batch_size=50)
        items_df = items_to_dataframe([i.to_dict() for i in items])
        print(f"Converted to DataFrame with {len(items_df)} rows")

    print("DataFrame info:")
    print(f"Shape: {items_df.shape}")

    return items_df