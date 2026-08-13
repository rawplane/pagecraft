# Image to PDF Converter CLI

Aplikasi CLI untuk mengonversi file gambar menjadi satu file PDF.

## Instalasi

1. Pastikan Python 3.7+ terinstal
2. Install dependensi:
```bash
pip install -r requirements.txt
```

## Usecase

### Konversi satu gambar:
```bash
python img2pdf_cli.py image.jpg -o output.pdf
```

### Konversi beberapa gambar:
```bash
python img2pdf_cli.py img1.jpg img2.png img3.webp -o merged.pdf
```

### Konversi semua gambar dalam direktori:
```bash
python img2pdf_cli.py images -o all_images.pdf
```

### Tentukan ukuran halaman (A4/Letter):
```bash
python img2pdf_cli.py image.jpg --size a4 -o document.pdf
```

### Urutkan berdasarkan waktu:
```bash
python img2pdf_cli.py images/ --sort-by modified -o sorted.pdf
```

## Opsi Lengkap

| Argumen | Deskripsi |
|---------|-----------|
| `input` | File gambar atau direktori (bisa lebih dari satu) |
| `-o, --output` | Path file PDF output (wajib) |
| `--size` | Ukuran halaman: `auto`, `a4`, `letter` (default: auto) |
| `--sort-by` | Urutkan: `name`, `created`, `modified` (default: name) |

## Format Gambar yang Didukung

`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.tiff`
