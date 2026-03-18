import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


def get_str(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def get_int(key: str, default: int = 0) -> int:
    value = os.environ.get(key)
    return int(value) if value is not None else default


def get_float(key: str, default: float = 0.0) -> float:
    value = os.environ.get(key)
    return float(value) if value is not None else default


def get_bool(key: str, default: bool = False) -> bool:
    value = os.environ.get(key)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    openai_api_key: str = get_str("OPENAI_API_KEY")
    port: int = get_int("PORT")
    frontend_url: str = get_str("FRONTEND_URL")
    log_level: str = get_str("LOG_LEVEL")
    openai_prompt_model: str = get_str("OPENAI_PROMPT_MODEL")
    openai_prompt_temperature: float = get_float("OPENAI_PROMPT_TEMPERATURE")
    openai_prompt_max_retries: int = get_int("OPENAI_PROMPT_MAX_RETRIES")

    openai_image_model: str = get_str("OPENAI_IMAGE_MODEL")
    image_size: str = get_str("IMAGE_SIZE")

    # Rate limiting (slowapi)
    generate_rate_limit: str = get_str("GENERATE_RATE_LIMIT")

    # Chatbot / RAG
    openai_embedding_model: str = get_str("OPENAI_EMBEDDING_MODEL")
    chatbot_retrieval_k: int = get_int("CHATBOT_RETRIEVAL_K")
    chatbot_index_ttl: int = get_int("CHATBOT_INDEX_TTL")

    # LangSmith optional tracing
    langsmith_tracing: bool = get_bool("LANGCHAIN_TRACING_V2", False)
    langsmith_api_key: str = get_str("LANGCHAIN_API_KEY")
    langsmith_project: str = get_str("LANGCHAIN_PROJECT", "chronocanvasai")


settings = Settings()
