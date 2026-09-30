# Reproducibility audit

What someone would need to regenerate every artefact from the inputs, and what currently
stops them.

> **Status as of 2026-09-27: four of the five blockers are closed.** Updated after the
> 2026-09-12 recovery of `train_baseline.py`, `algoverse_dataset.py`, `froc_eval.py`,
> `splits.csv` and `failure_predictor_ablation.py`. The per-blocker sections below are kept
> with their original diagnosis, each annotated with how it closed — the diagnosis is worth
> keeping because the same failure modes will recur.

## Verdict

| artefact | reproducible? | by what |
|---|---|---|
| `grid_v5.csv` + 720 images | **yes** | `01_generate_grid.ipynb`, md5-derived seeds, prior seeds read from the CSV |
| embeddings (5 `.npz`) | **yes** | `02_embeddings.ipynb` |
| `copypaste.csv` + 648 images | **yes** | `src/copypaste_generate.py`, fixed RNG seed |
| copy-paste detections + paired test | **yes** | `08_revision_run.ipynb` §3 |
| Baseline 1 FROC | **yes** | `08` §5–6, `froc_eval.py` convention, `splits.csv` |
| Baseline 2 abstention | **yes** | `08` §7 |
| k-NN coverage | **yes** | `08` §4 |
| predictor ablation ladder | **yes** | `failure_predictor_ablation.py`, reproduces to 6 dp |
| chest-identity controls | **yes** | `04_predictor_ablation_and_controls.ipynb` §8 |
| `table-matching-rules.csv` | **no** | still run ad hoc, script never saved |
| the 18 verification checks | **yes** | `src/verify_grid.py` |
| figures | **yes** | `src/make_figures.py`, `08` §9 |
| Baseline 3 | **not yet run** | `05_baseline3_augmentation.ipynb`, recipe recovered |

One gap left: `table-matching-rules.csv`. It is a result in the paper with no code behind it.

---

## Blocker 1 — generation seeds are not deterministic

`generate_grid_v5.ipynb` derives each image's seed as:

```python
seed = abs(hash(image_id)) % (2**31)
```

Python salts string hashing per process, so this returns a different value on every run:

```
$ for i in 1 2 3; do python3 -c "print(abs(hash('c0001_left_upper_clear_small')))"; done
665438937
2107643189
1914110162
```

A rerun therefore produces a *different grid*, not the same one. The claim in the README
that "the seed is derived deterministically from each `image_id`, so a rerun is
byte-identical" is **false as written**.

**Fix** — a stable hash:

```python
import hashlib
def stable_seed(image_id: str) -> int:
    """Deterministic across processes and machines. Python's built-in hash() is salted
    per interpreter, so it cannot be used for anything that must reproduce."""
    return int(hashlib.md5(image_id.encode()).hexdigest()[:8], 16) % (2**31)
```

**Mitigation for the existing grid** — the seeds actually used are recorded in
`grid_v5.csv`. A rerun can reproduce the current images exactly by reading the seed from
the CSV rather than recomputing it. Add this to the notebook:

```python
KNOWN = dict(zip(prev.image_id, prev.seed)) if prev is not None else {}
seed = KNOWN.get(image_id, stable_seed(image_id))
```

That makes the existing 720 images reproducible *and* future ones deterministic.

> Residual caveat: diffusion on GPU is only bit-reproducible on the same hardware and
> library versions. `torch.manual_seed` fixes the sampling noise, not cuDNN kernel
> selection. Same-GPU reruns should match; a different card may not. Worth one line in
> Methods rather than a claim of exact reproducibility.

---

## Blocker 2 — four notebooks and three scripts are not in the repo

| missing | produces | where it is |
|---|---|---|
| `01_generate_grid.ipynb` | the grid | project notes folder |
| `02_embeddings.ipynb` | the five `.npz` | chat cells only |
| `03_baselines.ipynb` | FROC, abstention sweep | chat cells only |
| `04_ablation_ladder.ipynb` | the predictor ablations | project notes folder |
| `verify_grid.py` | the 18 structural checks | run ad hoc |
| `matching_rules.py` | `table-matching-rules.csv` | run ad hoc |
| `ablation_ladder.py` | ladder tables | run ad hoc |

Anything "run ad hoc" is a result in the paper with no code behind it. That is the same
class of problem as the original grid: a number nobody can re-derive.

---

## Blocker 3 — the environment is not pinned

`requirements.txt` uses `>=`, so a fresh install gets whatever is current. Diffusers and
transformers both change generation behaviour between minor versions.

**Fix** — capture what actually ran, from the Colab session that produced the grid:

```python
!pip freeze > requirements-lock.txt
```

and record the GPU:

```python
import torch
print(torch.__version__, torch.version.cuda, torch.cuda.get_device_name(0))
```

---

## Blocker 4 — no train/validation split — **CLOSED 2026-09-12**

*Original diagnosis:* Baseline 1 was trained by a teammate; which images it saw is
unrecorded. Without it, real-versus-synthetic cannot separate memorisation from
generalisation, Baseline 3 is not comparable to Baseline 1, and any "held-out" claim is
unverifiable.

