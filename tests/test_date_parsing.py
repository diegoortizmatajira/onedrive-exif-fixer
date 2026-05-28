"""Unit tests for the DateParser class in onedrive_exif_fixer.date_parsing."""

from datetime import datetime

from onedrive_exif_fixer.date_parsing import DateParser


def test_parse_exact_exif_date() -> None:
    """
    Test the DateParser's ability to parse an exact EXIF date string.

    Uses the date format "%Y:%m:%d %H:%M:%S" and the exact date string
    "2020:01:02 03:04:05". Ensures that the resulting datetime value is
    correctly set to January 2nd, 2020, 03:04:05.
    """
    parser = DateParser(["%Y:%m:%d %H:%M:%S"])
    parsed = parser.parse_exact("2020:01:02 03:04:05")
    assert parsed is not None
    assert parsed.value == datetime(2020, 1, 2, 3, 4, 5)


def test_find_in_text() -> None:
    """
    Test the DateParser's ability to find and parse a date embedded within a text string.

    Uses the date format "%Y%m%d_%H%M%S" and the filename "IMG_20240503_121314.JPG".
    Ensures that the extracted date is correctly parsed as May 3rd, 2024, 12:13:14.
    """
    parser = DateParser(["%Y%m%d_%H%M%S"])
    parsed = parser.find_in_text("IMG_20240503_121314.JPG")
    assert parsed is not None
    assert parsed.value == datetime(2024, 5, 3, 12, 13, 14)


def test_year_month_defaults_day() -> None:
    """
    Test that parsing a date string with only year and month defaults to the
    first day of that month.

    Uses the DateParser class with the date format "%Y-%m" to parse the date string "2024-05".
    Ensures that the resulting date is correctly set to May 1st, 2024.
    """
    parser = DateParser(["%Y-%m"])
    parsed = parser.parse_exact("2024-05")
    assert parsed is not None
    assert parsed.value == datetime(2024, 5, 1)
