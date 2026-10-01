from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort, jsonify, make_response
import secrets
from db import get_db
from services import generate_quiz_code, hash_token, check_teacher_access, generate_csv_responses

bp = Blueprint('teacher', __name__, url_prefix='/teacher')

@bp.route('/create', methods=['POST'])
def create_quiz():
    """
    Route untuk membuat kuis baru. 
    Akan dipanggil dari formulir di halaman utama.
    """
    title = request.form.get('title')
    subject = request.form.get('subject')
    description = request.form.get('description')
    
    if not title:
        flash('Judul kuis tidak boleh kosong.', 'error')
        return redirect('/')
        
    # Menghasilkan token acak yang aman untuk manajemen kuis oleh guru
    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)
    
    # Menghasilkan kode pendek untuk siswa bergabung
    code = generate_quiz_code()
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'INSERT INTO quizzes (title, subject, description, code, manage_token_hash, status) VALUES (?, ?, ?, ?, ?, ?)',
        (title, subject, description, code, token_hash, 'DRAFT')
    )
    quiz_id = cursor.lastrowid
    db.commit()
    
    # Mengarahkan guru ke halaman pengelolaannya dengan menyertakan token mentah (sekali saja)
    return redirect(f'/teacher/manage/{quiz_id}?token={raw_token}')

@bp.route('/manage/<int:quiz_id>', methods=['GET'])
def manage_quiz(quiz_id):
    """
    Route halaman dashboard pengelola kuis.
    Menerima token dari URL pada kunjungan pertama, lalu menyimpan hak akses ke session.
    """
    db = get_db()
    quiz = db.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    
    if not quiz:
        abort(404)
        
    token = request.args.get('token')
    
    # Jika ada token di URL, verifikasi hash-nya
    if token:
        if hash_token(token) == quiz['manage_token_hash']:
            # Menyimpan ID kuis ini ke dalam session browser guru agar tidak perlu URL rahasia lagi
            authorized_quizzes = session.get('authorized_quizzes', [])
            if quiz_id not in authorized_quizzes:
                authorized_quizzes.append(quiz_id)
                session['authorized_quizzes'] = authorized_quizzes
                
            # Setelah menyimpan izin, hilangkan token dari URL untuk alasan keamanan
            return redirect(f'/teacher/manage/{quiz_id}')
        else:
            flash('Tautan pengelolaan tidak valid atau sudah kedaluwarsa.', 'error')
            return redirect('/')
            
    # Jika tidak ada token, periksa session
    if not check_teacher_access(quiz_id, session):
        flash('Anda tidak memiliki akses untuk mengelola kuis ini.', 'error')
        return redirect('/')
        
    # Mengambil soal-soal kuis
    questions = db.execute('SELECT * FROM questions WHERE quiz_id = ? ORDER BY sort_order ASC, id ASC', (quiz_id,)).fetchall()
    
    # Halaman yang ditampilkan tergantung pada status kuis
    if quiz['status'] == 'DRAFT':
        return render_template('teacher_draft.html', quiz=quiz, questions=questions)
    elif quiz['status'] in ['WAITING', 'ACTIVE']:
        # Mengambil statistik partisipan
        participants_count = db.execute('SELECT COUNT(*) as count FROM participants WHERE quiz_id = ?', (quiz_id,)).fetchone()['count']
        submissions_count = db.execute('SELECT COUNT(*) as count FROM submissions WHERE quiz_id = ?', (quiz_id,)).fetchone()['count']
        
        return render_template('teacher_dashboard.html', quiz=quiz, 
                               participants_count=participants_count, 
                               submissions_count=submissions_count)
    elif quiz['status'] == 'CLOSED':
        # Menampilkan hasil kuis
        submissions = db.execute('''
            SELECT p.nickname, s.score, s.correct_count, s.wrong_count, s.empty_count 
            FROM submissions s 
            JOIN participants p ON s.participant_id = p.id 
            WHERE s.quiz_id = ?
        ''', (quiz_id,)).fetchall()
        
        # Data untuk grafik
        stats = []
        for q in questions:
            correct = db.execute('''
                SELECT COUNT(*) as c FROM answers a JOIN submissions s ON a.submission_id = s.id
                WHERE a.question_id = ? AND a.is_correct = 1
            ''', (q['id'],)).fetchone()['c']
            wrong = db.execute('''
                SELECT COUNT(*) as c FROM answers a JOIN submissions s ON a.submission_id = s.id
                WHERE a.question_id = ? AND a.is_correct = 0
            ''', (q['id'],)).fetchone()['c']
            empty = db.execute('''
                SELECT COUNT(*) as c FROM answers a JOIN submissions s ON a.submission_id = s.id
                WHERE a.question_id = ? AND a.choice_id IS NULL
            ''', (q['id'],)).fetchone()['c']
            
            stats.append({
                'text': q['text'],
                'correct': correct,
                'wrong': wrong,
                'empty': empty
            })
            
        return render_template('teacher_report.html', quiz=quiz, submissions=submissions, stats=stats)