**Recovered.** `splits.csv` / `baseline1_splits.csv`, 77,012 bytes, byte-identical in three
places. Columns `img_name` and `split`; generated deterministically by `build_splits.py` from
`metadata.csv`, so it was never a lost random draw.

```
train  3855   (907 annotated, 2948 clean)
val     488   (113 annotated, 375 clean)
test    489   (114 annotated, 375 clean)
clean_canvas  50
```

Consequences now available: val- and test-only FROC (`08` §6), and a Baseline 3 comparison
against a valid comparator.

**And the training recipe came with it**, which was the larger half of the problem:

| | |
|---|---|
| backbone | `fasterrcnn_resnet50_fpn(weights="DEFAULT")` — COCO, not random init |
| optimiser | SGD lr 0.005, momentum 0.9, weight decay 0.0005 |
| schedule | `StepLR` step 3, gamma 0.1 |
| epochs / batch / seed | 5 / 2 / 42 |
| train-time aug | `ToTensor` + `RandomHorizontalFlip(0.5)` |

`05` had guessed `weights=None`, batch 4, seed 0. Random init versus COCO fine-tuning would
have invalidated the comparison on its own.

**Residual limitation, not fixable.** NODE21 ships no patient identifiers, so the split is
image-level and two studies of one patient can land on opposite sides. Recovering the split
makes the comparison internally consistent; it does not make it patient-level. State it.

---

## Blocker 6 — preprocessing did not match training — **found 2026-09-12, measured**

Not in the original audit because nobody knew. `algoverse_dataset.py` max-normalises at
native resolution with native-pixel boxes: no CLAHE, no percentile clip, no crop, no resize.
`src`'s `load_chest` does all four. Every real-data number before 2026-09-27 fed the
checkpoint images it had never seen in training.

Measured cost: **+0.034 mean FROC** moving to the training-matched path, monotone across all
seven operating points. Small, but it means §5–§8 of `03_baselines.ipynb` were
out-of-distribution measurements. `08` §5–6 supersede them.

Two secondary defects in the old path, both now gone: the centre crop discarded image
content, and ground-truth boxes outside the crop were **dropped** rather than clamped. None
were dropped on the last run, which was luck rather than design.

The grid is unaffected — it is intrinsically 512+CLAHE because RadEdit only runs at 512, and
every arm shares that pipeline, so within-grid contrasts cannot be confounded by it.

---

## Blocker 5 — MANIFEST checksums are blank

Two of three are unfilled, so nobody can confirm they have the same grid or the same
embeddings.

```bash
md5 01_ARTIFACTS/grid_v5_ckpt012.zip 01_ARTIFACTS/embeddings.zip
```

---

## What is already sound

**Provenance in every row.** `grid_v5.csv` carries original dimensions, crop offsets,
scale, lung box, requested and achieved mask size, and `coord_space`. Any image can be
traced back to its source without guessing.

**Raw detector output saved per image.** Changing a score threshold or a matching rule
never requires rerunning inference — the matching-rule sweep cost nothing for this reason.

**Backgrounds saved.** The contrast axis derives post-hoc with no generation.

**Empirical thresholds, not chosen ones.** "Painted" is defined by the null arm's maximum
`edit_norm`, so it is measured rather than asserted.

**The verification is structural, not statistical.** Every mask is measured back from its
own PNG and compared to what the CSV claims. That check would have caught the bug that
invalidated four earlier grids, in seconds.

---

## Order to fix — current

1. ~~`stable_seed` + read-seeds-from-CSV~~ — **done**, md5-derived, prior seeds read from the CSV
2. ~~Move the notebooks into the repo~~ — **done**, `01`–`08` are all tracked
3. ~~`pip freeze`~~ — **done**, `08` §2 writes `requirements-lock.txt` from the session that
   produces the numbers, alongside `environment.json` with the GPU and every input md5
4. ~~Fill the checksums~~ — **done**, `08` §10 writes `MANIFEST.csv` hashing every output
5. ~~Chase the train/val split~~ — **done**, recovered with the recipe

Remaining, in order:

6. **`table-matching-rules.csv` has no script.** The last result in the paper with no code
   behind it. Same class of problem as the original grid.
7. **Run `08_revision_run.ipynb`.** About 70 minutes, closes items 3, 7, 8, 9 and 10 and
   writes every table, figure, hash and lockfile.
8. **Run `05_baseline3_augmentation.ipynb`.** 6–10 GPU-hours, one arm, valid comparator.
9. **Ask where 0.889 came from.** Not a code problem — no recovered script produces it, and
   both differences between our FROC and `froc_eval.py` push sensitivity *down*, so it cannot
   be reached from our measurements. Most likely the published NODE21 challenge baseline was
   quoted as though it described this checkpoint. Until confirmed, it stays out of the paper.

Nothing on this list waits on a teammate. Item 9 is a question, not a dependency.
