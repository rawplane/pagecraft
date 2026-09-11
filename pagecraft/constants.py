"""Constants: supported file extensions."""

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}
SUPPORTED_HTML_EXTENSIONS = {".html", ".htm"}
# Backward-compatible alias
SUPPORTED_EXTENSIONS = SUPPORTED_IMAGE_EXTENSIONS | SUPPORTED_HTML_EXTENSIONS
