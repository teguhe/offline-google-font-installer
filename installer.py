"""
Google Fonts Offline Installer
================================
Jalankan script ini di Windows untuk menginstall font yang sudah diunduh.
Tidak memerlukan koneksi internet.

Cara pakai:
  python installer.py
  python installer.py --fonts-dir "GoogleFonts_Offline"

Bisa juga di-compile menjadi .exe menggunakan PyInstaller:
  pip install pyinstaller
  pyinstaller --onefile --windowed --icon=icon.ico installer.py
"""

import os
import sys
import json
import shutil
import ctypes
import platform
import threading
import subprocess
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox


# ── Konstanta ────────────────────────────────────────────────────────────────
APP_NAME    = "Google Fonts Offline Installer"
APP_VERSION = "1.0.0"
FONT_EXTENSIONS = {".ttf", ".otf"}

# Folder instalasi Windows
WINDOWS_FONT_DIR = Path("C:/Windows/Fonts")
USER_FONT_DIR    = Path.home() / "AppData/Local/Microsoft/Windows/Fonts"


# ── Utilitas ─────────────────────────────────────────────────────────────────

def is_windows() -> bool:
    return platform.system() == "Windows"

def is_admin() -> bool:
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False

def run_as_admin():
    """Restart script dengan hak administrator."""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit()

def install_font_windows(font_path: Path, system_wide: bool = True) -> tuple[bool, str]:
    """Install satu file font di Windows."""
    try:
        if system_wide and is_admin():
            dest = WINDOWS_FONT_DIR / font_path.name
        else:
            USER_FONT_DIR.mkdir(parents=True, exist_ok=True)
            dest = USER_FONT_DIR / font_path.name

        # Salin file
        shutil.copy2(font_path, dest)

        # Daftarkan ke registry (hanya Windows)
        if is_windows():
            import winreg
            reg_key = (
                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
                if system_wide and is_admin()
                else r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"
            )
            root = winreg.HKEY_LOCAL_MACHINE if (system_wide and is_admin()) else winreg.HKEY_CURRENT_USER
            with winreg.OpenKey(root, reg_key, 0, winreg.KEY_SET_VALUE) as key:
                font_type = "(TrueType)" if font_path.suffix.lower() == ".ttf" else "(OpenType)"
                winreg.SetValueEx(key, f"{font_path.stem} {font_type}", 0, winreg.REG_SZ, str(dest))

        return True, str(dest)
    except Exception as e:
        return False, str(e)

def install_font_linux(font_path: Path) -> tuple[bool, str]:
    """Install font di Linux (untuk testing)."""
    try:
        dest_dir = Path.home() / ".local/share/fonts"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / font_path.name
        shutil.copy2(font_path, dest)
        return True, str(dest)
    except Exception as e:
        return False, str(e)

def install_font(font_path: Path, system_wide: bool = True) -> tuple[bool, str]:
    if is_windows():
        return install_font_windows(font_path, system_wide)
    else:
        return install_font_linux(font_path)


# ── Scan folder font ──────────────────────────────────────────────────────────

def scan_fonts(fonts_dir: Path) -> list[dict]:
    """Scan folder dan kembalikan list font yang ditemukan."""
    fonts = []
    if not fonts_dir.exists():
        return fonts

    # Baca manifest jika ada
    manifest_path = fonts_dir / "manifest.json"
    families = {}
    if manifest_path.exists():
        try:
            data = json.loads(manifest_path.read_text())
            for name in data.get("fonts", []):
                families[name.replace(" ", "_")] = name
        except Exception:
            pass

    # Scan semua subfolder
    for sub in sorted(fonts_dir.iterdir()):
        if sub.is_dir():
            font_files = [f for f in sub.iterdir() if f.suffix.lower() in FONT_EXTENSIONS]
            if font_files:
                display_name = families.get(sub.name, sub.name.replace("_", " "))
                fonts.append({
                    "family": display_name,
                    "dir": sub,
                    "files": sorted(font_files),
                    "count": len(font_files),
                })

    # Scan root folder juga
    root_files = [f for f in fonts_dir.iterdir() if f.suffix.lower() in FONT_EXTENSIONS and f.is_file()]
    if root_files:
        fonts.insert(0, {
            "family": "(Root)",
            "dir": fonts_dir,
            "files": sorted(root_files),
            "count": len(root_files),
        })

    return fonts


# ── GUI ───────────────────────────────────────────────────────────────────────

