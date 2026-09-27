"""Vector-only RAG over the chunk store, with an optional LLM rerank.

Variants (the "before" column of the benchmark):
  vector   top-10 chunks by HNSW cosine search -> answer
  rerank   top-100 by HNSW -> the chat model picks the 10 most useful
           -> answer (retrieval recall showed answers sit in the top 100
           for 90% of questions but the top 10 for only 57%)

The answerer sees only the retrieved excerpts, cites chunk IDs in square
brackets, answers as of the corpus end (August 2026, DECISIONS #24), and
replies "REFUSE: <reason>" when the excerpts hold nothing relevant.

Outputs are cached per question in data/runs/<variant>.jsonl; re-runs
skip questions already answered, so a run is paid for once. Delete the
file to re-run a variant on purpose.

Run:
    python src/rag/pipeline.py vector
    python src/rag/pipeline.py rerank
    python src/rag/pipeline.py vector --limit 2      # smoke test
"""

from __future__ import annotations

import argparse
import json
import os
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import psycopg
from dotenv import load_dotenv
from openai import OpenAI
from pgvector.psycopg import register_vector

DSN = "host=localhost port=5432 dbname=kgrag user=kgrag password=localdev"
QUESTIONS = Path("benchmark/questions.json")
QEMB = Path("data/chunks/question_embeddings.npy")
RUNS = Path("data/runs")

K_ANSWER = 10
K_WIDE = 100
WORKERS = 4

ANSWER_INSTRUCTIONS = """\
You answer questions about the SEC filings (10-K, 10-Q, 8-K, DEF 14A) of \
eight biotech companies: Exelixis (EXEL), Halozyme (HALO), Sarepta (SRPT), \
Alkermes (ALKS), Ionis (IONS), Ultragenyx (RARE), Arrowhead (ARWR) and \
Neurocrine (NBIX). Use ONLY the excerpts provided; no outside knowledge.

- Answer directly and concisely. Give the specific names, amounts and \
dates the question asks for.
- Cite the chunk ID of every excerpt you rely on in square brackets right \
after the claim, e.g. [0000939767-26-000021#0221].
- The filings run through August 2026. Answer as of then: if a later \
filing updates an earlier one, or a filing announces a change effective \
on or before August 2026, the change has happened.
- If the excerpts contain nothing that answers the question, or it asks \
about companies or information these filings do not cover, reply with \
"REFUSE:" and one sentence saying why. If they answer only part of it, \
answer that part and say what is missing."""

RERANK_INSTRUCTIONS = """\
You select evidence for a question about SEC filings. From the numbered \
excerpts, choose the ones that most directly contain facts needed to \
answer the question (names, amounts, dates, relationships), not ones \
that are merely on the same topic. Multi-part questions may need \
excerpts from different companies or filings; cover every part. \
Return JSON only: {"ids": ["<chunk id>", ...]} with at most 10 IDs, \
most useful first."""

_local = threading.local()


def client() -> OpenAI:
    if not hasattr(_local, "client"):
        load_dotenv()
        endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
        _local.client = OpenAI(base_url=f"{endpoint}/openai/v1/", api_key=os.environ["AZURE_OPENAI_API_KEY"])
    return _local.client


def conn() -> psycopg.Connection:
    if not hasattr(_local, "conn"):
        _local.conn = psycopg.connect(DSN, autocommit=True)
        register_vector(_local.conn)
    return _local.conn


def llm(instructions: str, text: str) -> tuple[str, dict]:
    """One Responses API call with retry on rate limits and transient errors."""
    load_dotenv()
    for attempt in range(8):
        try:
            r = client().responses.create(
                model=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"], instructions=instructions, input=text,
            )
            return r.output_text, {"in": r.usage.input_tokens, "out": r.usage.output_tokens}
        except Exception as e:  # 429 / 5xx / network
            wait = min(2 ** attempt * 2, 60)
            print(f"  llm error ({type(e).__name__}: {str(e)[:80]}); retry in {wait}s")
            time.sleep(wait)
    raise RuntimeError("llm call failed after retries")


