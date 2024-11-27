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
tile_size = 0.05  # 0.05 degrees ~ 5.5km at the equator

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
years = [2022]
# Define the output directory
s2_dir = f"{prj_dir}/tif/s2_all_bands"

for year in years:
    start_date = f'{year}-02-01'  # Specify start date
    # start_date = '2024-01-01'  # Specify start date
    end_date = f'{year}-05-01'    # Specify end date

    # Sentinel-2 collection
    collection = (
        ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
        .filterBounds(roi)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 1))
        .map(mask_s2_clouds)
    )
    # Export each tile separately
    for idx, tile in enumerate(tiles):
        tile_geom = ee.Geometry.Polygon(list(tile.exterior.coords))
        tile_collection = collection.map(lambda img: img.clip(tile_geom))
        output_dir = os.path.join(s2_dir, f's2_tile_{idx + 1}')
        # Define output filename
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Export the tile collection
        geemap.ee_export_image_collection(
            tile_collection,
            out_dir=output_dir,
            region=tile_geom,
            scale=10,
            file_per_band=False  # Export all bands to a single file per tile
        )
        print(f"Exported tile {idx + 1} to {output_dir}")
