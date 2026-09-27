"""Hybrid RAG: graph facts from Neo4j + reranked vector chunks.

Per question:
  1. Entity linking. The chat model lists the entities the question names
     (companies, people, drugs, compounds, technologies, indications);
     each is matched to graph nodes by normalized name or alias
     (resolve.norm), falling back to fuzzy matching on names.
  2. Graph expansion (Cypher). Every edge touching a linked node, plus
     the other edges of neighbouring event nodes (Agreement, LegalCase,
     Payment) and neighbouring people, so a semantic hop through a
     reified deal or a shared director is one step. Facts are ranked:
     edges linking two linked entities first, then newest filing first,
     capped at MAX_FACTS.
  3. Answer. The answerer sees the graph facts (each with its source chunk
     IDs and filing date) and the rerank variant's top-10 chunks, with
     the same citation and refusal rules as the baseline.

Output rows match pipeline.py (data/runs/hybrid.jsonl) plus the linked
entities, the facts shown, and context_ids (every chunk ID the answerer
could legitimately cite), which the citation validator uses.

Run:
    python src/rag/hybrid.py [--limit N]
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
from neo4j import GraphDatabase

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "graph"))
from pipeline import ANSWER_INSTRUCTIONS, K_WIDE, QEMB, QUESTIONS, RUNS, fmt, llm, rerank, search  # noqa: E402
from resolve import norm  # noqa: E402

URI, AUTH = "bolt://localhost:7687", ("neo4j", "localdevpassword")
MAX_FACTS = 150
WORKERS = 4
LINK_TYPES = ["Company", "Person", "Drug", "Compound", "Technology", "Indication"]

LINK_INSTRUCTIONS = """\
List the named entities in the question that could be nodes in a \
knowledge graph of biotech SEC filings: companies (including the filers \
Exelixis, Halozyme, Sarepta, Alkermes, Ionis, Ultragenyx, Arrowhead, \
Neurocrine), people, drugs (brand names), compounds (generic names), \
technologies/platforms, and diseases/indications. Use the names as \
written, plus the fuller official name if you know it. Return JSON only: \
{"entities": [{"name": "...", "type": "Company|Person|Drug|Compound|Technology|Indication"}]}"""

HYBRID_INSTRUCTIONS = ANSWER_INSTRUCTIONS + """

You also get GRAPH FACTS extracted from the same filings. Each fact names \
its source chunk IDs and the filing date of its newest source; cite those \
chunk IDs like excerpt IDs. Facts from different filings can conflict \
over time (e.g. an older filing calling someone CEO): prefer the newest \
filing and any stated effective dates. Graph facts are extracted by a \
model and can be incomplete; the excerpts are the primary text."""

EXPAND = """
MATCH (s:Entity) WHERE s.id IN $ids
MATCH (s)-[r]-(m) WHERE NOT m:Filing
WITH collect(DISTINCT r) AS r1, collect(DISTINCT m) AS ms
UNWIND ms AS m
OPTIONAL MATCH (m)-[r2]-(o) WHERE (m:Agreement OR m:LegalCase OR m:Payment OR m:Person) AND NOT o:Filing
WITH r1, collect(DISTINCT r2) AS r2s
UNWIND r1 + r2s AS r
WITH DISTINCT r WHERE r IS NOT NULL
RETURN startNode(r).id AS a, labels(startNode(r)) AS la, startNode(r).name AS an,
       type(r) AS t, properties(r) AS p,
       endNode(r).id AS b, labels(endNode(r)) AS lb, endNode(r).name AS bn