def embed(text: str) -> np.ndarray:
    load_dotenv()
    r = client().embeddings.create(model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"], input=[text])
    return np.array(r.data[0].embedding, dtype=np.float32)


def search(vec: np.ndarray, k: int) -> list[dict]:
    rows = conn().execute(
        "SELECT chunk_id, ticker, form, date_filed, text FROM chunks "
        "ORDER BY embedding <=> %s LIMIT %s", (vec, k),
    ).fetchall()
    return [dict(zip(("chunk_id", "ticker", "form", "date_filed", "text"), r)) for r in rows]


def fmt(chunks: list[dict]) -> str:
    return "\n\n".join(
        f"[{c['chunk_id']}] {c['ticker']} {c['form']} filed {c['date_filed']}\n{c['text']}" for c in chunks
    )


def rerank(question: str, wide: list[dict]) -> tuple[list[dict], dict]:
    text, usage = llm(RERANK_INSTRUCTIONS, f"Question: {question}\n\nExcerpts:\n\n{fmt(wide)}")
    by_id = {c["chunk_id"]: c for c in wide}
    m = re.search(r"\{.*\}", text, re.S)
    try:
        picked = [i for i in json.loads(m.group(0))["ids"] if i in by_id] if m else []
    except (json.JSONDecodeError, KeyError, TypeError):
        picked = []
    picked = list(dict.fromkeys(picked))[:K_ANSWER]
    # pad with vector order if the model returned fewer than K (or garbage)
    for c in wide:
        if len(picked) >= K_ANSWER:
            break
        if c["chunk_id"] not in picked:
            picked.append(c["chunk_id"])
    return [by_id[i] for i in picked], usage


def answer(question: str, vec: np.ndarray | None, variant: str) -> dict:
    vec = embed(question) if vec is None else vec
    usage = {"in": 0, "out": 0}
    if variant == "vector":
        chunks = search(vec, K_ANSWER)
    elif variant == "rerank":
        chunks, u = rerank(question, search(vec, K_WIDE))
        usage = {k: usage[k] + u[k] for k in usage}
    else:
        raise ValueError(variant)
    text, u = llm(ANSWER_INSTRUCTIONS, f"Question: {question}\n\nExcerpts:\n\n{fmt(chunks)}")
    usage = {k: usage[k] + u[k] for k in usage}
    return {"answer": text, "retrieved": [c["chunk_id"] for c in chunks], "usage": usage}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("variant", choices=["vector", "rerank"])
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    qvecs = np.load(QEMB)  # rows follow questions.json order
    RUNS.mkdir(parents=True, exist_ok=True)
    out = RUNS / f"{args.variant}.jsonl"
    done = {json.loads(l)["id"] for l in out.open(encoding="utf-8")} if out.exists() else set()
    todo = [(q, qvecs[i]) for i, q in enumerate(questions) if q["id"] not in done][: args.limit]
    print(f"{args.variant}: {len(done)} cached, {len(todo)} to run")

    lock = threading.Lock()
    tot = {"in": 0, "out": 0}
    with ThreadPoolExecutor(WORKERS) as pool, out.open("a", encoding="utf-8") as f:
        futs = {pool.submit(answer, q["question"], v, args.variant): q for q, v in todo}
        for n, fut in enumerate(as_completed(futs), 1):
            q = futs[fut]
            rec = {"id": q["id"], "category": q["category"], "question": q["question"], **fut.result()}
            with lock:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                tot = {k: tot[k] + rec["usage"][k] for k in tot}
            print(f"  [{n}/{len(todo)}] {q['id']}  {rec['usage']['in']:,} in / {rec['usage']['out']:,} out")
    print(f"tokens this run: {tot['in']:,} in / {tot['out']:,} out")


if __name__ == "__main__":
    main()
