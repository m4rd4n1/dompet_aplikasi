# -*- coding: utf-8 -*-
"""
Dompet Aplikasi - Penyimpan & launcher file .bat, .exe, ISO, ZIP, RAR
Watermark: By. Entong Betawi
- File disimpan TERENKRIPSI (AES-Fernet)
- Tab: FILE .BAT | INSTALLER .EXE | ISO / ZIP / RAR
- Upload multi-file: bisa pilih banyak file sekaligus (Ctrl / Shift)
- Fitur Pencarian Cepat di Setiap Tab
- ISO : mount & baca isi (Mount-DiskImage bawaan Windows)
- ZIP : baca isi & extract (zipfile bawaan + cadangan PowerShell)
- RAR : baca isi & extract via 7-Zip / WinRAR yang terdeteksi otomatis
- Menu Pengaturan: Ganti Password & Kunci Ulang Folder
"""

import os
import sys
import base64
import hashlib
import shutil
import tempfile
import subprocess
import zipfile
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from cryptography.fernet import Fernet, InvalidToken

APP_NAME = "Dompet Aplikasi"
WATERMARK = "By. Entong Betawi"
APP_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "DompetAplikasi")
VAULT_DIR = os.path.join(APP_DIR, "vault")
KEY_SALT = os.path.join(APP_DIR, "vault.salt")
PW_FILE = os.path.join(APP_DIR, "vault.pw")
ICON_PATH = os.path.join(APP_DIR, "dompet_icon.png")

os.makedirs(VAULT_DIR, exist_ok=True)

ARSIPE_EXT = (".zip", ".rar", ".iso")


# ===================== KUNCI FOLDER (PROTEKSI) =====================

def kunci_folder_proteksi():
    """Sembunyikan + kunci ACL folder vault (hanya user Windows pemilik)."""
    try:
        os.system(f'attrib +h +s "{VAULT_DIR}"')
        os.system(f'attrib +h +s "{PW_FILE}"')
        os.system(f'attrib +h +s "{KEY_SALT}"')
        me = f"{os.environ.get('USERDOMAIN', '')}\\{os.environ.get('USERNAME', '')}"
        subprocess.run(["icacls", VAULT_DIR, "/inheritance:r"],
                       capture_output=True, creationflags=0x08000000)
        subprocess.run(["icacls", VAULT_DIR, "/grant", f"{me}:(OI)(CI)F", "SYSTEM:(OI)(CI)F"],
                       capture_output=True, creationflags=0x08000000)
    except Exception:
        pass


# ===================== IKON DOMPET (PIL) =====================

