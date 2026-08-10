# Reader's guide: biotech 10-Ks

The ~15 recurring constructs that generate most of the confusion in these
filings, each with a verdict on whether it matters for the graph. Keep this
open in a split pane while reading. If a passage doesn't map to one of these
and still confuses you, mark it `???` with a line number and batch it to
Claude at the end of the section.

## Deal structures (the heart of the graph)

**Collaboration agreement** — two companies jointly develop and/or sell a
drug, splitting costs and profits. Usually involves an upfront payment plus
milestones plus royalties. *Graph: YES — this is a core edge between two
companies, about a specific drug.*

**License agreement** — company A grants company B rights to develop/sell
A's compound, almost always limited by territory ("ex-U.S. rights",
"in Japan"). "Out-license" = we granted rights; "in-license" = we bought
rights. *Graph: YES — LICENSED_TO edges with drug + territory. Territory is
what makes "who sells drug X in Europe?" answerable.*

**Royalty** — a % of sales paid to a rights-holder, often continuing long
after the original deal ended. Key twist: a royalty stream is an asset that
can itself be SOLD to a third party (Royalty Pharma's entire business model
is buying them). So "who receives the royalty" can change hands on a date.
*Graph: YES — and it's the best source of dated, transferred edges.*

**Milestone payments** — one-time payments triggered by events: regulatory
approval, first commercial sale, hitting a sales threshold. *Graph: usually
just attributes on the license/collaboration edge, not their own thing.*

## Drugs and regulation

**Compound vs. brand** — one molecule (cabozantinib) can be sold as multiple
branded products (CABOMETYX, COMETRIQ), sometimes with different indications
or formulations. The ® symbol marks a brand name. *Graph: real ontology
decision — you already found it.*

**Indication** — the disease a drug is approved for or being tested against.
One drug accumulates indications over time, each via its own approval.
*Graph: probably YES — "approved for renal cell carcinoma" is a hop worth
having.*

**Trial/approval pipeline vocab** — Phase 1 → 2 → 3 trials, then an NDA
(small molecules) or BLA (biologics) filed with the FDA, then approval.
"Pivotal trial" = the one designed to support approval. *Graph: development
stage works fine as a property; don't make Phase 3 a node.*

**ANDA litigation / Paragraph IV** — a generic drugmaker files an
"Abbreviated New Drug Application" to sell a copy before the patents expire,
claiming the patents are invalid. The brand company then sues. You'll see
lists of generic challengers in Legal Proceedings. *Graph: it's a real
company-vs-company-over-drug edge; fine to note, fine to defer to v2.*

## Corporate structure

**Auditor** — the accounting firm that signs the audit, found in the "Report
of Independent Registered Public Accounting Firm" (searchable string). Only
four big firms audit most public companies, so overlaps across your eight
companies are near-guaranteed. The office CITY under the signature matters —
same firm, different offices is a real distinction. *Graph: YES — AUDITED_BY
is your most reliable cross-company edge.*

**Subsidiaries** — legal entities the company owns, listed in Exhibit 21.1.
NOTE: that exhibit is a separate file our downloader doesn't fetch yet, so
don't hunt for the list in the text — it isn't there.

**Segments** — how the company divides itself for financial reporting. Most
biotechs report exactly one segment, making this useless for the graph.
*Graph: skip.*

**"Incorporated by reference"** — legalese for "this information lives in a
different filing" (usually the annual proxy statement, form DEF 14A). This is
why officer and director bios are mostly ABSENT from the 10-K itself.
*When you see it: stop looking, the content is not in this document.*

## Money & accounting (almost all skippable)

**Restructuring / impairment** — accounting recognition of layoffs, exited
leases, written-down assets. *Graph: skip.*

**ATM offering / shelf registration** — mechanisms for selling new stock to
raise cash. *Graph: skip.*

**RSUs / stock-based compensation** — paying employees in stock. Generates
pages of tables. *Graph: skip.*

**Deferred revenue / milestone revenue recognition** — accounting for WHEN
deal money counts as revenue (the deal itself matters; the accounting for it
doesn't). *Graph: skip — but the deal being accounted for is often described
nearby and IS worth reading.*

## Whole sections you can skip without guilt

- "Forward-looking statements" disclaimer (~2 pages of legal boilerplate, in every filing)
- Item 5 (market for stock), Item 6 (reserved/selected data)
- Item 7A (quantitative market risk)
- Item 8 financial statement NUMBERS — except the audit report at the front of them (auditor name + city)
- Item 9/9A (controls and procedures)
- Part III entirely (it's all "incorporated by reference")

## Alias patterns to note when you see them

- "we / our / us / the Company" = the filer
- "(the 'XYZ Agreement')" — filings define shorthand on first use, then use it for 100 pages
- Parenthetical abbreviations: "GlaxoSmithKline (GSK)" — note both forms
- Former names: "formerly known as..." — gold, always note
