#!/usr/bin/env python3
import argparse
import io
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple
import img2pdf
from PIL import Image
from pypdf import PdfReader, PdfWriter
from tqdm import tqdm
from weasyprint import HTML

SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff'}
SUPPORTED_HTML_EXTENSIONS = {'.html', '.htm'}
# Backward-compatible alias
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

def get_image_files(input_paths: List[str], sort_by: str = 'name') -> List[Path]:
    """Backward-compatible wrapper: returns all valid inputs (images + HTML)."""
    return get_input_files(input_paths, sort_by)

def get_page_size(size: str, img: bytes) -> Optional[Tuple[float, float]]:
    if size == 'a4':
        return img2pdf.get_layout_fun(pagesize=img2pdf.parse_pagesize_rectarg('a4'))
    elif size == 'letter':
        return img2pdf.get_layout_fun(pagesize=img2pdf.parse_pagesize_rectarg('letter'))
    else:
        return None

def render_html_to_pdf_bytes(html_path: Path) -> bytes:
    """Render a single HTML file to PDF bytes via WeasyPrint.

    base_url points at the HTML file's parent dir so relative
    <img src>, <link rel=stylesheet> etc. resolve correctly.
    """
    buffer = io.BytesIO()
    HTML(filename=str(html_path), base_url=str(html_path.parent)).write_pdf(buffer)
    return buffer.getvalue()

def convert_image_to_pdf_bytes(image_path: Path, layout_fun=None) -> bytes:
    with open(image_path, 'rb') as f:
        img_data = f.read()
    if layout_fun:
        return img2pdf.convert(img_data, layout_fun=layout_fun)
    return img2pdf.convert(img_data)

def create_pdf(input_files: List[Path], output_path: str, page_size: str) -> None:
    if not input_files:
        print("Error: No valid input files to convert", file=sys.stderr)
        sys.exit(1)

    n_images = sum(1 for p in input_files if not is_html_file(p))
    n_html = len(input_files) - n_images
    print(f"Processing {len(input_files)} file(s) ({n_images} image(s), {n_html} HTML)...")

    layout_fun = None
    if page_size in ('a4', 'letter'):
        layout_fun = img2pdf.get_layout_fun(pagesize=img2pdf.parse_pagesize_rectarg(page_size))

    pdf_segments: List[bytes] = []

    for input_path in tqdm(input_files, desc="Converting", unit="file"):
        try:
            if is_html_file(input_path):
                pdf_segments.append(render_html_to_pdf_bytes(input_path))
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
        description='Convert images and HTML files to PDF',
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
        help='Page size: auto (original), a4, or letter (default: auto)'
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
