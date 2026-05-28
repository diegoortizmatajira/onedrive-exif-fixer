import argparse
import logging
from pathlib import Path
from typing import Iterable

from config import DEFAULT_CONFIG_PATH, load_config
from date_parsing import DateParser
from exiftool_service import ExifToolError, ExifToolService
from processor import FileProcessor
from reporting import CsvReporter


def main(argv: list[str] | None = None) -> int:
    """Run the EXIF fixer CLI.

    Parameters
    ----------
    argv
        Optional list of CLI arguments for testing.

    Returns
    -------
    int
        Process exit code.
    """

    parser = _build_parser()
    args = parser.parse_args(argv)
    _configure_logging()

    try:
        config = load_config(Path(args.config))
    except (FileNotFoundError, ValueError) as exc:
        logging.error("Config error: %s", exc)
        return 2

    date_parser = DateParser(config.date_formats)
    exiftool = ExifToolService(date_parser)
    processor = FileProcessor(exiftool, date_parser)

    try:
        files = list(_discover_files(Path(args.path)))
    except FileNotFoundError as exc:
        logging.error("%s", exc)
        return 2

    if not files:
        logging.error("No files found to process at %s.", args.path)
        return 2

    report_path = Path(args.report) if args.report else Path("dry-run-report.csv")
    if args.dry_run:
        with CsvReporter(report_path) as reporter:
            _process_files(
                files, processor, exiftool, args.overwrite_original, reporter
            )
    else:
        _process_files(files, processor, exiftool, args.overwrite_original, None)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fix or create EXIF taken dates for OneDrive uploads."
    )
    parser.add_argument("path", help="File or directory to process.")
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG_PATH),
        help=f"Path to configuration JSON (default: {DEFAULT_CONFIG_PATH}).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not modify files; output a CSV report.",
    )
    parser.add_argument("--report", help="CSV output path for dry-run mode.")
    parser.add_argument(
        "--overwrite-original",
        action="store_true",
        help="Overwrite files in-place instead of creating exiftool backups.",
    )
    return parser


def _configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def _discover_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return
    if not path.exists():
        raise FileNotFoundError(f"Target path not found: {path}")
    if path.is_dir():
        yield from (child for child in path.rglob("*") if child.is_file())


def _process_files(
    files: Iterable[Path],
    processor: FileProcessor,
    exiftool: ExifToolService,
    overwrite_original: bool,
    reporter: CsvReporter | None,
) -> None:
    for file_path in files:
        try:
            decision = processor.decide(file_path)
        except ExifToolError as exc:
            logging.error("Exiftool error for %s: %s", file_path, exc)
            continue

        if reporter is not None:
            reporter.write_decision(decision)
            continue

        if decision.candidate is None:
            logging.warning("No candidate date found for %s.", file_path)
            continue
        if not decision.should_update:
            logging.info("Skipping %s (taken date already present).", file_path)
            continue

        exiftool.write_all_dates(
            file_path, decision.candidate.value, overwrite_original
        )
        logging.info("Updated %s using %s.", file_path, decision.candidate.source.value)


if __name__ == "__main__":
    exit(main())
