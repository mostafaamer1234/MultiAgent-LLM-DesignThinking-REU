"""Export a saved pipeline run (data/outputs/*.json) as the studio's sample board (site/sample.json).

    python tools/export_site_sample.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "outputs"


def main() -> None:
    biz = json.loads((OUT / "business_info.json").read_text())
    market = json.loads(biz["market_data"])
    personas = json.loads((OUT / "persona_output.json").read_text())["personas"]
    conv = json.loads((OUT / "conversation_history.json").read_text())
    hyp = json.loads((OUT / "hypothesis_analysis.json").read_text())
    hypotheses = [h.strip() for h in re.split(r"\n\s*\d+\.\s*Hypothesis:\s*", "\n" + hyp["hypotheses"]) if h.strip()]
    interviews = {}
    for key, val in conv.items():
        name = val["persona"]["Name"]
        interviews[name] = [{"q": t.get("user") or t.get("question") or "", "a": t.get("persona") or t.get("response") or t.get("answer") or ""}
                            for t in val.get("conversations", []) if isinstance(t, dict)]
    sample = {
        "topic": market["topic"],
        "business_description": biz["business_description"],
        "business_vision": biz["business_vision"],
        "market": {k: market[k] for k in ("executive_summary", "market_overview", "market_trends", "opportunities", "risks_and_challenges") if k in market},
        "personas": personas,
        "interviews": interviews,
        "hypotheses": hypotheses,
        "prototypes": {r["hypothesis"]: r["recommendation"] for r in hyp.get("recommendations", [])},
    }
    (ROOT / "site" / "sample.json").write_text(json.dumps(sample, indent=1))
    print(len(personas), "personas,", len(hypotheses), "hypotheses,", sum(len(v) for v in interviews.values()), "interview turns")


if __name__ == "__main__":
    main()
