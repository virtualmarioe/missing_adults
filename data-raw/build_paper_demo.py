"""Regenerate data/paper_demo.json from data/cohort.json.

The resulting JSON ships three artifacts used by the in-browser GBC and SHAP
teaching demos:

  * `coef`        - IRLS-fitted logistic-regression coefficients over the full
                    7,855-case cohort, with four main effects (days elapsed,
                    age at missingness, municipality population bucket, sex)
                    and two interactions (days*age, days*muni).
  * `gbc_sample`  - 400-point stratified subsample used as training data for
                    the in-browser gradient boosting demo.
  * `bg_sample`   - 60 randomly drawn cases used as the background population
                    for Shapley marginalization.
  * `bee_sample`  - 80 randomly drawn cases used to populate the SHAP
                    beeswarm summary plot.

All features are pre-normalized to [0, 1] with the same scale the browser
side uses:
    days_norm = clip(days_elapsed / 10000, 0, 1)
    age_norm  = clip((age - 60) / 40, 0, 1)
    muni_norm = muni_idx / 4
    sex_f     = 1 if sex == 'F' else 0

Usage:
    python3 data-raw/build_paper_demo.py \
        --in data/cohort.json \
        --out data/paper_demo.json
"""
from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

try:
    import numpy as np
except ImportError:  # pragma: no cover
    print("numpy is required: `python3 -m pip install --user numpy`", file=sys.stderr)
    raise

SEED = 20250423
MUNI_TO_IDX = {'>4M': 4, '1M-4M': 3, '500k-1M': 2, '200k-500k': 1, '<200k': 0}
DAYS_MAX = 10000.0   # normalization + slider max in paper mode (~27 yr)
AGE_MIN, AGE_MAX = 60, 100
GBC_SAMPLE = 400
BEE_SAMPLE = 80
BG_SAMPLE = 60


def build_rows(records):
    rows = []
    for found, sex, age, yr, mo, muni, *_ in records:
        days = ((2021 - yr) * 12 + (8 - mo)) * 30.4
        if days < 0:
            continue
        x0 = max(0.0, min(1.0, days / DAYS_MAX))
        x1 = max(0.0, min(1.0, (max(AGE_MIN, min(AGE_MAX, age)) - AGE_MIN)
                         / (AGE_MAX - AGE_MIN)))
        x2 = MUNI_TO_IDX[muni] / 4.0
        x3 = 1.0 if sex == 'F' else 0.0
        rows.append({'x0': x0, 'x1': x1, 'x2': x2, 'x3': x3, 'found': int(found)})
    return rows


def fit_logistic(rows):
    X = np.asarray([
        [1, r['x0'], r['x1'], r['x2'], r['x3'],
         r['x0'] * r['x1'], r['x0'] * r['x2']]
        for r in rows
    ])
    y = np.asarray([r['found'] for r in rows], dtype=float)

    def sig(z):
        return 1.0 / (1.0 + np.exp(-z))

    w = np.zeros(X.shape[1])
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        for _ in range(200):
            p = sig(X @ w)
            g = X.T @ (p - y)
            W = p * (1.0 - p)
            H = (X.T * W) @ X + 1e-4 * np.eye(X.shape[1])
            step = np.linalg.solve(H, g)
            w = w - step
            if np.linalg.norm(step) < 1e-10:
                break
    names = ['b', 'dN', 'aN', 'mN', 'sF', 'dxa', 'dxm']
    with np.errstate(over='ignore', invalid='ignore', divide='ignore'):
        pred = sig(X @ w)
    return (
        {n: round(float(v), 4) for n, v in zip(names, w)},
        float(pred.mean()),
        float(((pred > 0.5).astype(int) == y).mean()),
    )


def stratified_sample(rows, n):
    pos = [r for r in rows if r['found'] == 1]
    neg = [r for r in rows if r['found'] == 0]
    random.shuffle(pos)
    random.shuffle(neg)
    target_pos = int(round(n * len(pos) / len(rows)))
    chosen = pos[:target_pos] + neg[:n - target_pos]
    random.shuffle(chosen)
    return chosen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--in', dest='inp', default='data/cohort.json')
    parser.add_argument('--out', dest='out', default='data/paper_demo.json')
    args = parser.parse_args()

    random.seed(SEED)
    payload = json.loads(Path(args.inp).read_text())
    rows = build_rows(payload['records'])
    coef, mean_pred, train_acc = fit_logistic(rows)

    mean_days = sum(r['x0'] for r in rows) / len(rows) * DAYS_MAX
    mean_age = sum(r['x1'] for r in rows) / len(rows) * (AGE_MAX - AGE_MIN) + AGE_MIN

    gbc = stratified_sample(rows, GBC_SAMPLE)
    bee = random.sample(rows, BEE_SAMPLE)
    bg = random.sample(rows, BG_SAMPLE)

    def pack_gbc(r):
        return [round(r['x0'], 4), round(r['x1'], 4), r['found']]

    def pack_shap(r):
        return [round(r['x0'], 4), round(r['x1'], 4),
                round(r['x2'], 4), int(r['x3']), r['found']]

    out = {
        'coef': coef,
        'gbc_sample': [pack_gbc(r) for r in gbc],
        'bee_sample': [pack_shap(r) for r in bee],
        'bg_sample': [pack_shap(r) for r in bg],
        'meta': {
            'days_max': int(DAYS_MAX),
            'age_min': AGE_MIN,
            'age_max': AGE_MAX,
            'records_used': len(rows),
            'train_acc': round(train_acc, 4),
            'mean_pred_found': round(mean_pred, 4),
            'mean_days': round(mean_days),
            'mean_age': round(mean_age),
            'seed': SEED,
        },
    }
    Path(args.out).write_text(json.dumps(out, separators=(',', ':')))
    print(f"wrote {args.out} "
          f"({len(gbc)} gbc, {len(bee)} bee, {len(bg)} bg; "
          f"train_acc={train_acc:.3f})")


if __name__ == '__main__':
    main()
