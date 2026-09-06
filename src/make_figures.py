"""
Figures for the grid v5 results. Uses the locked palette in figstyle.py.

RUN
    python3 make_figures.py "grid_v5_final (1)"

WHAT IT MAKES
    fig-generation-vs-detection.png   the headline: each axis, painting rate above,
                                      detection-among-painted below
    fig-failure-map-size-overlap.png  2D heatmaps, painting rate and detection
    fig-conspicuity.png               detection against CNR, the one real predictor
    fig-null-control.png              lesion vs null-edit vs untouched background

WHY THE FIGURES ARE PAIRED
    A raw hit/miss rate conflates two mechanisms. Overlap halves the chance RadEdit paints
    anything (chi2 p = 2e-18) yet has no effect on detection once a lesion exists
    (Friedman p = 0.42). Plotting only the raw rate would show a large "overlap effect"
    that is entirely the generator. Every panel therefore shows both.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).parent))
from figstyle import (apply_style, save, heatmap, wilson,
                      INK, EDGE, GRID, BLUE, BLUE_DEEP, SLATE, SLATE_PALE, CORAL)
import matplotlib.pyplot as plt

OV = ['clear', 'moderate', 'on_structure']
SZ = ['small', 'medium', 'large']
ZN = ['upper', 'mid', 'lower']
LABEL = {'overlap': 'Anatomical overlap', 'size': 'Lesion size', 'zone': 'Lung zone'}
ORDER = {'overlap': OV, 'size': SZ, 'zone': ZN}


def load(folder):
    d = pd.read_csv(Path(folder) / 'grid_v5.csv', keep_default_na=False, na_values=[''])
    for col, order in [('overlap', OV), ('size', SZ), ('zone', ZN)]:
        d[col] = pd.Categorical(d[col], order, ordered=True)

    nul = d[(d.arm == 'null_edit') & (d.det_background <= 0.05)]
    les = d[(d.arm == 'lesion') & (d.det_background <= 0.05)].copy()

    # "painted" is defined by the null arm, not by an arbitrary constant. Anything at or
    # below the strongest null edit is indistinguishable from asking for normal tissue.
    floor = nul.edit_norm.max()
    les['painted'] = les.edit_norm > floor
    print(f'{len(d)} rows | {d.chest.nunique()} chests | '
          f'{(d.det_background > 0.05).sum()} excluded for firing pre-edit')
    print(f'painted floor {floor:.3f} -> {les.painted.sum()}/{len(les)} painted')
    return d, les, nul, floor


def fig_generation_vs_detection(les, out):
    """The headline. Top row: does RadEdit paint? Bottom row: is it found once painted?"""
    P = les[les.painted]
    fig, ax = plt.subplots(2, 3, figsize=(13.5, 8.0), sharey='row')

    for j, axis in enumerate(['overlap', 'size', 'zone']):
        order = ORDER[axis]

        # --- generation. Chest-level Friedman, same test as the detection row: a
        # chi-square over images would treat ~54 images from one chest as independent,
        # which is the pseudoreplication that inflated the original 0.885.
        g = les.groupby(axis, observed=True).painted
        rate = g.mean().reindex(order)
        n    = g.size().reindex(order)
        k    = g.sum().reindex(order)
        ci   = np.array([wilson(kk, nn) for kk, nn in zip(k, n)]).T
        wg = (les.groupby(['chest', axis], observed=True).painted.mean()
                 .unstack(axis).reindex(columns=order).dropna())
        p_gen = (stats.friedmanchisquare(*[wg[c] for c in order])[1]
                 if len(wg) >= 3 else float('nan'))

        a = ax[0, j]
        a.bar(order, rate, color=BLUE, edgecolor=EDGE, linewidth=1.2,
              yerr=[rate-ci[0], ci[1]-rate],
              error_kw=dict(ecolor='black', capsize=4, capthick=1.4, lw=1.4))
        for x, v, top in zip(order, rate, ci[1]):
            a.text(x, top + 0.035, f'{v:.2f}', ha='center', fontweight='bold',
                   fontsize=12, color=INK)
        a.set_title(f'{LABEL[axis]}\nFriedman p = {p_gen:.2g}', fontsize=13,
                    fontweight='bold', color=INK)
        a.set_ylim(0, 1.12); a.grid(True, axis='y', color=GRID)

        # --- detection, among painted only, chest as the unit of independence
        gg = P.groupby(axis, observed=True).det_edited
        mean = gg.mean().reindex(order)
        w = (P.groupby(['chest', axis], observed=True).det_edited.mean()
               .unstack(axis).reindex(columns=order))
        sem = w.std() / np.sqrt(w.notna().sum())
        wc = w.dropna()            # only chests contributing every level
        p_det = (stats.friedmanchisquare(*[wc[c] for c in order])[1]
                 if len(wc) >= 3 else float('nan'))

        a = ax[1, j]
        a.bar(order, mean, color=SLATE, edgecolor=EDGE, linewidth=1.2,
              yerr=sem.values,
              error_kw=dict(ecolor='black', capsize=4, capthick=1.4, lw=1.4))
        for x, v, e in zip(order, mean, sem.values):
            a.text(x, v + (0 if np.isnan(e) else e) + 0.035, f'{v:.2f}', ha='center',
                   fontweight='bold', fontsize=12, color=INK)
        a.set_title(f'Friedman p = {p_det:.2g}', fontsize=12, color=INK)
        a.set_ylim(0, 1.12); a.grid(True, axis='y', color=GRID)
        a.set_xlabel(LABEL[axis], fontweight='bold', color=INK)

    ax[0, 0].set_ylabel('P(RadEdit paints a lesion)', fontweight='bold', color=INK)
    ax[1, 0].set_ylabel('Detector score,\namong painted only', fontweight='bold', color=INK)
    fig.suptitle('Generation and Detection Are Separate Effects',
                 fontsize=17, fontweight='bold', color=INK, y=0.985)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    save(fig, 'fig-generation-vs-detection', out)


def fig_failure_map(les, out):
    """2D map over the two axes that matter, one panel per mechanism."""
    P = les[les.painted]
    gen = (les.pivot_table(index='size', columns='overlap', values='painted',
                           observed=True).reindex(index=SZ, columns=OV))
    det = (P.pivot_table(index='size', columns='overlap', values='det_edited',
                         observed=True).reindex(index=SZ, columns=OV))

    fig, ax = plt.subplots(1, 2, figsize=(13.5, 4.8))
    heatmap(ax[0], gen.values, OV, SZ, vmin=0, vmax=1,
            cbar_label='P(painted)', fig=fig)
    ax[0].set_title('Generation: does RadEdit paint?', fontweight='bold', color=INK)
    heatmap(ax[1], det.values, OV, SZ, vmin=0, vmax=1,
            cbar_label='Detector score', fig=fig)
    ax[1].set_title('Detection: is it found, once painted?', fontweight='bold', color=INK)
    for a in ax:
        a.set_xlabel('Anatomical overlap', fontweight='bold', color=INK)
        a.set_ylabel('Lesion size', fontweight='bold', color=INK)
        a.grid(which='major', visible=False)
    fig.tight_layout()
    save(fig, 'fig-failure-map-size-overlap', out)


def fig_conspicuity(les, out):
    """CNR is the only thing that predicts detection once a lesion exists."""
    P = les[les.painted]
    fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.6))

    r, p = stats.pearsonr(P.cnr, P.det_edited)
    ax[0].scatter(P.cnr, P.det_edited, s=22, alpha=.55, color=BLUE, edgecolor=EDGE,
                  linewidth=.4)
    m, b = np.polyfit(P.cnr, P.det_edited, 1)
    xs = np.linspace(P.cnr.min(), P.cnr.max(), 50)
    ax[0].plot(xs, m*xs + b, color=BLUE_DEEP, lw=2.2)
    ax[0].set_xlabel('Contrast-to-noise ratio', fontweight='bold', color=INK)
    ax[0].set_ylabel('Detector score', fontweight='bold', color=INK)
    ax[0].set_title(f'Conspicuity predicts detection\nr = {r:+.3f}, p = {p:.2g}',
                    fontweight='bold', color=INK)

    r2, p2 = stats.pearsonr(P.structure_density, P.det_edited)
    ax[1].scatter(P.structure_density, P.det_edited, s=22, alpha=.55, color=SLATE_PALE,
                  edgecolor=EDGE, linewidth=.4)
    ax[1].set_xlabel('Structure density at the site', fontweight='bold', color=INK)
    ax[1].set_ylabel('Detector score', fontweight='bold', color=INK)
    ax[1].set_title(f'Anatomy does not\nr = {r2:+.3f}, p = {p2:.2g}',
                    fontweight='bold', color=INK)
    for a in ax:
        a.grid(True, color=GRID)
    fig.tight_layout()
    save(fig, 'fig-conspicuity', out)


def fig_null_control(les, nul, out):
    """Reviewer item 3b: is a 'hit' evidence of a lesion, or just of an edit?"""
    P = les[les.painted]
    groups = [('Untouched\nbackground', les.det_background.values, SLATE_PALE),
              ('Null edit\n(normal tissue\nrequested)', nul.det_edited.values, SLATE),
              ('Lesion edit\n(painted)', P.det_edited.values, BLUE)]

    fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.6))
    bp = ax[0].boxplot([g[1] for g in groups], tick_labels=[g[0] for g in groups],
                       patch_artist=True, showmeans=True, widths=.55,
                       medianprops=dict(color=INK, lw=2),
                       whiskerprops=dict(color=INK), capprops=dict(color=INK),
                       flierprops=dict(marker='o', markersize=3.5,
                                       markerfacecolor='none', markeredgecolor=SLATE),
                       meanprops=dict(marker='D', markersize=5,
                                      markerfacecolor=CORAL, markeredgecolor=EDGE))
    for patch, g in zip(bp['boxes'], groups):
        patch.set_facecolor(g[2]); patch.set_edgecolor(EDGE); patch.set_linewidth(1.2)
    ax[0].set_ylabel('Detector score', fontweight='bold', color=INK)
    ax[0].set_title('A hit means a lesion, not an edit', fontweight='bold', color=INK)

    rates = [(g[0], (g[1] > 0.05).mean(), len(g[1]), (g[1] > 0.05).sum()) for g in groups]
    ci = np.array([wilson(k, n) for _, _, n, k in rates]).T
    vals = [r[1] for r in rates]
    ax[1].bar([r[0] for r in rates], vals, color=[g[2] for g in groups],
              edgecolor=EDGE, linewidth=1.2,
              yerr=[np.array(vals)-ci[0], ci[1]-np.array(vals)],
              error_kw=dict(ecolor='black', capsize=4, capthick=1.4, lw=1.4))
    for x, v, (_, _, n, k) in zip([r[0] for r in rates], vals, rates):
        ax[1].text(x, v + 0.04, f'{k}/{n}', ha='center', fontweight='bold',
                   fontsize=12, color=INK)
    ax[1].set_ylabel('Fraction firing at the site', fontweight='bold', color=INK)
    ax[1].set_ylim(0, 1.12)
    ax[1].set_title('False-trigger rate', fontweight='bold', color=INK)
    for a in ax:
        a.grid(True, axis='y', color=GRID)
    fig.tight_layout()
    save(fig, 'fig-null-control', out)


def tables(les, nul, out):
    P = les[les.painted]
    rows = []
    for axis in ['overlap', 'size', 'zone']:
        for lvl in ORDER[axis]:
            a = les[les[axis] == lvl]
            b = P[P[axis] == lvl]
            lo, hi = wilson(a.painted.sum(), len(a))
            rows.append(dict(axis=axis, level=lvl, n=len(a),
                             painted=round(a.painted.mean(), 3),
                             painted_lo=round(lo, 3), painted_hi=round(hi, 3),
                             n_painted=len(b),
                             det_mean=round(b.det_edited.mean(), 3),
                             det_hit=round((b.det_edited > 0.05).mean(), 3)))
    t = pd.DataFrame(rows)
    Path(out).mkdir(parents=True, exist_ok=True)
    t.to_csv(Path(out) / 'table-axis-effects.csv', index=False)
    print('\n' + t.to_string(index=False))
    return t


if __name__ == '__main__':
    folder = sys.argv[1] if len(sys.argv) > 1 else 'grid_v5_final (1)'
    out = sys.argv[2] if len(sys.argv) > 2 else 'figures_v2'
    apply_style()
    d, les, nul, floor = load(folder)
    fig_generation_vs_detection(les, out)
    fig_failure_map(les, out)
    fig_conspicuity(les, out)
    fig_null_control(les, nul, out)
    tables(les, nul, out)
    print(f'\nall figures in {out}/ (300 DPI png + vector pdf)')
