import os
from shapely.geometry import shape

from geo_utils import reproject
from errors import UserInputError

DATA_PATH = '/usr/data/'
DEFAULT_SRS = 'epsg:5070'


def get_path(raster_name):
    raster_path = os.path.join(DATA_PATH, raster_name)
    if not os.path.isfile(raster_path):
        raise UserInputError(
            '{} is not valid file in DATA_DIR'.format(raster_name))
    return raster_path


def parse_config(request):
    """
    Parse a JSON object from the request.

    Keys:
        rasters (list): List of filenames for rasters
        queryPolygon (GeoJSON): Input to query on
        src_srs (string): Optional.  SRS of `rasters`. Defaults to EPSG:5070

    """

    req_config = request.get_json(silent=True)

    if req_config:
        rasters = req_config.get('rasters', None)
        if not rasters:
            raise UserInputError('rasters key is required in config')

        raster_paths = [get_path(raster) for raster in rasters]

        query_polygon = req_config.get('queryPolygon', None)
        if not query_polygon:
            raise UserInputError('queryPolygon key is required in config')

        srs = req_config.get('src_srs', DEFAULT_SRS)

        # Reproject the required input query polygon
        query_polygon_srs = reproject(shape(query_polygon), srs)

        # Modifications are optional, reproject if any exist
        mods = req_config.get('modifications', None)
        if mods:
            for mod in mods:
                mod['geom'] = reproject(shape(mod['geom']), srs)

        return {
            'query_polygon': query_polygon_srs,
            'raster_paths': raster_paths,
            'srs': srs,
            'mods': mods,
        }

    raise UserInputError('JSON config is required in body')
