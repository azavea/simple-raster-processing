from flask import Flask
import rasterio

import os.path

app = Flask(__name__)


@app.route('/histogram', methods=['POST'])
def histogram():
    # Testing that the library is available
    print os.path.isfile('/vagrant/shapes/DelDem4ad8.tif')
    #src = rasterio.open('/vagrant/shapes/DelDem4ad8.tif')
    #return src.read(1)


@app.route('/ping', methods=['GET'])
def ping():
    return 'pong'


if __name__ == '__main__':
    app.run(host='0.0.0.0',
            port=8081,
            debug=True)
