"""
Phase 4 tests — Gallery persistence + RunnableWithMessageHistory
Run with:
    pytest tests/test_phase4.py -v          # unit tests (no API/DB side effects)
    pytest tests/test_phase4.py -v -m live  # real DB + real API calls
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app
from models.portrait import Portrait

# ── Test DB setup ────────────────────────────────────────────────
# Use an isolated in-file SQLite DB per test run (cleaned up in teardown)

TEST_DB_URL = "sqlite:///./test_gallery.db"
test_engine = create_engine(
    TEST_DB_URL, connect_args={"check_same_thread": False}
)
TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def fresh_db():
    """Create all tables before each test; drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


# ── Helpers ──────────────────────────────────────────────────────

def seed_portrait(
    figure="Napoleon Bonaparte",
    style="baroque",
    prompt="Napoleon on battlefield",
    enhanced_prompt="A vivid baroque portrait of Napoleon...",
    image_url="https://example.com/napoleon.png",
):
    """Insert a portrait directly into the test DB."""
    db = TestSession()
    portrait = Portrait(
        figure=figure,
        style=style,
        prompt=prompt,
        enhanced_prompt=enhanced_prompt,
        image_url=image_url,
    )
    db.add(portrait)
    db.commit()
    db.refresh(portrait)
    db.close()
    return portrait


MOCK_GENERATE_RESULT = {
    "enhanced_prompt": "A dramatic baroque portrait of Napoleon...",
    "image_url": "https://oaidalleapiprodscus.blob.core.windows.net/napoleon.png",
}


# ── GET /gallery ─────────────────────────────────────────────────

def test_gallery_empty_returns_200():
    response = client.get("/api/gallery")
    assert response.status_code == 200


def test_gallery_empty_schema():
    data = client.get("/api/gallery").json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert "page_size" in data


def test_gallery_returns_seeded_portrait():
    seed_portrait()
    data = client.get("/api/gallery").json()
    assert data["total"] == 1
    assert data["items"][0]["figure"] == "Napoleon Bonaparte"


def test_gallery_pagination():
    for i in range(5):
        seed_portrait(figure=f"Figure {i}")
    data = client.get("/api/gallery?page=1&page_size=3").json()
    assert len(data["items"]) == 3
    assert data["total"] == 5


def test_gallery_style_filter_matches():
    seed_portrait(style="baroque")
    seed_portrait(style="anime")
    data = client.get("/api/gallery?style=baroque").json()
    assert data["total"] == 1
    assert data["items"][0]["style"] == "baroque"


def test_gallery_style_filter_no_match():
    seed_portrait(style="baroque")
    data = client.get("/api/gallery?style=watercolor").json()
    assert data["total"] == 0


def test_gallery_ordered_newest_first():
    seed_portrait(figure="First")
    seed_portrait(figure="Second")
    items = client.get("/api/gallery").json()["items"]
    assert items[0]["figure"] == "Second"


# ── GET /gallery/{id} ────────────────────────────────────────────

def test_get_portrait_by_id_returns_correct_item():
    portrait = seed_portrait(figure="Cleopatra")
    response = client.get(f"/api/gallery/{portrait.id}")
    assert response.status_code == 200
    assert response.json()["figure"] == "Cleopatra"


def test_get_portrait_by_id_not_found():
    response = client.get("/api/gallery/9999")
    assert response.status_code == 404


# ── DELETE /gallery/{id} ─────────────────────────────────────────

def test_delete_portrait_success():
    portrait = seed_portrait()
    response = client.delete(f"/api/gallery/{portrait.id}")
    assert response.status_code == 200
    assert response.json()["id"] == portrait.id


def test_delete_removes_from_gallery():
    portrait = seed_portrait()
    client.delete(f"/api/gallery/{portrait.id}")
    assert client.get(f"/api/gallery/{portrait.id}").status_code == 404


def test_delete_portrait_not_found():
    assert client.delete("/api/gallery/9999").status_code == 404


# ── Auto-save after generation ───────────────────────────────────

def test_generate_autosaves_to_gallery():
    """A successful POST /generate must save the portrait to the gallery."""
    with patch(
        "routers.generate.generate_portrait", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.return_value = MOCK_GENERATE_RESULT
        client.post("/api/generate", json={
            "figure": "Napoleon Bonaparte",
            "style": "baroque",
        })

    data = client.get("/api/gallery").json()
    assert data["total"] == 1
    saved = data["items"][0]
    assert saved["figure"] == "Napoleon Bonaparte"
    assert saved["style"] == "baroque"
    assert saved["image_url"] == MOCK_GENERATE_RESULT["image_url"]


def test_failed_generate_does_not_save_to_gallery():
    """A failed generation must NOT add anything to the gallery."""
    with patch(
        "routers.generate.generate_portrait", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.side_effect = Exception("DALL·E timeout")
        client.post("/api/generate", json={
            "figure": "Napoleon Bonaparte",
            "style": "baroque",
        })

    assert client.get("/api/gallery").json()["total"] == 0


# ── RunnableWithMessageHistory (session) ─────────────────────────

def test_generate_accepts_session_id():
    """Request with session_id must be accepted (200, not 422)."""
    with patch(
        "routers.generate.generate_portrait", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.return_value = MOCK_GENERATE_RESULT
        response = client.post("/api/generate", json={
            "figure": "Napoleon Bonaparte",
            "style": "baroque",
            "session_id": "test-session-abc",
        })
    assert response.status_code == 200


def test_generate_passes_session_id_to_service():
    """session_id must be forwarded to generate_portrait."""
    with patch(
        "routers.generate.generate_portrait", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.return_value = MOCK_GENERATE_RESULT
        client.post("/api/generate", json={
            "figure": "Marie Curie",
            "style": "art deco",
            "session_id": "session-xyz",
        })
    mock_gen.assert_called_once_with(
        figure="Marie Curie",
        style="art deco",
        user_prompt="",
        session_id="session-xyz",
    )


# ── Live tests ───────────────────────────────────────────────────

@pytest.mark.live
def test_live_generate_saves_to_gallery():
    """Live: after a real generation, gallery total must be 1."""
    client.post("/api/generate", json={
        "figure": "Julius Caesar",
        "style": "renaissance",
    })
    assert client.get("/api/gallery").json()["total"] == 1


@pytest.mark.live
def test_live_session_history_second_call():
    """
    Live: two calls with the same session_id — the second should produce
    a valid prompt (history chain is used for session calls).
    """
    session = "live-test-session-001"
    for figure in ["Napoleon Bonaparte", "same figure"]:
        response = client.post("/api/generate", json={
            "figure": figure,
            "style": "watercolor",
            "session_id": session,
        })
        assert response.status_code == 200
        assert response.json()["image_url"].startswith("https://")
