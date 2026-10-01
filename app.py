import os
from flask import Flask, render_template
from flask_wtf.csrf import CSRFProtect
import db

def create_app(test_config=None):
    """
    Fungsi utama (Application Factory) untuk membuat aplikasi Flask KelasPaham.
    Semua konfigurasi dasar diatur di sini.
    """
    app = Flask(__name__, instance_relative_config=True)
    
    # Pengaturan dasar aplikasi
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_key_jika_tidak_ada_env'),
        DATABASE=os.path.join(app.instance_path, 'kelaspaham.sqlite'),
    )

    if test_config is None:
        # Memuat konfigurasi dari file instance/config.py jika ada (tidak di-commit)
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Memuat konfigurasi khusus untuk pengujian
        app.config.from_mapping(test_config)

    # Memastikan folder instance ada untuk menyimpan database lokal
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Inisialisasi perlindungan CSRF agar formulir lebih aman dari serangan
    csrf = CSRFProtect()
    csrf.init_app(app)

    # Menyiapkan fungsi terkait database
    db.init_app(app)

    # Mendaftarkan route dari blueprint (alur aplikasi)
    from routes_teacher import bp as teacher_bp
    from routes_student import bp as student_bp
    
    app.register_blueprint(teacher_bp)
    app.register_blueprint(student_bp)

    # Route utama (halaman depan)
    @app.route('/')
    def index():
        return render_template('index.html')

    # Penanganan kesalahan umum
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error.html', error_msg="Halaman tidak ditemukan. Periksa kembali tautan yang Anda buka."), 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error.html', error_msg="Terjadi kesalahan pada sistem KelasPaham. Silakan coba lagi nanti."), 500

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=8080, debug=True)