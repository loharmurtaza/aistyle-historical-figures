"""
Phase 3 tests — Image generation with DALL·E 3
Run with:
    pytest tests/test_phase3.py -v          # unit tests (mocked, no API calls)
    pytest tests/test_phase3.py -v -m live  # includes real DALL·E 3 call (~$0.04)
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from openai import BadRequestError

from main import app

client = TestClient(app)

MOCK_IMAGE_URL = "https://oaidalleapiprodscus.blob.core.windows.net/test/mock-portrait.png"
MOCK_ENHANCED_PROMPT = (
    "Marie Curie, dressed in her signature dark laboratory coat, bends over "
    "glowing radium samples in her Paris laboratory, rendered in the sinuous "
    "lines and botanical ornamentation of Art Nouveau. Soft bioluminescent "
    "greens and golds illuminate her focused expression against a dark background."
)
MOCK_RESULT = {"enhanced_prompt": MOCK_ENHANCED_PROMPT, "image_url": MOCK_IMAGE_URL}


# ── Helper ───────────────────────────────────────────────────────

def post_generate(payload: dict, mock_result=None, mock_error=None):
    """POST /api/generate with generate_portrait service mocked."""
    with patch(
        "routers.generate.generate_portrait",
        new_callable=AsyncMock,
    ) as mock_fn:
        if mock_error:
            mock_fn.side_effect = mock_error
        else:
            mock_fn.return_value = mock_result or MOCK_RESULT
        return client.post("/api/generate", json=payload)


# ── Endpoint / schema tests ──────────────────────────────────────

def test_generate_returns_200():
    """POST /api/generate must return HTTP 200."""
    response = post_generate(
        {"figure": "Napoleon Bonaparte", "style": "baroque"}
    )
    assert response.status_code == 200


def test_generate_response_schema():
    """
    Response must contain image_url, enhanced_prompt, revised_prompt,
    figure, style.
    """
    data = post_generate(
        {"figure": "Cleopatra", "style": "art nouveau"}
    ).json()
    assert "image_url" in data
    assert "enhanced_prompt" in data
    assert "revised_prompt" in data
    assert "figure" in data
    assert "style" in data


def test_generate_response_values():
    """Response values must match mock result and request inputs."""
    data = post_generate(
        {"figure": "Marie Curie", "style": "art nouveau"}
    ).json()
    assert data["image_url"] == MOCK_IMAGE_URL
    assert data["enhanced_prompt"] == MOCK_ENHANCED_PROMPT
    assert data["figure"] == "Marie Curie"
    assert data["style"] == "art nouveau"


def test_generate_accepts_optional_user_prompt():
    """Request with user_prompt must return 200."""
    response = post_generate({
        "figure": "Julius Caesar",
        "style": "renaissance",
        "user_prompt": "crossing the Rubicon at night",
    })
    assert response.status_code == 200


def test_generate_returns_400_on_content_policy():
    """A BadRequestError must surface as HTTP 400."""
    bad_request = BadRequestError(
        message="Your request was rejected as a result of our safety system.",
        response=MagicMock(status_code=400),
        body={"error": {"code": "content_policy_violation"}},
    )
    response = post_generate(
        {"figure": "Napoleon", "style": "baroque"},
        mock_error=bad_request,
    )
    assert response.status_code == 400
    assert "content policy" in response.json()["detail"].lower()


def test_generate_returns_500_on_generic_error():
    """A generic exception must surface as HTTP 500."""
    response = post_generate(
        {"figure": "Einstein", "style": "sketch"},
        mock_error=Exception("connection timeout"),
    )
    assert response.status_code == 500
    assert "connection timeout" in response.json()["detail"]


# ── Validation tests ─────────────────────────────────────────────

def test_generate_rejects_missing_figure():
    """Request missing 'figure' must return HTTP 422."""
    assert client.post(
        "/api/generate", json={"style": "baroque"}
    ).status_code == 422


def test_generate_rejects_missing_style():
    """Request missing 'style' must return HTTP 422."""
    assert client.post(
        "/api/generate", json={"figure": "Napoleon"}
    ).status_code == 422


def test_generate_rejects_short_figure():
    """figure shorter than min_length=2 must return HTTP 422."""
    response = client.post(
        "/api/generate", json={"figure": "N", "style": "baroque"}
    )
    assert response.status_code == 422


# ── Service call tests ───────────────────────────────────────────

def test_generate_portrait_called_with_correct_inputs():
    """generate_portrait must be called with figure, style, and user_prompt."""
    with patch(
        "routers.generate.generate_portrait",
        new_callable=AsyncMock,
    ) as mock_fn:
        mock_fn.return_value = MOCK_RESULT
        client.post("/api/generate", json={
            "figure": "Marie Curie",
            "style": "Art Deco",
            "user_prompt": "in her lab",
        })
    mock_fn.assert_called_once_with(
        figure="Marie Curie",
        style="Art Deco",
        user_prompt="in her lab",
    )


def test_generate_portrait_called_with_empty_user_prompt_by_default():
    """
    When user_prompt is omitted, generate_portrait must receive empty string.
    """
    with patch(
        "routers.generate.generate_portrait",
        new_callable=AsyncMock,
    ) as mock_fn:
        mock_fn.return_value = MOCK_RESULT
        client.post(
            "/api/generate", json={"figure": "Einstein", "style": "ghibli"}
        )
    mock_fn.assert_called_once_with(
        figure="Einstein",
        style="ghibli",
        user_prompt="",
    )


# ── Live tests (real DALL·E 3 call — costs ~$0.04 per run) ──────

@pytest.mark.live
def test_live_generate_returns_valid_image_url():
    """Live: image_url must be a non-empty HTTPS URL."""
    response = client.post("/api/generate", json={
        "figure": "Napoleon Bonaparte",
        "style": "baroque oil painting",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["image_url"].startswith("https://")


@pytest.mark.live
def test_live_generate_returns_enhanced_prompt():
    """Live: enhanced_prompt must be non-empty and at least 80 chars."""
    response = client.post("/api/generate", json={
        "figure": "Cleopatra VII",
        "style": "art nouveau",
    })
    assert response.status_code == 200
    prompt = response.json()["enhanced_prompt"]
    assert isinstance(prompt, str) and len(prompt) >= 80


@pytest.mark.live
def test_live_generate_full_response_schema():
    """Live: all five response fields must be present and non-empty."""
    response = client.post("/api/generate", json={
        "figure": "Marie Curie",
        "style": "watercolor",
    })
    data = response.json()
    for field in (
        "image_url", "enhanced_prompt", "revised_prompt", "figure", "style"
    ):
        assert data.get(field), f"Field '{field}' missing or empty"
