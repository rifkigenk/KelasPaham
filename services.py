import hashlib
import secrets
import random
import string
from db import get_db

def generate_quiz_code(length=5):
    """
    Menghasilkan kode unik untuk kuis agar siswa bisa bergabung.
    Kode berupa huruf besar dan angka.
    """
    characters = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choice(characters) for i in range(length))
        db = get_db()
        # Pastikan kode unik, tidak ada yang sama di database
        exists = db.execute("SELECT id FROM quizzes WHERE code = ?", (code,)).fetchone()
        if not exists:
            return code

def hash_token(token):
    """
    Mengubah token mentah (teks rahasia) menjadi hash.
    Tujuannya agar token asli tidak tersimpan di database untuk keamanan.
    """
    # Menggunakan SHA-256 untuk hashing
    return hashlib.sha256(token.encode('utf-8')).hexdigest()

def check_teacher_access(quiz_id, session):
    """
    Memeriksa apakah guru saat ini memiliki akses ke kuis tertentu.
    Hak akses disimpan di dalam session browser.
    """
    # Mengambil daftar kuis yang boleh diakses dari session
    authorized_quizzes = session.get('authorized_quizzes', [])
    return quiz_id in authorized_quizzes

def calculate_score(correct_count, total_count):
    """
    Menghitung persentase nilai berdasarkan jumlah benar.
    Rumus: (Benar / Total) * 100, dibulatkan 2 desimal.
    """
    if total_count == 0:
        return 0.0
    return round((correct_count / total_count) * 100, 2)

def generate_csv_responses(quiz_id):
    """
    Membuat data format CSV dari nilai siswa.
    CSV adalah format teks sederhana yang bisa dibuka di Excel.
    """
    db = get_db()
    # Mengambil daftar pengiriman beserta identitas peserta
    submissions = db.execute('''
        SELECT p.nickname, s.score, s.correct_count, s.wrong_count, s.empty_count, s.submitted_at
        FROM submissions s
        JOIN participants p ON s.participant_id = p.id
        WHERE s.quiz_id = ?
        ORDER BY s.submitted_at ASC
    ''', (quiz_id,)).fetchall()
    
    # Header baris pertama
    csv_data = "Nama Peserta,Nilai,Benar,Salah,Kosong,Waktu Kirim\n"
    
    for row in submissions:
        # Menghindari formula Excel injection jika nama dimulai dengan tanda =
        safe_name = row['nickname'].replace('"', '""')
        if safe_name.startswith(('=', '+', '-', '@')):
            safe_name = "'" + safe_name
            
        csv_data += f'"{safe_name}",{row["score"]},{row["correct_count"]},{row["wrong_count"]},{row["empty_count"]},"{row["submitted_at"]}"\n'
        
    return csv_data
