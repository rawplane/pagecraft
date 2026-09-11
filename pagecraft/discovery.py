"""Input file discovery and sorting."""

import sys
from pathlib import Path
from typing import List

from pagecraft.constants import SUPPORTED_HTML_EXTENSIONS
from pagecraft.validation import validate_input_file


def is_html_file(file_path: Path) -> bool:
    return file_path.suffix.lower() in SUPPORTED_HTML_EXTENSIONS


def get_input_files(input_paths: List[str], sort_by: str = "name") -> List[Path]:
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

    if sort_by == "name":
        input_files.sort(key=lambda x: x.name.lower())
    elif sort_by == "created":
        input_files.sort(key=lambda x: x.stat().st_ctime)
    elif sort_by == "modified":
        input_files.sort(key=lambda x: x.stat().st_mtime)

    return input_files


def get_image_files(input_paths: List[str], sort_by: str = "name") -> List[Path]:
    """Backward-compatible wrapper: returns all valid inputs (images + HTML)."""
    return get_input_files(input_paths, sort_by)
