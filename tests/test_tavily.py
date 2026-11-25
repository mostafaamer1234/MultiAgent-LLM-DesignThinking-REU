from __future__ import annotations

from research_llm.search import tavily


class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_no_api_key_means_no_network_call(monkeypatch):
    monkeypatch.setattr(tavily.requests, "post", lambda *a, **k: (_ for _ in ()).throw(AssertionError("called")))
    assert tavily.tavily_search("q", api_key="") == []


def test_keeps_only_results_with_url_and_content(monkeypatch):
    payload = {"results": [
        {"url": "https://a.example", "title": "A", "content": " text "},
        {"url": "https://b.example", "title": "B", "content": ""},
        {"url": None, "title": "C", "content": "orphan"},
    ]}
    monkeypatch.setattr(tavily.requests, "post", lambda *a, **k: _Resp(payload))
    assert tavily.tavily_search("q", api_key="k") == [{"url": "https://a.example", "title": "A", "content": "text"}]


def test_network_errors_degrade_to_empty(monkeypatch):
    def boom(*a, **k):
        raise ConnectionError("down")

    monkeypatch.setattr(tavily.requests, "post", boom)
    assert tavily.tavily_search("q", api_key="k") == []
