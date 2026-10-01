from app import create_app
from db import get_db, init_db
from services import hash_token
import secrets

def create_demo():
    app = create_app()
    with app.app_context():
        # Pastikan tabel dibuat
        init_db()
        
        db = get_db()
        cursor = db.cursor()
        
        # Buat token dan hash
        raw_token = secrets.token_urlsafe(32)
        token_hash = hash_token(raw_token)
        code = "DEMO1"
        
        # Cek apakah kode sudah ada
        if db.execute('SELECT id FROM quizzes WHERE code = ?', (code,)).fetchone():
            print("Kuis demo dengan kode DEMO1 sudah ada.")
            return
            
        cursor.execute('''
            INSERT INTO quizzes (title, subject, description, code, manage_token_hash, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('Kuis Dasar Python (Demo)', 'Pemrograman', 'Kuis untuk demonstrasi aplikasi KelasPaham.', code, token_hash, 'DRAFT'))
        
        quiz_id = cursor.lastrowid
        
        # Daftar 10 soal
        questions = [
            {
                "text": "Fungsi apa yang digunakan untuk menampilkan teks ke layar di Python?",
                "topic": "Dasar",
                "exp": "Fungsi print() digunakan untuk mencetak output ke konsol.",
                "choices": [("echo()", "A", 0), ("print()", "B", 1), ("display()", "C", 0), ("show()", "D", 0)]
            },
            {
                "text": "Bagaimana cara membuat variabel x dengan nilai 5?",
                "topic": "Variabel",
                "exp": "Di Python, kita tidak perlu mendeklarasikan tipe data. Cukup x = 5.",
                "choices": [("int x = 5;", "A", 0), ("x = 5", "B", 1), ("var x = 5", "C", 0), ("let x = 5", "D", 0)]
            },
            {
                "text": "Tipe data dari [1, 2, 3] adalah...",
                "topic": "Tipe Data",
                "exp": "Kurung siku [] menandakan tipe data List di Python.",
                "choices": [("Tuple", "A", 0), ("Dictionary", "B", 0), ("List", "C", 1), ("Set", "D", 0)]
            },
            {
                "text": "Kata kunci untuk membuat fungsi baru di Python adalah...",
                "topic": "Fungsi",
                "exp": "Kata kunci def digunakan untuk mendefinisikan fungsi (define).",
                "choices": [("function", "A", 0), ("def", "B", 1), ("fun", "C", 0), ("method", "D", 0)]
            },
            {
                "text": "Berapakah hasil dari 5 // 2?",
                "topic": "Operator",
                "exp": "Operator // melakukan pembagian dengan pembulatan ke bawah (floor division).",
                "choices": [("2.5", "A", 0), ("3", "B", 0), ("2", "C", 1), ("1", "D", 0)]
            },
            {
                "text": "Komentar satu baris di Python diawali dengan...",
                "topic": "Dasar",
                "exp": "Tanda pagar # digunakan untuk komentar satu baris.",
                "choices": [("//", "A", 0), ("/*", "B", 0), ("#", "C", 1), ("--", "D", 0)]
            },
            {
                "text": "Bagaimana cara mengambil elemen pertama dari list my_list?",
                "topic": "List",
                "exp": "Indeks di Python dimulai dari 0.",
                "choices": [("my_list[1]", "A", 0), ("my_list(0)", "B", 0), ("my_list[0]", "C", 1), ("first(my_list)", "D", 0)]
            },
            {
                "text": "Pernyataan percabangan di Python menggunakan...",
                "topic": "Percabangan",
                "exp": "Python menggunakan if, elif, dan else.",
                "choices": [("if - else if - else", "A", 0), ("if - elif - else", "B", 1), ("switch - case", "C", 0), ("when - then", "D", 0)]
            },
            {
                "text": "Looping atau perulangan yang akan mengeksekusi selama kondisinya benar (True) adalah...",
                "topic": "Perulangan",
                "exp": "Perulangan while digunakan ketika kita ingin mengulang blok kode selama suatu kondisi bernilai True.",
                "choices": [("for", "A", 0), ("while", "B", 1), ("do-while", "C", 0), ("loop", "D", 0)]
            },
            {
                "text": "Apa hasil dari 'Hello' + 'World'?",
                "topic": "String",
                "exp": "Operator + pada string melakukan konkatenasi (penggabungan) tanpa spasi tambahan.",
                "choices": [("Hello World", "A", 0), ("HelloWorld", "B", 1), ("Error", "C", 0), ("['Hello', 'World']", "D", 0)]
            }
        ]
        
        for idx, q in enumerate(questions):
            cursor.execute('INSERT INTO questions (quiz_id, text, topic, explanation, sort_order) VALUES (?, ?, ?, ?, ?)',
                           (quiz_id, q["text"], q["topic"], q["exp"], idx))
            question_id = cursor.lastrowid
            
            for c_text, c_label, is_correct in q["choices"]:
                cursor.execute('INSERT INTO choices (question_id, text, is_correct, label) VALUES (?, ?, ?, ?)',
                               (question_id, c_text, is_correct, c_label))
                               
        db.commit()
        
        print(f"\n[SUKSES] Kuis Demo Berhasil Dibuat!\n")
        print(f"Kode Gabung Siswa: {code}")
        print(f"Tautan Akses Guru (Simpan ini):")
        print(f"http://localhost:8080/teacher/manage/{quiz_id}?token={raw_token}\n")

if __name__ == '__main__':
    create_demo()
