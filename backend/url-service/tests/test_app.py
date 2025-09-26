import os
os.environ["TESTING"] = "true"

import pytest
from fastapi.testclient import TestClient
from app import app
from db import init_db, SessionLocal
from models import Link

@pytest.fixture(scope="session", autouse=True)
def test_db():
    init_db()
    yield
    os.remove("./test.db")

client = TestClient(app, follow_redirects=False)

def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_create_link():
    response = client.post("/api/links", json={"url": "https://www.google.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["url"] == "https://www.google.com/"
    assert "slug" in data
    assert "qrPng" in data

def test_list_links():
    response = client.get("/api/links")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data

def test_get_link():
    response = client.post("/api/links", json={"url": "https://www.example.com"})
    assert response.status_code == 200
    data = response.json()
    slug = data["slug"]

    response = client.get(f"/api/links/{slug}")
    assert response.status_code == 200
    data = response.json()
    assert data["url"] == "https://www.example.com/"
    assert data["slug"] == slug

def test_delete_link():
    response = client.post("/api/links", json={"url": "https://www.todelete.com"})
    assert response.status_code == 200
    data = response.json()
    id = data["id"]
    slug = data["slug"]

    response = client.delete(f"/api/links/{id}")
    assert response.status_code == 204

    response = client.get(f"/api/links/{slug}")
    assert response.status_code == 404

def test_get_qr_code():
    response = client.post("/api/links", json={"url": "https://www.qrcode.com"})
    assert response.status_code == 200
    data = response.json()
    slug = data["slug"]

    response = client.get(f"/api/links/{slug}/qr")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

def test_redirect():
    response = client.post("/api/links", json={"url": "https://www.redirect.com"})
    assert response.status_code == 200
    data = response.json()
    slug = data["slug"]

    response = client.get(f"/r/{slug}")
    assert response.status_code == 302
    assert response.headers["location"] == "https://www.redirect.com/"

    db = SessionLocal()
    link = db.query(Link).filter(Link.slug == slug).first()
    assert link.clicks == 1
    db.close()
