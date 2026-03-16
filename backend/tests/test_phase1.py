"""
Phase 1 tests — Project setup + health check
Run with:
    pytest tests/test_phase1.py -v          # unit tests (mocked, no API calls)
    pytest tests/test_phase1.py -v -m live  # includes real OpenAI call
"""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from langchain_openai import ChatOpenAI

from main import app

client = TestClient(app)


# ── Helpers ─────────────────────────────────────────────────────

def get_health(side_effect=None):
    """
    Call GET /health with ChatOpenAI.ainvoke mocked at the class level.
    Patching on the class affects all instances including the shared llm singleton.
    """
    with patch.object(ChatOpenAI, "ainvoke", new_callable=AsyncMock) as mock_ainvoke:
        if side_effect:
            mock_ainvoke.side_effect = side_effect
        else:
            mock_ainvoke.return_value = None
        return client.get("/health")


# ── Structural tests (no real API call) ─────────────────────────

def test_health_returns_200():
    """GET /health must return HTTP 200."""
    assert get_health().status_code == 200


def test_health_response_schema():
    """Response must include all required fields with correct types."""
    data = get_health().json()
    assert data["status"] == "ok"
    assert data["service"] == "chronocanvasai-backend"
    assert data["version"] == "0.1.0"
    assert isinstance(data["openai_connected"], bool)


def test_health_openai_connected_true_on_success():
    """openai_connected is True when the LLM call succeeds."""
    assert get_health().json()["openai_connected"] is True


def test_health_openai_connected_false_on_failure():
    """openai_connected is False when the LLM raises any exception."""
    data = get_health(side_effect=Exception("network error")).json()
    assert data["openai_connected"] is False


def test_cors_allows_frontend_origin():
    """CORS header must allow the configured frontend origin."""
    with patch.object(ChatOpenAI, "ainvoke", new_callable=AsyncMock):
        response = client.get(
            "/health",
            headers={"Origin": "http://localhost:3000"},
        )
    assert "access-control-allow-origin" in response.headers


def test_docs_endpoint_available():
    """Auto-generated Swagger docs must be reachable at /docs."""
    assert client.get("/docs").status_code == 200


# ── Live connectivity test (requires real API key + network) ────

@pytest.mark.live
def test_health_live_openai_connection():
    """
    Hits the real OpenAI API. Only runs with: pytest -m live
    Requires OPENAI_API_KEY set in backend/.env
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["openai_connected"] is True
