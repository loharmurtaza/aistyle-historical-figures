"""
FAISS in-memory vector index + catalog summary for historical figures.

Lifecycle
---------
* Built once at server startup (blocking, before requests are served).
* TTL-based background refresh: when the TTL expires the *next caller*
  gets the current (slightly stale) data immediately while a background
  asyncio task silently rebuilds both the FAISS index and catalog summary.
  The caller is never blocked by a DB/embedding round-trip after startup.
* Hard invalidation (e.g. figure created/updated): TTL is zeroed so the
  next background task fires immediately, without waiting for the full TTL.

Two pieces of state are maintained together so they are always in sync:

  _vectorstore      — FAISS index for semantic search (RAG retrieval)
  _catalog_summary  — short text block injected into every chat system
                      prompt to answer global questions like
                      "what figures are in this app?"
"""
import asyncio
import time

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from sqlalchemy import distinct

from config import settings
from database import SessionLocal
from logger import get_logger
from models.figure import Figure

logger = get_logger(__name__)


class FiguresIndex:
    def __init__(self) -> None:
        self._vectorstore: FAISS | None = None
        self._catalog_summary: str = ""
        self._last_built_at: float = 0.0          # epoch seconds
        self._building: bool = False               # concurrency guard
        self._embeddings = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            model=settings.openai_embedding_model,
        )

    # ── public interface ─────────────────────────────────────────────────

    def build_sync(self) -> None:
        """Blocking build — call from startup before the event loop is busy."""
        self._run_build()

    async def build_async(self) -> None:
        """Non-blocking build — runs _run_build in a thread pool."""
        await asyncio.to_thread(self._run_build)

    def invalidate(self) -> None:
        """
        Force-expire the cache immediately.
        Schedules a background rebuild so the index is fresh as soon as
        possible, without blocking the caller (e.g. the figure-create endpoint).
        """
        self._last_built_at = 0.0
        logger.info("figures_index | invalidated — scheduling background rebuild")
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self.build_async())
        except RuntimeError:
            # No running loop (e.g. called from a sync context at startup).
            # The next search() call will trigger a rebuild.
            pass

    async def search(
        self, query: str, k: int = 5
    ) -> tuple[list[Document], float]:
        """
        Semantic search. Returns (docs, retrieval_ms).

        If the index has never been built, waits for the first build.
        If the TTL has expired, returns current data and triggers a
        background refresh (stale-while-revalidate).
        """
        if self._vectorstore is None:
            # First call — must block until we have something to search.
            await self.build_async()
        elif self._is_expired() and not self._building:
            # Stale — serve current data, refresh in background.
            logger.info(
                "figures_index | TTL expired — serving stale data, "
                "background refresh started"
            )
            asyncio.get_event_loop().create_task(self.build_async())

        if self._vectorstore is None:
            # DB was empty even after build — return nothing gracefully.
            return [], 0.0

        t0 = time.perf_counter()
        docs = await self._vectorstore.asimilarity_search(query, k=k)
        retrieval_ms = (time.perf_counter() - t0) * 1000.0
        return docs, retrieval_ms

    def get_catalog_summary(self) -> str:
        return self._catalog_summary

    # ── internals ────────────────────────────────────────────────────────

    def _is_expired(self) -> bool:
        return (time.time() - self._last_built_at) >= settings.chatbot_index_ttl

    def _run_build(self) -> None:
        """Synchronous build — always call via asyncio.to_thread from async code."""
        if self._building:
            return
        self._building = True
        t0 = time.perf_counter()
        try:
            db = SessionLocal()
            try:
                figures = db.query(Figure).all()
                total = len(figures)

                eras = sorted(
                    r[0]
                    for r in db.query(distinct(Figure.era)).all()
                    if r[0]
                )
                origins = sorted(
                    r[0]
                    for r in db.query(distinct(Figure.origin)).all()
                    if r[0]
                )
                all_tags: set[str] = set()
                for (tags_str,) in (
                    db.query(Figure.tags)
                    .filter(Figure.tags.isnot(None))
                    .all()
                ):
                    if tags_str:
                        all_tags.update(
                            t.strip()
                            for t in tags_str.split(",")
                            if t.strip()
                        )
                tags = sorted(all_tags)
            finally:
                db.close()

            # ── catalog summary (injected into every chat system prompt) ──
            era_preview = ", ".join(eras[:10])
            if len(eras) > 10:
                era_preview += f" … ({len(eras)} total)"
            origin_preview = ", ".join(origins[:10])
            if len(origins) > 10:
                origin_preview += f" … ({len(origins)} total)"
            tag_preview = ", ".join(tags[:15])
            if len(tags) > 15:
                tag_preview += f" … ({len(tags)} total)"

            self._catalog_summary = (
                f"Catalog overview ({total} figures total):\n"
                f"• Eras: {era_preview or 'none'}\n"
                f"• Origins: {origin_preview or 'none'}\n"
                f"• Tags: {tag_preview or 'none'}"
            )

            # ── FAISS index ───────────────────────────────────────────────
            if figures:
                docs = [_figure_to_doc(f) for f in figures]
                self._vectorstore = FAISS.from_documents(docs, self._embeddings)
            else:
                self._vectorstore = None

            self._last_built_at = time.time()
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            logger.info(
                "figures_index | built %d documents in %.0f ms "
                "| eras=%d origins=%d tags=%d",
                total,
                elapsed_ms,
                len(eras),
                len(origins),
                len(tags),
            )
        except Exception:
            logger.exception("figures_index | build failed")
        finally:
            self._building = False


# ── module-level singleton ────────────────────────────────────────────────
figures_index = FiguresIndex()


# ── helpers ───────────────────────────────────────────────────────────────
def _figure_to_doc(f: Figure) -> Document:
    born = str(f.born_year) if f.born_year is not None else "unknown"
    died = str(f.died_year) if f.died_year is not None else "unknown"
    content = (
        f"Name: {f.name}\n"
        f"Era: {f.era or 'Unknown'}\n"
        f"Origin: {f.origin or 'Unknown'}\n"
        f"Born: {born} | Died: {died}\n"
        f"Tags: {f.tags or 'none'}\n"
        f"Description: {f.description or ''}"
    )
    return Document(
        page_content=content,
        metadata={"name": f.name, "slug": f.slug},
    )
