"""
fix_extract.py
==============
Jalankan script ini untuk mengekstrak semua file .zip yang ada
di dalam folder GoogleFonts_Offline yang belum terekstrak.

Cara pakai:
  python fix_extract.py
  python fix_extract.py --dir "GoogleFonts_Offline"
"""

import zipfile
import argparse
from pathlib import Path


def fix_extract(fonts_dir: Path):
    print("=" * 50)
    print("  Google Fonts - Fix Extractor")
    print("=" * 50)
    print(f"Folder: {fonts_dir.resolve()}\n")

    if not fonts_dir.exists():
        print(f"ERROR: Folder tidak ditemukan: {fonts_dir}")
        return

    # Cari semua .zip di root folder
    zip_files = list(fonts_dir.glob("*.zip"))
    # Cari juga .zip di subfolder
    zip_files += list(fonts_dir.glob("**/*.zip"))
    zip_files = list(set(zip_files))

    if not zip_files:
        print("Tidak ada file .zip ditemukan.")
        # Cek apakah font sudah ada
        ttf_files = list(fonts_dir.glob("**/*.ttf")) + list(fonts_dir.glob("**/*.otf"))
        print(f"File font yang ditemukan: {len(ttf_files)} file")
        return

    print(f"Ditemukan {len(zip_files)} file .zip\n")

    total_extracted = 0
    total_failed = 0

    for zip_path in sorted(zip_files):
        print(f"📦 {zip_path.name}...", end=" ", flush=True)
        
        # Tentukan folder tujuan ekstrak
        # Jika zip ada di root, ekstrak ke subfolder dengan nama zip
        if zip_path.parent == fonts_dir:
            dest_dir = fonts_dir / zip_path.stem
        else:
            dest_dir = zip_path.parent
        
        dest_dir.mkdir(parents=True, exist_ok=True)

        try:
            extracted = 0
            with zipfile.ZipFile(zip_path, "r") as zf:
                # Lihat isi zip dulu
                all_members = zf.namelist()
                font_members = [m for m in all_members if m.lower().endswith((".ttf", ".otf"))]
                
                if not font_members:
                    print(f"⚠ Tidak ada .ttf/.otf (total {len(all_members)} file di zip)")
                    continue

                for member in font_members:
                    filename = Path(member).name
                    if not filename:
                        continue
                    target = dest_dir / filename
                    target.write_bytes(zf.read(member))
                    extracted += 1

            print(f"✓ {extracted} file diekstrak ke {dest_dir.name}/")
            zip_path.unlink()  # hapus zip setelah berhasil
            total_extracted += extracted

        except zipfile.BadZipFile:
            print(f"✗ File zip rusak/korup")
            total_failed += 1
        except Exception as e:
            print(f"✗ Error: {e}")
            total_failed += 1

    print()
    print("=" * 50)
    print(f"✅ Selesai! {total_extracted} file font diekstrak.")
    if total_failed:
        print(f"⚠  {total_failed} zip gagal diekstrak (mungkin rusak, coba download ulang).")
    
    # Hitung total font sekarang
    ttf_files = list(fonts_dir.glob("**/*.ttf")) + list(fonts_dir.glob("**/*.otf"))
    print(f"📊 Total file font sekarang: {len(ttf_files)} file")
    print()
    print("Sekarang jalankan installer.py dan klik Scan.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", default="GoogleFonts_Offline", help="Folder font")
    args = parser.parse_args()

    fix_extract(Path(args.dir))
    input("\nTekan Enter untuk keluar...")


if __name__ == "__main__":
    main()
