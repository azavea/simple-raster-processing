import numpy as np
import rasterio

NODATA = -2147483648

with rasterio.open('/usr/data/pa_512.tif') as src:
    kwargs = src.meta
    kwargs.update(
        driver='GTiff',
        dtype=rasterio.int32,
        count=1,
        #compress='lzw',
        nodata=NODATA,
        bigtiff='YES' # Output will be larger than 4GB
    )

    windows = src.block_windows(1)

    with rasterio.open(
            '/usr/data/pa_cm.tif',
            'w',
            **kwargs) as dst:
        for idx, window in windows:
            src_data = src.read(1, window=window)

            # Source nodata value is a very small negative number
            # Converting in to min int for the output raster
            np.putmask(src_data, src_data < -100000 , NODATA)

            # Convert to cm and save
            dst_data = (src_data * 100).astype(rasterio.int32)
            dst.write_band(1, dst_data, window=window)
