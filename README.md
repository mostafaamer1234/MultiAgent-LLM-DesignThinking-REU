# ResearchLLM: AI for Design Thinking

![CI](https://github.com/mostafaamer1234/MultiAgent-LLM-DesignThinking-REU/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)

> Penn State MC-REU research project (summer 2025): [LLMs for Design Thinking](https://sites.psu.edu/mcreu/2025/07/20/llms-for-design-thinking/). The manuscript is under review.


AI software engineering portfolio project focused on design thinking, market research, persona generation, and hypothesis-driven product exploration.

ResearchLLM is an end-to-end AI software engineering project that applies LLMs to the design thinking process. It turns raw market context into structured research, grounded personas, persona interviews, and testable product hypotheses through a reproducible workflow with a Python package, CLI pipeline, FastAPI service, persistent artifacts, and optional frontend.

This project is meant to demonstrate more than prompt writing. It shows how to build, organize, validate, and expose an AI workflow as software.

## Results at a glance

Three AI judges compared the three methods on each use case. The table shows the method each judge picked as best, taken from the published transcripts in [`artifacts/evaluation-transcripts/`](artifacts/evaluation-transcripts/):

| Use case | GPT-4o judge | Claude 3.7 Sonnet judge | Grok 4 judge |
|---|---|---|---|
| Computer-science education | Multi-agent + web | Multi-agent + web | Multi-agent + web |
| Tesla charging / winter range | Multi-agent + web | Multi-agent + web | Multi-agent + web |
| Wildfire infrastructure / policy | Multi-agent + web | Multi-agent + web | Multi-agent + web |

**9 of 9 judge verdicts favored the multi-agent + web-research system.** The judges cited deeper personas, more systemic hypotheses and more test-ready prototypes. Caveat: these are LLM judges, and one of them, GPT-4o, is also the generator, so self-preference bias is possible. There is no independent human score set yet (see [docs/REPRODUCIBILITY.md](docs/REPRODUCIBILITY.md)).

## Public research package

The repository now includes the evidence package requested for public reproducibility:

- **Complete generated records:** [`artifacts/generated-outputs/`](artifacts/generated-outputs/) preserves both supplied Google Docs as searchable text, including the outputs for each method and use case.
- **AI-judge transcripts:** [`artifacts/evaluation-transcripts/`](artifacts/evaluation-transcripts/) contains the public GPT-4o, Claude 3.7 Sonnet, and Grok 4 evaluation conversations.
- **Code:** [`scripts/`](scripts/) contains the original agent workflows; [`src/research_llm/`](src/research_llm/) contains the packaged pipeline/API implementation.
- **Provenance and limitations:** [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) records known settings, unavailable metadata, judge circularity, and the absence of an independent human score set.

### Methods evaluated

| Method | Market research | Design-thinking flow |
|---|---|---|
| Single prompt + model knowledge | Knowledge-based agent | Personas, hypotheses, and prototype recommendations in one pass |
| Single prompt + web research | Web-search agent | Personas, hypotheses, and prototype recommendations in one pass |
| Multi-agent + web research | Web-search agent | Persona generation and role-play, then hypothesis and prototype generation |

The nine core experiments apply these three methods to computer-science education, Tesla charging/winter range, and wildfire infrastructure/policy.

### Models used

- Candidate-output generator: GPT-4o through LangChain/OpenAI API.
- AI judges: GPT-4o (ChatGPT), Claude 3.7 Sonnet (Claude), and Grok 4 (Grok).

The available record reports generation with temperature `0.0`, top-p `1.0`, a fixed seed, and a maximum-token setting. The numeric seed, maximum-token value, and exact dated API snapshot were not retained. Judge-side sampling settings and dated backend snapshots were not exposed by the consumer chat interfaces. See the [full reproducibility notes](docs/REPRODUCIBILITY.md) before interpreting or attempting to repeat the evaluation.

## Project Objective

The objective of this project is to use LLMs to support the major stages of design thinking in a practical engineering system:

- **Empathize**: gather market context, external signals, and domain-specific research.
- **Define**: synthesize findings into a clear problem space and product framing.
- **Ideate**: generate personas and simulate role-based conversations to surface needs and friction.
- **Prototype direction**: create structured hypotheses and prototype recommendations for validation.

The goal is to help a builder move from broad market uncertainty to focused product insight through a structured workflow.

## Why This Project Is Relevant to AI Software Engineering

This repository demonstrates the kind of work employers look for in an AI software engineering project:

- Building an LLM workflow as a real application rather than a single notebook or prompt.
- Orchestrating multi-stage AI agents across research, personas, interviews, and synthesis.
- Designing a package structure with configuration, API routes, job persistence, and reusable utilities.
- Handling practical concerns such as environment loading, API keys, long-running jobs, saved outputs, and deployment.
- Supporting multiple interfaces: CLI, API, and frontend.
- Separating orchestration code from prompts and individual agents.

## Highlights

- **End-to-end AI workflow**: research -> personas -> interviews -> hypotheses.
- **Production-oriented structure**: installable package, configuration layer, reusable path helpers, Docker support.
- **API surface**: FastAPI endpoints for asynchronous research jobs and polling.
- **Persistent artifacts**: JSON outputs saved under `data/outputs/` for inspection and reuse.
- **Configurable model routing**: separate settings for research and synthesis models.
- **Extensible architecture**: LangGraph scaffold for future graph-based orchestration.
- **Frontend integration**: lightweight Next.js client for job submission and result polling.

## What the System Does

The default workflow runs three major phases:

1. **Web Market Research** (`scripts/WebMarketResearch.py`)
2. **Persona Generation and Interviews** (`scripts/Agent1EX.py`)
3. **Hypothesis and Prototype Recommendation** (`scripts/Agent2Hypothesis.py`)

Main entry point:

```bash
python main.py
```

There are also supporting modes for internal-only research, improvement analysis, and a one-shot combined agent.

## Design Thinking Workflow

### 1. Empathize

- Collect live market and domain context through web research.
- Optionally use internal-only market research based on model knowledge.
- Accept market context from JSON, text, PDF, or interactive input.

### 2. Define

- Convert research into structured summaries and reusable artifacts.
- Ground later stages in business description, business vision, and market context.

### 3. Ideate

- Generate multiple user personas from market data.
- Role-play conversations with those personas to surface goals, pain points, and preferences.

### 4. Prototype Direction

- Use persona data and conversation history to generate product hypotheses.
- Recommend lightweight prototypes or experiments to validate those hypotheses.

## Architecture Overview

### Core Entry Points

- `main.py`
  Top-level launcher for the full workflow.

- `src/research_llm/pipeline.py`
  Orchestrates research, persona, and hypothesis phases.

- `src/research_llm/cli.py`
  CLI entry point for serving the FastAPI API.

### Core Package

- `src/research_llm/config/`
  Environment-backed settings and model/runtime configuration.

- `src/research_llm/api/`
  FastAPI app and SQLite-backed job store for asynchronous research jobs.

- `src/research_llm/search/`
  Optional Tavily integration for stronger web search results.

- `src/research_llm/graph/`
  LangGraph scaffold for future graph-based orchestration.

- `src/research_llm/bootstrap.py`
  Centralized `.env` loading and runtime bootstrapping.

- `src/research_llm/paths.py`
  Repository path and artifact helpers.

### Agent Scripts

- `scripts/WebMarketResearch.py`
  External, web-augmented market research agent.

- `scripts/MarketResearch.py`
  Internal-only market research agent.

- `scripts/Agent1EX.py`
  Persona generation plus interactive persona interviews.

- `scripts/Agent2Hypothesis.py`
  Hypothesis generation and prototype recommendation from saved artifacts.

- `scripts/ImprovementResearch.py`
  Internal improvement analysis.

- `scripts/WebImprovementResearch.py`
  Web-based improvement analysis.

- `scripts/SinglePromptAgent.py`
  One-shot personas and hypotheses flow.

### Interfaces

- **CLI** for running full or partial workflows.
- **API** for submitting and polling research jobs.
- **Frontend** for lightweight interaction with the research service.

## Workflow Artifacts

Outputs are persisted under `data/outputs/`:

- `business_info.json`
  Business description, business vision, and market context.

- `persona_output.json`
  Generated personas and raw persona text.

- `conversation_history.json`
  Persona interview transcripts.

- `hypothesis_analysis.json`
  Hypotheses and prototype recommendations.

This makes the workflow inspectable, reusable, and easier to debug or extend.

## Tech Stack

- Python 3.11+
- LangChain
- LangChain OpenAI
- LangGraph
- FastAPI
- Uvicorn
- SQLite
- Pydantic / Pydantic Settings
- Requests / BeautifulSoup / Trafilatura / Newspaper3k
- Optional Tavily search integration
- Next.js + React
- Docker / Docker Compose

## Quick Start

### 1. Create environment file

```bash
cp .env.example .env
```

### 2. Add your OpenAI key

```env
OPENAI_API_KEY=sk-...
```

Optional:

- `TAVILY_API_KEY` for better web search.
- `ALLOW_SYNTHETIC_FALLBACK=true` only for demos.

### 3. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 4. Validate credentials

```bash
python check_openai.py
```

## Running the Full Pipeline

From repository root:

```bash
python main.py
```

With topic provided up front:

```bash
python main.py --topic "ai use cases for lawyers"
```

CLI package entry point after install:

```bash
research-llm-pipeline --topic "ai use cases for lawyers"
```

Useful flags:

- `--skip-research`
- `--skip-personas`
- `--skip-hypotheses`

Note: the persona phase (`Agent1EX`) is interactive by design.

## Run Individual Agents

See `scripts/README.md` for details. Common commands:

```bash
python scripts/WebMarketResearch.py
python scripts/MarketResearch.py
python scripts/Agent1EX.py
python scripts/Agent2Hypothesis.py --analyze
python scripts/ImprovementResearch.py
python scripts/WebImprovementResearch.py
python scripts/SinglePromptAgent.py
```

## API Usage

Start the server:

```bash
uvicorn research_llm.api.main:app --reload --app-dir src
```

Or:

```bash
research-llm-api
```

Endpoints:

- `POST /v1/jobs/web-research` with `{"topic": "..."}`
- `GET /v1/jobs/{job_id}`
- `GET /health`
- `GET /ready`

Example request:

```json
{
  "topic": "electric micromobility market in Europe"
}
```

## Frontend (Next.js)

```bash
cd frontend
npm install
echo 'NEXT_PUBLIC_API_BASE=http://localhost:8000' > .env.local
npm run dev
```

Then open [http://localhost:3000](http://localhost:3000).

## Docker

```bash
cp .env.example .env
docker compose up --build
```

## Configuration

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Required for LLM calls |
| `TAVILY_API_KEY` | Optional; improves web search quality |
| `ALLOW_SYNTHETIC_FALLBACK` | Default `false`; enables labeled demo fallback data |
| `OPENAI_MODEL_RESEARCH` | Lower-cost model for query and relevance passes |
| `OPENAI_MODEL_SYNTHESIS` | Model for final report synthesis |
| `RESEARCH_LLM_DATABASE_URL` | API job database URL |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins |

## Project Layout

| Path | Description |
|------|-------------|
| `main.py` | Full pipeline entry |
| `check_openai.py` | Credentials smoke test |
| `src/research_llm/` | Core package for config, API, orchestration, and helpers |
| `scripts/` | Agent implementations and CLI workflows |
| `data/outputs/` | Generated research, personas, and hypothesis artifacts |
| `data/samples/` | Sample inputs |
| `frontend/` | Next.js client |
| `tests/` | Automated tests |
| `docs/` | Supporting project documentation |

## Engineering Decisions Worth Noticing

- **Artifact-based handoff**: each phase produces structured JSON that downstream phases can reuse.
- **Mixed orchestration model**: interactive scripts plus service-driven API jobs.
- **Separation of concerns**: configuration, API, storage, search integration, and orchestration are split into modules.
- **Environment-aware bootstrapping**: `.env` loading is centralized instead of duplicated across entry points.
- **Extensibility path**: LangGraph scaffolding is included for future stateful orchestration.

## Testing

```bash
pytest
```

Additional manual validation paths:

- `python check_openai.py`
- `python scripts/test_pdf.py`
- run the API and submit a research job
- run the full pipeline and inspect `data/outputs/`

## Current Limitations

- Persona interviews are still interactive rather than fully automated.
- Output quality is prompt- and model-dependent.
- Automated test coverage is currently limited.
- Web-based research depends on network access and valid API credentials.
- Some workflows are stronger as research prototypes than production-ready systems without additional hardening.

## Engineering Roadmap

- Reduce manual steps in the persona phase with non-interactive CLI options.
- Add evaluation harnesses for output quality and consistency.
- Expand observability with structured logs, latency metrics, and cost tracking.
- Add CI checks for tests, linting, and pipeline smoke runs.
- Expand graph-based orchestration and checkpointing.
- Harden packaging and local-vs-Docker environment defaults.

## Security Notes

- Never commit `.env` or secrets.
- Rotate exposed keys immediately.
- Use separate credentials per environment when possible.
- Keep synthetic fallback disabled in normal usage unless clearly labeling demo data.

## Highlights

- pipeline orchestration and modular agent design
- API and job execution patterns
- environment and secret handling
- practical integration of LLMs into a design thinking workflow
- packaging, persistence, and deployment surface

## Summary

This project demonstrates the ability to design and implement a multi-stage LLM application, package it as maintainable software, expose it through APIs, preserve reusable artifacts, and structure it for future automation. It is a strong example of applied AI software engineering rather than ad hoc prompting.
ResearchLLM is an AI-assisted design thinking system that combines LLM orchestration, software engineering structure, and practical workflow design. It shows how to move from market research to personas to product hypotheses using reproducible software components instead of isolated prompt experiments.
