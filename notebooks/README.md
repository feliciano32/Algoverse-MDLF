# Notebooks

Run in order. Each writes a CSV that the next reads, so nothing depends on in-memory
state and any stage can be rerun alone.

| notebook | needs | time | writes |
|---|---|---|---|
| `01_generate_grid.ipynb` | GPU, NODE21, HF token | ~3 h | `grid_v5.csv` + images |
| `02_embeddings.ipynb` | GPU, grid, NODE21 | ~15 min | `*.npz` |
| `03_baselines.ipynb` | GPU, checkpoint, NODE21 | ~1.5 h | `froc.csv`, `per_nodule.csv` |
| `04_ablation_ladder.ipynb` | CPU, grid + embeddings | ~30 min | `table-ablation-ladder.csv` |

`01` is gated on accepting the terms at huggingface.co/microsoft/radedit and setting an
`HF_TOKEN` Colab secret.

## Two things that cost hours if skipped

**Run the preflight cells before the 3-hour generation.** They draw the detected lung
boxes and candidate lesion sites on eight chests, and check that the overlap manipulation
actually produces a density difference. A geometry error found at the preflight costs two
minutes; found afterwards it costs the whole run.

**Stage `.mha` files to local disk first.** Reading them one at a time over a mounted
Drive stalls inside a C call where `KeyboardInterrupt` cannot reach it — that failure
looks like an infinite loop and needs a runtime restart. One bulk copy avoids it.
