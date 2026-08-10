# Ontology v1

Status: DRAFT — freeze after sanity-check against the benchmark question set.
Changes after freeze require a DECISIONS.md entry.

## Global conventions

1. **Temporal trio.** Anything that unfolds in time — Agreement and LegalCase
   nodes, and every dated edge — carries `start_date`, `end_date` (empty until
   it ends), and `status`. Nothing is ever deleted for changing state
   (DECISIONS.md #3).
2. **Provenance.** Every relationship carries `source_chunk_id`. Reified event
   nodes (Agreement, LegalCase) carry it too (DECISIONS.md #8). Plain entity
   nodes don't — their facts arrive via edges.
3. **Names.** Every node has one canonical `name` plus `aliases[]`. Regional
   brand variants, parenthetical shorthands, and former names are aliases —
   never separate nodes (DECISIONS.md #7).
4. **Definitions are extraction instructions.** Each definition names the
   neighboring type it is most confusable with, so an extractor (human or LLM)
   can decide borderline cases.

## Entity types (9)

### Company
A legal business entity of any kind — drugmaker, auditor, royalty buyer,
generic challenger, financial intermediary. Not a Person; not a brand name.
Properties: name, aliases[], hq_city, former_names[]
Example: Exelixis, Inc. (aliases: "Exelixis", "the Company"; formerly
Exelixis Pharmaceuticals, Inc.)

### Drug
A distinct drug product — marketed or approvable, branded or generic — the
thing that is prescribed and sold. NOT the active molecule inside it (that is
Compound). Different formulations are different Drug nodes; regional names are
aliases on one node.
Properties: name, aliases[], branded (bool)
Examples: CABOMETYX (tablets) and COMETRIQ (capsules) — two Drug nodes sharing
one Compound. DARZALEX FASPRO (aliases: "DARZALEX SC", "DARZQURO") — one node,
three regional names.

### Compound
A distinct active molecule or biologic — small molecule, antibody, enzyme —
known by its scientific/generic name, independent of any product containing it
(that is Drug) or platform built on it (that is Technology).
Properties: name, aliases[]
Examples: cabozantinib (small molecule); daratumumab (antibody);
rHuPH20 (enzyme)

### Technology
A named platform, method, or device used to make or deliver drugs — something
licensed or deployed as a capability, not consumed as a molecule (that is
Compound).
Properties: name, aliases[], kind (platform | device)
Examples: ENHANZE (platform, built on rHuPH20); SMARTag (platform);
VIBEX (device)

### Person
An individual human being. Roles, titles, and employers are expressed as
OFFICER_OF edges with dates — never stored on the node.
Properties: name, aliases[]
Example: Michael M. Morrissey — positions live on OFFICER_OF edges to
Exelixis, not here.

### Agreement
A formal arrangement between companies — collaboration, license, option,
supply, asset purchase, acquisition, royalty purchase — reified as a node so
parties, covered assets, territory, and dates attach to one identifiable
thing (DECISIONS.md #2, #5).
Properties: name, type (collaboration | license | option | supply |
asset_purchase | acquisition | royalty_purchase | ...), territory,
start_date, end_date, status, source_chunk_id
Example: Exelixis–Invenra collaboration & license (type: collaboration_license;
start_date: 2018-05; status: active)
Note: ongoing royalty obligations are OWES_ROYALTY_TO edges, not Agreement
properties (DECISIONS.md #9).

### Indication
A disease or medical condition that a drug treats or is being developed to
treat. Nodes stay coarse (the condition); the filing's precise phrasing lives
on the connecting edge's `label` property (DECISIONS.md #10) — e.g. the node
is "renal cell carcinoma" while the edge label reads "previously treated
advanced RCC".
Properties: name, aliases[]
Example: renal cell carcinoma (aliases: "RCC", "kidney cancer")

### Filing
A document submitted to the SEC via EDGAR (10-K, 10-Q, 8-K). Not a court
document — court matters are LegalCase.
Properties: accession (EDGAR's unique filing id — the natural MERGE key),
type, period_end, date_filed, file_number
Example: Exelixis FY2025 10-K (accession: 0000939767-26-000021; type: 10-K;
period_end: 2026-01-02; date_filed: 2026-02-10)
Note: period_end and date_filed are different facts — the fiscal year the
content describes vs. the day it became public. Both are in
data/raw/manifest.json.

### LegalCase
A legal dispute (lawsuit, ANDA challenge, regulatory proceeding) involving
one or more parties, typically over a drug or patent.
Properties:
  name            e.g. "Exelixis v. MSN (MSN II)"
  court           e.g. "Delaware District Court", "D.N.J."
  case_number     e.g. "C.A. 22-00228" (when stated)
  filed_date      complaint filing date
  trial_date      scheduled trial, if set
  end_date        empty until the whole matter resolves
  status          active | resolved
  notice_date     OPEN: Paragraph IV notice date, ANDA cases only
  source_chunk_id
Example: Exelixis v. MSN II — Delaware, filed 2022, ruling Oct 2024, MSN
appealed to CAFC Nov 2024 → still active, no end_date. Consolidation is
expressed with CONSOLIDATED_INTO edges to a LegalCase instance representing
the consolidated matter (DECISIONS.md #11) — per-party involvement (Sun
settling Dec 2025) lives on PARTY_TO edges while the case stays active.

## Relationship types (13) — TODO: entries drafted by hand, reviewed next

PARTY_TO, COVERS, SUBSIDIARY_OF, AUDITED_BY, OFFICER_OF, CONTAINS,
USES_TECHNOLOGY, APPROVED_FOR, IN_DEVELOPMENT_FOR, OWNS, FILED_BY,
CONSOLIDATED_INTO, OWES_ROYALTY_TO

Format per entry: domain → range, one-line meaning, properties, one corpus
example. Two worked examples to match:

### AUDITED_BY
Company → Company. The subject's financial statements are audited by the
object (an accounting firm).
Properties: office, since_year, source_chunk_id
Example: Exelixis —AUDITED_BY{office: "San Mateo, CA", since: 2002}→
Ernst & Young LLP

### PARTY_TO
Company → Agreement | LegalCase. A party's involvement in a deal or case.
Properties: role, status, start_date, end_date, source_chunk_id
Example: Sun —PARTY_TO{role: defendant, status: settled,
end_date: 2025-12-30}→ [Consolidated Litigation]
