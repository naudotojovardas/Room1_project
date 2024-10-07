import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, get_db
from main import app
import random
import os
import tempfile

# --disable-warnings
os.environ["DISABLE_AUTH"] = "1"


# Create a temporary test database file
db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_file.name}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the get_db dependency to use the test database
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Apply the override to use the test database
app.dependency_overrides[get_db] = override_get_db

# Create a TestClient for testing FastAPI
client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_tables():
    print(f"Resetting database tables for: {SQLALCHEMY_DATABASE_URL}")

    # Drop all tables and recreate them. we need it because we are using the same database for all tests
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Debugging: Ensure tables are empty after reset
    db = TestingSessionLocal()
    user_count = db.query(Base.metadata.tables['users']).count()
    todo_count = db.query(Base.metadata.tables['todos']).count()
    print(f"Users in database after reset: {user_count}")
    print(f"Todos in database after reset: {todo_count}")
    db.close()

# Fixture to provide unique username and password
@pytest.fixture
def unique_user():
    unique_username = "testuser" + str(random.randint(1000, 9999))
    unique_password = "testpassword" + str(random.randint(1000, 9999))
    return {"username": unique_username, "password": unique_password}

def test_register_user(unique_user):
    # Use the unique username and password from the fixture
    response = client.post("/register", json={"username": unique_user['username'], "password": unique_user['password']})
    print(f"Register response: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == unique_user['username']
    assert "password" not in data  # Ensure the password is not returned

    # Test duplicate registration
    response = client.post("/register", json={"username": unique_user['username'], "password": unique_user['password']})
    assert response.status_code == 400
    assert response.json()["detail"] == "Username already registered"

def test_login(unique_user):
    # First, register the user
    response = client.post("/register", json={"username": unique_user['username'], "password": unique_user['password']})
    assert response.status_code == 200

    # Then, test successful login
    response = client.post(
        "/token",
        data={"username": unique_user['username'], "password": unique_user['password']},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    print(f"Login response: {response.json()}")
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

    # Test login with incorrect password
    response = client.post(
        "/token",
        data={"username": unique_user['username'], "password": "wrongpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"

    # Test login with non-existing user
    response = client.post(
        "/token",
        data={"username": "nonexistinguser", "password": "testpassword"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"


def test_create_todo_after_login(unique_user):
    # Register the user
    response = client.post("/register", json={"username": unique_user['username'], "password": unique_user['password']})
    assert response.status_code == 200

    # Login to get the access token
    response = client.post(
        "/token",
        data={"username": unique_user['username'], "password": unique_user['password']},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Use the token to create a new TODO item
    todo_data = {
        "name": "Test Todo",
        "description": "This is a test todo",
        "due_date": "2024-12-31T23:59:59",
        "status": False,
    }
    response = client.post(
        "/todos/",
        json=todo_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Todo"
    assert data["description"] == "This is a test todo"
    assert data["owner_id"] is not None

def test_get_all_todos(unique_user):
    # Register the user and log in
    response = client.post("/register", json={"username": unique_user['username'], "password": unique_user['password']})
    assert response.status_code == 200

    response = client.post(
        "/token",
        data={"username": unique_user['username'], "password": unique_user['password']},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Create multiple TODO items
    for i in range(3):
        todo_data = {
            "name": f"Test Todo {i}",
            "description": f"This is test todo {i}",
            "due_date": "2024-12-31T23:59:59",
            "status": False,
        }
        response = client.post(
            "/todos/",
            json=todo_data,
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

    # Get all TODO items
    response = client.get(
        "/todos/",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    todos = response.json()
    assert len(todos) == 3


def test_get_todo_by_id(unique_user):
    # Register and log in the user
    response = client.post("/register", json={"username": unique_user['username'], "password": unique_user['password']})
    assert response.status_code == 200

    response = client.post(
        "/token",
        data={"username": unique_user['username'], "password": unique_user['password']},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Create a TODO item
    todo_data = {
        "name": "Test Todo",
        "description": "This is a test todo",
        "due_date": "2024-12-31T23:59:59",
        "status": False,
    }
    response = client.post(
        "/todos/",
        json=todo_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    todo_id = response.json()["id"]

    # Retrieve the specific TODO item by ID
    response = client.get(
        f"/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Todo"
    assert data["description"] == "This is a test todo"

def test_update_todo_by_id(unique_user):
    # Register and log in the user
    response = client.post("/register", json={"username": unique_user['username'], "password": unique_user['password']})
    assert response.status_code == 200

    response = client.post(
        "/token",
        data={"username": unique_user['username'], "password": unique_user['password']},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Create a TODO item
    todo_data = {
        "name": "Test Todo",
        "description": "This is a test todo",
        "due_date": "2024-12-31T23:59:59",
        "status": False,
    }
    response = client.post(
        "/todos/",
        json=todo_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    todo_id = response.json()["id"]

    # Update the TODO item
    updated_todo_data = {
        "name": "Updated Test Todo",
        "description": "This is an updated test todo",
        "due_date": "2024-12-31T23:59:59",
        "status": True,
    }
    response = client.put(
        f"/todos/{todo_id}",
        json=updated_todo_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Test Todo"
    assert data["status"] is True

def test_delete_todo_by_id(unique_user):
    # Register and log in the user
    response = client.post("/register", json={"username": unique_user['username'], "password": unique_user['password']})
    assert response.status_code == 200

    response = client.post(
        "/token",
        data={"username": unique_user['username'], "password": unique_user['password']},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]

    # Create a TODO item
    todo_data = {
        "name": "Test Todo",
        "description": "This is a test todo",
        "due_date": "2024-12-31T23:59:59",
        "status": False,
    }
    response = client.post(
        "/todos/",
        json=todo_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    todo_id = response.json()["id"]

    # Delete the TODO item
    response = client.delete(
        f"/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Todo deleted successfully"}

    # Verify the TODO item was deleted
    response = client.get(
        f"/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Todo not found"



# run test: pytest test_auth.py or  pytest -v