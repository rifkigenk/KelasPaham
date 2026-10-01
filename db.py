import sqlite3
import os
from flask import g, current_app

def get_db():
    """
    Fungsi untuk mendapatkan koneksi database pada permintaan (request) saat ini.
    Jika koneksi belum ada di objek global `g`, maka akan dibuat koneksi baru.
    """
    if 'db' not in g:
        # Membuka koneksi ke database SQLite
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        # Mengubah hasil query agar bisa diakses seperti dictionary (menggunakan nama kolom)
        g.db.row_factory = sqlite3.Row
        
        # Mengaktifkan foreign key constraint agar relasi antartabel terjaga dengan baik
        g.db.execute('PRAGMA foreign_keys = ON')
        
        # Set timeout agar jika ada beberapa akses bersamaan, database menunggu sejenak sebelum gagal
        g.db.execute('PRAGMA busy_timeout = 3000')

    return g.db

def close_db(e=None):
    """
    Fungsi ini dipanggil secara otomatis di akhir setiap permintaan (request)
    untuk menutup koneksi database jika ada.
    """
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    """
    Fungsi untuk menginisialisasi tabel-tabel dalam database
    menggunakan file schema.sql.
    """
    db = get_db()
    
    # Membaca isi file schema.sql
    with current_app.open_resource('schema.sql') as f:
        # Menjalankan script SQL untuk membuat tabel
        db.executescript(f.read().decode('utf8'))

def init_app(app):
    """
    Mendaftarkan fungsi close_db agar dipanggil saat aplikasi selesai memproses request.
    """
    app.teardown_appcontext(close_db)
