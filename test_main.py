import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_handle_interactions():
    payload = {"type": "test_type", "id": "test_id", "data": {"key": "value"}}
    response = client.post("/interactions", json=payload)
    assert response.status_code == 200
    assert response.text == '{"type":1}'
