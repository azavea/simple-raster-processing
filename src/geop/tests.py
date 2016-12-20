from __future__ import division

import unittest
import geoprocessing
import geo_utils
import numpy as np

from copy import copy
from shapely.geometry import Point, Polygon
from shapely.geometry.geo import box

NLCD_PATH = '../test_data/philly_nlcd.tif'
NLCD_EDIT_PATH = '../test_data/philly_nlcd_edited.tif'
NLCD_ONES = '../test_data/philly_ones.tif'      # all cells are 1
NLCD_THREES = '../test_data/philly_threes.tif'  # all cells are 3
NLCD_LARGE = '../test_data/nlcd_large.tif'


class CountTests(unittest.TestCase):
    count_geom = Polygon([
            [1747260.99651947943493724, 2071928.23170474520884454],
            [1747260.99651947943493724, 2071884.15942327585071325],
            [1747323.9569215786177665, 2071882.06074320594780147],
            [1747321.85824150871485472, 2071927.53214472183026373],
            [1747260.99651947943493724, 2071928.23170474520884454]])

    expectedCounts = {'11': 2, '24': 2, '23': 2}

    def test_count(self):
        """
        Tests the count of a known polygon against the NLCD raster
        to verify the correct number of values are counted
        """
        total, counts = geoprocessing.count(self.count_geom, NLCD_PATH)

        self.assertEqual(total, 6)
        self.assertDictEqual(counts, self.expectedCounts)

    def test_count_with_mods(self):
        """
        Tests the count of a known polygon after modifications to a
        source raster have been made
        """
        # Change the area of the source raster that has a value of 11 to 42
        # within this polygon, which is a a subset of the AoI
        modificationPolygon = Polygon([
            [1747265.19387961947359145, 2071930.33038481511175632],
            [1747265.19387961947359145, 2071890.45546348579227924],
            [1747250.50311912968754768, 2071889.75590346241369843],
            [1747251.20267915306612849, 2071927.53214472183026373],
            [1747250.50311912968754768, 2071927.53214472183026373],
            [1747265.19387961947359145, 2071930.33038481511175632]])

        mods = [{'geom': modificationPolygon, 'newValue': 42}]

        # Expect the base counts but with all values of 11 changed to 42
        modifiedCounts = copy(self.expectedCounts)
        modifiedCounts['42'] = modifiedCounts.pop('11')

        total, counts = geoprocessing.count(self.count_geom, NLCD_PATH, mods)

        self.assertEqual(total, 6)
        self.assertDictEqual(counts, modifiedCounts)

    def test_pair_count(self):
        """
        Test the count of a known polygon against two edited rasters
        to verify that the correct pairs of values are counted
        """
        geom = Polygon([
            [1747247.00531901302747428, 2071931.02994483849033713],
            [1747248.4044390597846359, 2071849.88098213309422135],
            [1747333.05120188184082508, 2071848.48186208633705974],
            [1747333.05120188184082508, 2071931.02994483849033713],
            [1747247.00531901302747428, 2071931.02994483849033713]])

        expectedPairs = {
            '11::44': 2, '11::55': 1, '11::33': 1,
            '23::77': 2, '24::99': 1, '24::88': 2
        }
        pairs = geoprocessing.count_pairs(geom, [NLCD_PATH, NLCD_EDIT_PATH])

        self.assertDictEqual(pairs, expectedPairs)


class SamplingTests(unittest.TestCase):
    def test_xy(self):
        """
        Tests the value of a known point againt the NLCD raster
        to verify the cell value at the point is correct
        """
        geom = Point(1747240.00972, 2071756.8395)
        value = geoprocessing.sample_at_point(geom, NLCD_PATH)

        self.assertEqual(value, 11)


class WeightedOverlayTests(unittest.TestCase):
    def test_weighted_overlay(self):
        """
        Tests that rasters are appropriately weighted and summed
        for the weighted overlay operation
        """
        geom = Polygon([
            [1747032.24039185303263366, 2071990.49254682078026235],
            [1747037.83687203959561884, 2071660.30021581239998341],
            [1747416.29884465713985264, 2071660.99977583577856421],
            [1747415.59928463399410248, 2071989.79298679763451219],
            [1747032.24039185303263366, 2071990.49254682078026235]
        ])

        rasters = [NLCD_ONES, NLCD_THREES]
        weights = [   0.75  ,    0.25    ]  # noqa

        # Raster with all 1 values overlayed with all 3 values and their
        # weights should produce a new layer with all cells having the
        # value of `expected`
        expected = 1 * weights[0] + 3 * weights[1]
        layer = geoprocessing.weighted_overlay(geom, rasters, weights)
        self.assertTrue(np.all(layer == expected))


