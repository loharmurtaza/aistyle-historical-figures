"""SQLAlchemy ORM model for art styles."""
from sqlalchemy import Column, Integer, String

from database import Base


class Style(Base):
    __tablename__ = "styles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
