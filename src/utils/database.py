# src/utils/database.py
from sqlalchemy import create_engine, Column, String, Integer, DateTime, ForeignKey
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
    last_updated = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))

class GatePass(Base):
    __tablename__ = "gate_passes"
    id = Column(Integer, primary_key=True)
    student_id = Column(String, ForeignKey("student_contacts.student_id"), nullable=False)
    pass_id = Column(String, unique=True, nullable=False)  # Unique identifier for gate pass
    issued_date = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    expiry_date = Column(DateTime, nullable=False)
    payment_percentage = Column(Integer, nullable=False)  # e.g., 50, 75, 100
    whatsapp_number = Column(String, nullable=False)  # Tied to preferred_phone_number
    last_updated = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    pdf_path = Column(String, nullable=True)  # Temporary path for PDF file
    qr_path = Column(String, nullable=True)  # Temporary path for QR code file

def init_db():
    """Initialize database connection and return a session."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("⚠️  WARNING: DATABASE_URL not set. Defaulting to local SQLite database.", file=sys.stderr)
        print("📦 Using: sqlite:///data/contacts.db", file=sys.stderr)
        db_url = "sqlite:///data/contacts.db"
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://")
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()