"""Pagecraft: convert images and HTML files into a single PDF.

Public API (stable, backward-compatible):
    from pagecraft import get_input_files, get_image_files, create_pdf
"""

from pagecraft.discovery import get_input_files, get_image_files
from pagecraft.merge import create_pdf

__version__ = "0.2.0"

__all__ = ["get_input_files", "get_image_files", "create_pdf", "__version__"]
