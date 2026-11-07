import time
from contextlib import contextmanager
from typing import Dict, Any, Generator
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from backend.app.core.config import settings

db_url = settings.DATABASE_URL or "sqlite:///./editorial.db"

# Handle Render / Heroku postgres:// -> postgresql:// for SQLAlchemy 2.x
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

connect_args = {}
engine_kwargs = {
    "pool_pre_ping": True,
}

if db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False
else:
    # PostgreSQL connection pool configuration
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20
    engine_kwargs["pool_timeout"] = 30
    engine_kwargs["pool_recycle"] = 1800

def create_db_engine(target_url: str = None):
    """Creates a SQLAlchemy engine configured with production pooling and health invariants."""
    url = target_url or db_url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    
    c_args = {}
    e_kwargs = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        c_args["check_same_thread"] = False
    else:
        e_kwargs["pool_size"] = 10
        e_kwargs["max_overflow"] = 20
        e_kwargs["pool_timeout"] = 30
        e_kwargs["pool_recycle"] = 1800
    return create_engine(url, connect_args=c_args, **e_kwargs)

engine = create_db_engine(db_url)

# Enable Foreign Key enforcement for SQLite databases
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if db_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """Dependency for FastAPI route handlers."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """Context manager for standalone background jobs or scripts with automatic rollback on error."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def check_db_health() -> Dict[str, Any]:
    """Executes a ping query to evaluate connection health and latency."""
    start = time.perf_counter()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "status": "healthy",
            "latency_ms": latency_ms,
            "engine": "sqlite" if db_url.startswith("sqlite") else "postgresql"
        }
    except Exception as e:
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {
            "status": "unhealthy",
            "latency_ms": latency_ms,
            "error": str(e),
            "engine": "sqlite" if db_url.startswith("sqlite") else "postgresql"
        }
