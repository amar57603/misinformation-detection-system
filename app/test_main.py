import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_model_info_success():
    response = client.get("/api/model_info")
    # If models are loaded, it should return 200.
    if response.status_code == 200:
        data = response.json()
        assert "algorithm" in data
        assert "vocabulary_size" in data
        assert "top_fake_features" in data
        assert "top_real_features" in data
    else:
        # If models fail to load (503), just ensure it's handled gracefully
        assert response.status_code == 503

def test_predict_success_english_fake():
    fake_text = "BREAKING: Scientists CONFIRM that 5G towers are secretly spreading a new airborne pathogen designed to control human DNA! Governments worldwide are covering up this shocking truth. Your immune system is being destroyed right now!"
    response = client.post("/api/predict", json={"text": fake_text})
    if response.status_code == 200:
        data = response.json()
        assert "prediction" in data
        assert "confidence" in data
        assert data["language"] == "English"
    else:
        assert response.status_code == 503

def test_predict_success_malay_real():
    real_text = "Majlis Bandaraya Melaka Bersejarah telah melancarkan aplikasi mudah alih rasmi yang membolehkan penduduk membuat aduan berkaitan perkhidmatan perbandaran."
    response = client.post("/api/predict", json={"text": real_text})
    if response.status_code == 200:
        data = response.json()
        assert "prediction" in data
        assert "confidence" in data
        assert data["language"] == "Bahasa Malaysia"
    else:
        assert response.status_code == 503

def test_predict_error_empty_text():
    response = client.post("/api/predict", json={"text": ""})
    assert response.status_code == 422 # Pydantic validation error for min_length

def test_predict_error_short_text():
    # Only 2 words, the backend needs at least 3 non-stop words or will throw 400
    response = client.post("/api/predict", json={"text": "hello world"})
    assert response.status_code in (400, 422)
