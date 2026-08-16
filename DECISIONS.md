1. Auditors are Company nodes; office is an edge property (rejected: office nodes — nothing else connects to an office)
2. Agreements and legal cases are reified nodes; PARTY_TO with role covers both (rejected: pairwise edges with correlation tags)
3. Nothing is deleted for changing state — status + end date instead (the Sun-settlement rule)
4. Hop counts in the benchmark are semantic, not physical (agreement nodes add physical hops)
5. Acquisitions are Agreements with type: acquisition (rejected: bare ACQUIRED edge — consistency with reification)
6. One OFFICER_OF with start/end dates covers current and former roles (rejected: separate PREVIOUSLY_AT)
7. Regional brand names are aliases on one Drug node, never separate nodes
8. reified event nodes (Agreement, LegalCase) carry their own source_chunk_id, since their attributes are extracted claims just like edges are.
9. one node per original case + CONSOLIDATED_INTO edges to a LegalCase instance representing the consolidated matter; rejected: merged single node, because MSN I and MSN II carry different rulings with different approval-gate dates.
10. royalty obligations are OWES_ROYALTY_TO edges (rejected: royalty_terms text property on Agreement — we wanted traversable royalty flows).
11. Indication nodes stay coarse; the filing's verbatim phrasing lives on the edge's label property.
12. CONTAINS range widened to Drug | Technology -> Compound so ENHANZE can contain rHuPH20; rejected: a separate BASED_ON edge.
13. Hop labels reflect evidence dispersion, not ontology path length: a question is multi-hop only if its supporting facts live in separate passages. (Rejected: counting path hops, which let single-passage proxy-bio joins masquerade as 2-hop.)
14. Specificity lives in the answer, not the question: questions carry natural intent with minimal lexical giveaways; answers stay precise for grading. (Rejected: clue-style phrasing, which hands vector retrieval exact keywords and inflates its baseline.)
15. ontology_path is checked for validity, not exhaustiveness
16. Answer scope equals question scope, no more no less.
17. Default all-required for benchmark answers; open questions carry an explicit required_core; judge grades against core when present, full answer otherwise.
18. Content claims need quotes; provenance claims are supported by evidence metadata; absence claims ("first," "no longer," "only in") are verified by negative search, not quotation
19. PEER_OF added as the 14th relationship type (Company -> Company, directed, with year): the first live ontology sanity-check finding. Three benchmark questions traverse compensation peer groups and no existing edge could express "a company merely referred to by another's filing." Sweep and drafting agents had used PEER_OF as if it existed; the "paths use only terms in ontology.md" rule caught it. (Rejected: routing through Filing with a MENTIONS_PEER edge, which is still a new edge type, just an awkward one.)
20. Ontology paths use only terms defined in ontology.md; a path needing an undefined term is an ontology gap to surface, not a synonym to invent. Canonical names are perspective-neutral (royalty_purchase, not royalty_sale); direction lives on PARTY_TO roles.
21. Competitor mentions are NOT an edge type for now (no COMPETES_WITH); competitor questions are left to the vector path, which handles single-passage competitor lists well. Trigger for revisiting: a plausible question that needs the GRAPH to answer it (multi-hop through competition). Reasons for deferring: competitor lists are extraction-noisy (hedged "may compete with" language) and would roughly double Company nodes with non-corpus entities, the largest single amplifier of entity-resolution workload. Idempotent MERGE ingestion makes adding it later cheap.
22. Edge types are added on demand, where demand means "a plausible question needs the graph to answer it," not merely "a benchmark question needs it": the benchmark is a biased sample of real questions, and the vector path backstops single-passage facts the graph lacks.