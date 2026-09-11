"""Tests for merge module: parallel conversion, streaming, exit codes."""

import io
from pathlib import Path

from pypdf import PdfReader

from pagecraft.logging_config import (
    EXIT_PARTIAL,
    EXIT_SUCCESS,
    EXIT_TOTAL_FAIL,
)
from pagecraft.merge import (
    convert_all,
    convert_one,
    create_pdf,
)


class TestConvertOne:
    def test_image_returns_bytes(self, sample_images):
        pdf_bytes, err = convert_one(sample_images[0], "auto")
        assert pdf_bytes is not None
        assert err is None
        assert pdf_bytes[:4] == b"%PDF"

    def test_html_returns_bytes(self, sample_html):
        pdf_bytes, err = convert_one(sample_html, "auto")
        assert pdf_bytes is not None
        assert err is None
        assert pdf_bytes[:4] == b"%PDF"

    def test_corrupt_returns_error(self, corrupt_image):
        pdf_bytes, err = convert_one(corrupt_image, "auto")
        assert pdf_bytes is None
        assert err is not None


class TestConvertAll:
    def test_serial_path(self, sample_images):
        """jobs=1 uses serial path, yields in input order."""
        results = list(
            convert_all(sample_images, "auto", jobs=1, quiet=True)
        )
        assert len(results) == 3
        for path, pdf_bytes, err in results:
            assert pdf_bytes is not None
            assert err is None

    def test_parallel_path(self, sample_images):
        """jobs=2 uses ProcessPool, order not guaranteed."""
        results = list(
            convert_all(sample_images, "auto", jobs=2, quiet=True)
        )
        assert len(results) == 3
        paths = {r[0] for r in results}
        assert paths == set(sample_images)

    def test_single_file_uses_serial(self, sample_images):
        """1 file skips pool."""
        results = list(
            convert_all([sample_images[0]], "auto", jobs=4, quiet=True)
        )
        assert len(results) == 1


class TestCreatePdfExitCodes:
    def test_success_returns_0(self, sample_images, tmp_workspace):
        out = tmp_workspace / "out.pdf"
        code = create_pdf(sample_images, str(out), "auto", quiet=True)
        assert code == EXIT_SUCCESS
        assert out.exists()

    def test_empty_input_returns_3(self, tmp_workspace):
        out = tmp_workspace / "out.pdf"
        code = create_pdf([], str(out), "auto", quiet=True)
        assert code == EXIT_TOTAL_FAIL

    def test_mixed_html_image(self, sample_images, sample_html, tmp_workspace):
        inputs = sample_images + [sample_html]
        out = tmp_workspace / "out.pdf"
        code = create_pdf(inputs, str(out), "auto", quiet=True)
        assert code == EXIT_SUCCESS
        reader = PdfReader(str(out))
        assert len(reader.pages) >= 4

    def test_fast_path_small_batch(self, tmp_workspace):
        """<=20 image-only files uses fast path."""
        from PIL import Image
        imgs = []
        for i in range(5):
            p = tmp_workspace / f"img_{i}.png"
            Image.new("RGB", (50, 50), (i * 50, 0, 0)).save(p)
            imgs.append(p)
        out = tmp_workspace / "out.pdf"
        code = create_pdf(imgs, str(out), "auto", quiet=True)
        assert code == EXIT_SUCCESS
        reader = PdfReader(str(out))
        assert len(reader.pages) == 5
