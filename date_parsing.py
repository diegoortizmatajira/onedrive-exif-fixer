from dataclasses import dataclass
from datetime import datetime, timezone
import re
from typing import Iterable

_DIRECTIVE_TO_REGEX = {
    "Y": r"\d{4}",
    "y": r"\d{2}",
    "m": r"\d{2}",
    "d": r"\d{2}",
    "H": r"\d{2}",
    "M": r"\d{2}",
    "S": r"\d{2}",
    "f": r"\d{1,6}",
    "z": r"[+-]\d{2}:?\d{2}",
}


@dataclass(frozen=True)
class ParsedDate:
    """Parsed date value with format metadata.

    Parameters
    ----------
    value
        Parsed datetime value normalized to a naive UTC representation if
        timezone information is present.
    format_used
        The datetime format string that produced the value.
    matched_text
        The input text segment that matched the format.
    """

    value: datetime
    format_used: str
    matched_text: str


class DateParser:
    """Parse dates from exact values or text using configured formats.

    Parameters
    ----------
    formats
        Iterable of strptime-compatible formats to use for parsing.
    """

    def __init__(self, formats: Iterable[str]) -> None:
        self._formats = tuple(formats)
        if not self._formats:
            raise ValueError("At least one date format is required.")
        self._format_regexes = {fmt: re.compile(_format_to_regex(fmt)) for fmt in self._formats}

    @property
    def formats(self) -> tuple[str, ...]:
        """Return the configured date formats."""

        return self._formats

    def parse_exact(self, value: str) -> ParsedDate | None:
        """Parse a date when the full value is expected to match a format.

        Parameters
        ----------
        value
            The exact text representation of the date.

        Returns
        -------
        ParsedDate | None
            Parsed date metadata or None when no formats match.
        """

        for fmt in self._formats:
            parsed = _try_parse_exact(value, fmt)
            if parsed is not None:
                return ParsedDate(parsed, fmt, value)
        return None

    def find_in_text(self, text: str) -> ParsedDate | None:
        """Find and parse the first matching date substring in text.

        Parameters
        ----------
        text
            Input text that may contain an embedded date.

        Returns
        -------
        ParsedDate | None
            Parsed date metadata or None when no matches are found.
        """

        for fmt in self._formats:
            regex = self._format_regexes[fmt]
            match = regex.search(text)
            if match is None:
                continue
            matched_text = match.group(0)
            parsed = _try_parse_exact(matched_text, fmt)
            if parsed is not None:
                return ParsedDate(parsed, fmt, matched_text)
        return None


def _try_parse_exact(value: str, fmt: str) -> datetime | None:
    try:
        parsed = datetime.strptime(value, fmt)
    except ValueError:
        return None
    return _normalize_datetime(parsed)


def _normalize_datetime(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _format_to_regex(fmt: str) -> str:
    regex_parts: list[str] = []
    index = 0
    while index < len(fmt):
        char = fmt[index]
        if char == "%":
            if index + 1 >= len(fmt):
                raise ValueError(f"Invalid datetime format: {fmt}")
            directive = fmt[index + 1]
            if directive not in _DIRECTIVE_TO_REGEX:
                raise ValueError(f"Unsupported datetime directive: %{directive}")
            regex_parts.append(_DIRECTIVE_TO_REGEX[directive])
            index += 2
            continue
        regex_parts.append(re.escape(char))
        index += 1
    return "".join(regex_parts)
