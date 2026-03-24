"""Optional Tavily search API — returns text snippets tied to real URLs."""

from __future__ import annotations

from typing import Any

import requests


def tavily_search(
    query: str,
    api_key: str,
    max_results: int = 5,
    search_depth: str = "advanced",
) -> list[dict[str, Any]]:
    """Call Tavily /search. See https://docs.tavily.com"""
    if not api_key:
        return []
    try:
        r = requests.post(
            "https://api.tavily.com/search",
            json={
                "api_key": api_key,
                "query": query,
                "max_results": max_results,
                "search_depth": search_depth,
                "include_answer": False,
            },
            timeout=60,
        )
        r.raise_for_status()
        data = r.json()
        out = []
        for row in data.get("results") or []:
            url = row.get("url")
            content = (row.get("content") or "").strip()
            title = (row.get("title") or url or "source").strip()
            if url and content:
                out.append({"url": url, "title": title, "content": content})
        return out
    except Exception:
        return []
