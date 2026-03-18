"""
RAG-based chatbot service for historical figures.

Per-request flow
----------------
1. Retrieve: embed the user's message and run FAISS similarity search
   to find the top-k most relevant figures (no DB hit — all in RAM).
2. Build prompt: system message containing
     (a) catalog summary  — answers global questions ("what's in the app?")
     (b) RAG context      — top-k figure details for specific questions
   followed by the session's message history and the new user message.
3. Stream: pipe the assembled messages through the LLM and yield each
   token as it arrives.
4. Persist: write both the user message and the assistant message (with
   metrics) to the chat_messages table; update chat_sessions.last_active.

Timing and cost are logged at INFO level for every query:

  chatbot | session=<id> | retrieval=<ms>ms | first_token=<ms>ms
          | total=<ms>ms | docs=<k>
          | prompt_tokens=<n> | completion_tokens=<n> | total_tokens=<n>
"""
import time
from collections.abc import AsyncIterator
from datetime import datetime

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from database import SessionLocal
from logger import get_logger
from models.chat import ChatMessage, ChatSession
from services.figures_index import figures_index
from config import settings

logger = get_logger(__name__)

# ── Chat-specific LLM ─────────────────────────────────────────────────────
# Separate from the shared llm.py instance so we can enable stream_usage
# without affecting portrait-generation calls.

_chat_llm = ChatOpenAI(
    model=settings.openai_prompt_model,
    api_key=settings.openai_api_key,
    temperature=settings.openai_prompt_temperature,
    max_retries=settings.openai_prompt_max_retries,
    stream_usage=True,  # final chunk carries usage_metadata
)

# ── System prompt template ────────────────────────────────────────────────
# {catalog_summary} — refreshed from DB on TTL; covers global questions.
# {rag_context}     — top-k figures retrieved per query; covers specifics.

_SYSTEM_TEMPLATE = """\
You are an assistant for the ChronoCanvas platform. Your ONLY job is to
help users explore the figures, eras, origins, and tags that exist in
this catalog.

CATALOG OVERVIEW:
{catalog_summary}

RELEVANT FIGURES FOR THIS QUERY:
{rag_context}

STRICT RULES — follow every one of these without exception:
1. Answer EXCLUSIVELY from the two context blocks above. Do not add
   knowledge from your training data, even if you are certain it is
   correct.
2. If the user asks for information not present in the context blocks,
   respond with: "I don't have that detail in the catalog. For more
   information you can search on Wikipedia or Google."
3. Never explain historical background, cultural context, or biographical
   details that are not explicitly stated in the context blocks.
4. Keep answers short and direct. Do not pad with filler.
5. You may use light Markdown (bold, numbered lists) to improve
   readability.\
"""


# ── DB helpers ────────────────────────────────────────────────────────────

def _ensure_session(session_id: str, db) -> None:
    """Create a ChatSession row if one doesn't exist yet."""
    exists = (
        db.query(ChatSession)
        .filter(ChatSession.session_id == session_id)
        .first()
    )
    if not exists:
        db.add(ChatSession(session_id=session_id))
        db.commit()


def _load_history(session_id: str, db) -> list:
    """Return ordered LangChain messages for the session from the DB."""
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
        .all()
    )
    messages = []
    for row in rows:
        if row.role == "user":
            messages.append(HumanMessage(content=row.content))
        else:
            messages.append(AIMessage(content=row.content))
    return messages


def _persist_exchange(
    session_id: str,
    user_content: str,
    ai_content: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    retrieval_ms: float,
    first_token_ms: float,
    total_ms: float,
    docs_retrieved: int,
    db,
) -> None:
    """Write user + assistant rows and bump last_active on the session."""
    db.add(ChatMessage(
        session_id=session_id,
        role="user",
        content=user_content,
    ))
    db.add(ChatMessage(
        session_id=session_id,
        role="assistant",
        content=ai_content,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
        retrieval_ms=retrieval_ms,
        first_token_ms=first_token_ms,
        total_ms=total_ms,
        docs_retrieved=docs_retrieved,
    ))
    db.query(ChatSession).filter(
        ChatSession.session_id == session_id
    ).update({"last_active": datetime.utcnow()})
    db.commit()


