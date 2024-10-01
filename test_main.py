import pytest
from fastapi.testclient import TestClient
from main import app, get_db
from database import SessionLocal, engine, Base
from models import User, Todo


# Create a new session for each test
@pytest.fixture(scope="module")
def test_db():
    # Create the database schema
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    yield db
    db.close()
    # Drop the database schema after tests
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="module")
def client(test_db):
    return TestClient(app)


def test_register_user(client):
    response = client.post("/register", data={"email": "test@example.com", "password": "password123"})
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["email"] == "test@example.com"


def test_login_user(client):
    # First, register a user
    client.post("/register", data={"email": "test@example.com", "password": "password123"})
    response = client.post("/login", data={"email": "test@example.com", "password": "password123"})
    assert response.status_code == 200
    assert "user_id" in response.json()


def test_create_todo_item(client):
    # First, register a user
    client.post("/register", data={"email": "test@example.com", "password": "password123"})

    # Login to get the user ID
    login_response = client.post("/login", data={"email": "test@example.com", "password": "password123"})
    user_id = login_response.json()["user_id"]

    # Now create a TODO item
    response = client.post("/todos", data={
        "user_id": user_id,
        "name": "Test Todo",
        "description": "This is a test todo item.",
        "due_date": "2025-10-10T10:00:00"
    })

    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["name"] == "Test Todo"


def test_get_todos(client):
    # First, register a user and create a TODO
    client.post("/register", data={"email": "test@example.com", "password": "password123"})
    login_response = client.post("/login", data={"email": "test@example.com", "password": "password123"})
    user_id = login_response.json()["user_id"]

    client.post("/todos", data={
        "user_id": user_id,
        "name": "Test Todo",
        "description": "This is a test todo item.",
        "due_date": "2025-10-10T10:00:00"
    })

    # Get the todos
    response = client.get("/todos")
    assert response.status_code == 200
    assert len(response.json()["todos"]) > 0

# pytest test_main.py  <- run