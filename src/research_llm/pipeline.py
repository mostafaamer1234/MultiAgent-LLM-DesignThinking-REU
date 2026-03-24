"""
End-to-end orchestration: optional web research → Agent1EX (personas) → Agent2 (hypotheses).

Run from repo root: ``python main.py`` or installed: ``research-llm-pipeline``.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from research_llm.bootstrap import bootstrap
from research_llm.paths import repo_root

bootstrap()


def _scripts_dir() -> Path:
    return repo_root() / "scripts"


def run_web_research_phase(topic: str) -> bool:
    """Phase 1: gather sources and save a JSON report under data/outputs/."""
    scripts = _scripts_dir()
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))

    import WebMarketResearch as wmr  # noqa: PLC0415

    print("\n" + "=" * 60)
    print("PHASE 1 — Web market research")
    print("=" * 60 + "\n")
    agent = wmr.WebMarketResearchAgent()
    report = agent.conduct_web_research(topic)
    if not report:
        print("\nNo report produced (check API keys / network).")
        return False
    saved = agent.save_report(report, None)
    if saved:
        print(f"\nReport saved: {saved}")
        print(
            "\nNext (Phase 2): choose JSON input (option 3) in Agent1EX and pick this file.\n"
        )
    return bool(saved)


def _run_script(name: str, extra_args: list[str] | None = None) -> int:
    root = repo_root()
    argv = [sys.executable, str(root / "scripts" / name)]
    if extra_args:
        argv.extend(extra_args)
    return subprocess.call(
        argv,
        cwd=str(root),
        env=os.environ.copy(),
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Run the ResearchLLM pipeline: research → personas → hypotheses.",
    )
    parser.add_argument(
        "--topic",
        help="Topic for Phase 1 web research (non-empty skips the prompt).",
    )
    parser.add_argument(
        "--skip-research",
        action="store_true",
        help="Skip Phase 1 (use existing JSON in data/outputs/ for Agent1EX).",
    )
    parser.add_argument(
        "--skip-personas",
        action="store_true",
        help="Skip Phase 2 (Agent1EX); requires prior persona outputs.",
    )
    parser.add_argument(
        "--skip-hypotheses",
        action="store_true",
        help="Stop after Phase 2; do not run hypothesis agent.",
    )
    args = parser.parse_args(argv)

    print("\nResearchLLM — full pipeline")
    print(f"Repository: {repo_root()}")
    print("Artifacts:  data/outputs/\n")

    if not args.skip_research:
        topic = (args.topic or "").strip()
        if not topic:
            topic = input(
                "Phase 1 — Enter market research topic (or press Enter to skip): "
            ).strip()
        if topic:
            if not run_web_research_phase(topic):
                sys.exit(1)
        else:
            print("Skipping Phase 1 (no topic).\n")
    else:
        print("Skipping Phase 1 (--skip-research).\n")

    if not args.skip_personas:
        print("=" * 60)
        print("PHASE 2 — Personas & interviews (Agent1EX)")
        print("=" * 60)
        print(
            "• Enter business description & vision when asked.\n"
            "• For market data: choose 3 (JSON file) and select a report from data/outputs/\n"
            "  if you ran Phase 1, or use PDF/text/another source.\n"
            "• Chat with each persona; data is saved to data/outputs/ when you exit.\n"
        )
        code = _run_script("Agent1EX.py")
        if code != 0:
            print(f"\nAgent1EX exited with code {code}.")
            sys.exit(code)
    else:
        print("Skipping Phase 2 (--skip-personas).\n")

    if not args.skip_hypotheses:
        print("\n" + "=" * 60)
        print("PHASE 3 — Hypotheses & prototypes (Agent2Hypothesis)")
        print("=" * 60 + "\n")
        code = _run_script("Agent2Hypothesis.py", ["--analyze"])
        if code != 0:
            print(f"\nAgent2Hypothesis exited with code {code}.")
            sys.exit(code)
    else:
        print("Skipping Phase 3 (--skip-hypotheses).\n")

    print("\nPipeline finished. Review data/outputs/ for JSON results.\n")


if __name__ == "__main__":
    main()
