# scripts/test_db.py
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.database import init_db

def test_db():
    session = init_db()
    print("Database connection successful")

if __name__ == "__main__":
    test_db()