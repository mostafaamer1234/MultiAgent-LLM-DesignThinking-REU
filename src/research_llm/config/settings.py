from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from research_llm.bootstrap import repo_root


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(repo_root() / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str | None = Field(default=None, validation_alias="OPENAI_API_KEY")
    tavily_api_key: str | None = Field(default=None, validation_alias="TAVILY_API_KEY")

    allow_synthetic_fallback: bool = Field(
        default=False, validation_alias="ALLOW_SYNTHETIC_FALLBACK"
    )

    langchain_tracing_v2: bool = Field(
        default=False, validation_alias="LANGCHAIN_TRACING_V2"
    )
    langchain_api_key: str | None = Field(
        default=None, validation_alias="LANGCHAIN_API_KEY"
    )
    langchain_project: str | None = Field(
        default=None, validation_alias="LANGCHAIN_PROJECT"
    )
    langchain_endpoint: str | None = Field(
        default="https://api.smith.langchain.com",
        validation_alias="LANGCHAIN_ENDPOINT",
    )

    openai_model_research: str = Field(
        default="gpt-4o-mini", validation_alias="OPENAI_MODEL_RESEARCH"
    )
    openai_model_synthesis: str = Field(
        default="gpt-4o", validation_alias="OPENAI_MODEL_SYNTHESIS"
    )

    database_url: str = Field(
        default="sqlite:///./data/jobs.db", validation_alias="RESEARCH_LLM_DATABASE_URL"
    )
    cors_origins: str = Field(
        default="http://localhost:3000", validation_alias="CORS_ORIGINS"
    )

    @field_validator(
        "openai_api_key",
        "tavily_api_key",
        "langchain_api_key",
        mode="before",
    )
    @classmethod
    def _trim_secret(cls, v: object) -> str | None:
        if v is None:
            return None
        if isinstance(v, str):
            s = v.strip()
            if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
                s = s[1:-1].strip()
            return s or None
        return v  # type: ignore[return-value]


@lru_cache
def get_settings() -> Settings:
    return Settings()


def apply_langsmith_env() -> None:
    """Mirror optional LangSmith settings into os.environ for LangChain."""
    import os

    s = get_settings()
    if s.langchain_tracing_v2:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
    if s.langchain_api_key:
        os.environ["LANGCHAIN_API_KEY"] = s.langchain_api_key
    if s.langchain_project:
        os.environ["LANGCHAIN_PROJECT"] = s.langchain_project
    if s.langchain_endpoint:
        os.environ["LANGCHAIN_ENDPOINT"] = s.langchain_endpoint
