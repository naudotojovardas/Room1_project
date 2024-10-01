from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from models import User, Todo, create_user, create_todo, TodoItem
from database import SessionLocal, engine, Base
import bcrypt
from datetime import datetime
from typing import Optional
import os
import subprocess
from fastapi import FastAPI, HTTPException

def install_requirements():
    requirements_file = "requirements.txt"
    if os.path.exists(requirements_file):
        try:
            subprocess.check_call(["pip", "install", "-r", requirements_file])
            print(f"Requirements from {requirements_file} installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Error occurred while installing requirements: {e}")
            raise HTTPException(status_code=500, detail="Could not install requirements.")
    else:
        print(f"{requirements_file} not found.")






# Create FastAPI instance
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Initialize the database
Base.metadata.create_all(bind=engine)

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Hash the password
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# HTML for registration
@app.get("/register", response_class=HTMLResponse)
async def get_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register")
async def register_user(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return {"error": "User already exists"}

    hashed_password = hash_password(password)
    new_user = create_user(db, email=email, password=hashed_password)
    return {"id": new_user.id, "email": new_user.email}

# HTML for login
@app.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login_user(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == email).first()
    if not db_user or not bcrypt.checkpw(password.encode('utf-8'), db_user.hashed_password.encode('utf-8')):
        return {"error": "Invalid credentials"}

    return {"message": "Login successful", "user_id": db_user.id}

# HTML for TODO items
# HTML for TODO items
@app.get("/todos", response_class=HTMLResponse)
async def get_todos(request: Request, db: Session = Depends(get_db)):
    todos = db.query(Todo).all()
    users = db.query(User).all()  # Fetch all users for the dropdown
    return templates.TemplateResponse("todos.html", {"request": request, "todos": todos, "users": users})

# Function to create a TODO item (post request)
@app.post("/todos")
async def create_todo_item(
    user_id: int = Form(...),  # Ensure user_id is included in the form
    todo: TodoItem = Depends(TodoItem.as_form),
    db: Session = Depends(get_db)
):
    new_todo = create_todo(db, todo=todo, user_id=user_id)
    return {"id": new_todo.id, "name": new_todo.name}


install_requirements()