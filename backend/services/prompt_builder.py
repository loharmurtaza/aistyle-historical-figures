"""
Prompt enhancement service.

Stateless chain  : ChatPromptTemplate | llm | StrOutputParser()
History-aware    : RunnableWithMessageHistory wraps the same chain with a
                   MessagesPlaceholder so the model remembers the previous
                   figure/style within a session.
Chat history is  persisted to chat_history.db via SQLChatMessageHistory.
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory
from pydantic import BaseModel, Field

from llm import llm


# ── Extraction: figure title + resolved style ────────────────────

class FigureStyleExtraction(BaseModel):
    figure_title: str = Field(
        description=(
            "Clean, display-ready name of the historical figure only. "
            "E.g. 'Cleopatra', 'Napoleon Bonaparte'. "
            "Strip out any style, scene, or descriptor words."
        )
    )
    style: str = Field(
        description=(
            "The art style to use, resolved by priority: "
            "(1) style embedded in the user's query "
            "(e.g. 'as a Marvel superhero' → 'Marvel superhero'); "
            "(2) the separately provided style if given; "
            "(3) if neither, choose the most fitting style "
            "for this figure and era."
        )
    )


_EXTRACT_SYSTEM = """\
You are a parser for historical portrait generation requests.

Given a raw figure description and an optional separately-provided style,
extract the figure's clean display name and the art style to use.

Style priority:
1. If the user embedded a style in their description
   (e.g. "as a Marvel superhero", "in cyberpunk style",
   "as an anime character"), extract that style.
2. Otherwise, if a separate style was explicitly provided (not empty), use it.
3. If neither, choose the most fitting art style for this figure and era.

Output ONLY the JSON — no explanation.\
"""

_extract_llm = llm.with_structured_output(FigureStyleExtraction)


async def extract_figure_and_style(
    figure: str, style: str = ""
) -> FigureStyleExtraction:
    """Extract figure title and resolve art style from user input."""
    messages = [
        {"role": "system", "content": _EXTRACT_SYSTEM},
        {
            "role": "user",
            "content": (
                f"Figure description: {figure}\n"
                f"Separately provided style: {style or 'none'}"
            ),
        },
    ]
    result = await _extract_llm.ainvoke(messages)
    # with_structured_output may return a dict or model instance
    # depending on the LangChain version
    if isinstance(result, dict):
        return FigureStyleExtraction(**result)
    return result

# ── System prompt (shared by both chains) ────────────────────────

_system = """\
You are an expert art director specialising in AI image generation for
historical portraiture.

Your job is to turn a short subject description into a vivid, detailed
DALL·E 3 prompt.

Rules:
- If a style is provided, weave it organically into the description
  (lighting, palette, brushwork, composition). Do NOT just append
  "in <style> style" at the end.
- If no style is provided, choose the single most fitting art style for
  the figure and era, then apply it the same way.
- Include era-accurate clothing, setting, and context for the historical
  figure.
- Describe mood, atmosphere, and lighting.
- Keep the prompt between 2 and 4 sentences.
- Output ONLY the image prompt — no preamble, no labels, no quotes.\
"""

# ── Stateless chain (no history) ─────────────────────────────────

_stateless_prompt = ChatPromptTemplate.from_messages([
    ("system", _system),
    ("human", (
        "Figure: {figure}\n"
        "Style: {style}\n"
        "Extra context: {user_prompt}\n\n"
        "Write the DALL·E 3 prompt now."
    )),
])

_AI_PICK_LABEL = "Choose the most fitting art style for this figure"

enhancement_chain = _stateless_prompt | llm | StrOutputParser()

# ── Format-only chain (preserve user intent, no creative additions) ───

_format_system = """\
You are a technical formatter for AI image generation prompts.

Your job is to take the user's description and reformat it into a clear,
well-structured DALL·E 3 prompt WITHOUT adding creative elements that
were not in the original description.

Rules:
- Preserve ALL of the user's original ideas exactly as described.
- Do NOT add new characters, scenes, lighting, atmosphere, or details
  that the user did not mention.
