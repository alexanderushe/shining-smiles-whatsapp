# scripts/reset_db.py
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.database import init_db, StudentContact
from sqlalchemy import create_engine
from config import get_config

def reset_db():
    config = get_config()
    db_url = os.getenv("DATABASE_URL", "sqlite:///data/contacts.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://")
    engine = create_engine(db_url)
    StudentContact.__table__.drop(engine, checkfirst=True)
    StudentContact.__table__.create(engine)
    print("Database table reset")

if __name__ == "__main__":
    reset_db()