class RelassificationTests(unittest.TestCase):
    reclass_geom = Polygon([
        [1747032.24039185303263366, 2071990.49254682078026235],
        [1747037.83687203959561884, 2071660.30021581239998341],
        [1747416.29884465713985264, 2071660.99977583577856421],
        [1747415.59928463399410248, 2071989.79298679763451219],
        [1747032.24039185303263366, 2071990.49254682078026235]
    ])

    def test_single_reclass(self):
        """
        Tests that a single substitution is made for a reclass definition
        """
        reclass = [(11, 100)]
        new_layer = geoprocessing.reclassify(self.reclass_geom,
                                             NLCD_PATH, reclass)
        self.assertFalse(np.any(new_layer == 11))

        orig_count = geoprocessing.count(self.reclass_geom, NLCD_PATH)[1]['11']
        new_count = geoprocessing.masked_array_count(new_layer)[1]['100']

        self.assertEqual(orig_count, new_count)

    def test_multi_reclass(self):
        """
        Tests that a multiple substitutions are made for a reclass definition
        containing more than one definition
        """
        reclass = [(11, 100), (21, 200)]
        new_layer = geoprocessing.reclassify(self.reclass_geom, NLCD_PATH,
                                             reclass)
        self.assertFalse(np.any(new_layer == 11))
        self.assertFalse(np.any(new_layer == 21))

        orig_counts = geoprocessing.count(self.reclass_geom, NLCD_PATH)[1]
        new_counts = geoprocessing.masked_array_count(new_layer)[1]

        self.assertEqual(orig_counts['11'], new_counts['100'])
        self.assertEqual(orig_counts['21'], new_counts['200'])

    def test_range_reclass(self):
        """
        Tests a single reclass definition representing a range of values
        to reclass to the same value
        """
        reclass = [((22, 24), 200)]
        new_layer = geoprocessing.reclassify(self.reclass_geom,
                                             NLCD_PATH, reclass)

        # An inclusive range of values, present in the test data, should not
        # exist after reclassification
        self.assertFalse(np.any(new_layer == 22))
        self.assertFalse(np.any(new_layer == 23))
        self.assertFalse(np.any(new_layer == 24))

        orig_counts = geoprocessing.count(self.reclass_geom, NLCD_PATH)[1]
        old_count = orig_counts['22'] + orig_counts['23'] + orig_counts['24']

        new_count = geoprocessing.masked_array_count(new_layer)[1]['200']

        self.assertEqual(old_count, new_count)


class StatisticsTests(unittest.TestCase):
    """
    The statistics method is a shim over direct numpy methods and
    is therefore not extensively tested.  These tests should ensure
    that the method is proxying the right calls and generally working
    """
    stats_geom = Polygon([
            [1747260.99651947943493724, 2071928.23170474520884454],
            [1747260.99651947943493724, 2071884.15942327585071325],
            [1747323.9569215786177665, 2071882.06074320594780147],
            [1747321.85824150871485472, 2071927.53214472183026373],
            [1747260.99651947943493724, 2071928.23170474520884454]])

    geom_data = [11, 23, 24]

    def test_mean(self):
        """
        Test that the statitistics method returns the right value for mean
        """
        mean = geoprocessing.statistics(self.stats_geom, NLCD_PATH, 'mean')
        self.assertEqual(mean, sum(self.geom_data)/len(self.geom_data))

    def test_min(self):
        """
        Test that the statitistics method returns the right value for min
        """
        min_val = geoprocessing.statistics(self.stats_geom, NLCD_PATH, 'min')
        self.assertEqual(min_val, min(self.geom_data))

    def test_not_implmented(self):
        """
        Tests that unimplemented stats operations raise
        """
        self.assertRaises(Exception, geoprocessing.statistics,
                          self.stats_geom, NLCD_PATH, 'foo')


class ImageTests(unittest.TestCase):
    def test_decimated_read(self):
        """
        Test that a bounding box of greater than 256x256 is decimated to that
        shape on read
        """
        tile_src = box(1582986.11448, 2088466.53022,
                       1611281.91831, 2062319.77478)
        tile, _ = geo_utils.tile_read(tile_src, NLCD_LARGE)
        self.assertEqual(tile.shape, (256, 256))

    def test_color_palette(self):
        """
        Test that a raster source ColorTable is converted to an RGB array
        """
        colormap = {
            0: (100, 100, 100, 255),
            99: (45, 45, 45, 255),
            255: (75, 75, 75, 255)
        }

        class mock_reader():
            def colormap(self, _):
                return colormap

        palette = geo_utils.color_table_to_palette(mock_reader())

        # Test the the indexs of the palette match value + 3 (R,G & B)
        self.assertItemsEqual(palette[0:3], colormap[0][0:3])
        self.assertItemsEqual(palette[297:300], colormap[99][0:3])
        self.assertItemsEqual(palette[765:768], colormap[255][0:3])


class S3Tests(unittest.TestCase):
    def setUp(self):
        self.url = 's3://simple-raster-processing/nlcd_512_lzw_tiled.tif'
        self.geom = Polygon([
            [1747260.99651947943493724, 2071928.23170474520884454],
            [1747260.99651947943493724, 2071884.15942327585071325],
            [1747323.9569215786177665, 2071882.06074320594780147],
            [1747321.85824150871485472, 2071927.53214472183026373],
            [1747260.99651947943493724, 2071928.23170474520884454]])


    def test_read_count(self):
        """Test a small byte offset raster read using vsicurl s3 url"""

        _, s3_counts = geoprocessing.count(self.geom, self.url)
        _, disk_counts = geoprocessing.count(self.geom, NLCD_PATH)

        self.assertDictEqual(s3_counts, disk_counts,
                             "Reading the same offset from a local and s3 " +
                             "file did not produce equivalent results")


if __name__ == '__main__':
    unittest.main()
