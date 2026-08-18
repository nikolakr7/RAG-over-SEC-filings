# Pre-check worksheet: q030-q068 (unverified questions)

Prepared 2026-08-16 by Claude as an aid to the user's hand verification.
This is NOT verification. Every quote below still has to be seen in the
primary file by the user before `verified` flips. Nothing in
questions.json was edited.

Method: (1) every evidence quote was located mechanically in data/text/
(whitespace-tolerant, ellipsis segments matched separately), (2) every
ontology_path term was checked against ontology.md, (3) each located
passage was read against the verification rules in HANDOFF.md
(DECISIONS #15-22) and against nearby corpus text via targeted greps.

Results of the mechanical passes: all 113 quotes for q030-q068 locate in
the named filing; all path terms are defined in ontology.md. The
remaining findings are content and rule findings, listed per question.

Severity key: HIGH = answer contradicts or under-reports the corpus,
MEDIUM = scope/tense/provenance rule issue that would misgrade a correct
system answer, LOW = quote hygiene or an optional required_core.

File refs are `TICKER/file:line` under data/text/.

---

## q030  MEDIUM
Refs: ev1 HALO/10-K_2026-02-17:1880; ev2 ALKS/10-K_2026-02-25:10173
- The Halozyme half names only the Hypercon license. The same HALO
  passage (line 1880, two sentences earlier) says Janssen is an ENHANZE
  partner with two commercial products (DARZALEX FASPRO), which is the
  larger and older Janssen connection. A system answering "ENHANZE" would
  be correct and would fail against this answer. q050 (the 3-hop twin of
  this question) uses the ENHANZE/DARZALEX connection, so the two
  answers are inconsistent with each other. Suggest widening the answer
  to name both, or a required_core that accepts either.
- The $195.4 million award is not quoted. The FY2025 ALKS 10-K carries
  the award sentence directly after ev2 (line 10173-10178: "the Final
  Award provided ... that the Company was due back royalties of $195.4
  million"). Extend the quote.
- Near-duplicate of q050 (same two connections plus leadership). Flag for
  the user's decision; earlier audits cut such pairs.
- APPLIED 2026-08-16 on the user's instruction: answer widened to name
  the ENHANZE license (two commercial products incl. DARZALEX FASPRO)
  plus Hypercon; ALKS quote extended through the $195.4 million / $8.1
  million award sentence (all fragments on line 10173). Also, so every
  claim has a quote: added HALO quotes for the ENHANZE list (1879) and
  DARZALEX FASPRO (1979), extended the Hypercon quote to start at
  "Through our recent acquisition of Elektrofi" (1880), and added the
  ENHANZE agreement to ontology_path. `verified` left false for the
  user's own check. Open: q050 near-duplicate decision.
- APPLIED (same day): required_core added (disjunctive on the Halozyme
  side, dollar figure not required); ontology_path rewritten with
  directed PARTY_TO edges carrying roles (licensor/licensee,
  claimant/respondent), Agreement types, and the underlying
  NANOCRYSTAL/INVEGA license Agreement (status: active) alongside the
  resolved arbitration LegalCase.

## q031  OK (answer); path rewritten
Refs: ev1 EXEL/10-K_2026-02-10:1639; ev2 HALO/10-K_2026-02-17:1939
- Both halves report deal type + asset (symmetry rule met).
- APPLIED 2026-08-16 on the user's instruction: ontology_path rewritten
  from two undirected PARTY_TO stubs to directed edges with roles and
  Agreement types, plus the edges the answer actually asserts: COVERS to
  cabozantinib/atezolizumab and to ENHANZE, Roche -OWNS-> atezolizumab,
  Roche -OWES_ROYALTY_TO-> HALO, Phesgo -USES_TECHNOLOGY-> ENHANZE,
  Phesgo -APPROVED_FOR{Japan}-> HER2+ breast cancer, and
  Chugai -SUBSIDIARY_OF-> Roche (corpus phrase is "a member of the Roche
  Group"; mapping to SUBSIDIARY_OF follows the ontology's ViiV/GSK
  majority-ownership example). Company(Roche) is one node in both halves
  (both filings name F. Hoffmann-La Roche Ltd), which is the join.

## q032  LOW
Refs: ev1 ALKS/DEF14A_2026-04-06:4784; ev2 ARWR/DEF14A_2026-01-27:658
- Quotes lack subject identity: ev1 never says Reed is CFO / appointed
  September 2025 (the header eight lines above does: "Joshua Reed, Senior
  Vice President, Chief Financial Officer, Appointment to Current
  Position(s): September 2025"); ev2 starts "He spent..." and never names
  Olukotun or his directorship (header at line 638-646: "Adeoye Olukotun,
  MD, MPH, Independent Director, Director since: 2020"). Prepend both.

## q033  HIGH
Refs: ev1 HALO/10-K_2026-02-17:1879; ev2 EXEL/10-K_2026-02-10:1749
- "which other corpus company has its own direct Takeda deal?" has three
  answers, not one: Exelixis (cabozantinib Japan, 2017), Neurocrine (2020
  Takeda license, osavampator; the subject of q036/q048), and Arrowhead
  (Exclusive License and Co-Funding Agreement with Takeda Pharmaceuticals
  U.S.A., Inc., dated October 7, 2020, fazirsiran/ARO-AAT; ARWR
  10-K_2025-11-25, several passages incl. the exhibit index and the
  pipeline list "fazirsiran (formerly ARO-AAT, a collaboration with
  Takeda)"). Answer under-reports; either pluralize the question and list
  all three, or narrow the question to Exelixis explicitly.
- "showing Baxalta folded into Takeda" is an inference. The HALO 10-K
  only shows the joint naming; no corpus sentence explains why. Trim to
  what is quoted or accept as inference; the path's
  `Company(Baxalta US Inc.) -SUBSIDIARY_OF-> Company(Takeda)` also has
  no supporting sentence.
- APPLIED 2026-08-16: user pluralized the second half of the question;
  answer now names Exelixis, Neurocrine (2020 Takeda license, osavampator)
  and Arrowhead (Oct 2020 Exclusive License and Co-Funding Agreement,
  fazirsiran/ARO-AAT) with NBIX/10-K_2026-02-11:5464 and
  ARWR/10-K_2025-11-25:5697 quotes; Baxalta half trimmed to what the filing
  shows (one defined term covering two legal entities; no corporate
  history stated); required_core added; path rewritten per #23 with both
  Takeda entities as PARTY_TO licensees and no SUBSIDIARY_OF. Open: the
  "Why" wording still invites an outside-knowledge answer (Takeda's
  acquisition of Shire/Baxalta), which the corpus cannot supply.

## q034  LOW
Refs: ev1 SRPT/10-K_2026-03-02:2466; ev2 :2476; ev3 ARWR/10-K_2025-11-25:3091
- ev3 does not carry the deal name (it sits under a "Sarepta:" heading).
  A cleaner sentence exists at ARWR/10-K_2025-11-25:3334: "resulting from
  the recognition of $696.8 million in revenue under the Sarepta
  Collaboration Agreement". Suggest swapping.
- Deal-value rule respected (upfront and equity stated separately).

## q035  LOW (hop label)
Refs: ev1 HALO/10-K_2026-02-17:1954; ev2 :1963
- Both facts sit in the same "Takeda Collaboration" section nine lines
  apart. Under the evidence-dispersion rule this is borderline 2-hop; a
  chunker will probably split them, but note it.

## q036  HIGH
Refs: ev1 NBIX/10-K_2026-02-11:1127; ev2 :5469
- Answer says "Originally in-licensed ... with worldwide rights except
  Japan". That is the CURRENT state (ev1 is present tense in the FY2025
  10-K). ev2 itself says the January 2025 restatement included "the
  return of rights to osavampator in Japan to Takeda", and the pre-
  restatement 10-Q (NBIX/10-Q_2024-10-30) describes the 2020 grant as
  "exclusive rights to develop and commercialize" with no Japan carve-
  out. So the original license included Japan; the answer contradicts
  its own second sentence. Fix: "Originally in-licensed in 2020 with
  exclusive rights under a profit-and-loss-sharing structure; in January
  2025 the deal was amended and restated: profit-sharing became a
  royalty-bearing license and Japan rights returned to Takeda, leaving
  Neurocrine worldwide rights except Japan."

## q037  LOW
Refs: ev1 NBIX/10-Q_2024-10-30:1743; ev2 NBIX/10-K_2025-02-10:2115
- Absence claim ("no longer mentioned in the FY2025 10-K") verified:
  0 hits for "Idorsia" in NBIX/10-K_2026-02-11.
- "In the fourth quarter of 2024 Neurocrine gave Idorsia written notice"
  is in the 10-Q sentence right after ev1 but not quoted; extend ev1.

## q038  MEDIUM
Refs: ev1 SRPT/10-K_2025-02-28:2212; ev2 SRPT/10-K_2026-03-02:3713; ev3 :2409
- "with no safety caveats" is too strong: the ev1 passage itself states
  a contraindication (exon 8/9 deletions), and the FY2024 risk factors
  mention gene-therapy adverse events generically. What IS verifiably
  absent from the FY2024 10-K: "liver failure" (0), "boxed warning" (0),
  "passed away" (0), "acute serious liver injury" (0). Rephrase the
  absence claim to those specifics.
- The June 15, 2025 second death and the November 2025 boxed warning are
  in the answer but only in the context of ev2/ev3, not in the quotes;
  extend ev2 (next sentence) and ev3 ("In November 2025, we announced a
  boxed warning ...").
- APPLIED 2026-08-16: absence claim narrowed to "mentions no patient
  deaths, shipment suspension, or boxed warning" (each grep-verified at 0
  hits in the FY2024 10-K); ev1 extended with the non-ambulatory
  accelerated-approval sentence; ev2 extended with the June 15, 2025
  second death; ev3 extended with the November 2025 boxed-warning
  sentence; required_core added; path rewritten per #23 (APPROVED_FOR with
  label as of each 10-K, OWNS, two Filing nodes).

## q039  LOW
Refs: ev1 ALKS/10-K_2025-02-12:13763 (last fragment matched at 12756);
ev2 ALKS/10-Q_2025-10-28:5858
- ev1's final fragment "for VUMERITY" is not verbatim in the passage
  (the sentence reads "a generic version of VUMERITY"); fix the fragment.
- "bench trial set for July 28, 2025" is unquoted; the FY2024 10-K has
  "A bench trial is scheduled to begin on July 28, 2025." (same section).
- Absence claim verified: 0 hits for "Zydus" in ALKS/10-K_2026-02-25.

## q040  MEDIUM
Refs: ev1 IONS/8-K_2026-07-09:125; ev2 :129; ev3 IONS/8-K_2026-07-10:105
- The guidance-reaffirmation sentence is outside the question's scope
  (trial outcome). Under all-required grading a correct trial-outcome
  answer would fail. Two ways out: trim it (but then ev1+ev2 are one
  passage and the question becomes single-hop by the dispersion rule),
  or widen the question ("...and did Ionis change its 2026 guidance
  afterward?") to keep the 2-hop, two-8-K structure. Recommend widening.

## q041  HIGH
Refs: ev1 NBIX/8-K_2026-05-18:181; ev2 NBIX/10-Q_2026-07-31:2486
- The 10-Q attributes the funding elsewhere: "Cash paid for the
  acquisition, net of cash acquired, was approximately $2.36 billion and
  was funded from available liquidity, including cash on hand and
  proceeds from sales and maturities of available-for-sale debt
  securities" (liquidity section), and "liquidation of a significant
  portion of our debt security investments to fund the acquisition of
  Soleno in May 2026". The answer presents the revolver as the financing.
  The revolver facts are true and quotable ("In May 2026, we borrowed
  $600.0 million under the 2026 Credit Facility, and in June 2026, we
  repaid $600.0 million of principal"; "five-year"), but the answer needs
  to lead with cash on hand plus securities sales and present the $600M
  draw as concurrent, repaid in June. Currently the $600M draw/repay and
  "five-year" claims are unquoted; add those quotes too.
- APPLIED 2026-08-16: answer now leads with funding from cash on hand
  and sales/maturities of AFS debt securities (~$2.9B aggregate cash,
  ~$2.36B net of cash acquired), revolver presented as concurrent
  ($600.0M borrowed May 2026, repaid June 2026, nothing outstanding at
  June 30). Quotes added: NBIX/8-K_2026-05-18:211 ("funded by the Company
  from its available cash on hand"), NBIX/10-Q_2026-07-31:4021 (funding
  sentence) and :3935 (five-year facility; borrow/repay). required_core
  added. Path per #23: acquisition Agreement (effective_date, completed),
  Payment(consideration) PAID_UNDER it, Agreement(2026 Credit Facility,
  type: credit_facility) with borrower/administrative-agent roles, two
  Filing nodes. `credit_facility` added to ontology.md's Agreement type
  list (the old path had invented "supply/financing").

## q042  OK
Refs: ev1 HALO/10-K_2026-02-17:1879; ev2 :2009; ev3 EXEL/10-K_2026-02-10:5113; ev4 :1741

## q043  LOW
Refs: ev1 IONS/10-K_2026-02-26:4623; ev2 EXEL/10-K_2026-02-10:1740; ev3 :1740
- The Ionis sentence restates the premise; the question asks only about
  permanence of the Exelixis stream. Add required_core: "No. The U.S.
  leg of the cabozantinib royalty reverts to GSK after September 2026
  (non-U.S. is for the full term)."
- "January 2023" is not in the IONS quote (q007 has the dated exhibit
  line if wanted).

## q044  MEDIUM
Refs: ev1 ARWR/10-K_2025-11-25:3684; ev2 :5727; ev3 :1665
- "That license ended and rights returned to Arrowhead" is unquoted, and
  no ARWR filing in the corpus (FY2023, FY2024, FY2025 10-Ks, 10-Qs) says
  it; they only say the asset "had previously been licensed to Janssen in
  October 2018" and that GSK received a worldwide exclusive license on
  December 11, 2023. The only Janssen termination sentence in the corpus
  is about ARO-PNPLA3 (April 7, 2023), a different asset. Either soften
  to what the filings state or accept as a labeled inference.

## q045  MEDIUM
Refs: ev1 ARWR/DEF14A_2025-01-29:517; ev2 ARWR/10-K_2025-11-25:3346; ev3 :3346
- Answer says Ingram "is also an Arrowhead director" (present tense);
  the corpus says he served February 2025 to March 2026 (SRPT
  DEF14A_2026-04-24:991, already quoted in q064 ev3; ARWR
  DEF14A_2026-01-27:550 says he retired at the March 2026 meeting). The
  question's "spent a year" is right; the answer is stale. Fix tense and
  reuse the q064 quotes.
- ev1 is a nominee bio from before he joined (the same proxy says he "is
  expected to be appointed to the board before our 2025 Annual
  Meeting"). Weak evidence for "director"; replace with the q064 quotes.
- Consistent with verified q014 (joined effective February 2025).

## q046  MEDIUM
Refs: ev1 IONS/DEF14A_2026-04-23:933; ev2 :933; ev3 HALO/10-K_2026-02-17:1979
- "Does Janssen also do business with any other company in this corpus?"
  has a second correct answer: Alkermes (NanoCrystal/INVEGA license,
  RISPERDAL CONSTA supply, arbitration; q030/q050 material). A system
  naming Alkermes would fail. Add required_core accepting Halozyme or
  Alkermes, or widen the answer to name both.

## q047  OK
Refs: ev1 IONS/DEF14A_2026-04-23:937; ev2 HALO/10-K_2026-02-17:1879; ev3 :2011

## q048  OK
Refs: ev1 NBIX/10-K_2026-02-11:5464; ev2 HALO/10-K_2026-02-17:1963

## q049  LOW
Refs: ev1 SRPT/10-K_2026-03-02:7614; ev2 ARWR/10-K_2025-11-25:4022; ev3 :3346
- ev1 lacks the firm name (the "/s/ KPMG LLP" line immediately precedes
  it); prepend it.
- The auditor sentences restate the premise; the question asks about a
  direct relationship. Add required_core: "Yes: a licensing and
  collaboration agreement signed November 25, 2024."

## q050  MEDIUM
Refs: ev1 ALKS/10-K_2025-02-12:10764 (fragment "the Tribunal" matched at
12716); ev2 HALO/10-K_2026-02-17:1979; ev3 HALO/8-K_2026-04-30:74,76
- Answer starts "Yes." but the question is a "What are..." question:
  rephrase orphan. Drop "Yes."
- ev1 is stitched: at line 10764 the text reads `(the "Tribunal")`, so
  the fragment "the Tribunal" is not verbatim there. Use the clean
  sentence at 10764: "In May 2023, the arbitral tribunal (the
  "Tribunal") in the arbitration proceedings issued a final award (the
  "Final Award") which concluded the arbitration proceedings. The Final
  Award provided, among other things, that the Company was due back
  royalties of $195.4 million, inclusive of $8.1 million in late-payment
  interest related to 2022 U.S. net sales of the long-acting INVEGA
  products". Same fix applies to q053 ev2 (identical quote).
- Near-duplicate of q030 (see there).

## q051  OK
Refs: ev1 ALKS/10-K_2026-02-25:8577; ev2 :2318; ev3 :2318
- Minor: royalty is 3.85% "on net sales of LUMRYZ sold for narcolepsy"
  (plus other royalties for future non-narcolepsy indications); the
  answer's "on net sales of LUMRYZ" is slightly broader than the quote.

## q052  LOW
Refs: ev1 EXEL/10-K_2026-02-10:4347; ev2 HALO/10-K_2026-02-17:2813
- The Genentech-to-Roche link is in the corpus but unquoted: EXEL 10-K
  "marketed under a collaboration with Genentech, Inc. (a member of the
  Roche Group)". Add it; Halozyme's 10-K names Roche, not Genentech, as
  the ENHANZE partner (Genentech appears only for RITUXAN HYCELA and in a
  bio).
- "which of its products uses that technology": Phesgo is one of
  several (Herceptin SC/Hylecta, MabThera SC, Ocrevus Zunovo, Tecentriq
  Hybreza). Add required_core accepting any Roche ENHANZE product.

## q053  LOW
Refs: ev1 NBIX/DEF14A_2026-04-15:721; ev2 ALKS/10-K_2025-02-12:10764
- ev2 stitched-quote fix as in q050.

## q054  LOW
Refs: ev1 ALKS/10-K_2026-02-25:2421; ev2 IONS/10-K_2026-02-26:787; ev3 :789
- ev1 starts mid-sentence at "we granted"; start at "Under a license and
  collaboration agreement with Biogen, we granted ...".

## q055  MEDIUM
Refs: ev1 EXEL/10-K_2026-02-10:1684; ev2 HALO/10-K_2026-02-17:2746
- "both ultimately part of the Merck & Co. corporate family" is not in
  the corpus. The EXEL 10-K uses "Merck & Co., Inc." for pembrolizumab
  and competitor lists and "MSD International Business GmbH, known as
  Merck within the United States and Canada (Merck)" for the collaborator
  (a third naming), and HALO uses "Merck Sharp & Dohme Corp. ("Merck")".
  Nothing ties them together. Trim the family sentence or set
  required_core to the two entity names.
- Good entity-resolution test question otherwise (see HANDOFF "three
  distinct Merck entities").

## q056  LOW
Refs: ev1 EXEL/10-K_2026-02-10:7281; ev2 RARE/10-K_2026-02-18:4180; ev3 :1855
- "lead product" is unquoted (the RARE 10-K lists Crysvita first under
  Approved Products; it does not call it the lead product). Either name
  Crysvita in the question or accept.
- Near-duplicate of verified q022 plus one hop; flag for the user.

## q057  OK
Refs: ev1 SRPT/10-Q_2025-11-06:4089; ev2 :9348; ev3 ARWR/10-K_2025-11-25:2984; ev4 SRPT/10-K_2026-03-02:2467
- The two-filer date discrepancy (Nov 20 vs Nov 24, 2025) is real and
  quoted on both sides. Path is free text; acceptable under DECISIONS #15.

## q058  MEDIUM
Refs: ev1 EXEL/10-K_2026-02-10:7008
- Same 10-K: "On December 30, 2025, in accordance with the Sun Settlement
  Agreement, Sun was dismissed from the Consolidated Litigation" (lines
  7013 and 7017). "Had sued" makes the
  three-name answer defensible, but a system answering "MSN and Azurity
  (Sun settled and was dismissed)" would be at least as correct. Add the
  dismissal to the answer and quote it, or set required_core.

## q059  OK
Refs: ev1 EXEL:3239; ev2 RARE:5555; ev3 HALO:3876; ev4 IONS:6112; ev5 NBIX:2523 (all latest 10-Ks)
- Negative side (SRPT KPMG, ARWR KPMG, ALKS PwC) is covered by q062.

## q060  OK
Refs: ev1 EXEL/10-K_2026-02-10:1741; ev2 IONS/10-K_2026-02-26:4623; ev3 ARWR/10-K_2025-11-25:7520; ev4 RARE/10-K_2026-02-18:1975

## q061  LOW
Refs: ev1 HALO/10-K_2026-02-17:3870; ev2 ALKS/10-K_2026-02-25:4817; ev3 NBIX/8-K_2026-05-18:181
- ev2 is oblique (bridge-loan termination); the direct sentence is
  ALKS/10-K_2026-02-25:8577 (q051 ev1). Swap.
- Negative side checked by grep: no completed acquisitions 2025-2026 in
  EXEL, IONS, SRPT, ARWR, RARE filings (SRPT's Myonexus is 2019; ARWR's
  hit is Amgen acquiring Horizon). Halozyme also closed Surf Bio (Dec
  2025): count of companies stays 3, count of deals would be 4; consider
  noting Surf Bio in the answer.

## q062  OK
Refs: ev1 EXEL:3239; ev2 SRPT:7612; ev3 ALKS/10-K_2026-02-25:5744; ev4 ARWR/10-K_2025-11-25:4051

## q063  OK
Refs: IONS/DEF14A_2026-04-23:3048-3184 (six rows of the 2025 Peer Group table)
- Arrowhead confirmed absent from the table.

## q064  MEDIUM
Refs: ev1 NBIX/DEF14A_2026-04-15:721; ev2 SRPT/DEF14A_2026-04-24:991; ev3 :991; ev4 ARWR/DEF14A_2026-01-27:550
- Tense: the question asks "Do any individuals hold..." (present) but
  Ingram's overlap ended March 2026. Either rephrase to "Have any
  individuals held ... concurrently, per these filings?" or answer
  "Currently one (Pops); Ingram overlapped February 2025 to March 2026."
- Edge case for the negative side: Shalini Sharp (Ultragenyx EVP & CFO
  "from 2012 to 2020"; Neurocrine director since February 2020, per NBIX
  DEF14A_2026-04-15). The corpus cannot resolve whether the 2020 months
  overlapped. Decide whether the answer should mention her as not
  counted.

## q065  OK
Refs: ev1 RARE/10-K_2026-02-18:5540 (auditor's critical audit matter: "three royalty purchase agreements ... $320 million, $500 million and $400 million")

## q066  HIGH
Refs: ev1-ev4 EXEL/10-K_2026-02-10:6990, 7009, 7014, 7021
- The Legal Proceedings note headers give MSN, Sun, Azurity, plus Handa
  under "Other" (4). But the SAME 10-K's risk factors say: "we received
  Paragraph IV certification notice letters from MSN, Teva, Cipla, Sun,
  and Biocon concerning the respective ANDAs ... We have also received
  Paragraph IV certification notice letters from Azurity and Handa
  concerning the 505(b)(2) NDA that each has filed" and "With the
  exception of Handa ..., we have subsequently filed patent infringement
  lawsuits against these companies." That is seven challengers, six sued.
  The "per the Legal Proceedings note" scoping is a section-level
  giveaway that a retrieval system cannot be expected to honor, and a
  system answering 7 would be right about the corpus. Options: rewrite
  to "how many companies have sent Exelixis Paragraph IV notices over
  CABOMETYX per the FY2025 10-K" (7: MSN, Teva, Cipla, Sun, Biocon,
  Azurity, Handa), or rewrite to the still-active set as of the 10-K
  (MSN, Azurity, Handa; Sun settled Dec 30, 2025). Also check q058/q068
  stay consistent with whichever framing is chosen.

## q067  OK
Refs: NBIX/DEF14A_2026-04-15:1871-1884
- Year ambiguity checked: the 2024 peer group (NBIX DEF14A_2025-04-09)
  names the same five corpus companies, so the unqualified question has
  one answer. Halozyme is in neither NBIX group (0 hits in both
  proxies), consistent with the PEER_OF example in ontology.md.

## q068  OK
Refs: ev1 EXEL/10-Q_2026-08-05:3953; ev2 :3953; ev3 :3955
- Provenance claim "first disclosed in the Q2 2026 10-Q" checked: the Q1
  2026 10-Q (filed 2026-05-05) has no Accord ANDA or Almatica mention
  (its two "Accord" hits are "Accordingly"); both notice letters arrived
  in May 2026.

---

## Cross-cutting notes for the freeze

- Three near-duplicate pairs remain across categories: q030/q050,
  q022/q056 (q022 verified), and the q058/q066/q068 CABOMETYX-challenger
  trio (not duplicates, but their framings must agree on who counts).
- Rephrase orphans found: q050 ("Yes." on a what-question).
- Answers that pick one of several correct sub-answers (q030, q046,
  q052): decide between widening the answer and adding required_core;
  either works with the agreed judge design (core-when-present).
- The stitched "the Tribunal ..." quote appears twice (q050, q053).

---

# Re-check of the verified set (q001-q029, q069-q080), 2026-08-16

Same method as above, run at the user's request before moving on to q032.
Result: no HIGH findings; the verified set holds up. Everything found was
quote hygiene (claims in the answer whose supporting sentence sat next to
the quote but outside it), one path with the wrong counterparty, and two
judgment calls left for the user.

APPLIED (answers untouched; every new quote re-located verbatim):
- q001: quote now starts at "/s/ Ernst & Young LLP" (firm name was only in
  the answer). EXEL/10-K_2026-02-10:3238-3241.
- q002: ev2 extended to "Rose, Snyder & Jacobs LLP We have served as the
  Company's auditor from 2004 to 2023. Encino, California" (supports
  "before"). ARWR/10-K_2025-11-25:4051-4053.
- q004: ev1 now includes its antecedent sentence ("KKC pays us a royalty
  based on net sales in the European Territory."), and a second quote from
  Note 10 added that names Crysvita, the EU/U.K./Switzerland territory,
  RPI, December 2019 and $320 million. RARE/10-K_2026-02-18:1975, 9169.
- q012: quote extended with the next sentence (Ionis's own September 11,
  2025 Central District of California suit), which the answer asserts.
  IONS/10-K_2026-02-26:12528.
- q017: ev2 now starts at "for an aggregate value of approximately $325.0
  million. The Private Placement is expected to close concurrently with
  the Collaboration Agreement" (both claims were unquoted).
  ARWR/10-K_2024-11-26:3298.
- q020: ev2 had a colon that is not in the source (table header and row
  are separate lines); replaced with an ellipsis. ev1 now includes "at the
  2026 Annual Meeting of Stockholders held on March 19, 2026" (date was
  unquoted). ARWR/8-K_2026-03-20:86, 128-129.
- q024: ev1 extended through "valued at approximately $50.0 million. The
  remaining $50.0 million was paid by the Company in cash."
  SRPT/10-Q_2025-11-06:4089-4091.
- q027: (a) ontology_path named RPI Finance Trust as the buyer in the
  IONIS deal; the counterparty is Royalty Pharma Investments 2019 ICAV
  (ev3), fixed; (b) $320 million was unquoted, Note 10 sentence added
  (same as q004); (c) ev1 antecedent as in q004.
- q028: ev1 fragment "we currently earn royalties from" capitalized to
  match the source ("We ...").

OPEN, user's call:
- q006 (temporal): "Chief Executive Officer and Chairman" is correct as of
  the latest ALKS filing in the corpus (10-Q filed 2026-07-28 still says
  "upcoming retirement"), but the corpus also states he retires as CEO
  effective July 31, 2026 and stays as non-executive Chairman (8-K
  2026-02-25, q019). A system answering "Chairman; retiring as CEO July
  31, 2026" would read as a contradiction to a judge. Options: (i) leave
  as is; (ii) append "(per the April 2026 proxy; he has announced
  retirement as CEO effective July 31, 2026, remaining Chairman)" plus the
  8-K quote and a required_core of "CEO and Chairman"; (iii) anchor the
  question in time ("as of its 2026 proxy statement").
- q005: quote is oblique (bridge-loan termination "in connection with
  completion of the Avadel Acquisition"); the direct sentence is at
  ALKS/10-K_2026-02-25:8577 ("On February 12, 2026, the Company
  successfully completed the Avadel Acquisition"). Swap or add.
- q014: optional addition of the same-passage sentence that Ingram is not
  standing for re-election (term ends at ARWR's 2026 annual meeting), for
  consistency with q045/q064.
- q076 (out of scope): the premise names "MSN, Sun, and Azurity", but Sun
  was dismissed from the Consolidated Litigation on December 30, 2025 per
  the same 10-K. Either drop Sun or keep it as a deliberate stale-premise
  trap (refusal is still the graded behavior).

Checked and clean: q003, q007-q011, q013, q015, q016, q018, q019, q021-
q023, q025, q026, q029; q069-q080 (q079's absence claim re-verified:
0 hits for Merck/Keytruda in both HALO 2026 10-Qs; q070/q073/q080 grep
claims consistent). Path notation issues in this set (q015 `Ipsen|Takeda`
shorthand, reversed direction in q017/q018, free text in q020) are left
for the freeze sweep per DECISIONS #23.

## Verified set: second batch APPLIED (2026-08-16, later the same session)

- DECISIONS #24 (benchmark truth is as of the corpus end, August 2026)
  applied: q006 answer is now "Chairman of the Board (non-executive);
  retired as CEO effective July 31, 2026", with the 8-K quotes and a
  required_core; q013 and q019 updated to the same tense (Pops: Chairman,
  CEO until July 31, 2026); q014 answer now says Ingram served on
  Arrowhead's board February 2025 to March 2026 (SRPT DEF14A 2026-04-24
  quote added) with a required_core on the appointment.
- q008: quote extended through "licensed to Amgen in September 2016 under
  the Olpasiran Agreement" (the Amgen claim in the answer was unquoted).
- q076: premise now "(against MSN and Azurity)"; Sun was dismissed from
  the Consolidated Litigation on 2025-12-30.
- ontology_path rewritten for every question q001-q029 per DECISIONS #23
  (directed edges, roles on PARTY_TO, Agreement types, properties only
  where the question hinges, answer claims expressed as edges, Filing
  nodes where the question hinges on a filing/date, variable binding for
  q029). All terms still resolve against ontology.md; all quotes
  re-locate.

Ontology gaps surfaced by writing the paths against ontology.md (user's
zone; nothing changed in ontology.md):
1. Signing vs effective date (q010): Agreement has one start_date; the
   corpus and q010 distinguish signed 2024-11-25 from effective
   2025-02-07. Written for now as `start_date: 2024-11-25 (signed;
   effective 2025-02-07 ...)`. Candidate: an `effective_date` property.
2. Patents at issue (q012, q025; later q039, q058, q066, q068): no Patent
   entity or LegalCase property; the number is carried in the LegalCase
   label for now. Candidate: `patents[]` property on LegalCase.
3. Equity/stock purchase agreements (q017, q024): used `type:
   stock_purchase`, which is not in the Agreement type list.
4. Shareholder votes (q020): no entity; the vote is a vector-path fact,
   path reduced to Filing -FILED_BY-> Company.
5. Milestone/payment events under an Agreement (q024, later q057): not
   expressible as edges; the path names the Agreement only.
6. Acquisition closing: written as `end_date: <closing>, status:
   completed` (q005, q009), a convention to confirm or replace.
7. Affiliates that are not stated subsidiaries: RPI Finance Trust
   ("affiliate of Royalty Pharma"), Chugai ("member of the Roche Group").
   Written as node labels (q004/q027) and, for Chugai, SUBSIDIARY_OF
   (q031). Decide one treatment.

RESOLVED (2026-08-16, user's decisions, DECISIONS #25-#30): (1)+(6)
Agreement now has signing_date and effective_date (no start_date on
Agreement; acquisitions: effective_date = closing); (2) LegalCase.patents[];
(3) stock_purchase type; (4) votes deferred to the vector path; (5) Payment
reified node + PAID_UNDER edge, PARTY_TO range widened; (7) AFFILIATE_OF
edge, SUBSIDIARY_OF only when stated. Paths re-expressed accordingly for
q004, q005, q007, q009, q010, q012, q017, q018, q024, q025, q027, q030,
q031. Remaining unverified paths pick these up in the freeze sweep (q057
should get Payment nodes; q034/q045/q049 the SPA and upfront Payments;
q043/q060 AFFILIATE_OF for the Royalty Pharma vehicles).
