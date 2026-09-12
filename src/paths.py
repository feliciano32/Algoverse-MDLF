"""
Single source of truth for Drive paths. See DRIVE_LAYOUT.md.

Mapped from Drive on 2026-09-12 with the Drive connector, not from memory. Every path
below was read off a real folder id.

WHY THIS EXISTS
    Notebooks used to hard-code their own paths, and they disagreed. `01` wrote the grid to
    `Algoverse/grid_v5b_runs/` while `02` read from `Algoverse/data/grid_v5b_runs/data/`.
    The checkpoint was referenced as both `.pt` and `.pth`. NODE21 lived at three different
    paths across four notebooks. Every one of those cost a debugging round-trip.

    Then the Drive reorganisation renamed the top level to `01_data/ 02_results/ 03_old/
    04_misc/` and every one of those paths went stale at once.

USAGE
    from paths import P
    P.bootstrap()                      # resolve root, mount, verify inputs, report
    P.NODE21_IMAGES, P.CHECKPOINT, P.GRID_CSV, P.EMBEDDINGS, P.BASELINES
    mha = P.stage_local(names)         # bulk-copy .mha to local disk before reading them

NOTE ON DUPLICATION
    The notebooks do not import this file -- Colab has no copy of the repo, and cloning a
    private repo inside a notebook needs a token. Instead each notebook carries the same
    resolution block inline, kept verbatim in notebooks/CONFIG_CELL.md. If the layout
    changes, change it in three places: here, CONFIG_CELL.md, and cell 2 of each notebook.
"""

import os
import shutil
import subprocess
import time
from pathlib import Path

# `MyDrive/Algoverse` is a *shortcut* (id 16fB6rpTUvW3RK70pcc1dNl90qBdWjPqd, created
# 2026-06-06) pointing at the shared folder `Feliciano_Algoverse`
# (id 1Phfz57kr78RzGOVd6r-a-k1Q2rL5S3yl, owner fserrano1@hwemail.com). There is only one
# Algoverse folder. They are not two roots, and nothing needs mirroring between them.
# The Colab FUSE mount resolves the shortcut as a directory, so the first candidate
# normally wins; the rest are fallbacks for when the shortcut is missing.
ROOT_CANDIDATES = [
    '/content/drive/MyDrive/Algoverse',
    '/content/drive/MyDrive/Feliciano_Algoverse',
    '/content/drive/Shareddrives/Feliciano_Algoverse',
]

# Places things were before the reorganisation, and stray folders written by notebooks
# pointed at the old layout. Used only to produce a useful error, never to read from.
LEGACY = {
    'CHECKPOINT': ['Teammates/baseline1_checkpoint.pt',
                   'Teammates/baseline1_checkpoint.pth',
                   'results/baseline1_checkpoint.pth',
                   '03_old/results/baseline1_checkpoint.pth'],
    'NODE21':     ['Misc/node21', 'data/node21', '01_data/node21'],
    'GRID':       ['data/grid_v5b_runs/data', 'grid_v5b_runs/data', 'grid_v5b_runs',
                   '03_old/data/grid_v4'],
    'EMBEDDINGS': ['embeddings', 'data/embeddings'],
    'COPYPASTE':  ['data/copypaste_v2', 'copypaste_v2'],
}

# Folders that exist because a notebook wrote to the pre-reorganisation layout. Reported by
# bootstrap() so they get cleaned up rather than quietly accumulating a second copy of
# everything. Relative to ROOT unless marked as living at MyDrive root.
STRAYS_IN_ROOT = ['results', 'data', 'artifacts', 'grid_v5b_runs', 'Teammates']
STRAYS_IN_MYDRIVE = ['grid_v5_runs', 'grid_v4_runs', 'Teammates']


