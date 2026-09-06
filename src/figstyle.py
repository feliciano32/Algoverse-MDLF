"""
Figure style for the MDLF paper. Import this before plotting anything.

The palette was sampled directly from the approved figures in `figures/` -- every hex
below appears in fm-size-contrast.png, failure-predictor-auroc.png, str-coverage.png,
detector-performance.png and abstention-tradeoff.png. Do not introduce new colours.

USAGE
    from figstyle import *
    apply_style()

    fig, ax = new_fig()
    ...
    finish(fig, ax, title='...', xlabel='...', ylabel='...')
    save(fig, 'fm-size-location')      # writes 300 DPI png + pdf

WHY A MODULE RATHER THAN COPY-PASTED RCPARAMS
    Camera-ready requires a consistent scheme across every figure. One file means a
    change propagates; copied blocks drift, and drift is what a reviewer notices.
"""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

# ---------------------------------------------------------------- palette
# sampled from the approved figures; counts in parentheses are pixel frequencies

INK        = '#2c3e50'   # titles, axis labels, tick text            (all figures)
EDGE       = '#1f2d4d'   # bar / patch outlines                      (auroc, coverage)
GRID       = '#eeeeee'   # gridlines                                 (auroc, coverage)

BLUE       = '#6694de'   # primary series                            (auroc bar 1)
BLUE_MID   = '#4472c4'   # secondary                                 (heatmap mid)
BLUE_DEEP  = '#3c5182'   # dark series / high end of the ramp        (coverage, heatmap)
BLUE_LIT   = '#5583d1'   # between BLUE and BLUE_MID                 (heatmap)
BLUE_PALE  = '#9ab2e5'   # light series                              (coverage bar 2)
BLUE_MIST  = '#c6d1eb'   # lightest blue fill                        (coverage, heatmap)
BLUE_WASH  = '#e6ebf5'   # background bands                          (abstention)

SLATE      = '#7982a6'   # third series, muted                       (auroc bar 2)
SLATE_PALE = '#b4b8cb'   # fourth series, muted                      (auroc bar 3)

CORAL      = '#fc7c7c'   # reference lines only -- chance, threshold (auroc)

# ordered series colours, for anything with 2-5 groups
SERIES = [BLUE, SLATE, SLATE_PALE, BLUE_DEEP, BLUE_PALE]

# sequential ramp for heatmaps. Matches fm-size-contrast.png: near-white at 0,
# through the mid blues, to dark navy at 1.
CMAP = LinearSegmentedColormap.from_list(
    'mdlf_blues',
    ['#f7f7f7', BLUE_MIST, BLUE_PALE, BLUE_LIT, BLUE_MID, BLUE_DEEP, '#33456e'])


# ---------------------------------------------------------------- global style

def apply_style():
    mpl.rcParams.update({
        'figure.dpi': 110,
        'savefig.dpi': 300,               # camera-ready
        'savefig.bbox': 'tight',
        'figure.facecolor': 'white',
        'axes.facecolor': 'white',

        'font.family': 'DejaVu Sans',
        'font.size': 12,
        'axes.titlesize': 17,
        'axes.titleweight': 'bold',
        'axes.labelsize': 13,
        'axes.labelweight': 'bold',
        'axes.labelcolor': INK,
        'axes.titlecolor': INK,
        'text.color': INK,
        'xtick.color': INK,
        'ytick.color': INK,
        'xtick.labelsize': 11,
        'ytick.labelsize': 11,

        'axes.edgecolor': INK,
        'axes.linewidth': 1.1,
        'axes.spines.top': False,
        'axes.spines.right': False,

        'axes.grid': True,
        'axes.axisbelow': True,
        'grid.color': GRID,
        'grid.linewidth': 1.0,

        'legend.frameon': True,
        'legend.framealpha': 0.95,
        'legend.edgecolor': GRID,
        'legend.fontsize': 11,
    })


def new_fig(w=7.2, h=4.6):
    return plt.subplots(figsize=(w, h))


