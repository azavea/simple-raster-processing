import time
import numpy as np
import rasterio

from flask import Flask, request, jsonify
from rasterio import features
from shapely.geometry import shape

from errors import UserInputError
from geo_utils import get_window_and_affine, reproject
from request_utils import parse_config


app = Flask(__name__)


@app.route('/counts', methods=['POST'])
def count():
    """
    Perform a rudimentary cell count analysis on a portion of a
    provided raster
    """
    user_input = parse_config(request)

    start = time.clock()
    geom = reproject(
            shape(user_input['query_polygon']),
            to_srs=user_input['srs'])

    raster_path = user_input['raster_paths'][0]

    with rasterio.open(raster_path) as src:
        # Read a chunk of the raster that contains the bounding box of the
        # input geometry.  This has memory implications if that rectangle
        # is large. The affine transformation maps geom coordinates to the
        # image mask below.
        window, shifted_affine = get_window_and_affine(geom, src)
        data = src.read(1, window=window)

    # Create a numpy array to mask cells which don't intersect with the
    # polygon. Cells that intersect will have value of 0 (unmasked), the
    # rest are filled with 1s (masked)
    geom_mask = features.rasterize(
        [(geom, 0)],
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


@app.errorhandler(UserInputError)
def handle_error(error):
    response = jsonify({'message': error.message})
    response.status_code = error.status_code
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0',
            port=8081,
            debug=True)
