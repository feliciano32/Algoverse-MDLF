"""
Copy-paste lesion insertion — the controlled generator ablation.

WHY THIS EXISTS
    The reviewer asked whether the low synthetic hit rates reflect the DETECTOR or the
    GENERATOR, and wanted a radiologist to adjudicate. Radiologist review is out of reach,
    but a controlled comparison answers it quantitatively: hold the source chests, the
    insertion sites, the mask sizes and the frozen detector constant, and change only how
    the lesion is rendered. Any gap is then attributable to rendering.

    RadEdit arm : diffusion, already generated (grid_v5.csv, 720 images)
    this arm    : real nodule patches cut from annotated NODE21 images and pasted in

MATCHED TO THE GRID
    Every row of grid_v5.csv with arm == 'lesion' gets a copy-paste twin at the same
    cx, cy and the same mask diameter, on the same background. Same image_id with a
    '__cp' suffix. That makes it a paired comparison rather than two separate datasets.

RENDERING
    Naive pasting leaves a seam and an intensity step, which the detector could key on
    instead of the lesion. Two standard mitigations, both recorded so they can be argued
    about later:
      1. intensity match — the patch is shifted so its mean equals the destination's
         local mean, preserving internal texture and contrast
      2. feathered alpha — a raised-cosine falloff over the outer 25% of the radius, so
         there is no hard edge

    No Poisson blending. It is better at hiding seams but it also redistributes the
    lesion's own gradient, which changes the thing being measured.

OUTPUT
    <out>/images/<image_id>__cp.png    the pasted image
    <out>/masks/<image_id>__cp.png     the same mask the RadEdit arm used
    <out>/copypaste.csv                same schema as grid_v5.csv where it overlaps,
                                       plus patch provenance columns

RUN
    python3 copypaste_generate.py --grid grid_v5_ckpt012 \\
        --mha  Algoverse/Node21/Node21_data/node21/cxr_images/original_data/images \\
        --ann  Algoverse/Node21/Node21_data/node21/cxr_images/original_data/metadata.csv \\
        --out  copypaste --seed 0
"""

import argparse
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import SimpleITK as sitk
from PIL import Image

SIZE = 512
FEATHER = 0.25        # outer fraction of the radius over which alpha falls to zero
MIN_PATCH = 12        # ignore annotations smaller than this in source pixels


# ---------------------------------------------------------------- source images

def load_raw(path):
    a = sitk.GetArrayFromImage(sitk.ReadImage(str(path))).astype(np.float32)
    return a.squeeze() if a.ndim == 3 else a


def normalise(a):
    """Same percentile + CLAHE treatment the backgrounds got, so the patch and the
    destination live in the same intensity space."""
    lo, hi = np.percentile(a, [1, 99])
    a = np.clip((a - lo) / (hi - lo + 1e-8), 0, 1)
    return cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)) \
             .apply((a*255).astype(np.uint8)).astype(np.float32) / 255.0


def extract_patches(mha_dir, ann_csv, limit=None):
    """Cut every annotated nodule out of its source image, square and normalised."""
    raw = pd.read_csv(ann_csv)
    raw = raw[raw.img_name != 'n0507.mha']        # byte-identical duplicate of n1059
    pos = raw[raw.label == 1]
    patches = []
    for name, g in pos.groupby('img_name'):
        p = Path(mha_dir)/name
        if not p.exists():
            continue
        img = normalise(load_raw(p))
        H, W = img.shape
        for j, r in enumerate(g.itertuples()):
            side = max(r.width, r.height)
            if side < MIN_PATCH:
                continue
            cx, cy = r.x + r.width/2, r.y + r.height/2
            x0, y0 = int(cx - side/2), int(cy - side/2)
            if x0 < 0 or y0 < 0 or x0+side > W or y0+side > H:
                continue                          # drop, never clamp
            patches.append(dict(src=name.replace('.mha',''), idx=j,
                                side_px=int(side), orig_w=W, orig_h=H,
                                patch=img[y0:y0+side, x0:x0+side].copy()))
        if limit and len(patches) >= limit:
            break
    print(f'{len(patches)} nodule patches from {len({p["src"] for p in patches})} images')
    return patches


# ---------------------------------------------------------------- pasting

def feather_mask(n, feather=FEATHER):
    """Raised-cosine falloff over the outer `feather` of the radius. 1 inside, 0 outside."""
    y, x = np.mgrid[0:n, 0:n]
    r = np.sqrt((x - (n-1)/2)**2 + (y - (n-1)/2)**2) / ((n-1)/2)
    a = np.ones_like(r)
    edge = (r > 1-feather) & (r <= 1)
    a[edge] = 0.5 * (1 + np.cos(np.pi * (r[edge] - (1-feather)) / feather))
    a[r > 1] = 0.0
    return a


