#!/usr/bin/env python3
"""Quick OpenAI credential check (reads project root `.env`). Run: python check_openai.py"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from research_llm.bootstrap import bootstrap
from research_llm.config import get_settings


def main() -> int:
    bootstrap()
    s = get_settings()
    if not (s.openai_api_key or "").strip():
        print(
            "No OPENAI_API_KEY after loading `.env`. "
            "Set it in .env (no spaces around `=`): OPENAI_API_KEY=sk-...",
            file=sys.stderr,
        )
        return 1
    try:
        from openai import OpenAI

        client = OpenAI(api_key=s.openai_api_key)
        client.models.list()
    except Exception as e:  # noqa: BLE001 — surface API errors to the user
        msg = str(e)
        if "401" in msg or "invalid_api_key" in msg or "Incorrect API key" in msg:
            print(
                "OpenAI rejected this key (invalid or revoked). "
                "Create a new secret key at https://platform.openai.com/account/api-keys "
                "and update `.env` (then run this script again).",
                file=sys.stderr,
            )
        else:
            print(msg, file=sys.stderr)
        return 1
    print("OpenAI credentials OK (API accepted the key).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
