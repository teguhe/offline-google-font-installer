"""
Google Fonts Downloader
=======================
Jalankan script ini saat ONLINE untuk mengunduh font ke folder lokal.
Hasil unduhan bisa dipakai untuk instalasi offline.

Cara pakai:
  python google_font_downloader.py
  python google_font_downloader.py --fonts "Roboto,Open Sans,Lato"
  python google_font_downloader.py --all   (unduh semua ~1400+ font)
"""

import os
import sys
import json
import zipfile
import argparse
import urllib.request
import urllib.error
from pathlib import Path

# ── Popular font list (bisa dipakai tanpa API key) ──────────────────────────
POPULAR_FONTS = [
    "Roboto", "Open Sans", "Lato", "Montserrat", "Oswald",
    "Raleway", "PT Sans", "Merriweather", "Ubuntu", "Playfair Display",
    "Nunito", "Poppins", "Source Sans Pro", "Titillium Web", "Inconsolata",
    "Fira Sans", "Rubik", "Work Sans", "Noto Sans", "Inter",
    "Josefin Sans", "Mulish", "Barlow", "Quicksand", "Cabin",
    "Exo 2", "Karla", "Muli", "Oxygen", "Pacifico",
    "Dancing Script", "Lobster", "Abril Fatface", "Bebas Neue", "Anton",
    "Righteous", "Permanent Marker", "Shadows Into Light", "Amatic SC", "Comfortaa",
    "Noto Serif", "PT Serif", "Lora", "Crimson Text", "EB Garamond",
    "Source Code Pro", "Fira Code", "JetBrains Mono", "Space Mono", "Courier Prime",
    "Baloo 2", "Cardo", "Cormorant Garamond", "DM Sans", "DM Serif Display",
    "Fredoka One", "Gochi Hand", "Indie Flower", "Kalam", "Satisfy",
]

GOOGLE_FONTS_API = "https://fonts.googleapis.com/css2?family={family}:ital,wght@0,100;0,200;0,300;0,400;0,500;0,600;0,700;0,800;0,900;1,400;1,700&display=swap"
FONT_LIST_URL = "https://fonts.google.com/download/list"


def sanitize_name(name: str) -> str:
    return name.replace(" ", "_").replace("/", "_")


def download_font_zip(font_name: str, output_dir: Path) -> bool:
    """Download font zip dari Google Fonts."""
    family_param = font_name.replace(" ", "+")
    url = f"https://fonts.google.com/download?family={family_param}"
    font_dir = output_dir / sanitize_name(font_name)
    font_dir.mkdir(parents=True, exist_ok=True)

    zip_path = font_dir / f"{sanitize_name(font_name)}.zip"
    try:
        print(f"  ⬇  Mengunduh {font_name}...", end=" ", flush=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()

        if len(data) < 1000:
            print("✗ (gagal/tidak ditemukan)")
            return False

        zip_path.write_bytes(data)

        # Ekstrak file .ttf dan .otf saja
        with zipfile.ZipFile(zip_path, "r") as zf:
            for member in zf.namelist():
                if member.lower().endswith((".ttf", ".otf")):
                    filename = Path(member).name
                    target = font_dir / filename
                    target.write_bytes(zf.read(member))

        zip_path.unlink()  # hapus zip setelah ekstrak
        ttf_count = len(list(font_dir.glob("*.ttf"))) + len(list(font_dir.glob("*.otf")))
        print(f"✓ ({ttf_count} file)")
        return True

    except Exception as e:
        print(f"✗ ({e})")
        return False


def save_manifest(fonts_downloaded: list, output_dir: Path):
    """Simpan manifest.json untuk installer."""
    manifest = {"fonts": fonts_downloaded, "version": "1.0"}
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"\n✅ Manifest disimpan: {output_dir / 'manifest.json'}")


def main():
    parser = argparse.ArgumentParser(description="Google Fonts Downloader")
    parser.add_argument("--fonts", help="Daftar font dipisah koma, misal: \"Roboto,Lato\"")
    parser.add_argument("--all", action="store_true", help="Unduh semua font populer")
    parser.add_argument("--output", default="GoogleFonts_Offline", help="Folder output")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.fonts:
        font_list = [f.strip() for f in args.fonts.split(",") if f.strip()]
    else:
        font_list = POPULAR_FONTS

    print("=" * 55)
    print("       GOOGLE FONTS DOWNLOADER")
    print("=" * 55)
    print(f"📁 Output folder : {output_dir.resolve()}")
    print(f"🔤 Jumlah font   : {len(font_list)}")
    print("=" * 55)

    success, failed = [], []
    for font in font_list:
        ok = download_font_zip(font, output_dir)
        (success if ok else failed).append(font)

    save_manifest(success, output_dir)

    print("\n📊 RINGKASAN")
    print(f"   Berhasil : {len(success)} font")
    print(f"   Gagal    : {len(failed)} font")
    if failed:
        print(f"   Gagal    : {', '.join(failed)}")
    print(f"\n📦 Folder siap dipakai offline: {output_dir.resolve()}")
    print("   Salin folder ini ke PC target, lalu jalankan installer.py")


if __name__ == "__main__":
    main()
