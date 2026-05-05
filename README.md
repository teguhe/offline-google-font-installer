# 🔤 Google Fonts Offline Installer

Paket tools untuk mengunduh dan menginstall Google Fonts tanpa internet di Windows.

---

## 📦 Isi Paket

| File | Fungsi |
|------|--------|
| `google_font_downloader.py` | Unduh font saat **online** |
| `installer.py` | Install font secara **offline** (GUI) |
| `build_exe.bat` | Compile menjadi `.exe` (opsional) |

---

## 🚀 Cara Penggunaan

### Langkah 1 — Download Font (PC online)

```bash
# Install dependensi
pip install requests tqdm

# Unduh font populer (~60 family)
python google_font_downloader.py

# Atau tentukan font sendiri
python google_font_downloader.py --fonts "Roboto,Open Sans,Lato,Poppins"
```

Hasil: folder `GoogleFonts_Offline/` berisi file `.ttf`/`.otf`

### Langkah 2 — Salin ke PC Target

Salin seluruh folder `GoogleFonts_Offline/` beserta `installer.py` ke PC target (bisa via flashdisk, LAN, dll.)

### Langkah 3 — Install Font (PC offline)

```bash
python installer.py
```

Atau klik 2x `installer.exe` jika sudah dicompile.

**Cara pakai GUI:**
1. Browse ke folder `GoogleFonts_Offline`
2. Klik **Scan** untuk memuat daftar font
3. Centang font yang ingin diinstall
4. Klik **INSTALL FONT**

---

## 🔧 Compile ke .EXE (opsional)

Agar bisa dipakai tanpa Python terinstall:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "GoogleFontInstaller" installer.py
```

File `.exe` ada di folder `dist/`

---

## ℹ️ Catatan

- **Install System-wide** (semua user): butuh hak Administrator → klik kanan, "Run as Administrator"
- **Install User saja**: tidak butuh admin, font hanya tersedia untuk akun kamu
- Setelah install, restart aplikasi (Word, Photoshop, dll.) agar font muncul
- Kompatibel: Windows 10/11 (Python 3.8+)

---

## 📋 Font Populer yang Disertakan

Roboto, Open Sans, Lato, Montserrat, Oswald, Poppins, Nunito, Inter, Playfair Display,
Dancing Script, Fira Code, JetBrains Mono, Bebas Neue, Pacifico, Lobster, dan 40+ lainnya.
