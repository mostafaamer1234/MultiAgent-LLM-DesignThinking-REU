# Reproducibility artifacts

This directory preserves the research outputs and AI-judge records used in the comparative evaluation. Files are plain text or Markdown so they can be reviewed without proprietary software.

## Generated design-thinking outputs

| File | Contents |
|---|---|
| [`generated-outputs/test-results-1.txt`](generated-outputs/test-results-1.txt) | Earlier test record covering the Airbnb, Tesla, wildfire infrastructure, computer-science education, and single-prompt experiments contained in the first supplied Google Doc. |
| [`generated-outputs/test-results-2.txt`](generated-outputs/test-results-2.txt) | The nine core experiments: three use cases × three methods, plus the Phase 4 evaluation links, from the second supplied Google Doc. |

The three compared methods are:

1. Single-prompt design-thinking agent using market research generated from model knowledge.
2. Single-prompt design-thinking agent using web-based market research.
3. Multi-agent design-thinking system using web-based market research, persona generation/role-play, and a second hypothesis/prototype agent.

The core use cases are university computer-science education, Tesla charging/winter range, and wildfire infrastructure/policy.

## Evaluation transcripts

| Judge | Local transcript | Original share |
|---|---|---|
| GPT-4o | [`evaluation-transcripts/gpt-4o.md`](evaluation-transcripts/gpt-4o.md) | [ChatGPT share](https://chatgpt.com/share/688ce907-9a60-800f-9d8a-6e1af453ff65) |
| Claude 3.7 Sonnet | [`evaluation-transcripts/claude-3.7-sonnet.md`](evaluation-transcripts/claude-3.7-sonnet.md) | [Claude share](https://claude.ai/share/252d9d57-20a8-4daf-84b5-f96e35c72b8f) |
| Grok 4 | [`evaluation-transcripts/grok-4.md`](evaluation-transcripts/grok-4.md) | [Grok share](https://grok.com/share/c2hhcmQtMw%3D%3D_561bcaae-3230-49b8-96f8-2fe84b974a4d) |

The Claude public snapshot hides uploaded files, so that transcript contains all publicly rendered evaluator responses but cannot reproduce the hidden upload bytes. The evaluated generated outputs are preserved in `generated-outputs/`.

See [`../docs/REPRODUCIBILITY.md`](../docs/REPRODUCIBILITY.md) for provenance, known settings, unavailable metadata, and interpretation limits.
