import pytest
from fastapi.testclient import TestClient
from ivr_backend import app

client = TestClient(app)

def test_voice_entrypoint():
    response = client.post("/voice")
    assert response.status_code == 200
    assert "<Say>" in response.text

def test_conversation_booking_flow():
    data = {"CallSid": "abc123", "SpeechResult": "book ticket"}
    response = client.post("/conversation", data=data)
    assert response.status_code == 200
    assert "book a ticket" in response.text or "Sleeper" in response.text

def test_conversation_check_pnr():
    data = {"CallSid": "abc124", "SpeechResult": "check PNR"}
    response = client.post("/conversation", data=data)
    assert "P N R" in response.text

def test_call_end_clears_context():
    data = {"CallSid": "abc125"}
    client.post("/conversation", data={"CallSid": "abc125", "SpeechResult": "book ticket"})
    resp = client.post("/call/end", data=data)
    assert resp.status_code == 200
