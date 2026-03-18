from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models.portrait import Portrait
from models.figure import Figure
from models.style import Style
from models.schemas import StatsResponse

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=StatsResponse)
def get_stats(db: Session = Depends(get_db)):
    """Return live platform statistics."""
    portraits_created = db.query(func.count(Portrait.id)).scalar() or 0
    unique_figures = db.query(func.count(Figure.id)).scalar() or 0
    styles_available = db.query(func.count(Style.id)).scalar() or 0
    return StatsResponse(
        portraits_created=portraits_created,
        unique_figures=unique_figures,
        styles_available=styles_available,
    )
