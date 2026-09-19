import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings:
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "RECOMAI")
    PROJECT_TAGLINE: str = os.getenv("PROJECT_TAGLINE", "Discover what fits you, powered by intelligence.")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX", "/api/v1")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "recomai-secret-key-cse-portfolio-2026")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # Database URLs
    # Primary required: PostgreSQL with psycopg3 driver
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql+psycopg://postgres:postgres@localhost:5432/recomai_db"
    )
    FALLBACK_SQLITE_URL: str = os.getenv(
        "FALLBACK_SQLITE_URL",
        f"sqlite:///{BASE_DIR / 'recomai_local.db'}"
    )

    # MAX AI engine settings
    MAX_EMBEDDING_DIM: int = int(os.getenv("MAX_EMBEDDING_DIM", "64"))
    MAX_MODEL_NAME: str = os.getenv("MAX_MODEL_NAME", "modular-max-semantic-base")

    # Mojo engine settings
    MOJO_ENABLED: bool = os.getenv("MOJO_ENABLED", "True").lower() in ("true", "1", "yes")
    MOJO_BIN_PATH: str = os.getenv("MOJO_BIN_PATH", "mojo")
    MOJO_MODULE_PATH: Path = BASE_DIR / "backend" / "app" / "mojo"

settings = Settings()
