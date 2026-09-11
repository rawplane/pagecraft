"""Converters: HTML -> PDF bytes, image -> PDF bytes."""

import io
from pathlib import Path
from typing import Optional

import img2pdf
from weasyprint import HTML


def build_layout_fun(page_size: str):
    """Build an img2pdf layout function for the given page size.

    Returns None for 'auto' (original image size).
    """
    if page_size in ("a4", "letter"):
        return img2pdf.get_layout_fun(pagesize=img2pdf.parse_pagesize_rectarg(page_size))
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
    with open(image_path, "rb") as f:
        img_data = f.read()
    if layout_fun:
        return img2pdf.convert(img_data, layout_fun=layout_fun)
    return img2pdf.convert(img_data)
