"""Entity resolution: per-batch extractions -> one canonical graph.

Input: data/graph/<run>.jsonl from extract.py. Output:
data/graph/<run>.graph.json with canonical nodes and merged edges, which
load_neo4j.py loads.

Rules (conservative: a missed merge costs a hop, a wrong merge invents
facts):
- Plain entities (Company, Person, Drug, Compound, Technology,
  Indication) merge on a normalized name: case, punctuation, legal
  suffixes (Inc., plc, LLC ...), honorifics and degrees (Dr., Ph.D.),
  middle initials for people, and trademark symbols are ignored.
  Aliases merge two groups only when the alias points at exactly one
  group; an alias claimed by several distinct entities (three different
  "Merck"s in this corpus) merges nothing. For companies an alias also
  may only drop generic words ("Arrowhead Pharmaceuticals" -> "Arrowhead"),
  never distinguishing ones: "Royalty Pharma Investments 2019 ICAV" stays
  apart from Royalty Pharma (DECISIONS #30), and KGaA is not a strippable
  suffix, so Merck KGaA stays apart from Merck & Co.
- A surname-only person ("Dr. Rastetter") merges into the one full-name
  person with that surname in the same batch, else stays separate.
- Event nodes (Agreement, LegalCase, Payment) merge on type + resolved
  party set (+ agreement type, or payment kind + amount). Two deals of the
  same type between the same parties would merge; accepted for now.
- Edges merge on (type, from, to, qualifier), where the qualifier is the
  property that distinguishes parallel edges (role, territory,
  jurisdiction, year). Each merged edge keeps every source chunk ID and
  takes its properties from the NEWEST filing (DECISIONS #24: truth as of
  the corpus end), so a retirement in a 2026 8-K beats an older "active".

Run:
    python src/graph/resolve.py full
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

GRAPH_DIR = Path("data/graph")
CHUNKS = Path("data/chunks/chunks.jsonl")

PLAIN = {"Company", "Person", "Drug", "Compound", "Technology", "Indication"}
GENERIC = {"company", "the company", "we", "us", "our", "registrant", "the registrant", "partner",
           "licensee", "licensor", "collaborator", "agreement", "the agreement", "parent"}
SUFFIX = re.compile(
    r"\b(incorporated|inc|corporation|corp|company|co|limited|ltd|llc|l\.l\.c|plc|lp|llp|ag|sa|nv|bv|gmbh|"
    r"se|holdings?|group)\b\.?")
GENERIC_WORDS = {"pharmaceuticals", "pharmaceutical", "pharma", "therapeutics", "biosciences", "bioscience",
                 "biotech", "biotechnology", "biopharma", "international", "global", "laboratories", "labs",
                 "healthcare", "health", "and", "usa", "us", "america"}
HONOR = re.compile(r"\b(dr|mr|ms|mrs|m\.?d|ph\.?d|pharm\.?d|j\.?d|mba|esq)\b\.?")
QUALIFIER = {"PARTY_TO": "role", "OFFICER_OF": "role", "OWES_ROYALTY_TO": "territory",
             "APPROVED_FOR": "jurisdiction", "PEER_OF": "year", "IN_DEVELOPMENT_FOR": "label"}


def norm(name: str, typ: str) -> str:
    s = name.lower().replace("®", "").replace("™", "").replace("&", " and ")
    s = s.replace("’", "'")
    if typ == "Company":
        s = re.sub(r"^the\s+", "", s)
        s = SUFFIX.sub(" ", s.replace(",", " "))
        s = re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s)).strip()
        s = re.sub(r"^and\b|\band$", "", s).strip()
    if typ == "Person":
        s = HONOR.sub(" ", s)
        parts = [p for p in re.split(r"[\s,]+", re.sub(r"[^\w\s,-]", " ", s)) if p]
        parts = [p for p in parts if len(p) > 1 and p not in {"jr", "sr", "ii", "iii"}]
        return " ".join([parts[0], parts[-1]]) if len(parts) >= 2 else (parts[0] if parts else "")
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s)).strip()


class UF:
    def __init__(self) -> None:
        self.p: dict = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b) -> None:
        self.p[self.find(a)] = self.find(b)


def main() -> None:
    run = sys.argv[1] if len(sys.argv) > 1 else "full"
    batches = [json.loads(l) for l in (GRAPH_DIR / f"{run}.jsonl").open(encoding="utf-8")]
    filed = {}
    for l in CHUNKS.open(encoding="utf-8"):
        r = json.loads(l)
        filed[r["chunk_id"]] = r["date_filed"]

    # 1. every node mention gets a global id; plain types start grouped by normalized name
    mentions = {}  # gid -> node
    uf = UF()
    for b in batches:
        people_full = defaultdict(list)
        for key, n in b["nodes"].items():
            gid = (b["batch"], key)
            n = {**n, "batch": b["batch"]}
            mentions[gid] = n
            if n["type"] in PLAIN:
                k = norm(n["name"], n["type"])
                n["norm"] = k
                if k and k not in GENERIC:
                    uf.union(gid, ("name", n["type"], k))
                if n["type"] == "Person" and " " in k:
                    people_full[k.split()[-1]].append(gid)
        for gid, n in list(mentions.items()):  # surname-only people, same batch
            if gid[0] == b["batch"] and n["type"] == "Person" and n.get("norm") and " " not in n["norm"]:
                cands = {uf.find(g) for g in people_full.get(n["norm"], [])}
                if len(cands) == 1:
                    uf.union(gid, cands.pop())

    # 2. aliases: merge only when the alias names exactly one existing group
    name_groups = defaultdict(set)
    for gid, n in mentions.items():
        if n["type"] in PLAIN and n.get("norm"):
            name_groups[(n["type"], n["norm"])].add(uf.find(gid))
    claims = defaultdict(set)  # (type, alias_norm) -> groups claiming it
    for gid, n in mentions.items():
        if n["type"] in PLAIN:
            for a in n["aliases"]:
                an = norm(a, n["type"])
                if not an or an in GENERIC or an == n.get("norm"):
                    continue
                if n["type"] == "Company":
                    dropped = set(n.get("norm", "").split()) - set(an.split())
                    if not set(an.split()) <= set(n.get("norm", "").split()) or dropped - GENERIC_WORDS:
                        continue
                claims[(n["type"], an)].add(uf.find(gid))
    for key, srcs in claims.items():
        srcs = {uf.find(s) for s in srcs}
        targets = {uf.find(t) for t in name_groups.get(key, set())}
        if len(srcs) == 1 and len(targets) <= 1:
            (src,) = srcs
            if targets:
                uf.union(src, targets.pop())
            else:
                uf.union(("name", key[0], key[1]), src)

    # 3. canonical plain nodes
    nodes: dict[str, dict] = {}
    canon = {}
    groups = defaultdict(list)
    for gid, n in mentions.items():
        if n["type"] in PLAIN:
            groups[uf.find(gid)].append(n)
    for i, (root, ns) in enumerate(groups.items()):
        typ = ns[0]["type"]
        names = [n["name"] for n in ns]
        best = max(set(names), key=lambda s: (names.count(s), len(s)))
        nid = f"{typ[:3].lower()}{i}"
        aliases = sorted({a for n in ns for a in [n["name"], *n["aliases"]] if a != best
                          and norm(a, typ) not in GENERIC})
        props = {}
        for n in ns:
            props.update({k: v for k, v in n["props"].items() if v not in (None, "", [])})
        nodes[nid] = {"id": nid, "type": typ, "name": best, "aliases": aliases[:50], "props": props}
        canon[root] = nid
    for gid, n in mentions.items():
        if n["type"] in PLAIN:
            n["cid"] = canon[uf.find(gid)]

    # 4. event nodes: key on type + resolved parties (+ subtype)
    parties = defaultdict(set)
    for b in batches:
        for e in b["edges"]:
            if e["type"] == "PARTY_TO":
                parties[(b["batch"], e["to"])].add(mentions[(b["batch"], e["from"])].get("cid"))
    ev_key = {}
    for gid, n in mentions.items():
        if n["type"] in PLAIN:
            continue
        p = tuple(sorted(x for x in parties.get(gid, set()) if x))
        sub = ""
        if n["type"] == "Agreement":
            sub = str(n["props"].get("type", ""))
        elif n["type"] == "Payment":
            sub = f"{n['props'].get('kind', '')}|{n['props'].get('amount', '')}"
        key = (n["type"], p, sub) if p else (n["type"], ("solo", n["batch"], norm(n["name"], n["type"])), sub)
        ev_key.setdefault(key, []).append(gid)
    for i, (key, gids) in enumerate(ev_key.items()):
        ns = sorted((mentions[g] for g in gids), key=lambda n: filed.get(n.get("chunk_id"), ""))
        typ = key[0]
        nid = f"{typ[:3].lower()}e{i}"
        props = {}
        for n in ns:  # newest filing last, so its values win
            props.update({k: v for k, v in n["props"].items() if v not in (None, "", [])})
        names = [n["name"] for n in ns]
        nodes[nid] = {"id": nid, "type": typ, "name": ns[-1]["name"],
                      "aliases": sorted(set(names) - {ns[-1]["name"]})[:20], "props": props,
                      "source_chunk_ids": sorted({n["chunk_id"] for n in ns if n.get("chunk_id")})}
        for g in gids:
            mentions[g]["cid"] = nid

    # 5. edges: merge parallel assertions, newest filing wins
    edges: dict[tuple, dict] = {}
    for b in batches:
        for e in b["edges"]:
            a = mentions[(b["batch"], e["from"])]["cid"]
            z = mentions[(b["batch"], e["to"])]["cid"]
            q = str(e["props"].get(QUALIFIER.get(e["type"], ""), "")).lower().strip()
            k = (e["type"], a, z, q)
            date = filed.get(e["chunk_id"], "")
            cur = edges.get(k)
            if cur is None:
                edges[k] = cur = {"type": e["type"], "from": a, "to": z, "props": {},
                                  "source_chunk_ids": [], "_date": ""}
            cur["source_chunk_ids"].append(e["chunk_id"])
            props = {kk: v for kk, v in e["props"].items() if kk != "source_chunk_id" and v not in (None, "", [])}
            if date >= cur["_date"]:
                cur["props"] = {**cur["props"], **props}
                cur["_date"] = date
            else:
                cur["props"] = {**props, **cur["props"]}
    for e in edges.values():
        e["latest_filed"] = e.pop("_date")
        e["source_chunk_ids"] = sorted(set(e["source_chunk_ids"]))

    out = GRAPH_DIR / f"{run}.graph.json"
    out.write_text(json.dumps({"nodes": list(nodes.values()), "edges": list(edges.values())},
                              ensure_ascii=False), encoding="utf-8")
    by_type = defaultdict(int)
    for n in nodes.values():
        by_type[n["type"]] += 1
    print(f"{len(mentions)} node mentions -> {len(nodes)} nodes {dict(by_type)}")
    print(f"{sum(len(b['edges']) for b in batches)} edge assertions -> {len(edges)} edges")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
