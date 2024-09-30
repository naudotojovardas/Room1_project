# todo_app/
# │
# ├── main.py                # Main application file
# └── models.py              # Database models
# └── schemas.py             # Pydantic models for data validation
# └── database.py            # Database connection and setup


from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base


# SQLite database URL
DATABASE_URL = "sqlite:///./todo_app.db"

# Create the database engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# test connection
Base.metadata.create_all(bind=engine)

# User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    todos = relationship("Todo", back_populates="owner")
    # todos = Column(Integer, ForeignKey("todos.id"))

# Todo model
class Todo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, index=True)
    due_date = Column(String, index=True)
    status = Column(Boolean, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="todos")






