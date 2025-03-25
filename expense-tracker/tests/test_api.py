import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_user(test_db):
    with TestClient(app) as client:
        response = client.post(
            "/users/",
            json={"email": "test@example.com", "password": "testpass123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"

def test_create_transaction(test_db):
    with TestClient(app) as client:
        # First create and login user
        client.post("/users/", json={"email": "test@example.com", "password": "testpass123"})
        login_response = client.post("/token", data={"username": "test@example.com", "password": "testpass123"})
        token = login_response.json()["access_token"]
        
        # Create transaction
        response = client.post(
            "/transactions/",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "amount": 100.0,
                "category": "groceries",
                "description": "Weekly groceries",
                "type": "expense"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["amount"] == 100.0
        assert data["category"] == "groceries"
