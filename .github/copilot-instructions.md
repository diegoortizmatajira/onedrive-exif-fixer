# Copilot instructions

## Project overview

- Fix or create EXIF "taken" dates for OneDrive-uploaded photos and videos.
- Tech stack: Python, uv, and exiftool (external EXIF reader/writer).
- Support dry-run mode that does not modify files and outputs a CSV report.

## Build, test, lint

- Run tests: `python -m unittest discover -s tests -p "test_*.py"`
- Run a single test:
  `python -m unittest tests.test_date_parsing.DateParsingTests.test_parse_exact_exif_date`

## Architecture (big picture)

- Process files by reading existing EXIF and filesystem timestamps, then choose
  the "taken" date in this priority order: oldest EXIF date, original creation
  date, modified date, date in filename, date in parent folder name.
- Exiftool integration is wrapped in a Service class so it can be mocked in unit
  tests.
- A configuration file defines recognized date formats and customization.
- Dry-run mode outputs a CSV with: file path, current "taken" value, source of
  the new value, new value, and the format used to identify it.
- If only year and month are available, use the first day of that month.

## Key conventions

- Keep components modular and aligned with KISS.
- All components require unit tests.
- Use type annotations throughout the codebase.
