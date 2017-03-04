from __future__ import division

import collections
import json
import itertools
import math
import numpy as np
import rasterio

from affine import Affine
from geo_utils import mask_geom_on_raster
from shapely.ops import cascaded_union
from shapely.geometry import shape, mapping, MultiPolygon

from multiprocessing import Process, Queue

def count(geom, raster_path, modifications=None):
    """
    Perform a cell count analysis on a portion of a provided raster.

    Args:
        geom (Shapley Geometry): A polygon in the same SRS as `raster_path`
            which will define the area of analysis to count cell values.

        raster_path (string): A local file path to a geographic raster
            containing values to extract.

        mods (optional list<dict>): A list of geometries and value to alter the
            source raster, provided as dict containing the following keys:

            geom (geojson): polygon of area where modification should be
                applied.

            newValue (int|float): value to be written over the source raster
                in areas where it intersects geom.  Modifications are applied
                in order, meaning subsequent items can overwrite earlier ones.

    Returns:
        total (int): total number of cells included in census

        count_map (dict): cell value keys with count of number of occurrences
            within the raster masked by `geom`

    """

    masked_data, _ = mask_geom_on_raster(geom, raster_path, modifications)
    return masked_array_count(masked_data)


def masked_array_count(masked_data):
    # Perform count using numpy built-ins.  Compressing the masked array
    # creates a 1D array of just unmasked values.  May be able to speed up
    # by using scipy count_tier_group, but this is working well for now
    values, counts = np.unique(masked_data.compressed(), return_counts=True)

    # Make dict of val: count with string keys for valid json
    count_map = dict(zip(map(str, values), counts))

    return masked_data.count(), count_map


def count_pairs(geom, raster_paths):
    """
    Perform a cell count analysis on groupings of cells from 2 rasters stacked
    on top of each other.

    Args:
        geom (Shapley Geometry): A polygon in the same SRS as `raster_path`
            which will define the area of analysis to count cell values.

        raster_paths (list<string>): Two local file paths to geographic rasters
            containing values to group and count.

    Returns:
        pairs (dict): Grouped pairs as key with count of number of occurrences
            within the two rasters masked by geom
            ex:  { cell1_rastA::cell1_rastB: 42 }
    """

    # Read in two rasters and mask geom on both of them
    layers = tuple(mask_geom_on_raster(geom, raster_path)[0]
                   for raster_path in raster_paths)

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
    # Since it's sorted, repeated entries will have a value of 0 at that index
    diff_sort = np.diff(sorted_arr, axis=0)

    # True or False value for each index of diff_sort based on a diff_sort
    # having truthy or falsey values.  Indexes with no change (0 values) will
    # be represented as False in this array
    indexes_changed_mask = np.any(diff_sort, 1)

    # Get the indexes that are True, indicating an index of sorted_arr that has
    # a difference with its preceding value - ie, it represents a new
    # occurrence of a value
    diff_indexes = np.where(indexes_changed_mask)[0]

    # Get the rows at the diff indexes, these are unique at each index
    unique_rows = [sorted_arr[i] for i in diff_indexes] + [sorted_arr[-1]]

    # Prepend a -1 on the list of diff_indexes and append the index of the last
    # unique row, resulting in an array of index changes with fenceposts on
    # both sides.  ie, `[-1, ...list of diff indexes..., <idx of last sorted>]`
    idx_of_last_val = sorted_arr.shape[0] - 1
    diff_idx_with_start = np.insert(diff_indexes, 0, -1)
    fencepost_diff_indexes = np.append(diff_idx_with_start, idx_of_last_val)

    # Get the number of occurrences of each unique row based on the difference
    # between the indexes at which they change.  Since we put fenceposts up,
    # we'll get a count for the first and last elements of the diff indexes
    counts = np.diff(fencepost_diff_indexes)

    # Map the pairs to the count, compressing values to keys in this format:
    #   cell_r1::cell_r2
    pair_counts = zip(unique_rows, counts)
    pair_map = {str(k[0]) + '::' + str(k[1]): cnt for k, cnt in pair_counts}

    return pair_map


def sample_at_point(geom, raster_path):
    """
    Return the cell value for a raster at a provided geographic coordinate

    Args:
        geom (Shapely Geometry): A Point object in the same SRS as the target
            raster defining the point to extract the cell value.

        raster_path (string): A local file path to a geographic raster
            containing the value to extract.

    Returns:
        The cell value, in the data type of the input raster, at the point
        defined by geom

    """

    with rasterio.open(raster_path) as src:
        # Sample the raster at the given coordinates
        value_gen = src.sample([(geom.x, geom.y)], indexes=[1])
        value = value_gen.next().item(0)

    return value


def weighted_overlay(geom, raster_paths, weights):
    """
    Performs a weighted overlay analysis on provided rasters within a given
    area of interest. It is assumed that the provided rasters are already
    classified to a shared preference scale.

    Reference:
       http://pro.arcgis.com/en/pro-app/tool-reference/spatial-analyst/weighted-overlay.htm  # noqa

    Args:
        geom (Shapley Geometry): A polygon in the same SRS as `raster_path`
            which will define the area of interest in the weighted overlay

        raster_paths (list<string>): A  list of local file paths to geographic
            rasters containing values to weight and extract.

        weights (list<float>): A list of weights to multiply values from the
            corresponding index of  a raster in `raster_paths`.  The sum of
            all elements in this list should equal 1

    Returns:
        Numpy masked array of the results of the combining and weighting of
        the input rasters

    """
    # Read in rasters and mask geom on them
    layers = [mask_geom_on_raster(geom, raster_path)[0]
              for raster_path in raster_paths]

    return weighted_overlay_from_data(layers, weights)


