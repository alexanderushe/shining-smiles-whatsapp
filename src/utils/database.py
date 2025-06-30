# src/utils/database.py
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import sys
import datetime

Base = declarative_base()

class StudentContact(Base):
    __tablename__ = "student_contacts"
    id = Column(Integer, primary_key=True)
    student_id = Column(String, unique=True, nullable=False)
    firstname = Column(String, nullable=True)
    lastname = Column(String, nullable=True)
    student_mobile = Column(String, nullable=True)
    guardian_mobile_number = Column(String, nullable=True)
    preferred_phone_number = Column(String, nullable=False)
    email = Column(String, nullable=True)
    address = Column(String, nullable=True)
    preferred_contact_method = Column(String, nullable=True)  # whatsapp, sms, email
    emergency_contact_name = Column(String, nullable=True)
    emergency_contact_number = Column(String, nullable=True)
    preferred_language = Column(String, default="en")  # e.g., en, sn
    verification_code = Column(String, nullable=True)  # For WhatsApp verification
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    """Initialize database connection and return a session."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("⚠️  WARNING: DATABASE_URL not set. Defaulting to local SQLite database.", file=sys.stderr)
        print("📦 Using: sqlite:///data/contacts.db", file=sys.stderr)
        db_url = "sqlite:///data/contacts.db"
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://")  # Heroku compatibility
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()