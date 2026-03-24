"""Repository paths for scripts and generated artifacts."""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Directory containing `pyproject.toml`."""
    here = Path(__file__).resolve()
    for d in [here.parent] + list(here.parents):
        if (d / "pyproject.toml").is_file():
            return d
    return here.parents[2]


def data_dir() -> Path:
    d = repo_root() / "data"
    d.mkdir(parents=True, exist_ok=True)
    return d


def data_outputs_dir() -> Path:
    d = data_dir() / "outputs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def data_samples_dir() -> Path:
    d = data_dir() / "samples"
    d.mkdir(parents=True, exist_ok=True)
    return d


def list_market_research_json_paths() -> list[Path]:
    """JSON reports from market research agents (for CLI pickers)."""
    names = ("market_research", "web_market_research")
    found: list[Path] = []
    seen: set[str] = set()
    for base in (data_outputs_dir(), repo_root()):
        if not base.is_dir():
            continue
        for f in sorted(base.glob("*.json")):
            low = f.name.lower()
            if any(n in low for n in names):
                key = str(f.resolve())
                if key not in seen:
                    seen.add(key)
                    found.append(f)
    return found
