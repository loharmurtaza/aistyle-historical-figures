from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.style import Style
from models.schemas import StylesResponse

router = APIRouter(tags=["styles"])

FALLBACK_STYLES = [
    "baroque",
    "renaissance",
    "impressionism",
    "art deco",
    "watercolor",
    "anime",
    "pop art",
    "cubism",
    "minimalist",
    "photorealistic",
    "sketch",
    "oil painting",
    "digital art",
]


@router.get("/styles", response_model=StylesResponse)
def get_styles(db: Session = Depends(get_db)):
    """Returns the list of supported art styles from the database."""
    styles = db.query(Style.name).order_by(Style.name).all()
    names = [row.name for row in styles]
    return StylesResponse(styles=names if names else FALLBACK_STYLES)
