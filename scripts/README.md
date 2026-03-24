# CLI scripts

**Prefer the full workflow?** From the repo root run **`python main.py`** (see [README.md](../README.md)) — it runs web research → Agent1EX → Agent2 in order.

Run individual scripts below from the **repository root** (they add `src/` to `import research_llm`):

| Script | Purpose |
|--------|---------|
| `WebMarketResearch.py` | Web-augmented market research |
| `MarketResearch.py` | Internal (LLM-only) market research |
| `ImprovementResearch.py` | Improvement analysis (no web) |
| `WebImprovementResearch.py` | Improvement analysis with web |
| `Agent1EX.py` | Personas + business context + roleplay → `data/outputs/` |
| `Agent1Persona.py` | Older multi-persona flow |
| `Agent2Hypothesis.py` | Hypotheses + prototypes from Agent1 outputs |
| `SinglePromptAgent.py` | One-shot personas + hypotheses |
| `Chat.py` | Simple ChatGPT loop |
| `Second.py` | Single persona + roleplay demo |
| `test_pdf.py` | PyPDF smoke test |

Example:

```bash
cd /path/to/ResearchLLM
python scripts/WebMarketResearch.py
python scripts/Agent1EX.py
```

Generated JSON defaults to **`data/outputs/`** (see `research_llm.paths.data_outputs_dir`).
