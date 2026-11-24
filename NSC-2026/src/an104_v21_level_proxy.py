"""Session 47: a target-free second opinion on the test window's mean level.

The de-bias is a bet on the sign of the blend's level error (progress.md 312). One instrument that
does not come from the stack at all: `e = RH*es(T)/100` against `es(Tmin)`, where `Tmin` is the
CLEAN daily minimum recovered from the agronomic block as `2*daily_mean_temperature - daily_max`
(section 104 -- that block is a 22:00-to-22:00 daily constant with 0.06-0.12 C of jitter, computed
before the spikes were injected, so a daily median recovers it).

    RH_proxy(t) = 100 * k * es(Tmin(day)) / es(T(t))

with `k` the mean of `e/es(Tmin)` over the training prefix. The proxy is crude row by row -- its
RMSE is about 10 %RH -- but its MEAN is a different quantity, and the question here is only
whether a forward window's mean level sits above or below what the stack predicts.

Scored on every forward block: `k` and the proxy's own mean bias are fitted on labelled rows
strictly before the block's origin, so nothing after the origin enters.

    .venv/Scripts/python.exe src/an104_v21_level_proxy.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an36_increment_production as a36
import an47_v21_forward_benchmark as a47
import an76_v21_level_shape as a76
import an96_v21_increment_bundle_split as a96

OUT = ROOT / 'outputs' / 'audit_v21_s47'
MR = [m for m in fp.MODELS_L2 if m != 'ridge']
BLOCKS = ['B1_last15d', 'B2_prev15d', 'B3_shift7d', 'H1_last7d', 'H2_last14d', 'H3_last21d']


def proxy_series(g):
    """`100 * es(Tmin_clean) / es(T)` on the whole grid, before the `k` scale is applied."""
    c = fp.clean_exog(g)
    aday = (g.index - pd.Timedelta(hours=22)).normalize()
    dm = pd.DataFrame({'dmax': g.daily_max, 'dmt': g.daily_mean_temperature},
                      index=g.index).groupby(aday).median()
    tmin = pd.Series(aday.map(2 * dm.dmt - dm.dmax), index=g.index)
    return 100.0 * fp.es(tmin) / fp.es(c['air_temperature']), tmin


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    raw, tmin = proxy_series(g)
    c15 = a47.load_cache(a76.CACHE_15, a76.MANIFEST_15)
    c7 = a76.load_validated(a76.CACHE_7, a76.MANIFEST_7, '7-day forward')
    oof7 = a76.load_validated(a76.OOF7, a76.OOF7_MANIFEST, 'rebuilt 7-day OOF')
    labelled = pd.Series((g.is_test == 0).to_numpy(), index=g.index) & y.notna()
    rows = []
    for name in BLOCKS:
        O, V = a96.block_frames(g, y, name, c15, c7, oof7)
        idx = pd.DatetimeIndex(V.datetime)
        origin = pd.Timestamp(V.origin.iloc[0])
        pre = g.index[labelled.to_numpy() & (g.index <= origin)]
        k = float((y.loc[pre] / raw.loc[pre]).mean())
        est_pre = (k * raw.loc[pre])
        off = float((est_pre - y.loc[pre]).mean())        # the proxy's own prefix bias
        est = float((k * raw.loc[idx] - off).mean())
        p = a36.stack(O, V, MR, fp.BLEND_SHRINK)
        rows.append(dict(block=name, n=len(idx), truth=float(V.y.mean()),
                         model=float(p.mean()), proxy=est,
                         model_err=float(p.mean() - V.y.mean()),
                         proxy_err=est - float(V.y.mean())))
        print('  %-12s truth %6.3f   model %6.3f (%+.3f)   proxy %6.3f (%+.3f)'
              % (name, rows[-1]['truth'], rows[-1]['model'], rows[-1]['model_err'],
                 rows[-1]['proxy'], rows[-1]['proxy_err']), flush=True)
    d = pd.DataFrame(rows)
    print('\nmean |error| on the block mean: model %.3f   proxy %.3f'
          % (d.model_err.abs().mean(), d.proxy_err.abs().mean()))
    print('proxy sits ABOVE the model on %d of %d blocks; mean gap %+.3f'
          % (int((d.proxy > d.model).sum()), len(d), float((d.proxy - d.model).mean())))

    # the test window itself, fitted on the whole labelled prefix
    pre = g.index[labelled.to_numpy()]
    k = float((y.loc[pre] / raw.loc[pre]).mean())
    off = float((k * raw.loc[pre] - y.loc[pre]).mean())
    te = g.index[(g.is_test == 1).to_numpy()]
    est_te = float((k * raw.loc[te] - off).mean())
    sub = pd.read_csv(ROOT / 'outputs' / 'submissions'
                      / 'v21_increment_v16_noridge_todbias.csv')
    print('\nTEST WINDOW: proxy mean %.3f   shipped submission mean %.3f   gap %+.3f'
          % (est_te, sub.air_humidity.mean(), est_te - sub.air_humidity.mean()))
    d.to_csv(OUT / 'level_proxy.csv', index=False)
    (OUT / 'level_proxy.json').write_text(json.dumps(
        dict(blocks=rows, k=k, offset=off, test_proxy_mean=est_te,
             shipped_mean=float(sub.air_humidity.mean())), indent=2))
    return d


if __name__ == '__main__':
    run()
