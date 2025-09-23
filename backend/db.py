import os, pathlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

DB_PATH = os.getenv("DB_PATH", "data/shorty.db")
pathlib.Path(os.path.dirname(DB_PATH)).mkdir(parents=True, exist_ok=True)

# SQLite connection: check_same_thread=False allows use across threads in FastAPI
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def init_db():
    Base.metadata.create_all(engine)
