"""Retrieval recall: do benchmark evidence chunks land in the top-k?

Step 1 maps every benchmark evidence quote to its gold chunk(s), using
the chunking acceptance test's matching (DECISIONS #33): a quote is
split at ellipses into fragments, all whitespace is dropped (the parser
splits amounts like "$400.0 million" across lines, #33), curly quotes
are straightened (filings use them, benchmark quotes mostly do not), and
each fragment is searched for inside the chunks of the evidence's own
filing (ticker + form + date_filed; the benchmark writes "DEF14A" where
the chunks say "DEF 14A"). A fragment not inside any single chunk is
tried across adjacent chunk pairs. The mapping must reproduce the
acceptance result (288 of 290 fragments in one chunk, 2 in an adjacent
pair, 0 missing) or the script stops.

Step 2 retrieves the top-k chunks for each of the 68 in-scope questions,
once by exact scan (numpy) and once through the HNSW index (SQL, the
database's default ef_search), and scores three ways:

  any-hit   the question counts if ANY of its gold chunks is retrieved
  all-hit   the question counts only if EVERY evidence quote has a
            chunk retrieved
  quote     fraction of evidence quotes retrieved, pooled over questions

A quote whose fragments span several chunks counts as retrieved if any
of them is. Gold is filing-specific: an identical sentence in another
year's filing is not the gold chunk (DECISIONS #24, truth is dated).

Output: data/gold_chunks.json (the mapping) and printed tables.

Run (postgres container up):
    python src/vectorstore/retrieval_recall.py
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import psycopg
from pgvector.psycopg import register_vector

DSN = "host=localhost port=5432 dbname=kgrag user=kgrag password=localdev"

CHUNKS = Path("data/chunks/chunks.jsonl")
EMB = Path("data/chunks/embeddings.npy")
QUESTIONS = Path("benchmark/questions.json")
QEMB = Path("data/chunks/question_embeddings.npy")
GOLD = Path("data/gold_chunks.json")

KS = [3, 5, 10, 20]
EXPECTED = {"single": 288, "pair": 2, "missing": 0}


QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"'})
FORMS = {"DEF14A": "DEF 14A"}


def norm(s: str) -> str:
    return re.sub(r"\s+", "", s.translate(QUOTES))


def fragments(quote: str) -> list[str]:
    return [f for f in (norm(p) for p in re.split(r"\.\.\.|…", quote)) if f]


def map_gold(questions: list[dict], records: list[dict]) -> dict[str, list[list[str]]]:
    """question id -> one list of gold chunk IDs per evidence quote."""
    by_filing: dict[tuple, list[dict]] = defaultdict(list)
    for r in records:  # chunks.jsonl is in accession/seq order already
        by_filing[(r["ticker"], r["form"], r["date_filed"])].append(r)
    texts = {r["chunk_id"]: norm(r["text"]) for r in records}

    tally = {"single": 0, "pair": 0, "missing": 0}
    gold: dict[str, list[list[str]]] = {}
    for q in questions:
        per_quote = []
        for ev in q["evidence"]:
            pool = by_filing[(ev["ticker"], FORMS.get(ev["form"], ev["form"]), ev["date_filed"])]
            hit: set[str] = set()
            for frag in fragments(ev["quote"]):
                single = [r["chunk_id"] for r in pool if frag in texts[r["chunk_id"]]]
                if single:
                    tally["single"] += 1
                    hit.update(single)
                    continue
                pairs = [
                    (a["chunk_id"], b["chunk_id"]) for a, b in zip(pool, pool[1:])
                    if a["accession"] == b["accession"]
                    and frag in texts[a["chunk_id"]] + texts[b["chunk_id"]]
                ]
                if pairs:
                    tally["pair"] += 1
                    hit.update(pairs[0])
                else:
                    tally["missing"] += 1
                    print(f"  missing: {q['id']} {ev['ticker']} {ev['form']} {ev['date_filed']}: {frag[:80]!r}")
            per_quote.append(sorted(hit))
        if per_quote:
            gold[q["id"]] = per_quote

    print(f"fragments: {tally['single']} in one chunk, {tally['pair']} across an adjacent pair, "
          f"{tally['missing']} missing")
    assert tally == EXPECTED, f"gold mapping does not reproduce the acceptance test {EXPECTED}"
    return gold


def exact_topk(Q: np.ndarray, X: np.ndarray, k: int) -> np.ndarray:
    Qn = Q / np.linalg.norm(Q, axis=1, keepdims=True)
    Xn = X / np.linalg.norm(X, axis=1, keepdims=True)
    return np.argsort(-(Qn @ Xn.T), axis=1, kind="stable")[:, :k]


def score(gold_quotes: list[list[str]], retrieved: list[str]) -> tuple[bool, bool, int]:
    got = set(retrieved)
    hits = [bool(got.intersection(g)) for g in gold_quotes]
    return any(hits), all(hits), sum(hits)


def report(title: str, runs: dict[str, dict[str, list[str]]], gold, cat_of) -> None:
    print(f"\n{title}")
    print(f"{'':<10}" + "".join(f"{f'k={k} any/all/quote':>28}" for k in KS))
    for name, top in runs.items():
        cells = []
        for k in KS:
            a = al = qh = qn = 0
            for qid, g in gold.items():
                x, y, h = score(g, top[qid][:k])
                a += x; al += y; qh += h; qn += len(g)
            n = len(gold)
            cells.append(f"{a / n:.2f} / {al / n:.2f} / {qh / qn:.2f}")
        print(f"{name:<10}" + "".join(f"{c:>28}" for c in cells))


def main() -> None:
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    records = [json.loads(line) for line in CHUNKS.open(encoding="utf-8")]
    gold = map_gold(questions, records)
    GOLD.write_text(json.dumps(gold, indent=1), encoding="utf-8")

    ids = [r["chunk_id"] for r in records]
    Q_all = np.load(QEMB)
    qrow = {q["id"]: i for i, q in enumerate(questions)}
    order = list(gold)
    Q = Q_all[[qrow[qid] for qid in order]]
    cat_of = {q["id"]: q["category"] for q in questions}

    kmax = max(KS)
    exact = {qid: [ids[j] for j in row] for qid, row in zip(order, exact_topk(Q, np.load(EMB), kmax))}
    hnsw = {}
    with psycopg.connect(DSN) as conn:
        register_vector(conn)
        for qid, v in zip(order, Q):
            rows = conn.execute(
                "SELECT chunk_id FROM chunks ORDER BY embedding <=> %s LIMIT %s", (v, kmax)
            ).fetchall()
            hnsw[qid] = [r[0] for r in rows]

    n_quotes = sum(len(g) for g in gold.values())
    print(f"\n{len(gold)} in-scope questions, {n_quotes} evidence quotes")
    report("all in-scope questions", {"exact": exact, "hnsw": hnsw}, gold, cat_of)
    for cat in ["single_hop", "multi_hop_2", "multi_hop_3", "aggregation"]:
        sub = {qid: g for qid, g in gold.items() if cat_of[qid] == cat}
        report(f"{cat} ({len(sub)} questions)", {"exact": exact, "hnsw": hnsw}, sub, cat_of)

    lost = [(qid, k) for qid in order for k in KS
            if score(gold[qid], exact[qid][:k])[2] > score(gold[qid], hnsw[qid][:k])[2]]
    print(f"\nquestion/k cells where the index lost an evidence quote the exact scan found: {len(lost)}"
          + (f"  {lost}" if lost else ""))


if __name__ == "__main__":
    main()
