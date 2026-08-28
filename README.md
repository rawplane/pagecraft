Image to PDF Converter CLI

A CLI application for converting image files into a single PDF file.

Installation

1. Make sure Python 3.7+ is installed.
2. Install the dependencies:

pip install -r requirements.txt

Use Cases

Convert a single image:

python img2pdf_cli.py image.jpg -o output.pdf

Convert multiple images:

python img2pdf_cli.py img1.jpg img2.png img3.webp -o merged.pdf

Convert all images in a directory:

python img2pdf_cli.py images -o all_images.pdf

Specify the page size (A4/Letter):

python img2pdf_cli.py image.jpg --size a4 -o document.pdf

Sort by modification time:

python img2pdf_cli.py images/ --sort-by modified -o sorted.pdf

Complete Options

Argument| Description
"input"| Image file or directory (multiple inputs are supported)
"-o, --output"| Output PDF file path (required)
"--size"| Page size: "auto", "a4", "letter" (default: auto)
"--sort-by"| Sort by: "name", "created", "modified" (default: name)

Supported Image Formats

".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"
