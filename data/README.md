# Data

Nothing here is versioned. Four inputs are needed to reproduce the pipeline.

## 1. NODE21 chest radiographs — 29 GB

4,882 `.mha` files (3,748 clean `c*`, 1,134 annotated `n*`) plus `metadata.csv`
(5,224 rows, 1,476 with `label == 1`).

Source: https://node21.grand-challenge.org/ — registration required.

```
data/node21/images/*.mha
data/node21/metadata.csv
```

Only the 1,134 `n*` files are needed for real-nodule scoring; the `c*` files are the
clean backgrounds used as generation canvases.

> **Known issue.** `n0507.mha` and `n1059.mha` are byte-identical (md5
> `f1cfcef93312...`) but carry different annotations — n1059 has three nodules, n0507 has
> two, and two of them match to within a few pixels. This is inter-reader disagreement on
> the same scan. All code here drops `n0507` and keeps the more complete annotation.

## 2. Frozen detector checkpoint — 166 MB

Faster R-CNN ResNet-50 FPN, 2-class head, saved at epoch 5.
md5 `710179c54d6658f463ff453522de2a54`

```
data/baseline1_checkpoint.pth
```

Loads as a bare state dict — there is no `model` wrapper at the top level.

## 3. Generated grid — 266 MB

720 images (12 chests × 54 cells + 6 null-edit controls each), with masks, backgrounds
and per-image detection JSON.

Reproducible from `notebooks/01_generate_grid.ipynb` in about 3 GPU-hours; the seed is
derived deterministically from each `image_id`, so a rerun is byte-identical.

```
data/grid_v5/{images,masks,backgrounds,detections}/
```

`results/grid_v5.csv` is versioned and carries every measurement, so most analysis runs
without the images.

## 4. BiomedCLIP embeddings — 8 MB

```
data/embeddings/{synth,real}_{full,crop}.npz
data/embeddings/background_full.npz
data/embeddings/embeddings_hashes.json
```

Reproducible from `notebooks/02_embeddings.ipynb` in ~15 minutes.

> Assert `len(np.unique(X, axis=0)) == len(X)` on every feature matrix before using it.
> An earlier feature file in this project contained one vector repeated 180 times and
> nothing caught it for weeks.
