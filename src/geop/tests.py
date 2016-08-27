import unittest
import geoprocessing
import numpy as np

from copy import copy
from shapely.geometry import Point, Polygon

NLCD_PATH = '../test_data/philly_nlcd.tif'
NLCD_EDIT_PATH = '../test_data/philly_nlcd_edited.tif'
NLCD_ONES = '../test_data/philly_ones.tif'      # all cells are 1
NLCD_THREES = '../test_data/philly_threes.tif'  # all cells are 3


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


if __name__ == '__main__':
    unittest.main()
