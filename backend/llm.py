"""
Shared LangChain LLM client — initialised once, reused across all chains.

InMemoryCache is set globally so identical GPT-4o-mini calls (same figure +
style + user_prompt) are served from memory without hitting the API.
"""
from langchain_openai import ChatOpenAI
from langchain_core.globals import set_llm_cache
from langchain_community.cache import InMemoryCache
from config import settings

# One-liner: skips the LLM call entirely when the same prompt hits twice
set_llm_cache(InMemoryCache())

llm = ChatOpenAI(
    model=settings.openai_prompt_model,
    api_key=settings.openai_api_key,
    temperature=settings.openai_prompt_temperature,
    max_retries=settings.openai_prompt_max_retries,
)
