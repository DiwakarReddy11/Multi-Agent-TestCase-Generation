"""Central settings. Every value comes from environment variables / .env, never hard-coded."""

from functools import lru_cache

from dotenv import load_dotenv
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# LangSmith reads LANGSMITH_* straight from os.environ, so load .env into the process too.
load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    groq_api_key: SecretStr | None = None
    google_api_key: SecretStr | None = None
    openrouter_api_key: SecretStr | None = None

    generator_model: str = "groq:openai/gpt-oss-120b"
    judge_model: str = "google_genai:gemini-3.5-flash"
    fallback_model: str = "openrouter:recursive/flint-v1.0:free"

    llm_temperature: float = 0.2
    llm_max_retries: int = 3
    llm_timeout_s: int = 60
    cache_path: str = ".cache/llm_cache.sqlite"

    embedding_model: str = "BAAI/bge-small-en-v1.5"
    models_cache_dir: str = ".cache/models"
    chroma_path: str = "data/chroma"


@lru_cache
def get_settings() -> Settings:
    return Settings()
