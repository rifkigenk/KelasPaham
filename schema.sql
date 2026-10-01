-- schema.sql
-- Struktur database untuk KelasPaham

-- Tabel kuis menyimpan informasi utama tentang kuis
CREATE TABLE IF NOT EXISTS quizzes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    subject TEXT,
    description TEXT,
    code TEXT UNIQUE NOT NULL, -- Kode pendek untuk siswa bergabung (misal: A1B2C)
    manage_token_hash TEXT NOT NULL, -- Hash dari token rahasia untuk guru
    status TEXT NOT NULL DEFAULT 'DRAFT', -- DRAFT, WAITING, ACTIVE, CLOSED
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabel soal menyimpan pertanyaan dalam kuis
CREATE TABLE IF NOT EXISTS questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    topic TEXT,
    explanation TEXT,
    sort_order INTEGER DEFAULT 0,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

-- Tabel pilihan jawaban untuk setiap soal
CREATE TABLE IF NOT EXISTS choices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL CHECK (is_correct IN (0, 1)),
    label TEXT NOT NULL, -- A, B, C, D
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
);

-- Tabel peserta yang bergabung ke kuis
CREATE TABLE IF NOT EXISTS participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiz_id INTEGER NOT NULL,
    nickname TEXT NOT NULL,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT UNIQUE NOT NULL, -- ID unik dari session browser siswa
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

-- Tabel pengiriman resmi (satu per peserta per kuis)
CREATE TABLE IF NOT EXISTS submissions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id INTEGER NOT NULL UNIQUE, -- Unique constraint: satu peserta hanya punya satu submission resmi
    quiz_id INTEGER NOT NULL,
    score REAL,
    correct_count INTEGER,
    wrong_count INTEGER,
    empty_count INTEGER,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

-- Tabel detail jawaban dari pengiriman resmi
CREATE TABLE IF NOT EXISTS answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    submission_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    choice_id INTEGER, -- NULL jika kosong
    is_correct BOOLEAN, -- NULL jika kosong
    FOREIGN KEY (submission_id) REFERENCES submissions(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (choice_id) REFERENCES choices(id) ON DELETE CASCADE
);

-- Tabel untuk hasil latihan ulang (tidak masuk nilai resmi)
CREATE TABLE IF NOT EXISTS practices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id INTEGER NOT NULL,
    quiz_id INTEGER NOT NULL,
    score REAL,
    practiced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (participant_id) REFERENCES participants(id) ON DELETE CASCADE,
    FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
);

-- Tabel detail jawaban latihan ulang
CREATE TABLE IF NOT EXISTS practice_answers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    practice_id INTEGER NOT NULL,
    question_id INTEGER NOT NULL,
    choice_id INTEGER,
    is_correct BOOLEAN,
    FOREIGN KEY (practice_id) REFERENCES practices(id) ON DELETE CASCADE,
    FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
    FOREIGN KEY (choice_id) REFERENCES choices(id) ON DELETE CASCADE
);
