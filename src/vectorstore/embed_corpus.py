"""Embed every chunk in data/chunks/chunks.jsonl with text-embedding-3-small.

Writes data/chunks/embeddings.npy: float32, shape (n_chunks, 1536), where
row i is the chunk on line i of chunks.jsonl. Kept on disk deliberately so
pgvector schema iterations never re-spend the API cost (~$0.13 for the
full corpus).

Checkpoints every CHECKPOINT batches to data/chunks/embeddings.part.npy so
an interrupted run (rate limit, network) resumes instead of re-billing.

Run:
    python src/vectorstore/embed_corpus.py
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI

BATCH = 128
CHECKPOINT = 20  # save partial progress every N batches
DIM = 1536

CHUNKS = Path("data/chunks/chunks.jsonl")
OUT = Path("data/chunks/embeddings.npy")
PART = Path("data/chunks/embeddings.part.npy")


def main() -> None:
    load_dotenv()
    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
    client = OpenAI(
        base_url=f"{endpoint}/openai/v1/",
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
    )
    deployment = os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"]

    records = [json.loads(line) for line in CHUNKS.open(encoding="utf-8")]
    texts = [r["text"] for r in records]
    n = len(texts)

    vectors = np.zeros((n, DIM), dtype=np.float32)
    start = 0
    if PART.exists():
        partial = np.load(PART)
        # resume only if the partial file matches the current corpus shape;
        # a frozen chunker means this should always hold
        if partial.shape == (n, DIM):
            done_rows = int((np.abs(partial).sum(axis=1) > 0).sum())
            vectors = partial
            start = done_rows - (done_rows % BATCH)  # redo any half-saved batch
            print(f"resuming from checkpoint at row {start}")

    billed = 0
    t0 = time.time()
    for b, lo in enumerate(range(start, n, BATCH)):
        hi = min(lo + BATCH, n)
        for attempt in range(6):
            try:
                resp = client.embeddings.create(model=deployment, input=texts[lo:hi])
                break
            except Exception as e:  # rate limit / transient network
                wait = 2 ** attempt
                print(f"  batch {lo}-{hi} failed ({type(e).__name__}); retrying in {wait}s")
                time.sleep(wait)
        else:
            raise RuntimeError(f"batch {lo}-{hi} failed after retries")
        data = sorted(resp.data, key=lambda item: item.index)
        vectors[lo:hi] = np.array([d.embedding for d in data], dtype=np.float32)
        billed += resp.usage.total_tokens
        if (b + 1) % CHECKPOINT == 0:
            np.save(PART, vectors)
            rate = (hi - start) / max(time.time() - t0, 1e-9)
            print(f"{hi}/{n} rows  ({billed:,} tokens billed so far, {rate:.0f} rows/s)")

    np.save(OUT, vectors)
    PART.unlink(missing_ok=True)

    norms = np.linalg.norm(vectors, axis=1)
    print(f"\ndone: {n} vectors -> {OUT}")
    print(f"tokens billed: {billed:,}  (~${billed / 1e6 * 0.02:.4f} at $0.02/1M)")
    print(f"norms: min {norms.min():.6f}  max {norms.max():.6f}  zero-rows {(norms == 0).sum()}")


if __name__ == "__main__":
    main()
