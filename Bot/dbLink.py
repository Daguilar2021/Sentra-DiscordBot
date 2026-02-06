from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .config import Config
from .dbAccessLayer import Base # Using your specific filename

# The engine uses the DATABASE_URL which contains your password
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Syncs your dbAccessLayer models with your Postgres server"""
    # This won't overwrite existing data, just ensures tables exist
    Base.metadata.create_all(bind=engine)

def get_session():
    return SessionLocal()