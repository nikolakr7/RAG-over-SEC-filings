# Ontology v1

Status: DRAFT. Freeze after sanity-check against the benchmark question set.
Changes after freeze require a DECISIONS.md entry.

## Global conventions

1. **Temporal trio.** Anything that unfolds in time (Agreement and LegalCase
   nodes, and every dated edge) carries `start_date`, `end_date` (empty until
   it ends), and `status`. Nothing is ever deleted for changing state
   (DECISIONS.md #3).
2. **Provenance.** Every relationship carries `source_chunk_id`. Reified event
   nodes (Agreement, LegalCase) carry it too (DECISIONS.md #8). Plain entity
   nodes don't; their facts arrive via edges.
3. **Names.** Every node has one canonical `name` plus `aliases[]`. Regional
   brand variants, parenthetical shorthands, and former names are aliases,
   never separate nodes (DECISIONS.md #7).
4. **Definitions are extraction instructions.** Each definition names the
   neighboring type it is most confusable with, so an extractor (human or LLM)
   can decide borderline cases.

## Entity types (9)

### Company
A legal business entity of any kind: drugmaker, auditor, royalty buyer,
generic challenger, financial intermediary. Not a Person; not a brand name.
Properties: name, aliases[], hq_city, former_names[]
Example: Exelixis, Inc. (aliases: "Exelixis", "the Company"; formerly
Exelixis Pharmaceuticals, Inc.)

### Drug
A distinct drug product, marketed or approvable, branded or generic: the
thing that is prescribed and sold. NOT the active molecule inside it (that is
Compound). Different formulations are different Drug nodes; regional names are
aliases on one node.
Properties: name, aliases[], branded (bool)
Examples: CABOMETYX (tablets) and COMETRIQ (capsules), two Drug nodes sharing
one Compound. DARZALEX FASPRO (aliases: "DARZALEX SC", "DARZQURO"), one node,
three regional names.

### Compound
A distinct active molecule or biologic (small molecule, antibody, enzyme)
known by its scientific/generic name, independent of any product containing it
(that is Drug) or platform built on it (that is Technology).
Properties: name, aliases[]
Examples: cabozantinib (small molecule); daratumumab (antibody);
rHuPH20 (enzyme)

### Technology
A named platform, method, or device used to make or deliver drugs: something
licensed or deployed as a capability, not consumed as a molecule (that is
Compound).
Properties: name, aliases[], kind (platform | device)
Examples: ENHANZE (platform, built on rHuPH20); SMARTag (platform);
VIBEX (device)

### Person
An individual human being. Roles, titles, and employers are expressed as
OFFICER_OF edges with dates, never stored on the node.
Properties: name, aliases[]
Example: Michael M. Morrissey (positions live on OFFICER_OF edges to
Exelixis, not here)

### Agreement
A formal arrangement between companies (collaboration, license, option,
supply, asset purchase, acquisition, royalty purchase) reified as a node so
parties, covered assets, territory, and dates attach to one identifiable
thing (DECISIONS.md #2, #5).
Properties: name, type (collaboration | license | option | supply |
asset_purchase | acquisition | royalty_purchase | ...), territory,
start_date, end_date, status, source_chunk_id
Example: Exelixis-Invenra collaboration & license (type: collaboration_license;
start_date: 2018-05; status: active)
Note: ongoing royalty obligations are OWES_ROYALTY_TO edges, not Agreement
properties (DECISIONS.md #10).

### Indication
A disease or medical condition that a drug treats or is being developed to
treat. Nodes stay coarse (the condition); the filing's precise phrasing lives
on the connecting edge's `label` property (DECISIONS.md #11). The node is
"renal cell carcinoma" while the edge label reads "previously treated
advanced RCC".
Properties: name, aliases[]
Example: renal cell carcinoma (aliases: "RCC", "kidney cancer")

### Filing
A document submitted to the SEC via EDGAR (10-K, 10-Q, 8-K). Not a court
document (court matters are LegalCase).
Properties: accession (EDGAR's unique filing id, the natural MERGE key),
type, period_end, date_filed, file_number
Example: Exelixis FY2025 10-K (accession: 0000939767-26-000021; type: 10-K;
period_end: 2026-01-02; date_filed: 2026-02-10)
Note: period_end and date_filed are different facts: the fiscal year the
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
Example: Exelixis v. MSN II. Delaware, filed 2022, ruling Oct 2024, MSN
appealed to CAFC Nov 2024, so still active, no end_date. Consolidation is
expressed with CONSOLIDATED_INTO edges to a LegalCase instance representing
the consolidated matter (DECISIONS.md #9); per-party involvement (Sun
settling Dec 2025) lives on PARTY_TO edges while the case stays active.

## Relationship types (14)

Format per entry: domain -> range, meaning, properties, corpus example.

### PARTY_TO
Company -> Agreement | LegalCase. A party's involvement in a deal or case.
Properties: role, status, start_date, end_date, source_chunk_id
Examples: Sun -PARTY_TO{role: defendant, status: settled,
end_date: 2025-12-30}-> [Consolidated Litigation].
Halozyme -PARTY_TO{role: acquirer}-> [Elektrofi merger agreement]
<-PARTY_TO{role: acquired}- Elektrofi.
OPEN: Person could join the domain if employment agreements ever matter;
for now OFFICER_OF dates cover everything people-related.

### COVERS
Agreement | LegalCase -> Drug | Compound | Technology. The subject matter of
a deal or case: the asset being licensed, developed, purchased, or disputed.
Not the parties (those are PARTY_TO).
Properties: source_chunk_id
(No dates: the event node carries them; duplicating invites contradictions.)
Examples: [Exelixis-Ipsen 2016 agreement] -COVERS-> cabozantinib.
[Halozyme-Roche 2006 agreement] -COVERS-> ENHANZE.
[Consolidated Litigation] -COVERS-> CABOMETYX.

### SUBSIDIARY_OF
Company -> Company. The subject is a subsidiary (or majority-owned unit) of
the object.
Properties: start_date, end_date, status, source_chunk_id
Examples: Halozyme Hypercon, Inc. -SUBSIDIARY_OF{start_date: 2025-11-18}->
Halozyme Therapeutics. ViiV Healthcare -SUBSIDIARY_OF{status: active}-> GSK
(majority ownership).

### AUDITED_BY
Company -> Company. The subject's financial statements are audited by the
object (an accounting firm).
Properties: office, start_year, end_date, status, source_chunk_id
Example: Exelixis -AUDITED_BY{office: "San Mateo, CA", start_year: 2002,
status: active}-> Ernst & Young LLP
(Trio included because auditor changes are a real 8-K event category.)

### OFFICER_OF
Person -> Company. An officer, executive, or board director role at a
company. The role name lives on the edge, never on the Person node.
Properties: role, start_date, end_date, status, source_chunk_id
Examples: Helen Torley -OFFICER_OF{role: "President & CEO",
start_date: 2014-01, status: active}-> Halozyme.
Helen Torley -OFFICER_OF{status: former}-> Bristol-Myers Squibb
(prior employer; dates not stated in the filing, and that is fine).

### CONTAINS
Drug | Technology -> Compound. The object compound is an active component of
the subject.
Properties: source_chunk_id
Examples: Phesgo -CONTAINS-> pertuzumab AND -CONTAINS-> trastuzumab (two
edges, one drug). ENHANZE -CONTAINS-> rHuPH20 (Technology domain exists so
"which products depend on rHuPH20" can traverse Drug -> ENHANZE -> rHuPH20;
see DECISIONS.md #12).

### USES_TECHNOLOGY
Drug | Compound | Technology -> Technology. The subject is built with or
delivered by the object technology.
Properties: source_chunk_id
Examples: DARZALEX FASPRO -USES_TECHNOLOGY-> ENHANZE.
XB010 (a Compound; development-stage ADC) -USES_TECHNOLOGY-> SMARTag.

### APPROVED_FOR
Drug -> Indication. Regulatory approval to market the drug for an indication.
One edge per jurisdiction: approvals are regulator-by-regulator facts.
Properties: jurisdiction, approved_date, label (verbatim filing phrasing,
DECISIONS.md #11), source_chunk_id
Example: CABOMETYX -APPROVED_FOR{jurisdiction: "FDA",
approved_date: 2025-03-26, label: "advanced pancreatic and extra-pancreatic
neuroendocrine tumors"}-> neuroendocrine tumors. The EC approval of the same
pairing (Jul 2025) is a second edge.

### IN_DEVELOPMENT_FOR
Compound | Drug -> Indication. A development program aiming the subject at
the indication, past or present.
Properties: phase, label, start_date, end_date,
status (active | filed | discontinued), source_chunk_id
Examples: zanzalintinib -IN_DEVELOPMENT_FOR{phase: 3, status: filed}->
renal cell carcinoma (NDA filed Dec 2025, PDUFA Dec 2026).
cabozantinib -IN_DEVELOPMENT_FOR{status: discontinued,
end_date: 2025-07}-> metastatic castration-resistant prostate cancer
(CONTACT-02 sNDA abandoned; edge kept per the no-deletion rule).

### OWNS
Company -> Compound | Drug | Technology. The subject owns the asset, whether
developed in-house or acquired.
Properties: source_chunk_id
Examples: Halozyme -OWNS-> ENHANZE. Exelixis -OWNS-> cabozantinib.

### FILED_BY
Filing -> Company. The company that submitted the filing.
Properties: source_chunk_id
Example: [Exelixis FY2025 10-K] -FILED_BY-> Exelixis, Inc.

### CONSOLIDATED_INTO
LegalCase -> LegalCase. The subject case was consolidated into the object
case (which is an ordinary LegalCase instance, not a separate type).
Properties: date, source_chunk_id
Example: [Exelixis v. MSN I] -CONSOLIDATED_INTO{date: 2025-08-08}->
[Consolidated Litigation].

### OWES_ROYALTY_TO
Company -> Company. An ongoing royalty obligation from subject to object,
created by some agreement.
Properties: royalty_rate, basis (what sales it is computed on), territory,
start_date, end_date, status, source_chunk_id
Examples (the GSK reversion takes three edges, which is the point):
Exelixis -OWES_ROYALTY_TO{royalty_rate: "3%", basis: "net sales of
cabozantinib products", territory: "non-US", start_date: 2021-01-01,
status: active}-> Royalty Pharma.
Exelixis -OWES_ROYALTY_TO{royalty_rate: "3%", territory: "US",
start_date: 2021-01-01, end_date: 2026-09, status: active}-> Royalty Pharma.
Exelixis -OWES_ROYALTY_TO{royalty_rate: "3%", territory: "US",
start_date: 2026-09, status: pending}-> GSK.
Also: Ipsen -OWES_ROYALTY_TO{royalty_rate: "22-26% tiered", basis: "ex-US
net sales of cabozantinib products"}-> Exelixis.

### PEER_OF
Company -> Company. The subject names the object in its disclosed
executive-compensation peer group (DEF 14A). Directed: NBIX naming HALO a
peer does not imply the reverse. Peer groups are set annually and change,
so `year` is required. Distinct from competition: peers are comparables
for pay-setting (size, sector, stock profile), and need not compete for a
single patient. Added during the benchmark sanity-check (DECISIONS.md #19).
Properties: year, source_chunk_id
Examples: Neurocrine -PEER_OF{year: 2025}-> Alkermes; Neurocrine
-PEER_OF{year: 2025}-> Ultragenyx (Neurocrine's 2025 group names five corpus
companies; Ionis's names six).
