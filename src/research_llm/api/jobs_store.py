"""SQLite-backed job store for long-running research tasks."""

from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

_lock = threading.Lock()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class JobRecord:
    id: str
    status: str
    job_type: str
    payload: dict[str, Any]
    stage: str
    result: dict[str, Any] | None
    error: str | None
    created_at: str
    updated_at: str


class JobStore:
    def __init__(self, database_url: str) -> None:
        self._path = self._sqlite_path_from_url(database_url)
        self._conn: sqlite3.Connection | None = None

    @staticmethod
    def _sqlite_path_from_url(url: str) -> str:
        if url.startswith("sqlite:////"):
            return "/" + url[11:]
        if url.startswith("sqlite:///"):
            return url[10:]
        return url

    def connect(self) -> None:
        import os

        parent = os.path.dirname(self._path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        assert self._conn is not None
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                job_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                stage TEXT NOT NULL DEFAULT '',
                result TEXT,
                error TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def create_job(self, job_type: str, payload: dict[str, Any]) -> str:
        jid = str(uuid.uuid4())
        now = _utc_now()
        with _lock:
            assert self._conn is not None
            self._conn.execute(
                """
                INSERT INTO jobs (id, status, job_type, payload, stage, result, error, created_at, updated_at)
                VALUES (?, 'queued', ?, ?, '', NULL, NULL, ?, ?)
                """,
                (jid, job_type, json.dumps(payload), now, now),
            )
            self._conn.commit()
        return jid

    def update_job(
        self,
        jid: str,
        *,
        status: str | None = None,
        stage: str | None = None,
        result: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        now = _utc_now()
        fields: list[str] = ["updated_at = ?"]
        values: list[Any] = [now]
        if status is not None:
            fields.append("status = ?")
            values.append(status)
        if stage is not None:
            fields.append("stage = ?")
            values.append(stage)
        if result is not None:
            fields.append("result = ?")
            values.append(json.dumps(result))
        if error is not None:
            fields.append("error = ?")
            values.append(error)
        values.append(jid)
        with _lock:
            assert self._conn is not None
            self._conn.execute(
                f"UPDATE jobs SET {', '.join(fields)} WHERE id = ?", values
            )
            self._conn.commit()

    def get_job(self, jid: str) -> JobRecord | None:
        with _lock:
            assert self._conn is not None
            cur = self._conn.execute("SELECT * FROM jobs WHERE id = ?", (jid,))
            row = cur.fetchone()
        if not row:
            return None
        return JobRecord(
            id=row["id"],
            status=row["status"],
            job_type=row["job_type"],
            payload=json.loads(row["payload"]),
            stage=row["stage"] or "",
            result=json.loads(row["result"]) if row["result"] else None,
            error=row["error"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


_job_store: JobStore | None = None


def get_job_store() -> JobStore:
    global _job_store
    if _job_store is None:
        from research_llm.config import get_settings

        _job_store = JobStore(get_settings().database_url)
        _job_store.connect()
    return _job_store
