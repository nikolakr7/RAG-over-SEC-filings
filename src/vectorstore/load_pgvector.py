"""Create the chunks table in Postgres and load chunks + embeddings.

Schema per the approved Phase 2 design: chunk metadata columns for
filtered retrieval, text_sha256 as the DECISIONS #32 integrity column,
and a vector(1536) embedding. The HNSW index is deliberately NOT built
here; index construction and tuning (M, ef_construction, ef_search) is
its own step with its own measurements.

Idempotent: the table is created if absent and the load is a full
replace (TRUNCATE + COPY), so re-running after a chunker-accepted change
cannot leave a half-updated store.

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

        n = conn.execute("SELECT count(*) FROM chunks").fetchone()[0]
        by_form = conn.execute(
            "SELECT form, count(*) FROM chunks GROUP BY form ORDER BY count(*) DESC"
        ).fetchall()
        print(f"loaded {n} rows")
        print("by form:", by_form)


if __name__ == "__main__":
    main()
