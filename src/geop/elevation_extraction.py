from __future__ import division

import json
import itertools
import math

import numpy as np
import rasterio

from affine import Affine
from multiprocessing import Process, Queue, cpu_count
from shapely.geometry import shape, mapping, MultiPolygon

from geo_utils import mask_geom_on_raster, mask_sections_on_raster, \
    subdivide_polygon


# Iniialized globaly to share with multiple processes
SHARED_LAYER = None


def min_max_from_sections(geom, raster_path):
    sections = subdivide_polygon(geom, 1)
    print(len(sections))

    i = 0
    mins, maxs = [], []
    for tile, transform, meta, window in mask_sections_on_raster(sections, raster_path):
        print('.')
        #with rasterio.open('s3://cwbi-geoprocessing-ned/test-write.tif', 'r+', )
        fmeta = meta.copy()
        fmeta.update({
            'height': window[0][1] - window[0][0],
            'width': window[1][1] - window[1][0],
            'transform': transform
        })
        with rasterio.open('./test{}.tif'.format(i), 'w', **fmeta) as out:
            out.write(tile, indexes=1)

        mins.append(tile.min())
        maxs.append(tile.max())
        i += 1

    print(min(mins), max(maxs))


def save_features(cnt, features):
        s = MultiPolygon(features)

        with open('/usr/data/out/pa-{}.json'.format(cnt), 'w') as f:
            f.write(json.dumps(mapping(s)))
        print(cnt, 'saved')


def setup_processes(queue):
    shape_handler = Process(target=extract_between, args=((queue),))

    # Allow the main process to block until the spawned processes terminate
    shape_handler.daemon = False
    shape_handler.start()
    return shape_handler


def process_increments(geom, raster_path):

    # Get min/max of masked area
    print('start')
    layer, transform = mask_geom_on_raster(geom, raster_path)
    print('read in')
    min_el = layer.min()
    max_el = layer.max()

    # Make shared_layer a a module level variable that can be
    # shared between processes on a posix system.  Treat as readonly.
    # Then create a queue and processes to consume from it, based on
    # the system cpu count
    global SHARED_LAYER
    SHARED_LAYER = layer
    queue = Queue()
    processes = [setup_processes(queue) for i in range(cpu_count())]

    inc = .1524  # Half foot in meters
    cnt = 0
    lower = min_el
    upper = min_el + inc
    runs = math.ceil((max_el - min_el)/inc)

    print('{} to {}'.format(min_el, max_el))
    print('Generating {} levels using {} cores'.format(runs, cpu_count()))

    level = lower
    while level <= max_el:
        queue.put((cnt, transform, lower, upper))

        level += inc
        upper += inc
        cnt += 1

    # Put enough kill messages in the queue for each process to receive
    for p in processes:
        queue.put([None] * 4)


def extract_between(queue):

    while True:
        cnt, transform, lower, upper = queue.get()
        if cnt is not None:
            max_rows = SHARED_LAYER.shape[0]
            start = 0

            # These numbers have an impact on speed, memory use and output
            # Larger value will be slower and consume more memory at once, but
            # will produce fewer "stripes" in the resulting Geometry Collection
            end = 1000
            inc = 1000

            increment_vectors = []
            while start < max_rows:
                # Create array bool from mask and extract on it.
                layer_chunk = SHARED_LAYER[start:end]
                chunk = np.ones(shape=layer_chunk.shape, dtype=np.uint8)
                layer_mask_chunk = SHARED_LAYER.mask[start:end]

                mask = ((layer_chunk >= lower) & (layer_chunk <= upper) &
                        ~layer_mask_chunk)
                chunk[mask] = 0

                # Transorm the Affine from the large window to the chunk
                t = transform
                f = t.f + start * t.e
                affine = Affine(t.a, t.b, t.c, t.d, t.e, f)

                # Pull the features out
                features = rasterio.features.shapes(chunk, mask=mask,
                                                    transform=affine)

                # Exercise the generator to get a list of shapes
                chunk_vectors = [shape(feature[0]) for feature in features]

                # Persist the vectors from this chunk
                increment_vectors.append(chunk_vectors)

                # Increment the window to read from the raster layer
                start = end
                end = end + inc

            save_features(cnt, list(itertools.chain(*increment_vectors)))
        else:
            # When the queue sends a kill message, exit the read loop
            break
