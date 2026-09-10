import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from krishiayan.api.main import app
from krishiayan.core.db import Base, get_db
from krishiayan.models import entities  # noqa: F401
from krishiayan.services.crops import seed_crops

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=engine)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db


@pytest.fixture
def db():
    db = TestingSession()
    seed_crops(db)
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db):
    return TestClient(app)


@pytest.fixture
def auth_headers(client):
    r = client.post(
        "/v1/auth/register",
        json={"email": "farmer@example.com", "password": "soilguide", "full_name": "Test Farmer"},
    )
    if r.status_code == 409:
        r = client.post(
            "/v1/auth/login",
            json={"email": "farmer@example.com", "password": "soilguide"},
        )
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
