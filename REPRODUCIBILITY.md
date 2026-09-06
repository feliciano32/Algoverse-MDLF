# Reproducibility audit

What someone would need to regenerate every artefact from the inputs, and what currently
stops them. Written against the state at the 12-chest grid.

## Verdict

| artefact | reproducible from this repo? |
|---|---|
| `grid_v5.csv` + 720 images | **no** — notebook missing, and seeds are non-deterministic |
| embeddings (5 `.npz`) | **no** — notebook missing |
| `copypaste.csv` + 648 images | **yes** — `src/copypaste_generate.py`, fixed RNG seed |
| `table-matching-rules.csv` | **no** — run ad hoc, script never saved |
| ablation ladder results | **no** — notebook missing |
| the 18 verification checks | **no** — run ad hoc, script never saved |
| figures | **yes** — `src/make_figures.py` |

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

## Blocker 4 — no train/validation split

Baseline 1 was trained by a teammate; which images it saw is unrecorded. Without it:

- real-versus-synthetic cannot separate memorisation from generalisation
- Baseline 3, if run, is not comparable to Baseline 1
- any "held-out" claim is unverifiable

Not a code problem. Someone has to find the split file or the training script.

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

## Order to fix

1. `stable_seed` + read-seeds-from-CSV in the generation notebook — this is the one that
   makes the claim true rather than aspirational
2. Move the four notebooks and three ad-hoc scripts into the repo
3. `pip freeze` from the session that produced the grid
4. Fill the two checksums
5. Chase the train/val split

Items 1–4 are half a day. Item 5 depends on a teammate.
