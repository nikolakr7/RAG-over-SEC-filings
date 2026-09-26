"""Chunk the parsed corpus into retrieval units with permanent IDs.

Implements DECISIONS.md #31 (prefix-only XBRL strip), #32 (chunk IDs =
{accession}#{index:04d}, sha256 stored as integrity check), and #33
(whole lines merged to ~400 tokens, 800 hard max, sentence-split only for
oversized single lines, NO overlap).

THIS CHUNKER IS FROZEN once its first corpus run is accepted: embeddings,
pgvector rows, and every Phase 3 edge's source_chunk_id key off its
output. Changing anything here after that point invalidates all of them.

Run:
    python src/chunking/chunk_corpus.py

Reads:  data/raw/manifest.json, data/text/<TICKER>/*.txt
Writes: data/chunks/chunks.jsonl (one chunk per line)
Prints: a dry-run style report (counts, token percentiles, strip stats)
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

import numpy as np
import tiktoken

TARGET_TOKENS = 400
MAX_TOKENS = 800

ENC = tiktoken.get_encoding("cl100k_base")  # text-embedding-3-small's tokenizer

TEXT_DIR = Path("data/text")
OUT_PATH = Path("data/chunks/chunks.jsonl")

# --- DECISIONS #31: junk patterns for the prefix-only strip -----------------
# A line is junk if it matches any of these. The strip runs from the top of
# the file and stops FOREVER at the first non-junk line, so short lines deep
# in the document (Exhibit 21 subsidiary lists, table fragments) are safe.
JUNK_PATTERNS = [
    re.compile(r"^\S+$"),                      # single token, no spaces (halo-20260430, FALSE, EX-21.1, iso4217:USD)
    re.compile(r"^[\d\s.,:-]+$"),              # pure numbers / dates / numeric runs
    re.compile(r"^https?://"),                  # taxonomy URLs
    re.compile(r"(xbrli:|iso4217:|us-gaap|utr:|xbrldi:)"),
    re.compile(r"^(true|false|FY|Q[1-4])$", re.IGNORECASE),
]

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"'(])")


def is_junk_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return True  # blank lines inside the junk head don't end the strip
    return any(p.search(s) for p in JUNK_PATTERNS)


def strip_junk_head(lines: list[str]) -> tuple[list[str], int]:
    """Drop the leading junk block; return (kept_lines, n_stripped)."""
    for i, line in enumerate(lines):
        if not is_junk_line(line):
            return lines[i:], i
    return [], len(lines)  # a file that is ALL junk (shouldn't happen; report will show it)


def n_tokens(text: str) -> int:
    return len(ENC.encode(text, disallowed_special=()))


def split_oversized_line(line: str) -> list[str]:
    """Sentence-pack a single line that exceeds MAX_TOKENS (DECISIONS #33:
    never split mid-sentence)."""
    sentences = SENTENCE_SPLIT.split(line)
    pieces, buf, buf_tok = [], [], 0
    for s in sentences:
        t = n_tokens(s)
        if buf and buf_tok + t > TARGET_TOKENS:
            pieces.append(" ".join(buf))
            buf, buf_tok = [], 0
        buf.append(s)
        buf_tok += t
    if buf:
        pieces.append(" ".join(buf))
    return pieces


HEADING_LIKE = re.compile(r"^[A-Z\"'(]")


def is_heading_like(s: str) -> bool:
    """A short line that introduces what FOLLOWS (a name or section head:
    'Douglas S. Ingram', 'Takeda Collaboration'), as opposed to a short
    fragment that finishes what PRECEDES (amount lines like '195.4').
    Heading-like lines are carried forward at a flush, never stranded as
    a chunk's tail."""
    return (
        n_tokens(s) <= 15
        and HEADING_LIKE.match(s) is not None
        and not any(ch.isdigit() for ch in s)
        and not s.rstrip().endswith((".", "!", "?", ":", ";", ","))
    )


