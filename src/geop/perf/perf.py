import os
import sys
from shapely.geometry import Polygon

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import geo_utils as gp  # noqa

# 21,306 sq km
large_geom = Polygon([[1526562.40124153485521674,2050242.57054176111705601], [1666966.8961625280790031,2054540.66732505685649812],[1662668.79937923233956099, 1899809.18312641140073538],[1523697.00338600436225533,1899809.18312641140073538],[1526562.40124153485521674,2050242.57054176111705601]])  # noqa

# 921 sq km
med_geom = Polygon([[1615747.90949492086656392,1990427.39030756242573261],[1644939.15014813770540059,1990427.39030756242573261],[1644222.80068425508216023, 1958191.66443284461274743],[1615747.90949492086656392,1958728.92653075652197003],[1615747.90949492086656392,1990427.39030756242573261]]) # noqa

# 0.45 sq km
sm_geom = Polygon([[1638682.28529953747056425,1974555.77249841345474124],[1638699.07474009715951979,1973945.75615807599388063],[1639426.61716435290873051, 1973951.35263826255686581],[1639415.42420397978276014,1974555.77249841345474124],[1638682.28529953747056425,1974555.77249841345474124]])  # noqa

"""
Large geom sizes
"""


# Full NLCD: tif | none | 1024x1024
def read_lrg_1024_none():
    gp.mask_geom_on_raster(large_geom, '/usr/data/nlcd/nlcd_1024.tif')


# Full NLCD: tif | none | 512x512
def read_lrg_512_none():
    gp.mask_geom_on_raster(large_geom, '/usr/data/nlcd/nlcd_512.tif')


# Full NLCD: tif | none | 256x256
def read_lrg_256_none():
    gp.mask_geom_on_raster(large_geom, '/usr/data/nlcd/nlcd.tif')


# Full NLCD: tif | lzw | 512x512
def read_lrg_512_lzw():
    gp.mask_geom_on_raster(large_geom, '/usr/data/nlcd/nlcd_512_lzw.tif')


# Full NLCD: tif | lzw | 256x256
def read_lrg_256_lzw():
    gp.mask_geom_on_raster(large_geom, '/usr/data/nlcd/nlcd_cp.tif')


# Full NLCD: tif | packbits | 256x256
def read_lrg_256_pb():
    gp.mask_geom_on_raster(large_geom, '/usr/data/nlcd/nlcd_cp_pb.tif')


"""
Medium geom sizes
"""


# Full NLCD: tif | none | 1024x1024
def read_med_1024_none():
    gp.mask_geom_on_raster(med_geom, '/usr/data/nlcd/nlcd_1024.tif')


# Full NLCD: tif | none | 512x512
def read_med_512_none():
    gp.mask_geom_on_raster(med_geom, '/usr/data/nlcd/nlcd_512.tif')


# Full NLCD: tif | none | 256x256
def read_med_256_none():
    gp.mask_geom_on_raster(med_geom, '/usr/data/nlcd/nlcd.tif')


# Full NLCD: tif | lzw | 512x512
def read_med_512_lzw():
    gp.mask_geom_on_raster(med_geom, '/usr/data/nlcd/nlcd_512_lzw.tif')


# Full NLCD: tif | lzw | 256x256
def read_med_256_lzw():
    gp.mask_geom_on_raster(med_geom, '/usr/data/nlcd/nlcd_cp.tif')


# Full NLCD: tif | packbits | 256x256
def read_med_256_pb():
    gp.mask_geom_on_raster(med_geom, '/usr/data/nlcd/nlcd_cp_pb.tif')


"""
Small geom sizes
"""


# Full NLCD: tif | none | 1024x1024
def read_sm_1024_none():
    gp.mask_geom_on_raster(sm_geom, '/usr/data/nlcd/nlcd_1024.tif')


# Full NLCD: tif | none | 512x512
def read_sm_512_none():
    gp.mask_geom_on_raster(sm_geom, '/usr/data/nlcd/nlcd_512.tif')


# Full NLCD: tif | none | 256x256
def read_sm_256_none():
    gp.mask_geom_on_raster(sm_geom, '/usr/data/nlcd/nlcd.tif')


# Full NLCD: tif | lzw | 512x512
def read_sm_512_lzw():
    gp.mask_geom_on_raster(sm_geom, '/usr/data/nlcd/nlcd_512_lzw.tif')


# Full NLCD: tif | lzw | 256x256
def read_sm_256_lzw():
    gp.mask_geom_on_raster(sm_geom, '/usr/data/nlcd/nlcd_cp.tif')


# Full NLCD: tif | packbits | 256x256
def read_sm_256_pb():
    gp.mask_geom_on_raster(sm_geom, '/usr/data/nlcd/nlcd_cp_pb.tif')
