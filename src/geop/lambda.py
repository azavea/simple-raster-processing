from __future__ import print_function
from __future__ import division

from request_utils import parse_config
import geoprocessing


def handler(body, context):
    """
    Perform a cell count analysis on a portion of a provided raster.
    If `modifications` is present on the input payload, apply those
    modification values to the raster before performing the count.
    """

    # Due to differences in lamda and api gateway test interface, this
    # may be parsed json or a string
    user_input = parse_config(body)
    geom = user_input['query_polygon']
    layers = user_input['raster_paths']
    mods = user_input['mods']

    method = body['method']

    if method == 'count':
        return count(geom, layers[0], mods)


def count(geom, raster_path, mods):
    total, count_map = geoprocessing.count(geom, raster_path, mods)

    return {
        'cellCount': total,
        'counts': count_map,
    }


if __name__ == '__main__':
    """
    Simple check against the above function intended for lambda execution
    """
    url = "s3://simple-raster-processing/nlcd_512_lzw_tiled.tif"
    body = {
            "method": "count",
            "rasters": [url],
            "queryPolygon": {
                "type": "Polygon",
                "coordinates": [[[-75.26870727539062, 39.876546372401194],
                                 [-75.26870727539062, 40.05127080263306],
                                 [-75.03868103027344, 40.05127080263306],
                                 [-75.03868103027344, 39.876546372401194],
                                 [-75.26870727539062, 39.876546372401194]]]
              }
         }

    print(body)  # Output can be used in API Gateway test UI
    print(handler(body, None))
