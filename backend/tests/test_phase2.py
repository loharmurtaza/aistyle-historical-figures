"""
Phase 2 tests — Prompt enhancement with GPT-4o-mini
Run with:
    pytest tests/test_phase2.py -v          # unit tests (mocked)
    pytest tests/test_phase2.py -v -m live  # includes real GPT-4o-mini calls
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

MOCK_PROMPT = (
    "Napoleon Bonaparte, clad in his iconic grey overcoat and bicorne hat, "
    "stands resolute on a fog-drenched battlefield at dawn, rendered in the "
    "dramatic chiaroscuro of a Baroque oil painting. Candlelit warmth glows "
    "across his determined face against a turbulent, smoky sky."
)


# ── Helper ───────────────────────────────────────────────────────

def post_enhance(
    payload: dict, mock_return: str = MOCK_PROMPT, mock_error=None
):
    """POST /api/enhance-prompt with the enhance_prompt service mocked."""
    with patch(
        "routers.enhance_prompt.enhance_prompt",
        new_callable=AsyncMock,
    ) as mock_fn:
        if mock_error:
            mock_fn.side_effect = mock_error
        else:
            mock_fn.return_value = mock_return
        return client.post("/api/enhance-prompt", json=payload)


# ── Endpoint / schema tests ──────────────────────────────────────

def test_enhance_returns_200():
    """POST /api/enhance-prompt must return HTTP 200."""
    response = post_enhance(
        {"figure": "Napoleon Bonaparte", "style": "baroque"}
    )
    assert response.status_code == 200


def test_enhance_response_schema():
    """Response must contain enhanced_prompt, figure, and style fields."""
    data = post_enhance({"figure": "Cleopatra", "style": "anime"}).json()
    assert "enhanced_prompt" in data
    assert "figure" in data
    assert "style" in data
    assert data["figure"] == "Cleopatra"
    assert data["style"] == "anime"


def test_enhance_returns_mock_prompt():
    """enhanced_prompt in response must match what the service returns."""
    data = post_enhance({"figure": "Einstein", "style": "watercolor"}).json()
    assert data["enhanced_prompt"] == MOCK_PROMPT


def test_enhance_accepts_optional_user_prompt():
    """Request with an extra user_prompt field must still return 200."""
    response = post_enhance({
        "figure": "Julius Caesar",
        "style": "renaissance",
        "user_prompt": "Show him crossing the Rubicon",
    })
    assert response.status_code == 200


def test_enhance_returns_500_on_service_error():
    """A service exception must surface as HTTP 500."""
    response = post_enhance(
        {"figure": "Einstein", "style": "sketch"},
        mock_error=Exception("LLM timeout"),
    )
    assert response.status_code == 500
    assert "LLM timeout" in response.json()["detail"]


# ── Validation tests ─────────────────────────────────────────────

def test_enhance_rejects_missing_figure():
    """Request missing 'figure' must return HTTP 422."""
    response = client.post("/api/enhance-prompt", json={"style": "anime"})
    assert response.status_code == 422


def test_enhance_rejects_missing_style():
    """Request missing 'style' must return HTTP 422."""
    response = client.post("/api/enhance-prompt", json={"figure": "Napoleon"})
    assert response.status_code == 422


def test_enhance_rejects_empty_figure():
    """figure shorter than min_length=2 must return HTTP 422."""
    response = client.post(
        "/api/enhance-prompt", json={"figure": "N", "style": "baroque"}
    )
    assert response.status_code == 422


# ── Chain / service unit tests ───────────────────────────────────

def test_enhancement_chain_called_with_correct_inputs():
    """
    The service must be invoked with the exact figure and
    style from the request.
    """
    with patch(
        "routers.enhance_prompt.enhance_prompt",
        new_callable=AsyncMock,
    ) as mock_fn:
        mock_fn.return_value = MOCK_PROMPT
        client.post("/api/enhance-prompt", json={
            "figure": "Marie Curie",
            "style": "Art Deco",
        })
    mock_fn.assert_called_once_with(
        figure="Marie Curie",
        style="Art Deco",
        user_prompt="",
    )


# ── Live quality tests (real GPT-4o-mini call) ───────────────────

@pytest.mark.live
def test_live_enhance_returns_nonempty_string():
    """Live: enhanced_prompt must be a non-empty string."""
    response = client.post("/api/enhance-prompt", json={
        "figure": "Napoleon Bonaparte",
        "style": "baroque oil painting",
    })
    assert response.status_code == 200
    prompt = response.json()["enhanced_prompt"]
    assert isinstance(prompt, str)
    assert len(prompt) > 0


@pytest.mark.live
def test_live_enhance_prompt_min_length():
    """
    Live: enhanced_prompt must be at least 80
    characters (rich detail expected).
    """
    response = client.post("/api/enhance-prompt", json={
        "figure": "Cleopatra VII",
        "style": "art nouveau",
    })
    prompt = response.json()["enhanced_prompt"]
    assert len(prompt) >= 80, f"Prompt too short ({len(prompt)} chars): {prompt}"


@pytest.mark.live
def test_live_enhance_mentions_figure():
    """Live: enhanced_prompt must mention the historical figure by name."""
    figure = "Leonardo da Vinci"
    response = client.post("/api/enhance-prompt", json={
        "figure": figure,
        "style": "renaissance",
    })
    prompt = response.json()["enhanced_prompt"].lower()
    # Accept either full name or last name
    assert "da vinci" in prompt or "leonardo" in prompt, (
        f"Figure name not found in prompt: {prompt}"
    )


@pytest.mark.live
def test_live_enhance_weaves_in_style():
    """
    Live: enhanced_prompt must reference the requested art style naturally.
    """
    style = "watercolor"
    response = client.post("/api/enhance-prompt", json={
        "figure": "Marie Curie",
        "style": style,
    })
    prompt = response.json()["enhanced_prompt"].lower()
    assert style in prompt, f"Style '{style}' not found in prompt: {prompt}"
