from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# User creation model
class UserCreate(BaseModel):
    email: str
    password: str

# User login model
class UserLogin(BaseModel):
    email: str
    password: str

# TODO creation model
class TodoCreate(BaseModel):
    name: str
    description: str
    due_date: datetime
    status: Optional[bool] = False

# TODO update model
class TodoUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[bool] = None

# Response model for TODOs
class TodoResponse(BaseModel):
    id: int
    name: str
    description: str
    due_date: datetime
    status: bool

    class Config:
        orm_mode = True
