# tests/test_routes.py
from unittest.mock import patch
from datetime import datetime, timedelta

def test_homepage(client):
    res = client.get('/')
    assert res.status_code == 200
    assert b"Appointment" in res.data