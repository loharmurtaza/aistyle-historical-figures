"""Gallery CRUD service — auto-save, paginate, filter, delete."""
from typing import Optional
from sqlalchemy.orm import Session

from models.portrait import Portrait
from models.schemas import GalleryItem, GalleryResponse


def save_portrait(
    db: Session,
    figure: str,
    style: str,
    prompt: str,
    enhanced_prompt: str,
    image_url: str,
    image_data: bytes | None = None,
) -> Portrait:
    """Persist a generated portrait to the gallery."""
    portrait = Portrait(
        figure=figure,
        style=style,
        prompt=prompt,
        enhanced_prompt=enhanced_prompt,
        image_url=image_url,
        image_data=image_data,
    )
    db.add(portrait)
    db.commit()
    db.refresh(portrait)
    return portrait


def get_gallery(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    style: Optional[str] = None,
) -> GalleryResponse:
    """Return a paginated, optionally style-filtered list of portraits."""
    query = db.query(Portrait)
    if style:
        query = query.filter(Portrait.style.ilike(f"%{style}%"))

    total = query.count()
    items = (
        query.order_by(Portrait.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return GalleryResponse(
        items=[GalleryItem.model_validate(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_featured_portraits(
    db: Session, search_terms: list[str]
) -> list[dict]:
    """Return the latest portrait ID for each search term (ilike match)."""
    results = []
    for term in search_terms:
        portrait = (
            db.query(Portrait)
            .filter(Portrait.figure.ilike(f"%{term}%"))
            .order_by(Portrait.created_at.desc())
            .first()
        )
        results.append({
            "search_term": term,
            "id": portrait.id if portrait else None,
        })
    return results


def get_portrait_by_id(db: Session, portrait_id: int) -> Optional[Portrait]:
    return db.query(Portrait).filter(Portrait.id == portrait_id).first()


def delete_portrait(db: Session, portrait_id: int) -> bool:
    portrait = get_portrait_by_id(db, portrait_id)
    if not portrait:
        return False
    db.delete(portrait)
    db.commit()
    return True
