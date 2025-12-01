"""
Convert shapefiles to Parquet format using GeoPandas.

This script reads all shapefiles from a specified directory and converts them
to Parquet format, saving them in a subdirectory.
"""

import os
import glob
import re
from pathlib import Path
import geopandas as gpd
from tqdm import tqdm


def parse_filename_for_output(stem: str) -> str:
    """
    Parse the shapefile stem to extract probability and year.
    
    Example: 'cc45y30_p50' -> 'p50_2030'
    
    Parameters:
    -----------
    stem : str
        The stem of the shapefile (filename without extension)
    
    Returns:
    --------
    str
        New filename in format '{probability}_{year}.parquet'
    """
    # Extract probability (e.g., 'p50' after underscore)
    probability_match = re.search(r'_([pP]\d+)', stem)
    if probability_match:
        probability = probability_match.group(1)
    else:
        # Fallback: try to find p followed by digits anywhere
        prob_match = re.search(r'([pP]\d+)', stem)
        if prob_match:
            probability = prob_match.group(1)
        else:
            probability = "p50"  # Default fallback
    
    # Extract year (e.g., '30' after 'y' and convert to '2030')
    year_match = re.search(r'y(\d+)', stem)
    if year_match:
        year_suffix = year_match.group(1)
        # Convert to full year (e.g., '30' -> '2030', '18' -> '2018')
        if len(year_suffix) == 2:
            year = f"20{year_suffix}"
        else:
            year = year_suffix
    else:
        # Fallback: try to find 4-digit year
        year_match = re.search(r'(\d{4})', stem)
        if year_match:
            year = year_match.group(1)
        else:
            year = "2030"  # Default fallback
    
    return f"{probability}_{year}.parquet"


def convert_shapefiles_to_parquet(
    input_dir: str,
    output_dir: str = None,
    create_output_dir: bool = True
):
    """
    Convert all shapefiles in a directory to Parquet format.
    
    Parameters:
    -----------
    input_dir : str
        Path to the directory containing shapefiles
    output_dir : str, optional
        Path to the output directory for parquet files.
        If None, uses input_dir/parquet
    create_output_dir : bool, default True
        Whether to create the output directory if it doesn't exist
    
    Returns:
    --------
    list
        List of successfully converted files
    """
    input_path = Path(input_dir)
    
    # Set output directory
    if output_dir is None:
        output_path = input_path / "parquet"
    else:
        output_path = Path(output_dir)
    
    # Create output directory if it doesn't exist
    if create_output_dir:
        output_path.mkdir(parents=True, exist_ok=True)
        print(f"Output directory: {output_path}")
    
    # Find all shapefiles (files with .shp extension)
    shapefiles = list(input_path.glob("*.shp"))
    
    if not shapefiles:
        print(f"No shapefiles found in {input_dir}")
        return []
    
    print(f"Found {len(shapefiles)} shapefile(s) to convert")
    
    successful_conversions = []
    failed_conversions = []
    
    # Cache for already-created subdirectories
    created_subdirs = set()

    # Process each shapefile
    for shp_file in tqdm(shapefiles, desc="Converting shapefiles"):
        try:
            # Read shapefile
            gdf = gpd.read_file(shp_file)

            # Determine subfolder name from shapefile stem:
            # Default rule: take the part of the name up to and including the first 'y', e.g.
            #   'cc45sm2rb1y_2030' -> 'cc45sm2rb1y'
            # Exception: baseline file 'cc45y18_p50' goes into folder 'baseline'
            stem = shp_file.stem
            if stem == "cc45y18_p50":
                subfolder_name = "baseline"
            elif "y" in stem:
                y_index = stem.find("y")
                subfolder_name = stem[:y_index+1]  # Include everything up to and including 'y'
            else:
                subfolder_name = stem

            # Create subdirectory for this group if needed
            group_dir = output_path / subfolder_name
            if subfolder_name not in created_subdirs:
                group_dir.mkdir(parents=True, exist_ok=True)
                created_subdirs.add(subfolder_name)

            # Create output filename in format: {probability}_{year}.parquet
            output_filename = parse_filename_for_output(stem)
            output_file = group_dir / output_filename
            
            # Write to parquet
            gdf.to_parquet(output_file, index=False)
            
            successful_conversions.append(shp_file.name)
            print(f"✅ Converted: {shp_file.name} -> {subfolder_name}/{output_filename}")
            
        except Exception as e:
            failed_conversions.append((shp_file.name, str(e)))
            print(f"❌ Failed to convert {shp_file.name}: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("Conversion Summary:")
    print(f"  Successful: {len(successful_conversions)}")
    print(f"  Failed: {len(failed_conversions)}")
    
    if successful_conversions:
        print("\nSuccessfully converted files:")
        for filename in successful_conversions:
            print(f"  - {filename}")
    
    if failed_conversions:
        print("\nFailed conversions:")
        for filename, error in failed_conversions:
            print(f"  - {filename}: {error}")
    
    return successful_conversions


if __name__ == "__main__":
    # Configuration
    INPUT_DIR = r"N:\Deltabox\Postbox\Athanasiou, Panos\Salinity_Mekong\shp_p50"
    OUTPUT_DIR = r"N:\Deltabox\Postbox\Athanasiou, Panos\Salinity_Mekong\shp_p50\parquet"
    
    # Check if input directory exists
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Input directory does not exist: {INPUT_DIR}")
        exit(1)
    
    print(f"Input directory: {INPUT_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("="*60)
    
    # Convert shapefiles to parquet
    convert_shapefiles_to_parquet(
        input_dir=INPUT_DIR,
        output_dir=OUTPUT_DIR,
        create_output_dir=True
    )

