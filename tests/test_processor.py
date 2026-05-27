from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace
import unittest
from pathlib import Path

from onedrive_exif_fixer.date_parsing import DateParser, ParsedDate
from onedrive_exif_fixer.exiftool_service import ExifMetadata
from onedrive_exif_fixer.processor import DateSource, FileProcessor


class FakeExifTool:
    def __init__(self, metadata: ExifMetadata) -> None:
        self._metadata = metadata

    def read_metadata(self, file_path: Path) -> ExifMetadata:
        return self._metadata

    def write_all_dates(self, file_path: Path, date_value: datetime, overwrite_original: bool) -> None:
        raise AssertionError("write_all_dates should not be called in selection tests.")


class FileProcessorTests(unittest.TestCase):
    def test_existing_taken_date_is_preserved(self) -> None:
        taken = ParsedDate(
            value=datetime(2021, 1, 2, 3, 4, 5),
            format_used="%Y:%m:%d %H:%M:%S",
            matched_text="2021:01:02 03:04:05",
        )
        exiftool = FakeExifTool(ExifMetadata(taken=taken, other_dates=()))
        processor = FileProcessor(exiftool, DateParser(["%Y:%m:%d %H:%M:%S"]))
        decision = processor.decide(Path("image.jpg"))

        self.assertFalse(decision.should_update)
        self.assertEqual(decision.candidate.source, DateSource.EXISTING)

    def test_oldest_exif_date_selected(self) -> None:
        older = ParsedDate(
            value=datetime(2020, 1, 1, 0, 0, 0),
            format_used="%Y:%m:%d %H:%M:%S",
            matched_text="2020:01:01 00:00:00",
        )
        newer = ParsedDate(
            value=datetime(2021, 1, 1, 0, 0, 0),
            format_used="%Y:%m:%d %H:%M:%S",
            matched_text="2021:01:01 00:00:00",
        )
        exiftool = FakeExifTool(ExifMetadata(taken=None, other_dates=(newer, older)))
        processor = FileProcessor(exiftool, DateParser(["%Y:%m:%d %H:%M:%S"]))
        decision = processor.decide(Path("image.jpg"))

        self.assertTrue(decision.should_update)
        self.assertEqual(decision.candidate.source, DateSource.EXIF_OLDEST)
        self.assertEqual(decision.candidate.value, older.value)

    def test_filesystem_creation_used_when_no_exif_dates(self) -> None:
        exiftool = FakeExifTool(ExifMetadata(taken=None, other_dates=()))
        parser = DateParser(["%Y:%m:%d %H:%M:%S"])
        fake_stat = SimpleNamespace(st_birthtime=1_000_000_000, st_ctime=0, st_mtime=0)
        processor = FileProcessor(
            exiftool,
            parser,
            stat_provider=lambda _: fake_stat,
        )
        decision = processor.decide(Path("image.jpg"))

        self.assertTrue(decision.should_update)
        self.assertEqual(decision.candidate.source, DateSource.FILE_CREATION)


if __name__ == "__main__":
    unittest.main()
