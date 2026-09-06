"""
Real versus synthetic detection difficulty.

THE CLAIM THIS TESTS
    Are RadEdit-generated lesions detected at different confidence than real annotated
    nodules from the same dataset, by the same frozen detector?

THE ONE THING THAT WOULD INVALIDATE IT
    Real NODE21 images are 1024-3636 px; synthetic are 512. Feed each at its native size
    and any difference confounds RESOLUTION with LESION TYPE. Both sides here go through
    an identical pipeline -- centre-crop to square, 1st-99th percentile clip, CLAHE,
    resize to 512 -- and only then to the detector's 800 px input. The synthetic images
    were produced at 512, so the real ones are brought down to meet them.

COORDINATES
    Annotation boxes arrive in original pixel space and have to survive a square crop and
    two resizes. They are converted to FRACTIONS of the cropped square immediately, which
    makes every later resize a no-op. Boxes that fall outside the crop are DROPPED and
    counted, never clamped -- clamping is what produced F0.

RUN
    python3 real_vs_synthetic.py --mha  /path/to/node21/images \\
                                 --ann  /path/to/metadata.csv \\
                                 --grid grid_v5_ckpt012 \\
                                 --ckpt /path/to/baseline1_checkpoint.pth \\
                                 [--split /path/to/val_split.csv] [--out figures_v2]

OUTPUT
    real_nodule_scores.csv          one row per annotated nodule
    real_dropped.csv                boxes that fell outside the crop, with reasons
    fig-real-vs-synthetic.png/.pdf  distributions, box plot, size confound
    table-real-vs-synthetic.csv     the numbers for the paper
"""

import argparse
import sys
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import SimpleITK as sitk
import torch
import torchvision
from PIL import Image
from scipy import stats
from torchvision.models.detection.faster_rcnn import FastRCNNPredictor
from torchvision.transforms import functional as TF

sys.path.insert(0, str(Path(__file__).parent))
from figstyle import apply_style, save, INK, EDGE, GRID, BLUE, SLATE, SLATE_PALE, CORAL
import matplotlib.pyplot as plt

SIZE, DET_SIZE, SCORE_MIN = 512, 800, 0.05
CHEST_MM = 350.0          # typical chest width, for the mm conversion


# ---------------------------------------------------------------- detector

def load_detector(path, device):
    m = torchvision.models.detection.fasterrcnn_resnet50_fpn(
        weights=None, weights_backbone=None,
        box_score_thresh=0.0,        # 0.0 so nothing the 0.05 cutoff hides is lost
        box_detections_per_img=300)
    m.roi_heads.box_predictor = FastRCNNPredictor(
        m.roi_heads.box_predictor.cls_score.in_features, 2)
    st = torch.load(path, map_location=device)
    m.load_state_dict(st['model'] if 'model' in st else st)
    return m.eval().to(device)


@torch.no_grad()
def detect_all(model, pil, device, size=DET_SIZE):
    im = pil.convert('RGB').resize((size, size), Image.LANCZOS)
    o = model([TF.to_tensor(im).to(device)])[0]
    b, s = o['boxes'].cpu().numpy() / size, o['scores'].cpu().numpy()
    k = s >= SCORE_MIN
    return b[k], s[k]


def best_at(boxes, scores, t):
    """Highest score whose box CENTRE falls inside the target -- the project's matcher.
    The matching-rule sweep showed centre-in-box, IoU>0.1 and IoU>0.2 agree to within
    0.002, so this choice is not load-bearing."""
    return float(max((ss for bb, ss in zip(boxes, scores)
                      if t[0] <= (bb[0]+bb[2])/2 <= t[2]
                      and t[1] <= (bb[1]+bb[3])/2 <= t[3]), default=0.0))


# ---------------------------------------------------------------- preprocessing

def load_chest(path, size=SIZE):
    """IDENTICAL to the generation pipeline. If this drifts, the comparison is void."""
    a = sitk.GetArrayFromImage(sitk.ReadImage(str(path))).astype(np.float32)
    a = a.squeeze() if a.ndim == 3 else a
    oh, ow = a.shape
    s = min(oh, ow)
    x0, y0 = (ow - s) // 2, (oh - s) // 2
    a = a[y0:y0+s, x0:x0+s]
    lo, hi = np.percentile(a, [1, 99])
    a = np.clip((a - lo) / (hi - lo + 1e-8), 0, 1)
    a = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)) \
           .apply((a*255).astype(np.uint8)).astype(np.float32) / 255.0
    a = np.clip(cv2.resize(a, (size, size), interpolation=cv2.INTER_AREA), 0, 1)
    return Image.fromarray((a*255).astype(np.uint8)).convert('RGB'), (ow, oh, s, x0, y0)


# ---------------------------------------------------------------- annotations

