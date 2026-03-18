"""
Seed the styles table with the default art styles.

Run from the backend directory:
    python scripts/seed_styles.py
"""
import sys
import os

# Allow imports from the backend root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, Base, engine  # noqa: E402
import models  # noqa: F401, E402 — registers all ORM models
from models.style import Style  # noqa: E402


DEFAULT_STYLES = [
    "oil panting", "watercolor", "acrylic painting",
    "gouache", "fresco", "tempera", "pastel art",
    "ink wash (sumi-e)", "charcoal drawing",
    "pencil sketching", "abstract art", "cubism",
    "abstract expression", "surrealism", "minimalism",
    "conceptual art", "expressionism", "fauvism",
    "dadaism", "constructivism", "digital painting",
    "vector art", "pixel art", "3d rendering", "voxel art",
    "low poly art", "glitch art", "generative art",
    "ai-generated art", "anime", "manga", "pop art",
    "cartoon style", "comic book art", "street art",
    "graffiti", "sticker art", "kuwaii art", "chibi art",
    "baroque", "rococo", "art nouveau", "art deco",
    "ukiyo-e", "islamic art", "byzantine art", "gothic art",
    "renaissance", "neoclassicism", "cyberpunk",
    "steampunk", "vaporwave", "psychedelic art",
    "dark fantasy", "photorealism", "hyperrealism",
    "college art", "mixed media", "installation art"
]


def seed():
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        existing = {row.name for row in db.query(Style.name).all()}
        to_add = [Style(name=s) for s in DEFAULT_STYLES if s not in existing]

        if not to_add:
            print("Styles table already up to date — nothing to seed.")
            return

        db.add_all(to_add)
        db.commit()
        print(f"Seeded {len(to_add)} style(s): {[s.name for s in to_add]}")


if __name__ == "__main__":
    seed()
