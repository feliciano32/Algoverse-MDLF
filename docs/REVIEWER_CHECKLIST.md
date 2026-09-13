# Reviewer / mentor checklist

The 11 items raised against the draft. **Closed items stay visible** — struck through is
not the same as deleted, and a closed item still needs its evidence cited in the paper.

Evidence lives in `docs/FINDINGS.md` and `results/`.

| # | item | status | where the answer is |
|---|---|---|---|
| 1 | Predictor may be reading the source radiograph, not lesion difficulty | **CLOSED** | FINDINGS §2.3 |
| 2 | Do grid axes, or detector score alone, match 0.885? | **CLOSED** | FINDINGS §2.2 |
| 3 | 19.9% may be generation failure, not detection failure — needs two controls | **PARTLY CLOSED** | FINDINGS §1, §4 |
| 4 | Centre-in-box matching vs CheXpert firing | **OPEN** | — |
| 5 | No positive claim is made anywhere | **OPEN** | — |
| 6 | Retitle Fig. 2 | **CLOSED** | — |
| 7 | Abstention is evaluated on fitted cases | **CLOSED as a stated limitation** | FINDINGS §6 |
| 8 | Real-only 0.667, CI 0.444–0.862 on 34 cases | **OPEN** | — |
| 9 | Coverage metric is broken → use k-NN recall | **OPEN** | — |
| 10 | Add confidence intervals to Table 1 | **CLOSED** | FINDINGS §6 |
| 11 | 148 cells / 161 images discrepancy | **CLOSED** | — |

---

## 1 · Predictor may be reading the source radiograph — CLOSED

Tested three ways in `notebooks/04` §8.2 on the 155-positive label, all 12 chests scorable.
Full evidence in FINDINGS §2.3.

The mechanism is real: `biomedclip_full` decodes chest identity at **1.000** (12-way, chance
0.083), `biomedclip_crop` at 0.519. But it is not what carries the prediction —
**within-chest AUROC is 0.8032**, not collapsing to 0.5, and chest-centring the embedding
costs only 0.031.

What makes this reportable rather than assertable is §8.3, where the control is calibrated
against synthetic embeddings of known structure using the real chest labels and outcomes. A
*perfect* chest-identity embedding reaches pooled AUROC **0.5557** and within-chest 0.4901.
That is the ceiling, because `StratifiedGroupKFold` holds out whole chests and identity
cannot transfer to an unseen one. Observed: 0.7435 — 0.19 above the ceiling.

Answer in the paper: chest identity is present in the features, is quantified, and is
demonstrably not the signal. Report the calibration table alongside the claim.

## 2 · Do grid axes or detector score alone match 0.885? — CLOSED

`requested_axes` is near chance, consistent with §1 of FINDINGS.

**"Detector score alone" is ill-posed and was not implemented as asked.** If failure is
defined by thresholding `det_edited`, feeding `det_edited` in as a feature is circular and
scores ~1.0. The non-circular substitutes were run instead — `det_background` (the detector's
score on the *unedited* chest) and `chest_onehot` — and both are degenerate by construction:
`det_background` is zero for 693 of 720 rows, and `chest_onehot` produces a constant
prediction on held-out chests, so its AUROC is decided by tie-breaking. Neither is
reportable as a ladder arm. Noted in the notebook so no one reads the sub-0.5 value as
inverse signal.

The substantive question — do you need an embedding at all — is answered in FINDINGS §2.2
and the answer is no. On the unconditioned label `edit_norm` alone scores **0.9212** against
`biomedclip_full` at 0.7146. A one-dimensional conspicuity measure beats the 512-dimensional
embedding by 0.08.

## 3 · 19.9% — generation or detection failure? — PARTLY CLOSED

Two controls now exist and both are clean: **null-edit 0/45**, **backgrounds 0/413**
(FINDINGS §1). So detections are attributable to the edit.

What is still missing is the *comparative* half: the copy-paste arm is the controlled
generator experiment — same chests, same sites, same detector, only the rendering differs —
and **its 648 twins have never been scored** (`det_edited` all NaN). Scoring them yields a
paired test on `radedit_twin` and converts this item from an argument into a measurement.

Blocking nothing. Cheapest open result in the project.

