"""Smoke test: end-to-end conversion produces a valid PDF."""

from pathlib import Path

from pypdf import PdfReader

from pagecraft import create_pdf, get_input_files


def test_smoke_images(sample_images, tmp_workspace):
    """3 images -> 1 PDF with 3 pages."""
    files = get_input_files([str(p) for p in sample_images])
    assert len(files) == 3

    output = tmp_workspace / "out.pdf"
    create_pdf(files, str(output), "auto")

    assert output.exists()
    reader = PdfReader(str(output))
    assert len(reader.pages) == 3


def test_smoke_html(sample_html, tmp_workspace):
    """1 HTML -> 1 PDF with 1 page."""
    files = get_input_files([str(sample_html)])
    assert len(files) == 1

    output = tmp_workspace / "out.pdf"
    create_pdf(files, str(output), "auto")

    assert output.exists()
    reader = PdfReader(str(output))
    assert len(reader.pages) >= 1


def test_smoke_mixed(sample_images, sample_html, tmp_workspace):
    """3 images + 1 HTML -> 1 PDF with 4+ pages."""
    inputs = [str(p) for p in sample_images] + [str(sample_html)]
    files = get_input_files(inputs)
    assert len(files) == 4

    output = tmp_workspace / "out.pdf"
    create_pdf(files, str(output), "auto")

    assert output.exists()
    reader = PdfReader(str(output))
    assert len(reader.pages) >= 4
