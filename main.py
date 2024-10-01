from fastapi import FastAPI, Depends, Request, Form, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List
from fastapi.staticfiles import StaticFiles
from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError 

# importing schema classes
import schemas
from schemas import TodoCreate, TodoUpdate, TodoResponse 
import models
from models import User, Todo
from database import SessionLocal, engine, Base


# Define the OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Create FastAPI instance
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Initialize the database
Base.metadata.create_all(bind=engine)

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Password hashing settings
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Hash the password
# def hash_password(password: str) -> str:
#     return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Password hashing and verification functions
def get_password_hash(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(datetime.timezone.utc)() + expires_delta
    else:
        expire = datetime.now(datetime.timezone.utc)() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ----- Authentication and Registration -----
# FastAPI route handlers for user registration and login.

# def authenticate_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
#     # Validate token and return the user
#     user = db.query(User).filter(User.email == "test@example.com").first()
#     if user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
#     return user

def authenticate_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# HTML for registration
@app.get("/register", response_class=HTMLResponse)
async def get_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

# @app.post("/register")
# async def register_user(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
#     existing_user = db.query(User).filter(User.email == email).first()
#     if existing_user:
#         return {"error": "User already exists"}

#     hashed_password = hash_password(password)
#     new_user = create_user(db, email=email, password=hashed_password)
#     return {"id": new_user.id, "email": new_user.email}

# User registration
@app.post("/register")
async def post_register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    db: Session = Depends(get_db)
):
    if password != confirm_password:
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "error": "Passwords do not match"
        })
    
    hashed_password = pwd_context.hash(password)
    new_user = User(email=email, hashed_password=hashed_password)
    
    db.add(new_user)
    db.commit()
    
    return RedirectResponse(url="/login", status_code=303)

# HTML for login
@app.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# @app.post("/login")
# async def login_user(email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
#     db_user = db.query(User).filter(User.email == email).first()
#     if not db_user or not bcrypt.checkpw(password.encode('utf-8'), db_user.hashed_password.encode('utf-8')):
#         return {"error": "Invalid credentials"}

#     return {"message": "Login successful", "user_id": db_user.id}

# User login
@app.post("/login")
async def post_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    
    if not user or not pwd_context.verify(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Invalid credentials"
        })
    
    # You can add JWT token creation here for session management if needed
    return RedirectResponse(url="/", status_code=303)

# HTML for TODO items
# HTML for TODO items
# @app.get("/todos", response_class=HTMLResponse)
# async def get_todos(request: Request, db: Session = Depends(get_db)):
#     todos = db.query(Todo).all()
#     users = db.query(User).all()  # Fetch all users for the dropdown
#     return templates.TemplateResponse("todos.html", {"request": request, "todos": todos, "users": users})

# Get all TODO items for the current user
@app.get("/todos") 
async def get_todos(db: Session = Depends(get_db), current_user: User = Depends(authenticate_user)):
    todos = db.query(Todo).filter(Todo.owner_id == current_user.id).all()
    return todos

# Function to create a TODO item (post request)
# @app.post("/todos")
# async def create_todo_item(
#     user_id: int = Form(...),  # Ensure user_id is included in the form
#     todo: TodoItem = Depends(TodoItem.as_form),
#     db: Session = Depends(get_db)
# ):
#     new_todo = create_todo(db, todo=todo, user_id=user_id)
#     return {"id": new_todo.id, "name": new_todo.name}

# Create a new TODO item
@app.post("/todos", response_model=schemas.TodoResponse)
async def create_todo(todo: schemas.TodoCreate, db: Session = Depends(get_db), current_user: models.User = Depends(authenticate_user)):
    new_todo = models.Todo(
        name=todo.name,
        description=todo.description,
        due_date=todo.due_date,
        status=todo.status,
        owner_id=current_user.id
    )
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)
    
    return new_todo

# Delete a TODO item
@app.delete("/todos/{todo_id}", response_model=dict)
async def delete_todo(todo_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(authenticate_user)):
    todo_item = db.query(models.Todo).filter(models.Todo.id == todo_id, models.Todo.owner_id == current_user.id).first()
    if not todo_item:
        raise HTTPException(status_code=404, detail="Todo not found")

    db.delete(todo_item)
    db.commit()

    return {"message": "Todo deleted successfully"}

# Update a TODO item
@app.put("/todos/{todo_id}", response_model=schemas.TodoResponse)
async def update_todo(todo_id: int, todo: schemas.TodoUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(authenticate_user)):
    todo_item = db.query(models.Todo).filter(models.Todo.id == todo_id, models.Todo.owner_id == current_user.id).first()
    if not todo_item:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    for key, value in todo.dict().items():
        setattr(todo_item, key, value) if value else None

    db.commit()
    db.refresh(todo_item)
    
    return

# Run the FastAPI application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000)


