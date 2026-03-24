"""CLI entry: `research-llm-api` → Uvicorn."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    _src = Path(__file__).resolve().parent.parent
    if _src.name == "src" and str(_src) not in sys.path:
        sys.path.insert(0, str(_src))

    import uvicorn

    uvicorn.run(
        "research_llm.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        factory=False,
    )
