from services import calculate_score, hash_token, generate_quiz_code

def test_calculate_score():
    assert calculate_score(10, 10) == 100.0
    assert calculate_score(5, 10) == 50.0
    assert calculate_score(0, 10) == 0.0
    assert calculate_score(3, 9) == 33.33
    assert calculate_score(5, 0) == 0.0

def test_hash_token():
    token = "rahasia123"
    hashed = hash_token(token)
    assert hashed != token
    assert len(hashed) == 64 # Panjang SHA-256

def test_generate_quiz_code(app):
    with app.app_context():
        code = generate_quiz_code()
        assert len(code) == 5
        assert code.isalnum()
        assert code.isupper()
