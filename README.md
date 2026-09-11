# Pagecraft

A CLI tool for converting images and HTML files into a single PDF.

## Features

- Convert images (JPG, PNG, WebP, BMP, TIFF) and HTML files to PDF
- Merge multiple inputs into one PDF (order preserved or sorted)
- Parallel conversion (multi-core) for large batches
- Fast path for small image-only batches (skips intermediate merge)
- Page size options: auto (original), A4, Letter
- Sort by name, creation time, or modification time
- Semantic exit codes for shell scripting

## Installation

1. Make sure Python 3.8+ is installed.
2. Install the system libraries required by WeasyPrint (HTML rendering):

```bash
# Ubuntu/Debian
sudo apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
# macOS
brew install pango libffi
```

3. Install pagecraft:

```bash
# Recommended (isolated environment):
pipx install pagecraft

# Or from source (development):
pip install -e .
```

## Usage

### Convert a single image
```bash
pagecraft image.jpg -o output.pdf
```

### Convert multiple images
```bash
pagecraft img1.jpg img2.png img3.webp -o merged.pdf
```

### Convert all images in a directory
```bash
pagecraft images/ -o all_images.pdf
```

### Specify the page size (A4/Letter)
```bash
pagecraft image.jpg --size a4 -o document.pdf
```

### Sort by modification time
```bash
pagecraft images/ --sort-by modified -o sorted.pdf
```

### Convert a single HTML file
```bash
pagecraft page.html -o document.pdf
```

### Mix HTML and images (order preserved / sorted)
```bash
pagecraft cover.html img1.jpg chapter2.html -o mixed.pdf
```

### Convert a directory containing images and HTML
```bash
pagecraft mixed-content/ -o all.pdf
```

### Use 4 parallel jobs (for large batches)
```bash
pagecraft images/ -o out.pdf -j 4
```

## Complete Options

| Argument | Description |
| :--- | :--- |
| `input` | Image/HTML file or directory (multiple inputs are supported) |
| `-o, --output` | Output PDF file path *(required)* |
| `--size` | Page size: `auto`, `a4`, `letter` *(default: `auto`)* — applies to image pages; HTML pages follow their CSS `@page` |
| `--sort-by` | Sort by: `name`, `created`, `modified` *(default: `name`)* |
| `-j, --jobs` | Number of parallel conversion jobs *(default: CPU count)* |
| `--quiet` | Suppress progress output (warnings still shown) |
| `--verbose` | Show debug-level output (per-file details) |

## Exit Codes

| Code | Meaning |
| :--- | :--- |
| `0` | Success |
| `1` | No valid input files found |
| `2` | Some files failed (partial success) |
| `3` | All files failed, or output write error |

## Supported Input Formats

Images: `*.jpg`, `*.jpeg`, `*.png`, `*.webp`, `*.bmp`, `*.tiff`

HTML: `*.html`, `*.htm` (rendered with WeasyPrint — no JavaScript support; relative `<img>`/CSS resolve from the HTML file's directory)

## Performance

On a 2-core machine:

| Batch | Time | Peak RAM |
| :--- | :--- | :--- |
| 50 images | ~2.5s | ~71 MB |
| 500 images | ~8.2s | ~87 MB |

Parallel conversion uses all available CPU cores. On an 8-core machine, expect 4-5x speedup for large batches.

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run benchmarks
python -c "from PIL import Image; [Image.new('RGB',(800,600)).save(f'img_{i}.png') for i in range(50)]"
time pagecraft img_*.png -o bench.pdf
```
