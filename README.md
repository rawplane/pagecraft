# Image & HTML to PDF Converter CLI

A CLI application for converting image and HTML files into a single PDF file.

## Installation

1. Make sure Python 3.7+ is installed.
2. Install the system libraries required by WeasyPrint (HTML rendering):

```bash
# Ubuntu/Debian
sudo apt install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libffi-dev shared-mime-info
# macOS
brew install pango libffi
```

3. Install the dependencies:

```bash
pip install -r requirements.txt
```

## Use Cases

### Convert a single image
```bash
python img2pdf_cli.py image.jpg -o output.pdf
```

### Convert multiple images
```bash
python img2pdf_cli.py img1.jpg img2.png img3.webp -o merged.pdf
```

### Convert all images in a directory
```bash
python img2pdf_cli.py images -o all_images.pdf
```

### Specify the page size (A4/Letter)
```bash
python img2pdf_cli.py image.jpg --size a4 -o document.pdf
```

### Sort by modification time
```bash
python img2pdf_cli.py images/ --sort-by modified -o sorted.pdf
```

### Convert a single HTML file
```bash
python img2pdf_cli.py page.html -o document.pdf
```

### Mix HTML and images (order preserved / sorted)
```bash
python img2pdf_cli.py cover.html img1.jpg chapter2.html -o mixed.pdf
```

### Convert a directory containing images and HTML
```bash
python img2pdf_cli.py mixed-content/ -o all.pdf
```

## Complete Options

| Argument | Description |
| :--- | :--- |
| `input` | Image/HTML file or directory (multiple inputs are supported) |
| `-o, --output` | Output PDF file path *(required)* |
| `--size` | Page size: `auto`, `a4`, `letter` *(default: `auto`)* — applies to image pages; HTML pages follow their CSS `@page` |
| `--sort-by` | Sort by: `name`, `created`, `modified` *(default: `name`)* |

## Supported Input Formats

Images: `*.jpg`, `*.jpeg`, `*.png`, `*.webp`, `*.bmp`, `*.tiff`

HTML: `*.html`, `*.htm` (rendered with WeasyPrint — no JavaScript support; relative `<img>`/CSS resolve from the HTML file's directory)
```
