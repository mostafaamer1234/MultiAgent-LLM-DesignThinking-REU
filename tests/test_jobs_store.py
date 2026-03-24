from research_llm.api.jobs_store import JobStore


def test_job_lifecycle(tmp_path):
    db = tmp_path / "t.db"
    store = JobStore(f"sqlite:///{db}")
    store.connect()
    jid = store.create_job("web-research", {"topic": "x"})
    store.update_job(jid, status="running", stage="x")
    store.update_job(jid, status="succeeded", stage="done", result={"a": 1})
    rec = store.get_job(jid)
    assert rec is not None
    assert rec.status == "succeeded"
    assert rec.result == {"a": 1}
