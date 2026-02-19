"""Database connection and session utilities."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DB_FILE = Path(__file__).resolve().parents[2] / "finance_copilot.db"
DATABASE_URL = f"sqlite:///{DB_FILE}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
