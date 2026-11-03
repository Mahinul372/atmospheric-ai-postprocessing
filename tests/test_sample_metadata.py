import unittest
from datetime import datetime, timedelta, timezone

from src.sample_validation import hrrr_window, periods_match, previous_hour_window


class AccumulationAlignmentTests(unittest.TestCase):
    def test_hrrr_f01_window_is_initialization_to_one_hour(self):
        metadata = {"dataDate": 20240501, "dataTime": 1200, "startStep": 0, "endStep": 1}
        start, end = hrrr_window(metadata)
        self.assertEqual(start, datetime(2024, 5, 1, 12, tzinfo=timezone.utc))
        self.assertEqual(end, datetime(2024, 5, 1, 13, tzinfo=timezone.utc))

    def test_mrms_hourly_product_window_is_previous_hour(self):
        valid = datetime(2024, 5, 1, 13, tzinfo=timezone.utc)
        start, end = previous_hour_window(valid)
        self.assertEqual(start, datetime(2024, 5, 1, 12, tzinfo=timezone.utc))
        self.assertEqual(end, valid)

    def test_equal_windows_match(self):
        start = datetime(2024, 5, 1, 12, tzinfo=timezone.utc)
        end = start + timedelta(hours=1)
        self.assertTrue(periods_match(start, end, start, end))

    def test_shifted_observation_window_does_not_match(self):
        start = datetime(2024, 5, 1, 12, tzinfo=timezone.utc)
        end = start + timedelta(hours=1)
        self.assertFalse(periods_match(start, end, start - timedelta(hours=1), start))


if __name__ == "__main__":
    unittest.main()
