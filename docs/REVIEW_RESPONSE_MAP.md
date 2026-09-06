# Reviewer feedback → where it lands in the paper

Companion to `paper_ieee_annotated.md`. Every item below points at a marker in that file.

---

## Triage

| # | Reviewer point | Severity | Where | Marker |
|---|---|---|---|---|
| 1 | 0.885 vs 0.667 reads like a transfer result | **Critical** | Abstract, Intro contrib. (2), Conclusion, Fig. 2 caption | F-01, F-04, F-11, E-13 |
| 2 | Slice descriptor contradicts the shipped metadata | **Critical** (new — not raised by a reviewer) | Intro, final paragraph | F-05 |
| 3 | Deeper discussion of why the negative result matters | High | Discussion, new paragraph | A-05 |
| 4 | Show specific DOMINO failure examples | High | Results, after DOMINO paragraph | A-04 |
| 5 | 19.9% — detector failure or generator artifact? | High | Results §IV; Limitations §V | A-02, A-06, F-07 |
| 6 | Why does NODE21 only reach 0.667? | High | Methods; Results | F-09, A-03 |
| 7 | Name the positive finding | Medium | Abstract closing line | A-01 |
| 8 | Abstention is a non-event | Low | Abstract; Discussion | F-02, F-10, F-12 |
| 9 | Typos, grammar, consistency | Low | Throughout | E-01 … E-19 |

---

## 1. "The abstract reads like transfer" — critical

Appears in **four** places, not one. Fixing only the abstract will not close it.

| Location | Offending construction | Marker |
|---|---|---|
| Abstract | "...0.885 ± 0.012, **whereas** the corresponding real-only NODE21 task reaches 0.667" | F-01 |
| Intro, contribution (2) | "**a direct measurement of the synthetic-to-real failure gap**" ← strongest overclaim in the paper | F-04 |
| Conclusion | "...0.885 ...; on real NODE21 data, ... 0.667 ..., **a gap indicating**..." | F-11 |
| Fig. 2 caption | Correct, but the disclaimer is hard to parse | E-13 |

---

## 2. The 40-image slice description does not match the 40 images — critical, and new


**Intro currently says:** *"a coherent 40-image slice, every case a failure, dominated by small, low-contrast, upper-right nodules **with no anatomical overlap**."*

**The shipped metadata says:**

| Axis | Distribution across the 40 |
|---|---|
| Size | small 20 (50%) · medium 13 (33%) · large 7 (18%) |
| Contrast | low 18 (45%) · medium 13 (33%) · high 9 (23%) |
| Location | upper_right 11 (28%) · lower_left 8 (20%) · upper_left 7 (18%) · lower_right 7 (18%) · mid_left 4 (10%) · mid_right 3 (8%) |
| Overlap | **none 11 (28%)** · heart 10 (25%) · clavicle 7 (18%) · spine 7 (18%) · diaphragm 5 (13%) |

- **29 of 40 (72.5%) *do* have anatomical overlap.** "With no anatomical overlap" looks inverted.
- **Exactly 1 of 40 matches all four descriptors** (`synth_0003`). Nine match small+low; three match small+low+none; four match upper-right+none.
- Drawn from **16 distinct source radiographs**; IDs run to `synth_0178`, and every sidecar has `"qc_pass": null` — worth confirming the slice was computed over the 161-image QC-passing subset, since the paper attributes it there (F-06).

the corrected description is a **stronger** argument for your thesis. A slice spanning six locations and five overlap conditions makes "cuts across the predefined grid cells" self-evident, whereas a slice concentrated in one corner of the grid would arguably just be a grid cell. Suggested replacement text is at F-05.

---

## 3. "Why do the negative results matter?" — the biggest content gap


The argument to make (drafted at **A-05**): this is not an ordinary null result. The synthetic evaluation returns a *confidently structured* answer — large effect, stable across folds, shuffled-label control at chance, interpretable attribute map — that has every surface property of a positive robustness finding. Reported alone, as synthetic stress tests routinely are, it would be read as evidence that this detector's failure modes are understood. The real-side checks say otherwise. So the cost of skipping the checks is not a missed insight but a false one.

That converts "our results were negative" into "here is a reporting norm the field should adopt," which is also the framing reviewer 1 asked for in item 7.

---

## 4. DOMINO examples — you have the assets, they just are not in the paper

Currently three sentences and no visual for something the Intro calls a key finding. Recommended addition (~half a column), detailed at **A-04**:

- **Fig. 4** — 4–8 slice members, full radiograph + GT box + magnified inset. Draft: `fig4_domino_slice_examples_DRAFT.png` (panels 0003, 0005, 0164, 0097, 0136, 0121, 0153, 0036 — spans all three size levels, all three contrast levels, four of five overlap conditions). Layout mock-up only; regenerate at print resolution with your own windowing.
- **Small table** — slice composition vs. grid base rates. Makes "cuts across the grid" quantitative. Numbers above; raw data in the CSV.
- **One paragraph** — the failure case study. Draft text at A-04(c).

The case-study argument that holds up regardless of what you can say about image appearance: 16 source images, all six locations, all five overlap conditions → the cluster is not a relabelled grid cell; and GEORGE cannot see it because GEORGE can only rank groups the grid defines, whereas the operative axis (realized conspicuity) is latent and cuts across all of them.

---

## 5. The 19.9% sensitivity — you can answer this without a radiologist

