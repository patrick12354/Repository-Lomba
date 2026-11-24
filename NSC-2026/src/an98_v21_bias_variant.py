"""Session 42: the diurnal bias correction, re-opened on the backbone that is actually shipped.

`v11` (`--tod-blend --tod-bias`) scored public **3.00589**. `v12` (`--tod-blend --harm-bias`) scored
**3.02286**. The log switched to the harmonic form on nested cross-validation — §73 measured one
harmonic at −0.095 against three bands' −0.070 — and every stack since `v12`, including the file
that just scored 2.85383, carries `--harm-bias`. The band form has never been run on the v21
backbone.

Two reasons that is worth a measurement rather than an assumption:

* the leaderboard preferred the band form, by 0.017, and §85 calls that a tie rather than a
  reversal — but a tie is not the "clearly better" the nested table implied;
* §127 puts the `v11 -> v12` step at **α\* = +0.041**. The optimal step length for that swap was
  four per cent of the one taken. On the same table the drop-`ridge` step scored +25.8 and turned
  out to be worth −0.069 MSE (§285), so this diagnostic has one correct call on its record and this
  is its flattest entry.

The two corrections are not exclusive — `tod_bias` removes a per-band offset with the global level
subtracted out, `harm_bias` fits one sinusoid — so `both` is a legitimate arm rather than a
double-count, and `none` prices the correction as a whole.

Backbone is `MODELS_L2` without `ridge` and the plain increment terms: exactly the configuration
that scored 2.85383, so this changes one thing.

    .venv/Scripts/python.exe src/an98_v21_bias_variant.py
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
import an47_v21_forward_benchmark as a47
import an76_v21_level_shape as a76
import an91_v21_seq_member_arm as arm

OUT = ROOT / 'outputs' / 'audit_v21_s42'
M = list(fp.MODELS_L2)
MR = [m for m in M if m != 'ridge']
BLOCKS = ['B1_last15d', 'B2_prev15d', 'B3_shift7d', 'H1_last7d', 'H2_last14d', 'H3_last21d']
PRIMARY = ('B1_last15d', 'B2_prev15d')
SEVEN = ('H1_last7d', 'H2_last14d', 'H3_last21d')
MODES = ('harm', 'todbias', 'both', 'none')


def stack_bias(O, V, models, shrink, mode):
    """`an36.stack` with the bias stage swappable. `mode='harm'` reproduces it exactly."""
    U = np.ones(len(models)) / len(models)
    w, _ = nnls(O[models].to_numpy(), O.y.to_numpy())
    w = w / w.sum() if w.sum() > 0 else U.copy()
    w = (1 - shrink) * w + shrink * U
    edges, W = fp.tod_blend_weights(O, w, models=models, blend_shrink=shrink)
    work = O.copy()
    work['blend'] = np.clip(fp.apply_tod_blend(O[models].to_numpy(), O.tod.to_numpy(), edges, W),
                            5, 100)
    p = np.clip(fp.apply_tod_blend(V[models].to_numpy(), V.tod.to_numpy(), edges, W), 5, 100)
    if mode in ('todbias', 'both'):
        rel = fp.tod_bias(work, edges)
        p = np.clip(fp.apply_tod_bias(p, V.tod.to_numpy(), edges, rel), 5, 100)
        work['blend'] = np.clip(fp.apply_tod_bias(work.blend.to_numpy(), work.tod.to_numpy(),
                                                  edges, rel), 5, 100)
    if mode in ('harm', 'both'):
        p = np.clip(fp.apply_harm_bias(p, V.tod.to_numpy(), fp.harm_bias(work)), 5, 100)
    return p


def block_frames(g, y, name, c15, c7, oof7):
    if name.startswith('B'):
        return arm.frames_from_cache(c15[c15.block == name], M)
    d = c7[(c7.block == name) & (c7.scope == 'outer')].sort_values('datetime')
    V = pd.DataFrame({m: d['m_' + m].to_numpy() for m in M}, index=pd.DatetimeIndex(d.datetime))
    V['y'] = d.y.to_numpy()
    V['origin'] = d.origin.to_numpy()
    V['horizon_end'] = d.horizon_end.to_numpy()
    V['datetime'] = pd.DatetimeIndex(d.datetime)
    V['tod'] = V.index.hour + V.index.minute / 60.0
    return oof7[name], V


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    c15 = a47.load_cache(a76.CACHE_15, a76.MANIFEST_15)
    c7 = a76.load_validated(a76.CACHE_7, a76.MANIFEST_7, '7-day forward')
    oof7 = a76.load_validated(a76.OOF7, a76.OOF7_MANIFEST, 'rebuilt 7-day OOF')
    feats, res = {}, {m: [] for m in MODES}

    for name in BLOCKS:
        t0 = time.time()
        O, V = block_frames(g, y, name, c15, c7, oof7)
        idx = pd.DatetimeIndex(V.datetime)
        gh, F = a47.frame_at(g, V.horizon_end.iloc[0], feats)
        mask = a47.train_mask_before(g, gh, y, pd.Timestamp(V.origin.iloc[0]))
        inc = fp.fit_increments(F, y.reindex(gh.index), mask, a47.SEEDS_INC)
        terms = a47.increment_terms(F, idx, inc, None, 0.0)
        for mode in MODES:
            z = a47.solve(stack_bias(O, V, MR, fp.BLEND_SHRINK, mode), idx, terms)
            res[mode].append((name, V.y.to_numpy(), z))
        print('  %-12s [%.0f s]  %s' % (name, time.time() - t0,
                                        '  '.join('%s %.5f' % (m, fp.rmse(res[m][-1][1],
                                                                          res[m][-1][2]))
                                                  for m in MODES)), flush=True)

    def pooled(mode, sel):
        yy = np.concatenate([b for n, b, _ in res[mode] if n in sel])
        zz = np.concatenate([c for n, _, c in res[mode] if n in sel])
        return float(np.sqrt(np.mean((yy - zz) ** 2)))

    summary = {}
    print('\n%-9s %11s %11s %11s' % ('mode', 'd_primary', 'd_7d', 'worst_H'))
    for mode in MODES:
        dp = pooled(mode, PRIMARY) - pooled('harm', PRIMARY)
        d7 = pooled(mode, SEVEN) - pooled('harm', SEVEN)
        per = {n: fp.rmse(b, c) - fp.rmse(b2, c2)
               for (n, b, c), (_n, b2, c2) in zip(res[mode], res['harm'])}
        wh = max(per[n] for n in SEVEN)
        summary[mode] = dict(d_primary=dp, d_pooled7=d7, worst_h=wh, per_block=per)
        print('%-9s %+11.6f %+11.6f %+11.6f' % (mode, dp, d7, wh))
        print('   per block: %s' % {k: round(v, 5) for k, v in per.items()})
    (OUT / 'bias_variant.json').write_text(json.dumps(summary, indent=2, default=str))
    print('\n`harm` is the shipped arm and the reference, so its row is zero by construction.')
    print('§288/§289: on this family pooled has twice ranked a known-bad configuration best;'
          ' read worst_H alongside it.')
    return summary


if __name__ == '__main__':
    run()
