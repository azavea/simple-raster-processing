from affine import Affine
from functools import partial
from shapely.ops import transform

import pyproj


def get_window_and_affine(geom, raster_src):
    """
    Get a rasterio window block from the bounding box of a vector feature and
    calculates the affine transformation needed to map the coordinates of the
    geometry onto a resulting array defined by the shape of the window.

    Args:
        geom (Shapely geometry): A geometry in the spatial reference system
            of the raster to be read.

        raster_src (rasterio file-like object): A rasterio raster source which
            will have the window operation performed and contains the base
            affine transformation.

    Returns:
        A pair of tuples which define a rectangular range that can be provided
        to rasterio for a windowed read
        See: https://mapbox.github.io/rasterio/windowed-rw.html#windowrw

        An Affine object used to transform geometry coordinates to cell values
    """

    # Create a window range from the bounds
    ul = raster_src.index(*geom.bounds[0:2])
    lr = raster_src.index(*geom.bounds[2:4])
    window = ((lr[0], ul[0]+1), (ul[1], lr[1]+1))

    # Create an affine transformation relative to that window.  Still a little
    # opaque to me and lifted from:
    # https://snorfalorpagus.net/blog/2014/11/09/masking-rasterio-layers-with-vector-features/
    t = raster_src.affine
    c = t.c + ul[1] * t.a
    f = t.f + lr[0] * t.e
    shifted_affine = Affine(t.a, t.b, c, t.d, t.e, f)

    return window, shifted_affine


def reproject(geom, to_srs='epsg:5070', from_srs='epsg:4326'):
    """"
    Reproject `geom` from one spatial ref to another

    Args:
        geom (Shapely Geometry): A geometry object with coordinates to
            transform.
        from_srs (string): An EPSG code in the format of `epsg:nnnn` that
            specifies the existing spatial ref for `geom`
        to_srs (string): An EPSG code in the format of `epsg:nnnn` that
            specifies the desired ref for the returned geometry

    Returns:
        Shapely Geometry with coordinates transformed to the desired srs

    """
    projection = partial(
        pyproj.transform,
        pyproj.Proj(init=from_srs),
        pyproj.Proj(init=to_srs),
    )

    return transform(projection, geom)
