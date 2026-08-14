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