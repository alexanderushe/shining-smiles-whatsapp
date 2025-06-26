# scripts/create_tables.py
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.utils.database import Base, init_db

def create_tables():
    session = init_db()
    engine = session.bind
    Base.metadata.create_all(engine)
    print("✅ Tables created")

if __name__ == "__main__":
    create_tables()
