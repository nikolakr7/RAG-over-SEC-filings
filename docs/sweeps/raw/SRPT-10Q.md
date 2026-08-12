# SRPT 10-Qs, 2024-11-06 through 2026-08-05 (six quarters)

Grep targets per instructions: entered into | amendment | Legal Proceedings | Subsequent Events | termination | milestone | Arrowhead | ELEVIDYS. Line numbers refer to each respective source file in `data/text/SRPT/`.

## Q3 FY2024 — 10-Q_2024-11-06_000095017024122239.txt (period ended Sept 30, 2024)
- Dominant event: **Thermo Fisher / Brammer Bio termination**. Sarepta issued a termination notice to Thermo on July 18, 2024 for the June 2018 development/commercial manufacturing/supply agreement (amended May 2019, July 2020, Oct 2021, and a March 2023 4th amendment); termination effective Aug 21, 2024; net impact recorded as R&D expense; $91.9M increase in manufacturing expenses attributed to the termination in the MD&A cost discussion (line 7942); Roche reimbursed a portion of termination costs under the Roche Agreement (line 6210).
- No Arrowhead mentions at all — the Arrowhead Collaboration Agreement (signed Nov 25, 2024) postdates this filing.
- No ELEVIDYS safety-crisis language (deaths/suspension/label) — all 2025 events.
- Legal Proceedings section present at line 1373 (not drilled into; no new litigation flagged by the targeted grep terms).

## Q1 FY2025 — 10-Q_2025-05-06_000095017025064412.txt (period ended March 31, 2025)
- **Arrowhead Collaboration Agreement closes**: effective Feb 7, 2025 (HSR clearance) (line 2319); Arrowhead appointed CEO Douglas Ingram to its board effective Feb 2025 (line 2356); $500.0M upfront cash paid; $325.0M / 11,926,301-share equity investment recorded within strategic investments, subject to a sale restriction until August 2025, with an option to exchange the Arrowhead shares for pre-funded warrants (lines 2357-2370); up to ~$X.X billion in potential milestones referenced but exact figure omitted by the grep tool (line 2389 area).
- Feb 13, 2025: JPMorgan Chase $600.0M Credit Agreement entered (5-year revolver) (line 4185).
- Net product revenue increase driven by ELEVIDYS: +$241.0M YoY in Q1 2025 attributed to "its expanded label approval in June 2024" — still framed as commercial growth, not risk (line 5032).
- **No safety-crisis language found** — zero hits for "liver" anywhere in the file. Notable given baseline's timeline places one of the two ALF deaths in "March 2025"; as of this May 6, 2025 filing the event had evidently not yet been disclosed/deemed material, or is captured under different wording not matched by this grep pass.

## Q2 FY2025 — 10-Q_2025-08-06_000095017025103971.txt (period ended June 30, 2025)
- **Safety crisis fully disclosed this quarter**: "we recently announced two reported cases of ALF resulting in death in non-ambulatory patients following treatment with ELEVIDYS. Following these announcements, FDA proposed a safety label supplement..." (line 8744). "ELEVIDYS Suspension" appears as a defined term (line 6073). Risk factors reference "our ability to resume shipments of ELEVIDYS for non-ambulatory patients in the U.S." (line 8388) — i.e., ambulatory shipments had resumed by filing date but non-ambulatory had not.
- Arrowhead: continuing amortization/expense disclosure; a dedicated "Milestone Payment to Arrowhead" sub-heading appears (line 6058), consistent with the first $100.0M DM1 milestone achieved Aug 13, 2025 being discussed as a recognized/near-term obligation.
- No explicit securities/derivative-suit text surfaced in the targeted grep (the June 26, 2025 securities class action filing falls inside this quarter but wasn't captured by the sampled pattern hits — likely covered in a Legal Proceedings section not read in full per token budget).

## Q3 FY2025 — 10-Q_2025-11-06_000119312525269436.txt (period ended Sept 30, 2025)
- **ESSENCE confirmatory trial** dominates new risk language: "the possible impacts of the results of our ESSENCE confirmatory trial for VYONDYS and AMONDYS, including... potential regulatory actions from the FDA, including directives to remove these products from the market or alter labels..." (line 7583); explicitly ties the topline miss (Nov 3, 2025, just before this Nov 6 filing) to possible revocation of accelerated approvals under FDORA's expedited-withdrawal procedures (line 10360).
- No new Arrowhead milestone or Regenx/Genzyme litigation update surfaced by the targeted grep in this pass; second Arrowhead DM1 milestone (Nov 24, 2025, per baseline) falls at/after this filing's period end and is not captured in the sampled lines.
- Securities/derivative suit progression not directly captured in this pass (consolidated derivative suits and the securities action's transfer to D. Mass. both occurred Nov 2025, likely just after or at the edge of this filing window).

## Q1 FY2026 — 10-Q_2026-05-06_000119312526208893.txt (period ended March 31, 2026; POSTDATES the FY2025 10-K)
- Confirms as now-established fact (not new this quarter): FDA-mandated "boxed warning for acute liver injury (ALI) and acute liver failure (ALF)" plus "removal of the non-ambulatory population from the Indication and Usage section" for ELEVIDYS (line 4832) — matches the Nov 2025 label change reported in the FY2025 10-K baseline.
- Ongoing sirolimus (enhanced immunosuppression) study referenced as still under discussion with FDA regarding "possible impacts on the resumption of dosing in the non-ambulatory population" (line 4836).
- **No 2026 recovery yet for non-ambulatory ELEVIDYS**: risk factors still list "our ability to resume commercial shipments of ELEVIDYS for non-ambulatory patients in the U.S." as an open, unresolved item (line 6222) — i.e., non-ambulatory shipments had NOT resumed as of this filing.
- Regenxbio still listed only as a pipeline competitor (RGX-202) in this pass; no litigation-status line captured.

## Q2 FY2026 — 10-Q_2026-08-05_000119312526335003.txt (period ended June 30, 2026; most recent filing, POSTDATES the FY2025 10-K)
- Litigation: Regenx/U-Penn '274 Patent PTAB appeal still pending — "On October 20, 2025, Sarepta filed a notice of appeal of the PTAB's decision to the Federal Circuit, and the appeal is pending" (line 6222), i.e., unresolved as of mid-2026.
- **Still no non-ambulatory recovery**: "our ability to resume commercial shipments of ELEVIDYS for non-ambulatory patients in the U.S." remains listed as an open risk factor (line 8762), same wording as the prior quarter — no recovery signal for the U.S. non-ambulatory population through this filing.
- Partial commercial recovery signal via Roche/ex-US instead: contract manufacturing revenue to Roche rose (+$27.4M and +$41.1M in two separate period comparisons) "primarily driven by increased deliveries of ELEVIDYS to Roche," alongside continued "greater-than-expected write-offs of batches... not meeting our quality specifications" (lines 7167, 7271) — ex-US/Roche-side ELEVIDYS volume growing even as U.S. non-ambulatory sales remain frozen.
- Boxed-warning ALI/ALF and non-ambulatory-indication-removal language repeated verbatim as established fact (line 6282), same as Q1 FY2026.
