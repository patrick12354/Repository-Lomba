"""Session 42: the OOD stress gate, extended to the reconciled path, for the increment arms.

§288 found a negative control failing: on the primary B1+B2 population, `phys_dsh_lags` — the
configuration that actually scored public **2.93028** against 2.86595 — comes out as the BEST of
five arms at −0.065121. The 7-day population, the worst-H condition and B3 all rank it last, which
is the correct order. So the primary metric is anti-predictive for this family and the arms cannot
be ranked on the run that revealed it.

The OOD stress gate is the instrument that called drop-`ridge` correctly (§286) and it is an
independent population. But as built for §275 and §281 it scores `a36.stack` alone — the LEVEL
stack, with no reconciliation — which is fine for a member change and useless for an increment
change. This module adds the solve, so the arms are compared on the same object production ships.

**One limitation, stated rather than hidden.** `make_stress_splits` holds out a 3-day block from
the middle of the training period with a 96-hour embargo, so the increment models are fitted on
rows both before and after their scored window. Production fits them strictly before the origin.
The mask is identical for every arm, so the comparison between arms is fair; the absolute level of
each arm is not a forecast.

    .venv/Scripts/python.exe src/an97_v21_increment_stress.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an36_increment_production as a36
import an47_v21_forward_benchmark as a47
import an92_v21_capacity_stress as cap

OUT = ROOT / 'outputs' / 'audit_v21_s42'
MR = [m for m in fp.MODELS_L2 if m != 'ridge']          # the shipped backbone since §285
ARMS = (('plain', False, False, 0.0),
        ('phys', True, False, 0.0),
        ('phys_lags', True, True, 0.0),
        ('lags', False, True, 0.0),
        ('phys_dsh_lags', True, True, fp.INC_DESHRINK))


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    F = fp.make_features(g)
    y = g[fp.TARGET]
    is_tr = (g.is_test == 0).to_numpy() & y.notna().to_numpy()
    is_te = (g.is_test == 1).to_numpy()
    splits = cap.stress_splits(F, is_tr, is_te)
    print('stress splits: %s' % [(str(v.min().date()), len(v)) for _, v in splits], flush=True)

    per_arm, rows = {a[0]: [] for a in ARMS}, []
    for sid, (ti, vi) in enumerate(splits):
        t0 = time.time()
        tr, va = pd.DatetimeIndex(ti), pd.DatetimeIndex(vi)
        folds = cap.inner_folds(tr)
        V = pd.DataFrame({m: cap._fit(m, None, F, y, tr, va) for m in MR}, index=va)
        V['y'] = y.loc[va].to_numpy()
        V['tod'] = va.hour + va.minute / 60.0
        O = []
        for t, v in folds:
            d = pd.DataFrame({m: cap._fit(m, None, F, y, t, v) for m in MR},
                             index=pd.DatetimeIndex(v))
            d['y'] = y.loc[v].to_numpy()
            d['tod'] = pd.DatetimeIndex(v).hour + pd.DatetimeIndex(v).minute / 60.0
            O.append(d.reset_index(names='dt'))
        O = pd.concat(O, ignore_index=True)
        level = a36.stack(O, V, MR, fp.BLEND_SHRINK)

        # the increment models see the same rows the members did, for every arm alike
        mask = pd.Series(False, index=F.index)
        mask.loc[tr] = True
        for label, phys, lags, dsh in ARMS:
            inc = fp.fit_increments(F, y, mask, a47.SEEDS_INC,
                                    physics=phys, deshrink=bool(dsh), lags=lags)
            z = a47.solve(level, va, a47.increment_terms(F, va, inc, None, dsh))
            per_arm[label].append((V.y.to_numpy(), z))
            rows.append(dict(split=sid, arm=label, n=len(va), start=str(va.min()),
                             rmse=fp.rmse(V.y, z)))
        print('  split %d %s [%.0f s] %s'
              % (sid, va.min().date(), time.time() - t0,
                 '  '.join('%s %.4f' % (a, fp.rmse(*per_arm[a][-1])) for a, *_ in ARMS)),
              flush=True)

    pd.DataFrame(rows).to_csv(OUT / 'increment_stress.csv', index=False)
    base = cap.pooled_rmse(per_arm['plain'])
    base_worst = max(fp.rmse(a, b) for a, b in per_arm['plain'])
    summary = {}
    print('\n%-16s %10s %10s %10s %10s  improved' % ('arm', 'pooled', 'd_pooled', 'worst',
                                                     'd_worst'))
    for label, *_ in ARMS:
        pl = cap.pooled_rmse(per_arm[label])
        wo = max(fp.rmse(a, b) for a, b in per_arm[label])
        imp = sum(fp.rmse(a, b) < fp.rmse(c, d)
                  for (a, b), (c, d) in zip(per_arm[label], per_arm['plain']))
        summary[label] = dict(pooled=pl, d_pooled=pl - base, worst=wo, d_worst=wo - base_worst,
                              blocks_improved=int(imp), n_blocks=len(splits))
        print('%-16s %10.5f %+10.5f %10.5f %+10.5f  %d/%d'
              % (label, pl, pl - base, wo, wo - base_worst, imp, len(splits)))
    (OUT / 'increment_stress.json').write_text(json.dumps(summary, indent=2))
    print('\n`phys_dsh_lags` scored public 2.93028 against 2.86595. If it is not clearly the worst'
          ' arm here, this gate does not discriminate on this family and nothing may be promoted'
          ' from it.')
    return summary


if __name__ == '__main__':
    run()
