# Notebooks

Run in order. Each writes a CSV that the next reads, so nothing depends on in-memory state
and any stage can be rerun alone.

| notebook | needs | time | writes |
|---|---|---|---|
| `01_generate_grid.ipynb` | GPU, NODE21, HF token | ~3 h | `grid_v5.csv` + 720 images |
| `02_embeddings.ipynb` | GPU, grid, NODE21 | ~15 min | five `.npz` |
| `03_baselines.ipynb` | GPU, checkpoint, NODE21 | ~1.5 h | `froc.csv`, `per_nodule.csv` |
| `04_ablation_ladder.ipynb` | CPU, grid + embeddings | ~30 min | ladder tables |

`01` is gated on accepting the terms at huggingface.co/microsoft/radedit and setting an
`HF_TOKEN` Colab secret.

**`04` is not yet in the repository.** The blocks that need no embeddings have been run;
the notebook itself still has to be committed.

## Seeding

`01` includes a `stable_seed` cell that must run before generation. The original version
seeded from `abs(hash(image_id))`, and Python salts string hashing per interpreter — so a
rerun produced a *different* grid rather than the same one.

The cell also reloads the seeds recorded in `results/grid_v5.csv`, so the existing 720
images reproduce exactly while anything new is deterministic.

> Diffusion on GPU is bit-reproducible on the same hardware and library versions, not
> across them. `torch.manual_seed` fixes the sampling noise, not cuDNN kernel selection.

## Two things that cost hours if skipped

**Run the preflight cells in `01` before the three-hour generation.** They draw the
detected lung boxes and candidate lesion sites on eight chests, and check that the overlap
manipulation produces a real density difference. A geometry error caught at the preflight
costs two minutes; caught afterwards it costs the run. This is how the original
medial/lateral assumption was found to be wrong — the densest site is lateral at the apex
and medial at the base, so a fixed rule was wrong in the upper zone 100% of the time.

**Stage `.mha` files to local disk first.** Reading them one at a time over a mounted Drive
stalls inside a C call where `KeyboardInterrupt` cannot reach it. That failure looks like an
infinite loop and needs a runtime restart.

## Known limits of `03`

As committed it scores all 4,882 images in one pass, which overran a 12-hour Colab session.
Two changes are needed before rerunning: score the 1,134 positives first and the clean
images as a second pass, and checkpoint the per-image detection JSONs to Drive every ~50
images so a session death costs 50 images rather than everything.

## Outputs are stripped

All notebooks are committed without cell outputs — they were ~9 MB of embedded PNGs. The
figures they produce are in `results/figures/`.
