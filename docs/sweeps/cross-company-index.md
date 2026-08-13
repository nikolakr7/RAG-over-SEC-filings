# Cross-company overlap index

The multi-hop question menu: every connection between corpus companies (and
through shared third parties) surfaced by the full-corpus sweeps. Each entry
names the raw sweep file(s) with detail. LEADS, not evidence: verify in
data/text/ before citing in the benchmark.

## Auditors (firm and office)

| Company | Firm | Office | Since |
|---|---|---|---|
| EXEL | Ernst & Young LLP | San Mateo, CA | 2002 |
| RARE | Ernst & Young LLP | San Mateo, CA | 2012 |
| HALO | Ernst & Young LLP | San Diego, CA | 2006 |
| NBIX | Ernst & Young LLP | San Diego, CA | 1992 |
| IONS | Ernst & Young LLP | San Diego, CA | 1989 |
| SRPT | KPMG LLP | Boston, MA | 2002 |
| ARWR | KPMG LLP | San Diego, CA | 2024 |
| ALKS | PricewaterhouseCoopers LLP | Boston, MA | 2007 |

- E&Y audits 5 of 8 companies. Two SAME-OFFICE clusters: San Mateo (EXEL,
  RARE) and San Diego (HALO, NBIX, IONS).
- ARWR is the corpus's only auditor CHANGE: Rose, Snyder & Jacobs LLP
  (Encino, CA, 2004-2023; last report Nov 29, 2023) to KPMG San Diego (first
  report Nov 26, 2024). The FY2024 10-K prints both reports. [ARWR-10K-deltas]

## Corpus-to-corpus deals

- **SRPT <-> ARWR**: Exclusive License & Collaboration Agreement, signed Nov
  25, 2024, closed Feb 7, 2025. $500M upfront + $325M equity + up to ~$10B
  milestones; 7 named siRNA programs. Milestones: $100M DM1 (Jul/Aug 2025,
  HALF PAID BY SURRENDERING ~2.7M ARWR SHARES back to Arrowhead), $200M (Nov
  2025). Dec 2025 clinical supply agreement. $696.8M of ARWR's FY2025
  revenue. [SRPT-10K-FY2025, ARWR-10K-FY2025, ARWR-10Q]

## Corpus-to-corpus litigation

- **IONS vs ARWR**: patent US 9,593,333 vs plozasiran/REDEMPLO. Dueling
  complaints Sept 10-11, 2025 (ARWR declaratory judgment in D. Del.; Ionis
  infringement in C.D. Cal.). ARWR's Delaware DJ dismissed Dec 23, 2025;
  the C.D. Cal. infringement case continues. [IONS-10K-FY2025,
  ARWR-10K-FY2025, ARWR-10Q]

## Board interlocks (Person edges between corpus companies)

- **Richard F. Pops**: ALKS Chairman & CEO (CEO until Jul 31, 2026, then
  non-executive Chairman; successor Blair C. Jackson) AND NBIX director
  since April 1998. Confirmed in both companies' proxies.
  [NBIX-events-people, ALKS-events-people]
- **Shalini Sharp**: EVP & CFO of Ultragenyx 2012-2020, NBIX director since
  Feb 2020. [NBIX-events-people]
