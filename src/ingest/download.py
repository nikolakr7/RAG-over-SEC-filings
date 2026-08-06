"""Download SEC filings from EDGAR.

EDGAR is free and needs no API key, but it has two rules that will get you
blocked if you ignore them:

  1. Every request must send a User-Agent identifying you, including a real
     contact address. Requests without one get 403 Forbidden. (Try it — the
     SEC's own documentation page 403s a generic HTTP client.)
  2. Stay under 10 requests/second. We throttle well below that; nothing here
     is urgent enough to risk an IP ban.

Two endpoints do all the work:

  https://www.sec.gov/files/company_tickers.json
      One big ticker -> CIK map. A CIK is EDGAR's permanent company id.
      Tickers change, companies rename themselves, CIKs never move. Worth
      noticing now: this is EDGAR's own answer to the entity-resolution
      problem you'll be solving by hand in Phase 3.

  https://data.sec.gov/submissions/CIK##########.json
      Every filing a company has ever made. Note the CIK is zero-padded to
      10 digits in THIS url but not in the Archives url below. That
      inconsistency is EDGAR's, not ours.

Run:
    python src/ingest/download.py --per-company 1 --forms 10-K
    python src/ingest/download.py --per-company 6
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
import os

load_dotenv()

# Mid-cap biotech. Same sector on purpose: shared auditors, overlapping
# officers and directors, licensing deals with each other. That density is
# what makes multi-hop questions have answers. A grab-bag of unrelated
# companies would produce a graph with nothing to traverse.
TICKERS = [
    "EXEL",  # Exelixis
    "HALO",  # Halozyme
    "SRPT",  # Sarepta
    "ALKS",  # Alkermes
    "IONS",  # Ionis
    "RARE",  # Ultragenyx
    "ARWR",  # Arrowhead
    "NBIX",  # Neurocrine
]

TICKER_MAP_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{document}"

RAW_DIR = Path("data/raw")
MANIFEST_PATH = RAW_DIR / "manifest.json"

# SEC allows 10/sec. We use ~6/sec. The difference costs us seconds and buys
# us not having to think about it.
REQUEST_INTERVAL = 0.17
_last_request = 0.0


def _user_agent() -> str:
    ua = os.getenv("SEC_USER_AGENT", "").strip()
    if not ua or "example.com" in ua:
        raise SystemExit(
            "SEC_USER_AGENT is not set.\n"
            "Copy .env.example to .env and put your real email in it.\n"
            "SEC blocks requests that don't identify a contact."
        )
    return ua


def get(url: str) -> requests.Response:
    """One throttled GET. Every network call in this file goes through here,
    which is the only reliable way to be sure the rate limit is respected."""
    global _last_request
    elapsed = time.monotonic() - _last_request
    if elapsed < REQUEST_INTERVAL:
        time.sleep(REQUEST_INTERVAL - elapsed)
    response = requests.get(url, headers={"User-Agent": _user_agent()}, timeout=30)
    _last_request = time.monotonic()
    response.raise_for_status()
    return response


def resolve_ciks(tickers: list[str]) -> dict[str, dict]:
    """Map tickers to CIKs. The upstream JSON is keyed by meaningless integers
    ("0", "1", "2"...) rather than by ticker, so we have to walk all ~10k
    entries. One request, cached to disk for reuse."""
    cache = RAW_DIR / "company_tickers.json"
    if cache.exists():
        data = json.loads(cache.read_text(encoding="utf-8"))
    else:
        data = get(TICKER_MAP_URL).json()
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(data), encoding="utf-8")

    wanted = {t.upper() for t in tickers}
    found = {}
    for entry in data.values():
        if entry["ticker"] in wanted:
            found[entry["ticker"]] = {"cik": entry["cik_str"], "name": entry["title"]}

    for missing in wanted - found.keys():
        print(f"  ! {missing}: no CIK found (delisted, acquired, or renamed?)")
    return found


def list_filings(cik: int, forms: set[str], per_form: int) -> list[dict]:
    """Recent filings for one company, filtered by form type.

    The response stores filings as PARALLEL ARRAYS -- form[i], filingDate[i],
    and accessionNumber[i] all describe the same filing. It is not a list of
    objects. This is a compact format that is easy to misread, so we zip it
    back into dicts immediately and never think about indices again.
    """
    submissions = get(SUBMISSIONS_URL.format(cik=cik)).json()
    recent = submissions["filings"]["recent"]

    filings = []
    counts = {form: 0 for form in forms}
    for i in range(len(recent["form"])):
        form = recent["form"][i]
        if form not in forms or counts[form] >= per_form:
            continue
        counts[form] += 1
        filings.append(
            {
                "cik": cik,
                "company": submissions["name"],
                "sic": submissions.get("sic"),
                "sic_description": submissions.get("sicDescription"),
                "form": form,
                "filing_date": recent["filingDate"][i],
                "report_date": recent["reportDate"][i],
                "accession": recent["accessionNumber"][i],
                "primary_document": recent["primaryDocument"][i],
            }
        )
    return filings


def download(filing: dict, ticker: str) -> Path | None:
    """Fetch one filing's primary document. Returns None if already on disk.

    Skipping existing files makes this script safe to re-run -- the same
    property you'll want from MERGE in Neo4j later. Re-running an ingestion
    pipeline should be boring, not destructive.
    """
    # The Archives path wants the accession number with dashes stripped, and
    # the CIK WITHOUT zero-padding. Both differ from the submissions endpoint.
    accession_nodash = filing["accession"].replace("-", "")
    url = ARCHIVE_URL.format(
        cik=filing["cik"],
        accession=accession_nodash,
        document=filing["primary_document"],
    )

    out_dir = RAW_DIR / ticker
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{filing['form']}_{filing['filing_date']}_{accession_nodash}.htm"

    if out_path.exists():
        return None

    out_path.write_bytes(get(url).content)
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Download SEC filings from EDGAR.")
    parser.add_argument(
        "--per-company",
        type=int,
        default=1,
        help="How many of EACH form type to fetch per company (default 1).",
    )
    parser.add_argument(
        "--forms",
        nargs="+",
        default=["10-K", "10-Q", "8-K"],
        help="Which form types to fetch.",
    )
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    forms = set(args.forms)

    print(f"Resolving {len(TICKERS)} tickers...")
    companies = resolve_ciks(TICKERS)

    manifest = []
    downloaded = 0
    for ticker, info in sorted(companies.items()):
        filings = list_filings(info["cik"], forms, args.per_company)
        print(f"{ticker:<6} {info['name'][:38]:<40} {len(filings)} filings")

        for filing in filings:
            filing["ticker"] = ticker
            path = download(filing, ticker)
            if path is not None:
                downloaded += 1
                print(f"       + {path.name}")
            else:
                print(f"       . {filing['form']} {filing['filing_date']} (cached)")
            filing["raw_path"] = str(
                RAW_DIR
                / ticker
                / f"{filing['form']}_{filing['filing_date']}_{filing['accession'].replace('-', '')}.htm"
            )
            manifest.append(filing)

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"\n{len(manifest)} filings in manifest, {downloaded} newly downloaded.")
    print(f"Manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
