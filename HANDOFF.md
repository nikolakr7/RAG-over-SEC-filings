# Session handoff

Read this first in any new session. It is the state of the project as of
the last session, written so a fresh Claude session can continue without
re-explanation. Update it at the end of each session.

## What this project is

A hybrid knowledge-graph + vector RAG system over SEC filings (10-K, 10-Q,
8-K, DEF 14A) from 8 mid-cap biotechs (EXEL, HALO, SRPT, ALKS, IONS, RARE,
ARWR, NBIX). Portfolio project whose primary goal is the USER LEARNING THE
SKILLS AND INDUSTRY/HIREABILITY RELEVANCE, not just shipping. Full plan and phase definitions:
`C:\Users\nkrai\.claude\plans\ok-to-be-clear-jaunty-flame.md`
(phases 0-6; no timeline; ~15 hrs/week; phases gated by done-criteria).

Stack: Python, Postgres+pgvector and Neo4j (local Docker), Azure OpenAI
(gpt-5.6-terra-1 chat deployment, text-embedding-3-small; both working,
config in .env), FastAPI later. Repo: github.com/nikolakr7/baswe-1 (private).

## How we work (also saved in Claude's persistent memory)

- Tutor mode by default: user types the six write-it-yourself zones
  (ontology, benchmark questions, entity resolution, Cypher templates,
  citation validator, eval harness). Claude writes infrastructure.
- Predict-then-check; user keeps notes in a Google Doc (NOTES.md is a stub).
- Cost discipline: Sonnet/Opus subagents only, hard tool budgets, batches
  of 3-5, cost estimate stated before any fan-out. (A 30-agent Fable
  fan-out once exhausted the user's token limit.)
- Never restructure a file the user is actively editing.
- No em dashes in any writing.

## Where we are: Phase 1 COMPLETE. Benchmark v1 FROZEN 2026-08-18.

DONE:
- Phase 0 complete (databases, SQL/Cypher primers, corpus, Azure).
- Corpus: 152 filings / 173 files parsed to data/text/ (gitignored, 30 MB).
- ontology.md v1 FROZEN (2026-08-18): 10 entity types, 16 relationship
  types. Grown during verification as live sanity-check findings:
  PEER_OF (#19); Payment node + PAID_UNDER, AFFILIATE_OF,
  signing_date/effective_date on Agreement, patents[] on LegalCase,
  stock_purchase and credit_facility types (#25-#30). Changes from here
  need a DECISIONS entry and create v2.
- benchmark/questions.json v1 FROZEN: all 80 verified: true, hand-checked
  by the user quote-by-quote against primary filings. 47 of 68 in-scope
  questions carry required_core. Every ontology_path follows DECISIONS
  #23 (directed edges, roles, types, canonical shared instance names;
  #23(g) count-form for aggregation). Pre-freeze passes: all quotes
  re-located verbatim, all path terms and directions machine-audited,
  cross-question consistency read over every recurring fact family.
  Per-question repair log: benchmark/drafts/precheck-q030-q068.md.
- DECISIONS.md: 30 logged decisions with rejected alternatives. Read it.
  #17 (required_core grading), #23 (path notation), #24 (truth as of the
  corpus end, August 2026) matter most for Phase 2.
- docs/sweeps/: machine sweep notes over all 152 filings plus
  cross-company-index.md (leads only, never citable evidence).
- Methodology and provenance disclosed in benchmark/README.md.

Verification rules established (see DECISIONS #15-22):
- answer scope == question scope; trim answer or widen question
- every answer claim needs a quote; quotes must carry subject identity
  (not start mid-"we"); provenance claims are supported by evidence
  metadata; absence claims verified by negative search + positive control
- open questions get a `required_core` field (pass bar); default is
  all-required; judge grades against core when present
- ontology_path: validity not exhaustiveness; only ontology.md terms;
  properties (role/dates/territory) included when the question hinges on them
- watch for answers orphaned by the rephrase pass (answer fits the OLD
  question; originals are in benchmark/drafts/) and for deal values:
  never add upfront to milestones, state them separately with "up to"
- comparison questions: both halves report the same fields

Grading design (agreed, to be built in Phase 2 eval harness): claim-level,
binary pass/fail per question; extra correct info unpenalized;
contradiction fails; out-of-scope passes only on refusal; LLM judge
calibrated against ~20 hand-graded samples.

## Next steps, in order

Phase 2 begins:
1. Embeddings primer (tutor mode).
2. Chunking with stable chunk IDs; strip the old-format XBRL junk at the
   top of parsed .txt files first (see open items).
3. pgvector + HNSW index; embed the corpus.
4. Eval harness (USER-WRITTEN zone): claim-level binary judge per the
   agreed grading design below, calibrated against ~20 hand-graded
   samples; benchmark is frozen input, never edited by the harness.
5. Vector-only baseline scored against benchmark v1.

## Known open items

- NOTES.md in repo is empty (user keeps notes in Google Doc; consider a
  snapshot before phase end).
- Old-format XBRL junk at the top of parsed .txt files: strip before
  chunking in Phase 2 (noted for DECISIONS).
- Sarepta Therapeutics Investments Inc. absent from every SRPT Exhibit 21
  (a real-world gap, not a downloader bug).
- Corpus quirks worth remembering for entity resolution: three distinct
  "Merck" entities; two Takeda legal entities plus Baxalta; Akcea as Ionis
  subsidiary co-party; "Bristol Myers Squib" misspelling in HALO proxy;
  RPI Finance Trust and Royalty Pharma Investments 2019 ICAV as Royalty
  Pharma vehicles.
