# Findings

Everything here is measured on the **v5 grid** (720 images, 12 chests) or on real NODE21
(1,133 images, 1,474 nodules). Numbers that appear in the paper should come from this file
or from `results/`, not from a notebook output cell.

`docs/REVIEW_RESPONSE_MAP.md` describes the *previous* draft and cites v4-era numbers
(0.885, 0.667, 19.9%, 42.2%). Those are superseded here where they overlap.

---

## 1. The central result

Every axis in the grid controls whether RadEdit paints a lesion. **None of them controls
whether the detector finds it.** Chest is the unit of independence throughout — 12 chests,
60 cells each.

| axis | P(RadEdit paints) by level | p | detection among painted, p |
|---|---|---|---|
| overlap | 0.84 / 0.80 / 0.37 | 0.0002 | 0.15 |
| size | 0.60 / 0.66 / 0.76 | 0.0001 | 0.076 |
| zone | 0.67 / 0.80 / 0.53 | 0.0007 | 0.18 |

Detection is predicted by **realised conspicuity**, not by requested attributes:
CNR vs detection **r = +0.33, p = 4e-12**.

This is the paper's claim and it is a negative result about the grid design, not about the
detector. A stress test built on requested attributes measures generation success and
reports it as robustness.

### Controls that make the above interpretable

| control | n | fired |
|---|---|---|
| null-edit (prompt names normal parenchyma, same pipeline) | 45 | **0** |
| unedited backgrounds | 413 | **0** |

Neither control fires, so a detection in the lesion arm is attributable to the edit rather
than to pipeline artefacts or pre-existing structure.

---

## 2. Failure predictor ablation

5 repeats, folds split by **source chest** (`source_grouped`). The `stratified` column is
kept only to show how much leakage the naive split introduced.

| features | AUROC (source-grouped) | AUROC (stratified) | Brier | dim |
|---|---|---|---|---|
| biomedclip_full | **0.817 ± 0.022** | 0.845 ± 0.013 | 0.176 | 512 |
| biomedclip_crop | 0.750 ± 0.032 | 0.801 ± 0.025 | 0.107 | 512 |
| edit_norm | 0.727 ± 0.005 | 0.728 ± 0.005 | 0.217 | 1 |
| cnr | 0.722 ± 0.006 | 0.725 ± 0.004 | 0.212 | 1 |
| edit_norm + cnr | 0.725 ± 0.007 | 0.715 ± 0.008 | 0.214 | 2 |
| requested_axes | 0.561 ± 0.019 | 0.566 ± 0.016 | 0.231 | — |

Three things to read off it:

**The requested axes are near chance (0.561).** Consistent with §1.

**A single scalar matches a 512-dimensional embedding.** `cnr` alone (0.722) is not
distinguishable from `biomedclip_crop` (0.750) — t = 1.94. One hand-computed contrast
measure does the work of the lesion-crop embedding.

**Whole-image beats crop, and that is the suspicious result.** `biomedclip_full` (0.817)
clearly beats crop (t = 9.36). The lesion crop contains the lesion; the full image contains
the lesion *and the source radiograph*. So the gap is the predictor reading chest identity,
not lesion difficulty — this is checklist item 1 and it is **not yet closed**.

`biomedclip_full` also has the **worst Brier score** (0.176 vs 0.107 for crop): better
ranking, worse calibration. Do not report AUROC alone.

> Two retractions on the record. I earlier told Feliciano to stop using `edit_inside` as a
> gate — wrong direction, withdrawn. I also said the crop leaked less than the full image;
> the 5-repeat data reversed that. Both are corrected above.

---

## 3. Method constraints on RadEdit

These bound what the generator can be asked for, and each one cost a failed experiment.

**Locked to 512×512.** 768 and 1024 raise `tensor a (96) must match tensor b (64)` — the
UNet has 64×64 latent structure. Not a bug to fix. Consequence: the smallest reliable
lesion is **≈32 mm**, so every "nodule" in the grid is radiologically a **mass**. Say this
rather than letting a reviewer find it.

**Prompt text controls nothing except that it must name an anatomical location.** Size,
contrast and margin wording had no measurable effect. A prompt with no location fails to
paint.

**Edit strength varies ~4× between chests** at identical settings, which is why
`edit_norm` (edit_inside ÷ local texture std) is used instead of raw `edit_inside` — the
raw value is not comparable across chests.

**Density is not a proxy for anatomical overlap.** The medial/lateral assumption was
disproved: medial sites came out *less* dense (0.861 vs 1.028, p = 0.0012), because the
lung box is a rectangle. Replaced with a density-percentile search over candidate sites.

---

## 4. Copy-paste arm

648 twins, matched to the grid by `radedit_twin`. Intensity is matched on the **surround**,
not the lesion core — matching the core erases the contrast that makes it a nodule and
produced dark discs in an earlier version. After the fix: median contrast **+0.065**, 95%
positive.

**`det_edited` is still all NaN — these have not been scored.** Until they are, there is no
controlled generator comparison, which is the cheapest remaining result in the project.