# ── Public interface ──────────────────────────────────────────────────────

def reset_session(old_session_id: str) -> str:
    """
    Mark the old session as reset and create a fresh one.
    Returns the new session_id. DB records for the old session are retained.
    """
    import uuid
    new_session_id = str(uuid.uuid4())
    db = SessionLocal()
    try:
        db.query(ChatSession).filter(
            ChatSession.session_id == old_session_id
        ).update({"last_active": datetime.utcnow()})
        db.add(ChatSession(session_id=new_session_id))
        db.commit()
    finally:
        db.close()
    return new_session_id


async def chat_stream(
    message: str,
    session_id: str,
) -> AsyncIterator[str]:
    """
    Yield LLM response tokens one by one.
    Loads history from DB, streams the response, then persists the exchange.
    """
    t_start = time.perf_counter()

    # ── 1. Load history + ensure session row exists ───────────────────────
    db = SessionLocal()
    try:
        _ensure_session(session_id, db)
        history_messages = _load_history(session_id, db)
    finally:
        db.close()

    # ── 2. Retrieval (FAISS search in RAM, no DB hit) ─────────────────────
    docs, retrieval_ms = await figures_index.search(
        message, k=settings.chatbot_retrieval_k
    )
    catalog_summary = figures_index.get_catalog_summary()

    rag_context = (
        "\n\n---\n\n".join(doc.page_content for doc in docs)
        if docs
        else "No specific figures matched this query."
    )

    # ── 3. Build message list ─────────────────────────────────────────────
    system_content = _SYSTEM_TEMPLATE.format(
        catalog_summary=catalog_summary,
        rag_context=rag_context,
    )
    messages = [
        SystemMessage(content=system_content),
        *history_messages,
        HumanMessage(content=message),
    ]

    # ── 4. Stream LLM response ────────────────────────────────────────────
    t_llm_start = time.perf_counter()
    t_first_token_ms: float | None = None
    response_parts: list[str] = []
    last_chunk = None

    async for chunk in _chat_llm.astream(messages):
        last_chunk = chunk
        token: str = chunk.content  # type: ignore[assignment]
        if not token:
            # Empty content = usage-only chunk from OpenAI; don't yield.
            continue
        if t_first_token_ms is None:
            t_first_token_ms = (time.perf_counter() - t_llm_start) * 1000.0
        response_parts.append(token)
        yield token

    # ── 5. Extract token usage from the final chunk ───────────────────────
    usage = getattr(last_chunk, "usage_metadata", None) or {}
    prompt_tokens = usage.get("input_tokens", 0)
    completion_tokens = usage.get("output_tokens", 0)
    total_tokens = usage.get("total_tokens", 0)

    total_ms = (time.perf_counter() - t_start) * 1000.0
    first_token_ms_val = t_first_token_ms or 0.0

    # ── 6. Persist exchange to DB ─────────────────────────────────────────
    db = SessionLocal()
    try:
        _persist_exchange(
            session_id=session_id,
            user_content=message,
            ai_content="".join(response_parts),
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            retrieval_ms=retrieval_ms,
            first_token_ms=first_token_ms_val,
            total_ms=total_ms,
            docs_retrieved=len(docs),
            db=db,
        )
    finally:
        db.close()

    # ── 7. Log round-trip breakdown ───────────────────────────────────────
    logger.info(
        "chatbot | session=%s"
        " | retrieval=%.0f ms | first_token=%.0f ms | total=%.0f ms"
        " | docs_retrieved=%d"
        " | prompt_tokens=%d | completion_tokens=%d | total_tokens=%d",
        session_id,
        retrieval_ms,
        first_token_ms_val,
        total_ms,
        len(docs),
        prompt_tokens,
        completion_tokens,
        total_tokens,
    )
