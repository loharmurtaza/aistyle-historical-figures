from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import distinct, or_
from sqlalchemy.orm import Session

from database import get_db
from models.figure import Figure
from models.schemas import (
    FigureCreate, FigureItem, FiguresMetaResponse, FiguresResponse,
)
from services.figures_index import figures_index

router = APIRouter(tags=["figures"])

_FALLBACK_TS = datetime(2024, 1, 1, tzinfo=timezone.utc)

FALLBACK_FIGURES: list[FigureItem] = [
    FigureItem(
        id=0, name="Cleopatra VII", slug="cleopatra-vii",
        description="Last active pharaoh of ancient Egypt, famed for her "
        "intellect and political alliances.",
        born_year=-69, died_year=-30, era="Ancient Egypt", origin="Egypt",
        tags="ruler, military", featured=True, created_at=_FALLBACK_TS),
    FigureItem(
        id=0, name="Raja Dahir", slug="raja-dahir",
        description="Last Hindu ruler of Sindh, who stood against the Arab "
        "invasion of 711 CE.",
        born_year=663, died_year=712, era="Early Medieval", origin="Sindh",
        tags="ruler, military", featured=True, created_at=_FALLBACK_TS),
    FigureItem(
        id=0, name="Leonardo da Vinci", slug="leonardo-da-vinci",
        description="Italian Renaissance polymath — painter, scientist, "
        "engineer, and anatomist.",
        born_year=1452, died_year=1519, era="Renaissance", origin="Italy",
        tags="artist, scientist, engineer", featured=True,
        created_at=_FALLBACK_TS),
    FigureItem(
        id=0, name="Napoleon Bonaparte", slug="napoleon-bonaparte",
        description="French military genius who rose to become Emperor "
        "and reshaped modern Europe.",
        born_year=1769, died_year=1821, era="Napoleonic Era", origin="France",
        tags="ruler, military", featured=True, created_at=_FALLBACK_TS),
    FigureItem(
        id=0, name="Nikola Tesla", slug="nikola-tesla",
        description="Serbian-American inventor who pioneered alternating "
        "current and wireless technology.",
        born_year=1856, died_year=1943, era="Industrial Revolution",
        origin="Serbia", tags="scientist, engineer", featured=True,
        created_at=_FALLBACK_TS),
    FigureItem(
        id=0, name="Marie Curie", slug="marie-curie",
        description="Polish-French physicist and chemist, first person to win "
        "Nobel Prizes in two sciences.",
        born_year=1867, died_year=1934, era="Modern Era", origin="Poland",
        tags="scientist, physician", featured=True, created_at=_FALLBACK_TS),
    FigureItem(
        id=0, name="Genghis Khan", slug="genghis-khan",
        description="Founder and first Great Khan of the Mongol Empire, the "
        "largest contiguous land empire in history.",
        born_year=1162, died_year=1227, era="Medieval", origin="Mongolia",
        tags="ruler, military", featured=True, created_at=_FALLBACK_TS),
    FigureItem(
        id=0, name="Albert Einstein", slug="albert-einstein",
        description="German-born theoretical physicist who developed the "
        "theory of relativity.",
        born_year=1879, died_year=1955, era="Modern Era", origin="Germany",
        tags="scientist, philosopher", featured=True, created_at=_FALLBACK_TS),
]


def _split(value: Optional[str]) -> list[str]:
    """Split a comma-separated filter string into a clean list."""
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


