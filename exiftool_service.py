from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import subprocess
from typing import Iterable

from date_parsing import DateParser, ParsedDate

_TAKEN_TAGS: tuple[str, ...] = ("DateTimeOriginal", "SubSecDateTimeOriginal")


class ExifToolError(RuntimeError):
    """Raised when exiftool operations fail."""


@dataclass(frozen=True)
class ExifMetadata:
    """Parsed EXIF metadata dates.

    Parameters
    ----------
    taken
        The current "taken" date if present.
    other_dates
        Other available EXIF date values.
    """

    taken: ParsedDate | None
    other_dates: tuple[ParsedDate, ...]


class ExifToolService:
    """Wrap exiftool command usage for reading and writing dates.

    Parameters
    ----------
    parser
        Date parser used to interpret EXIF timestamps.
    exiftool_path
        Path or command name for the exiftool binary.
    timeout_seconds
        Max seconds to wait for exiftool commands.
    """

    def __init__(
        self,
        parser: DateParser,
        exiftool_path: str = "exiftool",
        timeout_seconds: int = 30,
    ) -> None:
        self._parser = parser
        self._exiftool_path = exiftool_path
        self._timeout_seconds = timeout_seconds

    def read_metadata(self, file_path: Path) -> ExifMetadata:
        """Read EXIF dates from a file.

        Parameters
        ----------
        file_path
            Path to the file to inspect.

        Returns
        -------
        ExifMetadata
            Parsed metadata including the current taken date.
        """

        output = self._run(["-j", "-time:all", str(file_path)])
        try:
            payload = json.loads(output)
        except json.JSONDecodeError as exc:
            raise ExifToolError(f"Failed to parse exiftool JSON output: {exc}") from exc
        if not payload or not isinstance(payload[0], dict):
            raise ExifToolError("Exiftool returned no metadata.")
        metadata = payload[0]
        taken = self._extract_taken(metadata)
        other_dates = self._extract_other_dates(metadata, taken)
        return ExifMetadata(taken=taken, other_dates=tuple(other_dates))

    def write_all_dates(
        self, file_path: Path, date_value: datetime, overwrite_original: bool
    ) -> None:
        """Write the provided datetime to all EXIF date fields.

        Parameters
        ----------
        file_path
            Path to the target file.
        date_value
            Datetime to write.
        overwrite_original
            Whether to overwrite in-place without creating backup copies.
        """

        formatted = date_value.strftime("%Y:%m:%d %H:%M:%S")
        args = [f"-AllDates={formatted}"]
        if overwrite_original:
            args.append("-overwrite_original")
        args.append(str(file_path))
        self._run(args)

    def _run(self, args: Iterable[str]) -> str:
        command = [self._exiftool_path, *args]
        try:
            completed = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                timeout=self._timeout_seconds,
            )
        except FileNotFoundError as exc:
            raise ExifToolError(
                f"Exiftool not found at '{self._exiftool_path}'. Ensure it is installed and on PATH."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise ExifToolError(f"Exiftool command timed out for {args}.") from exc
        except subprocess.CalledProcessError as exc:
            raise ExifToolError(
                f"Exiftool command failed: {exc.stderr.strip()}"
            ) from exc
        return completed.stdout

    def _extract_taken(self, metadata: dict[str, object]) -> ParsedDate | None:
        for tag in _TAKEN_TAGS:
            raw_value = metadata.get(tag)
            if not isinstance(raw_value, str):
                continue
            parsed = self._parser.parse_exact(raw_value)
            if parsed is not None:
                return parsed
        return None

    def _extract_other_dates(
        self, metadata: dict[str, object], taken: ParsedDate | None
    ) -> list[ParsedDate]:
        other_dates: list[ParsedDate] = []
        for tag, raw_value in metadata.items():
            if tag == "SourceFile" or tag in _TAKEN_TAGS:
                continue
            if not isinstance(raw_value, str):
                continue
            parsed = self._parser.parse_exact(raw_value)
            if parsed is not None:
                if taken is not None and parsed.value == taken.value:
                    continue
                other_dates.append(parsed)
        return other_dates
