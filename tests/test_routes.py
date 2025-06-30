# tests/test_routes.py
from unittest.mock import patch
from datetime import datetime, timedelta

def test_homepage(client):
    res = client.get('/')
    assert res.status_code == 200
    assert b"Appointment" in res.data

def test_contact_form(client):
    res = client.post('/contact', data={
        'name': 'Test',
        'email': 'test@example.com',
        'message': 'Test message'
    }, follow_redirects=True)
    assert b"Thank you for contacting us" in res.data

def test_admin_login_valid(client):
    res = client.post('/admin/login', data={
        'username': 'admin',
        'password': 'admin'
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Admin Dashboard" in res.data

def test_admin_login_invalid(client):
    res = client.post('/admin/login', data={
        'username': 'wrong',
        'password': 'wrong'
    }, follow_redirects=True)
    assert b"Invalid credentials" in res.data

def test_add_doctor(client):
    client.post('/admin/login', data={'username': 'admin', 'password': 'admin'})
    res = client.post('/admin/add_doctor', data={
        'name': 'Dr. Test',
        'specialization': 'Dermatology'
    }, follow_redirects=True)
    assert b"Doctor added successfully." in res.data