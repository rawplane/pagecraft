"""Command-line interface for pagecraft."""

import argparse
import sys

from pagecraft.discovery import get_input_files
from pagecraft.logging_config import EXIT_NO_INPUT, setup_logging
from pagecraft.merge import create_pdf


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert images and HTML files to PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s image.jpg -o output.pdf
  %(prog)s img1.jpg img2.png img3.webp -o merged.pdf
  %(prog)s /path/to/images -o all_images.pdf
  %(prog)s image.jpg --size a4 -o document.pdf
  %(prog)s images/ --sort-by modified -o sorted.pdf
  %(prog)s page.html -o document.pdf
  %(prog)s cover.html img1.jpg chapter2.html -o mixed.pdf
  %(prog)s ./mixed-content/ -o all.pdf
  %(prog)s images/ -o out.pdf -j 4   # use 4 parallel jobs

Exit codes:
  0  success
  1  no valid input files found
  2  some files failed (partial success)
  3  all files failed, or output write error
        """,
    )
    parser.add_argument(
        "input",
        nargs="+",
        help="Input image/HTML file(s) or directory containing images and HTML files",
    )
    parser.add_argument(
        "-o", "--output", required=True, help="Output PDF file path"
    )
    parser.add_argument(
        "--size",
        choices=["auto", "a4", "letter"],
        default="auto",
        help="Page size: auto (original), a4, or letter (default: auto)",
    )
    parser.add_argument(
        "--sort-by",
        choices=["name", "created", "modified"],
        default="name",
        help="Sort inputs by: name (alphanumeric), created (creation time), modified (default: name)",
    )
    parser.add_argument(
        "-j",
        "--jobs",
        type=int,
        default=None,
        help="Number of parallel conversion jobs (default: CPU count)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output (warnings still go to stderr)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show debug-level output (per-file details)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    setup_logging(quiet=args.quiet, verbose=args.verbose)

    input_files = get_input_files(args.input, args.sort_by)

    if not input_files:
        from pagecraft.logging_config import logger

        logger.error("No valid image or HTML files found")
        sys.exit(EXIT_NO_INPUT)

    exit_code = create_pdf(
        input_files,
        args.output,
        args.size,
        jobs=args.jobs,
        quiet=args.quiet,
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
