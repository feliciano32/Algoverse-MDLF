# Manifest

Checksums for artefacts too large to version, so anyone can confirm they have the same
files rather than a different run.

| artefact | size | md5 |
|---|---|---|
| `baseline1_checkpoint.pth` | 165.7 MB | `710179c54d6658f463ff453522de2a54` |
| `grid_v5_ckpt012.zip` | 254 MB | `5a6a2ddb34a55139aed088a9c45bdf9a` |
| `embeddings.zip` | 8.0 MB | `1e56ec83b734862489bf44bcd30e2aa7` |

Verify with, from a Colab session with Drive mounted (paths per `DRIVE_LAYOUT.md`):

```bash
D=/content/drive/MyDrive/Algoverse
md5sum $D/02_results/00_models/baseline1_checkpoint.pth \
       $D/01_data/01_grid/_runs/grid_v5_ckpt012.zip \
       $D/01_data/02_embeddings/embeddings.zip
```

(macOS: `md5` rather than `md5sum`. The `00_DATA/` and `01_ARTIFACTS/` prefixes an earlier
version of this file used never existed in Drive.)

## Grid contents

720 rows / 720 images / 720 masks / 720 detection JSONs / 12 backgrounds.
One schema, 43 columns. 648 lesion + 72 null-edit, 12 chests × 60 cells.

Verified by `src/verify_grid.py` — 18 structural checks, all passing:

- every mask **measured back from its own PNG** matches `mask_px_requested`
- all coordinates in [0,1], `coord_space` uniform
- every mask inside its declared lung box
- zone labels order vertically (0.266 < 0.450 < 0.633)
- overlap levels order by density (0.589 < 0.776 < 1.141)
- size labels exact and distinct (47 / 60 / 74, zero variance)
- no duplicate images, no blanks (minimum std 57.9)
- raw detector boxes present, so threshold and matching sweeps need no rerun
- 27 of 720 fire pre-edit and are recorded for exclusion
- null-edit control present: 72 images, 6 fired

## Embeddings

| file | shape | unique rows |
|---|---|---|
| `synth_full.npz` | (720, 512) | 720 / 720 |
| `synth_crop.npz` | (720, 512) | 720 / 720 |
| `real_full.npz` | (1133, 512) | 1133 / 1133 |
| `real_crop.npz` | (1474, 512) | 1474 / 1474 |
| `background_full.npz` | (12, 512) | 12 / 12 |

Reproducible to zero deviation on rerun. `n0507` is excluded throughout — it is a
byte-identical duplicate of `n1059` carrying a less complete annotation.

The unique-row counts are not decoration. An earlier feature file in this project held one
vector repeated 180 times, and no result computed from it could have been real.