@router.get("/figures", response_model=FiguresResponse)
def list_figures(
    page: int = 1,
    page_size: int = 50,
    era: Optional[str] = None,
    origin: Optional[str] = None,
    tags: Optional[str] = None,
    featured: Optional[bool] = None,
    born_year_min: Optional[int] = None,
    born_year_max: Optional[int] = None,
    q: Optional[str] = Query(None, description="Search by name, origin or era"),
    db: Session = Depends(get_db),
):
    """Paginated list of historical figures with optional filters."""
    query = db.query(Figure)

    if q:
        query = query.filter(
            or_(
                Figure.name.ilike(f"%{q}%"),
                Figure.origin.ilike(f"%{q}%"),
                Figure.era.ilike(f"%{q}%"),
            )
        )

    era_list = _split(era)
    if era_list:
        query = query.filter(or_(*[Figure.era.ilike(f"%{e}%") for e in era_list]))

    origin_list = _split(origin)
    if origin_list:
        query = query.filter(or_(*[Figure.origin.ilike(f"%{o}%") for o in origin_list]))

    tag_list = _split(tags)
    if tag_list:
        query = query.filter(or_(*[Figure.tags.ilike(f"%{t}%") for t in tag_list]))

    if featured is not None:
        query = query.filter(Figure.featured == featured)

    if born_year_min is not None:
        query = query.filter(Figure.born_year >= born_year_min)
    if born_year_max is not None:
        query = query.filter(Figure.born_year <= born_year_max)

    total = query.count()

    any_filter = any([q, era, origin, tags, featured is not None,
                      born_year_min is not None, born_year_max is not None])
    if total == 0 and not any_filter:
        return FiguresResponse(
            items=FALLBACK_FIGURES,
            total=len(FALLBACK_FIGURES),
            page=1,
            page_size=len(FALLBACK_FIGURES),
        )

    items = (
        query.order_by(Figure.name)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return FiguresResponse(
        items=[FigureItem.model_validate(f) for f in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/figures", response_model=FigureItem, status_code=status.HTTP_201_CREATED)
def create_figure(payload: FigureCreate, db: Session = Depends(get_db)):
    """Create a new historical figure."""
    slug = payload.name.lower().strip()
    slug = "".join(c if c.isalnum() or c == " " else "" for c in slug)
    slug = "-".join(slug.split())

    if db.query(Figure).filter(Figure.slug == slug).first():
        raise HTTPException(status_code=409, detail="A figure with this name already exists.")

    figure = Figure(
        name=payload.name.strip(),
        slug=slug,
        description=payload.description,
        born_year=payload.born_year,
        died_year=payload.died_year,
        era=payload.era,
        origin=payload.origin,
        tags=payload.tags,
        featured=payload.featured,
    )
    db.add(figure)
    db.commit()
    db.refresh(figure)
    figures_index.invalidate()
    return FigureItem.model_validate(figure)


@router.get("/figures/meta", response_model=FiguresMetaResponse)
def get_figures_meta(db: Session = Depends(get_db)):
    """Return distinct filter options (eras, origins, tags)."""
    total = db.query(Figure).count()

    if total == 0:
        eras = sorted(set(f.era for f in FALLBACK_FIGURES if f.era))
        origins = sorted(set(f.origin for f in FALLBACK_FIGURES if f.origin))
        all_tags: set[str] = set()
        for f in FALLBACK_FIGURES:
            if f.tags:
                all_tags.update(t.strip() for t in f.tags.split(",") if t.strip())
        return FiguresMetaResponse(eras=eras, origins=origins, tags=sorted(all_tags))

    eras = sorted(
        r[0] for r in db.query(distinct(Figure.era)).all() if r[0]
    )
    origins = sorted(
        r[0] for r in db.query(distinct(Figure.origin)).all() if r[0]
    )
    all_tags = set()
    for (tags_str,) in db.query(Figure.tags).filter(Figure.tags.isnot(None)).all():
        if tags_str:
            all_tags.update(t.strip() for t in tags_str.split(",") if t.strip())

    return FiguresMetaResponse(eras=eras, origins=origins, tags=sorted(all_tags))


@router.get("/figures/{slug}", response_model=FigureItem)
def get_figure(slug: str, db: Session = Depends(get_db)):
    """Get a single historical figure by slug."""
    figure = db.query(Figure).filter(Figure.slug == slug).first()
    if figure:
        return FigureItem.model_validate(figure)
    for f in FALLBACK_FIGURES:
        if f.slug == slug:
            return f
    raise HTTPException(status_code=404, detail="Figure not found")