The reviewer asked whether 19.9% reflects the detector or the generator, wanted a radiologist to check, and asked about the deadline. Radiologist review is off the table; the reviewer's own fallback — frame it as a domain gap — is the right call, and **your copy-paste arm already is the controlled experiment that makes the argument quantitative.**

Copy-paste and RadEdit v2 share the source images, the attribute grid, the insertion locations, and the fixed detector. The only variable that differs is how the lesion was rendered.

| Arm | Rendering | Sensitivity |
|---|---|---|
| Copy-paste | real nodule patches | **42.2%** (76/180) |
| RadEdit v2 (QC-passing) | diffusion | **19.9%** (32/161) |
| — | detector on real NODE21 val @0.5 FP/img | 88.9% |

Two conclusions follow, neither needing an expert reader:

1. The 22.3-point gap is attributable to generator rendering, since everything else is held constant. So 19.9% characterizes the **generator–detector pair**, not the detector.
2. The copy-paste ceiling of 42.2% sits far below the detector's 88.9% real-data sensitivity, so **insertion realism bounds achievable sensitivity on both arms** — this is what the domain gap looks like concretely in your setup.

Both numbers are already in the paper; they are just never placed side by side. Draft text at **A-02**, and a quantified rewrite of limitation one at **A-06**.

On the radiologist request: name it as scoped future work rather than leaving it unanswered — one sentence in Limitations converts an unmet request into a credited limitation.

**One caution.** I inspected the 40 slice images at high magnification against their GT boxes. In most, including several labelled `large` / `high` contrast, no discrete nodular opacity is visually apparent at the annotated location. I am not a radiologist and the shipped PNGs are 512×512 downsamples, so do not cite this — but a reviewer who opens the supplement will see the same thing, which is why getting ahead of it with the copy-paste argument matters.

---

## 6. Why 0.667?

The paper never gives **n**, **class balance**, or the CV protocol for the real-only ablation, and reports 0.885 with a ± while 0.667 has none. That asymmetry is itself part of why the number looks unexplained.

Two things to add (draft at **A-03**, flag at **F-09**):

- The mechanics: n, failure count, class balance, same 5-fold protocol, and a ± on 0.667.
- The reason: real nodules vary continuously in conspicuity rather than sitting on discrete grid levels, so there is no attribute structure for a global embedding to exploit; and real failures mix missed detections with localization errors, whereas every synthetic failure is a miss of a known inserted lesion. 0.667 means real failure structure is less linearly separable in BiomedCLIP space — not that the predictor is broken.

---

## 7. Name the positive finding

Your closing abstract sentence already contains it but frames it as a caveat. State it as a prescription instead: a synthetic stress test counts as robustness evidence *only* when paired with generator controls and an explicit synthetic-to-real check — and this paper's grid passes the first and fails the second, which is exactly what such a check is for. Draft at **A-01**; reinforced by A-05's three-check protocol.

---

## 8. Abstention

Agreed it is a non-event. Three light touches:

- **F-02** — abstract spends two sentences on it, and the second ("at high abstention rates, answered-case FNR can decrease") describes the *real-only ablation*, not the synthetic predictor. Compress to one line.
- **F-10** — the Discussion paragraph could be halved if you need space for A-05.
- **F-12** — the Conclusion says confidence abstention "matched **or exceeded**" the synthetic predictor, but §IV reports exact ties at all three operating points and no point where it exceeds. Soften, or cite the point where it does.

---

## 9. Minor edits

19 items, E-01 through E-19, all inline in the annotated file. Nothing consequential. The recurring ones: "chest x-ray" vs "chest X-ray" (E-01); the contraction "don't" (E-02); missing hyphens in "low contrast" and "cross domain" (E-06, E-14); "the detector performance" / "the average performance" style articles (E-16, E-18); Fig. 3's caption missing its terminal period (E-14); and "Related Works" → "Related Work" (E-09).

Two worth a second look because they are more than cosmetic:

- **E-11** — "Under the verified evaluation" is unexplained and may read as though an earlier result was wrong. Either delete it or make it concrete (e.g. leakage-checked folds).
- **F-08** — Table I's caption and the Results text both assert that confidence intervals overlap, but no CI appears anywhere in the paper. Add them, or reword.

---

## Consistency checks that passed

For completeness, these were verified against the PDF and are internally consistent:

- 76/180 = 42.2% ✓ · 32/161 = 19.9% ✓ · 161 − 32 = 129 ✓
- Table I FROC/sensitivity values match the Results narrative ✓
- Coverage figures (0/29 @ 0.039, 4/29 @ 0.075, 23/29 @ 0.100, 29/29 @ 0.150) match Fig. 3's caption ✓
- CheXpert 674/675 and 1574/1575; MIMIC 320/450 → FNR 0.289 ✓, 585/1013 → FPR 0.577 ✓
- Abstention rates and answered-case failure rates internally consistent ✓
- One inconsistency found: the Introduction lists **three** grid axes, everywhere else lists **four** (F-03)

---

## Files

| File | What it is |
|---|---|
| `paper_ieee_annotated.md` | Full text extraction with all markers inline |
| `REVIEW_RESPONSE_MAP.md` | This file |
| `domino_slice_composition.csv` | Attributes of all 40 slice images, for the F-05 check and the A-04 table |
| `fig4_domino_slice_examples_DRAFT.png` | Layout mock-up for the proposed Fig. 4 |