- **Douglas Ingram**: President & CEO of Sarepta since June 2017; ARWR
  director during fiscal 2025 (joined after the Nov 2024 SRPT-ARWR deal, on
  the ARWR CEO's recommendation), retired from the ARWR board at the Mar 19,
  2026 annual meeting. RESOLUTION NOTE: one delta sweep suggested this was a
  confusion with ARWR ex-Chairman Douglass Given; the proxy bio quote
  ("Mr. Ingram has served as the President and Chief Executive Officer of
  Sarepta Therapeutics, Inc. ... since June 2017") confirms Ingram is real
  and distinct from Given. [ARWR-events-people, SRPT-10K-FY2025]

## Compensation peer groups (company-level PEER_OF edges, from proxies)

- NBIX peer group names: ALKS, EXEL, IONS, SRPT, RARE
- IONS peer group names: ALKS, EXEL, HALO, NBIX, SRPT, RARE (6 of 8)
- HALO peer group names: ALKS, EXEL, IONS, NBIX, SRPT, RARE (6 of 8;
  the events-people sweep undercounted at 5; corrected against primary text
  during question drafting)

## Royalty Pharma: counterparty to HALF the corpus

Four of eight companies have sold royalty streams to (or owe royalties to)
Royalty Pharma entities. Prime aggregation-question material.

- EXEL: owes 3% cabozantinib royalty to Royalty Pharma since Jan 1, 2021
  (bought from GSK; US leg reverts to GSK after Sept 2026). [sweep-exel]
- IONS: Jan 9, 2023 deal (via Akcea): $500M upfront for 25% of SPINRAZA
  royalties (45% from 2028) + 25% of pelacarsen royalties. [IONS-10K-FY2025]
- ARWR: sold entire olpasiran (Amgen) royalty stream Nov 2022, up to $410M.
  [ARWR-10K-FY2025]
- RARE: sold European Crysvita royalty to RPI Finance Trust, $320M, Dec 2019
  (plus separate OMERS tranches 2022 and 2025). [RARE-10K-FY2025]

## Shared big-pharma counterparties (hub nodes)

- **Roche/Genentech**: EXEL (COTELLIC out-license; atezolizumab supply;
  CONTACT joint trials), HALO (largest ENHANZE partner, 5 royalty-paying
  products; Chugai is a Roche Group member), SRPT (ex-US ELEVIDYS deal, Dec
  2019, $1.2B upfront incl. equity), ARWR (Roche acquired Arrowhead's
  predecessor RNAi business, 2011), NBIX (dense Genentech/Roche alumni on
  board and management).
- **Takeda** (family incl. Baxalta, ex-Shire): EXEL (Japan cabozantinib
  license), HALO (TWO ENHANZE deals: 2007 HYQVIA via Takeda Pharmaceuticals
  International AG + Baxalta US; Dec 2025 ENTYVIO), NBIX (osavampator
  license, restated Jan 24, 2025: profit-share converted to royalties, Japan
  rights returned), ARWR (fazirsiran 50/50 US co-commercialization).
- **Janssen / J&J**: HALO (ENHANZE + Hypercon partner; new CFO Snellgrove is
  27-year J&J veteran), ALKS (RISPERDAL CONSTA / INVEGA NANOCRYSTAL saga:
  partial termination Nov 2021, arbitration award $195.4M May 2023,
  award-set royalty ladder to 2030), ARWR (former HBV licensee: JNJ-3989
  returned, then relicensed to GSK Dec 2023), IONS (director Michael Yang is
  ex-President of Janssen Biotech).
- **BMS**: EXEL (cabo + nivolumab/ipilimumab collaboration), HALO (ENHANZE:
  Opdivo Qvantig; CEO Torley and director Connaughton are ex-BMS), ALKS (CFO
  Reed and director Lurker ex-BMS), ARWR (director Olukotun ex-BMS), NBIX
  (multiple BMS alumni).
- **GSK** (incl. ViiV): EXEL (2002 collaboration created the cabozantinib
  royalty; US royalty leg reverts to GSK Sept 2026), HALO (ViiV, majority
  owned by GSK, is an ENHANZE partner), ARWR (two licenses incl. the HBV
  asset inherited from Janssen), IONS (bepirovirsen phase 3; EVP Jenne's
  company Elsie acquired by GSK 2023; director Diaz ex-GSK).
- **Biogen**: IONS (flagship partner: SPINRAZA and others; option on
  obudanersen expired unexercised 2024), ALKS (VUMERITY worldwide license,
  15% royalty; plus a Biogen/Zydus ANDA suit over VUMERITY found only in the
  ALKS FY2024 10-K). [ALKS-10K-deltas]
- **Merck disambiguation** (three distinct entities): "Merck" = MSD
  International Business GmbH, EXEL's zanzalintinib collaborator (Oct 2024);
  "Merck & Co." = competitor context in EXEL filings; Merck Sharp & Dohme =
  defendant in HALO's Keytruda-SC patent war. Do not merge these nodes
  without checking jurisdictional naming ("MSD" is Merck & Co. outside
  US/Canada; the EXEL filing defines its terms explicitly).

## Asset lineage chains (multi-owner assets)

- ARO-HBV: Arrowhead -> Janssen (2018, as JNJ-3989) -> returned -> GSK (Dec
  2023, as GSK5637608/daplusiran-tomligisiran).
- Cabozantinib royalty: GSK (2002) -> Royalty Pharma (2021) -> US leg back
  to GSK (Sept 2026).
- LUMRYZ royalty: Jazz-Avadel settlement (Oct 2025) -> inherited by ALKS via
  the Avadel acquisition (closed Feb 12, 2026): 3.85% of LUMRYZ narcolepsy
  net sales through Feb 2036.
- Elan lineage: ALKS acquired Elan Drug Technologies (2011); two current
  ALKS directors have Elan history.
- Baxalta lineage: Baxter -> Baxalta -> Shire -> Takeda; Baxalta US Inc. is
  a HALO ENHANZE counterparty; HALO's ex-COO Caudill is a Baxalta alum.

## Corpus-wide temporal events (2025-2026 highlights)

- SRPT: ELEVIDYS safety crisis (deaths Mar/Jun 2025, US shipment suspension
  Jul 22, 2025, boxed warning Nov 2025, ESSENCE trial miss) + securities and
  derivative litigation. The FY2023/FY2024 filings preserve the pre-crisis
  optimistic language: strong before/after contrast.
- NBIX: Soleno Therapeutics acquisition ($2.9B, closed May 18, 2026,
  POSTDATES the FY2025 10-K; exists only in 10-Qs/8-Ks). CEO handoff Gorman
  -> Gano, Oct 11, 2024.
- ALKS: Avadel acquisition closed Feb 12, 2026; CEO handoff Pops -> Jackson
  Aug 1, 2026; Amneal authorized-generic supply deal terminated Jul 2026.
- HALO: Merck/Keytruda-SC litigation narrative VANISHES from both 2026
  10-Qs after German injunction (Dec 2025): possible settlement, unresolved
  in corpus. CFO churn: LaBrosse -> Ramsay (interim) -> Snellgrove (Jun
  2026). COO Caudill departed Jun 30, 2026.
- EXEL: two new generic challengers only in 2026 10-Qs (Accord ANDA suit Jul
  2026; Almatica 505(b)(2) notice). Zanza PDUFA Dec 3, 2026. Consolidated
  trial Nov 2, 2026.
- IONS: eplontersen ATTR-CM phase 3 miss (Jul 2026); TRYNGOLZA second
  indication approved Jun 2026; Biogen/Novartis/AstraZeneca each terminated
  or lapsed a program 2024-2025 (de-partnering edges).
- RARE: setrusumab phase 3 failure (Dec 2025) -> restructuring (Feb 2026);
  REGENXBIO licenses terminated Nov 2025; securities class action Feb 2026.

## Known open questions / conflicts (do not treat as settled)

1. HALO-Merck litigation status after Dec 2025 (disappears from 2026 10-Qs).
2. RARE: unidentified ANDA co-defendant "Somerset" added by consolidation
   Apr 2026.
3. NBIX-Spruce Biosciences litigation resolution (present FY2024, gone
   FY2025, no explicit resolution found).
4. ALKS Exhibit 21 name drift: "Alkermes Controlled Therapeutics, Inc." vs
   "...Inc. II" across years.
5. IONS filing-internal inconsistency: higher-dose SPINRAZA PDUFA April 3
   vs April 23, 2026 (both appear in the FY2025 10-K).
