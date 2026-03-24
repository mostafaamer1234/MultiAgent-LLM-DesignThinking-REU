from __future__ import annotations

import sys
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

_SRC = Path(__file__).resolve().parents[2]
if _SRC.name == "src" and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Legacy CLI modules live in repository `scripts/`
_ROOT = Path(__file__).resolve().parents[3]
_SCRIPTS = _ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from research_llm.bootstrap import bootstrap
from research_llm.config import get_settings

bootstrap()

from research_llm.api.jobs_store import get_job_store

settings = get_settings()

app = FastAPI(title="ResearchLLM API", version="0.2.0")

_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins if _origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class WebResearchIn(BaseModel):
    topic: str


def _serialize_report(obj):  # noqa: ANN001
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump(mode="json")
        except TypeError:
            return obj.model_dump()
    return obj


def run_web_research_job(jid: str, topic: str) -> None:
    store = get_job_store()
    try:
        store.update_job(jid, status="running", stage="gather_sources")
        import WebMarketResearch as wmr

        agent = wmr.WebMarketResearchAgent()
        store.update_job(jid, stage="synthesize")
        report = agent.conduct_web_research(topic)
        if report is None:
            store.update_job(
                jid,
                status="failed",
                error="Research produced no report (no sources or failure).",
                stage="done",
            )
            return
        payload = _serialize_report(report)
        store.update_job(
            jid,
            status="succeeded",
            stage="done",
            result={"report": payload},
        )
    except Exception as e:
        store.update_job(jid, status="failed", error=repr(e), stage="error")


@app.on_event("startup")
def _startup() -> None:
    get_job_store()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
def ready() -> dict[str, str]:
    get_job_store()
    return {"status": "ready"}


@app.post("/v1/jobs/web-research")
def create_web_research(
    body: WebResearchIn,
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    jid = get_job_store().create_job("web-research", {"topic": body.topic})
    background_tasks.add_task(run_web_research_job, jid, body.topic)
    return {"job_id": jid, "status": "queued"}


@app.get("/v1/jobs/{job_id}")
def get_job(job_id: str) -> dict:
    rec = get_job_store().get_job(job_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "id": rec.id,
        "status": rec.status,
        "job_type": rec.job_type,
        "stage": rec.stage,
        "payload": rec.payload,
        "result": rec.result,
        "error": rec.error,
        "created_at": rec.created_at,
        "updated_at": rec.updated_at,
    }
