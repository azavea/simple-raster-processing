import time

from flask import Flask, request, jsonify, send_file

import geoprocessing

from errors import UserInputError
from geo_utils import tile_to_bbox
from request_utils import parse_config


app = Flask(__name__)


@app.route('/counts', methods=['POST'])
def count():
    """
    Perform a cell count analysis on a portion of a provided raster.
    If `modifications` is present on the input payload, apply those
    modification values to the raster before peforming the count.
    """
    user_input = parse_config(request)

    start = time.clock()
    geom = user_input['query_polygon']
    raster_path = user_input['raster_paths'][0]
    mods = user_input['mods']

    total, count_map = geoprocessing.count(geom, raster_path, mods)

    return jsonify({
        'time': time.clock() - start,
        'cellCount': total,
        'counts': count_map,
    })


@app.route('/pair-counts', methods=['POST'])
def pair_counts():
    """
    For a pair of rasters whose extents and srs match, count cell pairs that
    occur when the rasters are stacked.  This resembles the geoprocessing
    required to run TR-55.  At present, this does not accept modifications.
    """
    user_input = parse_config(request)

    start = time.clock()
    geom = user_input['query_polygon']
    raster_paths = user_input['raster_paths']

    pair_map = geoprocessing.count_pairs(geom, raster_paths)

    return jsonify({
        'time': time.clock() - start,
        'pairs': pair_map
    })


@app.route('/xy', methods=['POST'])
def xy():
    """
    Get the cell value for a given GeoJSON point.
    """
    user_input = parse_config(request)

    start = time.clock()
    geom = user_input['query_polygon']
    raster_path = user_input['raster_paths'][0]

    value = geoprocessing.sample_at_point(geom, raster_path)

    return jsonify({
        'time': time.clock() - start,
        'value': value
    })


@app.route('/stats/<stat>', methods=['POST'])
def stats(stat):
    """
    Return basic statistics for query window
    """
    user_input = parse_config(request)

    start = time.clock()
    geom = user_input['query_polygon']
    raster_path = user_input['raster_paths'][0]

    value = geoprocessing.statistics(geom, raster_path, stat)

    return jsonify({
        'time': time.clock() - start,
        'stat': stat,
        'value': value
    })


@app.route('/nlcd/<int:z>/<int:x>/<int:y>.png')
def nlcd(z, x, y):
    # This would need to otherwise be specified in a config.
    # Requirements are EPSG:3857 and a color table
    path = '/usr/data/nlcd/nlcd_webm.tif'
    bbox = tile_to_bbox(z, x, y)
    img = geoprocessing.render_tile(bbox, path)
    img.seek(0)
    return send_file(img, mimetype='image/png')


@app.errorhandler(UserInputError)
def handle_error(error):
    response = jsonify({'message': error.message})
    response.status_code = error.status_code
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0',
            port=8081,
            debug=True)
