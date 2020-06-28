import unittest

import strava_local_heatmap


class TestMonthExtraction(unittest.TestCase):
    def test_simple_range(self):
        start, stop = strava_local_heatmap.extract_start_stop_from_month('1-12')
        self.assertEqual((start, stop), (1, 13))

    def test_shorter_range(self):
        start, stop = strava_local_heatmap.extract_start_stop_from_month('3-9')
        self.assertEqual((start, stop), (3, 10))

    def test_lower_out_of_range(self):
        start, stop = strava_local_heatmap.extract_start_stop_from_month('0-12')
        self.assertEqual((start, stop), (1, 13))

    def test_upper_out_of_range(self):
        start, stop = strava_local_heatmap.extract_start_stop_from_month('1-13')
        self.assertEqual((start, stop), (1, 13))

    def test_both_out_of_ranage(self):
        start, stop = strava_local_heatmap.extract_start_stop_from_month('0-13')
        self.assertEqual((start, stop), (1, 13))

    def test_wrong_order(self):
        start, stop = strava_local_heatmap.extract_start_stop_from_month('12-1')
        self.assertEqual((start, stop), (1, 13))

    def test_wrong_order_lower_out_of_range(self):
        start, stop = strava_local_heatmap.extract_start_stop_from_month('12-0')
        self.assertEqual((start, stop), (1, 13))

    def test_wrong_order_upper_out_of_range(self):
        start, stop = strava_local_heatmap.extract_start_stop_from_month('13-1')
        self.assertEqual((start, stop), (1, 13))

    def test_wrong_format(self):
        start, stop = strava_local_heatmap.extract_start_stop_from_month('1-')
        self.assertEqual((start, stop), (1, 13))


if __name__ == '__main__':
    unittest.main()
