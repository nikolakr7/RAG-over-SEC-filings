# Corpus sweeps

Machine-extracted reference notes covering all 152 filings (FY2023-FY2025
10-Ks + Exhibit 21s, 10-Qs through mid-2026, 8-Ks, and DEF 14A proxies) for
all 8 corpus companies.

**Standing rule: sweeps are LEADS, never benchmark evidence.** Every fact
used in benchmark/questions.json must be verified against the primary filing
text in data/text/ with a quote. Sweeps can be wrong (see the San Jose
incident in the project history, and the Ingram/Given confusion resolved in
the cross-company index).

## Files

- `cross-company-index.md`: the overlap map (shared auditors, corpus-to-corpus
  deals and litigation, board interlocks, shared counterparties, royalty
  chains). Start here when hunting multi-hop question material.
- `raw/{TICKER}-10K-FY2025.md`: full sweep of each company's latest 10-K
  (EXEL and HALO equivalents live one directory up as docs/sweep-exel.md and
  docs/sweep-halo.md).
- `raw/{TICKER}-10K-deltas.md`: the two older 10-Ks as time-deltas (deal
  changes, subsidiary changes, litigation states, officer changes, auditor
  consistency).
- `raw/{TICKER}-10Q.md`: quarterlies, including 2026 quarters that POSTDATE
  the latest 10-K.
- `raw/{TICKER}-events-people.md`: 8-K events plus director/officer bios
  from proxies (prior employers, other board seats).
