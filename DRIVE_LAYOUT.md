# Drive layout — the source of truth

Mapped from Drive itself on **2026-09-12** with the Drive connector. Every path and folder
id below was read off a real folder, not reconstructed from memory. An earlier version of
this file was written from assumption and got the basic shape wrong; if this one and Drive
ever disagree, Drive wins and this file gets corrected.

---

## There is one Algoverse folder, not two

`MyDrive/Algoverse` is a **shortcut** — mimeType `application/vnd.google-apps.shortcut`,
id `16fB6rpTUvW3RK70pcc1dNl90qBdWjPqd`, created 2026-06-06. It points at the shared folder
**`Feliciano_Algoverse`**, id `1Phfz57kr78RzGOVd6r-a-k1Q2rL5S3yl`, owned by
`fserrano1@hwemail.com`.

They are the same folder. Writing to one writes to the other. There is nothing to mirror,
nothing to copy across, and no "working root vs team root" distinction — a previous version
of this document claimed there was, and that was wrong.

The Colab FUSE mount resolves the shortcut as an ordinary directory, which is why
everything has worked through `MyDrive/Algoverse` all along. If the shortcut is ever
deleted, recreate it: Drive → **Shared with me** → right-click `Feliciano_Algoverse` →
*Add shortcut to Drive* → *My Drive*.

---

## Actual structure

```
Feliciano_Algoverse/                          1Phfz57kr78RzGOVd6r-a-k1Q2rL5S3yl
│                                             == MyDrive/Algoverse (shortcut)
├── 01_data/                                  1l3Ne4iUiKGwZQLrBTkdgoYN9sJ3Oyk7y
│   ├── 00_source/                            1xnqPzyzbFOE45aexXmPRpDpSgrAG0Q0v
│   │   ├── node21/                           1yIm5lkqxJMmNAQEFUUzcRPXc1fnvuszB
│   │   │   ├── images/                       1xqnskgGoBPVXMpF8uD51GfhNdEbM1xLK
│   │   │   │                                 4,882 .mha (3,748 c*, 1,134 n*)
│   │   │   ├── metadata.csv                  139,559 B — 5,224 rows, 1,476 label==1
│   │   │   ├── node21_image_dims.csv         22,710 B
│   │   │   ├── filenames_orig_and_new.csv    45,283 B
│   │   │   └── node21_detection_baseline.zip 6,001 B — the organisers' baseline
│   │   ├── chexpert/                         1SlTWOZ7ONAzKOioc0p9a_zHuHF0ATjDU  not yet used
│   │   └── mimic_cxr/                        1tHX5LfcbAEHLDVyQBQztkGhJVbTmvurn  not yet used
│   │
│   ├── 01_grid/                              19nc2v7U0912fI4OWpE6v5zEvun5kwa9w
│   │   ├── images/                           720 png
│   │   ├── masks/                            720 png
│   │   ├── backgrounds/                      12 png
│   │   ├── detections/                       720 json — every box above 0.05
│   │   ├── grid_v5.csv                       231,145 B — 720 rows, 43 cols
│   │   └── skipped.csv                       568 B — 8 rejected chests
│   │
│   ├── 02_embeddings/                        1sE_vUmKaLkn1F8wfzyrfn8oCeTGb1e1n
│   │   ├── synth_full.npz                    (720, 512)
│   │   ├── synth_crop.npz                    (720, 512)
│   │   ├── real_full.npz                     (1133, 512)   n0507 dropped
│   │   ├── real_crop.npz                     (1474, 512)
│   │   ├── background_full.npz               (12, 512)
│   │   ├── real_crop_index.csv               62,802 B
│   │   └── embeddings_hashes.json            285 B
│   │
│   └── 03_copypaste/                         1_Vgyx3LVjpj-Nz14W_lAJkT5VKGGcayj
│       ├── images/                           648 png
│       ├── masks/                            648 png
│       └── copypaste.csv                     224,950 B — matched to grid by radedit_twin
│
├── 02_results/                               1aTM-txBwej6-EkbCf5sN9KAC62T3Daxk
│   ├── 00_models/                            1n__eRtMemnNXYHaP1GfVTJww1bHMNdnH
│   │   └── baseline1_checkpoint.pth          165,726,756 B   <- .pth, NOT .pt
│   ├── 01_figures/                           13UvrLCrtAV9x0aAhkSibCs6tlHq265uO
│   │   └── Figure2.png                       (Maia's)
│   ├── 02_baselines/                         1c95E3QZ-EbizQnrNlbzm2Kt5ZDO-QdMK  empty
│   ├── 03_predictor/                         created by P.bootstrap()
│   └── 04_baseline3/                         created by P.bootstrap()
│
├── 03_old/                                   15QDeYrv95NphZulWWQkLbNyZORoCVwFE
│   ├── data/      features/ grid_specs/ grid_v4/ misc/
│   ├── results/   baseline3_results/ exploration/ week4_baselines/
│   │              task1.1_marginals.csv, task1.1_marginals_manifest.json
│   └── README.txt
│
├── 04_misc/                                  1Ke4fGuD7rnCjQA0MK038UnxkqV4OlSE6
│   └── Me/
│
└── Copy of MDLF Research Doc Spring 2026     (Google Doc)
```

### The two new subfolders

`02_results/` has `00_models`, `01_figures`, `02_baselines` in Drive already. `03_predictor`
and `04_baseline3` do not exist yet — `P.bootstrap()` creates them, following the same
numbering. Predictor ablation tables and Baseline 3 checkpoints/detections go there rather
than being dropped loose in `02_results/`.

