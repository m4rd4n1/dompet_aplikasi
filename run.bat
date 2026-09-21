@echo off
title Dompet Aplikasi - Run & Test
color 0B

echo ============================================
echo    DOMPET APLIKASI - TEST LOKAL
echo    By. Entong Betawi
echo ============================================
echo.

echo [1/3] Memeriksa dependencies...
pip install cryptography pillow pyinstaller
if errorlevel 1 (
    echo GAGAL install dependencies. Cek koneksi internet / Python.
    pause
    exit /b 1
)
echo        OK.
echo.

echo [2/3] Menjalankan pengujian otomatis...
python dompet_aplikasi.py --test
if errorlevel 1 (
    echo.
    echo PENGETESAN GAGAL! Periksa kembali kodenya.
    pause
    exit /b 1
)
echo.

echo [3/3] Menjalankan aplikasi utama...
python dompet_aplikasi.py

echo.
echo ============================================
echo    By. Entong Betawi
echo ============================================
pause