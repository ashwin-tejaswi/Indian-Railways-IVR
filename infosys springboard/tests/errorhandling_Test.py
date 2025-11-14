import pytest
from fastapi.testclient import TestClient
from ivr_backend import app
client = TestClient(app)

def test_conversation_with_no_input():
    data = {"CallSid": "abc999"}
    response = client.post("/conversation", data=data)
    assert response.status_code == 200
    assert "didn’t understand" in response.text or "repeat" in response.text

def test_call_start_missing_number():
    payload = {}
    response = client.post("/call/start", json=payload)
    assert response.status_code == 200
    assert "Missing 'to'" in response.text

def test_invalid_endpoint():
    response = client.get("/nonexistent")
    assert response.status_code == 404