@bp.route('/api/status/<int:quiz_id>', methods=['GET'])
def api_status(quiz_id):
    """
    Route API untuk mendapatkan pembaruan data secara real-time (polling).
    """
    if not check_teacher_access(quiz_id, session):
        return jsonify({'error': 'Akses ditolak'}), 403
        
    db = get_db()
    quiz = db.execute('SELECT status FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    if not quiz:
        return jsonify({'error': 'Tidak ditemukan'}), 404
        
    participants = db.execute('SELECT nickname FROM participants WHERE quiz_id = ?', (quiz_id,)).fetchall()
    submissions = db.execute('SELECT p.nickname FROM submissions s JOIN participants p ON s.participant_id = p.id WHERE s.quiz_id = ?', (quiz_id,)).fetchall()
    
    sub_names = [s['nickname'] for s in submissions]
    parts_data = []
    for p in participants:
        status = 'Selesai' if p['nickname'] in sub_names else 'Mengerjakan'
        parts_data.append({'nickname': p['nickname'], 'status': status})
        
    return jsonify({
        'status': quiz['status'],
        'participants': parts_data,
        'participants_count': len(participants),
        'submissions_count': len(submissions)
    })

@bp.route('/change_status/<int:quiz_id>', methods=['POST'])
def change_status(quiz_id):
    """
    Route untuk mengubah status kuis (DRAFT -> WAITING -> ACTIVE -> CLOSED).
    Semua perubahan harus diperiksa terlebih dahulu.
    """
    if not check_teacher_access(quiz_id, session):
        abort(403)
        
    new_status = request.form.get('status')
    if new_status not in ['WAITING', 'ACTIVE', 'CLOSED']:
        abort(400)
        
    db = get_db()
    quiz = db.execute('SELECT status FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    
    # Logika alur status kuis
    if new_status == 'WAITING' and quiz['status'] != 'DRAFT':
        flash('Hanya kuis DRAFT yang dapat diterbitkan.', 'error')
    elif new_status == 'ACTIVE' and quiz['status'] != 'WAITING':
        flash('Kuis hanya bisa dimulai dari status WAITING.', 'error')
    elif new_status == 'CLOSED' and quiz['status'] != 'ACTIVE':
        flash('Kuis hanya bisa ditutup dari status ACTIVE.', 'error')
    elif new_status == 'WAITING':
        # Periksa minimal 1 soal sebelum diterbitkan
        q_count = db.execute('SELECT COUNT(*) as c FROM questions WHERE quiz_id = ?', (quiz_id,)).fetchone()['c']
        if q_count == 0:
            flash('Kuis harus memiliki minimal 1 soal sebelum diterbitkan.', 'error')
            return redirect(f'/teacher/manage/{quiz_id}')
            
        db.execute('UPDATE quizzes SET status = ? WHERE id = ?', (new_status, quiz_id))
        db.commit()
    else:
        # Ubah status normalnya
        db.execute('UPDATE quizzes SET status = ? WHERE id = ?', (new_status, quiz_id))
        db.commit()
        
    return redirect(f'/teacher/manage/{quiz_id}')

@bp.route('/add_question/<int:quiz_id>', methods=['POST'])
def add_question(quiz_id):
    """
    Menambahkan soal baru saat kuis dalam status DRAFT.
    """
    if not check_teacher_access(quiz_id, session):
        abort(403)
        
    db = get_db()
    quiz = db.execute('SELECT status FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    if quiz['status'] != 'DRAFT':
        flash('Kuis yang sudah diterbitkan tidak dapat diubah.', 'error')
        return redirect(f'/teacher/manage/{quiz_id}')
        
    text = request.form.get('text')
    topic = request.form.get('topic')
    explanation = request.form.get('explanation')
    correct_choice = request.form.get('correct_choice') # A, B, C, D
    
    choices = {
        'A': request.form.get('choice_a'),
        'B': request.form.get('choice_b'),
        'C': request.form.get('choice_c'),
        'D': request.form.get('choice_d')
    }
    
    if not text or not all(choices.values()) or not correct_choice:
        flash('Pertanyaan dan semua pilihan jawaban wajib diisi.', 'error')
        return redirect(f'/teacher/manage/{quiz_id}')
        
    cursor = db.cursor()
    cursor.execute('INSERT INTO questions (quiz_id, text, topic, explanation) VALUES (?, ?, ?, ?)',
                   (quiz_id, text, topic, explanation))
    question_id = cursor.lastrowid
    
    # Menyimpan pilihan jawaban A, B, C, D
    for label, choice_text in choices.items():
        is_correct = 1 if label == correct_choice else 0
        cursor.execute('INSERT INTO choices (question_id, text, is_correct, label) VALUES (?, ?, ?, ?)',
                       (question_id, choice_text, is_correct, label))
                       
    db.commit()
    flash('Soal berhasil ditambahkan.', 'success')
    return redirect(f'/teacher/manage/{quiz_id}')

@bp.route('/export_csv/<int:quiz_id>')
def export_csv(quiz_id):
    """
    Mengekspor hasil kuis ke format CSV yang bisa didownload.
    """
    if not check_teacher_access(quiz_id, session):
        abort(403)
        
    csv_data = generate_csv_responses(quiz_id)
    
    response = make_response(csv_data)
    response.headers['Content-Disposition'] = f'attachment; filename=hasil_kuis_{quiz_id}.csv'
    response.headers['Content-Type'] = 'text/csv'
    return response
