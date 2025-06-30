# tests/conftest.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import Doctor, Admin


@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False

    with app.app_context():
        db.create_all()

        # Add a test doctor
        doctor = Doctor(name='Dr. Smith', specialization='Cardiology', is_active=True)
        db.session.add(doctor)

        # Add a default admin
        admin = Admin(username='admin', password='admin')
        db.session.add(admin)

        db.session.commit()

        yield app.test_client()

        db.session.remove()
        db.drop_all()
