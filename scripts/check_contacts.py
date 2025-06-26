# scripts/check_contacts.py
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.utils.database import init_db, StudentContact

def check_contacts():
    session = init_db()
    contacts = session.query(StudentContact).all()
    for contact in contacts:
        print(f"Student ID: {contact.student_id}, Phone: {contact.phone_number}")

if __name__ == "__main__":
    check_contacts()