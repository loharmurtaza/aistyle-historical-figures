"""
Image generation service — LangGraph pipeline.

Graph topology:
  START → extract → build_prompt → generate → END          (happy path)
                                 ↘ soften → generate → END  (content policy)

- extract      : LLM parses figure title and resolves art style from raw input
- build_prompt : calls GPT-4o-mini to build a vivid DALL·E prompt
- generate : calls DALL·E 3; on content policy error sets a retry flag
- soften   : re-enhances with an art-only instruction (max 1 retry)
"""
from typing import Optional, TypedDict

from langchain_community.utilities.dalle_image_generator import (
    DallEAPIWrapper,
)
from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, StateGraph
from openai import APIConnectionError, APITimeoutError, BadRequestError
from openai import RateLimitError

from config import settings
from logger import get_logger
from services.prompt_builder import (
    enhance_prompt,
    enhance_prompt_with_history,
    extract_figure_and_style,
    format_prompt,
    sanitize_figure_description,
)

logger = get_logger(__name__)


# ── Public exception ─────────────────────────────────────────────

class ContentPolicyError(Exception):
    """Raised when DALL·E refuses the prompt after the soften retry."""


# ── DALL·E 3 chain ───────────────────────────────────────────────

_dalle = DallEAPIWrapper(
    model=settings.openai_image_model,
    n=1,
    size=settings.image_size,
    quality="standard",
    api_key=settings.openai_api_key,
)

_dalle_chain = RunnableLambda(_dalle.run).with_retry(
    retry_if_exception_type=(
        RateLimitError, APITimeoutError, APIConnectionError
    ),
    stop_after_attempt=2,
)

# ── LangGraph state ──────────────────────────────────────────────


class _State(TypedDict):
    figure: str              # raw user input
    style: str               # raw style input (may be empty)
    user_prompt: str
    session_id: Optional[str]
    enhance: bool            # True = creative, False = format-only
    figure_title: Optional[str]    # extracted clean display name
    resolved_style: Optional[str]  # extracted or LLM-decided style
    enhanced_prompt: Optional[str]
    image_url: Optional[str]
    content_policy_hit: bool
    attempt: int


# ── Graph nodes ──────────────────────────────────────────────────

async def _extract_node(state: _State) -> dict:
    """Parse figure title and resolve art style from raw input."""
    extracted = await extract_figure_and_style(
        figure=state["figure"],
        style=state["style"],
    )
    logger.info(
        "Extracted — figure_title=%r  resolved_style=%r",
        extracted.figure_title,
        extracted.style,
    )
    return {
        "figure_title": extracted.figure_title,
        "resolved_style": extracted.style,
    }


async def _enhance_node(state: _State) -> dict:
    resolved_style = state.get("resolved_style") or state["style"]
    if not state.get("enhance", True):
        ep = await format_prompt(
            figure=state["figure"],
            style=resolved_style,
            user_prompt=state["user_prompt"],
        )
    elif state.get("session_id"):
        ep = await enhance_prompt_with_history(
            figure=state["figure"],
            style=resolved_style,
            session_id=state["session_id"],
            user_prompt=state["user_prompt"],
        )
    else:
        ep = await enhance_prompt(
            figure=state["figure"],
            style=resolved_style,
            user_prompt=state["user_prompt"],
        )
    preview = ep[:200] + "..." if len(ep) > 200 else ep
    logger.info("Enhanced prompt: %s", preview)
    return {"enhanced_prompt": ep}


async def _generate_node(state: _State) -> dict:
    try:
        url = await _dalle_chain.ainvoke(state["enhanced_prompt"])
        logger.info(
            "Image generated successfully — figure=%r  url=%.80s",
            state.get("figure_title") or state["figure"],
            url,
        )
        return {"image_url": url, "content_policy_hit": False}
    except BadRequestError:
        logger.warning(
            "Content policy hit for figure=%r (attempt %d)",
            state.get("figure_title") or state["figure"],
            state["attempt"] + 1,
        )
        return {
            "content_policy_hit": True,
            "attempt": state["attempt"] + 1,
        }


async def _soften_node(state: _State) -> dict:
    """Re-enhance with a sanitized, policy-safe scene description."""
    safe_figure = await sanitize_figure_description(state["figure"])
    logger.info("Softened figure description: %r", safe_figure)
    soften_ctx = (
        "Artistic and symbolic interpretation only. "
        "Focus on allegorical, painterly representation. "
        "Avoid any realistic or potentially sensitive depictions."
    )
    style = state.get("resolved_style") or state["style"]
    if not state.get("enhance", True):
        ep = await format_prompt(
            figure=safe_figure,
            style=style,
            user_prompt=soften_ctx,
        )
    else:
        ep = await enhance_prompt(
            figure=safe_figure,
            style=style,
            user_prompt=soften_ctx,
        )
    return {"enhanced_prompt": ep}


def _route_after_generate(state: _State) -> str:
    if state["content_policy_hit"] and state["attempt"] < 2:
        return "soften"
    return END


# ── Build the graph ──────────────────────────────────────────────

_workflow = StateGraph(_State)
_workflow.add_node("extract", _extract_node)
_workflow.add_node("build_prompt", _enhance_node)
_workflow.add_node("generate", _generate_node)
_workflow.add_node("soften", _soften_node)
_workflow.set_entry_point("extract")
_workflow.add_edge("extract", "build_prompt")
_workflow.add_edge("build_prompt", "generate")
_workflow.add_conditional_edges(
    "generate",
    _route_after_generate,
    {"soften": "soften", END: END},
)
_workflow.add_edge("soften", "generate")

_generation_graph = _workflow.compile()


# ── Public interface ─────────────────────────────────────────────

async def generate_portrait(
    figure: str,
    style: str,
    user_prompt: str = "",
    session_id: Optional[str] = None,
    enhance: bool = True,
) -> dict:
    """
    Run the LangGraph extract→enhance→generate pipeline.
    On a content policy refusal the graph automatically softens the prompt
    and retries once before raising ContentPolicyError.
    Returns dict with enhanced_prompt, image_url, figure_title,
    and resolved_style.
    """
    final = await _generation_graph.ainvoke({
        "figure": figure,
        "style": style,
        "user_prompt": user_prompt or "None provided",
        "session_id": session_id,
        "enhance": enhance,
        "figure_title": None,
        "resolved_style": None,
        "enhanced_prompt": None,
        "image_url": None,
        "content_policy_hit": False,
        "attempt": 0,
    })

    if final.get("content_policy_hit") and not final.get("image_url"):
        raise ContentPolicyError(
            "DALL·E refused the prompt even after softening."
        )

    return {
        "enhanced_prompt": final["enhanced_prompt"],
        "image_url": final["image_url"],
        "figure_title": final.get("figure_title") or figure,
        "resolved_style": final.get("resolved_style") or style,
    }
