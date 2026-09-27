"""Measure HNSW index recall and latency against the exact scan.

Index recall, not retrieval recall: the question here is "did the index
return what the exact scan would have returned?", so ground truth is the
exact top-K computed in numpy from data/chunks/embeddings.npy. Whether
those chunks contain the benchmark evidence is a separate measurement
(retrieval recall, next step).

Queries are the 80 benchmark questions, embedded once and cached at
data/chunks/question_embeddings.npy (~2k tokens, a fraction of a cent).
Using them is label-free: only the question text is embedded, never the
answers or evidence, and the only thing tuned is agreement with the exact
scan.

Recall is tie-aware. 1,638 chunks share a byte-identical vector with at
least one other chunk (boilerplate repeated across filings), so the exact
top-K can have several equally valid members at rank K. A returned chunk
counts as a hit if its exact distance is no worse than the exact K-th
distance (+TIE_EPS). Strict ID-match recall is reported alongside.

Plan: exact-scan baseline first (no index), then for each (M,
ef_construction) build, rebuild the index and sweep ef_search. Builds are
the expensive axis, ef_search is a session setting (see HANDOFF). The last
build in BUILDS is left in place.

Run (postgres container up):
    python src/vectorstore/hnsw_sweep.py
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np
import psycopg
from dotenv import load_dotenv
from openai import OpenAI
from pgvector.psycopg import register_vector

DSN = "host=localhost port=5432 dbname=kgrag user=kgrag password=localdev"

CHUNKS = Path("data/chunks/chunks.jsonl")
EMB = Path("data/chunks/embeddings.npy")
QUESTIONS = Path("benchmark/questions.json")
QEMB = Path("data/chunks/question_embeddings.npy")
OUT = Path("data/hnsw_sweep.json")

K = 10
BUILDS = [(8, 32), (32, 128), (16, 64)]  # (M, ef_construction); (16, 64) is pgvector's default, built last so it stays
EF_SEARCH = [10, 20, 40, 80, 160, 320]
TIE_EPS = 1e-5
INDEX = "chunks_embedding_hnsw"

QUERY = "SELECT chunk_id FROM chunks ORDER BY embedding <=> %(q)s LIMIT %(k)s"


def embed_questions(texts: list[str]) -> np.ndarray:
    if QEMB.exists():
        cached = np.load(QEMB)
        if cached.shape == (len(texts), 1536):
            return cached
    load_dotenv()
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
    client = OpenAI(base_url=f"{endpoint}/openai/v1/", api_key=os.environ["AZURE_OPENAI_API_KEY"])
    resp = client.embeddings.create(model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"], input=texts)
    vecs = np.array([d.embedding for d in sorted(resp.data, key=lambda d: d.index)], dtype=np.float32)
    np.save(QEMB, vecs)
    print(f"embedded {len(texts)} questions ({resp.usage.total_tokens:,} tokens billed)")
    return vecs


def exact_distances(Q: np.ndarray, X: np.ndarray) -> np.ndarray:
    """Cosine distance from every query to every chunk, shape (n_queries, n_chunks)."""
    Qn = Q / np.linalg.norm(Q, axis=1, keepdims=True)
    Xn = X / np.linalg.norm(X, axis=1, keepdims=True)
    return 1.0 - (Qn.astype(np.float64) @ Xn.astype(np.float64).T)


def recall(returned: list[list[str]], dist: np.ndarray, row_of: dict[str, int]) -> tuple[float, float]:
    """(tie-aware recall@K, strict ID recall@K), averaged over queries."""
    tie_hits = strict_hits = 0
    for i, ids in enumerate(returned):
        order = np.argsort(dist[i], kind="stable")
        kth = dist[i, order[K - 1]]
        truth = {j for j in order[:K]}
        rows = [row_of[c] for c in ids]
        tie_hits += min(sum(dist[i, r] <= kth + TIE_EPS for r in rows), K)
        strict_hits += sum(r in truth for r in rows)
    n = len(returned) * K
    return tie_hits / n, strict_hits / n


def run_queries(conn: psycopg.Connection, Q: np.ndarray) -> tuple[list[list[str]], list[float]]:
    returned, ms = [], []
    for q in Q:
        t = time.perf_counter()
        rows = conn.execute(QUERY, {"q": q, "k": K}).fetchall()
        ms.append((time.perf_counter() - t) * 1000)
        returned.append([r[0] for r in rows])
    return returned, ms


def summarize(label: str, returned, ms, dist, row_of, extra: dict) -> dict:
    tie_r, strict_r = recall(returned, dist, row_of)
    short = sum(len(r) < K for r in returned)
    row = {
        "config": label, **extra,
        "recall_at_10": round(tie_r, 4), "strict_id_recall_at_10": round(strict_r, 4),
        "p50_ms": round(float(np.percentile(ms, 50)), 2), "p95_ms": round(float(np.percentile(ms, 95)), 2),
        "queries_short_of_k": short,
    }
    print(f"{label:<28} recall@10 {tie_r:.4f} (strict {strict_r:.4f})  "
          f"p50 {row['p50_ms']:>7.2f} ms  p95 {row['p95_ms']:>7.2f} ms"
          + (f"  [{short} queries returned < {K}]" if short else ""))
    return row


def main() -> None:
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    Q = embed_questions([q["question"] for q in questions])
    X = np.load(EMB)
    chunk_ids = [json.loads(line)["chunk_id"] for line in CHUNKS.open(encoding="utf-8")]
    assert X.shape[0] == len(chunk_ids)
    row_of = {c: i for i, c in enumerate(chunk_ids)}
    dist = exact_distances(Q, X)

    srt = np.sort(dist, axis=1)
    boundary_ties = int((srt[:, K] <= srt[:, K - 1] + TIE_EPS).sum())
    print(f"{len(Q)} queries, {len(chunk_ids)} chunks; {boundary_ties} queries have a tie at rank {K}\n")

    results = []
    with psycopg.connect(DSN, autocommit=True) as conn:
        register_vector(conn)
        conn.execute("SET max_parallel_workers_per_gather = 0")  # single core, same as the hand-timed scan
        conn.execute(f"DROP INDEX IF EXISTS {INDEX}")

        # Baseline: exact scan through SQL. Also a self-check: its recall
        # against the numpy ground truth must be 1.0, or the two disagree
        # about distances and every number below is suspect.
        run_queries(conn, Q)  # warm the cache
        returned, ms = run_queries(conn, Q)
        base = summarize("exact scan (no index)", returned, ms, dist, row_of, {"kind": "exact"})
        assert base["recall_at_10"] == 1.0, "SQL exact scan disagrees with numpy ground truth"
        results.append(base)

        conn.execute("SET maintenance_work_mem = '1GB'")  # the index holds a copy of every vector
        # A parallel build puts that memory in /dev/shm, which Docker caps
        # at 64 MB by default ("could not resize shared memory segment").
        # Serial builds use ordinary memory; seconds at this corpus size.
        conn.execute("SET max_parallel_maintenance_workers = 0")
        for m, efc in BUILDS:
            print()
            conn.execute(f"DROP INDEX IF EXISTS {INDEX}")
            t = time.perf_counter()
            conn.execute(
                f"CREATE INDEX {INDEX} ON chunks USING hnsw (embedding vector_cosine_ops) "
                f"WITH (m = {m}, ef_construction = {efc})"
            )
            build_s = time.perf_counter() - t
            size_mb = conn.execute(f"SELECT pg_relation_size('{INDEX}')").fetchone()[0] / 2**20
            print(f"built M={m} ef_construction={efc} in {build_s:.1f} s, index {size_mb:.0f} MB")

            for ef in EF_SEARCH:
                conn.execute(f"SET hnsw.ef_search = {ef}")
                # The planner costs the index scan up with ef_search and
                # silently switches to the seq scan when it looks cheaper:
                # recall 1.0 at exact-scan latency, which reads as a great
                # index. Force the index here and check the plan at every ef.
                conn.execute("SET enable_seqscan = off")
                plan = [r[0] for r in conn.execute("EXPLAIN " + QUERY, {"q": Q[0], "k": K})]
                assert any(INDEX in line for line in plan), (
                    "index not used: " + " | ".join(line.split("(")[0].strip() for line in plan)
                )
                run_queries(conn, Q)  # warm
                returned, ms = run_queries(conn, Q)
                results.append(summarize(
                    f"M={m} efc={efc} ef_search={ef}", returned, ms, dist, row_of,
                    {"kind": "hnsw", "m": m, "ef_construction": efc, "ef_search": ef,
                     "build_s": round(build_s, 1), "index_mb": round(size_mb, 1)},
                ))

    OUT.write_text(json.dumps(results, indent=1), encoding="utf-8")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
