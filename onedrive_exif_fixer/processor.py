from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import os
from pathlib import Path
from typing import Callable, Protocol

from .date_parsing import DateParser, ParsedDate
from .exiftool_service import ExifMetadata


class ExifTool(Protocol):
    """Protocol for EXIF tool operations."""

    def read_metadata(self, file_path: Path) -> ExifMetadata:
        """Read metadata from a file."""

    def write_all_dates(self, file_path: Path, date_value: datetime, overwrite_original: bool) -> None:
        """Write all EXIF date fields to a file."""


class DateSource(str, Enum):
    """Enumerates how a date candidate was chosen."""

    EXISTING = "existing"
    EXIF_OLDEST = "exif_oldest"
    FILE_CREATION = "file_creation"
    FILE_MODIFIED = "file_modified"
    FILENAME = "filename"
    PARENT_FOLDER = "parent_folder"
    NOT_FOUND = "not_found"


@dataclass(frozen=True)
class DateCandidate:
    """Selected candidate date.

    Parameters
    ----------
    value
        Datetime value to apply.
    source
        Source category that produced the value.
    format_used
        Format string or label used to identify the value.
    """

    value: datetime
    source: DateSource
    format_used: str


@dataclass(frozen=True)
class FileDecision:
    """Decision data for a single file.

    Parameters
    ----------
    file_path
        File path being processed.
    current_taken
        Existing taken date if present.
    candidate
        New candidate date and metadata.
    should_update
        Whether to apply the candidate in non-dry-run mode.
    """

    file_path: Path
    current_taken: ParsedDate | None
    candidate: DateCandidate | None
    should_update: bool


class FileProcessor:
    """Determine the taken date for files based on configured priority.

    Parameters
    ----------
    exiftool
        Exif tool service used to read metadata.
    parser
        Date parser used for filename and folder parsing.
    stat_provider
        Optional override for filesystem stat calls to ease testing.
    """

    def __init__(
        self,
        exiftool: ExifTool,
        parser: DateParser,
        stat_provider: Callable[[Path], os.stat_result] | None = None,
    ) -> None:
        self._exiftool = exiftool
        self._parser = parser
        self._stat_provider = stat_provider or Path.stat

    def decide(self, file_path: Path) -> FileDecision:
        """Determine the taken date decision for a file.

        Parameters
        ----------
        file_path
            File to process.

        Returns
        -------
        FileDecision
            The decision including any candidate updates.
        """

        metadata = self._exiftool.read_metadata(file_path)
        if metadata.taken is not None:
            candidate = DateCandidate(
                value=metadata.taken.value,
                source=DateSource.EXISTING,
                format_used=metadata.taken.format_used,
            )
            return FileDecision(
                file_path=file_path,
                current_taken=metadata.taken,
                candidate=candidate,
                should_update=False,
            )

        candidate = self._select_candidate(file_path, metadata)
        return FileDecision(
            file_path=file_path,
            current_taken=metadata.taken,
            candidate=candidate,
            should_update=candidate is not None,
        )

    def _select_candidate(self, file_path: Path, metadata: ExifMetadata) -> DateCandidate | None:
        if metadata.other_dates:
            oldest = min(metadata.other_dates, key=lambda item: item.value)
            return DateCandidate(
                value=oldest.value,
                source=DateSource.EXIF_OLDEST,
                format_used=oldest.format_used,
            )

        creation_time = self._get_creation_time(file_path)
        if creation_time is not None:
            return DateCandidate(
                value=creation_time,
                source=DateSource.FILE_CREATION,
                format_used="filesystem",
            )

        modified_time = self._get_modified_time(file_path)
        if modified_time is not None:
            return DateCandidate(
                value=modified_time,
                source=DateSource.FILE_MODIFIED,
                format_used="filesystem",
            )

        filename_candidate = self._parser.find_in_text(file_path.stem)
        if filename_candidate is not None:
            return DateCandidate(
                value=filename_candidate.value,
                source=DateSource.FILENAME,
                format_used=filename_candidate.format_used,
            )

        parent_candidate = self._parser.find_in_text(file_path.parent.name)
        if parent_candidate is not None:
            return DateCandidate(
                value=parent_candidate.value,
                source=DateSource.PARENT_FOLDER,
                format_used=parent_candidate.format_used,
            )

        return None

    def _get_creation_time(self, file_path: Path) -> datetime | None:
        stat_result = self._stat_provider(file_path)
        birth_time = getattr(stat_result, "st_birthtime", None)
        if birth_time is not None:
            return datetime.fromtimestamp(birth_time)
        if stat_result.st_ctime:
            return datetime.fromtimestamp(stat_result.st_ctime)
        return None

    def _get_modified_time(self, file_path: Path) -> datetime | None:
        stat_result = self._stat_provider(file_path)
        if stat_result.st_mtime:
            return datetime.fromtimestamp(stat_result.st_mtime)
        return None
