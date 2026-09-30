# Notebooks

Paths come from the canonical block described in `CONFIG_CELL.md`; `src/check_paths_sync.py`
fails if any copy drifts. Drive layout is in `../DRIVE_LAYOUT.md`.

## For the revisions, run one notebook

**`08_revision_run.ipynb`** produces every remaining number, table and figure in a single
pass, then hands off to Baseline 3. One detector load, one staging pass, everything
resumable.

| § | what | cost | closes |
|---|---|---|---|
| 1–2 | paths, split, detector, environment capture | 2 min | reproducibility |
| 3 | copy-paste twins, paired generator test | 10 min | **item 3** |
| 4 | k-NN coverage | 1 min | **item 9** |
| 5 | all 4,881 images scored native | ~50 min | true FP rate |
| 6 | Baseline 1 FROC, `froc_eval` convention, 4 scopes | 3 min | **item 10** |
| 7 | Baseline 2 abstention, case-level + clustered | 1 min | **items 7, 10** |
| 8 | real-only predictor power check | 1 min | **item 8** |
| 9 | four figures, 300 DPI PNG + vector PDF | 3 min | — |
| 10 | md5 manifest, lockfile, checklist summary | 1 min | reproducibility |
| 11 | hand-off to Baseline 3 | — | — |

Outputs land in `02_results/06_revision/{tables,figures}` with `MANIFEST.csv`,
`environment.json` and `requirements-lock.txt` beside them.

Then **`05_baseline3_augmentation.ipynb`** in a fresh runtime, 6–10 GPU-hours.

## Everything else

| notebook | role | state |
|---|---|---|
| `01_generate_grid.ipynb` | RadEdit grid, 720 images, 12 chests | run; grid in Drive |
| `02_embeddings.ipynb` | BiomedCLIP embeddings | run; 5 npz in Drive |
| `03_baselines.ipynb` | baselines 1 & 2, the long-form version | §1–8 run, §9–10 supersede them |
| `04_predictor_ablation_and_controls.ipynb` | ablation ladder + chest-identity controls | run |
| `05_baseline3_augmentation.ipynb` | augmented training | not run — the only long job left |
| `06_copypaste_scoring.ipynb` | twin scoring, long-form | superseded by `08` §3 |
| `07_knn_coverage.ipynb` | k-NN coverage, long-form | superseded by `08` §4 |
| `08_revision_run.ipynb` | **the revision run** | the one to run |

`06` and `07` are kept because they document their sections at length; `08` is the same
computation with the prose compressed. Run `08`.

## Nothing is blocked on a teammate

Recovered 2026-09-12, all previously-blocking inputs:

| was blocked on | recovered from |
|---|---|
| training recipe | `train_baseline.py` — COCO init, batch 2, seed 42, SGD 0.005/0.9/5e-4, StepLR 3/0.1 |
| train/val/test split | `splits.csv` / `baseline1_splits.csv`, 77,012 B — 907/113/114 annotated + 3,748 clean |
| preprocessing | `algoverse_dataset.py` — max-normalise at native resolution, native-pixel boxes |
| FROC definition | `froc_eval.py` — greedy one-to-one, clean images in the denominator |
| predictor label + protocol | `config.json` — 419 images, 23 positives, `edit_norm > 0.4919`, liblinear, KFold over chests |

One open question needs a person, not code: **where the 0.889 sensitivity in the earlier
draft came from.** No recovered script produces it, and both differences between our FROC and
`froc_eval.py` push sensitivity *down*. Until someone confirms it, it stays out of the paper.

## Two things to put in place first

`splits.csv` → `01_data/00_source/baseline1_splits.csv` (77,012 bytes). `08` and `05` look
there first, then glob, then refuse rather than inventing a split.

`node21_detection_baseline.zip` → `01_data/00_source/node21/` (already there). Only `05`
needs it, for the upstream `training_utils`.

## Conventions that cost something to learn

**`ismount`, not `isdir`.** A plain directory under an unmounted `/content/drive` is also a
dir, and creating one blocks the mount and makes Drive look empty.

**Test for the `01_data` marker, not the root folder.** An unresolved shortcut and a stale
empty directory both exist. That is how a stray empty `results/` tree got created.

**Bulk-stage `.mha` before reading.** Reading them one at a time over the mount stalls inside
a C call where `KeyboardInterrupt` cannot reach it. It looks like an infinite loop and needs a
runtime restart. Twice, hours each.

**Checkpoint to Drive, not `/content`.** 12-hour cap, and `/content` does not survive.
Detections sync every 50 images, training checkpoints every epoch.

**Never let a loop skip silently.** `if not p.exists(): continue` turns a staging failure into
a fast, wrong run. Every loop here asserts instead.

**`SCORE_MIN` is an operating point, not a filter.** Detections are stored with
`box_score_thresh=0.0` and a 300-box cap, so no threshold or matching-rule change needs
inference again.
