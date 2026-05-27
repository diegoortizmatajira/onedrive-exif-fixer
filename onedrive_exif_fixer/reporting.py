from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TextIO

from .processor import DateSource, FileDecision

_OUTPUT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass
class CsvReporter:
    """Write dry-run reports for processed files.

    Parameters
    ----------
    path
        Destination CSV path.
    """

    path: Path
    _handle: TextIO | None = None
    _writer: csv.DictWriter | None = None

    def __enter__(self) -> CsvReporter:
        self._handle = self.path.open("w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(
            self._handle,
            fieldnames=[
                "image_file_path",
                "current_taken",
                "new_value_source",
                "new_value",
                "format_used",
            ],
        )
        self._writer.writeheader()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        if self._handle is not None:
            self._handle.close()

    def write_decision(self, decision: FileDecision) -> None:
        """Write a single file decision to the CSV.

        Parameters
        ----------
        decision
            The file decision to write.
        """

        if self._writer is None:
            raise RuntimeError("CsvReporter is not initialized. Use within a context manager.")
        current_taken = _format_datetime(decision.current_taken.value) if decision.current_taken else ""
        if decision.candidate is None:
            source = DateSource.NOT_FOUND.value
            new_value = ""
            format_used = ""
        else:
            source = decision.candidate.source.value
            new_value = _format_datetime(decision.candidate.value)
            format_used = decision.candidate.format_used
        self._writer.writerow(
            {
                "image_file_path": str(decision.file_path),
                "current_taken": current_taken,
                "new_value_source": source,
                "new_value": new_value,
                "format_used": format_used,
            }
        )


def _format_datetime(value: datetime) -> str:
    return value.strftime(_OUTPUT_DATE_FORMAT)
