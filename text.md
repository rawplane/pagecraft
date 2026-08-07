Kamu adalah seorang Senior Software Engineer. Buatkan kode lengkap untuk aplikasi CLI (Command Line Interface) yang berfungsi mengonversi file gambar menjadi satu file PDF.

Spesifikasi & Persyaratan:
1. Bahasa Pemrograman: Python 3 (Gunakan library `img2pdf` atau `Pillow` dipadu dengan `argparse` atau `click`).
2. Fitur Utama:
   - Input Fleksibel: Mampu menerima input berupa satu gambar, beberapa gambar sekaligus, atau seluruh gambar di dalam suatu direktori/folder.
   - Pengurutan File: Gambar harus digabungkan ke PDF sesuai urutan alfanumerik nama file (atau opsi urut berdasarkan waktu buat/modifikasi).
   - Pengaturan Output: Opsi untuk menentukan nama dan jalur (path) file PDF output.
   - Ukuran Halaman: Opsi menentukan ukuran halaman PDF (Auto/Original, A4, atau Letter) dengan posisi gambar centered/fit-to-page.
   - Progress Bar: Menampilkan indikator kemajuan (misal memakai `tqdm`) saat memproses banyak gambar.
3. Penanganan Error & Validasi:
   - Validasi ekstensi file gambar yang didukung (.jpg, .jpeg, .png, .webp, .bmp, .tiff).
   - Lewati file non-gambar secara halus (berikan warning di console tanpa mematikan program).
   - Penanganan error jika file tidak ditemukan atau akses ditolak.
4. Output yang Diharapkan:
   - Kode program Python yang modular dan bersih (Clean Code & Type Hints).
   - Isi file `requirements.txt` untuk dependensinya.
   - Panduan cara instalasi dan contoh perintah eksekusi CLI lengkap dengan berbagai flag/argumennya.
