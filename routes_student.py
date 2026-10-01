from flask import Blueprint, render_template, request, redirect, session, flash, abort, jsonify
from db import get_db
import uuid
from services import calculate_score

bp = Blueprint('student', __name__, url_prefix='/student')

@bp.route('/join', methods=['POST'])
def join_quiz():
    code = request.form.get('code', '').strip().upper()
    nickname = request.form.get('nickname', '').strip()
    
    if not code or not nickname:
        flash('Kode kuis dan nama panggilan harus diisi.', 'error')
        return redirect('/')
        
    db = get_db()
    quiz = db.execute('SELECT id, status FROM quizzes WHERE code = ?', (code,)).fetchone()
    
    if not quiz:
        flash('Kode kuis tidak ditemukan.', 'error')
        return redirect('/')
        
    if quiz['status'] == 'DRAFT':
        flash('Kuis belum diterbitkan oleh guru.', 'error')
        return redirect('/')
        
    if quiz['status'] == 'CLOSED':
        flash('Kuis ini sudah ditutup.', 'error')
        return redirect('/')
        
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    
    session_id = session['session_id']
    
    participant = db.execute('SELECT id FROM participants WHERE quiz_id = ? AND session_id = ?', 
                             (quiz['id'], session_id)).fetchone()
                             
    if not participant:
        cursor = db.cursor()
        cursor.execute('INSERT INTO participants (quiz_id, nickname, session_id) VALUES (?, ?, ?)',
                       (quiz['id'], nickname, session_id))
        db.commit()
        
    return redirect(f"/student/quiz/{quiz['id']}")

@bp.route('/quiz/<int:quiz_id>')
def quiz_page(quiz_id):
    if 'session_id' not in session:
        return redirect('/')
        
    db = get_db()
    participant = db.execute('SELECT id, nickname FROM participants WHERE quiz_id = ? AND session_id = ?',
                             (quiz_id, session['session_id'])).fetchone()
                             
    if not participant:
        flash('Sesi Anda tidak ditemukan. Silakan bergabung kembali.', 'error')
        return redirect('/')
        
    quiz = db.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    
    submission = db.execute('SELECT * FROM submissions WHERE participant_id = ?', (participant['id'],)).fetchone()
    
    if submission:
        if quiz['status'] == 'CLOSED':
            answers_query = '''
                SELECT q.id as q_id, q.text as question_text, q.explanation, 
                       c_user.text as user_answer_text, c_user.label as user_answer_label,
                       c_correct.text as correct_answer_text, c_correct.label as correct_answer_label,
                       a.is_correct as is_user_correct
                FROM answers a
                JOIN questions q ON a.question_id = q.id
                LEFT JOIN choices c_user ON a.choice_id = c_user.id
                LEFT JOIN choices c_correct ON q.id = c_correct.question_id AND c_correct.is_correct = 1
                WHERE a.submission_id = ?
            '''
            details = db.execute(answers_query, (submission['id'],)).fetchall()
            
            # Memeriksa apakah ada hasil latihan
            practice = db.execute('SELECT * FROM practices WHERE participant_id = ? AND quiz_id = ? ORDER BY practiced_at DESC LIMIT 1', 
                                  (participant['id'], quiz_id)).fetchone()
                                  
            return render_template('student_result.html', quiz=quiz, submission=submission, 
                                   details=details, nickname=participant['nickname'], practice=practice)
        else:
            return render_template('student_waiting.html', quiz=quiz, message="Jawaban Anda berhasil dikirim. Menunggu kuis ditutup oleh guru untuk melihat hasil.")
            
    if quiz['status'] == 'WAITING':
        return render_template('student_waiting.html', quiz=quiz, message="Menunggu guru memulai kuis.")
        
    if quiz['status'] == 'ACTIVE':
        questions = db.execute('SELECT id, text, sort_order FROM questions WHERE quiz_id = ? ORDER BY sort_order ASC, id ASC', (quiz_id,)).fetchall()
        
        q_data = []
        for q in questions:
            choices = db.execute('SELECT id, text, label FROM choices WHERE question_id = ? ORDER BY label ASC', (q['id'],)).fetchall()
            q_data.append({
                'id': q['id'],
                'text': q['text'],
                'choices': choices
            })
            
        return render_template('student_quiz.html', quiz=quiz, questions=q_data, nickname=participant['nickname'])
        
    return redirect('/')

