from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship, Session
from database import Base
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from fastapi import Form


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    todos = relationship("Todo", back_populates="owner")

def create_user(db: Session, email: str, password: str):
    db_user = User(email=email, hashed_password=password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

class Todo(Base):
    __tablename__ = 'todos'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    due_date = Column(DateTime)
    status = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey('users.id'))

    owner = relationship("User", back_populates="todos")

class TodoItem(BaseModel):
    name: str
    description: Optional[str] = None
    due_date: datetime
    status: bool = False

    @classmethod
    def as_form(
            cls,
            name: str = Form(...),
            description: Optional[str] = Form(None),
            due_date: datetime = Form(...),
            status: bool = Form(False)
    ) -> "TodoItem":
        return cls(name=name, description=description, due_date=due_date, status=status)

def create_todo(db: Session, todo: TodoItem, user_id: int):
    db_todo = Todo(**todo.dict(), user_id=user_id)
    db.add(db_todo)
    db.commit()
    db.refresh(db_todo)
    return db_todo