def guess_columns(df):
    """NODE21 metadata column names vary between releases."""
    low = {c.lower(): c for c in df.columns}
    def pick(*names):
        for n in names:
            if n in low:
                return low[n]
        return None
    cols = dict(name=pick('img_name', 'image', 'filename', 'file', 'name'),
                x=pick('x', 'x1', 'xmin', 'bbox_x'),
                y=pick('y', 'y1', 'ymin', 'bbox_y'),
                w=pick('width', 'w', 'bbox_width'),
                h=pick('height', 'h', 'bbox_height'),
                label=pick('label', 'class', 'nodule'))
    missing = [k for k, v in cols.items() if v is None and k != 'label']
    if missing:
        raise SystemExit(f'could not identify columns {missing} in {list(df.columns)}\n'
                         f'edit guess_columns() or rename them')
    return cols


def score_real(mha_dir, ann_path, model, device, split_path=None):
    raw = pd.read_csv(ann_path)
    C = guess_columns(raw)
    pos = raw[raw[C['label']] == 1] if C['label'] and C['label'] in raw else raw
    print(f'{len(pos)} annotated nodules across {pos[C["name"]].nunique()} images')

    val = None
    if split_path:
        sp = pd.read_csv(split_path)
        val = set(sp.iloc[:, 0].astype(str).str.replace('.mha', '', regex=False))
        print(f'validation split: {len(val)} images')

    rows, dropped = [], []
    for name, g in pos.groupby(C['name']):
        fn = name if str(name).endswith('.mha') else f'{name}.mha'
        p = Path(mha_dir) / fn
        if not p.exists():
            dropped.append((name, 'file missing')); continue
        img, (W, H, s, x0, y0) = load_chest(p)
        boxes, scores = detect_all(model, img, device)

        for _, r in g.iterrows():
            # original pixels -> fractions of the CROPPED SQUARE. Every later resize is
            # then a no-op, which is the whole point.
            fx0 = (r[C['x']] - x0) / s
            fy0 = (r[C['y']] - y0) / s
            fx1 = (r[C['x']] + r[C['w']] - x0) / s
            fy1 = (r[C['y']] + r[C['h']] - y0) / s
            if not (0 <= fx0 < fx1 <= 1 and 0 <= fy0 < fy1 <= 1):
                dropped.append((name, f'box outside crop '
                                      f'{fx0:.2f},{fy0:.2f},{fx1:.2f},{fy1:.2f}'))
                continue                      # drop, never clamp
            t = (fx0, fy0, fx1, fy1)
            stem = str(name).replace('.mha', '')
            rows.append(dict(
                img_name=stem, orig_w=W, orig_h=H, crop_side=s,
                split=('val' if (val and stem in val) else 'train' if val else 'all'),
                fx0=round(fx0, 4), fy0=round(fy0, 4), fx1=round(fx1, 4), fy1=round(fy1, 4),
                box_frac_w=round(fx1-fx0, 4),
                approx_mm=round(CHEST_MM * (fx1-fx0), 1),
                det_score=round(best_at(boxes, scores, t), 4),
                n_boxes=int(len(scores))))

    real = pd.DataFrame(rows)
    drp = pd.DataFrame(dropped, columns=['img_name', 'reason'])
    print(f'scored {len(real)}, dropped {len(drp)}')
    if len(drp):
        print(drp.reason.str.split(' ').str[:3].str.join(' ').value_counts().to_string())
    return real, drp


# ---------------------------------------------------------------- synthetic side

def load_synth(grid_dir):
    d = pd.read_csv(Path(grid_dir)/'grid_v5.csv', keep_default_na=False, na_values=[''])
    nul = d[(d.arm == 'null_edit') & (d.det_background <= 0.05)]
    les = d[(d.arm == 'lesion') & (d.det_background <= 0.05)].copy()

    # "painted" is defined by the null arm, not an arbitrary constant: anything at or
    # below the strongest normal-tissue edit is indistinguishable from no lesion.
    floor = nul.edit_norm.max()
    les['painted'] = les.edit_norm > floor
    P = les[les.painted].copy()
    P['approx_mm'] = (CHEST_MM * P.mask_px_requested / SIZE).round(1)
    print(f'synthetic: {len(les)} lesion rows, {len(P)} painted (floor {floor:.3f}), '
          f'{P.chest.nunique()} chests')
    return P


# ---------------------------------------------------------------- compare

