"""Load `.env` from the repository root once."""

from __future__ import annotations

import os
from pathlib import Path

_ROOT: Path | None = None


def _normalize_secret(value: str | None) -> str:
    if not value or not isinstance(value, str):
        return ""
    s = value.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"":
        s = s[1:-1].strip()
    return s


def repo_root() -> Path:
    """Directory containing `pyproject.toml`, or fallback relative to this file."""
    global _ROOT
    if _ROOT is None:
        here = Path(__file__).resolve()
        for d in [here.parent, *here.parents]:
            if (d / "pyproject.toml").is_file():
                _ROOT = d
                break
        else:
            _ROOT = here.parents[2]
    return _ROOT


def bootstrap() -> None:
    """Load environment variables from `.env` at repo root (no-op if file missing)."""
    try:
        from dotenv import dotenv_values, load_dotenv
    except ImportError:
        return
    env_path = repo_root() / ".env"
    if not env_path.is_file():
        return
    load_dotenv(env_path, override=False)
    # If the shell sets OPENAI_API_KEY= (empty), load_dotenv will not override it
    # (override=False). Fill missing/blank secrets from the file so .env still wins.
    file_vars = dotenv_values(env_path) or {}
    for key in ("OPENAI_API_KEY", "TAVILY_API_KEY", "LANGCHAIN_API_KEY"):
        cur = _normalize_secret(os.environ.get(key))
        raw = _normalize_secret(
            file_vars.get(key) if isinstance(file_vars.get(key), str) else None
        )
        if raw and not cur:
            os.environ[key] = raw
    try:
        from research_llm.config.settings import get_settings

        get_settings.cache_clear()
    except Exception:
        pass


bootstrap()
