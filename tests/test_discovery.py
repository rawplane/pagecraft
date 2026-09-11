"""Tests for discovery module: file finding and sorting."""

from pathlib import Path

from pagecraft.discovery import (
    get_image_files,
    get_input_files,
    is_html_file,
)


class TestIsHtmlFile:
    def test_html(self):
        assert is_html_file(Path("foo.html")) is True

    def test_htm(self):
        assert is_html_file(Path("foo.htm")) is True

    def test_image(self):
        assert is_html_file(Path("foo.png")) is False

    def test_uppercase(self):
        assert is_html_file(Path("FOO.HTML")) is True


class TestGetInputFiles:
    def test_single_file(self, sample_images):
        files = get_input_files([str(sample_images[0])])
        assert len(files) == 1
        assert files[0] == sample_images[0]

    def test_multiple_files(self, sample_images):
        inputs = [str(p) for p in sample_images]
        files = get_input_files(inputs)
        assert len(files) == 3

    def test_directory(self, sample_images, sample_html, tmp_workspace):
        files = get_input_files([str(tmp_workspace)])
        # 3 images + 1 html
        assert len(files) == 4

    def test_nonexistent_path(self, tmp_path):
        files = get_input_files([str(tmp_path / "nope")])
        assert len(files) == 0

    def test_skips_corrupt(self, sample_images, corrupt_image, tmp_workspace):
        files = get_input_files([str(tmp_workspace)])
        # 3 valid images, corrupt excluded (no html in this workspace)
        assert len(files) == 3
        # Corrupt file is not in results
        assert corrupt_image not in files

    def test_sort_by_name(self, tmp_workspace):
        from PIL import Image
        for name in ["c.png", "a.png", "b.png"]:
            Image.new("RGB", (10, 10)).save(tmp_workspace / name)
        files = get_input_files([str(tmp_workspace)], sort_by="name")
        names = [p.name for p in files]
        assert names == ["a.png", "b.png", "c.png"]

    def test_backward_compat_wrapper(self, sample_images):
        """get_image_files is a backward-compatible alias."""
        files = get_image_files([str(p) for p in sample_images])
        assert len(files) == 3
