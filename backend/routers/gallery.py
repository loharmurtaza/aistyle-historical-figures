from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from database import get_db
from models.schemas import GalleryItem, GalleryResponse
from services.gallery import (
    get_gallery,
    get_portrait_by_id,
    delete_portrait,
    get_featured_portraits,
)

router = APIRouter(tags=["gallery"])


@router.get("/gallery", response_model=GalleryResponse)
def list_gallery(
    page: int = 1,
    page_size: int = 20,
    style: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Paginated gallery with optional style filter."""
    return get_gallery(db, page=page, page_size=page_size, style=style)


@router.get("/gallery/featured")
def list_featured(figures: str, db: Session = Depends(get_db)):
    """Return the latest portrait ID for each comma-separated figure name."""
    terms = [t.strip() for t in figures.split(",") if t.strip()]
    return get_featured_portraits(db, terms)


@router.get("/gallery/{portrait_id}", response_model=GalleryItem)
def get_portrait(portrait_id: int, db: Session = Depends(get_db)):
    portrait = get_portrait_by_id(db, portrait_id)
    if not portrait:
        raise HTTPException(status_code=404, detail="Portrait not found")
    return GalleryItem.model_validate(portrait)


@router.get("/gallery/{portrait_id}/image")
def get_portrait_image(portrait_id: int, db: Session = Depends(get_db)):
    """Serve the stored image bytes for a portrait."""
    portrait = get_portrait_by_id(db, portrait_id)
    if not portrait:
        raise HTTPException(status_code=404, detail="Portrait not found")
    if not portrait.image_data:
        raise HTTPException(
            status_code=404,
            detail="No image data stored for this portrait",
        )
    return Response(content=portrait.image_data, media_type="image/png")


@router.delete("/gallery/{portrait_id}")
def remove_portrait(portrait_id: int, db: Session = Depends(get_db)):
    if not delete_portrait(db, portrait_id):
        raise HTTPException(status_code=404, detail="Portrait not found")
    return {"message": "Portrait deleted", "id": portrait_id}
