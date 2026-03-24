"use client";

import { useState } from "react";

const API =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") || "http://127.0.0.1:8000";

type JobResponse = {
  id: string;
  status: string;
  stage: string;
  result: { report?: Record<string, unknown> } | null;
  error: string | null;
};

export default function Page() {
  const [topic, setTopic] = useState("");
  const [jobId, setJobId] = useState<string | null>(null);
  const [job, setJob] = useState<JobResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [pollMsg, setPollMsg] = useState("");

  async function startResearch(e: React.FormEvent) {
    e.preventDefault();
    if (!topic.trim()) return;
    setBusy(true);
    setJob(null);
    setPollMsg("");
    try {
      const r = await fetch(`${API}/v1/jobs/web-research`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: topic.trim() }),
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      setJobId(data.job_id);
      poll(data.job_id);
    } catch (err) {
      setPollMsg(String(err));
      setBusy(false);
    }
  }

  async function poll(id: string) {
    const deadline = Date.now() + 15 * 60 * 1000;
    while (Date.now() < deadline) {
      const r = await fetch(`${API}/v1/jobs/${id}`);
      if (!r.ok) {
        setPollMsg(await r.text());
        setBusy(false);
        return;
      }
      const j: JobResponse = await r.json();
      setJob(j);
      if (j.status === "succeeded" || j.status === "failed") {
        setBusy(false);
        return;
      }
      await new Promise((r) => setTimeout(r, 2000));
    }
    setPollMsg("Timed out waiting for job.");
    setBusy(false);
  }

  return (
    <main>
      <h1>ResearchLLM — Web research</h1>
      <p className="status">
        API: <code>{API}</code>
      </p>
      <form onSubmit={startResearch}>
        <label htmlFor="topic">Research topic</label>
        <textarea
          id="topic"
          rows={3}
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g. Electric micromobility market in Europe"
        />
        <button type="submit" disabled={busy}>
          {busy ? "Running…" : "Start job"}
        </button>
      </form>
      {pollMsg && <p className="status">{pollMsg}</p>}
      {jobId && (
        <p className="status">
          Job <code>{jobId}</code> — {job?.status ?? "…"} {job?.stage ? `(${job.stage})` : ""}
        </p>
      )}
      {job?.error && (
        <pre style={{ color: "#f4212e" }}>{job.error}</pre>
      )}
      {job?.result?.report && (
        <pre>{JSON.stringify(job.result.report, null, 2)}</pre>
      )}
    </main>
  );
}
