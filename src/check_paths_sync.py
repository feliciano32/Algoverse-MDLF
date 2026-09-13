#!/usr/bin/env python3
"""Fail if the canonical paths block has drifted between the notebooks and CONFIG_CELL.md.

The block is duplicated by necessity -- Colab has no copy of the repo, so the notebooks
cannot import src/paths.py. Duplication that nothing checks is duplication that diverges,
and a notebook silently writing to a stale path is the exact failure this repo has already
paid for twice.

    python src/check_paths_sync.py        # exits 1 on any mismatch
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARK = 'CANONICAL DRIVE PATHS'
END = "print(f'root: {ROOT}')"
NOTEBOOKS = ['01_generate_grid.ipynb', '02_embeddings.ipynb',
             '03_baselines.ipynb', '04_predictor_ablation_and_controls.ipynb',
             '05_baseline3_augmentation.ipynb', '06_copypaste_scoring.ipynb',
             '07_knn_coverage.ipynb']


def shared_part(text):
    """Everything from the banner to the end of the shared block, with the pip line
    dropped -- 01 has none and 02 installs open_clip too."""
    i = text.index(MARK)
    j = text.index(END) + len(END)
    body = text[text.index('\n', i):j]
    return '\n'.join(l for l in body.split('\n') if not l.startswith('!')).strip()


def from_notebook(name):
    d = json.loads((ROOT/'notebooks'/name).read_text())
    hits = [''.join(c['source']) for c in d['cells']
            if MARK in ''.join(c['source'])]
    if len(hits) != 1:
        raise SystemExit(f'{name}: {len(hits)} cells contain the banner, expected 1')
    return shared_part(hits[0])


def from_doc():
    md = (ROOT/'notebooks'/'CONFIG_CELL.md').read_text()
    blocks = re.findall(r'```python\n(.*?)```', md, re.S)
    for b in blocks:
        if MARK in b:
            return shared_part(b)
    raise SystemExit('CONFIG_CELL.md: no python block contains the banner')


def main():
    want = from_doc()
    bad = []
    for name in NOTEBOOKS:
        got = from_notebook(name)
        status = 'ok' if got == want else 'DRIFTED'
        print(f'  {status:8} {name}')
        if got != want:
            bad.append(name)
            import difflib
            for line in list(difflib.unified_diff(
                    want.split('\n'), got.split('\n'),
                    'CONFIG_CELL.md', name, lineterm=''))[:40]:
                print(f'      {line}')
    # src/paths.py is a different shape (a class), so it cannot be compared line for line.
    # What can be checked is that it names the same folders.
    py = (ROOT/'src'/'paths.py').read_text()
    for folder in ['01_data', '00_source', '01_grid', '02_embeddings', '03_copypaste',
                   '02_results', '00_models', '01_figures', '02_baselines',
                   '03_predictor', '04_baseline3']:
        if f"'{folder}'" not in py:
            print(f'  MISSING  src/paths.py never mentions {folder}')
            bad.append('src/paths.py')
    if bad:
        print(f'\n{len(set(bad))} file(s) out of sync. See DRIVE_LAYOUT.md.')
        return 1
    print('\nall copies of the canonical paths block agree.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
