# ./Sentra-DiscordBot/Bot/DB/dbLink.py
# Connects to the database and creates the tables (if they don't exist)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..config import Config
from .dbAccessLayer import Base 

engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Syncs your dbAccessLayer models with your Postgres server"""
    
    Base.metadata.create_all(bind=engine)

def get_session():
    return SessionLocal()