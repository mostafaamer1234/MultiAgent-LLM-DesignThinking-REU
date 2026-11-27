"""API tests with the research agent replaced by a fake, so no API keys or network are needed."""

from __future__ import annotations

import sys
import types

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel


class FakeReport(BaseModel):
    topic: str
    sources: list[str]


def _install_fake_agent(monkeypatch, report):
    class FakeAgent:
        def conduct_web_research(self, topic):
            return report(topic) if callable(report) else report

    module = types.ModuleType("WebMarketResearch")
    module.WebMarketResearchAgent = FakeAgent
    monkeypatch.setitem(sys.modules, "WebMarketResearch", module)


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("RESEARCH_LLM_DATABASE_URL", f"sqlite:///{tmp_path / 'jobs.db'}")
    from research_llm.api import jobs_store
    from research_llm.config import settings as settings_mod

    settings_mod.get_settings.cache_clear()
    monkeypatch.setattr(jobs_store, "_job_store", None)
    from research_llm.api.main import app

    with TestClient(app) as c:
        yield c
    assert (tmp_path / "jobs.db").exists()  # the test used its own database, not data/jobs.db
    settings_mod.get_settings.cache_clear()


def test_health_and_ready(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/ready").json() == {"status": "ready"}


def test_web_research_job_succeeds_and_stores_report(client, monkeypatch):
    _install_fake_agent(monkeypatch, lambda topic: FakeReport(topic=topic, sources=["https://example.org/a"]))
    created = client.post("/v1/jobs/web-research", json={"topic": "EV winter range"}).json()
    assert created["status"] == "queued"
    job = client.get(f"/v1/jobs/{created['job_id']}").json()  # background task runs before the response returns
    assert job["status"] == "succeeded"
    assert job["result"]["report"] == {"topic": "EV winter range", "sources": ["https://example.org/a"]}


def test_job_fails_cleanly_when_no_report(client, monkeypatch):
    _install_fake_agent(monkeypatch, None)
    jid = client.post("/v1/jobs/web-research", json={"topic": "x"}).json()["job_id"]
    job = client.get(f"/v1/jobs/{jid}").json()
    assert job["status"] == "failed" and "no report" in job["error"].lower()


def test_unknown_job_is_404(client):
    assert client.get("/v1/jobs/does-not-exist").status_code == 404


def test_topic_is_required(client):
    assert client.post("/v1/jobs/web-research", json={}).status_code == 422
