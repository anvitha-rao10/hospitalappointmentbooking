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