def finish(fig, ax, title=None, xlabel=None, ylabel=None, grid_axis='y'):
    if title:  ax.set_title(title, color=INK, fontweight='bold', pad=14)
    if xlabel: ax.set_xlabel(xlabel, color=INK, fontweight='bold')
    if ylabel: ax.set_ylabel(ylabel, color=INK, fontweight='bold')
    ax.grid(True, axis=grid_axis, color=GRID, linewidth=1.0)
    ax.set_axisbelow(True)
    fig.tight_layout()
    return fig


FIGDIR = Path('figures_v2')

def save(fig, name, figdir=None):
    """300 DPI PNG plus a vector PDF. Both, always -- the PDF is what goes in LaTeX."""
    d = Path(figdir or FIGDIR); d.mkdir(parents=True, exist_ok=True)
    for ext in ('png', 'pdf'):
        fig.savefig(d / f'{name}.{ext}', dpi=300, bbox_inches='tight',
                    facecolor='white')
    print(f'wrote {d}/{name}.png and .pdf')


# ---------------------------------------------------------------- chart helpers

def heatmap(ax, M, xlabels, ylabels, vmin=0, vmax=1, fmt='{:.2f}',
            cbar_label='Failure Rate', fig=None):
    """
    Matches fm-size-contrast.png: white gridlines between cells, value printed in each,
    label colour flipping to white on dark cells so it stays readable.
    """
    im = ax.imshow(M, cmap=CMAP, vmin=vmin, vmax=vmax, aspect='auto')
    ax.set_xticks(range(len(xlabels)), xlabels)
    ax.set_yticks(range(len(ylabels)), ylabels)
    ax.set_xticks([x - 0.5 for x in range(1, len(xlabels))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(ylabels))], minor=True)
    ax.grid(which='minor', color='white', linewidth=3)
    ax.grid(which='major', visible=False)
    ax.tick_params(which='minor', length=0)

    span = (vmax - vmin) or 1
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            v = M[i, j]
            if v != v:                     # NaN
                continue
            dark = (v - vmin) / span > 0.85    # matches the reference: 0.78 dark, 0.91 white
            ax.text(j, i, fmt.format(v), ha='center', va='center',
                    fontweight='bold', fontsize=13,
                    color='white' if dark else '#3a3a3a')
    if fig is not None:
        cb = fig.colorbar(im, ax=ax)
        cb.set_label(cbar_label, color=INK, fontweight='bold')
        cb.ax.tick_params(colors=INK)
    return im


def bars(ax, labels, values, errs=None, colors=None, annotate=True, fmt='{:.3f}'):
    """Matches failure-predictor-auroc.png: dark edges, black caps, bold value on top."""
    colors = colors or SERIES[:len(values)]
    b = ax.bar(labels, values, yerr=errs, color=colors,
               edgecolor=EDGE, linewidth=1.2,
               error_kw=dict(ecolor='black', capsize=5, capthick=1.6, lw=1.6))
    if annotate:
        for r, v, e in zip(b, values, errs or [0]*len(values)):
            ax.text(r.get_x() + r.get_width()/2, v + (e or 0) + 0.025,
                    fmt.format(v), ha='center', fontweight='bold',
                    fontsize=15, color=INK)
    return b


def refline(ax, y, label='Random Chance'):
    """The coral dashed reference line. Reserved for chance / threshold only."""
    ax.axhline(y, color=CORAL, linestyle='--', linewidth=2.4, label=label, zorder=1)


def wilson(k, n, z=1.96):
    """95% Wilson interval. Behaves near 0 and 1 where the normal interval does not."""
    if n == 0:
        return (float('nan'), float('nan'))
    p, d = k / n, 1 + z**2 / n
    c = (p + z**2 / (2*n)) / d
    h = z * (p*(1-p)/n + z**2/(4*n**2))**0.5 / d
    return max(0.0, c - h), min(1.0, c + h)
