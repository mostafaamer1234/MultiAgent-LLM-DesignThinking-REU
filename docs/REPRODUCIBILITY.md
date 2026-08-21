# Reproducibility and provenance

## Experimental design

The comparison uses three real-world design-thinking scenarios:

1. Improving a university computer-science curriculum.
2. Addressing Tesla charging time and reduced winter range.
3. Improving infrastructure or policy for wildfire risk in mountain areas.

Each scenario was run with three methods, producing nine core experiments:

1. Single-prompt agent + knowledge-based market research.
2. Single-prompt agent + web-based market research.
3. Multi-agent system + web-based market research. Agent 1 creates personas and supports persona role-play; Agent 2 uses the prior inputs, personas, and conversation history to form hypotheses and prototype recommendations.

The original generated records are in [`../artifacts/generated-outputs/`](../artifacts/generated-outputs/). The implementation is in [`../scripts/`](../scripts/) and the packaged pipeline in [`../src/research_llm/`](../src/research_llm/).

## Models and settings

### Artifact generation

- Model: `gpt-4o` through LangChain and the OpenAI API.
- Recorded manuscript context: `temperature = 0.0`, `top-p = 1.0`, a fixed seed, and a maximum-token setting sufficient for complete outputs.
- Not retained in the available records: numeric seed, maximum-token value, and exact dated GPT-4o API snapshot.

The current repository also contains later engineering defaults and some scripts with their own temperatures (for example, configurable `gpt-4o-mini` research and `gpt-4o` synthesis routes). Those current defaults must not be assumed to be the exact settings of every archived experiment.

### AI-assisted evaluation

- ChatGPT judge: GPT-4o.
- Claude judge: Claude 3.7 Sonnet.
- Grok judge: Grok 4.
- Interface: provider consumer-chat share sessions.

The consumer interfaces did not expose or allow control of judge temperature, top-p, seed, maximum output tokens, or exact dated backend snapshots. Consequently, the transcripts support procedural inspection but not guaranteed bit-for-bit reproduction.

## Evaluation caveats

GPT-4o generated the candidate artifacts and also served as the ChatGPT judge. This creates possible self-preference or same-model-family bias. Claude 3.7 Sonnet and Grok 4 add cross-provider comparison, but are still AI judges and do not create fully independent ground truth.

No independent qualified-human score set using the five evaluation criteria was found in the available project materials. The persona role-play participant is part of the method and is not treated as an independent outcome evaluator. AI-judge rankings should therefore be interpreted as exploratory model-based comparisons.

For stronger follow-up validation, anonymize and randomize outputs, blind multiple qualified evaluators to method labels and authorship, apply the same criterion-level rubric independently, and report agreement (for example, ICC or Kendall's W).

## Source records

- [Google Doc: first generated-output record](https://docs.google.com/document/d/1Nx8J319JpaGsJKL_NDV0Qos7vTJWJFserEA6vrZEq_A/edit?usp=sharing)
- [Google Doc: nine-experiment record and evaluation links](https://docs.google.com/document/d/1001rUlJrw4GdoQcSx57l-_IYJkovhBHE13s7M0N49m4/edit?usp=sharing)
- [GPT-4o evaluation share](https://chatgpt.com/share/688ce907-9a60-800f-9d8a-6e1af453ff65)
- [Claude 3.7 Sonnet evaluation share](https://claude.ai/share/252d9d57-20a8-4daf-84b5-f96e35c72b8f)
- [Grok 4 evaluation share](https://grok.com/share/c2hhcmQtMw%3D%3D_561bcaae-3230-49b8-96f8-2fe84b974a4d)

## Manuscript context

The latest revised-paper context available to this packaging task identifies the models and limitations above. The revised Word manuscript itself was not available as a recoverable local attachment, so it is not included here. This document records only the supported reproducibility statements and does not invent or reconstruct the manuscript.
