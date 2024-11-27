import os
import rasterio
from rasterio.merge import merge
import glob

# Set the working directory
os.chdir('E:/Projects/personal/coimbatore_lulc')

# Get the list of all TIFF basenames in the specific tile folder
tif_basenames = [os.path.basename(tif) for tif in glob.glob('tif/l8/l8_tile_1/*.tif')]

for tif_basename in tif_basenames:
    out_file = f'tif/s2_all_bands/{tif_basename}'
    
    # Check if the output file already exists
    if not os.path.exists(out_file):
        # Get the list of all matching files across different folders
        in_files = glob.glob(f'tif/l8/*/{tif_basename}')
        
        src_files_to_mosaic = []
        
        # Open each raster file and append to the list
        for in_file in in_files:
            src = rasterio.open(in_file)
            src_files_to_mosaic.append(src)
        
        # Merge the rasters
        mosaic, out_trans = merge(src_files_to_mosaic, method='first')

        # Copy the metadata of the first file
        out_meta = src_files_to_mosaic[0].meta.copy()

        # Update the metadata to reflect the dimensions of the mosaic
        out_meta.update({
            "driver": "GTiff",
            "height": mosaic.shape[1],
            "width": mosaic.shape[2],
            "transform": out_trans,
            "count": mosaic.shape[0]  # Update to the correct number of layers
        })

        # Write the merged raster to a new file
        with rasterio.open(out_file, 'w', **out_meta) as dest:
            dest.write(mosaic)
        
        # Close all the raster files
        for src in src_files_to_mosaic:
            src.close()
        
        print(f"Exported and merged {tif_basename} into {out_file}")
