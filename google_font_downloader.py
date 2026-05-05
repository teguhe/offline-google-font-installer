"""
Google Fonts Downloader (Fixed v2)
=====================================
Mengunduh Google Fonts via npm @fontsource, lalu konversi woff2 -> TTF.
Tidak memerlukan API key. Bekerja 100% offline setelah download selesai.

Instalasi dependensi:
  pip install fonttools brotli

Cara pakai:
  python google_font_downloader.py
  python google_font_downloader.py --fonts "Roboto,Open Sans,Poppins"
  python google_font_downloader.py --list
"""

import io
import sys
import json
import time
import tarfile
import argparse
import urllib.request
from pathlib import Path

# ── Katalog font: "Nama Tampilan" -> "npm-package-slug" ─────────────────────
FONT_CATALOG = {
    # Sans-serif
    "Roboto":             "roboto",
    "Open Sans":          "open-sans",
    "Lato":               "lato",
    "Montserrat":         "montserrat",
    "Oswald":             "oswald",
    "Raleway":            "raleway",
    "Poppins":            "poppins",
    "Nunito":             "nunito",
    "Inter":              "inter",
    "Ubuntu":             "ubuntu",
    "Rubik":              "rubik",
    "Work Sans":          "work-sans",
    "Fira Sans":          "fira-sans",
    "Noto Sans":          "noto-sans",
    "Mulish":             "mulish",
    "Barlow":             "barlow",
    "Quicksand":          "quicksand",
    "Cabin":              "cabin",
    "Karla":              "karla",
    "DM Sans":            "dm-sans",
    "Josefin Sans":       "josefin-sans",
    "Titillium Web":      "titillium-web",
    "Exo 2":              "exo-2",
    "Source Sans 3":      "source-sans-3",
    "PT Sans":            "pt-sans",
    "Oxygen":             "oxygen",
    "Hind":               "hind",
    "Mukta":              "mukta",
    # Serif
    "Merriweather":       "merriweather",
    "Playfair Display":   "playfair-display",
    "Lora":               "lora",
    "PT Serif":           "pt-serif",
    "Noto Serif":         "noto-serif",
    "EB Garamond":        "eb-garamond",
    "Crimson Text":       "crimson-text",
    "Cormorant Garamond": "cormorant-garamond",
    "DM Serif Display":   "dm-serif-display",
    "Cardo":              "cardo",
    # Display
    "Anton":              "anton",
    "Righteous":          "righteous",
    "Fredoka":            "fredoka",
    "Comfortaa":          "comfortaa",
    "Baloo 2":            "baloo-2",
    "Pacifico":           "pacifico",
    "Lobster":            "lobster",
    "Abril Fatface":      "abril-fatface",
    "Amatic SC":          "amatic-sc",
    "Bebas Neue":         "bebas-neue",
    # Handwriting
    "Dancing Script":     "dancing-script",
    "Caveat":             "caveat",
    "Shadows Into Light": "shadows-into-light",
    "Indie Flower":       "indie-flower",
    "Kalam":              "kalam",
    "Satisfy":            "satisfy",
    "Permanent Marker":   "permanent-marker",
    "Gochi Hand":         "gochi-hand",
    # Monospace
    "Source Code Pro":    "source-code-pro",
    "Fira Code":          "fira-code",
    "JetBrains Mono":     "jetbrains-mono",
    "Space Mono":         "space-mono",
    "Courier Prime":      "courier-prime",
    "Inconsolata":        "inconsolata",
}

NPM_REGISTRY = "https://registry.npmjs.org"
NPM_HEADERS  = {"User-Agent": "npm/9.0.0 node/v18.0.0"}


