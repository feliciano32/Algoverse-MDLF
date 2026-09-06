# Archive

Superseded code, kept because the paper's methods section describes what changed and why.

`generate_grid_v3.py` and `v4` produced the grids that were later invalidated. v3 contains
the coordinate-space bug (F0): mask coordinates were computed against `IMG_SIZE / src_w`
where `src_w` was read *after* the image had already been resized, so the scale factor was
always 1.0. The clamping line

```python
if x1 <= x0: x1 = min(IMG_SIZE, x0 + 20)
```

turned impossible boxes into 20-pixel slivers instead of failing, which is why 89 of 180
images carried a one-pixel mask undetected.

Nothing here should be run. It is provenance.
