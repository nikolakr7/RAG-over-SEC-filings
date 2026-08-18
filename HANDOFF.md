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

## Where we are: Phase 1, benchmark verification (last step before freeze)

DONE:
- Phase 0 complete (databases, SQL/Cypher primers, corpus, Azure).
- Corpus: 152 filings / 173 files parsed to data/text/ (gitignored, 30 MB).
- ontology.md v1: 10 entity types, 16 relationship types. Added during
  verification as live sanity-check findings: PEER_OF (#19); then, from
  writing q001-q031 paths strictly against the ontology (2026-08-16):
  Payment node + PAID_UNDER, AFFILIATE_OF, signing_date/effective_date on
  Agreement, patents[] on LegalCase, stock_purchase type (#25-#30).
  Status DRAFT until the benchmark freezes.
- DECISIONS.md: 30 logged decisions with rejected alternatives. Read it.
  #23 (path notation) and #24 (benchmark truth is as of the corpus end,
  August 2026) govern how remaining questions get fixed.
- docs/sweeps/: machine sweep notes over all 152 filings plus
  cross-company-index.md (leads only, never citable evidence).
- benchmark/questions.json: 80 questions (20 single-hop, 21 two-hop, 16
  three-hop, 11 aggregation, 12 out-of-scope), LLM-drafted with grep-
  verified quotes, rephrased to natural questions, temporally diversified.
  Methodology and provenance disclosed in benchmark/README.md.

IN PROGRESS: the user is hand-verifying all 80 questions (flag
`verified: true` only after seeing each quote in the primary file). As of
this handoff q001-q041 and the out-of-scope set q069-q080 are verified:
true (53 of 80); q042-q068 (27 questions: the multi_hop_3 and aggregation
sets) remain, and the user is going in order. The verified set q001-q029
was re-checked and repaired on 2026-08-16 (quote hygiene, one wrong path
counterparty, temporal wording per DECISIONS #24, all paths normalized
per #23). Verification is finding real defects at a steady rate, which is
the process working. Rules are logged in DECISIONS #15-30 and the README.

Pre-check worksheet for the remaining 39: benchmark/drafts/
precheck-q030-q068.md (written 2026-08-16 by Claude; not verification,
an aid). All 113 quotes were located mechanically (file:line refs are in
the worksheet) and all ontology_path terms checked against ontology.md.
Content findings: 4 HIGH (q033 Takeda deals under-reported: NBIX and
ARWR also have direct Takeda deals; q036 original osavampator territory
misstated; q041 Soleno funding was cash on hand plus securities sales per
the 10-Q, not the revolver; q066 the same 10-K names seven CABOMETYX
challengers, not four), 10 MEDIUM (scope/tense/provenance), the rest LOW
or OK. Near-duplicate pairs still present: q030/q050, q022/q056.

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

1. Finish verifying q030-q068 (user drives, with the pre-check worksheet
   open alongside; Claude answers questions, greps on request, never
   edits questions.json without being asked). Log accepted fixes in
   DECISIONS.md / README as before.
2. Ontology sanity check: every multi-hop question expressible through the
   14 types (mostly done implicitly during verification).
3. Freeze: all 80 verified:true, commit "Freeze benchmark v1", flip
   ontology.md status from DRAFT to FROZEN.
4. Phase 2 begins: embeddings primer, chunking with stable chunk IDs,
   pgvector + HNSW, eval harness (user-written), vector baseline scored.

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