def paste(dest01, patch01, cx, cy, diam, size=SIZE):
    """
    Alpha-composite a resized patch at (cx, cy) in fractional coords.
    Returns (composited image, stats dict). Raises if it does not fit -- no clamping.
    """
    d = int(round(diam))
    px, py = int(round(cx*size - d/2)), int(round(cy*size - d/2))
    if px < 0 or py < 0 or px+d > size or py+d > size:
        raise ValueError(f'patch {d}px at ({px},{py}) does not fit')

    patch = cv2.resize(patch01, (d, d), interpolation=cv2.INTER_AREA)
    alpha = feather_mask(d)
    region = dest01[py:py+d, px:px+d]

    # Intensity match on the SURROUND, not the core.
    #
    # Matching the core would set the nodule to the same brightness as the lung it
    # replaces, which erases the contrast that makes it a nodule -- the first attempt did
    # exactly that and produced dark discs. Aligning the surrounding lung instead keeps
    # the nodule's own contrast against its background while removing the brightness step
    # at the seam, which the detector could otherwise key on instead of the lesion.
    core = alpha > 0.9                      # the nodule
    ring = (alpha > 0.05) & (alpha < 0.6)   # surrounding lung, inside the feathered edge
    if ring.sum() < 8:
        ring = ~core
    shift = region[ring].mean() - patch[ring].mean()
    patch = np.clip(patch + shift, 0, 1)

    out = dest01.copy()
    out[py:py+d, px:px+d] = alpha*patch + (1-alpha)*region
    # contrast of the pasted nodule against its own surround -- should be positive
    # (nodules are denser than lung) and roughly preserved from the source
    return out, dict(paste_shift=round(float(shift), 4),
                     lesion_contrast=round(float(patch[core].mean()-patch[ring].mean()), 4),
                     dest_core_std=round(float(region[core].std()), 4))


# ---------------------------------------------------------------- run

def main(a):
    grid = Path(a.grid)
    out = Path(a.out)
    (out/'images').mkdir(parents=True, exist_ok=True)
    (out/'masks').mkdir(parents=True, exist_ok=True)

    g = pd.read_csv(grid/'grid_v5.csv', keep_default_na=False, na_values=[''])
    les = g[g.arm == 'lesion'].reset_index(drop=True)
    print(f'{len(les)} RadEdit lesion cells to mirror, {les.chest.nunique()} chests')

    patches = extract_patches(a.mha, a.ann)
    assert patches, 'no usable nodule patches'
    rng = np.random.default_rng(a.seed)

    bgs = {}
    rows, skipped = [], []
    for _, r in les.iterrows():
        if r.chest not in bgs:
            bp = grid/'backgrounds'/f'{r.chest}.png'
            bgs[r.chest] = np.asarray(Image.open(bp).convert('L'), np.float32)/255.0
        dest = bgs[r.chest]

        # a patch at least as large as the target, so it is downscaled not upscaled --
        # upsampling a small patch invents detail the detector could respond to
        ok = [p for p in patches if p['side_px'] >= r.mask_px_requested]
        pool = ok if ok else patches
        p = pool[rng.integers(len(pool))]

        try:
            comp, stats = paste(dest, p['patch'], r.cx, r.cy, r.mask_px_requested)
        except ValueError as e:
            skipped.append(dict(image_id=r.image_id, reason=str(e))); continue

        iid = f'{r.image_id}__cp'
        Image.fromarray((comp*255).astype(np.uint8)).convert('RGB') \
             .save(out/'images'/f'{iid}.png')
        # reuse the RadEdit arm's mask verbatim, so the target box is identical
        Image.open(grid/'masks'/f'{r.image_id}.png').save(out/'masks'/f'{iid}.png')

        d = r.to_dict()
        d.update(image_id=iid, arm='copypaste', radedit_twin=r.image_id,
                 patch_src=p['src'], patch_idx=p['idx'], patch_side_px=p['side_px'],
                 scale_factor=round(r.mask_px_requested/p['side_px'], 3),
                 det_edited=np.nan, det_background=r.det_background, gain=np.nan,
                 edit_inside=np.nan, edit_norm=np.nan, cnr=np.nan, n_boxes=np.nan,
                 prompt='copy-paste', **stats)
        rows.append(d)

    cp = pd.DataFrame(rows)
    cp.to_csv(out/'copypaste.csv', index=False)
    if skipped:
        pd.DataFrame(skipped).to_csv(out/'skipped.csv', index=False)

    print(f'\nwrote {len(cp)} images, skipped {len(skipped)}')
    print(f'patch sources used: {cp.patch_src.nunique()} distinct images')
    print(f'downscaled (scale <= 1): {(cp.scale_factor <= 1).mean():.0%}')
    print(f'intensity shift: median {cp.paste_shift.abs().median():.3f}')
    print(f'lesion contrast vs surround: median {cp.lesion_contrast.median():+.4f}, '
          f'{(cp.lesion_contrast>0).mean():.0%} positive (nodules should be BRIGHTER)')
    print('\nDETECTION SCORES ARE NaN -- score these with the frozen detector at 800px,')
    print('exactly as the RadEdit arm was, then merge on radedit_twin for the paired test.')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--grid', required=True)
    ap.add_argument('--mha', required=True)
    ap.add_argument('--ann', required=True)
    ap.add_argument('--out', default='copypaste')
    ap.add_argument('--seed', type=int, default=0)
    main(ap.parse_args())
