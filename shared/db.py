"""Database helpers for the bot."""

#region Imports

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

#endregion


#region Setup

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DATA_DIR, "scheduled_events.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DATABASE_URL,
    future=True,
    echo=False,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

#endregion


#region Helpers

def init_db() -> None:
    """Initialize database settings and create tables."""
    os.makedirs(DATA_DIR, exist_ok=True)
    Base.metadata.create_all(bind=engine)
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA journal_mode=WAL;")

#endregion
