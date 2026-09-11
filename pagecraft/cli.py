"""Command-line interface for pagecraft."""

import argparse
import sys

from pagecraft.discovery import get_input_files
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
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    input_files = get_input_files(args.input, args.sort_by)

    if not input_files:
        print("Error: No valid image or HTML files found", file=sys.stderr)
        sys.exit(1)

    create_pdf(input_files, args.output, args.size)


if __name__ == "__main__":
    main()
