"""
Seed the figures table from a JSON file.

Run from the backend directory:
    python scripts/seed_figures.py
    python scripts/seed_figures.py --file path/to/custom.json

The JSON file must be an array of objects matching this shape:
{
  "name": "Full Name",
  "slug": "full-name",
  "description": "One-sentence bio.",
  "born_year": 1234,       // int, negative for BCE, null if unknown
  "died_year": 1234,       // int, negative for BCE, null if unknown
  "era": "Renaissance",
  "origin": "Italy",
  "tags": "artist, scientist",
  "featured": false
}
"""
import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import SessionLocal, Base, engine  # noqa: E402
import models  # noqa: F401, E402
from models.figure import Figure  # noqa: E402

DEFAULT_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "figures_data.json"
)


def seed(filepath: str):
    if not os.path.exists(filepath):
        print(f"Error: file not found — {filepath}")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("Error: JSON root must be an array.")
        sys.exit(1)

    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        existing_slugs = {row.slug for row in db.query(Figure.slug).all()}
        existing_names = {row.name for row in db.query(Figure.name).all()}

        to_add = []
        skipped = 0
        for entry in data:
            if (
                entry.get("slug") in existing_slugs
                or entry.get("name") in existing_names
            ):
                skipped += 1
                continue
            to_add.append(Figure(
                name=entry["name"],
                slug=entry["slug"],
                description=entry.get("description"),
                born_year=entry.get("born_year"),
                died_year=entry.get("died_year"),
                era=entry.get("era"),
                origin=entry.get("origin"),
                tags=entry.get("tags"),
                featured=bool(entry.get("featured", False)),
            ))

        if not to_add:
            print(f"Nothing to add — {skipped} record(s) already exist.")
            return

        db.add_all(to_add)
        db.commit()
        print(
            f"Seeded {len(to_add)} figure(s). Skipped {skipped} duplicate(s)."
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--file", default=DEFAULT_FILE, help="Path to figures JSON file"
    )
    args = parser.parse_args()
    seed(args.file)
