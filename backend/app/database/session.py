import logging
from typing import Generator
import atexit
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.database.base import Base

logger = logging.getLogger("recomai.database")

# Try connecting to PostgreSQL first
ACTIVE_DB_URL = settings.DATABASE_URL
IS_POSTGRES = True

try:
    # Test connection to configured PostgreSQL database
    test_engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        connect_args={"connect_timeout": 3}
    )
    with test_engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    logger.info("Successfully connected to primary PostgreSQL database at %s", settings.DATABASE_URL)
    engine = test_engine
except Exception as e:
    logger.warning(
        "Could not connect to PostgreSQL at '%s' (%s). "
        "Falling back to local SQLite engine (%s) to allow seamless startup.",
        settings.DATABASE_URL,
        str(e),
        settings.FALLBACK_SQLITE_URL
    )
    ACTIVE_DB_URL = settings.FALLBACK_SQLITE_URL
    IS_POSTGRES = False
    engine = create_engine(
    ACTIVE_DB_URL,
    connect_args={"check_same_thread": False} if not IS_POSTGRES else {"connect_timeout": 3},
    pool_pre_ping=True,
)

# Ensure engine connections are cleaned up when the interpreter exits
import atexit
atexit.register(lambda: engine.dispose())

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Dependency for providing a SQLAlchemy database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def check_db_connection() -> dict:
    """Return runtime diagnostic status of the database connection."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {
            "status": "connected",
            "is_postgres": IS_POSTGRES,
            "url": str(engine.url).split("@")[-1] if "@" in str(engine.url) else str(engine.url),
            "driver": engine.driver
        }
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
            "is_postgres": IS_POSTGRES
        }

def init_db():
    """Create all database tables."""
    # Import all models so metadata is populated
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info("Database schema initialized successfully.")
