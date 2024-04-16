import unittest
from datetime import datetime, timedelta, timezone
from harvest.templating import filters


class TestFilters(unittest.TestCase):
    def test_list_filters(self):
        filter_methods = filters.list_filters()
        self.assertIsInstance(filter_methods, dict)
        self.assertIn('datetime_ago', filter_methods)
        self.assertIn('datetime_in', filter_methods)

    def test_parse_datetime(self):
        date_str = '2022-01-01T00:00:00'
        date_obj = datetime(2022, 1, 1, tzinfo=timezone.utc)
        self.assertEqual(filters.parse_datetime(date_str), date_obj)
        self.assertEqual(filters.parse_datetime(date_obj), date_obj)
        self.assertIsNone(filters.parse_datetime('invalid date'))

    def test_filter_datetime_ago(self):
        reference_date = datetime(2022, 1, 1, tzinfo=timezone.utc)
        expected_date = datetime(2021, 12, 31, tzinfo=timezone.utc)
        self.assertEqual(filters.filter_datetime_ago(reference_date, days=1), expected_date)
        self.assertEqual(filters.filter_datetime_ago(reference_date.isoformat(), days=1), expected_date)
        self.assertEqual(filters.filter_datetime_ago(reference_date, result_as_string=True, days=1), expected_date.isoformat())

    def test_filter_datetime_in(self):
        reference_date = datetime(2022, 1, 1, tzinfo=timezone.utc)
        expected_date = datetime(2022, 1, 2, tzinfo=timezone.utc)
        self.assertEqual(filters.filter_datetime_in(reference_date, days=1), expected_date)
        self.assertEqual(filters.filter_datetime_in(reference_date.isoformat(), days=1), expected_date)
        self.assertEqual(filters.filter_datetime_in(reference_date, result_as_string=True, days=1), expected_date.isoformat())


if __name__ == '__main__':
    unittest.main()