class FontInstallerApp(tk.Tk):
    COLORS = {
        "bg":       "#0f1117",
        "panel":    "#1a1d27",
        "card":     "#22263a",
        "accent":   "#4f8ef7",
        "accent2":  "#6c63ff",
        "success":  "#3ecf8e",
        "warning":  "#f59e0b",
        "error":    "#ef4444",
        "text":     "#e2e8f0",
        "muted":    "#64748b",
        "border":   "#2d3353",
    }

    def __init__(self):
        super().__init__()
        self.title(f"  {APP_NAME}  v{APP_VERSION}")
        self.geometry("820x640")
        self.minsize(700, 500)
        self.configure(bg=self.COLORS["bg"])
        self.resizable(True, True)

        self.fonts_dir   = tk.StringVar(value="GoogleFonts_Offline")
        self.system_wide = tk.BooleanVar(value=True)
        self.all_fonts   = []          # list of font dicts
        self.var_checks  = {}          # family -> BooleanVar
        self._build_ui()
        self._try_auto_load()

    # ── Layout ────────────────────────────────────────────────────────────────

    def _build_ui(self):
        C = self.COLORS
        self.configure(bg=C["bg"])

        # ── Header ──────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=C["panel"], pady=18)
        hdr.pack(fill="x")

        tk.Label(hdr, text="🔤", font=("Segoe UI Emoji", 28), bg=C["panel"], fg=C["accent"]).pack(side="left", padx=(24, 8))
        title_frame = tk.Frame(hdr, bg=C["panel"])
        title_frame.pack(side="left")
        tk.Label(title_frame, text="Google Fonts", font=("Segoe UI", 18, "bold"), bg=C["panel"], fg=C["text"]).pack(anchor="w")
        tk.Label(title_frame, text="Offline Installer", font=("Segoe UI", 10), bg=C["panel"], fg=C["muted"]).pack(anchor="w")

        # Status badge
        if not is_windows():
            badge_txt, badge_col = "Mode Demo (Linux/Mac)", C["warning"]
        elif is_admin():
            badge_txt, badge_col = "Administrator ✓", C["success"]
        else:
            badge_txt, badge_col = "User Biasa", C["warning"]
        tk.Label(hdr, text=f"  {badge_txt}  ", font=("Segoe UI", 9, "bold"),
                 bg=badge_col, fg="white", padx=6, pady=3).pack(side="right", padx=20)

        # ── Toolbar: pilih folder ─────────────────────────────────────────
        toolbar = tk.Frame(self, bg=C["panel"], pady=10, padx=18)
        toolbar.pack(fill="x")

        tk.Label(toolbar, text="Folder Font:", font=("Segoe UI", 10), bg=C["panel"], fg=C["muted"]).pack(side="left")
        entry = tk.Entry(toolbar, textvariable=self.fonts_dir, font=("Consolas", 10),
                         bg=C["card"], fg=C["text"], insertbackground=C["text"],
                         relief="flat", bd=0, highlightthickness=1,
                         highlightcolor=C["accent"], highlightbackground=C["border"])
        entry.pack(side="left", fill="x", expand=True, padx=(8, 8), ipady=5)

        btn_browse = tk.Button(toolbar, text="📂 Browse", command=self._browse_folder,
                               bg=C["card"], fg=C["text"], relief="flat",
                               font=("Segoe UI", 9), cursor="hand2",
                               activebackground=C["border"], padx=10)
        btn_browse.pack(side="left", padx=(0, 8))

        btn_scan = tk.Button(toolbar, text="🔍 Scan", command=self._scan_fonts,
                             bg=C["accent"], fg="white", relief="flat",
                             font=("Segoe UI", 9, "bold"), cursor="hand2",
                             activebackground=C["accent2"], padx=14)
        btn_scan.pack(side="left")

        # ── Opsi install ──────────────────────────────────────────────────
        opt_frame = tk.Frame(self, bg=C["bg"], pady=6, padx=20)
        opt_frame.pack(fill="x")

        cb = tk.Checkbutton(opt_frame, text="Install untuk semua pengguna (System-wide, butuh admin)",
                            variable=self.system_wide, bg=C["bg"], fg=C["muted"],
                            selectcolor=C["card"], activebackground=C["bg"],
                            font=("Segoe UI", 9))
        cb.pack(side="left")

        # ── Daftar font ───────────────────────────────────────────────────
        list_frame = tk.Frame(self, bg=C["bg"])
        list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 6))

        # Header kolom
        col_hdr = tk.Frame(list_frame, bg=C["panel"], pady=6)
        col_hdr.pack(fill="x")

        tk.Label(col_hdr, text="  ☐  Pilih", width=8, font=("Segoe UI", 9, "bold"),
                 bg=C["panel"], fg=C["muted"], anchor="w").grid(row=0, column=0, padx=(8,0))
        tk.Label(col_hdr, text="Nama Font Family", font=("Segoe UI", 9, "bold"),
                 bg=C["panel"], fg=C["muted"], anchor="w").grid(row=0, column=1, sticky="w", padx=8)
        tk.Label(col_hdr, text="File", width=5, font=("Segoe UI", 9, "bold"),
                 bg=C["panel"], fg=C["muted"]).grid(row=0, column=2, padx=20)
        tk.Label(col_hdr, text="Status", width=14, font=("Segoe UI", 9, "bold"),
                 bg=C["panel"], fg=C["muted"]).grid(row=0, column=3, padx=10)
        col_hdr.columnconfigure(1, weight=1)

        # Canvas scroll
        canvas_frame = tk.Frame(list_frame, bg=C["card"], bd=0,
                                highlightthickness=1, highlightbackground=C["border"])
        canvas_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(canvas_frame, bg=C["card"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_frame = tk.Frame(self.canvas, bg=C["card"])

        self.scroll_frame.bind("<Configure>", lambda e: self.canvas.configure(
            scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scroll_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # mouse scroll
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(-1*(e.delta//120), "units"))

        self._show_placeholder("Pilih folder font dan klik Scan")

        # ── Footer ───────────────────────────────────────────────────────
        footer = tk.Frame(self, bg=C["panel"], pady=12, padx=18)
        footer.pack(fill="x", side="bottom")

        self.lbl_status = tk.Label(footer, text="Siap.", font=("Segoe UI", 9),
                                   bg=C["panel"], fg=C["muted"], anchor="w")
        self.lbl_status.pack(side="left", fill="x", expand=True)

        self.progress = ttk.Progressbar(footer, length=180, mode="determinate")
        self.progress.pack(side="left", padx=12)

        self.btn_select_all = tk.Button(footer, text="✔ Semua", command=self._select_all,
                                         bg=C["card"], fg=C["text"], relief="flat",
                                         font=("Segoe UI", 9), cursor="hand2", padx=10)
        self.btn_select_all.pack(side="left", padx=(0, 6))

        self.btn_deselect = tk.Button(footer, text="✗ Batal Pilih", command=self._deselect_all,
                                       bg=C["card"], fg=C["text"], relief="flat",
                                       font=("Segoe UI", 9), cursor="hand2", padx=10)
        self.btn_deselect.pack(side="left", padx=(0, 12))

        self.btn_install = tk.Button(footer, text="⬇  INSTALL FONT", command=self._install,
                                      bg=C["accent"], fg="white", relief="flat",
                                      font=("Segoe UI", 11, "bold"), cursor="hand2",
                                      padx=20, pady=4, activebackground=C["accent2"])
        self.btn_install.pack(side="right")

    # ── Helpers UI ────────────────────────────────────────────────────────────

    def _show_placeholder(self, msg: str):
        for w in self.scroll_frame.winfo_children():
            w.destroy()
        tk.Label(self.scroll_frame, text=msg, font=("Segoe UI", 11),
                 bg=self.COLORS["card"], fg=self.COLORS["muted"]).pack(pady=60)

    def _set_status(self, msg: str, color: str = None):
        self.lbl_status.config(text=msg, fg=color or self.COLORS["muted"])
        self.update_idletasks()

    # ── Actions ──────────────────────────────────────────────────────────────

    def _browse_folder(self):
        d = filedialog.askdirectory(title="Pilih folder font")
        if d:
            self.fonts_dir.set(d)
            self._scan_fonts()

    def _try_auto_load(self):
        if Path(self.fonts_dir.get()).exists():
            self._scan_fonts()

    def _scan_fonts(self):
        d = Path(self.fonts_dir.get())
        if not d.exists():
            self._show_placeholder(f"Folder tidak ditemukan: {d}")
            self._set_status("⚠ Folder tidak ditemukan.", self.COLORS["warning"])
            return

        self.all_fonts = scan_fonts(d)
        self.var_checks = {}

        for w in self.scroll_frame.winfo_children():
            w.destroy()

        if not self.all_fonts:
            self._show_placeholder("Tidak ada file font (.ttf/.otf) ditemukan.")
            self._set_status("Tidak ada font.", self.COLORS["warning"])
            return

        C = self.COLORS
        self.status_labels = {}

        for i, font in enumerate(self.all_fonts):
            row_bg = C["card"] if i % 2 == 0 else C["panel"]
            row = tk.Frame(self.scroll_frame, bg=row_bg)
            row.pack(fill="x")

            var = tk.BooleanVar(value=True)
            self.var_checks[font["family"]] = var

            cb = tk.Checkbutton(row, variable=var, bg=row_bg,
                                selectcolor=C["card"], activebackground=row_bg,
                                cursor="hand2")
            cb.grid(row=0, column=0, padx=(12, 4), pady=5)

            tk.Label(row, text=font["family"], font=("Segoe UI", 10),
                     bg=row_bg, fg=C["text"], anchor="w").grid(row=0, column=1, sticky="w", padx=4)

            tk.Label(row, text=str(font["count"]), font=("Segoe UI", 9),
                     bg=row_bg, fg=C["muted"]).grid(row=0, column=2, padx=20)

            status_lbl = tk.Label(row, text="Belum diinstall", font=("Segoe UI", 9),
                                   bg=row_bg, fg=C["muted"], width=14)
            status_lbl.grid(row=0, column=3, padx=10)
            self.status_labels[font["family"]] = status_lbl

            row.columnconfigure(1, weight=1)

        total_files = sum(f["count"] for f in self.all_fonts)
        self._set_status(f"✓ Ditemukan {len(self.all_fonts)} family, {total_files} file font.")

    def _select_all(self):
        for var in self.var_checks.values():
            var.set(True)

    def _deselect_all(self):
        for var in self.var_checks.values():
            var.set(False)

    def _install(self):
        selected = [f for f in self.all_fonts if self.var_checks.get(f["family"], tk.BooleanVar()).get()]
        if not selected:
            messagebox.showwarning("Peringatan", "Tidak ada font yang dipilih!")
            return

        total_files = sum(f["count"] for f in selected)
        confirm = messagebox.askyesno(
            "Konfirmasi Install",
            f"Akan menginstall {len(selected)} family ({total_files} file font).\n\n"
            f"{'System-wide (semua user)' if self.system_wide.get() else 'Hanya untuk user ini'}\n\nLanjutkan?"
        )
        if not confirm:
            return

        # Cek admin jika system-wide
        if self.system_wide.get() and is_windows() and not is_admin():
            ans = messagebox.askyesno(
                "Hak Administrator Dibutuhkan",
                "Install system-wide membutuhkan hak administrator.\n\n"
                "Klik Yes untuk restart sebagai administrator,\n"
                "atau No untuk install hanya untuk user ini."
            )
            if ans:
                run_as_admin()
                return
            else:
                self.system_wide.set(False)

        self.btn_install.config(state="disabled")
        self.progress["maximum"] = total_files
        self.progress["value"] = 0

        threading.Thread(target=self._do_install, args=(selected,), daemon=True).start()

    def _do_install(self, selected: list):
        C = self.COLORS
        done = 0
        ok_count = 0
        fail_count = 0
        system_wide = self.system_wide.get()

        for font in selected:
            family_ok = True
            for ffile in font["files"]:
                success, detail = install_font(ffile, system_wide)
                done += 1
                if success:
                    ok_count += 1
                else:
                    fail_count += 1
                    family_ok = False

                self.progress["value"] = done
                self._set_status(f"Menginstall: {font['family']} — {ffile.name}")
                self.update_idletasks()

            lbl = self.status_labels.get(font["family"])
            if lbl:
                if family_ok:
                    lbl.config(text="✓ Terinstall", fg=C["success"])
                else:
                    lbl.config(text="⚠ Sebagian gagal", fg=C["warning"])

        # Refresh cache font di Windows
        if is_windows():
            try:
                ctypes.windll.gdi32.AddFontResourceExW.restype = ctypes.c_int
            except Exception:
                pass

        self.btn_install.config(state="normal")
        self._set_status(f"✅ Selesai! {ok_count} file berhasil, {fail_count} gagal.")

        msg = f"Instalasi selesai!\n\n✓ Berhasil: {ok_count} file font\n"
        if fail_count:
            msg += f"✗ Gagal: {fail_count} file\n"
        msg += "\nRestart aplikasi (Word, dll.) untuk melihat font baru."
        messagebox.showinfo("Instalasi Selesai", msg)


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--fonts-dir", default="GoogleFonts_Offline")
    args, _ = parser.parse_known_args()

    app = FontInstallerApp()
    app.fonts_dir.set(args.fonts_dir)
    app._try_auto_load()
    app.mainloop()


if __name__ == "__main__":
    main()
