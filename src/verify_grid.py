"""
Structural verification of a generated grid.

Eighteen checks. None of them is statistical -- they ask whether the files on disk say
what the CSV claims they say. The check that matters most measures every mask back from
its own PNG: on the grid this pipeline replaced, that would have returned 89 failures,
and nothing at the time was asking.

RUN
    python3 verify_grid.py <grid_folder>
    -> exit 0 if everything passes, 1 otherwise
"""

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

FAILED = []


def check(name, ok, detail=''):
    print(f'{"PASS" if ok else "FAIL"}  {name}' + (f'   {detail}' if detail else ''))
    if not ok:
        FAILED.append(name)


def main(folder):
    G = Path(folder)
    csv = G/'grid_v5.csv' if (G/'grid_v5.csv').exists() else next(G.glob('*.csv'))
    d = pd.read_csv(csv, keep_default_na=False, na_values=[''])

    print('=== STRUCTURE ===')
    check('single schema', len(pd.read_csv(csv, nrows=0).columns) == d.shape[1],
          f'{d.shape[1]} cols')
    check('unique image_id', d.image_id.nunique() == len(d), f'{len(d)} rows')
    check('arms parse (not NaN)', d.arm.notna().all(),
          str(d.arm.value_counts().to_dict()))
    per = d.groupby('chest').size()
    check('equal cells per chest', per.nunique() == 1,
          f'{d.chest.nunique()} chests x {per.iloc[0]}')

    print('\n=== FILES ON DISK, NOT THE CSV ===')
    img = {p.stem for p in (G/'images').glob('*.png')}
    msk = {p.stem for p in (G/'masks').glob('*.png')}
    det = {p.stem for p in (G/'detections').glob('*.json')}
    check('csv == images == masks == detections', set(d.image_id) == img == msk == det,
          f'csv {len(d)} img {len(img)} msk {len(msk)} det {len(det)}')
    check('a background per chest',
          all((G/'backgrounds'/f'{c}.png').exists() for c in d.chest.unique()))

    print('\n=== COORDINATES (the class of bug that invalidated four earlier grids) ===')
    check('all coords in [0,1]',
          all(d[c].between(0, 1).all() for c in
              ['cx','cy','mask_x0','mask_y0','mask_x1','mask_y1']))
    check('coord_space uniform', (d.coord_space == 'fraction_of_image').all())
    check('mask inside its declared lung',
          ((d.mask_x0 >= d.lung_x0) & (d.mask_y0 >= d.lung_y0)
           & (d.mask_x1 <= d.lung_x1) & (d.mask_y1 <= d.lung_y1)).all())
    check('mask_px achieved == requested',
          (d.mask_px_achieved == d.mask_px_requested).all())
    check('every mask >= the 47px latent floor', (d.mask_px_achieved >= 47).all())

    bad = []
    for _, r in d.iterrows():
        m = np.asarray(Image.open(G/'masks'/f'{r.image_id}.png'))
        ys, xs = np.nonzero(m)
        if len(xs) == 0:
            bad.append((r.image_id, 'EMPTY')); continue
        w = xs.max() - xs.min() + 1
        if abs(w - r.mask_px_requested) > 2:
            bad.append((r.image_id, f'{w} vs {r.mask_px_requested}'))
    check('EVERY MASK MEASURED FROM ITS OWN PNG', not bad,
          f'{len(bad)} mismatches' + (f' e.g. {bad[:2]}' if bad else ''))

    print('\n=== LABELS MEAN WHAT THEY SAY ===')
    o = d.groupby('zone').cy.mean()
    check('zones order vertically', o['upper'] < o['mid'] < o['lower'],
          f'{o["upper"]:.3f} < {o["mid"]:.3f} < {o["lower"]:.3f}')
    les = d[d.arm == 'lesion']
    dn = les.groupby('overlap').structure_density.mean()
    if {'clear','moderate','on_structure'} <= set(dn.index):
        check('density orders clear < moderate < on_structure',
              dn['clear'] < dn['moderate'] < dn['on_structure'],
              f'{dn["clear"]:.3f} < {dn["moderate"]:.3f} < {dn["on_structure"]:.3f}')
    sz = d.groupby('size').mask_px_achieved.agg(['min','max'])
    check('size labels are distinct and exact', (sz['min'] == sz['max']).all(),
          str(sz['min'].to_dict()))

    print('\n=== INTEGRITY ===')
    h = {}
    for i in d.image_id:
        h.setdefault(hashlib.md5((G/'images'/f'{i}.png').read_bytes()).hexdigest(),
                     []).append(i)
    dup = {k: v for k, v in h.items() if len(v) > 1}
    check('no duplicate images', not dup, f'{len(dup)} duplicate groups')

    stats = [(i,) + (lambda a: (a.std(), a.max()))(
             np.asarray(Image.open(G/'images'/f'{i}.png').convert('L'), np.float32))
             for i in d.image_id]
    check('no blank or degenerate images',
          all(s > 10 and m > 100 for _, s, m in stats),
          f'min std {min(s for _, s, _ in stats):.1f}')

    print('\n=== READY FOR DOWNSTREAM ===')
    import json
    j = json.load(open(G/'detections'/f'{d.image_id.iloc[0]}.json'))
    check('detections carry raw boxes and scores',
          set(j.get('edited', {})) >= {'boxes','scores'},
          'threshold and matching sweeps need no rerun')
    fired = (d.det_background > 0.05).sum()
    check('background contamination recorded', 'det_background' in d,
          f'{fired}/{len(d)} fire pre-edit -- exclude these from every rate')
    if 'arm' in d and (d.arm == 'null_edit').any():
        n = d[d.arm == 'null_edit']
        check('null-edit control present', len(n) > 0,
              f'{len(n)} images, {(n.det_edited > 0.05).sum()} fired')

    print()
    if FAILED:
        print(f'{len(FAILED)} CHECKS FAILED: {FAILED}')
        return 1
    print(f'ALL CHECKS PASSED  ({len(d)} rows, {d.chest.nunique()} chests)')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else 'grid_v5_ckpt012'))