- Apply the art style cleanly to the existing description.
- Keep it concise (1–3 sentences).
- Output ONLY the formatted prompt — no preamble, no labels, no quotes.\
"""

_format_prompt = ChatPromptTemplate.from_messages([
    ("system", _format_system),
    ("human", (
        "Figure: {figure}\n"
        "Style: {style}\n"
        "User description: {user_prompt}\n\n"
        "Format this into a DALL·E 3 prompt now."
    )),
])

format_chain = _format_prompt | llm | StrOutputParser()

# ── History-aware chain (RunnableWithMessageHistory) ─────────────
#
# MessagesPlaceholder inserts the session's previous messages between
# the system prompt and the new human message, so the model can reference
# "same figure as before" or "change the style" naturally.

# In-memory store keyed by session_id.
# For production persistence swap _get_session_history to use
# SQLChatMessageHistory with an async-compatible DB
# (e.g. PostgreSQL + asyncpg).
_session_store: dict[str, InMemoryChatMessageHistory] = {}

_history_prompt = ChatPromptTemplate.from_messages([
    ("system", _system),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", (
        "Figure: {input}\n"
        "Style: {style}\n"
        "Extra context: {user_prompt}\n\n"
        "Write the DALL·E 3 prompt now."
    )),
])

_history_chain = _history_prompt | llm | StrOutputParser()


def _get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in _session_store:
        _session_store[session_id] = InMemoryChatMessageHistory()
    return _session_store[session_id]


history_aware_enhance_chain = RunnableWithMessageHistory(
    _history_chain,
    _get_session_history,
    input_messages_key="input",       # key added to history as HumanMessage
    history_messages_key="chat_history",
)


# ── Sanitize chain (DALL·E content-policy softening) ─────────────

_SANITIZE_SYSTEM = """\
You are a content safety rewriter for AI image generation prompts.

Your job is to rewrite a scene description so it will pass DALL·E 3's content
policy, while preserving the creative intent as closely as possible.

Rules:
- Replace all combat, fighting, violence, or conflict language with peaceful,
  symbolic, or artistic alternatives (e.g. "fighting" → "facing", "battling"
  → "standing before", "clashing" → "meeting").
- Keep ALL characters and the overall scene intent intact.
- Frame the scene as a mythological, allegorical, or symbolic composition.
- Output ONLY the rewritten description — no preamble, no labels, no quotes.\
"""

_sanitize_prompt = ChatPromptTemplate.from_messages([
    ("system", _SANITIZE_SYSTEM),
    ("human", "Original description: {figure}\n\nRewrite it now."),
])

sanitize_chain = _sanitize_prompt | llm | StrOutputParser()


# ── Public interface ─────────────────────────────────────────────
async def sanitize_figure_description(figure: str) -> str:
    """Rewrite a potentially policy-violating figure description to be DALL·E-safe."""
    result = await sanitize_chain.ainvoke({"figure": figure})
    return result.strip()


async def format_prompt(
    figure: str, style: str = "", user_prompt: str = ""
) -> str:
    """Format-only — preserve user intent, no creative additions."""
    result = await format_chain.ainvoke({
        "figure": figure,
        "style": style or _AI_PICK_LABEL,
        "user_prompt": user_prompt or figure,
    })
    return result.strip()


async def enhance_prompt(
    figure: str, style: str = "", user_prompt: str = ""
) -> str:
    """Stateless enhancement — no session context."""
    result = await enhancement_chain.ainvoke({
        "figure": figure,
        "style": style or _AI_PICK_LABEL,
        "user_prompt": user_prompt or "None provided",
    })
    return result.strip()


async def enhance_prompt_with_history(
    figure: str,
    style: str = "",
    session_id: str = "",
    user_prompt: str = "",
) -> str:
    """
    History-aware enhancement.
    The model sees previous figure/style exchanges for this session,
    enabling follow-ups like "same figure but in watercolor".
    """
    result = await history_aware_enhance_chain.ainvoke(
        {
            "input": figure,
            "style": style or _AI_PICK_LABEL,
            "user_prompt": user_prompt or "None provided",
        },
        config={"configurable": {"session_id": session_id}},
    )
    return result.strip()
