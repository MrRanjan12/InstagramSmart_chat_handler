import time
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base

from backend.config import config

db_url = config.DATABASE_URL or ""
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine_kwargs = {
    "pool_pre_ping": True,
}

if "postgresql" in db_url:
    engine_kwargs.update({
        "pool_recycle": 300,
        "pool_size": 10,
        "max_overflow": 20,
        "connect_args": {
            "connect_timeout": 15,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        }
    })
elif "sqlite" in db_url:
    engine_kwargs.update({
        "connect_args": {"check_same_thread": False}
    })

engine = create_engine(
    db_url,
    **engine_kwargs
)

sessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency for route handlers.
    """
    db = sessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context(max_retries: int = 3, retry_delay: float = 2.0):
    """
    Resilient context manager for database sessions in background tasks.
    Automatically retries on transient connection issues (e.g. Neon cold starts).
    """
    db = None
    for attempt in range(1, max_retries + 1):
        try:
            db = sessionLocal()
            db.execute(text("SELECT 1"))
            break
        except Exception as e:
            if db:
                db.close()
                db = None
            if attempt == max_retries:
                print(f"[DATABASE] Connection failed after {max_retries} attempts: {e}")
                raise e
            print(f"[DATABASE] Neon wake-up / reconnect attempt {attempt}/{max_retries} in {retry_delay}s... ({e})")
            time.sleep(retry_delay)

    try:
        yield db
        db.commit()
    except Exception:
        if db:
            db.rollback()
        raise
    finally:
        if db:
            db.close()