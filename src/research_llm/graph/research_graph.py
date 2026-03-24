"""
LangGraph orchestration scaffold for research workflows.

Extend with persona generation and hypothesis nodes; add checkpointing for HITL.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, NotRequired, TypedDict

from langgraph.graph import END, StateGraph

_ROOT = Path(__file__).resolve().parents[3]
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))


class ResearchPipelineState(TypedDict, total=False):
    topic: str
    business_description: NotRequired[str]
    business_vision: NotRequired[str]
    market_data: NotRequired[str]
    web_report: NotRequired[dict[str, Any]]
    error: NotRequired[str]


def _node_web_research(state: ResearchPipelineState) -> dict[str, Any]:
    import WebMarketResearch as wmr

    topic = (state.get("topic") or "").strip()
    if not topic:
        return {"error": "missing topic"}
    agent = wmr.WebMarketResearchAgent()
    report = agent.conduct_web_research(topic)
    if report is None:
        return {"error": "web research returned no report"}
    try:
        dump = report.model_dump(mode="json")
    except TypeError:
        dump = report.model_dump()
    return {"web_report": dump}


def build_research_graph():
    g = StateGraph(ResearchPipelineState)
    g.add_node("web_research", _node_web_research)
    g.set_entry_point("web_research")
    g.add_edge("web_research", END)
    return g.compile()


def run_linear_pipeline(topic: str) -> ResearchPipelineState:
    graph = build_research_graph()
    return graph.invoke({"topic": topic})
