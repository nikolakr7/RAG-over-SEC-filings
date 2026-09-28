# Hybrid knowledge-graph + vector RAG over biotech SEC filings

**Status: complete (September 2026).**

Question answering over 152 SEC filings (10-K, 10-Q, 8-K, DEF 14A) from
eight mid-cap biotechs (EXEL, HALO, SRPT, ALKS, IONS, RARE, ARWR, NBIX),
comparing plain vector retrieval against a hybrid that adds a knowledge
graph extracted from the same filings. Scored on a frozen, hand-verified
80-question benchmark built before any system existed.

**Headline results** (in-scope pass rate, 68 questions):

- Vector top-10: **0.29**. Adding an LLM reranker over the top 100:
  **0.47**. Adding the knowledge graph: **0.50-0.53**. Rerank and hybrid
  both beat vector-only decisively (paired sign tests, p = 0.01 and
  p <= 0.001).
- The graph's gain over the reranker alone is **not established** at
  this sample size: two runs with identical inputs flip about 15% of
  verdicts. It is clearest on aggregation questions (0.55 -> 0.73).
- Out-of-scope questions are refused 12/12, and 99-100% of cited chunk
  IDs are real and were in the answerer's context.
- Multi-hop questions remain the open problem (roughly 30-45% pass).

**Stack:** Python 3.13, Postgres 17 + pgvector (HNSW), Neo4j 5, Azure
OpenAI (a GPT-5-class chat deployment for extraction, reranking,
answering and judging; text-embedding-3-small), Docker Compose.

## Architecture

```
filings -> parse -> chunk (17,311 chunks, ~400 tokens, IDs {accession}#{seq})
   |                     |
   |                     +-> embed (text-embedding-3-small) -> Postgres/pgvector, HNSW index
   |
   +-> LLM extraction against ontology.md (10 entity types, 16 edge types)
          -> validate -> entity resolution -> Neo4j (3.3k nodes, 7.7k edges,
             every edge carries its source chunk IDs)

question -> vector top-100 -> LLM rerank to 10 chunks --------------+
         -> LLM entity linking -> Cypher neighbourhood expansion     |
            (through reified Agreement/LegalCase/Payment nodes,     +-> answer with
             shared people, and shared companies such as a common   |   chunk-ID citations
             auditor) -> facts ranked by similarity ----------------+
         -> (optional) split into sub-questions, answer each, combine
```

Key design decisions, each with rejected alternatives, are in
[DECISIONS.md](DECISIONS.md) (37 entries); the graph schema is
[ontology.md](ontology.md).

## Benchmark

[benchmark/questions.json](benchmark/questions.json): 80 questions (20
single-hop, 21 two-hop, 16 three-hop, 11 aggregation, 12 out-of-scope),
LLM-drafted and hand-verified quote by quote against the filings, frozen
before any system was built. Questions were deliberately phrased without
the filings' exact wording (DECISIONS #14), so lexical overlap does not
flatter vector retrieval. Methodology and known biases:
[benchmark/README.md](benchmark/README.md).

Grading ([src/eval/judge.py](src/eval/judge.py)): an LLM judge, binary
pass/fail per question against a `required_core` pass bar; extra correct
information is not penalized, contradiction fails, and out-of-scope
questions pass only on a refusal. Spot-check files of 10 stratified
verdicts per run are in `data/runs/*.spotcheck.md`.

## Results

In-scope pass rate (68 questions) and out-of-scope refusals (12):

| | single-hop | 2-hop | 3-hop | aggregation | **in-scope** | refusals |
|---|---|---|---|---|---|---|
| Vector top-10 | 0.60 | 0.14 | 0.12 | 0.27 | **0.29** | 12/12 |
| Vector top-100, LLM rerank to 10 | 0.75 | 0.24 | 0.38 | 0.55 | **0.47** | 11/12 |
| Hybrid (graph + rerank), run 1 | 0.70 | 0.33 | 0.44 | 0.73 | **0.53** | 12/12 |
| Hybrid (graph + rerank), run 2 | 0.80 | 0.24 | 0.31 | 0.73 | **0.50** | 12/12 |
| Hybrid + question splitting + shared-company hop (1 run) | 0.75 | 0.38 | 0.38 | 0.64 | **0.53** | 12/12 |

Paired sign tests over the 80 questions:

- Rerank beats vector: 14 wins vs 3 losses (p = 0.01).
- Hybrid beats vector: 16-17 wins vs 1-2 losses (p <= 0.001).
- Hybrid vs rerank alone: 8 wins vs 3-5 losses (p = 0.2-0.6), **not
  established**. Two hybrid runs given identical chunks flipped 12 of 80
  verdicts, so answer-generation noise is about +-3 questions per run;
  the graph's gain over a strong reranker is suggestive (largest on
  aggregation) but within that noise at n = 68.

Citations: every answer in every variant cites chunk IDs; 99-100% of
cited IDs exist and were in the answerer's context
([src/eval/citations.py](src/eval/citations.py)).

### What the numbers say

1. **Vector retrieval's problem is ranking, not coverage.** The chunk
   holding the answer is in the top 10 for 57% of questions but the top
   100 for 90% (`src/vectorstore/retrieval_recall.py`). Cross-year
   duplicate passages take ~2 of 10 slots but collapsing them gains only
   2 points. A reranker over a wide net is the single biggest win.
