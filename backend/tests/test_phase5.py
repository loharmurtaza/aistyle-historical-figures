"""
Phase 5 tests — Rate limiting, InMemoryCache, GET /styles, LangGraph retry
Run with:
    pytest tests/test_phase5.py -v          # unit tests (no API side effects)
    pytest tests/test_phase5.py -v -m live  # real API calls
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app

# ── Test DB setup ─────────────────────────────────────────────────

TEST_DB_URL = "sqlite:///./test_phase5.db"
test_engine = create_engine(
    TEST_DB_URL, connect_args={"check_same_thread": False}
)
TestSession = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine
)


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
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(autouse=True)
def reset_limiter():
    """Clear the slowapi MemoryStorage window between tests."""
    from rate_limit import limiter
    try:
        limiter._storage.reset()
    except Exception:
        pass
    yield
    try:
        limiter._storage.reset()
    except Exception:
        pass


MOCK_RESULT = {
    "enhanced_prompt": "A vivid baroque portrait of Napoleon...",
    "image_url": (
        "https://oaidalleapiprodscus.blob.core.windows.net/napoleon.png"
    ),
}

# ── GET /styles ───────────────────────────────────────────────────


def test_styles_returns_200():
    response = client.get("/api/styles")
    assert response.status_code == 200


def test_styles_returns_list():
    data = client.get("/api/styles").json()
    assert "styles" in data
    assert isinstance(data["styles"], list)
    assert len(data["styles"]) > 0


def test_styles_contains_expected_values():
    styles = client.get("/api/styles").json()["styles"]
    for expected in ["baroque", "renaissance", "watercolor", "anime"]:
        assert expected in styles


# ── InMemoryCache ────────────────────────────────────────────────


def test_llm_cache_is_configured():
    """InMemoryCache must be set on the global LLM cache."""
    from langchain_core.globals import get_llm_cache
    from langchain_community.cache import InMemoryCache

    assert isinstance(get_llm_cache(), InMemoryCache)


def test_llm_cache_stores_and_retrieves():
    """
    Values written to InMemoryCache must be retrievable by the same key,
    confirming identical prompts will skip the LLM call.
    """
    from langchain_core.globals import get_llm_cache
    from langchain_core.outputs import ChatGeneration
    from langchain_core.messages import AIMessage

    cache = get_llm_cache()
    cache.clear()

    fake_gen = [ChatGeneration(message=AIMessage(content="cached output"))]
    cache.update("my-prompt", "my-llm-key", fake_gen)

    retrieved = cache.lookup("my-prompt", "my-llm-key")
    assert retrieved is not None
    assert retrieved[0].message.content == "cached output"

    # A second lookup returns the same entry (no duplication)
    assert cache.lookup("my-prompt", "my-llm-key") == retrieved


def test_llm_cache_miss_returns_none():
    """Looking up a key that was never stored must return None."""
    from langchain_core.globals import get_llm_cache

    cache = get_llm_cache()
    cache.clear()

    assert cache.lookup("nonexistent-prompt", "nonexistent-key") is None


# ── Rate limiting ────────────────────────────────────────────────


def test_rate_limit_allows_requests_under_threshold():
    """First request must not be rate-limited."""
    with patch(
        "routers.generate.generate_portrait", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.return_value = MOCK_RESULT
        response = client.post(
            "/api/generate",
            json={"figure": "Napoleon Bonaparte", "style": "baroque"},
        )
    assert response.status_code == 200


def test_rate_limit_blocks_after_threshold():
    """After 10 requests/minute the 11th must return 429."""
    with patch(
        "routers.generate.generate_portrait", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.return_value = MOCK_RESULT
        responses = [
            client.post(
                "/api/generate",
                json={"figure": "Napoleon Bonaparte", "style": "baroque"},
            )
            for _ in range(11)
        ]
    status_codes = [r.status_code for r in responses]
    assert 429 in status_codes


# ── LangGraph content policy retry ──────────────────────────────


def test_content_policy_error_returns_400_after_exhausted_retries():
    """
    If DALL·E refuses the prompt even after softening, the endpoint must
    return 400 (not 500).
    """
    from services.image_generator import ContentPolicyError

    with patch(
        "routers.generate.generate_portrait", new_callable=AsyncMock
    ) as mock_gen:
        mock_gen.side_effect = ContentPolicyError(
            "DALL·E refused after retry"
        )
        response = client.post(
            "/api/generate",
            json={"figure": "Napoleon Bonaparte", "style": "baroque"},
        )

    assert response.status_code == 400
    assert "content policy" in response.json()["detail"].lower()


def test_langgraph_soften_node_called_on_content_policy():
    """
    The soften node must re-enhance with an art-only instruction when the
    generate node hits a content policy error on the first call.
    enhance_prompt is called twice: once normally, once in the soften node.
    """
    from openai import BadRequestError as OAIBadRequest
    from httpx import Response as HttpxResponse
    from services.image_generator import generate_portrait

    attempt = {"count": 0}

    async def flaky_dalle(prompt: str) -> str:
        import httpx
        attempt["count"] += 1
        if attempt["count"] == 1:
            req = httpx.Request("POST", "https://api.openai.com")
            raw = HttpxResponse(400, request=req, content=b'{"error": {}}')
            raise OAIBadRequest(
                message="content_policy_violation",
                response=raw,
                body={"error": {}},
            )
        return "https://oaidalleapiprodscus.blob.core.windows.net/ok.png"

    # _generate_node calls _dalle_chain.ainvoke(...), so we need a MagicMock
    # with ainvoke set as an AsyncMock — not a bare AsyncMock (which would
    # put side_effect on __call__, not on the .ainvoke attribute).
    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(side_effect=flaky_dalle)
    with (
        patch("services.image_generator._dalle_chain", mock_chain),
        patch(
            "services.image_generator.enhance_prompt",
            new_callable=AsyncMock,
            return_value="A vivid prompt",
        ) as mock_enhance,
    ):
        result = asyncio.get_event_loop().run_until_complete(
            generate_portrait("Napoleon Bonaparte", "baroque")
        )

    # enhance was called twice: once in enhance_node, once in soften_node
    assert mock_enhance.call_count == 2
    assert result["image_url"].startswith("https://")


def test_langgraph_raises_content_policy_error_after_two_failures():
    """
    If DALL·E refuses both the original and the softened prompt,
    generate_portrait must raise ContentPolicyError.
    """
    from openai import BadRequestError as OAIBadRequest
    from httpx import Response as HttpxResponse
    from services.image_generator import ContentPolicyError, generate_portrait

    async def always_bad(prompt: str) -> str:
        import httpx
        req = httpx.Request("POST", "https://api.openai.com")
        raw = HttpxResponse(400, request=req, content=b'{"error": {}}')
        raise OAIBadRequest(
            message="content_policy_violation",
            response=raw,
            body={"error": {}},
        )

    mock_chain = MagicMock()
    mock_chain.ainvoke = AsyncMock(side_effect=always_bad)
    with (
        patch("services.image_generator._dalle_chain", mock_chain),
        patch(
            "services.image_generator.enhance_prompt",
            new_callable=AsyncMock,
            return_value="A vivid prompt",
        ),
    ):
        with pytest.raises(ContentPolicyError):
            asyncio.get_event_loop().run_until_complete(
                generate_portrait("Napoleon Bonaparte", "baroque")
            )


# ── LangSmith config ──────────────────────────────────────────────


def test_langsmith_settings_have_defaults():
    """LangSmith fields should not raise on access even without env vars."""
    from config import settings

    assert isinstance(settings.langsmith_tracing, bool)
    assert isinstance(settings.langsmith_project, str)


# ── Live tests ────────────────────────────────────────────────────


@pytest.mark.live
def test_live_styles_endpoint():
    """Live: /styles must return a non-empty list."""
    data = client.get("/api/styles").json()
    assert len(data["styles"]) > 0


@pytest.mark.live
def test_live_generate_with_langgraph():
    """Live: full LangGraph pipeline must return a valid DALL·E URL."""
    response = client.post(
        "/api/generate",
        json={"figure": "Cleopatra", "style": "art deco"},
    )
    assert response.status_code == 200
    assert response.json()["image_url"].startswith("https://")
