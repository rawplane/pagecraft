"""Input file validation."""

import sys
from pathlib import Path

from PIL import Image

from pagecraft.constants import SUPPORTED_HTML_EXTENSIONS, SUPPORTED_IMAGE_EXTENSIONS


def _warn(message: str, file_path: Path) -> None:
    print(f"Warning: {message}: {file_path}", file=sys.stderr)


def validate_image_file(file_path: Path) -> bool:
    if not file_path.exists():
        _warn("File not found", file_path)
        return False
    if not file_path.is_file():
        _warn("Not a file", file_path)
        return False
    if file_path.suffix.lower() not in SUPPORTED_IMAGE_EXTENSIONS:
        _warn("Unsupported file type, skipping", file_path)
        return False
    try:
        with Image.open(file_path) as img:
            img.verify()
        return True
    except Exception as e:
        _warn(f"Invalid or corrupted image, skipping ({e})", file_path)
        return False


def validate_html_file(file_path: Path) -> bool:
    if not file_path.exists():
        _warn("File not found", file_path)
        return False
    if not file_path.is_file():
        _warn("Not a file", file_path)
        return False
    if file_path.suffix.lower() not in SUPPORTED_HTML_EXTENSIONS:
        _warn("Unsupported file type, skipping", file_path)
        return False
    try:
        if file_path.stat().st_size == 0:
            _warn("Empty HTML file, skipping", file_path)
            return False
        return True
    except Exception as e:
        _warn(f"Cannot access HTML file, skipping ({e})", file_path)
        return False


def validate_input_file(file_path: Path) -> bool:
    suffix = file_path.suffix.lower()
    if suffix in SUPPORTED_IMAGE_EXTENSIONS:
        return validate_image_file(file_path)
    if suffix in SUPPORTED_HTML_EXTENSIONS:
        return validate_html_file(file_path)
    print(f"Warning: Unsupported file type, skipping: {file_path}", file=sys.stderr)
    return False