def buat_ikon_dompet():
    """Gambar ikon dompet dengan tulisan 'App Installer' di tengah. Return path PNG."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None
    if os.path.exists(ICON_PATH):
        return ICON_PATH

    size = 256
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([16, 60, 240, 220], radius=28, fill=(139, 94, 60, 255))
    d.rounded_rectangle([16, 40, 240, 96], radius=24, fill=(160, 112, 74, 255))
    d.rounded_rectangle([150, 120, 240, 190], radius=18, fill=(120, 80, 50, 255))
    d.ellipse([212, 142, 236, 166], fill=(255, 210, 100, 255))
    d.line([28, 106, 228, 106], fill=(100, 66, 40, 255), width=3)

    try:
        font = ImageFont.truetype("arialbd.ttf", 34)
        font2 = ImageFont.truetype("arialbd.ttf", 26)
    except Exception:
        font = font2 = ImageFont.load_default()

    def center(draw_obj, txt, fnt, y):
        bb = draw_obj.textbbox((0, 0), txt, font=fnt)
        draw_obj.text(((size - (bb[2] - bb[0])) // 2, y), txt, font=fnt, fill=(255, 255, 255, 255))

    center(d, "App", font, 116)
    center(d, "Installer", font2, 158)
    img.save(ICON_PATH)
    return ICON_PATH


def pasang_ikon_aplikasi(window: tk.Tk):
    path = buat_ikon_dompet()
    if path:
        try:
            icon = tk.PhotoImage(file=path)
            window.iconphoto(True, icon)
            window._icon_ref = icon
        except Exception:
            pass


# ===================== PROTEKSI / ENKRIPSI =====================

def derive_key(password: str, salt: bytes) -> bytes:
    return base64.urlsafe_b64encode(
        hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000)
    )


def load_vault(password: str) -> Fernet:
    if os.path.exists(KEY_SALT):
        with open(KEY_SALT, "rb") as f:
            salt = f.read()
    else:
        salt = os.urandom(16)
        with open(KEY_SALT, "wb") as f:
            f.write(salt)
    key = derive_key(password, salt)
    pw_hash = hashlib.sha256(key).hexdigest()
    if os.path.exists(PW_FILE):
        with open(PW_FILE, "r") as f:
            if f.read().strip() != pw_hash:
                raise ValueError("Password salah!")
    else:
        with open(PW_FILE, "w") as f:
            f.write(pw_hash)
    return Fernet(key)


def encrypt_and_store(fernet: Fernet, src_path: str) -> str:
    """Enkripsi file dan simpan ke vault."""
    with open(src_path, "rb") as f:
        data = f.read()
    token = fernet.encrypt(data)
    safe_name = hashlib.sha256(os.path.basename(src_path).encode()).hexdigest()[:16]
    ext = os.path.splitext(src_path)[1].lower()
    enc_name = safe_name + ext + ".enc"
    with open(os.path.join(VAULT_DIR, enc_name), "wb") as f:
        f.write(token)
    return enc_name


def decrypt_to_temp(fernet: Fernet, enc_name: str, dest_dir: str) -> str:
    with open(os.path.join(VAULT_DIR, enc_name), "rb") as f:
        data = fernet.decrypt(f.read())
    dest = os.path.join(dest_dir, enc_name[:-4])
    with open(dest, "wb") as f:
        f.write(data)
    return dest


def load_meta() -> dict:
    meta_path = os.path.join(VAULT_DIR, "meta.json")
    if os.path.exists(meta_path):
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}


def save_meta(meta: dict):
    with open(os.path.join(VAULT_DIR, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


# ===================== GANTI PASSWORD =====================

def ganti_password(password_lama: str, password_baru: str) -> None:
    """Verifikasi password lama, dekripsi semua file, enkripsi ulang dengan kunci baru."""
    load_vault(password_lama)  # ValueError jika salah
    with open(KEY_SALT, "rb") as f:
        salt_lama = f.read()
    key_lama = derive_key(password_lama, salt_lama)

    isi = {}
    for fn in os.listdir(VAULT_DIR):
        if fn.endswith(".enc"):
            with open(os.path.join(VAULT_DIR, fn), "rb") as f:
                isi[fn] = Fernet(key_lama).decrypt(f.read())

    salt_baru = os.urandom(16)
    key_baru = derive_key(password_baru, salt_baru)
    fernet_baru = Fernet(key_baru)

    for fn, data in isi.items():
        with open(os.path.join(VAULT_DIR, fn), "wb") as f:
            f.write(fernet_baru.encrypt(data))

    with open(KEY_SALT, "wb") as f:
        f.write(salt_baru)
    with open(PW_FILE, "w") as f:
        f.write(hashlib.sha256(key_baru).hexdigest())
    kunci_folder_proteksi()


# ===================== AUTO-CARI EXE =====================

def find_installer_in_folder(folder: str):
    """Cari file installer .exe dalam folder (prioritas 'setup'/'install')."""
    if not os.path.isdir(folder):
        return None
    exes = [os.path.join(root, fn)
            for root, _, files in os.walk(folder)
            for fn in files if fn.lower().endswith(".exe")]
    if not exes:
        return None

    def priority(p):
        name = os.path.basename(p).lower()
        score = 0
        if "setup" in name:
            score -= 3
        if "install" in name:
            score -= 2
        score += p.count(os.sep)
        return score

    exes.sort(key=priority)
    return exes[0]


# ===================== DETEKSI TOOLS ARSIP (WinRAR / 7-Zip) =====================

def cari_tool_arsip():
    """Cari tool untuk RAR: 7z.exe (7-Zip) atau WinRAR/UnRAR. Return (path, jenis)."""
    kandidat = []
    program_dirs = [
        os.environ.get("ProgramFiles", r"C:\Program Files"),
        os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", ""),
    ]
    for base in program_dirs:
        if not base:
            continue
        kandidat += [
            os.path.join(base, "7-Zip", "7z.exe"),
            os.path.join(base, "WinRAR", "WinRAR.exe"),
            os.path.join(base, "WinRAR", "UnRAR.exe"),
        ]
    for nama in ("7z.exe", "7za.exe", "WinRAR.exe", "UnRAR.exe"):
        path_ = shutil.which(nama)
        if path_:
            kandidat.append(path_)

    for p in kandidat:
        if os.path.isfile(p):
            jenis = "7z" if "7z" in os.path.basename(p).lower() else "winrar"
            return p, jenis
    return None, None


def _rar_list(tool, jenis, path):
    hasil = []
    if jenis == "7z":
        r = subprocess.run([tool, "l", "-ba", path],
                           capture_output=True, text=True, errors="replace", timeout=300)
        for line in r.stdout.splitlines():
            if len(line) > 53:
                nama = line[53:].strip()
                if nama:
                    hasil.append(nama)
    else:
        r = subprocess.run([tool, "lb", path],
                           capture_output=True, text=True, errors="replace", timeout=300)
        hasil = [l.strip() for l in r.stdout.splitlines() if l.strip()]
    return hasil


def _rar_extract(tool, jenis, path, dest):
    os.makedirs(dest, exist_ok=True)
    if jenis == "7z":
        subprocess.run([tool, "x", f"-o{dest}", "-y", path],
                       capture_output=True, timeout=1800, check=True)
    else:
        subprocess.run([tool, "x", "-y", path, dest + "\\"],
                       capture_output=True, timeout=1800, check=True)


# ===================== MOUNT / UNMOUNT ISO =====================

def mount_iso(path: str):
    ps = (f"$img = Mount-DiskImage -ImagePath '{path}' -PassThru; "
          f"($img | Get-Volume).DriveLetter")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=120)
        letter = r.stdout.strip().upper()
        return f"{letter}:\\" if letter else None
    except Exception:
        return None


def unmount_iso(drive: str):
    letter = drive[0]
    ps = f"Dismount-DiskImage -DevicePath (Get-Volume -DriveLetter {letter}).Path"
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                       capture_output=True, timeout=60)
    except Exception:
        pass


# ===================== BACA & EXTRACT ISO / ZIP / RAR =====================

def baca_isi_arsipe(path: str):
    ext = os.path.splitext(path)[1].lower()

    if ext == ".zip":
        try:
            with zipfile.ZipFile(path) as z:
                return z.namelist(), "ZIP"
        except zipfile.BadZipFile:
            ps = ("Add-Type -AssemblyName System.IO.Compression.FileSystem; "
                  f"[System.IO.Compression.ZipFile]::OpenRead('{path}').Entries.FullName")
            r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                               capture_output=True, text=True, errors="replace", timeout=120)
            daftar = [l.strip() for l in r.stdout.splitlines() if l.strip()]
            if daftar:
                return daftar, "ZIP"
            raise RuntimeError("File ZIP tidak dapat dibaca (mungkin rusak).")

    if ext == ".rar":
        tool, jenis = cari_tool_arsip()
        if not tool:
            raise RuntimeError(
                "Tidak ada tool RAR di PC ini.\n\n"
                "Solusi:\n"
                "1. Install 7-Zip (gratis): https://www.7-zip.org\n"
                "2. Install WinRAR: https://www.win-rar.com")
        daftar = _rar_list(tool, jenis, path)
        if not daftar:
            raise RuntimeError("Gagal membaca daftar isi RAR.")
        return daftar, f"RAR ({os.path.basename(tool)})"

    if ext == ".iso":
        drive = mount_iso(path)
        if not drive:
            raise RuntimeError("Gagal me-mount ISO.")
        isi = []
        for item in os.listdir(drive):
            p = os.path.join(drive, item)
            isi.append(("[DIR]  " + item) if os.path.isdir(p) else item)
        return isi, f"ISO (ter-mount di {drive})"

    raise ValueError("Format tidak didukung.")


def extract_arsipe(path: str, dest: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    os.makedirs(dest, exist_ok=True)

    if ext == ".zip":
        try:
            with zipfile.ZipFile(path) as z:
                z.extractall(dest)
        except zipfile.BadZipFile:
            subprocess.run(["powershell", "-NoProfile", "-Command",
                            f"Expand-Archive -LiteralPath '{path}' -DestinationPath '{dest}' -Force"],
                           capture_output=True, timeout=1800, check=True)

    elif ext == ".rar":
        tool, jenis = cari_tool_arsip()
        if not tool:
            raise RuntimeError("Tidak ada tool RAR di PC ini. Install 7-Zip terlebih dahulu.")
        _rar_extract(tool, jenis, path, dest)

    elif ext == ".iso":
        drive = mount_iso(path)
        if not drive:
            raise RuntimeError("Gagal me-mount ISO.")
        for item in os.listdir(drive):
            s = os.path.join(drive, item)
            d = os.path.join(dest, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
        unmount_iso(drive)
        return dest

    return dest


def daftar_file_rekursif(folder: str):
    hasil = []
    jumlah_file = 0
    total_ukuran = 0
    for root, dirs, files in os.walk(folder):
        rel_base = os.path.relpath(root, folder)
        for d in sorted(dirs):
            rel = d if rel_base == "." else os.path.join(rel_base, d)
            hasil.append("[DIR]    " + rel)
        for f in sorted(files):
            p = os.path.join(root, f)
            ukuran = os.path.getsize(p)
            jumlah_file += 1
            total_ukuran += ukuran
            rel = f if rel_base == "." else os.path.join(rel_base, f)
            hasil.append(f"{ukuran:>12,} B    {rel}")
    ket = f"{jumlah_file} file, total {total_ukuran / 1024 / 1024:.1f} MB"
    return hasil, ket


# ===================== DIALOG GANTI PASSWORD =====================

class GantiPasswordDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title(APP_NAME + " - Ganti Password")
        self.geometry("420x250")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        frm = ttk.Frame(self, padding=20)
        frm.pack(fill="both", expand=True)
        ttk.Label(frm, text="🔑 Ganti Password Dompet", font=("Segoe UI", 12, "bold")).pack(pady=(0, 10))
        
        ttk.Label(frm, text="Password lama:").pack(anchor="w")
        self.e_lama = ttk.Entry(frm, show="●", width=35)
        self.e_lama.pack(pady=(2, 6))
        self.e_lama.focus_set()

        ttk.Label(frm, text="Password baru (min. 4 karakter):").pack(anchor="w")
        self.e_baru = ttk.Entry(frm, show="●", width=35)
        self.e_baru.pack(pady=(2, 6))

        ttk.Label(frm, text="Ulangi password baru:").pack(anchor="w")
        self.e_baru2 = ttk.Entry(frm, show="●", width=35)
        self.e_baru2.pack(pady=(2, 12))

        btns = ttk.Frame(frm)
        btns.pack()
        ttk.Button(btns, text="Simpan", command=self.simpan, width=12).pack(side="left", padx=5)
        ttk.Button(btns, text="Batal", command=self.destroy, width=12).pack(side="left", padx=5)

    def simpan(self):
        lama, baru, baru2 = self.e_lama.get(), self.e_baru.get(), self.e_baru2.get()
        if not lama or not baru:
            messagebox.showwarning(APP_NAME, "Semua kolom wajib diisi.", parent=self)
            return
        if len(baru) < 4:
            messagebox.showwarning(APP_NAME, "Password baru minimal 4 karakter.", parent=self)
            return
        if baru != baru2:
            messagebox.showwarning(APP_NAME, "Konfirmasi password baru tidak cocok.", parent=self)
            return
        try:
            ganti_password(lama, baru)
            messagebox.showinfo(APP_NAME, "Password berhasil diganti!\nSemua file telah dienkripsi ulang dengan kunci baru.", parent=self)
            self.destroy()
        except (ValueError, InvalidToken):
            messagebox.showerror(APP_NAME, "Password lama salah!", parent=self)
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Gagal mengganti password: {e}", parent=self)


# ===================== DIALOG ISI ARSIP =====================

class IsiArsipDialog(tk.Toplevel):
    def __init__(self, parent, nama: str, daftar: list, keterangan: str):
        super().__init__(parent)
        self.title(f"Isi Arsip: {nama} ({keterangan})")
        self.geometry("600x450")
        self.transient(parent)

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)
        frm.columnconfigure(0, weight=1)
        frm.rowconfigure(0, weight=1)

        tree = ttk.Treeview(frm, columns=("item",), show="headings")
        tree.heading("item", text=f"Daftar Item ({len(daftar)} ditemukan)")
        tree.column("item", width=540)
        tree.grid(row=0, column=0, sticky="nsew")
        
        sb = ttk.Scrollbar(frm, orient="vertical", command=tree.yview)
        sb.grid(row=0, column=1, sticky="ns")
        tree.configure(yscrollcommand=sb.set)

        for item in daftar:
            tree.insert("", "end", values=(item,))

        ttk.Button(frm, text="Tutup", command=self.destroy, width=15).grid(row=1, column=0, columnspan=2, pady=10)


# ===================== GUI UTAMA =====================

class DompetApp(tk.Tk):
    def __init__(self, fernet: Fernet):
        super().__init__()
        self.fernet = fernet
        self.meta = load_meta()
        self.title(f"{APP_NAME}  |  {WATERMARK}")
        self.geometry("860x600")
        self.minsize(700, 500)
        pasang_ikon_aplikasi(self)

        try:
            style = ttk.Style(self)
            style.theme_use("clam")
        except tk.TclError:
            pass

        # Menu Pengaturan Atas
        menubar = tk.Menu(self)
        menu_atr = tk.Menu(menubar, tearoff=0)
        menu_atr.add_command(label="🔑 Ganti Password...", command=lambda: GantiPasswordDialog(self))
        menu_atr.add_separator()
        menu_atr.add_command(label="🔒 Kunci Ulang Folder Vault", command=self.kunci_ulang)
        menu_atr.add_separator()
        menu_atr.add_command(label="Keluar Aplikasi", command=self.destroy)
        menubar.add_cascade(label="⚙ Pengaturan", menu=menu_atr)
        self.config(menu=menubar)

        # Header Aplikasi
        header = ttk.Frame(self, padding=15)
        header.pack(fill="x")
        
        ikon = buat_ikon_dompet()
        if ikon:
            try:
                from PIL import Image, ImageTk
                self._header_icon = ImageTk.PhotoImage(Image.open(ikon).resize((64, 64)))
                tk.Label(header, image=self._header_icon).pack(side="left", padx=(0, 15))
            except Exception:
                pass
                
        judul = ttk.Frame(header)
        judul.pack(side="left", fill="x", expand=True)
        ttk.Label(judul, text=f"💼 {APP_NAME}", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(judul, text="Penyimpanan aman terenkripsi untuk berkas batch, installer, dan arsip digital",
                  foreground="#666666", font=("Segoe UI", 10)).pack(anchor="w")

        # Notebook Tab
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(0, 10))
        self.notebook.add(self._make_tab("bat"), text="   📄 FILE .BAT   ")
        self.notebook.add(self._make_tab("exe"), text="   ⚙️ INSTALLER .EXE   ")
        self.notebook.add(self._make_tab("arsip"), text="   📦 ISO / ZIP / RAR   ")

        # Status Bar Bawah
        self.status_var = tk.StringVar(value="Status: Siap")
        status_bar = ttk.Frame(self, padding=(12, 6))
        status_bar.pack(fill="x", side="bottom")
        ttk.Label(status_bar, textvariable=self.status_var, font=("Segoe UI", 9)).pack(side="left")
        ttk.Label(status_bar, text=WATERMARK, foreground="#8B5E3C", font=("Segoe UI", 9, "bold")).pack(side="right")

        self.refresh_lists()

    def kunci_ulang(self):
        kunci_folder_proteksi()
        messagebox.showinfo(APP_NAME, "Folder penyimpanan berhasil dikunci ulang dengan aman.")

    def _make_tab(self, ftype: str) -> ttk.Frame:
        frame = ttk.Frame(self.notebook, padding=12)
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(1, weight=1)

        # Search Bar Atas Tab
        search_frm = ttk.Frame(frame)
        search_frm.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        ttk.Label(search_frm, text="🔍 Cari:").pack(side="left", padx=(0, 5))
        
        search_var = tk.StringVar()
        setattr(self, f"search_{ftype}", search_var)
        search_var.trace_add("write", lambda *args, ft=ftype: self.filter_list(ft))
        
        entry_cari = ttk.Entry(search_frm, textvariable=search_var, width=30)
        entry_cari.pack(side="left", fill="x", expand=True)

        # Tabel Data
        tree = ttk.Treeview(frame, columns=("name",), show="headings", height=12)
        judul_kolom = {"bat": "Nama Berkas Batch (.bat)", 
                       "exe": "Nama Installer / Direktori Aplikasi",
                       "arsip": "Nama Arsip / ISO / ZIP / RAR"}[ftype]
        tree.heading("name", text=judul_kolom)
        tree.column("name", width=620)
        tree.grid(row=1, column=0, sticky="nsew")
        
        sb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        sb.grid(row=1, column=1, sticky="ns")
        tree.configure(yscrollcommand=sb.set)

        # Tombol Aksi Bawah
        btns = ttk.Frame(frame)
        btns.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        if ftype == "bat":
            ttk.Button(btns, text="➕ Tambah .BAT", command=self.add_bat).pack(side="left", padx=(0, 4))
            ttk.Button(btns, text="▶ Jalankan", command=lambda: self.run_item(ftype)).pack(side="left", padx=4)
        elif ftype == "exe":
            ttk.Button(btns, text="➕ Tambah .EXE", command=self.add_exe).pack(side="left", padx=(0, 4))
            ttk.Button(btns, text="📁 Tambah Folder", command=self.add_folder).pack(side="left", padx=4)
            ttk.Button(btns, text="▶ Jalankan / Install", command=lambda: self.run_item(ftype)).pack(side="left", padx=4)
        else:
            ttk.Button(btns, text="➕ Tambah Arsip", command=self.add_arsip).pack(side="left", padx=(0, 4))
            ttk.Button(btns, text="👀 Baca Isi", command=self.baca_arsip).pack(side="left", padx=4)
            ttk.Button(btns, text="📤 Extract...", command=self.extract_arsip_gui).pack(side="left", padx=4)

        ttk.Button(btns, text="🗑 Hapus", command=lambda: self.delete_item(ftype)).pack(side="right", padx=4)
        ttk.Button(btns, text="💾 Ekstrak File", command=lambda: self.extract_item(ftype)).pack(side="right", padx=4)

        tree.bind("<Double-1>", lambda e: self.baca_arsip() if ftype == "arsip" else self.run_item(ftype))
        setattr(self, f"tree_{ftype}", tree)
        return frame

    def items_of(self, ftype):
        return {k: v for k, v in self.meta.items() if v.get("type") == ftype}

    def refresh_lists(self):
        total_items = len(self.meta)
        for ftype in ("bat", "exe", "arsip"):
            self.filter_list(ftype)
        self.status_var.set(f"Total Berkas Tersimpan: {total_items} item di dalam Vault")

    def filter_list(self, ftype):
        tree = getattr(self, f"tree_{ftype}")
        search_var = getattr(self, f"search_{ftype}")
        keyword = search_var.get().lower()

        tree.delete(*tree.get_children())
        for enc, info in self.items_of(ftype).items():
            label = info["display"]
            if info.get("from_folder"):
                label += "    (dari folder)"
            if keyword in label.lower():
                tree.insert("", "end", iid=enc, values=(label,))

    def selected(self, ftype):
        sel = getattr(self, f"tree_{ftype}").selection()
        return sel[0] if sel else None

    def _tambah_banyak(self, paths, ftype, keterangan=""):
        berhasil, gagal = [], []
        for path in paths:
            try:
                enc = encrypt_and_store(self.fernet, path)
                self.meta[enc] = {"display": os.path.basename(path), "type": ftype}
                berhasil.append(os.path.basename(path))
            except Exception as e:
                gagal.append(f"{os.path.basename(path)}: {e}")
        if berhasil or gagal:
            save_meta(self.meta)
            kunci_folder_proteksi()
            self.refresh_lists()
        if gagal:
            messagebox.showwarning(APP_NAME, f"{len(berhasil)} file berhasil disimpan, {len(gagal)} gagal:\n\n" + "\n".join(gagal))
        elif berhasil:
            messagebox.showinfo(APP_NAME, f"{len(berhasil)} file {keterangan} berhasil disimpan secara terenkripsi.")

    def add_bat(self):
        paths = filedialog.askopenfilenames(title="Pilih file .BAT", filetypes=[("Batch files", "*.bat"), ("Semua file", "*.*")])
        if not paths: return
        valid = [p for p in paths if p.lower().endswith(".bat")]
        if not valid: return
        self._tambah_banyak(valid, "bat", ".bat")

    def add_exe(self):
        paths = filedialog.askopenfilenames(title="Pilih installer .EXE", filetypes=[("Executable", "*.exe"), ("Semua file", "*.*")])
        if not paths: return
        valid = [p for p in paths if p.lower().endswith(".exe")]
        if not valid: return
        self._tambah_banyak(valid, "exe", "installer")

    def add_folder(self):
        folder = filedialog.askdirectory(title="Pilih folder berisi installer")
        if not folder: return
        found = find_installer_in_folder(folder)
        if not found:
            messagebox.showwarning(APP_NAME, "Tidak ditemukan file .exe di dalam folder tersebut.")
            return
        try:
            enc = encrypt_and_store(self.fernet, found)
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Gagal menyimpan installer:\n{e}")
            return
        self.meta[enc] = {"display": os.path.basename(found), "type": "exe", "from_folder": True, "source_folder": folder}
        save_meta(self.meta)
        kunci_folder_proteksi()
        self.refresh_lists()
        messagebox.showinfo(APP_NAME, f"Installer ditemukan dan disimpan:\n{found}")

    def add_arsip(self):
        paths = filedialog.askopenfilenames(title="Pilih ISO / ZIP / RAR", filetypes=[("Arsip & ISO", "*.iso *.zip *.rar"), ("Semua file", "*.*")])
        if not paths: return
        valid = [p for p in paths if p.lower().endswith(ARSIPE_EXT)]
        if not valid: return
        self._tambah_banyak(valid, "arsip", "arsip")

    def _dekripsi_arsip_terpilih(self):
        enc = self.selected("arsip")
        if not enc:
            messagebox.showwarning(APP_NAME, "Pilih berkas arsip terlebih dahulu dari daftar.")
            return None, None
        tmpdir = tempfile.mkdtemp(prefix="dompet_arsip_")
        try:
            path = decrypt_to_temp(self.fernet, enc, tmpdir)
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Gagal mendekripsi berkas:\n{e}")
            shutil.rmtree(tmpdir, ignore_errors=True)
            return None, None
        return path, tmpdir

    def baca_arsip(self):
        path, tmpdir = self._dekripsi_arsip_terpilih()
        if not path: return
        try:
            ekstrak_dir = os.path.join(tmpdir, "isi")
            extract_arsipe(path, ekstrak_dir)
            daftar, ket = daftar_file_rekursif(ekstrak_dir)
            if not daftar:
                messagebox.showwarning(APP_NAME, "Arsip kosong.")
                return
            dlg = IsiArsipDialog(self, os.path.basename(path), daftar, f"{os.path.splitext(path)[1].upper()[1:]} - {ket}")
            self.wait_window(dlg)
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Gagal membaca isi arsip:\n{e}")
        finally:
            try:
                if path.lower().endswith(".iso"):
                    subprocess.run(["powershell", "-NoProfile", "-Command", f"Dismount-DiskImage -ImagePath '{path}'"], capture_output=True, timeout=60)
                shutil.rmtree(tmpdir, ignore_errors=True)
            except Exception:
                pass

    def extract_arsip_gui(self):
        path, tmpdir = self._dekripsi_arsip_terpilih()
        if not path: return
        dest = filedialog.askdirectory(title=f"Pilih folder tujuan ekstraksi {os.path.basename(path)}")
        if not dest:
            shutil.rmtree(tmpdir, ignore_errors=True)
            return
        try:
            hasil = extract_arsipe(path, dest)
            messagebox.showinfo(APP_NAME, f"Ekstraksi selesai:\n{hasil}")
            os.startfile(hasil)
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Gagal mengekstrak arsip:\n{e}")
        finally:
            if not path.lower().endswith(".iso"):
                shutil.rmtree(tmpdir, ignore_errors=True)

    def extract_item(self, ftype):
        enc = self.selected(ftype)
        if not enc:
            messagebox.showwarning(APP_NAME, "Pilih berkas terlebih dahulu.")
            return
        info = self.meta[enc]
        dest = filedialog.asksaveasfilename(initialfile=info["display"], defaultextension=os.path.splitext(info["display"])[1])
        if not dest: return
        tmp = decrypt_to_temp(self.fernet, enc, tempfile.gettempdir())
        shutil.copyfile(tmp, dest)
        try:
            os.remove(tmp)
        except OSError:
            pass
        messagebox.showinfo(APP_NAME, f"Berkas berhasil diekstrak ke:\n{dest}")

    def run_item(self, ftype):
        enc = self.selected(ftype)
        if not enc:
            messagebox.showwarning(APP_NAME, "Pilih item terlebih dahulu.")
            return
        info = self.meta[enc]

        if ftype == "bat":
            tmpdir = tempfile.mkdtemp(prefix="dompet_")
            try:
                bat = decrypt_to_temp(self.fernet, enc, tmpdir)
                subprocess.Popen(["cmd", "/c", bat, "&", "rd", "/s", "/q", tmpdir],
                                 cwd=tmpdir, creationflags=subprocess.CREATE_NEW_CONSOLE)
            except Exception as e:
                messagebox.showerror(APP_NAME, f"Gagal menjalankan script: {e}")
            return

        exe_path = decrypt_to_temp(self.fernet, enc, tempfile.gettempdir())
        folder = info.get("source_folder", "")
        if info.get("from_folder") and folder and os.path.isdir(folder):
            candidate = find_installer_in_folder(folder)
            if candidate and os.path.basename(candidate).lower() != os.path.basename(exe_path).lower():
                exe_path = candidate
        try:
            if exe_path.lower().endswith(".exe"):
                subprocess.Popen(["powershell", "-WindowStyle", "Hidden", "-Command",
                                  f"Start-Process -FilePath '{exe_path}' -Verb RunAs"])
                messagebox.showinfo(APP_NAME, f"Memulai installer:\n{exe_path}")
            else:
                subprocess.Popen(["cmd", "/c", "start", "", exe_path])
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Gagal menjalankan installer: {e}")

    def delete_item(self, ftype):
        enc = self.selected(ftype)
        if not enc: return
        if not messagebox.askyesno(APP_NAME, "Apakah Anda yakin ingin menghapus item ini dari dompet?"):
            return
        try:
            os.remove(os.path.join(VAULT_DIR, enc))
        except FileNotFoundError:
            pass
        del self.meta[enc]
        save_meta(self.meta)
        self.refresh_lists()


# ===================== LAYAR PASSWORD =====================

class PasswordDialog(tk.Tk):
    def __init__(self):
        super().__init__()
        first_time = not os.path.exists(PW_FILE)
        self.title(APP_NAME + " - " + ("Buat Password Baru" if first_time else "Autentikasi Diperlukan"))
        self.geometry("440x220")
        self.resizable(False, False)
        self.fernet = None
        pasang_ikon_aplikasi(self)

        frm = ttk.Frame(self, padding=20)
        frm.pack(fill="both", expand=True)
        
        ttk.Label(frm, text=("💼 Buat Master Password Baru" if first_time else "💼 Masukkan Password Dompet"),
                  font=("Segoe UI", 11, "bold")).pack(pady=(0, 10))
        
        self.pw = ttk.Entry(frm, show="●", width=36)
        self.pw.pack(pady=4)
        
        if first_time:
            ttk.Label(frm, text="Ulangi password:").pack(pady=(6, 0))
            self.pw2 = ttk.Entry(frm, show="●", width=36)
            self.pw2.pack(pady=4)
            
        self.pw.focus_set()
        self.pw.bind("<Return>", lambda e: self.submit())
        
        ttk.Button(frm, text="Buka Dompet", command=self.submit, width=15).pack(pady=10)
        ttk.Label(self, text=WATERMARK, foreground="#8B5E3C", font=("Segoe UI", 9, "bold")).pack(anchor="e", padx=15, pady=(0, 5))

    def submit(self):
        try:
            pw = self.pw.get()
            if not pw:
                messagebox.showwarning(APP_NAME, "Password tidak boleh kosong.")
                return
            if hasattr(self, "pw2") and pw != self.pw2.get():
                messagebox.showwarning(APP_NAME, "Konfirmasi password tidak cocok.")
                return
            self.fernet = load_vault(pw)
            self.destroy()
        except ValueError as e:
            messagebox.showerror(APP_NAME, str(e))
        except Exception as e:
            messagebox.showerror(APP_NAME, f"Terjadi kesalahan: {e}")


# ===================== PENGETESAN OTOMATIS =====================

def self_test():
    global VAULT_DIR, KEY_SALT, PW_FILE
    vault_asli = VAULT_DIR
    vault_test = tempfile.mkdtemp(prefix="dompet_test_")
    VAULT_DIR = os.path.join(vault_test, "vault")
    KEY_SALT = os.path.join(vault_test, "vault.salt")
    PW_FILE = os.path.join(vault_test, "vault.pw")
    os.makedirs(VAULT_DIR, exist_ok=True)

    ok = True
    try:
        ikon = buat_ikon_dompet()
        print(f"[TEST 1] Ikon dompet: {'OK' if ikon else 'GAGAL'}")
        ok &= bool(ikon)

        fernet = load_vault("test123")
        test_file = os.path.join(vault_test, "dompet_test.bat")
        with open(test_file, "w") as f:
            f.write("@echo off\necho Halo dari Dompet Aplikasi!\npause\n")
        enc = encrypt_and_store(fernet, test_file)
        hasil = open(decrypt_to_temp(fernet, enc, vault_test)).read()
        print(f"[TEST 2] Enkripsi/dekripsi .bat: {'OK' if 'Halo' in hasil else 'GAGAL'}")
        ok &= "Halo" in hasil

        ganti_password("test123", "test456")
        fernet_baru = load_vault("test456")
        hasil2 = open(decrypt_to_temp(fernet_baru, enc, vault_test)).read()
        print(f"[TEST 3] Ganti password + re-enkripsi: {'OK' if 'Halo' in hasil2 else 'GAGAL'}")
        ok &= "Halo" in hasil2

        folder_test = os.path.join(vault_test, "folder_test")
        os.makedirs(folder_test, exist_ok=True)
        open(os.path.join(folder_test, "setup.exe"), "w").close()
        ditemukan = find_installer_in_folder(folder_test)
        hasil4 = ditemukan and os.path.basename(ditemukan) == "setup.exe"
        print(f"[TEST 4] Auto-cari installer: {'OK' if hasil4 else 'GAGAL'}")
        ok &= bool(hasil4)

        zip_path = os.path.join(vault_test, "tes.zip")
        with zipfile.ZipFile(zip_path, "w") as z:
            z.writestr("folder_demo/isi.txt", "Halo ZIP Dompet!")
        daftar, _ = baca_isi_arsipe(zip_path)
        dest = os.path.join(vault_test, "hasil_zip")
        extract_arsipe(zip_path, dest)
        file_hasil = os.path.join(dest, "folder_demo", "isi.txt")
        ok5 = ("folder_demo/isi.txt" in daftar) and os.path.exists(file_hasil)
        print(f"[TEST 5] ZIP baca isi + extract: {'OK' if ok5 else 'GAGAL'}")
        ok &= ok5

        tool, jenis = cari_tool_arsip()
        print(f"[TEST 6] Tool RAR: {('OK -> ' + tool) if tool else 'Tidak terdeteksi (opsional untuk file RAR)'}")

    except Exception as e:
        print(f"[TEST] ERROR: {e}")
        ok = False
    finally:
        shutil.rmtree(vault_test, ignore_errors=True)
        VAULT_DIR = vault_asli

    print("=" * 50)
    print(f"HASIL PENGETESAN: {'SEMUA LOLOS ✔' if ok else 'ADA YANG GAGAL ✘'}")
    return ok


def main():
    if "--test" in sys.argv:
        sys.exit(0 if self_test() else 1)
    dlg = PasswordDialog()
    dlg.mainloop()
    if dlg.fernet is None:
        sys.exit(0)
    app = DompetApp(dlg.fernet)
    kunci_folder_proteksi()
    app.mainloop()


if __name__ == "__main__":
    main()