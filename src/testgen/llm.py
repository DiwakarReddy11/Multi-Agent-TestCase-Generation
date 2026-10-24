"""LLM factory: the one place that knows about providers, keys, caching and fallbacks."""

from pathlib import Path
from typing import Any, Literal

from langchain.chat_models import init_chat_model
from langchain_community.cache import SQLiteCache
from langchain_core.globals import set_llm_cache
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, SecretStr

from testgen.config import Settings, get_settings

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
Role = Literal["generator", "judge"]


def _key(secret: SecretStr | None) -> str | None:
    return secret.get_secret_value() if secret else None


def build_chat_model(spec: str, settings: Settings | None = None) -> BaseChatModel:
    """Build a chat model from a 'provider:model' spec, e.g. 'groq:llama-3.3-70b-versatile'."""
    s = settings or get_settings()
    provider, _, model = spec.partition(":")
    common: dict[str, Any] = {
        "temperature": s.llm_temperature,
        "max_retries": s.llm_max_retries,
        "timeout": s.llm_timeout_s,
    }

    if provider == "openrouter":
        return ChatOpenAI(
            model=model, base_url=OPENROUTER_BASE_URL, api_key=_key(s.openrouter_api_key), **common
        )
    keys = {"groq": s.groq_api_key, "google_genai": s.google_api_key}
    if provider not in keys:
        raise ValueError(f"Unsupported provider '{provider}' in spec '{spec}'")
    return init_chat_model(model, model_provider=provider, api_key=_key(keys[provider]), **common)


def get_llm(role: Role = "generator", schema: type[BaseModel] | None = None) -> Runnable:
    """Primary model for the role, with the free fallback model behind it.

    Structured output is applied to each model *before* adding fallbacks, because a
    fallback wrapper doesn't support `.with_structured_output()`.
    """
    s = get_settings()
    primary_spec = s.generator_model if role == "generator" else s.judge_model
    models = [build_chat_model(spec, s) for spec in (primary_spec, s.fallback_model)]
    runnables: list[Runnable] = [m.with_structured_output(schema) if schema else m for m in models]
    return runnables[0].with_fallbacks(runnables[1:])


def enable_cache(path: str | None = None) -> None:
    """Cache identical LLM calls on disk, so re-runs during development cost no quota."""
    db = Path(path or get_settings().cache_path)
    db.parent.mkdir(parents=True, exist_ok=True)
    set_llm_cache(SQLiteCache(database_path=str(db)))
