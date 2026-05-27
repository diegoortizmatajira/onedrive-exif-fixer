from __future__ import annotations

from datetime import datetime

from onedrive_exif_fixer.date_parsing import DateParser


def test_parse_exact_exif_date() -> None:
    parser = DateParser(["%Y:%m:%d %H:%M:%S"])
    parsed = parser.parse_exact("2020:01:02 03:04:05")
    assert parsed is not None
    assert parsed.value == datetime(2020, 1, 2, 3, 4, 5)


def test_find_in_text() -> None:
    parser = DateParser(["%Y%m%d_%H%M%S"])
    parsed = parser.find_in_text("IMG_20240503_121314.JPG")
    assert parsed is not None
    assert parsed.value == datetime(2024, 5, 3, 12, 13, 14)


def test_year_month_defaults_day() -> None:
    parser = DateParser(["%Y-%m"])
    parsed = parser.parse_exact("2024-05")
    assert parsed is not None
    assert parsed.value == datetime(2024, 5, 1)
