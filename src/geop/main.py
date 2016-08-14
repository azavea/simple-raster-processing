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


@app.route('/pair-counts', methods=['POST'])
def pair_counts():
    """
    For a pair of rasters whos extents and srs match, count cell pairs that
    occur when the rasters are stacked.  This resembles the geoprocessing
    required to run TR-55.
    """
    user_input = parse_config(request)

    start = time.clock()
    geom = reproject(
            shape(user_input['query_polygon']),
            to_srs=user_input['srs'])

    def mask_geom_on_raster(raster_path):
        with rasterio.open(raster_path) as src:
            window, shifted_affine = get_window_and_affine(geom, src)
            data = src.read(1, window=window)

        geom_mask = features.rasterize(
            [(geom, 0)],
            out_shape=data.shape,
            transform=shifted_affine,
            fill=1,
            dtype=np.uint8,
            all_touched=True
        )

        return np.ma.array(data=data, mask=geom_mask.astype(bool))

    layers = [mask_geom_on_raster(raster_path)
              for raster_path in user_input['raster_paths']]

    first = layers[0].astype('str')
    second = layers[1].astype('str')

    with_sep = np.core.defchararray.add('::', second)
    joined = np.core.defchararray.add(first, with_sep)

    values, counts = np.unique(joined, return_counts=True)

    # Make dict of val: count with string keys for valid json
    count_map = dict(zip(values, counts))

    return jsonify({
        'time': time.clock() - start,
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
