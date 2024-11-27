library(terra)
setwd('E:/Projects/personal/coimbatore_lulc')
tif_basenames <- basename(Sys.glob('tif/s2_all_bands/s2_tile_9/*.tif'))
for(tif_basename in tif_basenames){
  out_file <- sprintf('tif/s2_all_bands/%s', tif_basename)
  if(!file.exists(out_file)){
    in_files <- Sys.glob(sprintf('tif/s2_all_bands/*/%s', tif_basename))
    
    m_ras <- rast(in_files[1], lyrs = 1:13)
    
    for(in_file in in_files[-1]){
      ras <- rast(in_file, lyrs=1:13)
      m_ras <- merge(ras, m_ras)
      print(in_file)
      # break
    }    writeRaster(m_ras, out_file)
    # ras <- merge(in_files)
    
  }
  
}
