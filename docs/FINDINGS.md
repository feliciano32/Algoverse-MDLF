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

**The committed `results/table-predictor-ablation.csv` is reproducible and citable.** The
original harness was recovered on 2026-09-12 from `Algoverse_Predictor_Code_Outputs.zip`
(Dhruv, shared 2026-09-12) and re-run: `biomedclip_full` source-grouped returns **0.816667**
against the committed 0.8166447, on a different scikit-learn version (1.7.2 vs 1.8.0). Input
sha256s match `config.json` exactly. Rerun with:

```bash
python3 src/failure_predictor_ablation.py --out rerun/predictor
```

> **Three retractions.** Between the loss of the harness and its recovery I claimed the table
> was not citable, that `synth_full.npz` and `synth_crop.npz` might have been transposed, and
> that `biomedclip_full` does not really beat `biomedclip_crop`. **All three were wrong**, and
> all three came from my reconstruction of the protocol in `notebooks/04` §3 differing from
> the original in four ways: `StratifiedGroupKFold` instead of plain `KFold` over the 12
> chest IDs, `solver='lbfgs'` instead of `liblinear`, an 11-column `requested_axes` encoding
> that I built with 13 columns by wrongly including `position`, and a painted floor of 0.50
> instead of 0.4919. The `notebooks/04` §8 results computed on the `all_lesion` label are a
> *different experiment*, not a correction of this one.

### 2.1 The recovered protocol

| | |
|---|---|
| cohort | **419 images**, 12 source chests |
| positives | **23** (5.49%) — `det_edited <= 0.05` |
| painted floor | `edit_norm > 0.4919`, calibrated on 69 eligible null edits |
| model | `StandardScaler` per training fold → `LogisticRegression(C=1.0, class_weight='balanced', solver='liblinear', max_iter=5000)`, no tuning |
| folds | 5 folds × 5 repeats, seed 42 |
| ungrouped | `StratifiedKFold` over images |
| grouped | `KFold` over the 12 unique chest IDs, shuffled per repeat, **not label-stratified** |

| features | dim | stratified | source_grouped |
|---|---|---|---|
| biomedclip_full | 512 | 0.845 ± 0.013 | **0.817 ± 0.022** |
| biomedclip_crop | 512 | 0.801 ± 0.025 | 0.750 ± 0.032 |
| edit_norm | 1 | 0.728 ± 0.005 | 0.727 ± 0.005 |
| cnr | 1 | 0.725 ± 0.004 | 0.722 ± 0.006 |
| edit_norm + cnr | 2 | 0.715 ± 0.008 | 0.725 ± 0.007 |
| requested_axes | 11 | 0.566 ± 0.016 | 0.561 ± 0.019 |

The substantive reading is unchanged from §1: requested axes are near chance, and a single
scalar (`cnr` 0.722, `edit_norm` 0.727) is close to the 512-dimensional lesion crop (0.750).

**The painted floor does condition on a competing feature.** `edit_norm > 0.4919` truncates
the variance of `edit_norm` and, by correlation, of `cnr`, so the scalars are handicapped
relative to the embeddings on this cohort. That is a documented design choice — the original
SUMMARY.md calls the filter "a proxy rather than a verified lesion annotation" — not an
error. It does mean the embedding-versus-scalar margin is an upper bound on the embedding's
advantage. `notebooks/04` §8 quantifies the sensitivity on an unconditioned label.

### 2.2 Detector exposure — a confound worth stating plainly

`config.json` records the detector's own split per source chest. **8 of the 12 source chests
were in the detector's training set** (c0005 val; c0012, c0018, c0021 test; the rest train).

| | chests | images | failures | rate |
|---|---|---|---|---|
| train-exposed | 8 | 276 | 20 | 0.0725 |
| held-out | 4 | 143 | 3 | 0.0210 |

Fisher exact p = 0.0392, direction **opposite** to the naive expectation — the detector fails
*more* on chests it trained on. Do not report that as a finding: the held-out arm has **3
failure events**, and 4 of the 12 chests contain zero failures at all. The interval on a
3-event rate is wide enough to swallow the effect.

What to say instead: the design cannot separate lesion difficulty from detector familiarity,
because two thirds of the source radiographs were seen during detector training and the
held-out remainder has too few events to estimate the difference. Grouped predictor folds
make chests unseen to *the predictor*, not to the detector. The original SUMMARY.md flags
this qualitatively; the numbers above make it quantitative.

### 2.3 Checklist item 1 — closed

The concern: `biomedclip_full` beating `biomedclip_crop` could mean the predictor reads the
source radiograph rather than the lesion.

**Computed directly from the original harness's own out-of-fold predictions**
(`oof_predictions.csv`, source-grouped, averaged over the 5 repeats), so this is not a
reconstruction:

| features | pooled AUROC | within-chest AUROC | chests scorable |
|---|---|---|---|
| biomedclip_full | 0.8166 | **0.7933 ± 0.031** | 8/12 |
| biomedclip_crop | 0.7501 | 0.7584 ± 0.048 | 8/12 |
| edit_norm | 0.7265 | 0.7652 | 8/12 |
| cnr | 0.7219 | 0.7595 | 8/12 |
| requested_axes | 0.5610 | 0.5637 ± 0.021 | 8/12 |

