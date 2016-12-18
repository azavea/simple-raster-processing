from PIL import Image
from io import BytesIO

from geo_utils import tile_read


def render_tile(geom, raster_path, user_palette):
    """
    Generates a visual PNG map tile from a vector polygon

    Args:
        geom (Shapely Geometry): A polygon corresponding to a TMS tile
            request boundary

        raster_path (string): A local file path to a raster in EPSG:3857
            to generate visual tile from

        uer_palette (optional list): A sequence of RGB triplets whose index
            corresponds to the raster value which will be rendered. If
            provided, will override a ColorTable defined in the raster
    Returns:
        Byte Array of image in the PNG format
    """
    tile, palette = tile_read(geom, raster_path)
    return render_tile_from_data(tile, user_palette or palette)


def render_tile_from_data(tile, palette):
    """
    Generates a visual PNG map tile from an ndarray of raster data

    Args:
        tile (ndarray) : A square 256x256 array of raster values

        palette (list<int>): A list of RGB values to render `tile`

    Returns:
        Byte Array of image in the PNG format
    """
    img = Image.fromarray(tile, mode='P')

    if len(palette):
        img.putpalette(palette)

    img_data = BytesIO()
    img.save(img_data, 'png')
    img_data.seek(0)
    return img_data
