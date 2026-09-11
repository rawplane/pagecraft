#!/usr/bin/env python3
"""
Convert images and HTML files to PDF.

HTML rendering uses Playwright + a single reused headless Chromium
instance (instead of spinning up a fresh render engine per file), which
is significantly faster than WeasyPrint for batches of HTML files and
gives much better fidelity for modern CSS (flexbox, grid, etc.).

Setup (one-time):
    pip install playwright img2pdf pillow pypdf tqdm --break-system-packages
    playwright install chromium
"""
import argparse
import io
import sys
from pathlib import Path
from typing import Dict, List, Optional

import img2pdf
from PIL import Image
from pypdf import PdfReader, PdfWriter
from tqdm import tqdm

try:
    from playwright.sync_api import sync_playwright, Error as PlaywrightError
except ImportError:
    print(
        "Error: playwright is not installed. Run:\n"
        "  pip install playwright --break-system-packages\n"
        "  playwright install chromium",
        file=sys.stderr,
    )
    sys.exit(1)

SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
SUPPORTED_HTML_EXTENSIONS = {'.html', '.htm'}
SUPPORTED_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_HTML_EXTENSIONS


def validate_image_file(file_path: Path) -> bool:
    if not file_path.exists():
        print(f"Warning: File not found: {file_path}", file=sys.stderr)
        return False
    if not file_path.is_file():
        print(f"Warning: Not a file: {file_path}", file=sys.stderr)
        return False
    if file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        print(f"Warning: Unsupported file type, skipping: {file_path}", file=sys.stderr)
        return False
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception as e:
        print(f"Warning: Invalid or corrupted image, skipping: {file_path} ({e})", file=sys.stderr)
        return False


