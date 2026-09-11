"""Tests for converters module."""

import io
from pathlib import Path

from pypdf import PdfReader

from pagecraft.converters import (
    build_layout_fun,
    convert_image_to_pdf_bytes,
    render_html_to_pdf_bytes,
)


class TestBuildLayoutFun:
    def test_auto_returns_none(self):
        assert build_layout_fun("auto") is None

    def test_a4_returns_callable(self):
        fun = build_layout_fun("a4")
        assert fun is not None
        assert callable(fun)

    def test_letter_returns_callable(self):
        fun = build_layout_fun("letter")
        assert fun is not None
        assert callable(fun)


class TestConvertImageToPdfBytes:
    def test_produces_valid_pdf(self, sample_images):
        pdf_bytes = convert_image_to_pdf_bytes(sample_images[0])
        assert pdf_bytes[:4] == b"%PDF"
        reader = PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) == 1

    def test_with_layout_fun(self, sample_images):
        fun = build_layout_fun("a4")
        pdf_bytes = convert_image_to_pdf_bytes(sample_images[0], layout_fun=fun)
        assert pdf_bytes[:4] == b"%PDF"


class TestRenderHtmlToPdfBytes:
    def test_produces_valid_pdf(self, sample_html):
        pdf_bytes = render_html_to_pdf_bytes(sample_html)
        assert pdf_bytes[:4] == b"%PDF"
        reader = PdfReader(io.BytesIO(pdf_bytes))
        assert len(reader.pages) >= 1

    def test_relative_resource_resolution(self, tmp_workspace):
        """HTML <img src> relative to the HTML file's directory."""
        from PIL import Image

        img_path = tmp_workspace / "logo.png"
        Image.new("RGB", (100, 50), (0, 128, 0)).save(img_path)
        html = tmp_workspace / "page.html"
        html.write_text(
            '<html><body><img src="logo.png"></body></html>'
        )
        pdf_bytes = render_html_to_pdf_bytes(html)
        assert pdf_bytes[:4] == b"%PDF"
