import pytest
from uuid import UUID
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool

from app.main import app, verify_api_key
from app.database import get_session
from app.models import Task, TaskStatus

# Clé API valide pour les tests
VALID_API_KEY = "test-token-123"

# Montage d'une base de données SQLite en mémoire pour les tests unitaires
@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    # Remplacement du générateur de session par la session de test en mémoire
    def get_session_override():
        return session
    
    app.dependency_overrides[get_session] = get_session_override
    
    # Remplacement des clés API valides par notre clé de test
    from app.config import settings
    settings.API_KEYS_RAW = VALID_API_KEY
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()

def test_verify_api_key_required(client: TestClient):
    # Sans clé API, l'accès doit être refusé (401)
    response = client.get("/api/v1/tasks")
    assert response.status_code == 401
    assert "clé API est manquante" in response.json()["detail"]

def test_verify_api_key_invalid(client: TestClient):
    # Avec une clé API incorrecte, l'accès doit être refusé (403)
    response = client.get("/api/v1/tasks", headers={"X-API-Key": "mauvaise-cle"})
    assert response.status_code == 403
    assert "Clé API invalide" in response.json()["detail"]

def test_create_and_read_task(client: TestClient):
    headers = {"X-API-Key": VALID_API_KEY}
    
    # 1. Création d'une tâche
    payload = {
        "title": "Acheter du pain",
        "description": "Prendre une tradition bien cuite",
        "status": "A faire"
    }
    response = client.post("/api/v1/tasks", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Acheter du pain"
    assert "id" in data
    assert "created_at" in data
    task_id = data["id"]
    
    # 2. Lecture de la tâche spécifique
    response = client.get(f"/api/v1/tasks/{task_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Acheter du pain"

def test_update_task_status(client: TestClient):
    headers = {"X-API-Key": VALID_API_KEY}
    
    # 1. Création
    payload = {"title": "Coder l'API"}
    response = client.post("/api/v1/tasks", json=payload, headers=headers)
    task_id = response.json()["id"]
    
    # 2. Passage à "En cours"
    response = client.put(f"/api/v1/tasks/{task_id}", json={"status": "En cours"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "En cours"
    
    # 3. Passage à "Termine"
    response = client.put(f"/api/v1/tasks/{task_id}", json={"status": "Termine"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "Termine"

def test_delete_task(client: TestClient):
    headers = {"X-API-Key": VALID_API_KEY}
    
    # 1. Création
    payload = {"title": "Tâche éphémère"}
    response = client.post("/api/v1/tasks", json=payload, headers=headers)
    task_id = response.json()["id"]
    
    # 2. Suppression
    response = client.delete(f"/api/v1/tasks/{task_id}", headers=headers)
    assert response.status_code == 204
    
    # 3. Vérification de la disparition (404)
    response = client.get(f"/api/v1/tasks/{task_id}", headers=headers)
    assert response.status_code == 404
