# Archived notebooks

Exploratory work that produced findings still in force, but which should not be run as
pipeline code. Outputs stripped; the conclusions are recorded in each notebook's header
cell and in the main README.

| notebook | what it established |
|---|---|
| `difficulty_sweep.ipynb` | RadEdit is locked to 512 px (so every lesion is a **mass**, not a nodule); prompt text does not control lesion type; conspicuity is a real axis but only post-hoc |
| `frozen_detector_probe.ipynb` | the generate-then-detect loop works, and detector input resolution does not matter — its internal transform rescales everything to ~800 px |
| `preprocessing_standalone.ipynb` | crop don't squash; percentile don't min-max; record what was done |

## Why they are kept rather than deleted

Each contains a result that is quoted in the paper. `difficulty_sweep` in particular is the
evidence behind three stated constraints on the method, and a reader who wants to check
"RadEdit cannot generate a nodule" should be able to see the tensor-shape error that
establishes it.

Two of these also contain **superseded** conclusions, marked as such in their headers. The
frozen-detector probe reported 20 detections out of 20 across five seeds; the 12-chest grid
gives a mean of 0.815 with real failures. The difficulty sweep measured a 40% failure rate
on a single chest that later turned out to be one where RadEdit edits unusually weakly.

Recording a retraction next to the original claim is the only reliable defence against
re-deriving a dead result. That has already happened twice in this project.
