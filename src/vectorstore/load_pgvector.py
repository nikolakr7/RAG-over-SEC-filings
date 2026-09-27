"""Create the chunks table in Postgres and load chunks + embeddings.

Schema per the approved Phase 2 design: chunk metadata columns for
filtered retrieval, text_sha256 as the DECISIONS #32 integrity column,
and a vector(1536) embedding, then the HNSW index chosen by the sweep in
hnsw_sweep.py (DECISIONS #34): M=16, ef_construction=64, with
hnsw.ef_search=80 set as the database default so every new connection
gets it.

Idempotent: the table is created if absent and the load is a full
replace (TRUNCATE + COPY), so re-running after a chunker-accepted change
cannot leave a half-updated store. The index is dropped before the COPY and
built after it: one bulk build instead of 17k incremental inserts.

Run (postgres container up: docker compose up -d postgres):
    python src/vectorstore/load_pgvector.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import psycopg
from pgvector.psycopg import register_vector

DSN = "host=localhost port=5432 dbname=kgrag user=kgrag password=localdev"

# DECISIONS #34. ef_search=80 is also the highest value at which the
# planner still chose the index over a seq scan on this corpus; above it
# queries silently fall back to the exact scan. Re-check the plan if the
# corpus or these parameters change.
INDEX = "chunks_embedding_hnsw"
HNSW_M = 16
HNSW_EF_CONSTRUCTION = 64
HNSW_EF_SEARCH = 80

CHUNKS = Path("data/chunks/chunks.jsonl")
EMB = Path("data/chunks/embeddings.npy")

SCHEMA = """
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS chunks (
    chunk_id     text PRIMARY KEY,
    accession    text NOT NULL,
    ticker       text NOT NULL,
    form         text NOT NULL,
    date_filed   date NOT NULL,
    source_file  text NOT NULL,
    seq          int  NOT NULL,
    n_tokens     int  NOT NULL,
    text_sha256  text NOT NULL,
    text         text NOT NULL,
    embedding    vector(1536) NOT NULL
);
"""


def main() -> None:
    records = [json.loads(line) for line in CHUNKS.open(encoding="utf-8")]
    vectors = np.load(EMB)
    assert vectors.shape == (len(records), 1536), (
        f"embeddings {vectors.shape} do not match {len(records)} chunks -- "
        "re-run embed_corpus.py against the current chunks.jsonl"
    )

    # Integrity check before anything touches the database (DECISIONS #32):
    # the stored hashes must match the text we are about to load.
    for r in records[:: max(len(records) // 500, 1)]:  # sampled, ~500 checks
        assert hashlib.sha256(r["text"].encode("utf-8")).hexdigest() == r["text_sha256"], (
            f"text drift detected at {r['chunk_id']}"
        )

    with psycopg.connect(DSN) as conn:
        conn.execute(SCHEMA)
        register_vector(conn)
        conn.execute(f"DROP INDEX IF EXISTS {INDEX}")
        conn.execute("TRUNCATE chunks")
        with conn.cursor() as cur:
            with cur.copy(
                "COPY chunks (chunk_id, accession, ticker, form, date_filed, "
                "source_file, seq, n_tokens, text_sha256, text, embedding) FROM STDIN"
            ) as copy:
                for r, vec in zip(records, vectors):
                    copy.write_row((
                        r["chunk_id"], r["accession"], r["ticker"], r["form"],
                        r["date_filed"], r["source_file"], r["seq"],
                        r["n_tokens"], r["text_sha256"], r["text"], vec,
                    ))
        conn.commit()

        # The index holds its own copy of every vector (~128 MB here). A
        # parallel build would put that memory in /dev/shm, which Docker
        # caps at 64 MB, so build serially.
        conn.execute("SET maintenance_work_mem = '1GB'")
        conn.execute("SET max_parallel_maintenance_workers = 0")
        conn.execute(
            f"CREATE INDEX {INDEX} ON chunks USING hnsw (embedding vector_cosine_ops) "
            f"WITH (m = {HNSW_M}, ef_construction = {HNSW_EF_CONSTRUCTION})"
        )
        conn.execute(f"ALTER DATABASE kgrag SET hnsw.ef_search = {HNSW_EF_SEARCH}")
        conn.commit()

        n = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
        by_form = conn.execute(
            "SELECT form, count(*) FROM chunks GROUP BY form ORDER BY count(*) DESC"
        ).fetchall()
        print(f"loaded {n} rows")
        print("by form:", by_form)


if __name__ == "__main__":
    main()
