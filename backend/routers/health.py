from fastapi import APIRouter
from langchain_core.messages import HumanMessage
from llm import llm
from models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(request: None = None):
    """
    Returns service status and confirms OpenAI connectivity via a
    minimal LangChain invocation (max_tokens=1 to keep cost negligible).
    """
    try:
        await llm.ainvoke(
            [HumanMessage(content="ping")],
            config={"max_tokens": 1},
        )
        openai_connected = True
    except Exception:
        openai_connected = False

    return HealthResponse(
        status="ok",
        service="chronocanvasai-backend",
        version="0.1.0",
        openai_connected=openai_connected,
    )
