# todo_app/
# │
# ├── main.py                # Main application file
# └── models.py              # Database models
# └── schemas.py             # Pydantic models for data validation
# └── database.py            # Database connection and setup


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base



# SQLite database URL
DATABASE_URL = "sqlite:///./todo_app.db"

# Create the database engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# test connection
Base.metadata.create_all(bind=engine)


