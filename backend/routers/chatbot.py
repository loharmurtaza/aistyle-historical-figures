"""
POST /api/chat — streaming chatbot endpoint.

Accepts a user message and an optional session_id.
Returns a Server-Sent Events stream where each event carries one LLM token.
The stream is terminated by a final `data: [DONE]` event.

SSE event format
----------------
  data: {"token": "<text>"}\n\n   — one chunk of the LLM response
  data: [DONE]\n\n                — stream finished

The token is JSON-encoded so that newlines and special characters inside
the text never break the SSE framing.
"""
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from models.schemas import ChatRequest, ChatResetResponse
from services.chatbot import chat_stream, reset_session

router = APIRouter(tags=["chatbot"])


@router.post("/chat/{session_id}/reset", response_model=ChatResetResponse)
async def reset_chat_session(session_id: str) -> ChatResetResponse:
    """
    Close the given session and return a fresh session_id.
    Existing messages are retained in the DB for analytics.
    """
    new_id = reset_session(session_id)
    return ChatResetResponse(new_session_id=new_id)


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    session_id = request.session_id or "default"

    async def event_stream():
        async for token in chat_stream(request.message, session_id):
            payload = json.dumps({"token": token}, ensure_ascii=False)
            yield f"data: {payload}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            # Prevent proxies / nginx from buffering the stream.
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
