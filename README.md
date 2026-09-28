# Hybrid knowledge-graph + vector RAG over biotech SEC filings

Question answering over 152 SEC filings (10-K, 10-Q, 8-K, DEF 14A) from
eight mid-cap biotechs (EXEL, HALO, SRPT, ALKS, IONS, RARE, ARWR, NBIX),
comparing plain vector retrieval against a hybrid that adds a knowledge
graph extracted from the same filings. Scored on a frozen, hand-verified
80-question benchmark.

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
            (through reified Agreement/LegalCase/Payment nodes      +-> answer with
             and shared people) -> facts ranked by similarity ------+    chunk-ID citations
```

Key design decisions, each with rejected alternatives, are in
[DECISIONS.md](DECISIONS.md) (36 entries); the graph schema is
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
   but multi-hop questions stay hard: most remaining failures are an
   answerer declining or omitting half of a two-part answer even when the
   needed facts are in context.

## Cost

Azure OpenAI tokens: corpus embedding 6.5M ($0.13); graph extraction
17.1M in / 3.3M out; benchmark runs 0.3M (vector), 3.0M (rerank), 3.9M +
1.0M (hybrid runs, the second reusing run 1's reranked chunks). All
outputs are cached per chunk, batch, or question, so re-scoring never
re-bills.

## Reproduce

```bash
docker compose up -d                        # Postgres+pgvector, Neo4j
python src/chunking/chunk_corpus.py         # needs data/text from src/ingest
python src/vectorstore/embed_corpus.py
python src/vectorstore/load_pgvector.py     # table + HNSW index
python src/rag/pipeline.py vector
python src/rag/pipeline.py rerank
python src/run_graph_and_score.py           # extract, resolve, load, hybrid, judge, citations
```

Azure settings go in `.env` (see `.env.example`). The chat deployment
needs a few hundred thousand tokens per minute for extraction to finish
in about an hour; `src/rag/pipeline.py` throttles to the deployment's
reported limit.

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
