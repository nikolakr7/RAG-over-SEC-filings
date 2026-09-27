"""Load a resolved graph (data/graph/<run>.graph.json) into Neo4j.

Full replace: wipes the database, then creates every node with its
ontology type as label plus a shared :Entity label (unique `id`), every
edge with its properties plus `source_chunk_ids` and `latest_filed`, and
the Filing nodes + FILED_BY edges from chunk metadata (never extracted).
The eight filer Company nodes get a `ticker` property.

Neo4j properties must be primitives or lists of primitives, so nested
values the extractor produced are stored as JSON strings.

Run (neo4j container up: docker compose up -d neo4j):
    python src/graph/load_neo4j.py full
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from neo4j import GraphDatabase

sys.path.insert(0, str(Path(__file__).resolve().parent))
from extract import FILERS  # noqa: E402
from resolve import norm  # noqa: E402

URI, AUTH = "bolt://localhost:7687", ("neo4j", "localdevpassword")
GRAPH_DIR = Path("data/graph")
CHUNKS = Path("data/chunks/chunks.jsonl")


def flat(props: dict) -> dict:
    out = {}
    for k, v in props.items():
        k = re.sub(r"\W", "_", str(k))
        if isinstance(v, (str, int, float, bool)):
            out[k] = v
        elif isinstance(v, list) and v and all(isinstance(x, str) for x in v):
            out[k] = v
        elif v not in (None, [], {}):
            out[k] = json.dumps(v, ensure_ascii=False)
    return out


def main() -> None:
    run = sys.argv[1] if len(sys.argv) > 1 else "full"
    g = json.loads((GRAPH_DIR / f"{run}.graph.json").read_text(encoding="utf-8"))

    # filer tickers -> canonical company node (largest node whose name normalizes like the filer)
    ticker_of = {}
    for t, name in FILERS.items():
        target = norm(name, "Company")
        cands = [n for n in g["nodes"] if n["type"] == "Company"
                 and (norm(n["name"], "Company") == target
                      or target in {norm(a, "Company") for a in n["aliases"]})]
        if cands:
            ticker_of[max(cands, key=lambda n: len(n["aliases"]))["id"]] = t
    filer_node = {t: nid for nid, t in ticker_of.items()}

    filings = {}
    for l in CHUNKS.open(encoding="utf-8"):
        r = json.loads(l)
        filings.setdefault(r["accession"], {"id": r["accession"], "accession": r["accession"], "form": r["form"],
                                            "date_filed": r["date_filed"], "ticker": r["ticker"]})

    drv = GraphDatabase.driver(URI, auth=AUTH)
    with drv.session() as s:
        s.run("MATCH (n) DETACH DELETE n")
        s.run("CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE")
        by_type = defaultdict(list)
        for n in g["nodes"]:
            props = flat(n["props"])
            props.update(id=n["id"], name=n["name"], aliases=n["aliases"])
            if n.get("source_chunk_ids"):
                props["source_chunk_ids"] = n["source_chunk_ids"]
            if n["id"] in ticker_of:
                props["ticker"] = ticker_of[n["id"]]
            by_type[n["type"]].append(props)
        for typ, rows in by_type.items():
            for i in range(0, len(rows), 2000):
                s.run(f"UNWIND $rows AS p CREATE (n:Entity:{typ}) SET n = p", rows=rows[i:i + 2000])

        s.run("UNWIND $rows AS p CREATE (n:Entity:Filing) SET n = p", rows=list(filings.values()))
        s.run("UNWIND $rows AS r MATCH (f:Filing {id: r.acc}), (c:Entity {id: r.cid}) CREATE (f)-[:FILED_BY]->(c)",
              rows=[{"acc": a, "cid": filer_node[f["ticker"]]} for a, f in filings.items() if f["ticker"] in filer_node])

        by_rel = defaultdict(list)
        for e in g["edges"]:
            props = flat(e["props"])
            props.update(source_chunk_ids=e["source_chunk_ids"], latest_filed=e["latest_filed"])
            by_rel[e["type"]].append({"a": e["from"], "b": e["to"], "p": props})
        for typ, rows in by_rel.items():
            for i in range(0, len(rows), 2000):
                s.run(f"UNWIND $rows AS r MATCH (a:Entity {{id: r.a}}), (b:Entity {{id: r.b}}) "
                      f"CREATE (a)-[x:{typ}]->(b) SET x = r.p", rows=rows[i:i + 2000])

        counts = s.run("MATCH (n) RETURN [l IN labels(n) WHERE l <> "Entity"][0] AS t, count(*) AS c ORDER BY c DESC").data()
        rels = s.run("MATCH ()-[r]->() RETURN type(r) AS t, count(*) AS c ORDER BY c DESC").data()
    drv.close()
    print("filers linked:", sorted(ticker_of.values()), "missing:", sorted(set(FILERS) - set(ticker_of.values())))
    print("nodes:", {r["t"]: r["c"] for r in counts})
    print("edges:", {r["t"]: r["c"] for r in rels})


if __name__ == "__main__":
    main()
