"""Shared pytest fixtures for pagecraft tests."""

import io
from pathlib import Path

import pytest
from PIL import Image


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    """A clean temporary directory for test inputs/outputs."""
    return tmp_path


@pytest.fixture
def sample_images(tmp_workspace: Path) -> list[Path]:
    """Create 3 small PNG images for testing."""
    paths = []
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]
    for i, color in enumerate(colors):
        img = Image.new("RGB", (200, 200), color=color)
        p = tmp_workspace / f"img_{i}.png"
        img.save(p)
        paths.append(p)
    return paths


@pytest.fixture
def sample_html(tmp_workspace: Path) -> Path:
    """Create a simple HTML file for testing."""
    html_path = tmp_workspace / "page.html"
    html_path.write_text(
        "<!DOCTYPE html><html><head><style>"
        "body { margin: 2cm; font-family: sans-serif; }"
        "</style></head><body><h1>Test Page</h1>"
        "<p>Hello from pagecraft test.</p></body></html>"
    )
    return html_path


@pytest.fixture
def corrupt_image(tmp_workspace: Path) -> Path:
    """Create a file with .png extension but invalid content."""
    p = tmp_workspace / "corrupt.png"
    p.write_bytes(b"not a real png")
    return p


@pytest.fixture
def empty_html(tmp_workspace: Path) -> Path:
    """Create an empty HTML file."""
    p = tmp_workspace / "empty.html"
    p.write_text("")
    return p