"""

_driver = None
_index: dict[str, list[tuple[str, str]]] = {}
_names: list[str] = []
_lock = threading.Lock()


def driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(URI, auth=AUTH)
    return _driver


def build_index() -> None:
    """normalized name/alias -> [(node id, type)] for the linkable types."""
    with _lock:
        if _index:
            return
        with driver().session() as s:
            rows = s.run("MATCH (n:Entity) WHERE NOT n:Filing AND NOT n:Agreement AND NOT n:LegalCase "
                         "AND NOT n:Payment RETURN n.id AS id, [l IN labels(n) WHERE l <> 'Entity'][0] AS t, "
                         "n.name AS name, n.aliases AS aliases, n.ticker AS ticker").data()
        for r in rows:
            keys = {norm(r["name"], r["t"])} | {norm(a, r["t"]) for a in r["aliases"] or []}
            if r["ticker"]:
                keys.add(r["ticker"].lower())
            for k in keys:
                if k:
                    _index.setdefault(k, []).append((r["id"], r["t"]))
        _names.extend(_index)


def link(question: str) -> tuple[list[str], list[str], dict]:
    text, usage = llm(LINK_INSTRUCTIONS, question)
    m = re.search(r"\{.*\}", text, re.S)
    try:
        ents = json.loads(m.group(0))["entities"] if m else []
    except (json.JSONDecodeError, KeyError):
        ents = []
    ids, found = [], []
    for e in ents:
        typ = e.get("type") if e.get("type") in LINK_TYPES else "Company"
        k = norm(str(e.get("name", "")), typ)
        hits = _index.get(k) or _index.get(norm(str(e.get("name", "")), "Company")) or []
        if not hits and k:
            close = difflib.get_close_matches(k, _names, n=1, cutoff=0.88)
            hits = _index.get(close[0], []) if close else []
        if hits:
            found.append(e.get("name", ""))
            ids += [h[0] for h in hits[:3]]
    return list(dict.fromkeys(ids)), found, usage


def facts_for(ids: list[str]) -> list[dict]:
    if not ids:
        return []
    with driver().session() as s:
        rows = s.run(EXPAND, ids=ids).data()
    seeds = set(ids)
    for r in rows:
        r["both"] = r["a"] in seeds and r["b"] in seeds
        r["date"] = r["p"].get("latest_filed", "")
    rows.sort(key=lambda r: (not r["both"], r["date"]), reverse=False)
    both = [r for r in rows if r["both"]]
    rest = sorted((r for r in rows if not r["both"]), key=lambda r: r["date"], reverse=True)
    return (both + rest)[:MAX_FACTS]


def fmt_fact(r: dict) -> str:
    p = {k: v for k, v in r["p"].items() if k not in ("source_chunk_ids", "latest_filed")}
    la = [l for l in r["la"] if l != "Entity"][0]
    lb = [l for l in r["lb"] if l != "Entity"][0]
    props = ", ".join(f"{k}: {v}" for k, v in p.items())
    src = ", ".join(r["p"].get("source_chunk_ids", [])[:3])
    return (f"{la}({r['an']}) -{r['t']}" + (f" {{{props}}}" if props else "") + f"-> {lb}({r['bn']})"
            f"  [newest filing {r['date']}; sources: {src}]")


def answer(question: str, vec: np.ndarray) -> dict:
    build_index()
    ids, found, u0 = link(question)
    facts = facts_for(ids)
    chunks, u1 = rerank(question, search(vec, K_WIDE))
    fact_text = "\n".join(fmt_fact(f) for f in facts) or "(no graph facts found)"
    text, u2 = llm(HYBRID_INSTRUCTIONS,
                   f"Question: {question}\n\nGRAPH FACTS:\n{fact_text}\n\nExcerpts:\n\n{fmt(chunks)}")
    context = {c["chunk_id"] for c in chunks} | {c for f in facts for c in f["p"].get("source_chunk_ids", [])[:3]}
    usage = {k: u0[k] + u1[k] + u2[k] for k in ("in", "out")}
    return {"answer": text, "retrieved": [c["chunk_id"] for c in chunks], "linked": found,
            "n_facts": len(facts), "context_ids": sorted(context), "usage": usage}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--name", default="hybrid")
    args = ap.parse_args()
    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))
    qvecs = np.load(QEMB)
    out = RUNS / f"{args.name}.jsonl"
    done = {json.loads(l)["id"] for l in out.open(encoding="utf-8")} if out.exists() else set()
    todo = [(q, qvecs[i]) for i, q in enumerate(questions) if q["id"] not in done][: args.limit]
    print(f"{args.name}: {len(done)} cached, {len(todo)} to run")
    with ThreadPoolExecutor(WORKERS) as pool, out.open("a", encoding="utf-8") as f:
        futs = {pool.submit(answer, q["question"], v): q for q, v in todo}
        for n, fut in enumerate(as_completed(futs), 1):
            q = futs[fut]
            rec = {"id": q["id"], "category": q["category"], "question": q["question"], **fut.result()}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            f.flush()
            print(f"  [{n}/{len(todo)}] {q['id']} linked={rec['linked']} facts={rec['n_facts']}")


if __name__ == "__main__":
    main()
