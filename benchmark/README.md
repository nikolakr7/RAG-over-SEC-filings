# Benchmark question set

**FROZEN as of 2026-08-18 (benchmark v1).** All 80 questions are
`verified: true`. From here, questions are never edited, added, or
removed; git history is the witness. This is what makes the Phase 5
numbers a benchmark instead of a demo. If a defect is ever found
post-freeze, it is logged in DECISIONS.md and scored as-is for v1; a fix
would create v2, never silently amend v1.

## Methodology and provenance

This is an **LLM-drafted, human-verified** benchmark. Questions were drafted
by Claude (Sonnet agents) from the corpus in data/text/, with a hard rule
that every evidence quote be located verbatim in primary filing text before
a candidate survived (sweep notes were leads only, never quotable). Drafts
were then deduplicated and balanced to 80.

Verification protocol (completed 2026-08-18): every question shipped with
"verified": false. The human author checked each question against the
quoted filing in data/text/ and flipped the flag only after seeing the
evidence with their own eyes. Verification found and fixed real defects
at a steady rate (wrong-tense answers, under-reported answer sets, one
funding attribution error, quote-hygiene issues); the per-question repair
log is benchmark/drafts/precheck-q030-q068.md, the rules it produced are
DECISIONS.md #15-#30, and the ontology sanity-check (writing every path
strictly against ontology.md) drove the ontology additions in #25-#30.
Before the freeze, three mechanical passes ran over all 80: every
evidence quote re-located verbatim in its named filing, every
ontology_path term and edge direction checked against ontology.md, and a
cross-question consistency read over every recurring fact family.

Known bias, disclosed: an LLM drafted these questions and an LLM (Phase 3)
extracts the graph, so the benchmark may over-represent facts LLMs reliably
notice, which can flatter measured accuracy relative to fully human-authored
questions. The human verification pass mitigates wrong answers, not this
selection effect.

Final distribution: 20 single_hop, 21 multi_hop_2, 16 multi_hop_3,
11 aggregation, 12 out_of_scope.

Evidence-source diversity (added after review flagged latest-10-K
concentration): 12 redundant latest-10-K questions were swapped for
temporal and form-diverse ones. Evidence now spans 10-K (109 quotes),
DEF14A (27), 8-K (12), and 10-Q (11), with quotes from 2024, 2025, and
2026 filings; temporal questions exercise the ontology's status/date
machinery (deal terminations, CEO successions, before/after contrasts,
facts that exist only in quarterlies). One question deliberately captures
two filers dating the same milestone differently (SRPT: Nov 24, 2025 vs
ARWR: Nov 20, 2025).

Post-draft rephrase-and-audit pass (before human verification): questions
rewritten from clue-style phrasing to natural information needs, with the
rule that specificity lives in the answer, not the question; hop labels
re-audited against EVIDENCE DISPERSION (a question is multi-hop only if its
supporting facts live in separate passages; two questions whose facts
co-occur in one proxy-bio paragraph were reclassified to single_hop); four
cross-category near-duplicates cut and replaced with freshly grep-verified
questions; one evidence attribution bug fixed (a Halozyme quote mislabeled
as Ionis).

## Schema (one object per question in questions.json)

```json
{
  "id": "q001",
  "category": "multi_hop_2",
  "question": "Which companies in the corpus share an audit office with Exelixis?",
  "answer": "None. E&Y audits Exelixis from San Mateo and Halozyme from San Diego. Other companies verified individually.",
  "required_core": "None share an office with Exelixis.",
  "ontology_path": "Company(Exelixis) -AUDITED_BY{office: San Mateo, CA}-> Company(Ernst & Young LLP) <-AUDITED_BY{office: San Diego, CA}- Company(Halozyme)",
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
- `required_core` (optional): the pass bar for grading. Present on 47 of
  the 68 in-scope questions, wherever the full answer carries precision
  detail, provenance narration, or background beyond the question's
  literal ask; the judge grades against the core when present and the
  full answer otherwise (all claims required; DECISIONS.md #17). Extra
  correct information is never penalized.
- `evidence`: at least one quote per fact the answer depends on, verbatim
  from the actual filing in data/text/ (ellipses join fragments of one
  passage). For multi-hop questions, one entry per hop.
- `ontology_path`: required for multi_hop_2 / multi_hop_3 / aggregation
  (single_hop carries one too). Notation per DECISIONS.md #23: directed
  edges in domain -> range order, roles on every PARTY_TO, `type` on
  every Agreement, canonical instance names shared across questions, and
  `count(...) where ...` with a bound result set for aggregation. If a
  question cannot be written as a path through ontology.md's types, that
  is a question bug or an ontology gap to surface (#20).
- `out_of_scope` questions need `answer` set to why the system should
  refuse (prefixed REFUSE), and no ontology_path or evidence.

## Targets

60 to 80 questions: ~15 single_hop, ~20 multi_hop_2, ~15 multi_hop_3,
~10 aggregation, ~10 out_of_scope.

## Process

Fact-first: find a verified fact chain in the filings, then write the
question whose answer it is. Batches of 12 to 15 per session, hard stop.
