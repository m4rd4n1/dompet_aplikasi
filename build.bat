@echo off
title Dompet Aplikasi - Build EXE
color 0A

echo ============================================
echo    DOMPET APLIKASI - BUILD EXE
echo    By. Entong Betawi
echo ============================================
echo.

echo [1/3] Install / perbarui dependencies...
pip install --upgrade cryptography pillow pyinstaller
if errorlevel 1 (
    echo GAGAL install dependencies. Cek koneksi internet / Python.
    pause
    exit /b 1
)
echo        OK.
echo.

echo [2/3] Membangun DompetAplikasi.exe...
pyinstaller --onefile --noconsole --name "DompetAplikasi" dompet_aplikasi.py
if errorlevel 1 (
    echo Build GAGAL.
    pause
    exit /b 1
)
echo.

echo [3/3] Membersihkan direktori sisa build...
if exist build rmdir /s /q build
if exist DompetAplikasi.spec del /q DompetAplikasi.spec

echo ============================================
echo    Selesai! Berkas EXE siap digunakan:
echo    dist\DompetAplikasi.exe
echo    By. Entong Betawi
echo ============================================
pause