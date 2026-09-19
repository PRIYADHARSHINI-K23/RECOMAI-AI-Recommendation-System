"""Script to initialize and seed the RECOMAI database."""
import sys
import logging
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from app.database.session import init_db, SessionLocal, check_db_connection
from app.database.seed_data import seed_database

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("recomai.init_db")

def main():
    logger.info("Checking database connection status...")
    db_status = check_db_connection()
    logger.info("Connection status: %s", db_status)

    logger.info("Creating all database tables...")
    init_db()

    logger.info("Seeding categories, items, demo users, and interactions...")
    with SessionLocal() as db:
        seed_database(db)

    logger.info("RECOMAI database initialized and seeded successfully!")

if __name__ == "__main__":
    main()
