# OneDrive EXIF data fixed

## Scope

- Be able to fix or create EXIF data for OneDrive uploaded pictures and videos.
- If actual "taken" date is missing, then use the following in order:
  1. Oldest date in existing EXIF date (if any)
  2. Original Creation Date from the file
  3. Modified Date from the file
  4. Date in filename if available
  5. Date in parent folder name if available
- Have a configuration file for customization.
- App should support Dry-run scenarios to test the process without affecting the
  actual files, instead it must produce a CSV file, with details about:
  - Image file path
  - Current value for "taken"
  - Source for the found new value
  - New value to be used
  - Format used to identify the value.

## Configuration

- List of recognized date formats

## Tech stack

- Python
- UV
- Exiftool (as external EXIT reader/writer)

## Architecture

- Architecture must be modular and each component must respect KISS principles.
- External tools like Exiftool should be wrapped in a Service class (that can be
  mocked for unit test)
- There should be unit tests for all components.
- Code must always use data type annotations

## Border cases

- If there is no day value available, but there is year and month, use the first
  day of that month.
