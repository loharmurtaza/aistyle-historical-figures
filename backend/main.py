import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlalchemy import text
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import HumanMessage
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import settings
from llm import llm
from logger import get_logger
from database import engine
import models  # noqa: F401  # registers all ORM models
from models.portrait import Portrait  # noqa: F401
from database import Base
from rate_limit import limiter
from routers import (
    health, enhance_prompt, generate,
    gallery, styles, stats, figures, chatbot
)
from services.figures_index import figures_index

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Verify OpenAI connectivity once at startup.
    """
    # LangSmith optional tracing — set env vars before chains are invoked
    if settings.langsmith_tracing and settings.langsmith_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = settings.langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = settings.langsmith_project
        logger.info(
            "LangSmith tracing enabled — project: %s",
            settings.langsmith_project,
        )

    # Create DB tables (portraits) if they don't exist yet
    Base.metadata.create_all(bind=engine)

    # Migrate: add image_data column if it doesn't exist yet
    # (SQLite ALTER TABLE)
    with engine.connect() as conn:
        cols = [
            row[1] for row in conn.execute(
                text("PRAGMA table_info(portraits)")
            )
        ]
        if "image_data" not in cols:
            conn.execute(
                text("ALTER TABLE portraits ADD COLUMN image_data BLOB")
            )
            conn.commit()
            logger.info("Migrated portraits table: added image_data column")

    logger.info("Database tables ready")

    # Build the FAISS figures index at startup (blocking — before requests are served).
    # This embeds all figures via OpenAI and loads them into RAM.
    # Subsequent refreshes happen in the background on TTL expiry.
    logger.info("Building figures index (FAISS + catalog summary)...")
    figures_index.build_sync()

    try:
        await llm.ainvoke(
            [HumanMessage(content="ping")],
            config={"max_tokens": 1},
        )
        logger.info("OpenAI connection verified")
    except Exception as e:
        logger.warning("Could not reach OpenAI — %s", e)
    yield


app = FastAPI(
    title="ChronoCanvasAI Backend",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(enhance_prompt.router, prefix="/api")
app.include_router(generate.router, prefix="/api")
app.include_router(gallery.router, prefix="/api")
app.include_router(styles.router, prefix="/api")
app.include_router(figures.router, prefix="/api")
app.include_router(stats.router, prefix="/api")
app.include_router(chatbot.router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=True)
