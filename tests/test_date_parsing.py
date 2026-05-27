from __future__ import annotations

import unittest
from datetime import datetime

from onedrive_exif_fixer.date_parsing import DateParser


class DateParsingTests(unittest.TestCase):
    def test_parse_exact_exif_date(self) -> None:
        parser = DateParser(["%Y:%m:%d %H:%M:%S"])
        parsed = parser.parse_exact("2020:01:02 03:04:05")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.value, datetime(2020, 1, 2, 3, 4, 5))

    def test_find_in_text(self) -> None:
        parser = DateParser(["%Y%m%d_%H%M%S"])
        parsed = parser.find_in_text("IMG_20240503_121314.JPG")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.value, datetime(2024, 5, 3, 12, 13, 14))

    def test_year_month_defaults_day(self) -> None:
        parser = DateParser(["%Y-%m"])
        parsed = parser.parse_exact("2024-05")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.value, datetime(2024, 5, 1))


if __name__ == "__main__":
    unittest.main()
