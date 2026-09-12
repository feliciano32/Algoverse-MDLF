# The canonical paths cell

Every notebook's path cell starts with the block below, **verbatim**. Mapped from Drive
2026-09-12 with the Drive connector; the full layout with folder ids is in
`../DRIVE_LAYOUT.md`.

## Why this is duplicated instead of imported

`src/paths.py` is the same layout as a module, and scripts use it. The notebooks cannot:
Colab has no copy of this repo, and cloning a private repo from inside a notebook needs a
token. So the block is pasted into each notebook as its paths cell.

That means a layout change has to be made in **three** places — `src/paths.py`, this file,
and the paths cell of each notebook. To catch drift, run:

```bash
python src/check_paths_sync.py
```

It compares the block in all four notebooks against this file byte for byte and exits
non-zero on a mismatch.

## Where the block lives

| notebook | cell | tail after the shared block |
|---|---|---|
| `01_generate_grid.ipynb` | after the HF-login/mount cell | `CHECK` only — writes via `RUNS` and `GRID` |
| `02_embeddings.ipynb` | cell 0 | `CHECK` only — reads `GRID`, writes `EMB_DIR` |
| `03_baselines.ipynb` | cell 2 | `OUT`/`DEST` = `B1_DIR`, sync helpers |
| `05_baseline3_augmentation.ipynb` | cell 2 | `OUT`/`DEST` = `B3_DIR`, sync helpers |

`01` and `02` have already been run and their outputs are in Drive; they were repointed so a
rerun does not recreate the old tree.

---

## The shared block

```python
# ===========================================================================
# CANONICAL DRIVE PATHS
# Mirrored from src/paths.py and notebooks/CONFIG_CELL.md. Mapped from Drive
# 2026-09-12 with the Drive connector. Change all three together.
# Full layout, folder ids and the old->new table: DRIVE_LAYOUT.md
# ===========================================================================
!pip -q install SimpleITK
import os, json, glob, time, shutil, subprocess, random
from pathlib import Path
from google.colab import drive

# --- mount -----------------------------------------------------------------
# ismount(), not isdir(). A plain local directory under an unmounted
# /content/drive is also a dir, and creating one blocks the mount and makes
# Drive look empty -- that happened once and looked like a wiped Drive.
if not os.path.ismount('/content/drive'):
    if Path('/content/drive').exists():
        os.system('fusermount -u /content/drive 2>/dev/null')
        shutil.rmtree('/content/drive', ignore_errors=True)
    drive.mount('/content/drive')
assert Path('/content/drive/MyDrive').is_dir(), 'mount failed'

# --- resolve the root ------------------------------------------------------
# MyDrive/Algoverse is a SHORTCUT to the shared folder Feliciano_Algoverse.
# One folder, not two; the FUSE mount resolves it as a directory.
# Test for the 01_data marker, never for the root itself: an unresolved
# shortcut and a stale empty directory both "exist", and that is exactly how
# a stray empty results/ tree got created on 2026-09-12.
ROOT = None
for _c in ['/content/drive/MyDrive/Algoverse',
           '/content/drive/MyDrive/Feliciano_Algoverse',
           '/content/drive/Shareddrives/Feliciano_Algoverse']:
    if (Path(_c)/'01_data').is_dir():
        ROOT = Path(_c); break
assert ROOT is not None, (
    'Algoverse root not found. Tried MyDrive/Algoverse, '
    'MyDrive/Feliciano_Algoverse, Shareddrives/Feliciano_Algoverse.\n'
    f'MyDrive top level: '
    f'{sorted(p.name for p in Path("/content/drive/MyDrive").iterdir())[:20]}\n'
    'MyDrive/Algoverse is a shortcut to the shared Feliciano_Algoverse. If it '
    'is gone: Drive -> Shared with me -> right-click Feliciano_Algoverse -> '
    'Add shortcut to Drive -> My Drive.')

# --- layout ----------------------------------------------------------------
NODE21    = ROOT/'01_data'/'00_source'/'node21'
MHA_SRC   = NODE21/'images'                      # 4,882 .mha
ANN_CSV   = NODE21/'metadata.csv'                # 5,224 rows, 1,476 label==1
GRID      = ROOT/'01_data'/'01_grid'
GRID_CSV  = GRID/'grid_v5.csv'                   # 231,145 bytes if it is the right one
RUNS      = GRID/'_runs'                         # generation checkpoint zips, not data
EMB_DIR   = ROOT/'01_data'/'02_embeddings'
CPASTE    = ROOT/'01_data'/'03_copypaste'
MODELS    = ROOT/'02_results'/'00_models'
CKPT      = MODELS/'baseline1_checkpoint.pth'    # .pth -- the old .pt path is dead
FIGS      = ROOT/'02_results'/'01_figures'
B1_DIR    = ROOT/'02_results'/'02_baselines'
PRED_DIR  = ROOT/'02_results'/'03_predictor'
B3_DIR    = ROOT/'02_results'/'04_baseline3'

print(f'root: {ROOT}')
```

## Names it defines

