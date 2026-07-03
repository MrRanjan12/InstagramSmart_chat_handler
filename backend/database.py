from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base

from backend.config import config

engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True
)

sessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db():
    db = sessionLocal()

    try:
        yield db

    finally:
        db.close()