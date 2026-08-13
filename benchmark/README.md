# Benchmark question set

Frozen once complete. After the graph exists, questions are never edited,
added, or removed; git history is the witness. This is what makes the Phase 5
numbers a benchmark instead of a demo.

## Methodology and provenance

This is an **LLM-drafted, human-verified** benchmark. Questions were drafted
by Claude (Sonnet agents) from the corpus in data/text/, with a hard rule
that every evidence quote be located verbatim in primary filing text before
a candidate survived (sweep notes were leads only, never quotable). Drafts
were then deduplicated and balanced to 80.

Verification protocol: every question ships with "verified": false. The
human author checks each question against the quoted filing in data/text/
and flips the flag only after seeing the evidence with their own eyes.
**The set freezes when all 80 are verified: true** (and the ontology
sanity-check passes). Until then, a question that fails verification is
fixed or replaced, with the change noted in DECISIONS.md.

Known bias, disclosed: an LLM drafted these questions and an LLM (Phase 3)
extracts the graph, so the benchmark may over-represent facts LLMs reliably
notice, which can flatter measured accuracy relative to fully human-authored
questions. The human verification pass mitigates wrong answers, not this
selection effect.

Final distribution: 16 single_hop, 23 multi_hop_2, 17 multi_hop_3,
12 aggregation, 12 out_of_scope. Heavier on multi-hop than the original
targets, deliberately: multi-hop is what this project measures.

## Schema (one object per question in questions.json)

```json
{
  "id": "q001",
  "category": "multi_hop_2",
  "question": "Which companies in the corpus share an audit office with Exelixis?",
  "answer": "None. E&Y audits Exelixis from San Mateo and Halozyme from San Diego. Other companies verified individually.",
  "ontology_path": "Company -AUDITED_BY{office}-> Company <-AUDITED_BY{office}- Company",
  "evidence": [
    {
      "ticker": "EXEL",
      "form": "10-K",
      "date_filed": "2026-02-10",
      "quote": "Ernst & Young LLP ... San Mateo, California"
    },
    {
      "ticker": "HALO",
      "form": "10-K",
      "date_filed": "2026-02-17",
      "quote": "Ernst & Young LLP ... San Diego, California"
    }
  ]
}
```

## Field rules

- `category`: single_hop | multi_hop_2 | multi_hop_3 | aggregation | out_of_scope
- Hop counts are SEMANTIC (DECISIONS.md #4): conceptual joins, not physical
  edges through Agreement/LegalCase nodes.
- `answer`: hand-verified against filing text. Not from sweeps, not from
  memory, not from the web.
- `evidence`: at least one quote per fact the answer depends on, from the
  actual filing in data/text/. For multi-hop questions, one entry per hop.
- `ontology_path`: required for multi_hop_2 / multi_hop_3 / aggregation.
  If a question cannot be written as a path through ontology.md's types,
  stop: it is either a question bug or an ontology bug. Surface it before
  writing more questions.
- `out_of_scope` questions need `answer` set to why the system should
  refuse, and no ontology_path.

## Targets

60 to 80 questions: ~15 single_hop, ~20 multi_hop_2, ~15 multi_hop_3,
~10 aggregation, ~10 out_of_scope.

## Process

Fact-first: find a verified fact chain in the filings, then write the
question whose answer it is. Batches of 12 to 15 per session, hard stop.