Within-chest AUROC does not collapse — 0.7933 against a pooled 0.8166. Only 8 of 12 chests
are scorable because four contain no failures at all.

Supporting controls from `notebooks/04` §8, on the reconstructed cohort:

| control | result |
|---|---|
| chest-ID decodable from `biomedclip_full` | **1.000** (12-way, chance 0.083) |
| chest-ID decodable from `biomedclip_crop` | 0.519 |
| chest-centred embedding, `biomedclip_full` | drop of 0.031 |

The mechanism is real — the whole-image embedding identifies the radiograph perfectly — but
it is not what carries the prediction. Within-chest AUROC does not collapse.

**The control is calibrated against known answers** (`04` §8.3), which is what makes it
reportable. Synthetic embeddings with known structure, using the real chest labels and real
outcomes:

| regime | pooled AUROC | within-chest |
|---|---|---|
| A — perfect chest identity, no lesion info | **0.5557** | **0.4901** |
| B — lesion signal, no chest identity | 1.000 | 1.000 |
| C — both | 0.9791 | 1.000 |
| observed, `biomedclip_full` | 0.7435 | 0.8372 |

Regime A is the ceiling on the confound: because `StratifiedGroupKFold` holds out whole
chests, a chest-identity feature cannot transfer to a held-out chest, so even a *perfect*
one reaches only 0.556 — despite failure rate genuinely spanning 0.061 to 0.648 across
chests. The observed 0.7435 is 0.19 above that ceiling. Chest memorisation cannot account
for the result.

### 2.4 What the preprocessing discovery does *not* touch

Everything in §1 and §2 is a **within-grid** comparison: every arm — lesion, null-edit,
background, every axis level — went through the same 512 px CLAHE pipeline, because RadEdit
only operates at 512 and the grid images were generated that way. A constant cannot confound
a contrast, so the axis effects, the CNR correlation, the controls and this ablation all
stand as measured.

What it does mean is that the detector is being run **out of distribution** on the grid: it
was trained on native-resolution, max-normalised, uncropped images (see §5). So absolute
detection rates on the grid are not the detector's true capability and must not be compared
directly to real-data sensitivity without equalising preprocessing on both sides. See §5 for
which numbers need rescoring.

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

## 4b. The training recipe and split, recovered

Recovered 2026-09-12 from `train_baseline.py`, `algoverse_dataset.py` and `splits.csv`
(Maia's folder), plus `baseline1_splits.csv` in Dhruv's bundle — byte-identical at 77,012 B.
**Nothing needs to be rebuilt.**

| | value |
|---|---|
| backbone | `fasterrcnn_resnet50_fpn(weights="DEFAULT")` — **COCO-pretrained**, explicitly not the upstream `model.pth` |
| head | `FastRCNNPredictor`, 2 classes |
| optimiser | SGD lr 0.005, momentum 0.9, weight decay 0.0005 |
| schedule | `StepLR` step 3, gamma 0.1 |
| epochs / batch / seed | 5 / **2** / **42** |
| train-time aug | `ToTensor` + `RandomHorizontalFlip(0.5)` only |
| checkpoints | `epoch_{n}.pth`, `{"model":…, "epoch":…}` — hence `baseline1_checkpoint.pth` = epoch 5 |
| split | `splits.csv`, `img_name` + `split`, generated deterministically by `build_splits.py` from `metadata.csv` |

Our `05` had assumed `weights=None`, batch 4, seed 0. Random init versus COCO fine-tuning is
not a tuning detail; Baseline 3 would have been incomparable on that alone.

### The preprocessing does not match what our notebooks do

`algoverse_dataset.NoduleDataset` does, per image:

```python
arr = sitk.GetArrayFromImage(sitk.ReadImage(path)).squeeze()
arr = arr.astype(np.float32) / max(arr.max(), 1.0)   # max-normalise
img = Image.fromarray(arr, mode='F')                 # then ToTensor, repeat to 3 channels
# boxes: [x, y, x+w, y+h] in NATIVE pixels
```

**No CLAHE. No percentile clipping. No centre crop. No resize** — the model's own
`GeneralizedRCNNTransform` handles scaling. Our `load_chest` does centre-crop-to-square,
1/99 percentile clip, CLAHE, and resize to 512 with fractional coordinates. Those are
different pipelines, and the checkpoint only ever saw the first.

Two consequences beyond distribution shift: the centre crop *discards image content*, and our
box handling **drops** ground-truth boxes falling outside the crop rather than clamping. On
the current run none were dropped, so it happened not to matter — but that was luck.

## 5. Baseline 1 — FROC on real NODE21

> **These numbers are provisional and must be rescored.** They were produced by feeding the
> checkpoint 512 px, CLAHE, centre-cropped images. §4b shows it was trained on
> native-resolution, max-normalised, uncropped images. The FROC below is the detector
> evaluated out of distribution, which is the most likely explanation for 0.67 here against
> the 0.885/0.889 in the earlier draft. `notebooks/03` now scores **both** pipelines and
> reports the delta. Nothing in §5 or §6 is citable until that runs.

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
