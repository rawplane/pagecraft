"""PDF creation: convert inputs and merge into a single PDF.

Phase 1: behavior-identical refactor of the original create_pdf().
Parallelization and streaming come in Phase 2.
"""

import io
import sys
from pathlib import Path
from typing import List, Optional

from pypdf import PdfReader, PdfWriter
from tqdm import tqdm

from pagecraft.converters import (
    build_layout_fun,
    convert_image_to_pdf_bytes,
    render_html_to_pdf_bytes,
)
from pagecraft.discovery import is_html_file


def convert_one(input_path: Path, page_size: str) -> Optional[bytes]:
    """Convert a single input file to PDF bytes.

    Returns None on failure (the error is printed to stderr by the caller
    in Phase 1; Phase 3 replaces this with structured logging).
    """
    if is_html_file(input_path):
        return render_html_to_pdf_bytes(input_path)
    layout_fun = build_layout_fun(page_size)
    return convert_image_to_pdf_bytes(input_path, layout_fun)


def create_pdf(input_files: List[Path], output_path: str, page_size: str) -> None:
    if not input_files:
        print("Error: No valid input files to convert", file=sys.stderr)
        sys.exit(1)

    n_images = sum(1 for p in input_files if not is_html_file(p))
    n_html = len(input_files) - n_images
    print(f"Processing {len(input_files)} file(s) ({n_images} image(s), {n_html} HTML)...")

    pdf_segments: List[bytes] = []

    for input_path in tqdm(input_files, desc="Converting", unit="file"):
        try:
            segment = convert_one(input_path, page_size)
            if segment is not None:
                pdf_segments.append(segment)
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

        with open(output_path, "wb") as f:
            writer.write(f)

        print(f"\nSuccess! PDF created: {output_path}")
        print(f"Total files processed: {len(pdf_segments)}")

    except PermissionError:
        print(f"Error: Permission denied writing to {output_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error creating PDF: {e}", file=sys.stderr)
        sys.exit(1)
