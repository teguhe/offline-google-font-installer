@echo off
echo ========================================
echo  Google Fonts Installer - Build EXE
echo ========================================
echo.

:: Cek apakah Python terinstall
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python tidak ditemukan!
    echo Pastikan Python 3.8+ sudah terinstall dan ada di PATH.
    pause
    exit /b 1
)

:: Install pyinstaller
echo [1/3] Menginstall PyInstaller...
pip install pyinstaller -q

:: Build exe
echo [2/3] Compiling installer.py...
pyinstaller --onefile --windowed ^
    --name "GoogleFontInstaller" ^
    --add-data "GoogleFonts_Offline;GoogleFonts_Offline" ^
    --hidden-import tkinter ^
    --hidden-import winreg ^
    installer.py

echo.
echo [3/3] Selesai!
echo.
echo File EXE ada di: dist\GoogleFontInstaller.exe
echo.
echo Salin file berikut ke PC target:
echo   - dist\GoogleFontInstaller.exe
echo   - GoogleFonts_Offline\  (folder font)
echo.
pause
