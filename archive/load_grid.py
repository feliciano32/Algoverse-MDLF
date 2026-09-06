"""
Canonical loaders. Import these in Colab rather than reading files directly.

    !cp /content/drive/MyDrive/load_grid.py .
    from load_grid import load_grid, load_features

    full, valid = load_grid()                    # 161, 132
    X = load_features(FEATURES_NPZ, valid)       # (132, 512), aligned by ID

WHY THIS IS SO SMALL NOW
    grid_annotated.csv already contains the merged, deduped, annotated frame --
    spec + hit/miss + source + geometry + valid_for_analysis. This module just reads
    it and enforces the tripwires. Do NOT reintroduce merging here; two routes to the
    same dataframe is exactly how this project ended up with 89-vs-29 labelings, two
    predictor checkpoints, and a stub embeddings file.

WHICH FILE FOR WHAT
    grid_annotated.csv                        per-image, canonical. Use this.
    george_worst_groups.csv                   per-cell, computed on the contaminated
                                              161, no source column. Stale derivative.
    biomedclip_features_radedit_v2_full.npz   the real embeddings, 161 x 512.
    synth_features_768.npz                    STUB -- 180 rows, all identical. See
                                              FINDINGS.md F2. Never use.
"""

import glob
import hashlib
import os

import numpy as np
import pandas as pd

GRID_CSV = "/content/drive/MyDrive/Algoverse/grid_annotated.csv"
FEATURES_SHA256 = "18335d0891acac500aefb236e2eb03e840a5fd48db4594d88b5cdaae104c270f"

# Update these deliberately if the exclusion list changes (e.g. if the F13 placement
# check condemns heart as well). A failure here means something upstream moved.
EXPECT_FULL, EXPECT_FULL_HITS = 161, 32
EXPECT_VALID, EXPECT_VALID_HITS = 132, 32


def load_grid(path=GRID_CSV, verbose=True):
    """Return (full, valid) from the annotated grid.

    full  -- all 161 QC-passing images, exclusions flagged not deleted
    valid -- the analysis set, currently 132

    Use `valid` for every result. Use `full` only to reproduce published numbers.
    """
    if not os.path.exists(path):
        # Drive paths are case-sensitive in Colab and the folder has moved once.
        hits = glob.glob("/content/drive/MyDrive/**/grid_annotated.csv", recursive=True)
        if not hits:
            raise FileNotFoundError(
                f"{path} not found, and no grid_annotated.csv anywhere under MyDrive. "
                f"Check the folder name -- 'Algoverse' and 'algoverse' are different paths."
            )
        print(f"note: {path} missing, using {hits[0]}")
        path = hits[0]

    g = pd.read_csv(path)
    v = g[g["valid_for_analysis"]].copy()

    if verbose:
        print(f"full  {len(g):>4} images, {g.hit.sum():>2} hits")
        print(f"valid {len(v):>4} images, {v.hit.sum():>2} hits ({v.hit.mean():.3f})")
        excl = g.loc[~g.valid_for_analysis, "anatomy_overlap"].value_counts()
        for k, n in excl.items():
            print(f"  excluded: {n} x {k}")

    assert (len(g), g.hit.sum()) == (EXPECT_FULL, EXPECT_FULL_HITS), \
        f"expected {EXPECT_FULL}/{EXPECT_FULL_HITS}, got {len(g)}/{g.hit.sum()}"
    assert (len(v), v.hit.sum()) == (EXPECT_VALID, EXPECT_VALID_HITS), \
        f"expected {EXPECT_VALID}/{EXPECT_VALID_HITS}, got {len(v)}/{v.hit.sum()}"
    return g, v


def load_features(npz_path, frame, verify_hash=True):
    """Embeddings aligned to `frame` row-for-row, matched by image ID.

    Matching by ID rather than position is the point -- a matrix written in a
    different order would otherwise produce plausible wrong numbers.
    """
    z = np.load(npz_path, allow_pickle=True)
    ids, feats = z["ids"], z["features"]

    # the one-line check that would have caught the stub file instantly
    n_unique = len(np.unique(feats, axis=0))
    assert n_unique == len(feats), (
        f"only {n_unique} unique rows of {len(feats)} -- this is the broken "
        f"synth_features_768.npz. Use biomedclip_features_radedit_v2_full.npz."
    )

    if verify_hash:
        got = hashlib.sha256(feats.tobytes()).hexdigest()
        if got != FEATURES_SHA256:
            print(f"WARNING: feature hash {got[:16]}... != expected "
                  f"{FEATURES_SHA256[:16]}...  (dtype or ordering may differ)")

    lookup = {str(s): i for i, s in enumerate(ids)}
    idx = frame["synth_image_id"].map(lookup)
    assert idx.notna().all(), f"{idx.isna().sum()} images have no embedding"
    return feats[idx.astype(int).to_numpy()]
