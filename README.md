💼 Dompet Aplikasi

Penyimpan & launcher aman untuk file .bat, installer .exe, ISO, ZIP, dan RAR

<img width="860" height="641" alt="image" src="https://github.com/user-attachments/assets/737b996b-81d3-460d-8b25-4418f1a2e3b2" />


📖 Deskripsi

Dompet Aplikasi adalah aplikasi desktop berbasis Python (Tkinter) yang berfungsi sebagai penyimpanan terenkripsi dan launcher untuk berbagai jenis berkas:

📄 File .BAT — script batch Windows
⚙️ Installer .EXE — termasuk auto-deteksi installer dalam folder
📦 ISO / ZIP / RAR — arsip yang bisa dibaca isinya dan diekstrak
Seluruh berkas disimpan dalam bentuk terenkripsi AES-128 (Fernet) dengan master password yang diderivasi melalui PBKDF2-HMAC-SHA256 (600.000 iterasi).

✨ Fitur Utama


Fitur	Keterangan

🔐 Enkripsi Fernet (AES)	Semua berkas dienkripsi sebelum disimpan ke vault
🔑 Master Password	Password di-hash (SHA-256 dari key terderivasi), salt acak tersimpan terpisah
🗂 3 Tab Kategori	FILE .BAT · INSTALLER .EXE · ISO / ZIP / RAR
📋 Upload Multi-File	Pilih banyak file sekaligus (Ctrl / Shift)
🔍 Pencarian Cepat	Filter langsung di setiap tab
📀 ISO Mount	Mount & baca isi via Mount-DiskImage bawaan Windows
🗜 ZIP	Baca isi & ekstrak via zipfile bawaan + cadangan PowerShell
📦 RAR	Baca isi & ekstrak via 7-Zip / WinRAR (terdeteksi otomatis)
🔒 Proteksi Folder	Vault disembunyikan (attrib +h +s) + ACL dikunci via icacls
⚙️ Pengaturan	Ganti Password (re-enkripsi otomatis) & Kunci Ulang Folder
🧪 Self-Test	Uji otomatis fungsi inti dengan flag --test
🖥️ Persyaratan Sistem
OS: Windows 10 / 11 (fitur mount ISO, ACL, dan attrib hanya ada di Windows)
Python: 3.8 atau lebih baru

🚀 Cara Penggunaan

Pertama kali dijalankan — aplikasi akan meminta Anda membuat Master Password (konfirmasi dua kali).
Berikutnya — masukkan password untuk membuka dompet.
defould user dan password ( admin | admin )
Pilih tab sesuai jenis berkas, lalu klik tombol ➕ Tambah untuk mengunggah file (bisa banyak sekaligus).
Gunakan kolom 🔍 Cari untuk memfilter daftar dengan cepat.
Pilih item lalu gunakan tombol aksi:
▶ Jalankan — menjalankan .bat / installer .exe
👀 Baca Isi — melihat isi arsip (double-click juga berfungsi)
📤 Extract... — mengekstrak arsip ke folder pilihan
💾 Ekstrak File — menyimpan salinan berkas asli
🗑 Hapus — menghapus item dari dompet

Menu ⚙ Pengaturan

🔑 Ganti Password — memverifikasi password lama, lalu mendekripsi dan mengenkripsi ulang semua berkas dengan kunci baru + salt baru.
🔒 Kunci Ulang Folder Vault — menerapkan kembali atribut hidden/system dan ACL pada folder vault.
