import ee
import geemap
import os
import geopandas as gpd
import fiona

ee.Authenticate()
# Initialize Google Earth Engine
ee.Initialize(project="ee-project")

# Define project directory
prj_dir = "/home/thiyaku/Projects/personal/"

shp_file = f"{prj_dir}/kml/AOI.kml"

fiona.drvsupport.supported_drivers['KML'] = 'rw' # enable KML support which is disabled by default
boundary_gdf = gpd.read_file(shp_file, driver='KML')
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


# Function to compute NDVI
def compute_ndvi(image):
    ndvi = image.normalizedDifference(['SR_B5', 'SR_B4']).rename('NDVI')
    return image.addBands(ndvi)

# Applies scaling factors.
def apply_scale_factors(image):
  optical_bands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
  thermal_bands = image.select('ST_B.*').multiply(0.00341802).add(149.0)
  return image.addBands(optical_bands, None, True).addBands(
      thermal_bands, None, True
  )


def mask_clouds(image):
    # Select the QA_PIXEL band
    qa = image.select('QA_PIXEL')
    
    # Bits 3 and 5 are cloud shadow and cloud, respectively
    cloud_shadow_bit = 1 << 3  # Bit 3 is for cloud shadow
    cloud_bit = 1 << 5         # Bit 5 is for cloud

    # Create a mask where cloud shadow and cloud bits are set to 0 (indicating clear conditions)
    mask = qa.bitwiseAnd(cloud_shadow_bit).eq(0).And(qa.bitwiseAnd(cloud_bit).eq(0))
    
    # Apply the mask to the image
    return image.updateMask(mask)


# Define date range
years = [2010, 2015]

for year in years:
    start_date = f'{year}-05-01'  # Specify start date
    # start_date = '2024-01-01'  # Specify start date
    end_date = f'{year}-10-30'    # Specify end date

    # Load Landsat 8 collection, filter by date and bounds, and map the NDVI function
    collection = (
        ee.ImageCollection('LANDSAT/LE07/C02/T1_L2')
        .filterDate(start_date, end_date)
        .filterBounds(roi)
        .map(mask_clouds)
        .map(apply_scale_factors)
    )

    # Map the function over the collection to compute NDVI for each image
    # collection_with_ndvi = collection.map(compute_ndvi)


    # Define the output directory
    output_dir = f"{prj_dir}/tif/l7"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # Export the collection to Google Drive or download locally
    geemap.ee_export_image_collection(collection,
                                    out_dir=output_dir,
                                    region=roi,
                                    scale=10)