def validate_html_file(file_path: Path) -> bool:
    if not file_path.exists():
        print(f"Warning: File not found: {file_path}", file=sys.stderr)
        return False
    if not file_path.is_file():
        print(f"Warning: Not a file: {file_path}", file=sys.stderr)
        return False
    if file_path.suffix.lower() not in SUPPORTED_HTML_EXTENSIONS:
        print(f"Warning: Unsupported file type, skipping: {file_path}", file=sys.stderr)
        return False
    try:
        if file_path.stat().st_size == 0:
            print(f"Warning: Empty HTML file, skipping: {file_path}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"Warning: Cannot access HTML file, skipping: {file_path} ({e})", file=sys.stderr)
        return False


def validate_input_file(file_path: Path) -> bool:
    suffix = file_path.suffix.lower()
    if suffix in SUPPORTED_IMAGE_EXTENSIONS:
        return validate_image_file(file_path)
    if suffix in SUPPORTED_HTML_EXTENSIONS:
        return validate_html_file(file_path)
    print(f"Warning: Unsupported file type, skipping: {file_path}", file=sys.stderr)
    return False


def is_html_file(file_path: Path) -> bool:
    return file_path.suffix.lower() in SUPPORTED_HTML_EXTENSIONS


def get_input_files(input_paths: List[str], sort_by: str = 'name') -> List[Path]:
    input_files: List[Path] = []

    for input_path in input_paths:
        path = Path(input_path)

        if path.is_file():
            if validate_input_file(path):
                input_files.append(path)
        elif path.is_dir():
            for file in path.iterdir():
                if validate_input_file(file):
                    input_files.append(file)
        else:
            print(f"Warning: Path not found or inaccessible: {path}", file=sys.stderr)

    if sort_by == 'name':
        input_files.sort(key=lambda x: x.name.lower())
    elif sort_by == 'created':
        input_files.sort(key=lambda x: x.stat().st_ctime)
    elif sort_by == 'modified':
        input_files.sort(key=lambda x: x.stat().st_mtime)

    return input_files


def convert_image_to_pdf_bytes(image_path: Path, layout_fun=None) -> bytes:
    with open(image_path, 'rb') as f:
        img_data = f.read()
    if layout_fun:
        return img2pdf.convert(img_data, layout_fun=layout_fun)
    return img2pdf.convert(img_data)


def render_html_files_to_pdf_bytes(html_paths: List[Path], page_size: str) -> Dict[Path, bytes]:
    """
    Render every HTML file to PDF bytes using ONE reused headless
    Chromium instance/page. Launching the browser is the expensive
    part, not navigating to a new file, so reusing it across all
    HTML inputs is what makes this fast for batches.
    """
    pdf_kwargs = {}
    if page_size == 'a4':
        pdf_kwargs['format'] = 'A4'
    elif page_size == 'letter':
        pdf_kwargs['format'] = 'Letter'
    else:
        # Respect the page's own @page CSS size if it has one
        pdf_kwargs['prefer_css_page_size'] = True

    results: Dict[Path, bytes] = {}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            for html_path in tqdm(html_paths, desc="Rendering HTML", unit="file"):
                try:
                    page.goto(html_path.resolve().as_uri(), wait_until='load')
                    results[html_path] = page.pdf(**pdf_kwargs)
                except Exception as e:
                    print(f"Warning: Error rendering HTML file {html_path}: {e}", file=sys.stderr)
            page.close()
            browser.close()
    except PlaywrightError as e:
        print(
            f"Error: Chromium is not installed for Playwright ({e}).\n"
            "Run: playwright install chromium",
            file=sys.stderr,
        )
        sys.exit(1)

    return results


def create_pdf(input_files: List[Path], output_path: str, page_size: str) -> None:
    if not input_files:
        print("Error: No valid input files to convert", file=sys.stderr)
        sys.exit(1)

    html_files = [p for p in input_files if is_html_file(p)]
    n_images = len(input_files) - len(html_files)
    print(f"Processing {len(input_files)} file(s) ({n_images} image(s), {len(html_files)} HTML)...")

    layout_fun = None
    if page_size in ('a4', 'letter'):
        layout_fun = img2pdf.get_layout_fun(pagesize=img2pdf.parse_pagesize_rectarg(page_size))

    # Render all HTML files up front in a single browser session
    html_pdf_map: Dict[Path, bytes] = {}
    if html_files:
        html_pdf_map = render_html_files_to_pdf_bytes(html_files, page_size)

    pdf_segments: List[bytes] = []
    for input_path in tqdm(input_files, desc="Assembling", unit="file"):
        try:
            if is_html_file(input_path):
                segment = html_pdf_map.get(input_path)
                if segment is None:
                    continue  # already warned during rendering
                pdf_segments.append(segment)
            else:
                pdf_segments.append(convert_image_to_pdf_bytes(input_path, layout_fun))
        except PermissionError:
            print(f"Warning: Permission denied, skipping: {input_path}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"Warning: Error converting file {input_path}: {e}", file=sys.stderr)
            continue

    if not pdf_segments:
        print("Error: Failed to convert any input files", file=sys.stderr)
        sys.exit(1)

    try:
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        writer = PdfWriter()
        for segment in pdf_segments:
            reader = PdfReader(io.BytesIO(segment))
            for page in reader.pages:
                writer.add_page(page)

        with open(output_path, 'wb') as f:
            writer.write(f)

        print(f"\nSuccess! PDF created: {output_path}")
        print(f"Total files processed: {len(pdf_segments)}")

    except PermissionError:
        print(f"Error: Permission denied writing to {output_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error creating PDF: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Convert images and HTML files to PDF (fast HTML rendering via Playwright/Chromium)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s image.jpg -o output.pdf
  %(prog)s img1.jpg img2.png img3.webp -o merged.pdf
  %(prog)s /path/to/images -o all_images.pdf
  %(prog)s image.jpg --size a4 -o document.pdf
  %(prog)s images/ --sort-by modified -o sorted.pdf
  %(prog)s page.html -o document.pdf
  %(prog)s cover.html img1.jpg chapter2.html -o mixed.pdf
  %(prog)s ./mixed-content/ -o all.pdf
        '''
    )

    parser.add_argument(
        'input',
        nargs='+',
        help='Input image/HTML file(s) or directory containing images and HTML files'
    )

    parser.add_argument(
        '-o', '--output',
        required=True,
        help='Output PDF file path'
    )

    parser.add_argument(
        '--size',
        choices=['auto', 'a4', 'letter'],
        default='auto',
        help='Page size: auto (original / CSS @page size for HTML), a4, or letter (default: auto)'
    )

    parser.add_argument(
        '--sort-by',
        choices=['name', 'created', 'modified'],
        default='name',
        help='Sort inputs by: name (alphanumeric), created (creation time), modified (default: name)'
    )

    args = parser.parse_args()

    input_files = get_input_files(args.input, args.sort_by)

    if not input_files:
        print("Error: No valid image or HTML files found", file=sys.stderr)
        sys.exit(1)

    create_pdf(input_files, args.output, args.size)


if __name__ == '__main__':
    main()
