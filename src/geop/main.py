import os
import time
import numpy as np
import rasterio

from flask import Flask, request, jsonify
from rasterio import features
from shapely.geometry import shape

from utils import get_window_and_affine, reproject


app = Flask(__name__)

DATA_PATH = '/usr/data/'


@app.route('/counts', methods=['POST'])
def count():
    """
    Perform a rudimentary cell count analysis on a portion of a
    provided raster

    Query String Args:
        filename: file name of a valid geotiff in DATA_DIR
    """

    raster = request.args.get('filename')
    if not raster:
        return handle_error('filename parameter is required')

    raster_path = os.path.join(DATA_PATH, raster)
    if not os.path.isfile(raster_path):
        return handle_error('{} is not valid file in DATA_DIR'.format(raster))

    query_polygon = request.get_json(silent=True)
    if not query_polygon:
        return handle_error('GeoJSON polygon is required in body')

    start = time.clock()
    geom_5070 = reproject(shape(query_polygon))

    with rasterio.open(raster_path) as src:
        # Read a chunk of the raster that contains the bounding box of the
        # input geometry.  This has memory implications if that rectangle
        # is large. The affine transformation maps geom coordinates to the
        # image mask below.
        window, shifted_affine = get_window_and_affine(geom_5070, src)
        data = src.read(1, window=window)

    # Create a numpy array to mask cells which don't intersect with the
    # polygon. Cells that intersect will have value of 0 (unmasked), the
    # rest are filled with 1s (masked)
    geom_mask = features.rasterize(
        [(geom_5070, 0)],
        out_shape=data.shape,
        transform=shifted_affine,
        fill=1,
        dtype=np.uint8,
        all_touched=True
    )

    masked_data = np.ma.array(data=data, mask=geom_mask.astype(bool))

    # Perform count using numpy built-ins.  Compressing the masked array
    # creates a 1D array of just unmasked values.  May be able to speed up
    # by using scipy count_tier_group, but this is working well for now
    values, counts = np.unique(masked_data.compressed(), return_counts=True)

    # Make dict of val: count with string keys for valid json
    count_map = dict(zip(map(str, values), counts))

    return jsonify({
        'time': time.clock() - start,
        'cellCount': masked_data.count(),
        'counts': count_map,
    })


def handle_error(msg, code=400):
    response = jsonify({'message': msg})
    response.status_code = code
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0',
            port=8081,
            debug=True)