@bp.route('/submit/<int:quiz_id>', methods=['POST'])
def submit_quiz(quiz_id):
    if 'session_id' not in session:
        abort(403)
        
    db = get_db()
    db.execute("BEGIN TRANSACTION")
    
    try:
        participant = db.execute('SELECT id FROM participants WHERE quiz_id = ? AND session_id = ?',
                                 (quiz_id, session['session_id'])).fetchone()
                                 
        if not participant:
            db.rollback()
            abort(403)
            
        quiz = db.execute('SELECT status FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
        
        if quiz['status'] != 'ACTIVE':
            db.rollback()
            flash('Kuis sudah tidak aktif atau ditutup. Pengiriman ditolak.', 'error')
            return redirect(f'/student/quiz/{quiz_id}')
            
        existing = db.execute('SELECT id FROM submissions WHERE participant_id = ?', (participant['id'],)).fetchone()
        if existing:
            db.rollback()
            return redirect(f'/student/quiz/{quiz_id}')
            
        questions = db.execute('SELECT id FROM questions WHERE quiz_id = ?', (quiz_id,)).fetchall()
        
        correct_count = 0
        wrong_count = 0
        empty_count = 0
        
        answers_to_insert = []
        
        for q in questions:
            q_id_str = str(q['id'])
            choice_id = request.form.get(f'q_{q_id_str}')
            
            if not choice_id:
                empty_count += 1
                answers_to_insert.append((q['id'], None, None))
                continue
                
            choice = db.execute('SELECT is_correct FROM choices WHERE id = ? AND question_id = ?', 
                                (choice_id, q['id'])).fetchone()
                                
            if choice and choice['is_correct']:
                correct_count += 1
                answers_to_insert.append((q['id'], choice_id, 1))
            else:
                wrong_count += 1
                answers_to_insert.append((q['id'], choice_id, 0))
                
        total_questions = len(questions)
        score = calculate_score(correct_count, total_questions)
        
        cursor = db.cursor()
        cursor.execute(
            'INSERT INTO submissions (participant_id, quiz_id, score, correct_count, wrong_count, empty_count) VALUES (?, ?, ?, ?, ?, ?)',
            (participant['id'], quiz_id, score, correct_count, wrong_count, empty_count)
        )
        sub_id = cursor.lastrowid
        
        for ans in answers_to_insert:
            cursor.execute(
                'INSERT INTO answers (submission_id, question_id, choice_id, is_correct) VALUES (?, ?, ?, ?)',
                (sub_id, ans[0], ans[1], ans[2])
            )
            
        db.commit()
    except Exception as e:
        db.rollback()
        pass
        
    return redirect(f'/student/quiz/{quiz_id}')

@bp.route('/practice/<int:quiz_id>', methods=['GET'])
def practice_quiz(quiz_id):
    """
    Halaman untuk latihan ulang pada soal yang dijawab salah atau kosong.
    Hanya bisa diakses jika kuis sudah ditutup dan siswa punya submission.
    """
    if 'session_id' not in session:
        return redirect('/')
        
    db = get_db()
    participant = db.execute('SELECT id, nickname FROM participants WHERE quiz_id = ? AND session_id = ?',
                             (quiz_id, session['session_id'])).fetchone()
                             
    if not participant:
        flash('Sesi Anda tidak ditemukan.', 'error')
        return redirect('/')
        
    quiz = db.execute('SELECT * FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    
    if quiz['status'] != 'CLOSED':
        flash('Latihan ulang hanya bisa dilakukan setelah kuis ditutup.', 'error')
        return redirect(f'/student/quiz/{quiz_id}')
        
    submission = db.execute('SELECT id FROM submissions WHERE participant_id = ?', (participant['id'],)).fetchone()
    if not submission:
        flash('Anda belum mengikuti kuis ini, tidak dapat melakukan latihan ulang.', 'error')
        return redirect('/')
        
    # Ambil pertanyaan yang salah atau kosong dari submission resmi
    wrong_answers = db.execute('''
        SELECT q.id, q.text, q.sort_order 
        FROM answers a 
        JOIN questions q ON a.question_id = q.id 
        WHERE a.submission_id = ? AND (a.is_correct = 0 OR a.is_correct IS NULL)
        ORDER BY q.sort_order ASC, q.id ASC
    ''', (submission['id'],)).fetchall()
    
    if not wrong_answers:
        flash('Semua jawaban Anda sudah benar! Tidak ada soal untuk dilatih ulang.', 'success')
        return redirect(f'/student/quiz/{quiz_id}')
        
    q_data = []
    for q in wrong_answers:
        choices = db.execute('SELECT id, text, label FROM choices WHERE question_id = ? ORDER BY label ASC', (q['id'],)).fetchall()
        q_data.append({
            'id': q['id'],
            'text': q['text'],
            'choices': choices
        })
        
    return render_template('student_practice.html', quiz=quiz, questions=q_data, nickname=participant['nickname'])

@bp.route('/submit_practice/<int:quiz_id>', methods=['POST'])
def submit_practice(quiz_id):
    """
    Menyimpan hasil latihan ulang. Nilainya tidak digabung dengan nilai resmi.
    """
    if 'session_id' not in session:
        abort(403)
        
    db = get_db()
    participant = db.execute('SELECT id FROM participants WHERE quiz_id = ? AND session_id = ?',
                             (quiz_id, session['session_id'])).fetchone()
                             
    if not participant:
        abort(403)
        
    quiz = db.execute('SELECT status FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    
    if quiz['status'] != 'CLOSED':
        abort(403)
        
    submission = db.execute('SELECT id FROM submissions WHERE participant_id = ?', (participant['id'],)).fetchone()
    if not submission:
        abort(403)
        
    # Ambil id soal yang diulang
    wrong_answers = db.execute('''
        SELECT q.id FROM answers a JOIN questions q ON a.question_id = q.id 
        WHERE a.submission_id = ? AND (a.is_correct = 0 OR a.is_correct IS NULL)
    ''', (submission['id'],)).fetchall()
    
    total_practice = len(wrong_answers)
    correct_count = 0
    
    answers_to_insert = []
    
    for q in wrong_answers:
        choice_id = request.form.get(f'q_{q["id"]}')
        
        if not choice_id:
            answers_to_insert.append((q['id'], None, 0))
            continue
            
        choice = db.execute('SELECT is_correct FROM choices WHERE id = ? AND question_id = ?', 
                            (choice_id, q['id'])).fetchone()
                            
        if choice and choice['is_correct']:
            correct_count += 1
            answers_to_insert.append((q['id'], choice_id, 1))
        else:
            answers_to_insert.append((q['id'], choice_id, 0))
            
    score = calculate_score(correct_count, total_practice)
    
    cursor = db.cursor()
    cursor.execute(
        'INSERT INTO practices (participant_id, quiz_id, score) VALUES (?, ?, ?)',
        (participant['id'], quiz_id, score)
    )
    practice_id = cursor.lastrowid
    
    for ans in answers_to_insert:
        cursor.execute(
            'INSERT INTO practice_answers (practice_id, question_id, choice_id, is_correct) VALUES (?, ?, ?, ?)',
            (practice_id, ans[0], ans[1], ans[2])
        )
        
    db.commit()
    
    flash('Latihan ulang berhasil diselesaikan. Lihat hasilnya di bawah ini.', 'success')
    return redirect(f'/student/quiz/{quiz_id}')

@bp.route('/api/status/<int:quiz_id>')
def api_status(quiz_id):
    db = get_db()
    quiz = db.execute('SELECT status FROM quizzes WHERE id = ?', (quiz_id,)).fetchone()
    
    if not quiz:
        return jsonify({'error': 'Not found'}), 404
        
    return jsonify({'status': quiz['status']})
