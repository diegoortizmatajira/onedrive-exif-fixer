"""Unit tests for the FileProcessor class in the onedrive_exif_fixer module."""

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

from onedrive_exif_fixer.date_parsing import DateParser, ParsedDate
from onedrive_exif_fixer.exiftool_service import ExifMetadata
from onedrive_exif_fixer.processor import DateSource, FileProcessor


class FakeExifTool:
    """
    A mock implementation of an ExifTool service for testing purposes.

    This class simulates the behavior of the ExifTool service to provide
    controlled testing scenarios without actual file operations.

    Attributes:
        _metadata (ExifMetadata): The metadata to be used for simulating
                                  ExifTool read operations.
    """

    def __init__(self, metadata: ExifMetadata) -> None:
        """
        Initialize the FakeExifTool with specific metadata.

        Args:
            metadata (ExifMetadata): The metadata that will be returned by
                                     the read_metadata method.
        """
        self._metadata = metadata

    def read_metadata(self, file_path: Path) -> ExifMetadata:
        """
        Simulate reading the metadata of a file.

        Args:
            file_path (Path): The path of the file whose metadata is being read.

        Returns:
            ExifMetadata: The predefined metadata for testing.
        """
        return self._metadata

    def write_all_dates(
        self, file_path: Path, date_value: datetime, overwrite_original: bool
    ) -> None:
        """
        Simulate writing all date values to a file.

        This method raises an error to ensure it is not called in selection tests.

        Args:
            file_path (Path): The path of the file to write dates to.
            date_value (datetime): The date value to be written.
            overwrite_original (bool): Whether to overwrite the original file.

        Raises:
            AssertionError: Always raised to indicate this method should not be
                            invoked during selection tests.
        """
        raise AssertionError("write_all_dates should not be called in selection tests.")


def test_existing_taken_date_is_preserved() -> None:
    """
    Test that an existing 'taken' date in the metadata is preserved.

    This unit test ensures that when a photo already has a 'taken' date in its metadata,
    the FileProcessor does not modify or update it. The decision logic confirms that
    processing is not required and identifies the existing date as the source.
    """
    taken = ParsedDate(
        value=datetime(2021, 1, 2, 3, 4, 5),
        format_used="%Y:%m:%d %H:%M:%S",
        matched_text="2021:01:02 03:04:05",
    )
    exiftool = FakeExifTool(ExifMetadata(taken=taken, other_dates=()))
    processor = FileProcessor(exiftool, DateParser(["%Y:%m:%d %H:%M:%S"]))
    decision = processor.decide(Path("image.jpg"))

    assert not decision.should_update
    assert decision.candidate is not None
    assert decision.candidate.source == DateSource.EXISTING


def test_oldest_exif_date_selected() -> None:
    """
    Test that the oldest EXIF date is selected.

    This unit test ensures that when multiple EXIF dates are available,
    the FileProcessor selects the oldest date as the candidate for the
    'taken' date value. The decision logic confirms that processing is
    required and identifies the oldest date as the source.
    """
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

    assert decision.should_update
    assert decision.candidate is not None
    assert decision.candidate.source == DateSource.EXIF_OLDEST
    assert decision.candidate.value == older.value


def test_filesystem_creation_used_when_no_exif_dates() -> None:
    """
    Test that file system creation date is used when no EXIF dates are available.

    This unit test verifies that when there are no EXIF dates available in the metadata,
    the FileProcessor falls back to using the file system creation timestamp as the
    candidate 'taken' date.
    """
    exiftool = FakeExifTool(ExifMetadata(taken=None, other_dates=()))
    parser = DateParser(["%Y:%m:%d %H:%M:%S"])
    fake_stat = SimpleNamespace(st_birthtime=1_000_000_000, st_ctime=0, st_mtime=0)
    processor = FileProcessor(
        exiftool,
        parser,
        stat_provider=lambda _: fake_stat,  # pyright: ignore[reportArgumentType]
    )
    decision = processor.decide(Path("image.jpg"))

    assert decision.should_update
    assert decision.candidate is not None
    assert decision.candidate.source == DateSource.FILE_CREATION
