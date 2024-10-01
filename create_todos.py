import requests

# Base URL
BASE_URL = "http://127.0.0.1:8000"

# User credentials
user_email = "test@example.com"
user_password = "yourpassword"

# Register
def register_user(email, password):
    response = requests.post(f"{BASE_URL}/register", json={"email": email, "password": password})
    if response.status_code == 200:
        print("User registered successfully!")
    else:
        print(f"Failed to register user: {response.status_code} - {response.text}")

# Log get the access token
def login_user(email, password):
    response = requests.post(f"{BASE_URL}/token", data={"username": email, "password": password})
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Failed to log in: {response.status_code} - {response.text}")
        return None

# Create TODO item
def create_todo(access_token, name, description, due_date, status=False):
    headers = {"Authorization": f"Bearer {access_token}"}
    todo_data = {
        "name": name,
        "description": description,
        "due_date": due_date,
        "status": status,
    }
    response = requests.post(f"{BASE_URL}/todos/", headers=headers, json=todo_data)
    if response.status_code == 200:
        print("TODO created successfully:", response.json())
    else:
        print(f"Failed to create TODO: {response.status_code} - {response.text}")

if __name__ == "__main__":
    # Step 1: Register the user
    register_user(user_email, user_password)

   # Log in the user
    token = login_user(user_email, user_password)

    if token:
        #Create TODO items
        create_todo(token, "Learn FastAPI", "Study the FastAPI documentation.", "2024-01-01T00:00:00")
        create_todo(token, "Build TODO app", "Develop a TODO application using FastAPI.", "2024-01-15T00:00:00")
