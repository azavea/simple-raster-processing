import os
import time

from flask import Flask, request, jsonify
import numpy as np
import rasterio

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

    counts = {}
    start = time.clock()
    with rasterio.open(raster_path) as src:
        w = src.read(1, window=((10000, 10350), (10000, 10350)))

        for idx, cell in np.ndenumerate(w):
            cell_val = str(cell)

            if cell_val in counts:
                counts[cell_val] += 1
            else:
                counts[cell_val] = 1

    elapsed = time.clock() - start
    cells = reduce(lambda s, key: s + counts[key], counts.keys(), 0)

    return jsonify({
        'time': elapsed,
        'cellCount': cells,
        'counts': counts,
    })


def handle_error(msg, code=400):
    response = jsonify({'message': msg})
    response.status_code = code
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0',
            port=8081,
            debug=True)
