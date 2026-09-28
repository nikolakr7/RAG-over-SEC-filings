"""Phase 3 extraction: chunks -> ontology v1 nodes and edges (JSON).

Each LLM call gets ontology.md verbatim as its instructions (its
definitions are written as extraction instructions, ontology convention
4) plus up to BATCH consecutive chunks from ONE filing, headed with the
filer's name so "we" / "the Company" resolve. The model returns nodes
with batch-local keys and edges between those keys; every edge and every
Agreement / LegalCase / Payment node carries the chunk_id it came from
(ontology convention 2).

Output is validated against ontology v1 (types, edge domain -> range,
chunk_id belongs to the batch); anything invalid is dropped and counted,
never repaired by guessing. Filing nodes and FILED_BY edges are NOT
extracted; the loader creates them from chunk metadata.

Results are cached per batch in data/graph/<run>.jsonl (resumable, paid
once). Entity resolution and the Neo4j load are separate steps.

Run:
    python src/graph/extract.py pilot     # ~50 benchmark-evidence chunks
    python src/graph/extract.py full      # whole corpus
"""

from __future__ import annotations

import json
import re
import sys
import threading
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "rag"))
from pipeline import llm  # noqa: E402

CHUNKS = Path("data/chunks/chunks.jsonl")
GOLD = Path("data/gold_chunks.json")
ONTOLOGY = Path("ontology.md")
OUT_DIR = Path("data/graph")

BATCH = 8
WORKERS = 16
PILOT_CHUNKS = 48

FILERS = {
    "EXEL": "Exelixis, Inc.", "HALO": "Halozyme Therapeutics, Inc.",
    "SRPT": "Sarepta Therapeutics, Inc.", "ALKS": "Alkermes plc",
    "IONS": "Ionis Pharmaceuticals, Inc.", "RARE": "Ultragenyx Pharmaceutical Inc.",
    "ARWR": "Arrowhead Pharmaceuticals, Inc.", "NBIX": "Neurocrine Biosciences, Inc.",
}

NODE_TYPES = {"Company", "Drug", "Compound", "Technology", "Person", "Agreement",
              "Indication", "LegalCase", "Payment"}
EVENT_TYPES = {"Agreement", "LegalCase", "Payment"}
EDGES = {  # type -> (domain, range), ontology v1
    "PARTY_TO": ({"Company"}, {"Agreement", "LegalCase", "Payment"}),
    "COVERS": ({"Agreement", "LegalCase"}, {"Drug", "Compound", "Technology"}),
    "SUBSIDIARY_OF": ({"Company"}, {"Company"}),
    "AFFILIATE_OF": ({"Company"}, {"Company"}),
    "AUDITED_BY": ({"Company"}, {"Company"}),
    "OFFICER_OF": ({"Person"}, {"Company"}),
    "CONTAINS": ({"Drug", "Technology"}, {"Compound"}),
    "USES_TECHNOLOGY": ({"Drug", "Compound", "Technology"}, {"Technology"}),
    "APPROVED_FOR": ({"Drug"}, {"Indication"}),
    "IN_DEVELOPMENT_FOR": ({"Compound", "Drug"}, {"Indication"}),
    "OWNS": ({"Company"}, {"Compound", "Drug", "Technology"}),
    "CONSOLIDATED_INTO": ({"LegalCase"}, {"LegalCase"}),
    "PAID_UNDER": ({"Payment"}, {"Agreement", "LegalCase"}),
    "OWES_ROYALTY_TO": ({"Company"}, {"Company"}),
    "PEER_OF": ({"Company"}, {"Company"}),
}

TASK = """

# YOUR TASK

You are extracting a knowledge graph from SEC filing excerpts using the \
ontology above. Extract ONLY facts the excerpts state; never outside \
knowledge. Skip excerpts with nothing in scope (financial tables, \
boilerplate risk language, signatures) by extracting nothing from them.

Rules:
- "we", "us", "our", "the Company" mean the FILER named in the header.
- Use the most complete name the text gives as `name` (e.g. "Ernst & Young \
LLP", "Takeda Pharmaceuticals International AG"); put shorter forms used \
in the text in `aliases`.
- Do NOT extract Filing nodes or FILED_BY edges. Do NOT extract \
competitors (no competition edges exist), shareholder votes, or \
contingent "up to" milestone amounts as Payment nodes.
- Agreement, LegalCase and Payment nodes need a short stable `name` \
naming the parties and subject (e.g. "Exelixis-Ipsen cabozantinib \
collaboration and license", "Exelixis v. MSN (MSN II)").
- Put dates as YYYY-MM-DD, YYYY-MM or YYYY. Include `status` and dates on \
edges and event nodes when the text gives them.
- Every edge and every Agreement/LegalCase/Payment node must carry the \
`chunk_id` of the excerpt that states it.
- Only the 15 edge types above (excluding FILED_BY), in the stated \
domain -> range direction.

Return JSON only, exactly this shape:
{"nodes": [{"key": "n1", "type": "Company", "name": "...", "aliases": [], \
"props": {}, "chunk_id": "..."}],
 "edges": [{"type": "PARTY_TO", "from": "n1", "to": "n2", "props": \
{"role": "licensor"}, "chunk_id": "..."}]}
If nothing is in scope, return {"nodes": [], "edges": []}."""


