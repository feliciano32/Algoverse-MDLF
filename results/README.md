# results

Versioned because they are small and carry every number in the paper. The imagery they
derive from is not versioned — see `../data/README.md`.

| file | rows | what it is |
|---|---|---|
| `grid_v5.csv` | 720 | the synthetic grid. 648 lesion + 72 null-edit, 12 chests, 43 columns |
| `skipped.csv` | 8 | chests rejected by the lung-detection screen, with reasons |
| `copypaste.csv` | 648 | copy-paste twins matched to every RadEdit lesion cell. Detection scores pending |
| `table-axis-effects.csv` | 9 | painting rate and detection by level, with Wilson intervals |
| `table-matching-rules.csv` | 32 | hit rate under 8 matching rules × 4 score thresholds |
| `domino_slice_composition.csv` | 40 | attributes of the DOMINO slice members |
| `figures/` | | camera-ready, 300 DPI PNG + vector PDF |

## Reading grid_v5.csv

One row per generated image. The columns that matter:

| column | meaning |
|---|---|
| `arm` | `lesion` or `null_edit`. The null arm requested normal tissue at the same site, mask and seed |
| `overlap` | `clear` / `moderate` / `on_structure` — density percentile of the chosen site, not an anatomical assumption |
| `structure_density` | brightness at the site relative to that lung field's median. >1 means more tissue superimposed |
| `edit_norm` | `edit_inside` divided by local texture. **Use this, not `edit_inside`** — raw edit magnitude is not comparable between chests |
| `cnr` | contrast-to-noise of the painted lesion. The only measured predictor of detection |
| `det_edited` / `det_background` | detector score at the lesion site, edited and untouched |
| `coord_space` | always `fraction_of_image`. Recorded so a future reader never has to infer it |

## Two conventions

**A lesion counts as painted** when `edit_norm` exceeds the maximum reached by the null
arm. That threshold is empirical, not chosen — anything below it is by construction
indistinguishable from asking for normal tissue.

**Rows where `det_background > 0.05` are excluded** from every analysis. The detector
already fires at those sites before any edit, so they are not clean controls. 27 of 720.