## 4 · Centre-in-box vs CheXpert firing — OPEN

Untouched. `results/table-matching-rules.csv` has the matching-rule sweep for the grid but
the CheXpert comparison was never run. Needs a decision on whether it is in scope for this
venue at all.

## 5 · No positive claim — OPEN

Still the weakest structural point. The material for a claim exists in FINDINGS §1 and §2:
a stress test built on requested attributes measures **generation success** and reports it
as robustness, and the fix is a three-check protocol — generator controls, a realised-
conspicuity covariate, and an explicit synthetic-to-real check. That is a prescription, not
a null result. It is not yet written as one anywhere in the draft.

## 6 · Fig. 2 title — CLOSED

## 7 · Abstention evaluated on fitted cases — CLOSED as a stated limitation

Not fixable without a held-out split, and the honest move is to say so. FINDINGS §6 states
it: the threshold is chosen and evaluated on the same 1,133 cases, and the answered subset
is selected on `max_score`, which correlates with `best_score`, so the FNR falls partly by
construction. The sweep describes a trade-off on this set and is not a held-out guarantee.

Carry that sentence into the paper verbatim. The item is closed by disclosure, not by fix.

## 8 · Real-only 0.667 on 34 cases, CI 0.444–0.862 — OPEN

Do not confuse this with the FROC score of 0.6717 in FINDINGS §5 — **coincidentally similar
numbers, different quantities.** The 0.667 is the real-only failure-predictor AUROC on 34
cases; the 0.6717 is mean FROC sensitivity over seven operating points on 1,133 images.
Flagging because two numbers this close will get conflated.

The CI 0.444–0.862 spans chance. n = 34 cannot support the comparison being asked of it.
Either report it as underpowered with the interval attached, or drop the comparison.

## 9 · Coverage metric broken → k-NN recall — OPEN

The coverage figures in the old draft (0/29, 4/29, 23/29, 29/29 at four radii) are radius
sweeps in an unnormalised embedding space, which is not a coverage measure. Replace with
k-NN recall: for each real failure, is at least one of its k nearest synthetic neighbours
also a failure?

Embeddings exist. No GPU. Blocked only on deciding k and the distance metric.

## 10 · Confidence intervals on Table 1 — CLOSED

Wilson intervals are in `results/table-baseline2-clustered.csv`, and the cluster-bootstrap
check in FINDINGS §6 shows Wilson is **adequate** here (inflation 0.95–1.03×) because there
are only 1.30 nodules per image.

Report both facts. The negative clustering result is what justifies using Wilson on the real
side while using chest-as-unit on the synthetic side, where cluster size is 60.

## 11 · 148 cells / 161 images — CLOSED

---

## Not on the reviewer's list, but owed

**Tell the mentor about the scaling bug.** Outstanding since **18 August**. The longer it
goes unmentioned the worse the disclosure looks, and every number computed before the fix is
implicated.

**Recover the train/val split and training recipe from Dhruv.** Baseline 1 is `epoch_5` of a
run whose hyperparameters were never written down, and there is no recorded split. Until
both surface, **Baseline 3 cannot be compared to Baseline 1 at all** — any FROC difference
also contains whatever the recipe and split difference contributes. This is the longest-lead
dependency in the project and it is not technical.

*Same conversation:* ask who ran the original predictor ablation what its label was, and
whether `synth_full.npz` and `synth_crop.npz` could have been passed in transposed. Both
questions are in items 1–2 above and both are cheaper to answer by asking than by inferring.

**If the split never surfaces, retraining Baseline 1 is part of the cost of Baseline 3.** A
new split plus a new recipe means the existing checkpoint is not a valid comparator, so a
fair generator comparison needs *both* arms retrained — 12 to 20 GPU-hours against a 12-hour
session cap, not 6 to 10. Note that the copy-paste vs RadEdit comparison the paper actually
needs for item 3 is **inference only** and needs no training at all.

**`requirements-lock.txt`** from the session that produced the grid. `requirements.txt` has
no pins.

**`04_ablation_ladder.ipynb` is missing.** Its results are committed in
`results/table-predictor-ablation.csv` but the code that produced them is not in the repo.
That is a reproducibility hole in the one result the paper leans on hardest.
