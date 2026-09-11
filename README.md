# convert_to_pdf.py

Convert images and HTML files to PDF — bisa dicampur dalam satu output PDF (misal cover HTML, lalu beberapa gambar, lalu chapter HTML lagi).

HTML dirender pakai **Playwright + headless Chromium** dengan satu browser instance yang dipakai ulang untuk semua file, jadi jauh lebih cepat daripada render ulang engine per file, dan lebih akurat untuk CSS modern (flexbox, grid, dll) dibanding engine non-browser.

## Instalasi

```bash
pip install playwright img2pdf pillow pypdf tqdm --break-system-packages
playwright install chromium
```

`playwright install chromium` wajib dijalankan sekali — ini yang download binary browser-nya (bukan cuma library Python-nya).

## Cara Pakai

```bash
# Satu file
python convert_to_pdf.py image.jpg -o output.pdf

# Beberapa file, urutan sesuai argumen/sorting
python convert_to_pdf.py img1.jpg img2.png img3.webp -o merged.pdf

# Semua file yang didukung di dalam folder
python convert_to_pdf.py /path/to/images -o all_images.pdf

# Paksa ukuran halaman A4
python convert_to_pdf.py image.jpg --size a4 -o document.pdf

# Urutkan berdasarkan tanggal modifikasi
python convert_to_pdf.py images/ --sort-by modified -o sorted.pdf

# HTML tunggal
python convert_to_pdf.py page.html -o document.pdf

# Campur HTML dan gambar dalam satu PDF
python convert_to_pdf.py cover.html img1.jpg chapter2.html -o mixed.pdf

# Semua file (gambar + HTML) di dalam folder
python convert_to_pdf.py ./mixed-content/ -o all.pdf
```

## Argumen

| Argumen | Wajib | Deskripsi |
|---|---|---|
| `input` | ✅ | Satu atau lebih file gambar/HTML, atau path folder yang isinya file-file tersebut |
| `-o`, `--output` | ✅ | Path file PDF hasil output |
| `--size` | ❌ | `auto` (default), `a4`, atau `letter`. Untuk HTML, `auto` menghormati ukuran `@page` di CSS kalau ada |
| `--sort-by` | ❌ | `name` (default, alfabetis), `created`, atau `modified` |

## Format yang Didukung

- **Gambar**: `.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.tiff`
- **HTML**: `.html`, `.htm` — resource relatif (`<img src>`, `<link rel="stylesheet">`, dll) di-resolve otomatis relatif terhadap lokasi file HTML-nya

## Catatan

- File yang gagal divalidasi/dirender (rusak, kosong, permission denied) akan di-skip dengan warning di stderr, bukan menghentikan seluruh proses.
- Jika folder mengandung campuran file yang didukung dan tidak didukung, hanya file yang didukung yang diproses.
- Urutan file dalam PDF akhir mengikuti urutan argumen `input` (untuk file individual) dan hasil sorting (`--sort-by`) untuk isi folder.
