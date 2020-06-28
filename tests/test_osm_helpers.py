import unittest
import osm_helpers


class TestDeg2XY(unittest.TestCase):
    def setUp(self) -> None:
        self.zoom_9 = 9
        self.zoom_13 = 13
        self.lat = 50.7742
        self.lon = 6.0745

    def test_x_y_conversion_9(self):
        x_9, y_9 = osm_helpers.deg2xy(self.lat, self.lon, self.zoom_9)
        self.assertAlmostEqual(x_9, 264.639288888888, places=8)
        self.assertAlmostEqual(y_9, 171.915145811798, places=8)

    def test_x_y_conversion_13(self):
        x_13, y_13 = osm_helpers.deg2xy(self.lat, self.lon, self.zoom_13)
        self.assertAlmostEqual(x_13, 4234.228622222222, places=8)
        self.assertAlmostEqual(y_13, 2750.642332988770, places=8)

    def test_x_y_num_conversion_9(self):
        x_9, y_9 = osm_helpers.deg2tile_coord(self.lat, self.lon, self.zoom_9)
        self.assertEqual((x_9, y_9), (264, 171))

    def test_x_y_num_conversion_13(self):
        x_13, y_13 = osm_helpers.deg2tile_coord(self.lat, self.lon, self.zoom_13)
        self.assertEqual((x_13, y_13), (4234, 2750))


class TestTileLoad(unittest.TestCase):
    def setUp(self) -> None:
        self.tile_url = 'https://maps.wikimedia.org/osm-intl/13/4234/2750.png'
        self.x = 4234
        self.y = 2750
        self.zoom = 13

    def test_tile_url(self):
        url = osm_helpers.get_tile_url(self.x, self.y, self.zoom)
        self.assertEqual(url, self.tile_url)


if __name__ == '__main__':
    unittest.main()
