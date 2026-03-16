"""
SQLAlchemy database setup.
Uses SQLite for local dev — swap SQLITE_URL for a Postgres URL in production.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

SQLITE_URL = "sqlite:///./gallery.db"

engine = create_engine(
    SQLITE_URL,
    connect_args={"check_same_thread": False},  # SQLite-only flag
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# FastAPI dependency — yields a DB session and closes it after the request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