def chunk_lines(lines: list[str]) -> tuple[list[str], int]:
    """Greedy merge of whole lines to TARGET_TOKENS (DECISIONS #33).
    Returns (chunks, n_oversized_lines_split).

    Two boundary refinements, both found by the acceptance test (benchmark
    quote fragments must land inside single chunks):
    - after sentence-packing an oversized line, its LAST piece seeds the
      next buffer instead of being flushed, so trailing fragment lines
      (the parser splits '$195.4 million' across lines) rejoin the
      sentence that owns them;
    - a heading-like trailing line is carried forward at a flush so a
      name/section head stays with the paragraph it introduces."""
    chunks, buf, buf_tok, n_split = [], [], 0, 0

    def flush(carry_headings: bool) -> None:
        nonlocal buf, buf_tok
        if not buf:
            return
        carried: list[str] = []
        if carry_headings:
            while buf and is_heading_like(buf[-1]):
                carried.insert(0, buf.pop())
        if buf:
            chunks.append("\n".join(buf))
        buf = carried
        buf_tok = sum(n_tokens(x) for x in buf)

    for line in lines:
        s = line.strip()
        if not s:
            continue
        t = n_tokens(s)
        if t > MAX_TOKENS:
            flush(carry_headings=True)
            if buf:  # carried headings introduce the giant paragraph
                chunks.append("\n".join(buf))
                buf, buf_tok = [], 0
            pieces = split_oversized_line(s)
            chunks.extend(pieces[:-1])
            # last piece seeds the next buffer so trailing fragment lines
            # ('195.4', 'million, inclusive of $') stay attached to it
            buf, buf_tok = [pieces[-1]], n_tokens(pieces[-1])
            n_split += 1
            continue
        # A line that begins lowercase or with a digit/currency fragment
        # continues the PREVIOUS sentence (the parser splits '$410.0
        # million' across lines), so no boundary may fall before it:
        # glue it on, flushing only at the hard max.
        glue = not HEADING_LIKE.match(s)
        limit = MAX_TOKENS if glue else TARGET_TOKENS
        # +1 per joined line: chunks are joined with "\n" and tokenization
        # is not additive, so summing bare line counts undercounts the
        # final chunk (table-heavy chunks blew the hard max before this).
        if buf and buf_tok + t + 1 > limit:
            flush(carry_headings=True)
        buf.append(s)
        buf_tok += t + (1 if len(buf) > 1 else 0)
    flush(carry_headings=False)
    if buf:  # trailing headings at end of file still need a home
        chunks.append("\n".join(buf))
    return chunks, n_split


def load_manifest() -> dict[str, dict]:
    """Map accession-without-dashes -> manifest entry (dashed accession,
    ticker, form, filing_date)."""
    entries = json.loads(Path("data/raw/manifest.json").read_text(encoding="utf-8"))
    return {e["accession"].replace("-", ""): e for e in entries}


FNAME_RE = re.compile(r"^(?P<form>[^_]+)_(?P<date>\d{4}-\d{2}-\d{2})_(?P<acc>\d{18})(?:_(?P<exhibit>.+))?\.txt$")


def main() -> None:
    manifest = load_manifest()

    # Group files by accession; deterministic order per DECISIONS #32:
    # primary document first, then exhibits sorted by filename.
    by_accession: dict[str, list[Path]] = defaultdict(list)
    meta_by_acc: dict[str, dict] = {}
    for ticker_dir in sorted(TEXT_DIR.iterdir()):
        for f in sorted(ticker_dir.glob("*.txt")):
            m = FNAME_RE.match(f.name)
            assert m, f"unparseable filename: {f}"
            acc = m.group("acc")
            by_accession[acc].append(f)
            if acc not in meta_by_acc:
                mf = manifest.get(acc)
                assert mf, f"accession {acc} not in manifest ({f})"
                meta_by_acc[acc] = mf
    for acc, files in by_accession.items():
        files.sort(key=lambda p: ("_EX" in p.name, p.name))

    records = []
    strip_report = []   # (n_stripped, file, first_kept_line)
    total_split = 0
    for acc, files in sorted(by_accession.items()):
        mf = meta_by_acc[acc]
        seq = 0
        for f in files:
            lines = f.read_text(encoding="utf-8", errors="replace").split("\n")
            kept, n_stripped = strip_junk_head(lines)
            strip_report.append((n_stripped, str(f.relative_to(TEXT_DIR)), kept[0][:80] if kept else "<EMPTY>"))
            chunks, n_split = chunk_lines(kept)
            total_split += n_split
            for text in chunks:
                records.append({
                    "chunk_id": f"{mf['accession']}#{seq:04d}",
                    "accession": mf["accession"],
                    "ticker": mf["ticker"],
                    "form": mf["form"],
                    "date_filed": mf["filing_date"],
                    "source_file": str(f.relative_to(TEXT_DIR)).replace("\\", "/"),
                    "seq": seq,
                    "n_tokens": n_tokens(text),
                    "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                    "text": text,
                })
                seq += 1

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as fh:
        for r in records:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ---- report -------------------------------------------------------
    toks = np.array([r["n_tokens"] for r in records])
    print(f"accessions: {len(by_accession)}   files: {sum(len(v) for v in by_accession.values())}   chunks: {len(records)}")
    print(f"total tokens: {toks.sum():,}   oversized lines sentence-split: {total_split}")
    print("token percentiles:", {p: int(np.percentile(toks, p)) for p in (0, 25, 50, 75, 95, 99, 100)})
    print(f"chunks over hard max ({MAX_TOKENS}): {(toks > MAX_TOKENS).sum()}")
    print("\nmost head-lines stripped (top 5):")
    for n, name, first in sorted(strip_report, reverse=True)[:5]:
        print(f"  {n:5d}  {name}\n         first kept: {first!r}")
    print("\nleast stripped (bottom 3):")
    for n, name, first in sorted(strip_report)[:3]:
        print(f"  {n:5d}  {name}\n         first kept: {first!r}")
    dup = len(records) - len({r["chunk_id"] for r in records})
    print(f"\nduplicate chunk_ids: {dup}")
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