def weighted_overlay_from_data(layers, weights):
    # Multiply the weight for each layer across all cell values
    weighted = [layer * weights[idx] for idx, layer in enumerate(layers)]

    # Add the weighted layers together into a single layer
    final = sum(weighted)
    return final


def reclassify(geom, raster_path, substitutions):
    """
    Reclassifies a raster by substituting all occurences of a value or range of
    values with another provided value.  Substitutions are applied in order.

    Args:
        geom (Shapley Geometry): A polygon in the same SRS as `raster_path`
            which will define the area of interest where the reclass is applied

        raster_path (string): A  local file path to a geographic raster
            containing values reclassify.

        substitutions (list<[oldVal, newval]>): A list of pairs whose first
            index represents the old value to be replaced with the value in
            the second index.  If oldVal is an iterable, it will create an
            inclusive range of values for reclassification:
               [11, 1]: all 11 values will be replaced by 1
               [[90,99], 9]: all values >= 90 & <=99 will be replaced by 9

    Returns:
        Numpy masked array of the results of making the changes defined for
        all cells represented by `substitutions`
    """
    # Read in the raster and mask geom on it
    layer, transform = mask_geom_on_raster(geom, raster_path)
    return reclassify_from_data(layer, substitutions)


def reclassify_from_data(layer, substitutions):
    # For every range or direct replacement, copy over existing values
    for reclass in substitutions:
        old, new = reclass

        if isinstance(old, collections.Iterable):
            low, high = old
            expression = np.ma.where((low <= layer) & (layer <= high))
        else:
            expression = np.ma.where(old == layer)

        layer[expression] = new

    return layer


def statistics(geom, raster_path, stat):
    """
    Computes the specified statistic over the values in raster_path that
    intersect with geom

    Args:
        geom (Shapley Geometry): A polygon in the same SRS as `raster_path`
            which will define the area of interest where the statistic
            is calculated

        raster_path (string): A local file path to a geographic raster
            containing values reclassify.

        stat (string): The statistic to be calculated. Valid values:
            mean, min, max, stddev

    Returns
        The single value of the statistical operation
    """
    # Read in the raster and mask geom on it
    layer, _ = mask_geom_on_raster(geom, raster_path)

    # Determine the correct statistic requested
    if stat == 'max':
        return layer.max().item(0)
    elif stat == 'min':
        return layer.min().item(0)
    elif stat == 'mean':
        return layer.mean()
    elif stat == 'stddev':
        return layer.std()
    else:
        raise Exception("{0} has not been implemented".format(stat))


def extract(geom, raster_path, value):
    layer, transform = mask_geom_on_raster(geom, raster_path)
    mask = layer == value
    features = rasterio.features.shapes(layer, mask=mask, transform=transform)

    return [feature[0] for feature in features]

def union(cnt, features):
        s = MultiPolygon(features)

        with open('/usr/data/out/pa-{}.json'.format(cnt), 'w') as f:
            f.write(json.dumps(mapping(s)))
        print(cnt, 'saved')


def setup_queue(queue):
    shape_handler = Process(target=extract_above, args=((queue),))
    shape_handler.daemon = False
    shape_handler.start()
    return shape_handler


def elevation_increments(geom, raster_path):

    # Get min/max of masked area
    print('start')
    layer, transform = mask_geom_on_raster(geom, raster_path)
    print('read in')
    min_el = layer.min()
    max_el = layer.max()

    inc = .1524  # Half foot in meters
    cnt = 0
    lower = min_el
    upper = min_el + inc
    runs = math.ceil((max_el - min_el)/inc)

    print('{} to {}'.format(min_el, max_el))
    print('Generating {} levels'.format(runs))

    queue = Queue()
    processes = [setup_queue(queue) for i in range(5)]

    shapes = []
    level = lower
    while level <= max_el:
        queue.put((cnt, layer, transform, lower, upper))

        level += inc
        upper += inc
        cnt += 1

    for p in processes:
        queue.put([None] * 5)


def extract_above(queue):

    while True:
        cnt, layer, transform, lower, upper = queue.get()
        if cnt is not None:
            max_rows = layer.shape[0]
            start = 0
            end = 1000
            inc = 1000

            increment_vectors = []
            while start < max_rows:
                # Create array bool from mask and extract on it.
                layer_chunk = layer[start:end]
                chunk = np.ones(shape=layer_chunk.shape, dtype=np.uint8)
                layer_mask_chunk = layer.mask[start:end]

                mask = ((layer_chunk >= lower) & (layer_chunk <= upper) & ~layer_mask_chunk)
                chunk[mask] = 0

                # Transorm the Affine from the large window to the chunk
                t = transform
                f = t.f + start * t.e
                shifted = Affine(t.a, t.b, t.c, t.d, t.e, f)

                # Pull the features out
                features = rasterio.features.shapes(chunk, mask=mask, transform=shifted)

                # Exercise the generator to get a list of shapes
                chunk_vectors = [shape(feature[0]) for feature in features]

                # Union them together into a single polygon
                #increment_vectors.append(cascaded_union(chunk_vectors)))
                increment_vectors.append(chunk_vectors)

                start = end
                end = end + inc

            #return cascaded_union(increment_vectors)
            union(cnt, list(itertools.chain(*increment_vectors)))
        else:
            print('fin')
            break
