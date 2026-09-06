# src

| file | what it does |
|---|---|
| `figstyle.py` | the locked figure palette, sampled from the approved figures. Import and call `apply_style()` before plotting; `save()` writes 300 DPI PNG and vector PDF |
| `make_figures.py` | regenerates all four result figures from a grid folder |
| `copypaste_generate.py` | the controlled generator ablation — real nodule patches pasted at the same sites and mask sizes as the RadEdit arm |
| `real_vs_synthetic.py` | scores real annotated nodules and compares against the synthetic distribution |

## Palette

Do not introduce new colours. Every hex in `figstyle.py` was sampled from figures already
approved for this project, and camera-ready requires one consistent scheme across all of
them.

```
INK   #2c3e50   titles, labels, ticks
BLUE  #6694de   primary series
SLATE #7982a6   secondary series
CORAL #fc7c7c   reference lines only — chance, thresholds
GRID  #eeeeee   gridlines
```

## Usage

```bash
python3 make_figures.py <grid_folder> <output_folder>

python3 copypaste_generate.py --grid <grid_folder> --mha <node21_images> \
        --ann <metadata.csv> --out copypaste --seed 0

python3 real_vs_synthetic.py --mha <node21_images> --ann <metadata.csv> \
        --grid <grid_folder> --ckpt <checkpoint.pth> [--split <val.csv>]
```
