def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b"KelasPaham" in response.data
    assert b"Gabung Kuis" in response.data

def test_create_quiz(client):
    # Menguji pembuatan kuis oleh guru
    response = client.post('/teacher/create', data={
        'title': 'Kuis Python',
        'subject': 'Pemrograman'
    }, follow_redirects=False)
    
    # Harus di-redirect ke halaman manage kuis baru
    assert response.status_code == 302
    assert '/teacher/manage/' in response.location
    assert '?token=' in response.location

def test_student_join(client, app):
    # Buat kuis DRAFT dulu untuk tes
    with app.app_context():
        from db import get_db
        db = get_db()
        db.execute("INSERT INTO quizzes (title, code, manage_token_hash, status) VALUES ('Tes', 'A1B2C', 'hash', 'ACTIVE')")
        db.commit()

    # Siswa mencoba bergabung
    response = client.post('/student/join', data={
        'nickname': 'Budi',
        'code': 'A1B2C'
    }, follow_redirects=False)
    
    assert response.status_code == 302
    assert '/student/quiz/' in response.location