2. **The HNSW index costs nothing measurable.** Index recall@10 vs the
   exact scan is 0.97-0.99 across builds, at ~2 ms vs 81 ms, and it never
   lost a benchmark evidence chunk the exact scan found (DECISIONS #34).
3. **The graph helps where facts are spread across filings** (aggregation
   0.55 -> 0.73 in both hybrid runs; peer groups, royalty counterparties),
   but multi-hop questions stay hard. Two answer-side and retrieval-side
   fixes were tested on the 37 multi-hop questions, two runs each with
   the same reranked chunks (`hybrid.py --mode decomp`):

   | multi-hop passes (of 37) | run 1 | run 2 | pass in both |
   |---|---|---|---|
   | hybrid | 14 | 10 | 8 |
   | + split into sub-questions, graph facts as evidence | 12 | 15 | 11 |
   | + hop through shared companies (auditor, peer group, royalty buyer, parent) | 14 | 16 | 12 |

   A consistent upward trend (per question over both runs: 9 better, 4
   worse, p = 0.27), not established, and the overall in-scope rate is
   unchanged at 0.53 because single-hop and aggregation moved within
   noise. What still fails: extraction errors in the graph (Ultragenyx's
   auditor start year recorded as the 2026 report year instead of 2012,
   q022) and required details that never reach the answerer.

## Cost

Azure OpenAI tokens: corpus embedding 6.5M ($0.13); graph extraction
17.1M in / 3.3M out (the largest item); benchmark answering 0.3M
(vector), 3.0M (rerank), 3.9M + 1.0M (hybrid runs, the second reusing
run 1's reranked chunks), about 3.8M for the multi-hop experiments, plus
LLM judging. All outputs are cached per chunk, batch or question, so
re-scoring never re-bills.

## Reproduce

Prerequisites: Python 3.13, Docker, an Azure OpenAI resource with a chat
deployment and a text-embedding-3-small deployment.

```bash
python -m venv .venv && .venv/Scripts/activate   # source .venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env.example .env                        # fill in SEC_USER_AGENT and the Azure values
docker compose up -d                        # Postgres+pgvector (5432), Neo4j (7474/7687)

python src/ingest/download.py               # ~150 filings from EDGAR into data/raw
python src/ingest/parse.py                  # -> data/text
python src/chunking/chunk_corpus.py         # -> data/chunks/chunks.jsonl
python src/vectorstore/embed_corpus.py      # -> data/chunks/embeddings.npy
python src/vectorstore/load_pgvector.py     # table + HNSW index

python src/rag/pipeline.py vector           # baseline answers
python src/rag/pipeline.py rerank
python src/run_graph_and_score.py           # extract, resolve, load Neo4j, hybrid, judge, citations
python src/rag/hybrid.py --mode decomp --reuse-chunks hybrid --name decomp   # best multi-hop config
python src/eval/judge.py vector rerank hybrid decomp
```

`data/` is gitignored and fully regenerated by these steps. Extraction
needs a chat deployment with a few hundred thousand tokens per minute to
finish in about an hour; `src/rag/pipeline.py` throttles to the
deployment's reported limit. Diagnostics: `src/vectorstore/hnsw_sweep.py`
(index tuning) and `src/vectorstore/retrieval_recall.py` (does the gold
evidence chunk get retrieved).

## Repository layout

```
benchmark/            questions.json (frozen v1) and its methodology README
ontology.md           graph schema: 10 entity types, 16 relationship types
DECISIONS.md          37 design decisions with rejected alternatives
src/ingest/           EDGAR download and HTML-to-text parsing
src/chunking/         structure-aware chunker (frozen; chunk IDs are provenance keys)
src/vectorstore/      embedding, pgvector load + HNSW, index and retrieval diagnostics
src/graph/            LLM extraction, entity resolution, Neo4j loader
src/rag/              pipeline.py (vector, rerank), hybrid.py (graph + chunks)
src/eval/             judge.py (LLM grader), citations.py (citation validator)
src/primers/          embedding-similarity exercises from the learning phase
docs/                 per-company filing sweeps used to draft the benchmark
```

## Limitations

- One benchmark of 80 questions; differences under ~5 questions between
  single runs are noise (see above). Repeated runs would tighten this.
- The judge is an LLM; it was spot-checked, not formally calibrated
  against a hand-graded set.
- Entity resolution is rule-based and conservative: it prefers a missed
  merge (a lost hop) over a wrong one (an invented fact). Two deals of the
  same type between the same parties merge into one node.
- The graph keeps every dated claim; resolving "former vs current" is
  left to the answerer, which uses filing dates and effective dates
  (DECISIONS #24).
- The graph inherits extraction errors (e.g. an auditor start year
  recorded as the report year); nothing re-verifies extracted facts
  against their source chunk.

## What I would do next

1. **Settle the graph's value with repeated runs**: three or more runs
   per variant to shrink the noise band below the gap being measured.
2. **Verify extracted facts**: a second LLM pass that checks each edge
   against its source chunk, targeting dates and amounts, where the
   known extraction errors are.
3. **Hand-calibrate the judge** on ~20 answers and report agreement.
4. **Graph-first answering for aggregation**: the graph already holds
   the complete set for questions like "which companies owe royalties to
   Royalty Pharma entities"; a Cypher template for set-valued questions
   could answer them exactly instead of via the LLM.
