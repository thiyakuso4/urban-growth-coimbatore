from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt
from datetime import date

# Connect to the Copernicus Open Access Hub
api = SentinelAPI('email', 'password', 'https://scihub.copernicus.eu/dhus')

# Define project directory
prj_dir = "E:/Projects/personal/coimbatore_lulc"

gpkg_file = f"{prj_dir}/gpkg/cbe_corporation_boundary.gpkg"
geojson_file = f"{prj_dir}/geojson/Cbe2011Wards.geojson"
# Define your AOI (can be a GeoJSON or manually defined polygon)
footprint = geojson_to_wkt(read_geojson(geojson_file))
print(footprint)
# Search for Sentinel-2 products
products = api.query(footprint,
                     date=('20220101', '20220131'),
                     platformname='Sentinel-2',
                     cloudcoverpercentage=(0, 10))

# Download the products
api.download_all(products)
