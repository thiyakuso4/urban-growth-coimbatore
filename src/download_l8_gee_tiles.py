import ee
import geemap
import os
import geopandas as gpd
from shapely.geometry import box

# Authenticate and initialize Earth Engine
ee.Authenticate()
ee.Initialize(project="ee-project")

# Define project directory
prj_dir = "/mnt/e/Projects/personal/coimbatore_lulc"

# Load the shapefile and convert it to the required CRS
shp_file = f"{prj_dir}/gpkg/cbe_corporation_boundary.gpkg"
boundary_gdf = gpd.read_file(shp_file)
boundary_gdf_4326 = boundary_gdf.to_crs(4326)

# Get the total bounds of the shapefile
total_bounds = boundary_gdf_4326.total_bounds

# Create an Earth Engine geometry from the bounds
polygon = ee.Geometry.Rectangle(total_bounds.tolist())

# Define the region of interest (ROI)
roi = polygon
# Cloud masking function
def mask_s2_clouds(image):
    qa = image.select('QA60')
    cloud_bit_mask = 1 << 10
    cirrus_bit_mask = 1 << 11
    mask = qa.bitwiseAnd(cloud_bit_mask).eq(0).And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
    return image.updateMask(mask).divide(10000)
# Define tile size (in degrees, this can be adjusted)
tile_size = 0.1  # 0.1 degrees ~ 11 km at the equator

# Create a grid of tiles
minx, miny, maxx, maxy = total_bounds
tiles = []
x = minx
while x < maxx:
    y = miny
    while y < maxy:
        tile = box(x, y, min(x + tile_size, maxx), min(y + tile_size, maxy))
        tiles.append(tile)
        y += tile_size
    x += tile_size

# Define date range
years = [2017, 2018, 2019, 2020, 2021, 2022, 2023]
years = [2015, 2016]

# Applies scaling factors.
def apply_scale_factors(image):
  optical_bands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
  thermal_bands = image.select('ST_B.*').multiply(0.00341802).add(149.0)
  return image.addBands(optical_bands, None, True).addBands(
      thermal_bands, None, True
  )


# Function to mask clouds and cloud shadows using the QA_PIXEL band
def mask_clouds(image):
    # Get the QA_PIXEL band
    qa = image.select('QA_PIXEL')
    
    # Bits 4 and 5 are cloud shadow and cloud respectively
    cloud_shadow_bit = 1 << 4  # Bit 4
    cloud_bit = 1 << 5         # Bit 5
    
    # Bits 3 and 7 are dilated cloud and cirrus clouds respectively
    dilated_cloud_bit = 1 << 3 # Bit 3
    cirrus_cloud_bit = 1 << 7  # Bit 7
    
    # Combine the masks using bitwise operations
    mask = qa.bitwiseAnd(cloud_shadow_bit).eq(0) \
           .bitwiseAnd(qa.bitwiseAnd(cloud_bit).eq(0)) \
           .bitwiseAnd(qa.bitwiseAnd(dilated_cloud_bit).eq(0)) \
           .bitwiseAnd(qa.bitwiseAnd(cirrus_cloud_bit).eq(0))
    
    return image.updateMask(mask)


# Define date range
# years = [2015, 2016, 2017, 2018]
import numpy as np
years = np.arange(2015, 2024)
l8_dir = f"{prj_dir}/tif/l8"
for year in years:
    start_date = f'{year}-01-01'  # Specify start date
    # start_date = '2024-01-01'  # Specify start date
    end_date = f'{year}-03-31'    # Specify end date

    # Load Landsat 8 collection, filter by date and bounds, and map the NDVI function
    collection = (
        ee.ImageCollection('LANDSAT/LC08/C02/T1_L2')
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt('CLOUD_COVER', 15))
        .filterBounds(roi)
        .map(mask_clouds)
        .map(apply_scale_factors)
    )
    # Export each tile separately
    for idx, tile in enumerate(tiles):
        tile_geom = ee.Geometry.Polygon(list(tile.exterior.coords))
        tile_collection = collection.map(lambda img: img.clip(tile_geom))
        output_dir = os.path.join(l8_dir, f'l8_tile_{idx + 1}')
        # Define output filename
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Export the tile collection
        geemap.ee_export_image_collection(
            tile_collection,
            out_dir=output_dir,
            region=tile_geom,
            scale=30,
            file_per_band=False  # Export all bands to a single file per tile
        )
        print(f"Exported tile {idx + 1} to {output_dir}")