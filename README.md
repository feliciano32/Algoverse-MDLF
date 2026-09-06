# Synthetic Lesion Stress Testing Measures the Generator, Not the Detector

Code and results for a study of diffusion-based synthetic lesion insertion as a method for
stress-testing chest X-ray nodule detectors.

## The finding

Every axis of a controlled synthetic attribute grid — lesion size, lung zone, and
anatomical overlap — determines whether the generator **produces a lesion at all**. None of
them affects whether the detector **finds one**.

| axis | P(RadEdit paints a lesion) | detector score, among painted |
|---|---|---|
| anatomical overlap | 0.84 / 0.80 / **0.37** — p = 0.0002 | 0.78 / 0.85 / 0.78 — p = 0.15 |
| lesion size | 0.60 / 0.66 / 0.76 — p = 0.0001 | 0.78 / 0.84 / 0.81 — p = 0.076 |
| lung zone | 0.67 / 0.80 / 0.53 — p = 0.0007 | 0.84 / 0.79 / 0.79 — p = 0.18 |

Chest is the unit of independence throughout (Friedman over 12 chests). Detection among
successfully painted lesions is predicted only by conspicuity (CNR, r = +0.33, p = 4e-12),
not by any anatomical attribute.

**Consequence:** a failure rate measured over such a grid characterises the generator, not
the model under test. Two controls separate them, and both are included here.

## Controls

| control | result | what it rules out |
|---|---|---|
| untouched background at the same site | 0 / 413 fired | the detector responding to the location |
| null edit — normal tissue requested, same site, mask and seed | 0 / 45 fired | the detector responding to *any* edit |
| copy-paste twin — same site and mask, real nodule patch instead of diffusion | 648 images, scoring pending | rendering versus lesion |

## Repository layout

```
src/          analysis and generation code
notebooks/    Colab notebooks, in run order
results/      CSVs and camera-ready figures (small, versioned)
docs/         findings log, reviewer checklist, work split
archive/      superseded generators, kept for provenance
data/         not versioned — see data/README.md
```

## Reproducing

Data is not in the repository (29 GB of source imaging, a 166 MB checkpoint, 720 generated
images). See `data/README.md` for what to obtain and where it goes.

```
1. notebooks/01_generate_grid.ipynb     RadEdit generation, ~3 h GPU  -> results/grid_v5.csv
2. notebooks/02_embeddings.ipynb        BiomedCLIP, ~15 min GPU       -> data/embeddings/
3. src/copypaste_generate.py            copy-paste ablation, CPU      -> results/copypaste.csv
4. src/real_vs_synthetic.py             real-nodule scoring, ~30 min  -> results/real_*.csv
5. notebooks/03_ablation_ladder.ipynb   predictor ablations, CPU
6. src/make_figures.py                  all figures, CPU              -> results/figures/
```

Every step writes a CSV; every later step reads one. Nothing depends on in-memory state
from a previous step, so any stage can be rerun in isolation.

## Design decisions worth knowing before reading the code

**Coordinates are fractions of the image, never pixels.** An earlier version of this grid
computed mask coordinates in the wrong space — the scale factor was always 1.0 because the
image had already been resized before its dimensions were read. 89 of 180 images received a
one-pixel mask, and no check downstream ever asked whether the mask landed where it was
requested. Every coordinate here is a fraction, `coord_space` is recorded in every row, and
`make_mask` **raises** rather than clamping.

**Positions derive from each chest's own anatomy.** The earlier grid reused one set of fixed
coordinates across all backgrounds. Chests differ in size and position within the frame, so
one set cannot land correctly on all of them. Lung fields are detected per chest and every
position is a fraction of that chest's detected lung box.

**The overlap axis is measured, not assumed.** An initial design placed lesions medially and
laterally on the assumption that medial sites carry more overlapping anatomy. That is true at
the lung base and false at the apex, where the lateral edge picks up the clavicle and chest
wall — the assumption was wrong in the upper zone 100% of the time. The final design scans
each zone and selects sites by measured `structure_density` percentile.

**"Painted" is defined by the null arm.** RadEdit's edit strength varies roughly fourfold
between chests, so an absolute threshold is meaningless: an `edit_inside` of 9.44 on one
chest detected at 0.966 while 7.93 on another detected at 0.000. A lesion counts as painted
when its `edit_norm` exceeds the strongest null edit — anything below that is, by
construction, indistinguishable from asking for normal tissue.

**Every detector box above 0.05 is saved as JSON.** Changing a score threshold or a matching
rule never requires rerunning inference. The matching-rule sweep in
`results/table-matching-rules.csv` was produced this way at no compute cost.

## Constraints of the method

**RadEdit is architecturally locked to 512 px.** Generation at 768 or 1024 fails with a
tensor shape mismatch — the UNet carries 64×64 latent structure. The smallest mask that
produces anything is 47 px, roughly 32 mm on a typical chest. The clinical nodule/mass
boundary is 30 mm, so **every lesion this pipeline can produce is a mass, not a nodule.**

**Prompt text does not control lesion type.** Across nodule, mass, consolidation, airspace
opacity and ground-glass opacity, detection ran 0.899 to 0.954 — upward — on visually
indistinguishable images. The prompt must name an anatomical location or nothing is painted
at all (three-word prompts: 0 of 5 seeds), but beyond that it varies nothing.

## Statistical note

Twelve chests contribute 54 images each. Treating those as 648 independent samples inflates
significance: the overlap effect on detection reads p = 0.028 pooled over images and p = 0.15
with chest as the unit. Every test in this repository uses chest as the unit of
independence, and the ablation ladder reports grouped and ungrouped cross-validation side by
side so the gap is visible rather than hidden.

## Citation

Serrano III, F. A., Bhatnagar, D., Li, L., Frank, M., Nijjer, K. Algoverse AI Research.