class Paths:
    def __init__(self, root=None):
        self._root = Path(root) if root else None

    # ---------------------------------------------------------------- root
    @property
    def ROOT(self):
        if self._root is None:
            self._root = self.resolve_root()
        return self._root

    @ROOT.setter
    def ROOT(self, value):
        self._root = Path(value)

    def resolve_root(self):
        """First candidate that actually contains `01_data`. Testing for the marker rather
        than for the folder itself matters: an unresolved shortcut, or a directory created
        under an unmounted /content/drive, both exist and are both empty."""
        for c in ROOT_CANDIDATES:
            if (Path(c)/'01_data').is_dir():
                return Path(c)
        tried = '\n'.join(f'    {c}' for c in ROOT_CANDIDATES)
        top = []
        if Path('/content/drive/MyDrive').is_dir():
            top = sorted(p.name for p in Path('/content/drive/MyDrive').iterdir())[:20]
        raise FileNotFoundError(
            'could not find the Algoverse root. Tried:\n' + tried +
            f'\n\n  top level of MyDrive: {top}\n\n'
            '  `MyDrive/Algoverse` is a shortcut to the shared folder '
            '`Feliciano_Algoverse`.\n'
            '  If it is gone, open Drive -> Shared with me, right-click '
            '`Feliciano_Algoverse`,\n'
            '  and choose "Add shortcut to Drive" -> My Drive.')

    # ---------------------------------------------------------------- layout
    # 01_data -- INPUTS and generated datasets
    @property
    def DATA(self):           return self.ROOT/'01_data'
    @property
    def SOURCE(self):         return self.DATA/'00_source'
    @property
    def GRID(self):           return self.DATA/'01_grid'
    @property
    def EMBEDDINGS(self):     return self.DATA/'02_embeddings'
    @property
    def COPYPASTE(self):      return self.DATA/'03_copypaste'

    @property
    def NODE21(self):         return self.SOURCE/'node21'
    @property
    def NODE21_IMAGES(self):  return self.NODE21/'images'
    @property
    def NODE21_META(self):    return self.NODE21/'metadata.csv'
    @property
    def NODE21_DIMS(self):    return self.NODE21/'node21_image_dims.csv'
    @property
    def CHEXPERT(self):       return self.SOURCE/'chexpert'
    @property
    def MIMIC_CXR(self):      return self.SOURCE/'mimic_cxr'

    @property
    def GRID_CSV(self):       return self.GRID/'grid_v5.csv'
    @property
    def GRID_SKIPPED(self):   return self.GRID/'skipped.csv'
    @property
    def GRID_IMAGES(self):    return self.GRID/'images'
    @property
    def GRID_MASKS(self):     return self.GRID/'masks'
    @property
    def GRID_BACKGROUNDS(self): return self.GRID/'backgrounds'
    @property
    def GRID_DETECTIONS(self):  return self.GRID/'detections'
    @property
    def COPYPASTE_CSV(self):  return self.COPYPASTE/'copypaste.csv'

    # 02_results -- ANALYSIS OUTPUT
    @property
    def RESULTS(self):        return self.ROOT/'02_results'
    @property
    def MODELS(self):         return self.RESULTS/'00_models'
    @property
    def FIGURES(self):        return self.RESULTS/'01_figures'
    @property
    def BASELINES(self):      return self.RESULTS/'02_baselines'
    @property
    def PREDICTOR(self):      return self.RESULTS/'03_predictor'
    @property
    def BASELINE3(self):      return self.RESULTS/'04_baseline3'

    @property
    def CHECKPOINT(self):     return self.MODELS/'baseline1_checkpoint.pth'

    # 03_old -- superseded, read-only, never a source for a number in the paper
    @property
    def OLD(self):            return self.ROOT/'03_old'
    @property
    def MISC(self):           return self.ROOT/'04_misc'

    # a local scratch mirror -- /content, wiped between sessions
    LOCAL = Path('/content/work')

    # ---------------------------------------------------------------- mount
    def mount(self):
        """Mount only if it is not already a real mount.

        `os.path.isdir('/content/drive/MyDrive')` is true for a plain local directory, so
        it cannot be used as the test. Creating folders under an unmounted /content/drive
        also blocks the mount and makes Drive look empty -- that happened, and it looked
        like the whole Drive had been wiped.
        """
        if os.path.ismount('/content/drive'):
            return 'already mounted'
        if Path('/content/drive').exists():
            os.system('fusermount -u /content/drive 2>/dev/null')
            shutil.rmtree('/content/drive', ignore_errors=True)
        from google.colab import drive
        drive.mount('/content/drive')
        assert Path('/content/drive/MyDrive').is_dir(), 'mount failed'
        return 'mounted'

    # ---------------------------------------------------------------- checks
    def _legacy_hits(self, key):
        return [self.ROOT/p for p in LEGACY.get(key, []) if (self.ROOT/p).exists()]

    def strays(self):
        """Folders from the pre-reorganisation layout. Empty ones are safe to delete; a
        non-empty one holds something that was never migrated."""
        found = []
        for rel in STRAYS_IN_ROOT:
            p = self.ROOT/rel
            if p.is_dir():
                found.append((p, len(list(p.iterdir()))))
        md = Path('/content/drive/MyDrive')
        for rel in STRAYS_IN_MYDRIVE:
            p = md/rel
            if p.is_dir():
                found.append((p, len(list(p.iterdir()))))
        return found

    def bootstrap(self, require=('NODE21', 'CHECKPOINT'), make_dirs=True, verbose=True):
        """Mount, resolve the root, create the writable output tree, verify inputs, report.
        Raises on a missing required input, naming the legacy location if one is found."""
        if verbose:
            print(self.mount())
        root = self.ROOT                              # raises with guidance if unresolvable

        if make_dirs:
            for d in (self.BASELINES, self.PREDICTOR, self.BASELINE3, self.FIGURES,
                      self.MODELS):
                d.mkdir(parents=True, exist_ok=True)

        status, problems = [], []
        checks = [
            ('NODE21',      self.NODE21_IMAGES, 'dir'),
            ('NODE21_META', self.NODE21_META,   'file'),
            ('CHECKPOINT',  self.CHECKPOINT,    'file'),
            ('GRID',        self.GRID_CSV,      'file'),
            ('EMBEDDINGS',  self.EMBEDDINGS,    'dir'),
            ('COPYPASTE',   self.COPYPASTE_CSV, 'file'),
        ]
        for name, p, kind in checks:
            if p.exists() and (kind == 'file' or any(p.iterdir())):
                if kind == 'dir':
                    extra = f'  ({len(list(p.iterdir()))} items)'
                else:
                    extra = f'  ({p.stat().st_size:,} bytes)'
                status.append(f'  OK       {name:<12} {p}{extra}')
            else:
                hits = self._legacy_hits(name.replace('_META', ''))
                status.append(f'  MISSING  {name:<12} {p}')
                if hits:
                    status.append(f'           -> found at a pre-reorg location: {hits[0]}')
                problems.append((name, p, hits[0] if hits else None))

        if verbose:
            print(f'\nroot: {root}')
            print('\n'.join(status))

        missing_required = [n for n, _, _ in problems if n.split('_')[0] in require]
        if missing_required:
            lines = [f'required input missing: {missing_required}', '']
            for n, p, legacy in problems:
                if n.split('_')[0] not in require:
                    continue
                lines.append(f'  {n} expected at {p}')
                if legacy:
                    lines.append(f'      it is at {legacy}')
                    lines.append('      move it, or set P.ROOT and rerun. See '
                                 'DRIVE_LAYOUT.md')
            raise FileNotFoundError('\n'.join(lines))

        if verbose:
            if self.GRID_CSV.exists():
                n = self.GRID_CSV.stat().st_size
                print(f'\ngrid_v5.csv is {n:,} bytes'
                      + ('  -- matches the verified 720-row grid' if n == 231145
                         else '  -- NOT the verified size (231,145). Which grid is this?'))
            st = self.strays()
            if st:
                print('\nstray folders from the old layout (see DRIVE_LAYOUT.md):')
                for p, n in st:
                    note = 'empty, safe to delete' if n == 0 else f'{n} items -- CHECK'
                    print(f'  {p}   ({note})')
        return self

    # ---------------------------------------------------------------- staging
    def stage_local(self, names, sub='node21', verbose=True):
        """Bulk-copy source files to local disk before reading them.

        Reading .mha one at a time over the Drive mount stalls inside a C call where
        KeyboardInterrupt cannot reach it. It looks like an infinite loop and needs a
        runtime restart. This has cost hours twice.
        """
        dst = self.LOCAL/sub
        dst.mkdir(parents=True, exist_ok=True)
        t0, staged = time.time(), 0
        for i, n in enumerate(names):
            if not (dst/n).exists():
                subprocess.run(['cp', str(self.NODE21_IMAGES/n), str(dst/n)], check=True)
                staged += 1
            if verbose and i % 200 == 0:
                print(f'  {i}/{len(names)}  ({time.time()-t0:.0f}s)')
        if verbose:
            gb = sum(f.stat().st_size for f in dst.iterdir())/1e9
            print(f'staged {staged} new, {len(list(dst.iterdir()))} present, '
                  f'{gb:.1f} GB, {time.time()-t0:.0f}s')
        return dst

    # ---------------------------------------------------------------- sync
    def sync(self, local_dir, drive_dir, verbose=False):
        """Copy anything new to Drive. The only reason a dead session is survivable:
        Colab caps at 12 hours and /content does not persist."""
        drive_dir = Path(drive_dir); drive_dir.mkdir(parents=True, exist_ok=True)
        n = 0
        for f in Path(local_dir).iterdir():
            if f.is_file() and not (drive_dir/f.name).exists():
                shutil.copy(f, drive_dir/f.name); n += 1
        if verbose:
            print(f'  +{n} -> {drive_dir}')
        return n

    def restore(self, drive_dir, local_dir, verbose=False):
        """Pull back whatever a previous session managed to save."""
        local_dir = Path(local_dir); local_dir.mkdir(parents=True, exist_ok=True)
        drive_dir = Path(drive_dir)
        if not drive_dir.exists():
            return 0
        n = 0
        for f in drive_dir.iterdir():
            if f.is_file() and not (local_dir/f.name).exists():
                shutil.copy(f, local_dir/f.name); n += 1
        if verbose:
            print(f'  restored {n} from {drive_dir}')
        return n


P = Paths()