def instructions() -> str:
    return ONTOLOGY.read_text(encoding="utf-8") + TASK


def make_batches(records: list[dict]) -> list[list[dict]]:
    by_acc: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        by_acc[r["accession"]].append(r)
    batches = []
    for acc in sorted(by_acc):
        rs = sorted(by_acc[acc], key=lambda r: r["seq"])
        batches += [rs[i:i + BATCH] for i in range(0, len(rs), BATCH)]
    return batches


def validate(raw: dict, chunk_ids: set[str], stats: Counter) -> dict:
    nodes = {}
    for n in raw.get("nodes", []):
        t = n.get("type")
        if t not in NODE_TYPES or not str(n.get("name", "")).strip() or not n.get("key"):
            stats["node_dropped_invalid"] += 1
            continue
        if t in EVENT_TYPES and n.get("chunk_id") not in chunk_ids:
            stats["node_dropped_bad_chunk"] += 1
            continue
        nodes[n["key"]] = {"type": t, "name": n["name"].strip(),
                           "aliases": [a for a in n.get("aliases") or [] if isinstance(a, str)],
                           "props": n.get("props") or {}, "chunk_id": n.get("chunk_id")}
    edges = []
    for e in raw.get("edges", []):
        spec = EDGES.get(e.get("type"))
        src, dst = nodes.get(e.get("from")), nodes.get(e.get("to"))
        if not spec or not src or not dst:
            stats["edge_dropped_unknown"] += 1
        elif src["type"] not in spec[0] or dst["type"] not in spec[1]:
            stats["edge_dropped_domain_range"] += 1
        elif e.get("chunk_id") not in chunk_ids:
            stats["edge_dropped_bad_chunk"] += 1
        else:
            edges.append({"type": e["type"], "from": e["from"], "to": e["to"],
                          "props": e.get("props") or {}, "chunk_id": e["chunk_id"]})
    stats["nodes_kept"] += len(nodes)
    stats["edges_kept"] += len(edges)
    return {"nodes": nodes, "edges": edges}


def extract(batch: list[dict], instr: str, stats: Counter) -> dict:
    r0 = batch[0]
    header = (f"FILER: {FILERS[r0['ticker']]} ({r0['ticker']})\nFORM: {r0['form']}\n"
              f"FILED: {r0['date_filed']}\nACCESSION: {r0['accession']}\n\nEXCERPTS:\n\n")
    body = "\n\n".join(f"[chunk_id: {r['chunk_id']}]\n{r['text']}" for r in batch)
    raw_text, usage = llm(instr, header + body)
    m = re.search(r"\{.*\}", raw_text, re.S)
    try:
        raw = json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        raw = {}
        stats["unparseable"] += 1
    graph = validate(raw, {r["chunk_id"] for r in batch}, stats)
    return {"batch": r0["chunk_id"], "accession": r0["accession"], "ticker": r0["ticker"],
            "chunk_ids": [r["chunk_id"] for r in batch], **graph, "usage": usage}


def main() -> None:
    run = sys.argv[1] if len(sys.argv) > 1 else "pilot"
    records = [json.loads(l) for l in CHUNKS.open(encoding="utf-8")]
    if run == "pilot":
        gold = json.loads(GOLD.read_text(encoding="utf-8"))
        want = list(dict.fromkeys(c for g in gold.values() for q in g for c in q))[:PILOT_CHUNKS]
        records = [r for r in records if r["chunk_id"] in set(want)]
    elif run != "full":
        raise SystemExit("run must be pilot or full")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"{run}.jsonl"
    done = {json.loads(l)["batch"] for l in out.open(encoding="utf-8")} if out.exists() else set()
    batches = [b for b in make_batches(records) if b[0]["chunk_id"] not in done]
    print(f"{run}: {len(records)} chunks, {len(done)} batches cached, {len(batches)} to run")

    instr = instructions()
    stats: Counter = Counter()
    lock = threading.Lock()
    tot = Counter()
    with ThreadPoolExecutor(WORKERS) as pool, out.open("a", encoding="utf-8") as f:
        futs = [pool.submit(extract, b, instr, stats) for b in batches]
        for n, fut in enumerate(as_completed(futs), 1):
            rec = fut.result()
            with lock:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                tot.update(rec["usage"])
            if n % 25 == 0 or n == len(batches):
                print(f"  {n}/{len(batches)} batches, tokens {tot['in']:,} in / {tot['out']:,} out")
    print("validation:", dict(stats))
    if batches:
        print(f"per batch: {tot['in'] / len(batches):,.0f} in / {tot['out'] / len(batches):,.0f} out")


if __name__ == "__main__":
    main()
