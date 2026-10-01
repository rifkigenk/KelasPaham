import pytest
import os
import tempfile
from app import create_app
from db import get_db, init_db

@pytest.fixture
def app():
    # Membuat file database sementara
    db_fd, db_path = tempfile.mkstemp()

    app = create_app({
        'TESTING': True,
        'DATABASE': db_path,
        'WTF_CSRF_ENABLED': False, # Nonaktifkan CSRF untuk mempermudah testing POST
    })

    with app.app_context():
        init_db()

    yield app

    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
