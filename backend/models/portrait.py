"""SQLAlchemy ORM model for the portrait gallery."""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, LargeBinary

from database import Base


class Portrait(Base):
    __tablename__ = "portraits"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    figure = Column(String(255), nullable=False, index=True)
    style = Column(String(100), nullable=False, index=True)
    prompt = Column(Text, nullable=False)           # raw user input
    enhanced_prompt = Column(Text, nullable=False)  # GPT-4o-mini output
    image_url = Column(Text, nullable=False)
    image_data = Column(LargeBinary, nullable=True)  # stored image bytes
    # Python-side default gives unique timestamps even for rapid inserts
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
