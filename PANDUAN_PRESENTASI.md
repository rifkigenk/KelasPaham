# Panduan Presentasi KelasPaham

Panduan ini disusun untuk membantu Anda mempresentasikan aplikasi KelasPaham di depan guru dan teman sekelas.

## 1. Latar Belakang & Masalah
* **Masalah:** Mengoreksi kuis secara manual memakan waktu. Selain itu, terkadang guru sulit mengetahui materi mana yang paling banyak tidak dipahami siswa karena harus menghitung manual jawaban salah dari seluruh kelas.
* **Solusi:** KelasPaham adalah aplikasi kuis interaktif berbasis web.
* **Manfaat Utama:**
  * Guru: Dapat membuat soal dengan cepat, nilai langsung dihitung oleh sistem, dan ada grafik analisis butir soal.
  * Siswa: Dapat bergabung tanpa perlu mendaftar akun, mengerjakan soal langsung dari HP, dan bisa melakukan "Latihan Ulang" untuk soal-soal yang dijawab salah/kosong guna memperbaiki pemahaman.

## 2. Teknologi yang Digunakan
* **Backend:** Python dengan kerangka kerja (framework) **Flask**.
* **Database:** **SQLite**. SQLite dipilih karena ringan, tidak perlu server database terpisah, dan datanya disimpan dalam satu file lokal (di folder `instance/`).
* **Frontend:** HTML, CSS, dan JavaScript murni (Vanilla). Tidak menggunakan framework CSS besar (seperti Bootstrap) agar desainnya lebih unik (custom) dan proses belajarnya lebih mendasar. Pembaruan data (polling) dan pembuatan grafik juga dibangun manual dari awal.
* **Server Produksi Lokal:** **Waitress**, digunakan agar aplikasi stabil saat diakses banyak siswa (HP) melalui jaringan WiFi lokal (tethering/hotspot).

## 3. Struktur & Hubungan Antartabel (Database)
Aplikasi ini memiliki beberapa tabel penting yang saling berelasi:
1. `quizzes`: Menyimpan data kuis (judul, kode gabung, status).
2. `questions`: Menyimpan pertanyaan, berelasi ke `quizzes` (satu kuis banyak pertanyaan).
3. `choices`: Menyimpan pilihan jawaban A, B, C, D. Berelasi ke `questions`.
4. `participants`: Menyimpan data siswa yang bergabung.
5. `submissions`: Menyimpan hasil *pengiriman resmi*. Satu peserta HANYA BOLEH memiliki satu submission di satu kuis (diatur menggunakan konstrain `UNIQUE` di database).
6. `answers`: Menyimpan detail jawaban resmi siswa untuk tiap soal.
7. `practices` & `practice_answers`: Tabel khusus untuk menyimpan nilai dan detail jawaban dari fitur Latihan Ulang, sengaja dipisah agar tidak merusak rata-rata nilai resmi kelas.

## 4. Alur Kerja (Workflow)
* **Pembuatan Kuis:** Guru membuat kuis (status `DRAFT`). Kuis belum bisa diakses siswa.
* **Bergabung:** Kuis diubah menjadi `WAITING` (Diterbitkan). Siswa memasukkan kode dan nama. Mereka masuk ke *Ruang Tunggu*.
* **Pengerjaan:** Guru menekan tombol "Mulai", status menjadi `ACTIVE`. Halaman siswa otomatis memperbarui diri dan menampilkan soal.
* **Pengiriman:** Siswa mengirim jawaban. Penghitungan nilai dilakukan di **Backend** berdasarkan kunci jawaban di database, bukan di frontend, sehingga siswa tidak bisa mencurangi nilai lewat *Inspect Element*.
* **Penutupan & Laporan:** Guru menekan "Tutup", status menjadi `CLOSED`. Siswa bisa melihat nilainya. Guru dapat melihat laporan nilai dan grafik "Analisis Butir Soal" lalu mengekspornya ke CSV.

## 5. Pertanyaan yang Sering Muncul & Cara Menjawabnya

**Tanya:** *Mengapa siswa tidak perlu membuat akun/login? Bagaimana aplikasi membedakan Budi A dan Budi B?*
**Jawab:** Aplikasi ini didesain untuk kepraktisan di ruang kelas, sehingga menghemat waktu. Aplikasi menggunakan `session` pada Flask yang disimpan dalam cookie browser. Saat siswa bergabung, sistem membuatkan ID Session unik (`uuid`). Jika ada dua orang bernama "Budi", mereka tetap memiliki session ID yang berbeda di tabel `participants`.

**Tanya:** *Bagaimana cara mencegah siswa mengirim jawaban dua kali?*
**Jawab:** Saya mengamankannya di dua lapis. Lapis pertama di kode Python (Flask): mengecek apakah session ID ini sudah ada di tabel `submissions`. Lapis kedua (paling kuat) di Database: kolom `participant_id` pada tabel `submissions` diset `UNIQUE`. Jadi, database akan menolak penyimpanan kedua dari peserta yang sama. Operasi penyimpanan ini juga dibungkus dalam *Transaction* (db.execute("BEGIN TRANSACTION")).

**Tanya:** *Bagaimana grafik batang di halaman laporan dibuat? Apakah memakai library?*
**Jawab:** Tidak, grafik batang tersebut murni dibangun dari logika matematika sederhana di HTML/CSS. Lebar warna hijau (benar), merah (salah), dan abu-abu (kosong) dihitung di server (Flask) dalam bentuk persentase, lalu persentase itu dimasukkan ke dalam atribut `style="width: XX%;"` di file HTML (Jinja template).

**Tanya:** *Apakah kunci jawaban bisa diintip siswa lewat kode sumber halaman (View Page Source)?*
**Jawab:** Tidak bisa. Pada status `ACTIVE`, data kunci jawaban (`is_correct`) sengaja tidak dikirimkan ke HTML siswa. Kunci jawaban baru dikirimkan bersama hasil ketika kuis sudah berstatus `CLOSED`.

## 6. Skenario Demonstrasi (Praktik 5 Menit)
1. **[Guru]** Buka web di laptop, buat kuis baru. (Gunakan perintah `python demo_quiz.py` sebelum presentasi agar soal sudah tersedia).
2. **[Guru]** Ubah status kuis menjadi "Terbitkan". Perlihatkan kode kuis di layar laptop.
3. **[Siswa]** Minta salah satu teman/guru membuka browser di HP dan masukkan IP laptop Anda beserta port 8080.
4. **[Siswa]** Teman mengisi nama dan kode kuis, memperlihatkan tampilan "Ruang Tunggu".
5. **[Guru]** Tunjukkan di laptop bahwa jumlah peserta yang bergabung bertambah secara real-time (karena ada *polling*).
6. **[Guru]** Klik "Mulai Kuis". Tunjukkan HP teman otomatis pindah ke halaman soal.
7. **[Siswa]** Teman menjawab soal (sengaja salahkan beberapa soal), lalu klik "Kirim".
8. **[Guru]** Perlihatkan di laptop bahwa jumlah pengiriman bertambah. Klik "Tutup Kuis".
9. **[Guru]** Tunjukkan halaman laporan (nilai teman dan grafik otomatis muncul). Klik tombol "Unduh CSV" untuk menunjukkan bukti rekapnya bisa dibuka di Excel.
10. **[Siswa]** Tunjukkan HP teman, nilai muncul beserta tombol "Mulai Latihan". Klik tombol tersebut dan buktikan siswa bisa belajar lagi dari kesalahannya.
