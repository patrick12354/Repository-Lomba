"""Session 26, Tahap 3: let the reconciliation see the last labelled humidity before the
forecast origin.

`diff_operator(idx, h)` builds a row only when BOTH endpoints of a pair are inside `idx`, and at
inference `idx` is the test index. So the very first test timestamps are constrained by nothing
on their left: the 30-minute model knows what the humidity did between 14:30 and 15:00 on the
first day of the horizon, but the solve never gets told what the humidity WAS at 14:30, even
though that is a labelled training row.

The fix is to solve on the union of a tail of labelled rows and the horizon, pinning the
labelled part to its observed values with a large weight. Every difference edge that crosses the
boundary then exists by construction, no new operator is needed, and the pinned rows drop out of
the answer. It is emphatically NOT section 6/35/46's global offset: no statistic of the holdout
is estimated, and the anchor's influence decays away from the boundary because the only thing
carrying it inward is the same D operator that was already there.

**What it can be worth.** With the frozen INC_SPEC of 1 and 4 half-hour steps, exactly five of a
horizon's 720 rows gain a new direct constraint. Anything beyond that arrives through the solve.
Expect a small number or nothing; the point is to close the question rather than to leave it
listed as untried. Section 168's warning stands: labels BEFORE the origin are legitimate, labels
inside the horizon are not, and the test below is what separates them.

PRE-REGISTERED: primary is pooled RMSE over B1+B2 against the Tahap 1 incumbent on identical
rows; also reported per lead-time slice, because a boundary effect that is real must be
concentrated at the start of the horizon. Unlike every other candidate in this session the
anchor MAY move the overall mean, and that is not a defect here.

    .venv/Scripts/python.exe src/an50_v21_boundary.py
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import diags, identity
from scipy.sparse.linalg import spsolve

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
import final_pipeline as fp
import an47_v21_forward_benchmark as a47

OUT = ROOT / 'outputs' / 'audit_v21'
TAIL_POINTS = 48          # 24 h of labelled rows carried into the solve
PIN = 1e6                 # weight on those rows; large enough that z equals the label there
LEADS = [(0, 6), (6, 24), (24, 72), (72, 168), (168, 360)]     # hours from the origin


def anchored_solve(level, idx, tail_idx, tail_y, F, inc, deshrink):
    """The shipped objective, solved over [tail | horizon] with the tail pinned."""
    aug = pd.DatetimeIndex(np.concatenate([tail_idx.to_numpy(), idx.to_numpy()])).sort_values()
    n, k = len(aug), len(tail_idx)
    is_tail = aug.isin(tail_idx)
    w = np.where(is_tail, PIN, 1.0)
    p = np.empty(n)
    p[is_tail] = tail_y.reindex(aug[is_tail]).to_numpy()
    p[~is_tail] = pd.Series(level, index=idx).reindex(aug[~is_tail]).to_numpy()
    assert np.isfinite(p).all() and k == is_tail.sum()

    A = diags(w, format='csc')
    rhs = w * p
    for h, lam in fp.INC_SPEC:
        D, st = fp.diff_operator(aug, h)
        if D is None:
            continue
        X = fp.inc_design(F, h, inc['cols'], inc['physics']).loc[st]
        t = np.mean([np.asarray(m.predict(X)).ravel() for m in inc[h]], axis=0)
        if deshrink and ('f', h) in inc:
            f = 1.0 + fp.INC_DESHRINK * (inc[('f', h)] - 1.0)
            t = t.mean() + (t - t.mean()) * f
        A = (A + lam * (D.T @ D)).tocsc()
        rhs = rhs + lam * (D.T @ t)
    z = spsolve(A, rhs)
    assert np.isfinite(z).all()
    kept = np.clip(z, 5, 100)[~is_tail]
    return kept, float(np.max(np.abs(z[is_tail] - p[is_tail])))


def lead_table(P, label):
    rows = []
    for lo, hi in LEADS:
        h = (pd.DatetimeIndex(P.datetime) - pd.DatetimeIndex(P.origin)).total_seconds() / 3600.0
        m = (h >= lo) & (h < hi)
        if not m.any():
            continue
        d = P.loc[m]
        rows.append(dict(candidate=label, lead='%d-%dh' % (lo, hi), n=int(m.sum()),
                         rmse=fp.rmse(d.y, d.recon)))
    return pd.DataFrame(rows)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cache = pd.read_pickle(a47.CACHE)
    g = fp.load_grid()
    y = g[fp.TARGET]
    outer = cache.loc[cache.scope == 'outer']

    base = a47.score_config(g, y, cache, physics=True, deshrink=fp.INC_DESHRINK)
    ref = a47.report(base, 'incumbent_physics_dsh')
    print('incumbent pooled %.5f' % ref['pooled'])

    t0 = time.time()
    rows, tails = [], []
    for name, blk in outer.groupby('block', sort=False):
        gh, F = a47.block_frame(g, blk)
        yh = y.reindex(gh.index)
        d = blk.sort_values('datetime')
        idx = pd.DatetimeIndex(d.datetime)
        origin = pd.Timestamp(d.origin.iloc[0])
        mask = a47.train_mask_before(g, gh, y, origin)
        lab = gh.index[mask.to_numpy()]
        tail = lab[-TAIL_POINTS:]
        inc = fp.fit_increments(F, yh, mask, a47.SEEDS_INC, physics=True, deshrink=True)
        z, pin_err = anchored_solve(d.level.to_numpy(), idx, tail, yh, F, inc, True)
        rows.append(d.assign(recon=z))
        b = base.loc[base.block == name].sort_values('datetime')
        tails.append(dict(block=name, tail_points=len(tail),
                          tail_start=str(tail.min()), origin=str(origin),
                          max_pin_error=pin_err,
                          moved_rms=float(np.sqrt(np.mean((z - b.recon.to_numpy()) ** 2))),
                          moved_first_row=float(z[0] - b.recon.to_numpy()[0]),
                          mean_shift=float(z.mean() - b.recon.mean())))
        print('  %-11s anchor pinned to within %.2e, moved %.5f RMS, first row %+.4f'
              % (name, pin_err, tails[-1]['moved_rms'], tails[-1]['moved_first_row']))
    P = pd.concat(rows, ignore_index=True)
    r = a47.report(P, 'boundary_anchor', ref)
    bs = a47.bootstrap(base, P)
    r.update({'boot_' + k: v for k, v in bs.items()})
    print('  boundary_anchor pooled %.5f  (%+.5f)  [%.0f s]'
          % (r['pooled'], r['d_pooled'], time.time() - t0))
    print('  bootstrap dMSE %+.4f [%+.4f, %+.4f]' % (bs['mean'], bs['lo'], bs['hi']))

    L = pd.concat([lead_table(base, 'incumbent'), lead_table(P, 'boundary_anchor')])
    W = L.pivot(index='lead', columns='candidate', values='rmse')
    W['delta'] = W.boundary_anchor - W.incumbent
    print('\nBY LEAD TIME (all three blocks)')
    print(W.to_string(float_format=lambda v: '%.5f' % v))

    R = pd.DataFrame([ref, r])
    R.to_csv(OUT / 'boundary.csv', index=False)
    W.to_csv(OUT / 'boundary_leads.csv')
    (OUT / 'boundary.json').write_text(json.dumps(
        dict(summary=R.to_dict('records'), blocks=tails,
             leads=W.reset_index().to_dict('records'),
             tail_points=TAIL_POINTS, pin_weight=PIN), indent=2, default=str))
    print('\nPASSES THE SECTION-180 BAR:', 'yes' if r.get('promotable') else 'no')


if __name__ == '__main__':
    main()
