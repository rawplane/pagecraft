"""Tests for validation module."""

from pathlib import Path

from pagecraft.validation import (
    validate_html_file,
    validate_image_file,
    validate_input_file,
)


class TestValidateImage:
    def test_valid_png(self, sample_images):
        for p in sample_images:
            assert validate_image_file(p) is True

    def test_nonexistent_file(self, tmp_path):
        p = tmp_path / "nope.png"
        assert validate_image_file(p) is False

    def test_unsupported_extension(self, tmp_path):
        p = tmp_path / "file.txt"
        p.write_text("hello")
        assert validate_image_file(p) is False

    def test_corrupt_image(self, corrupt_image):
        assert validate_image_file(corrupt_image) is False

    def test_directory_not_file(self, tmp_path):
        assert validate_image_file(tmp_path) is False


class TestValidateHtml:
    def test_valid_html(self, sample_html):
        assert validate_html_file(sample_html) is True

    def test_empty_html(self, empty_html):
        assert validate_html_file(empty_html) is False

    def test_nonexistent_html(self, tmp_path):
        p = tmp_path / "nope.html"
        assert validate_html_file(p) is False

    def test_unsupported_extension(self, tmp_path):
        p = tmp_path / "file.xyz"
        p.write_text("data")
        assert validate_html_file(p) is False


class TestValidateInputFile:
    def test_dispatches_image(self, sample_images):
        assert validate_input_file(sample_images[0]) is True

    def test_dispatches_html(self, sample_html):
        assert validate_input_file(sample_html) is True

    def test_unsupported(self, tmp_path):
        p = tmp_path / "file.txt"
        p.write_text("hello")
        assert validate_input_file(p) is False
