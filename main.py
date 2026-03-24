#!/usr/bin/env python3
"""Convenience launcher: wires ``src`` on path and runs the full pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
_SRC = _ROOT / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from research_llm.pipeline import main as run_pipeline

if __name__ == "__main__":
    run_pipeline()
