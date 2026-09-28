"""Citation validator: are an answer's cited chunk IDs real and grounded?

For each answer in data/runs/<variant>.jsonl:
  - cited IDs are parsed from square brackets ({accession}#{seq})
  - an ID is VALID if it exists in the chunk store AND was in the context
    the answerer was shown (retrieved chunks, plus graph-fact sources for
    hybrid runs); an ID outside the context is invented or misremembered
  - a cited chunk is GOLD if it is one of the question's benchmark
    evidence chunks, or the adjacent-pair neighbour of one (DECISIONS #33:
    2 of 290 quote fragments span a chunk boundary)

Reports, per variant: share of non-refusal answers with at least one
citation, share of cited IDs that are valid, share of answers whose
citations are all valid, and share of in-scope answers citing a gold
chunk.

Run:
    python src/eval/citations.py vector rerank hybrid
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

RUNS = Path("data/runs")
CHUNKS = Path("data/chunks/chunks.jsonl")
GOLD = Path("data/gold_chunks.json")
CITE = re.compile(r"\d{10}-\d{2}-\d{6}#\d{4}")
# a refusal leads the answer, or leads its "Final answer:" (decomp mode)
REFUSAL = re.compile(r"^\s*(\d+\.\s*)?REFUSE|Final answer:\s*REFUSE", re.I)


def neighbours(cid: str) -> set[str]:
    acc, seq = cid.split("#")
    return {cid} | {f"{acc}#{int(seq) + d:04d}" for d in (-1, 1) if int(seq) + d >= 0}


def main() -> None:
    variants = sys.argv[1:] or ["vector", "rerank"]
    known = {json.loads(l)["chunk_id"] for l in CHUNKS.open(encoding="utf-8")}
    gold = json.loads(GOLD.read_text(encoding="utf-8"))
    print(f"{'variant':<10}{'cites any':>11}{'IDs valid':>11}{'all valid':>11}{'cites gold':>12}")
    for v in variants:
        rows = [json.loads(l) for l in (RUNS / f"{v}.jsonl").open(encoding="utf-8")]
        answered = [r for r in rows if not REFUSAL.search(r["answer"])]
        n_ids = n_valid = all_valid = with_cite = gold_hit = in_scope = 0
        for r in answered:
            ids = CITE.findall(r["answer"])
            context = set(r.get("context_ids") or r["retrieved"])
            valid = [i for i in ids if i in known and i in context]
            n_ids += len(ids)
            n_valid += len(valid)
            with_cite += bool(ids)
            all_valid += bool(ids) and len(valid) == len(ids)
            if r["id"] in gold:
                in_scope += 1
                g = set().union(*(neighbours(c) for q in gold[r["id"]] for c in q))
                gold_hit += bool(set(ids) & g)
        n = max(len(answered), 1)
        print(f"{v:<10}{with_cite / n:>11.2f}{n_valid / max(n_ids, 1):>11.2f}{all_valid / n:>11.2f}"
              f"{gold_hit / max(in_scope, 1):>12.2f}")


if __name__ == "__main__":
    main()