def compare(real, synth, out):
    r = real[real.split == 'val'] if (real.split == 'val').any() else real
    if (real.split == 'train').any():
        t = real[real.split == 'train']
        print(f'\ntrain {len(t)} mean {t.det_score.mean():.3f} | '
              f'val {len(r)} mean {r.det_score.mean():.3f} '
              f'-> memorisation gap {t.det_score.mean()-r.det_score.mean():+.3f}')

    rows = []
    for lab, v in [('real (held-out)', r.det_score), ('synthetic (painted)', synth.det_edited)]:
        rows.append(dict(group=lab, n=len(v), mean=round(v.mean(), 3),
                         median=round(v.median(), 3),
                         q25=round(v.quantile(.25), 3), q75=round(v.quantile(.75), 3),
                         found=round((v >= SCORE_MIN).mean(), 3)))
    T = pd.DataFrame(rows)
    print('\n' + T.to_string(index=False))

    u, p = stats.mannwhitneyu(synth.det_edited, r.det_score)
    rb = abs(1 - 2*u/(len(synth)*len(r)))
    print(f'\nMann-Whitney p = {p:.4g}   rank-biserial r = {rb:.3f}')

    # chest-level, so 54 images from one chest are not treated as 54 samples
    per = synth.groupby('chest').det_edited.mean()
    up, pp = stats.mannwhitneyu(per, r.det_score)
    print(f'chest-level (n={len(per)} synthetic chests vs {len(r)} real): p = {pp:.4g}')

    print(f'\nsize: real median {r.approx_mm.median():.1f} mm (max {r.approx_mm.max():.1f}), '
          f'synthetic {sorted(synth.approx_mm.unique())}')
    rr, rp = stats.pearsonr(r.approx_mm, r.det_score)
    print(f'among real nodules, size vs detection: r = {rr:+.3f} (p = {rp:.3g})')
    bigger = (synth.approx_mm.min() > r.approx_mm).mean()
    print(f'{bigger:.0%} of real nodules are smaller than the smallest synthetic lesion')
    print('-> if synthetic score higher AND are larger AND size helps detection among'
          '\n   real nodules, the size confound runs AGAINST the finding, not for it.')

    T['mann_whitney_p'] = p
    T['rank_biserial'] = round(rb, 3)
    Path(out).mkdir(parents=True, exist_ok=True)
    T.to_csv(Path(out)/'table-real-vs-synthetic.csv', index=False)
    return r, p


def figure(r, synth, p, out):
    fig, ax = plt.subplots(1, 3, figsize=(15, 4.4))

    ax[0].hist(r.det_score, bins=30, alpha=.65, density=True, color=SLATE,
               edgecolor=EDGE, linewidth=.6, label=f'real (n={len(r)})')
    ax[0].hist(synth.det_edited, bins=30, alpha=.65, density=True, color=BLUE,
               edgecolor=EDGE, linewidth=.6, label=f'synthetic (n={len(synth)})')
    ax[0].set_xlabel('Detector score', fontweight='bold', color=INK)
    ax[0].set_ylabel('Density', fontweight='bold', color=INK)
    ax[0].set_title('Score distributions', fontweight='bold', color=INK)
    ax[0].legend()

    bp = ax[1].boxplot([r.det_score, synth.det_edited], tick_labels=['real', 'synthetic'],
                       patch_artist=True, showmeans=True, widths=.55,
                       medianprops=dict(color=INK, lw=2),
                       whiskerprops=dict(color=INK), capprops=dict(color=INK),
                       flierprops=dict(marker='o', markersize=3.5,
                                       markerfacecolor='none', markeredgecolor=SLATE),
                       meanprops=dict(marker='D', markersize=5,
                                      markerfacecolor=CORAL, markeredgecolor=EDGE))
    for patch, c in zip(bp['boxes'], [SLATE, BLUE]):
        patch.set_facecolor(c); patch.set_edgecolor(EDGE); patch.set_linewidth(1.2)
    ax[1].set_ylabel('Detector score', fontweight='bold', color=INK)
    ax[1].set_title(f'Mann-Whitney p = {p:.2g}', fontweight='bold', color=INK)

    ax[2].scatter(r.approx_mm, r.det_score, s=20, alpha=.5, color=SLATE,
                  edgecolor=EDGE, linewidth=.3, label='real')
    for mm, sub in synth.groupby('approx_mm'):
        ax[2].scatter([mm]*len(sub), sub.det_edited, s=20, alpha=.5, color=BLUE,
                      edgecolor=EDGE, linewidth=.3)
    ax[2].scatter([], [], s=20, color=BLUE, label='synthetic')
    ax[2].set_xlabel('Lesion size (mm, approx)', fontweight='bold', color=INK)
    ax[2].set_ylabel('Detector score', fontweight='bold', color=INK)
    ax[2].set_title('The size confound runs the wrong way', fontweight='bold', color=INK)
    ax[2].legend()

    for a in ax:
        a.grid(True, color=GRID); a.set_axisbelow(True)
    fig.suptitle('Real versus Synthetic Detection Difficulty',
                 fontsize=17, fontweight='bold', color=INK)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    save(fig, 'fig-real-vs-synthetic', out)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--mha', required=True, help='NODE21 .mha folder')
    ap.add_argument('--ann', required=True, help='annotation csv with boxes')
    ap.add_argument('--grid', default='grid_v5_ckpt012')
    ap.add_argument('--ckpt', required=True)
    ap.add_argument('--split', default=None, help='csv listing validation image names')
    ap.add_argument('--out', default='figures_v2')
    a = ap.parse_args()

    apply_style()
    dev = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f'device: {dev}')
    model = load_detector(a.ckpt, dev)

    real, drp = score_real(a.mha, a.ann, model, dev, a.split)
    real.to_csv(Path(a.out).joinpath('real_nodule_scores.csv') if Path(a.out).exists()
                else 'real_nodule_scores.csv', index=False)
    drp.to_csv('real_dropped.csv', index=False)

    synth = load_synth(a.grid)
    r, p = compare(real, synth, a.out)
    figure(r, synth, p, a.out)
    print(f'\ndone -> {a.out}/')