def get(url: str, timeout: int = 30) -> bytes:
    req = urllib.request.Request(url, headers=NPM_HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def get_tarball_url(package_slug: str) -> str | None:
    """Ambil URL tarball versi terbaru dari npm registry."""
    url = f"{NPM_REGISTRY}/@fontsource/{package_slug}"
    try:
        meta = json.loads(get(url, timeout=15))
        latest = meta["dist-tags"]["latest"]
        return meta["versions"][latest]["dist"]["tarball"]
    except Exception as e:
        return None


def woff2_to_ttf(woff2_data: bytes) -> bytes | None:
    """Konversi woff2 bytes ke TTF bytes menggunakan fonttools."""
    try:
        from fontTools.ttLib import TTFont
        font = TTFont(io.BytesIO(woff2_data))
        font.flavor = None  # hapus woff2 flavor -> jadi TTF biasa
        buf = io.BytesIO()
        font.save(buf)
        return buf.getvalue()
    except Exception as e:
        return None


def download_font(font_name: str, package_slug: str, output_dir: Path) -> bool:
    """Download satu font family dan simpan sebagai .ttf."""
    font_dir = output_dir / font_name.replace(" ", "_")
    font_dir.mkdir(parents=True, exist_ok=True)

    # 1. Ambil URL tarball
    tarball_url = get_tarball_url(package_slug)
    if not tarball_url:
        print("✗ Tidak ditemukan di npm")
        return False

    # 2. Download tarball .tgz
    try:
        tgz_data = get(tarball_url, timeout=60)
    except Exception as e:
        print(f"✗ Gagal download: {e}")
        return False

    # 3. Buka tarball dan ekstrak woff2
    try:
        tf = tarfile.open(fileobj=io.BytesIO(tgz_data), mode="r:gz")
    except Exception as e:
        print(f"✗ Gagal buka tgz: {e}")
        return False

    # Ambil file woff2: hanya latin, hanya normal weight (bukan ext)
    # Contoh nama: package/files/roboto-latin-400-normal.woff2
    woff2_members = [
        m for m in tf.getmembers()
        if m.name.endswith(".woff2")
        and "latin-" in m.name
        and "latin-ext" not in m.name
    ]

    if not woff2_members:
        # Fallback: ambil semua woff2
        woff2_members = [m for m in tf.getmembers() if m.name.endswith(".woff2")]

    if not woff2_members:
        print("✗ Tidak ada file woff2")
        return False

    # 4. Konversi woff2 -> TTF dan simpan
    converted = 0
    for member in woff2_members:
        try:
            woff2_data = tf.extractfile(member).read()
            ttf_data   = woff2_to_ttf(woff2_data)
            if ttf_data:
                # Buat nama TTF dari nama woff2
                # misal: roboto-latin-400-normal.woff2 -> Roboto-400-Regular.ttf
                stem = Path(member.name).stem  # roboto-latin-400-normal
                parts = stem.split("-")
                # Ambil weight dan style
                weight = next((p for p in parts if p.isdigit()), "400")
                style  = "Italic" if "italic" in stem else "Regular"
                ttf_name = f"{font_name.replace(' ', '')}-{weight}-{style}.ttf"
                (font_dir / ttf_name).write_bytes(ttf_data)
                converted += 1
        except Exception:
            pass

    if converted > 0:
        print(f"✓ {converted} file TTF")
        return True
    else:
        print("✗ Konversi gagal")
        return False


def check_dependencies() -> bool:
    """Cek apakah fonttools dan brotli tersedia."""
    missing = []
    try:
        import fontTools
    except ImportError:
        missing.append("fonttools")
    try:
        import brotli
    except ImportError:
        missing.append("brotli")

    if missing:
        print(f"❌ Dependensi kurang: {', '.join(missing)}")
        print(f"   Jalankan: pip install {' '.join(missing)}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description="Google Fonts Downloader v2")
    parser.add_argument("--fonts", help="Font dipisah koma: \"Roboto,Lato\"")
    parser.add_argument("--output", default="GoogleFonts_Offline", help="Folder output")
    parser.add_argument("--list", action="store_true", help="Tampilkan semua font tersedia")
    args = parser.parse_args()

    if args.list:
        print(f"Font tersedia ({len(FONT_CATALOG)}):")
        for name in sorted(FONT_CATALOG):
            print(f"  - {name}")
        return

    print("=" * 56)
    print("    GOOGLE FONTS DOWNLOADER  v2")
    print("=" * 56)

    # Cek dependensi
    if not check_dependencies():
        sys.exit(1)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.fonts:
        requested  = [f.strip() for f in args.fonts.split(",") if f.strip()]
        font_list  = {k: v for k, v in FONT_CATALOG.items() if k in requested}
        not_found  = [f for f in requested if f not in FONT_CATALOG]
        if not_found:
            print(f"⚠  Tidak ada di katalog: {', '.join(not_found)}")
            print("   Gunakan --list untuk daftar lengkap.\n")
    else:
        font_list = FONT_CATALOG

    print(f"📁 Output  : {output_dir.resolve()}")
    print(f"🔤 Font    : {len(font_list)} family")
    print(f"🌐 Sumber  : npmjs.com (@fontsource)")
    print("=" * 56)

    # Cek koneksi
    print("🔗 Memeriksa koneksi...", end=" ", flush=True)
    try:
        get("https://registry.npmjs.org", timeout=10)
        print("✓\n")
    except Exception as e:
        print(f"✗\nGagal terhubung ke npmjs.org: {e}")
        sys.exit(1)

    success, failed = [], []
    for i, (name, slug) in enumerate(font_list.items(), 1):
        print(f"[{i:2}/{len(font_list)}] {name:30s} ", end="", flush=True)
        ok = download_font(name, slug, output_dir)
        (success if ok else failed).append(name)
        time.sleep(0.2)

    # Simpan manifest
    manifest = {"fonts": success, "version": "2.0", "source": "fontsource/npm"}
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    print("\n" + "=" * 56)
    print("📊 RINGKASAN")
    print(f"   ✓ Berhasil : {len(success)} font")
    print(f"   ✗ Gagal    : {len(failed)} font")
    if failed:
        print(f"\n   Font gagal:")
        for f in failed:
            print(f"     - {f}")
    print(f"\n📦 Siap offline: {output_dir.resolve()}")
    print("   Jalankan installer.py untuk install ke Windows.")


if __name__ == "__main__":
    main()
