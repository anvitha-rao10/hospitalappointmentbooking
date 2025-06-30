# tests/test_routes.py
from unittest.mock import patch
from datetime import datetime, timedelta

def test_homepage(client):
    res = client.get('/')
    assert res.status_code == 200
    assert b"Appointment" in res.data

def test_doctor_corner(client):
    res = client.get('/doctor_corner')
    assert res.status_code == 200
    assert b"Cardiology" in res.data

def test_contact_form(client):
    res = client.post('/contact', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'message': 'Hello!'
    }, follow_redirects=True)
    assert b"Thank you for contacting us" in res.data

@patch('app.send_email')
def test_successful_appointment(mock_send_email, client):
    future_time = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0).strftime('%H:%M')
    future_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

    res = client.post('/', data={
        'confirm': 'yes',
        'name': 'Test Patient',
        'email': 'patient@example.com',
        'phone': '1234567890',
        'doctor': 'Dr. Smith',
        'date': future_date,
        'time': future_time
    }, follow_redirects=True)

    assert b"Appointment booked successfully" in res.data or b"Added to waiting list" in res.data
    assert mock_send_email.called

def test_admin_login_success(client):
    res = client.post('/admin/login', data={
        'username': 'admin',
        'password': 'admin'
    }, follow_redirects=True)
    assert b"Dashboard" in res.data or res.status_code == 200

def test_admin_login_fail(client):
    res = client.post('/admin/login', data={
        'username': 'wrong',
        'password': 'wrong'
    }, follow_redirects=True)
    assert b"Invalid credentials" in res.data

def test_toggle_doctor(client):
    # Log in as admin first
    client.post('/admin/login', data={'username': 'admin', 'password': 'admin'})
    
    # Toggle doctor active status
    res = client.post('/admin/toggle_doctor/1', follow_redirects=True)
    assert b"Doctor" in res.data

def test_delete_appointment(client):
    # Log in and create an appointment
    client.post('/admin/login', data={'username': 'admin', 'password': 'admin'})
    
    from models import Appointment
    from app import db
    from datetime import datetime

    new_appt = Appointment(
        name='ToDelete',
        email='del@example.com',
        phone='9999999999',
        doctor='Dr. Smith',
        appointment_time=datetime.now() + timedelta(days=1),
        status='confirmed'
    )
    db.session.add(new_appt)
    db.session.commit()

    # Delete the appointment
    res = client.post(f'/admin/delete/{new_appt.id}', follow_redirects=True)
    assert b"Deleted & archived" in res.data