| name | resolves to |
|---|---|
| `ROOT` | `MyDrive/Algoverse` (a shortcut to the shared `Feliciano_Algoverse`) |
| `NODE21` / `MHA_SRC` / `ANN_CSV` | `01_data/00_source/node21[/images, /metadata.csv]` |
| `GRID` / `GRID_CSV` | `01_data/01_grid[/grid_v5.csv]` |
| `RUNS` | `01_data/01_grid/_runs` — generation checkpoint zips, not data |
| `EMB_DIR` | `01_data/02_embeddings` |
| `CPASTE` | `01_data/03_copypaste` |
| `MODELS` / `CKPT` | `02_results/00_models[/baseline1_checkpoint.pth]` |
| `FIGS` | `02_results/01_figures` |
| `B1_DIR` | `02_results/02_baselines` |
| `PRED_DIR` | `02_results/03_predictor` |
| `B3_DIR` | `02_results/04_baseline3` |

> `EMB_DIR`, not `EMB`. `02_embeddings.ipynb` uses `EMB` for its local scratch directory,
> and the two shadowed each other in an earlier version of this cell.

> In `02_embeddings.ipynb`, `GRID` is reassigned to the local copy (`/content/grid`) after
> the copy cell runs. That is deliberate and commented at the point it happens.

---

## Tail — `03_baselines.ipynb`

```python

OUT  = Path('/content/baselines');      (OUT/'dets').mkdir(parents=True, exist_ok=True)
DEST = B1_DIR;                          (DEST/'dets').mkdir(parents=True, exist_ok=True)
FIGS.mkdir(parents=True, exist_ok=True)

# --- verify inputs ---------------------------------------------------------
for _p in (MHA_SRC, ANN_CSV, CKPT):
    assert _p.exists(), (
        f'{_p} missing.\n  its parent holds: '
        f'{sorted(q.name for q in _p.parent.iterdir())[:12] if _p.parent.is_dir() else "parent does not exist either"}'
        '\n  see the old->new table in DRIVE_LAYOUT.md')
print('inputs ok')

# --- stray folders from the pre-reorganisation layout ----------------------
_stray = [ROOT/'results', ROOT/'data', ROOT/'artifacts', ROOT/'grid_v5b_runs',
          Path('/content/drive/MyDrive/grid_v5_runs'),
          Path('/content/drive/MyDrive/grid_v4_runs'),
          Path('/content/drive/MyDrive/Teammates')]
_hits = [(p, len(list(p.iterdir()))) for p in _stray if p.is_dir()]
if _hits:
    print('\nstray folders from the old layout (DRIVE_LAYOUT.md lists what to do):')
    for p, n in _hits:
        print(f'  {p}   ({"empty, safe to delete" if n == 0 else str(n) + " items -- CHECK"})')


def sync_to_drive(sub='dets'):
    """Copy anything new to Drive. Cheap, idempotent, and the only reason a dead session
    is survivable -- /content does not persist."""
    n = 0
    for f in (OUT/sub).iterdir():
        if not (DEST/sub/f.name).exists():
            shutil.copy(f, DEST/sub/f.name); n += 1
    return n


def restore_from_drive(sub='dets'):
    """Pull back whatever a previous session managed to save."""
    n = 0
    for f in (DEST/sub).iterdir():
        if not (OUT/sub/f.name).exists():
            shutil.copy(f, OUT/sub/f.name); n += 1
    return n

print(f'\nrestored {restore_from_drive()} detection files from a previous session')
print(f'writing to {DEST}')
```

## Tail — `05_baseline3_augmentation.ipynb`

```python

OUT  = Path('/content/baseline3')
DEST = B3_DIR
for d in [OUT/'aug', OUT/'ckpt', OUT/'dets']:  d.mkdir(parents=True, exist_ok=True)
for d in [DEST/'ckpt', DEST/'dets']:           d.mkdir(parents=True, exist_ok=True)

# --- verify inputs ---------------------------------------------------------
for _p in (MHA_SRC, ANN_CSV):
    assert _p.exists(), (
        f'{_p} missing.\n  its parent holds: '
        f'{sorted(q.name for q in _p.parent.iterdir())[:12] if _p.parent.is_dir() else "parent does not exist either"}'
        '\n  see the old->new table in DRIVE_LAYOUT.md')
print('inputs ok')

# --- stray folders from the pre-reorganisation layout ----------------------
_stray = [ROOT/'results', ROOT/'data', ROOT/'artifacts', ROOT/'grid_v5b_runs',
          Path('/content/drive/MyDrive/grid_v5_runs'),
          Path('/content/drive/MyDrive/grid_v4_runs'),
          Path('/content/drive/MyDrive/Teammates')]
_hits = [(p, len(list(p.iterdir()))) for p in _stray if p.is_dir()]
if _hits:
    print('\nstray folders from the old layout (DRIVE_LAYOUT.md lists what to do):')
    for p, n in _hits:
        print(f'  {p}   ({"empty, safe to delete" if n == 0 else str(n) + " items -- CHECK"})')


def to_drive(sub):
    n = 0
    for f in (OUT/sub).iterdir():
        if not (DEST/sub/f.name).exists():
            shutil.copy(f, DEST/sub/f.name); n += 1
    return n

def from_drive(sub):
    n = 0
    for f in (DEST/sub).iterdir():
        if not (OUT/sub/f.name).exists():
            shutil.copy(f, OUT/sub/f.name); n += 1
    return n

print(f'\nrestored {from_drive("ckpt")} checkpoints, {from_drive("dets")} detection files')
print(f'writing to {DEST}')
print(f"Baseline 1 FROC for comparison will be read from {B1_DIR/'table-froc.csv'}")
```
