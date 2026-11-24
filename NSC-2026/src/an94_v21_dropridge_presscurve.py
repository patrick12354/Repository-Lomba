"""Session 41: price dropping `ridge` at the private slice's own pressure support.

§281 left the two internal gates disagreeing: on the forward blocks dropping `ridge` is +0.0094
pooled on the primary population, and on the OOD stress blocks it is −0.0520. Both are proxies for
the private slice and they point opposite ways, so neither settles it.

§138 built the one instrument in this log that prices a member change *at a stated support level*.
It traces the gain against the held-out window's pressure support and reads the fitted line off at
the private slice's own 0.802. It resolved the `v19` question exactly this way -- "the private slice
does not go far enough out of support to make the change pay" -- but it only ever ran the BUNDLE
(`drop ridge` + `robust_hbt` + `bag_nopress` + shrink 0.0), which is the confound §127 showed was
carrying the loss. The isolated component was never put on the curve.

This is §138's harness with two arms instead of three: the v21 backbone, and the same backbone
with `ridge` removed. Same shrinkage, same members otherwise, so the curve prices one change.

Held-out windows are built from pressure ranks and a fixed RNG -- feature values only, never the
target -- exactly as `an29_presscurve.py` builds them.

    .venv/Scripts/python.exe src/an94_v21_dropridge_presscurve.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import nnls

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp

OUT = ROOT / 'outputs' / 'audit_v21_s41'
SPECS = [(8, 0), (12, 0), (18, 0), (25, 0), (8, 10), (12, 14), (6, 18), (4, 24), (3, 30)]


def blend(meta, P, models, lam):
    U = np.ones(len(models)) / len(models)
    w, _ = nnls(meta[models].values, meta.y.values)
    w = w / w.sum() if w.sum() else U.copy()
    w = (1 - lam) * w + lam * U
    work = meta.copy()
    work['blend'] = np.clip(work[models].values @ w, 5, 100)
    e, W = fp.tod_blend_weights(work, w, models=models, blend_shrink=lam)
    work['blend'] = np.clip(fp.apply_tod_blend(work[models].values, work.tod.values, e, W), 5, 100)
    pr = np.clip(fp.apply_tod_blend(P[models].values, P.tod.values, e, W), 5, 100)
    return np.clip(fp.apply_harm_bias(pr, P.tod.values, fp.harm_bias(work)), 5, 100)


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    F = fp.make_features(g)
    y = g[fp.TARGET]
    idx = g.index
    is_tr = (g.is_test == 0).values & y.notna().values
    PRESS = sorted(set(F.columns) - set(fp.no_pressure(F)))
    M = list(fp.MODELS_L2)
    MR = [m for m in M if m != 'ridge']

    tr_idx = idx[is_tr]
    pday = pd.Series(F.loc[tr_idx, 'pressure'].values,
                     index=tr_idx.normalize()).groupby(level=0).mean()
    order = list(pday.sort_values(ascending=False).index)
    rng = np.random.default_rng(11)                     # an29's seed, so the windows match

    def fit(name, trm, vam):
        return np.clip(fp.predict(fp.base_model(name), F.loc[trm], y[trm].values, F.loc[vam],
                                  fp.es(F.loc[vam, 'T'].values),
                                  y[trm].values * fp.es(F.loc[trm, 'T'].values) / 100.0,
                                  fp.SEEDS_OOF), 5, 100)

    t0, rows = time.time(), []
    for k, dil in SPECS:
        days = list(order[:k])
        if dil:
            mid = order[len(order) // 3: 2 * len(order) // 3]
            days += list(rng.choice(mid, min(dil, len(mid)), replace=False))
        hold = set(days)
        vam = is_tr & np.array([d in hold for d in idx.normalize()])
        trm = is_tr & ~vam
        if vam.sum() < 200 or trm.sum() < 1400:
            continue
        A, B = F.loc[trm, PRESS], F.loc[vam, PRESS]
        lo, hi = A.quantile(.01), A.quantile(.99)
        sup = float((((B >= lo) & (B <= hi)) | B.isna()).mean().mean())

        P = pd.DataFrame({m: fit(m, trm, vam) for m in M}, index=idx[vam])
        P['tod'] = P.index.hour + P.index.minute / 60.0
        P['y'] = y.reindex(P.index).values
        inner = F.index[trm]
        cut = inner[int(len(inner) * 0.65)]
        itr, iva = trm & (idx <= cut), trm & (idx > cut)
        Mr = pd.DataFrame({m: fit(m, itr, iva) for m in M}, index=idx[iva])
        Mr['tod'] = Mr.index.hour + Mr.index.minute / 60.0
        Mr['y'] = y.reindex(Mr.index).values

        r_ctrl = fp.rmse(P.y, blend(Mr, P, M, fp.BLEND_SHRINK))
        r_drop = fp.rmse(P.y, blend(Mr, P, MR, fp.BLEND_SHRINK))
        rows.append(dict(k=k, dilute=dil, n=int(vam.sum()), sup=sup,
                         ctrl=r_ctrl, drop_ridge=r_drop, gain=r_drop - r_ctrl))
        print('  support %.3f  n=%3d  ctrl %.4f  drop_ridge %.4f  gain %+.4f  [%.0fs]'
              % (sup, vam.sum(), r_ctrl, r_drop, r_drop - r_ctrl, time.time() - t0), flush=True)

    R = pd.DataFrame(rows).sort_values('sup')
    R.to_csv(OUT / 'dropridge_presscurve.csv', index=False)
    slope = np.polyfit(R.sup, R.gain, 1)
    corr = float(np.corrcoef(R.sup, R.gain)[0, 1])
    print('\n  corr(pressure support, drop_ridge gain) = %+.3f' % corr)

    A = F.loc[idx[is_tr], PRESS]
    lo, hi = A.quantile(.01), A.quantile(.99)
    te = F.loc[(g.is_test == 1).values, PRESS]

    def cov(B):
        return float((((B >= lo) & (B <= hi)) | B.isna()).mean().mean())

    out = dict(corr=corr, slope=float(slope[0]), intercept=float(slope[1]),
               rows=R.to_dict('records'), at={})
    for nm, v in (('public 220', cov(te.iloc[:220])), ('private 514', cov(te.iloc[220:])),
                  ('whole test', cov(te))):
        pred = float(np.polyval(slope, v))
        out['at'][nm] = dict(support=v, predicted_gain=pred)
        print('  at %-12s (pressure support %.3f): predicted drop_ridge gain %+.4f'
              % (nm, v, pred))
    (OUT / 'dropridge_presscurve.json').write_text(json.dumps(out, indent=2))
    print('\nNegative is better. §138 read the v19 bundle off this curve the same way.')
    return out


if __name__ == '__main__':
    run()
