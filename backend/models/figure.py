"""SQLAlchemy ORM model for historical figures."""
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func

from database import Base


class Figure(Base):
    __tablename__ = "figures"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    born_year = Column(Integer, nullable=True)
    died_year = Column(Integer, nullable=True)
    era = Column(String(100), nullable=True, index=True)
    origin = Column(String(100), nullable=True, index=True)
    tags = Column(String(500), nullable=True)   # comma-separated
    featured = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
