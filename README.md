# KelasPaham

Aplikasi kuis interaktif sederhana untuk guru dan siswa. Dibuat dengan Flask, SQLite, dan Vanilla HTML/CSS/JS.

## Fitur Utama
* **Tanpa Registrasi:** Siswa hanya butuh kode kuis dan nama panggilan.
* **Manajemen Kuis:** Guru dapat membuat, menerbitkan, dan menutup kuis.
* **Pemantauan Real-time:** Guru dapat melihat siswa yang bergabung dan mengirim jawaban secara langsung (menggunakan polling JS sederhana tanpa WebSockets).
* **Latihan Ulang:** Siswa dapat berlatih kembali khusus untuk soal yang dijawab salah/kosong.
* **Ekspor Laporan:** Ekspor nilai dan rekapitulasi ke format CSV.

## Cara Menjalankan

### Persiapan (Satu Kali Saja)

1. **Buka Terminal / Command Prompt** dan masuk ke folder `kelaspaham`.
2. **Buat Virtual Environment:**
   ```bash
   python -m venv .venv
   ```
3. **Aktivasi Virtual Environment:**
   * **Windows Command Prompt:** `.venv\Scripts\activate.bat`
   * **Windows PowerShell:** `.venv\Scripts\Activate.ps1`
     * *Catatan:* Jika PowerShell menolak karena masalah *Execution Policy*, gunakan langsung path python-nya tanpa diaktivasi: `.venv\Scripts\python.exe`
   * **macOS / Linux:** `source .venv/bin/activate`
4. **Instal Dependensi:**
   ```bash
   pip install -r requirements.txt
   ```
   *(Atau `.venv\Scripts\python.exe -m pip install -r requirements.txt`)*
5. **Buat file konfigurasi `.env`:**
   Salin file `.env.example` menjadi `.env` lalu ganti isi `SECRET_KEY` dengan teks acak milik Anda.

### Menjalankan untuk Pengembangan (Development)

Untuk melihat perubahan secara langsung (hot-reload):

```bash
flask run --port=8080 --debug
```
*(Atau `.venv\Scripts\python.exe -m flask run --port=8080 --debug`)*

Buka `http://localhost:8080` di browser.

### Menjalankan untuk Presentasi/Demo di Jaringan Lokal (Waitress)

Gunakan `waitress` agar aplikasi lebih stabil dan bisa diakses teman dari HP melalui jaringan WiFi yang sama.

```bash
waitress-serve --port=8080 app:create_app
```
*(Atau `.venv\Scripts\waitress-serve.exe --port=8080 "app:create_app"*)*

**Cara siswa mengakses dari HP:**
1. Pastikan laptop dan HP siswa berada di koneksi WiFi yang sama (misal *tethering* HP ke laptop).
2. Cari alamat IPv4 laptop Anda (Ketik `ipconfig` di Windows PowerShell/CMD dan lihat bagian *IPv4 Address*, contoh: `192.168.1.5`).
3. Beritahu siswa untuk membuka browser di HP dan mengetik: `http://192.168.1.5:8080`. (Catatan: `localhost` di HP merujuk ke HP itu sendiri, jadi jangan gunakan `localhost`).
4. *Jika tidak bisa diakses*, pastikan Windows Firewall mengizinkan koneksi masuk untuk port 8080. (Buka *Windows Defender Firewall* -> *Advanced settings* -> *Inbound Rules* -> *New Rule* -> *Port* -> *TCP 8080* -> *Allow the connection*).

### Menghentikan Server
Tekan `Ctrl + C` pada terminal tempat server berjalan.

### Membuat Kuis Demo
Anda bisa langsung membuat kuis demo beserta isinya tanpa perlu mengetik manual:
```bash
python demo_quiz.py
```
*(Atau `.venv\Scripts\python.exe demo_quiz.py`)*

## Menguji Aplikasi
Untuk menjalankan pengujian otomatis:
```bash
pytest
```
*(Atau `.venv\Scripts\pytest.exe`)*