---

## 5. Baseline 1 — FROC on real NODE21

Frozen detector, 1,133 images (`n0507` dropped as a byte-identical duplicate of `n1059`
carrying the less complete annotation), 1,474 nodules, centre-in-box matching.

| FP / image | sensitivity |
|---|---|
| 0.125 | 0.3786 |
| 0.25 | 0.4986 |
| 0.5 | 0.6024 |
| 1.0 | 0.7123 |
| 2.0 | 0.7849 |
| 4.0 | 0.8345 |
| 8.0 | 0.8908 |

**FROC score (mean of 7 operating points): 0.6717.** Seven distinct, monotone values — the
F6 double-threshold truncation that collapsed the old curve to five duplicate points stays
fixed.

Two properties of the detection dumps that affect interpretation:

- **No score floor is applied.** `box_score_thresh=0.0`, cap 300 boxes; stored scores run
  down to 0.002, median 238 boxes per image. `SCORE_MIN = 0.05` is therefore **only the
  operating point at which a nodule is declared detected** — a reported choice, not a
  filter. The notebook markdown claiming "all boxes above 0.05" is wrong.
- **Some images hit the 300-box cap.** Truncation keeps the highest-scoring 300, so nothing
  above any usable threshold was lost. State it anyway.

Because there is effectively no floor, ~238 boxes are scattered per image and only **15 of
1,474 nodules** have no box centre in them at all. "Hit rate" is meaningless here; only
"hit above a threshold" means anything.

---

## 6. Baseline 2 — confidence-only abstention, corrected

`results/table-baseline2-clustered.csv` supersedes `table-baseline2.csv`. Three faults in
the original: abstention was nodule-weighted, Wilson treated nodules as independent, and
the operating point was inherited silently from `SCORE_MIN`.

| cases declined | nodule FNR [clustered 95%] | case FNR |
|---|---|---|
| 0.0% | 0.2056 [0.1849, 0.2274] | **0.2454** |
| 20.7% | 0.1229 [0.1052, 0.1417] | 0.1537 |
| 42.8% | 0.0941 [0.0748, 0.1131] | 0.1250 |
| 59.9% | 0.0650 [0.0463, 0.0844] | 0.0881 |

**Lead with the case-level number.** At zero abstention 20.6% of nodules are missed but
**24.5% of cases contain at least one miss**. The case figure is what a clinician acts on.

**Abstention is a weak lever and the curve shows where it dies.** The first fifth of cases
declined buys a 40% relative cut (0.206 → 0.123). The next forty percent buys almost
nothing (0.123 → 0.065). If this is the baseline a method has to beat, that plateau is the
target.

**61 images (5.4%) have `max_score < 0.05`** — the detector is silent on them. A distinct
failure mode from firing in the wrong place, and worth separating.

**`fnr_nodule` is not monotone** (0.1229 at 0.40 → 0.1231 at 0.45). Not a bug: abstention
removed 26 nodules of which only 3 were misses, an 11.5% rate below the 12.3% base, so the
remainder got marginally worse. Note it in the caption or someone will "fix" it.

### The clustering correction is negligible here, and that is the finding

Cluster bootstrap over images gives **CI inflation 0.95–1.03×** versus Wilson — i.e. none.
Cause: **1.30 nodules per image**. The design effect ceiling is `1 + (m̄−1)·ICC = 1 + 0.30·ICC`,
so even at perfect within-image correlation the interval could only widen by √1.30 ≈ 1.14×.

So **Wilson is defensible for the real-nodule baselines** and Table 1 does not need
revising. State this explicitly, because it draws the line against the synthetic grid,
where cluster size is **60 images per chest, not 1.3** — which is exactly why chest as the
unit of independence is load-bearing in §1 and nearly free here. A reader who sees
clustering applied to one and not the other will assume inconsistency unless shown the
check.

Caveat that stays open: **image is a proxy for patient.** NODE21 ships no patient
identifiers, so two studies of one patient can land on both sides of any split. The
correction above is a floor.

Caveat on the sweep itself: the threshold is chosen and evaluated on the same 1,133 cases,
and the answered subset is selected on `max_score`, which correlates with `best_score`. The
FNR falls partly by construction. This describes a trade-off on this set; it is not a
held-out guarantee. (Checklist item 7.)

---

## 7. Data hygiene established

- **`n0507` excluded everywhere.** Byte-identical to `n1059`, 2 nodules vs 3, less
  complete. 1,476 − 2 = 1,474 nodules; 1,134 − 1 = 1,133 images. Matches
  `real_crop.npz` (1474, 512).
- **Embeddings were built from v5**, not v4 — all 720 keys match the v5 image IDs including
  the 72 `__null` controls.
- **Seeds are md5-derived, not `hash()`.** Python salts `hash()` per process, so the old
  seeding was not reproducible across sessions.
- **`arm='null'` renamed to `null_edit`** — pandas parses the string `"null"` as NaN.
- **Grid is a single 43-column schema.** The mixed 42/43-column CSV was discarded, not
  patched.
