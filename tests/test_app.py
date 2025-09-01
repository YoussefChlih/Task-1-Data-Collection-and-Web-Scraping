import pytest
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def test_home():
    response = client.get("/")
    assert response.status_code == 200

def test_scrape():
    response = client.post("/scrape", json={"url": "https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)", "format": "csv"})
    assert response.status_code == 200
    assert "job_id" in response.json()