### `03_old/` is quarantine

Nothing in `03_old/` may supply a number in the paper. It holds `grid_v4` (450 images,
two-level overlap, superseded), the week-4 baselines, and the task-1.1 marginals. It is kept
for provenance, not for reuse.

---

## Strays — folders written by notebooks pointed at the old layout

These are the residue of the reorganisation. `P.bootstrap()` lists them on every run with an
item count, so they get cleaned up instead of quietly becoming a second copy of everything.

| path | state | what to do |
|---|---|---|
| `Feliciano_Algoverse/results/baselines/dets/` | empty, created 2026-09-12 22:11 | delete — a run today used the pre-reorg `ROOT/results/` path |
| `MyDrive/grid_v5_runs/` | empty | delete — where `01` used to write checkpoints |
| `MyDrive/Teammates/` | empty | delete — where the checkpoint used to live |
| `MyDrive/grid_v4_runs/` | `grid_v4.csv` (148,663 B), `skipped.csv` | move into `03_old/data/grid_v4/`, then delete |

The `results/baselines/dets/` one is the important signal: it means a notebook was run
**today** against the old paths and silently created a fresh empty tree rather than failing.
That is the failure mode the root-marker check in `paths.py` now prevents — it tests for
`01_data/`, so an empty or unresolved root raises instead of being created.

---

## Old paths → new paths

Every notebook written before 2026-09-06 uses the left column. All of it is dead.

| old | new |
|---|---|
| `Algoverse/data/node21/` | `01_data/00_source/node21/` |
| `Algoverse/Misc/node21/` | `01_data/00_source/node21/` |
| `Algoverse/Teammates/baseline1_checkpoint.pt` | `02_results/00_models/baseline1_checkpoint.pth` |
| `Algoverse/data/grid_v5b_runs/data/` | `01_data/01_grid/` |
| `Algoverse/grid_v5b_runs/` | `01_data/01_grid/` |
| `Algoverse/embeddings/` | `01_data/02_embeddings/` |
| `Algoverse/data/copypaste_v2/` | `01_data/03_copypaste/` |
| `Algoverse/results/baselines/` | `02_results/02_baselines/` |
| `Algoverse/results/baseline3/` | `02_results/04_baseline3/` |
| `Algoverse/data/radedit_synthetic/` | `03_old/data/grid_v4/` — superseded, do not use |

> **`grid_v5b_runs` was a checkpoint folder, not a grid folder.** The generation notebook
> wrote checkpoint zips into it and the grid landed one level down in `data/`, which is why
> the old path reads `grid_v5b_runs/data/`. The grid is now `01_data/01_grid/` and
> checkpoints go under `02_results/` — different kinds of thing that were never meant to
> nest.

---

## Which grid is current

`01_data/01_grid/grid_v5.csv` — **231,145 bytes**, 720 rows, 12 chests, 43 columns,
three-level overlap axis. Verified by `src/verify_grid.py`, 18 structural checks.
`P.bootstrap()` prints the byte count and flags it if it is not 231,145.

`03_old/data/grid_v4/` and `MyDrive/grid_v4_runs/grid_v4.csv` hold the v4 grid: 450 images,
two-level overlap, superseded. It was pointed at as "the current data" more than once. It is
not.

The BiomedCLIP embeddings were built from **v5** — all 720 keys match the 720 v5 image ids
exactly, including the 72 `__null` controls.

---

## Usage

```python
from paths import P        # or the inline block in notebooks/CONFIG_CELL.md

P.bootstrap()              # mounts, resolves the root, verifies inputs, lists strays
                           # raises on a missing required input

P.NODE21_IMAGES            # .../01_data/00_source/node21/images
P.NODE21_META              # .../01_data/00_source/node21/metadata.csv
P.CHECKPOINT               # .../02_results/00_models/baseline1_checkpoint.pth
P.GRID_CSV                 # .../01_data/01_grid/grid_v5.csv
P.EMBEDDINGS               # .../01_data/02_embeddings
P.COPYPASTE_CSV            # .../01_data/03_copypaste/copypaste.csv
P.BASELINES                # .../02_results/02_baselines
P.BASELINE3                # .../02_results/04_baseline3
P.PREDICTOR                # .../02_results/03_predictor
```

### The notebooks do not import this module

Colab has no copy of the repo, and cloning a private repo from inside a notebook needs a
token. So each notebook carries the same resolution block inline as its cell 2. The block is
kept verbatim in `notebooks/CONFIG_CELL.md`.

**A layout change therefore has to be made in three places:** `src/paths.py`,
`notebooks/CONFIG_CELL.md`, and cell 2 of each affected notebook. That duplication is
deliberate — the alternative is a notebook that cannot run without repo access — but it is
the thing most likely to drift, so it is written down here.

---

## Rules

**Never hard-code a Drive path anywhere except the one config cell.** That is how `01` came
to write the grid somewhere `02` did not look.

**Test for the `01_data` marker, not for the root folder.** An unresolved shortcut and a
directory created under an unmounted `/content/drive` both exist and are both empty. That is
how a stray `results/` tree got created today.

**Never write into `01_data/00_source/`.** Inputs only.

**Long runs checkpoint to Drive, not to `/content`.** Colab caps sessions at 12 hours and
`/content` does not survive. Detection loops sync every 50 images; training checkpoints every
epoch. Both have already been lost once to this.

**`03_old/` is read-only.** No number in the paper comes out of it.
