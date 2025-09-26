import os, pathlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

if os.getenv("DATABASE_URL"): 
    DATABASE_URL = os.getenv("DATABASE_URL")
else:
    DATABASE_URL = "sqlite:///./data/shorty.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    from models import Base
    Base.metadata.create_all(bind=engine)

