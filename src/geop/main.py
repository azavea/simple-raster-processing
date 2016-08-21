import time
import numpy as np

from flask import Flask, request, jsonify
from shapely.geometry import shape

from errors import UserInputError
from geo_utils import mask_geom_on_raster, reproject
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
    to_srs = user_input['srs']
    geom = reproject(
            shape(user_input['query_polygon']),
            to_srs=to_srs)

    raster_path = user_input['raster_paths'][0]
    mods = user_input['mods']
    if mods:
        for mod in mods:
            mod['geom'] = reproject(shape(mod['geom']), to_srs)

    masked_data = mask_geom_on_raster(geom, raster_path, mods)

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
    For a pair of rasters whose extents and srs match, count cell pairs that
    occur when the rasters are stacked.  This resembles the geoprocessing
    required to run TR-55.
    """
    user_input = parse_config(request)

    start = time.clock()
    geom = reproject(
            shape(user_input['query_polygon']),
            to_srs=user_input['srs'])

    # Read in two rasters and mask geom on both of them
    layers = tuple(mask_geom_on_raster(geom, raster_path)
                   for raster_path in user_input['raster_paths'])

    # Take the two masked arrays, and stack them along the third axis
    # Effectively: [[cell_1a, cell_1b], [cell_2a, cell_2b], ..],[[...]]
    pairs = np.ma.dstack(layers)

    # Get the array in 2D form
    arr = pairs.reshape(-1, pairs.shape[-1])

    # Remove Rows which have masked values
    trim_arr = np.ma.compress_rowcols(arr, 0)

    # Lexicographically sort so that repeated pairs follow one another
    sorted_arr = trim_arr[np.lexsort(trim_arr.T), :]

    # The difference between index n and n+1 in sorted_arr, for each index.
    # Since it's sorted, repated entries will have a value of 0 at that index
    diff_sort = np.diff(sorted_arr, axis=0)

    # True or False value for each index of diff_sort where based on a diff_sort
    # having truthy or falsey values.  Indexs with no change (0 values) will be
    # represended as False in this array
    indexes_changed_mask = np.any(diff_sort, 1)

    # Get the indexes that are True, indicating an index of sorted_arr that has
    # a difference with its preceeding value - ie, it represents a new occurance
    # of a value
    diff_indexes = np.where(indexes_changed_mask)[0]

    # Get the rows at the diff indexes, these are unique at each index
    unique_rows = [sorted_arr[i] for i in diff_indexes] + [sorted_arr[-1]]

    # Prepend a -1 on the list of diff_indexes and append the index of the last
    # unique row, resulting in an array of index changes with fenceposts on
    # both sides.  ie, `[-1, ...list of diff indexes..., <idx of last sorted>]`
    idx_of_last_val = sorted_arr.shape[0] - 1
    diff_idx_with_start = np.insert(diff_indexes, 0, -1)
    fencepost_diff_indexes = np.append(diff_idx_with_start, idx_of_last_val)

    # Get the number of occurences of each unique row based on the difference
    # between the indexes at which they change.  Since we put fenceposts up,
    # we'll get a count for the first and last elements of the diff indexes
    counts = np.diff(fencepost_diff_indexes)

    # Map the pairs to the count, compressing values to keys in this format:
    #   cell_r1::cell_r2
    pair_counts = zip(unique_rows, counts)
    pair_map = {str(k[0]) + '::' + str(k[1]): cnt for k, cnt in pair_counts}

    return jsonify({
        'time': time.clock() - start,
        'pairs': pair_map
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
