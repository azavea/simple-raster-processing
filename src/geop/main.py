from flask import Flask, request, jsonify, send_file
import numpy as np

import geoprocessing
import tiles

from errors import UserInputError
from geo_utils import tile_to_bbox, tile_read
from request_utils import parse_config


app = Flask(__name__)


@app.route('/counts', methods=['POST'])
def count():
    """
    Perform a cell count analysis on a portion of a provided raster.
    If `modifications` is present on the input payload, apply those
    modification values to the raster before performing the count.
    """
    user_input = parse_config(request)

    geom = user_input['query_polygon']
    raster_path = user_input['raster_paths'][0]
    mods = user_input['mods']

    total, count_map = geoprocessing.count(geom, raster_path, mods)

    return jsonify({
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

    geom = user_input['query_polygon']
    raster_paths = user_input['raster_paths']

    pair_map = geoprocessing.count_pairs(geom, raster_paths)

    return jsonify({
        'pairs': pair_map
    })


@app.route('/xy', methods=['POST'])
def xy():
    """
    Get the cell value for a given GeoJSON point.
    """
    user_input = parse_config(request)

    geom = user_input['query_polygon']
    raster_path = user_input['raster_paths'][0]

    value = geoprocessing.sample_at_point(geom, raster_path)

    return jsonify({
        'value': value
    })


@app.route('/stats/<stat>', methods=['POST'])
def stats(stat):
    """
    Return basic statistics for query window
    """
    user_input = parse_config(request)

    geom = user_input['query_polygon']
    raster_path = user_input['raster_paths'][0]

    value = geoprocessing.statistics(geom, raster_path, stat)

    return jsonify({
        'stat': stat,
        'value': value
    })


@app.route('/<layer>/<int:z>/<int:x>/<int:y>.png')
def layer_tile(layer, z, x, y):
    """
    Given a known layer, render the tile at z/x/y with an embedded color table
    or a user defined color palette
    """
    # This would need to otherwise be specified in a config.
    # Requirements are EPSG:3857
    user_palette = None
    if layer == 'nlcd':
        path = '/usr/data/nlcd/nlcd_webm_512.tif'
    elif layer == 'nlcd_s3':
        path = 's3://simple-raster-processing/nlcd_webm_512.tif'
    elif layer == 'soil':
        path = '/usr/data/hydro_soils_webm_512.tif'
        user_palette = [255,255,255, 255,255,212, 254,227,145, 204,76,2, 140,45,4, 254,196,79, 254,153,41, 236,112,20]  # noqa
    else:
        raise UserInputError('No layer {0} is registered.'.format(layer))

    bbox = tile_to_bbox(z, x, y)

    img = tiles.render_tile(bbox, path, user_palette)
    return send_file(img, mimetype='image/png')


@app.route('/nlcd-grouped/<int:z>/<int:x>/<int:y>.png')
def reclass_tile(z, x, y):
    """
    On the fly reclassification of NLCD values into groups
    """
    # This would need to otherwise be specified in a config.
    # Requirements are EPSG:3857 and a color table
    path = '/usr/data/nlcd/nlcd_webm_512.tif'
    bbox = tile_to_bbox(z, x, y)
    tile, palette = tile_read(bbox, path)
    # Reclassify the nlcd data to be in related groups
    substitutions = [[(21, 24), 23], [(41, 52), 41], [(71, 74), 71],
                     [(81, 82), 81], [(90, 95), 11]]
    geoprocessing.reclassify_from_data(tile, substitutions)

    # Render new tiles using the reclassified nlcd data
    img = tiles.render_tile_from_data(tile, palette)
    return send_file(img, mimetype='image/png')


@app.route('/priority/<int:z>/<int:x>/<int:y>.png')
def priority(z, x, y):
    """
    A contrived prioritization analysis to identify areas where Green
    Stormwater Infrastructure projects would have the most benefit. This
    demonstrates chaining a few geoprocessing tasks together:  First, two
    layers are reclassified into normalized priority scores, which are then
    applied to a weighted overlay, determining an overall priority score. This
    final layer is then rendered visually to denote where GSI projects could
    have a high impact.  The reclassifications and weights could easily be
    provided by the client, exposing they dynamic nature of this on-the-fly
    processing.
    """
    # This would need to otherwise be specified in a config.
    # Requirements are EPSG:3857
    nlcd_path = '/usr/data/nlcd/nlcd_webm_512.tif'
    soil_path = '/usr/data/hydro_soils_webm_512.tif'

    # Decimated read for the bbox of each layer.
    bbox = tile_to_bbox(z, x, y)
    nlcd_tile, _ = tile_read(bbox, nlcd_path)
    soil_tile, _ = tile_read(bbox, soil_path)

    # Reclassify both the nlcd and soils data sets into a priority map of
    # 0 (low) to 10 (high) normalized values.  For example, NLCD 21-24 are
    # highly impervious and are rated as a 10, where 42-43 are forested and
    # marked a low priority
    nlcd_reclass = [[11, 0], [(21, 24), 10], [31, 7], [(41, 43), 1],
                    [(51, 52), 6], [(71, 74), 4], [(81, 82), 5], [(90, 95), 2]]

    # Soil values aren't linearly worse, 3&4 have the slowest infiltration,
    # followed by 6&7.  Ordering is important so a reclassed value doesn't
    # get reclassed again by a subsequent rule
    soil_reclass = [[255, 0], [3, 8], [4, 10], [(6, 7), 8], [5, 6], [2, 5]]

    nlcd_priority = geoprocessing.reclassify_from_data(nlcd_tile, nlcd_reclass)
    soil_priority = geoprocessing.reclassify_from_data(soil_tile, soil_reclass)

    # Use the two relative priority layers and weight them, giving the NLCD
    # layer more weight when determining an overall priority map.  The result
    # is a layer with values of 0 - 10 that identifies areas more in need
    # of Green Stormwater Infrastructure projects, based on the defined
    # scores and preferences.
    layers = [nlcd_priority, soil_priority]
    weights = [0.65, 0.35]
    priority = geoprocessing.weighted_overlay_from_data(layers, weights)

    # The weighted overlay will produce floats, but for rendering purposes we
    # can round to ints so that we can create a straightforward palette
    priority_rounded = priority.astype(np.uint8)

    # A color palette from 0 (white -> green) to 10 (red) for our overall
    # site priorities
    palette = [255,255,255, 0,104,55, 26,152,80, 102,189,99, 166,217,106, 217,239,139, 254,224,139, 253,174,97, 244,109,67, 215,48,39, 165,0,38]  # noqa

    # Render the image tile for this priority map with the new palette
    img = tiles.render_tile_from_data(priority_rounded, palette)
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
