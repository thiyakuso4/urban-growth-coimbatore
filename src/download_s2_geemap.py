import ee
import geemap
import os
import geopandas as gpd

ee.Authenticate()
# Initialize Google Earth Engine
ee.Initialize(project="ee-project")

# Define project directory
prj_dir = "/mnt/e/Projects/personal/coimbatore_lulc"

shp_file = f"{prj_dir}/gpkg/cbe_corporation_boundary.gpkg"

boundary_gdf = gpd.read_file(shp_file)
boundary_gdf_4326 = boundary_gdf.to_crs(4326)
# Get the total bounds of the shapefile
total_bounds = boundary_gdf_4326.total_bounds

# Create an Earth Engine geometry from the bounds
polygon = ee.Geometry.Rectangle(total_bounds.tolist())

# Define the region of interest (ROI) - Example coordinates (longitude, latitude)
# latitude, longitude = 53.26882980, -6.91951934
# buffer_distance = 1000
# roi = ee.Geometry.Point([longitude, latitude]).buffer(buffer_distance)  # Adjust with your coordinates and buffer distance
roi = polygon
# Define date range
start_date = '2024-05-01'  # Specify start date
# start_date = '2024-01-01'  # Specify start date
end_date = '2024-05-31'    # Specify end date


def mask_s2_clouds(image):
    """Masks clouds in a Sentinel-2 image using the QA band.

    Args:
        image (ee.Image): A Sentinel-2 image.

    Returns:
        ee.Image: A cloud-masked Sentinel-2 image.
    """
    qa = image.select('QA60')

    # Bits 10 and 11 are clouds and cirrus, respectively.
    cloud_bit_mask = 1 << 10
    cirrus_bit_mask = 1 << 11

    # Both flags should be set to zero, indicating clear conditions.
    mask = (
        qa.bitwiseAnd(cloud_bit_mask)
        .eq(0)
        .And(qa.bitwiseAnd(cirrus_bit_mask).eq(0))
    )

    return image.updateMask(mask).divide(10000)


# Sentinel-2 collection
collection = (
    ee.ImageCollection('COPERNICUS/S2_HARMONIZED')
    .filterBounds(roi)
    .filterDate(start_date, end_date)
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
    .map(mask_s2_clouds)
    # .select(['B2', 'B3', 'B4'])
)


# Function to compute NDVI
def compute_ndvi(image):
    ndvi = image.normalizedDifference(['B8', 'B4']).rename('NDVI')
    return image.addBands(ndvi)

# Map the function over the collection to compute NDVI for each image
# collection_with_ndvi = collection.map(compute_ndvi)


# Define the output directory
output_dir = f"{prj_dir}/tif/s2_all_bands"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
# Export the collection to Google Drive or download locally
geemap.ee_export_image_collection(collection,
                                  out_dir=output_dir,
                                  region=roi,
                                  scale=10)