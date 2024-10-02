# todo.py
from fastapi import Depends, APIRouter, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from database import SessionLocal, Todo
from auth import get_current_user, User  # Import the user retrieval function

router = APIRouter()

# Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class TodoCreate(BaseModel):
    name: str
    description: str
    due_date: datetime
    status: bool = False

class TodoUpdate(BaseModel):
    name: str
    description: str
    due_date: datetime
    status: bool

class TodoInDB(TodoCreate):
    id: int
    owner_id: int

@router.post("/", response_model=TodoInDB)
def create_todo(todo: TodoCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    new_todo = Todo(**todo.dict(), owner_id=user.id)
    db.add(new_todo)
    db.commit()
    db.refresh(new_todo)
    return new_todo

@router.get("/{todo_id}", response_model=TodoInDB)
def read_todo(todo_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    todo = db.query(Todo).filter(Todo.id == todo_id, Todo.owner_id == user.id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@router.put("/{todo_id}", response_model=TodoInDB)
def update_todo(todo_id: int, todo: TodoUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    existing_todo = db.query(Todo).filter(Todo.id == todo_id, Todo.owner_id == user.id).first()
    if not existing_todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    for key, value in todo.dict().items():
        setattr(existing_todo, key, value)
    db.commit()
    db.refresh(existing_todo)
    return existing_todo

@router.delete("/{todo_id}")
def delete_todo(todo_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    todo = db.query(Todo).filter(Todo.id == todo_id, Todo.owner_id == user.id).first()
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    db.delete(todo)
    db.commit()
    return {"detail": "Todo deleted successfully"}

@router.get("/")
def get_all_todos(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    todos = db.query(Todo).filter(Todo.owner_id == user.id).all()
    return todos

# Include the router in the main FastAPI app
# This should be done in the main.py file.
