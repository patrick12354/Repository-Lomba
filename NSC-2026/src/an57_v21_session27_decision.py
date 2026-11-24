"""Session 27, Tahap E: the decision, in one place, against the bar that was written down first.

Nothing here fits anything. It reads the per-row predictions every session-27 script wrote,
applies the section-180 bar unchanged, and reports the paired calendar-block bootstrap at BOTH
block lengths the plan asks for rather than the one that happens to be narrower.

**The bar** (frozen in session 26, restated, not revised): pooled B1+B2 gain >= 0.02 against the
control DECLARED BEFORE THE RUN, both primary blocks improving, and B3 degrading by at most 0.05.

**The control.** Every session-27 candidate is compared against `v21_physics_deshrink_half`
rebuilt in the same namespace, because section 190 changed the harness and a candidate measured
against session 26's 5.474126 would be reading a measurement repair as a mechanism gain. The
delta against `v21_increment`, the configuration that actually scored 2.86595 on the public
board, is reported alongside so the two baselines never get mixed.

**What the bootstrap is and is not.** It resamples calendar blocks of these 30 days. It does not
correct for the dozens of candidates this calendar has now been searched over, and the share of
draws in which a candidate loses is a property of that resample -- not a probability about a
private leaderboard nobody has seen. The worst-day column is there because a pooled gain carried
by one calendar day is a different object from one spread across the window.

    .venv/Scripts/python.exe src/an57_v21_session27_decision.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
import final_pipeline as fp
import an47_v21_forward_benchmark as a47

OUT = a47.OUT_S27
CONTROL = 'v21_physics_deshrink_half'
PUBLIC_BASELINE = 'v21_increment'

# label -> pickle written by the script that produced it. Missing files are reported as not run
# rather than silently skipped, so a table can never look complete when it is not.
CANDIDATES = {
    'v21_increment': 'preds_v21_increment.pkl',
    'v21_physics': 'preds_v21_physics.pkl',
    'v21_physics_deshrink_half': 'preds_v21_physics_deshrink_half.pkl',
    'v21_physics_forward_factor': 'preds_v21_physics_forward_factor.pkl',
    'level_contributions': 'preds_level_contributions.pkl',
    'block_bagged_5bag': 'preds_block_bagged.pkl',
    'distributed_lag_blend': 'preds_distributed_lag.pkl',
}


def outer(P):
    P = P.loc[P.score].copy()
    if 'scope' in P.columns:
        P = P.loc[P.scope == 'outer']
    return P


def main():
    preds, missing = {}, []
    for label, fn in CANDIDATES.items():
        p = OUT / fn
        if p.exists():
            preds[label] = outer(pd.read_pickle(p))
        else:
            missing.append(label)
    if missing:
        print('NOT RUN (no prediction file): %s' % ', '.join(missing))
    assert CONTROL in preds, 'the declared control has no predictions; run an53 first'

    ctrl = a47.report(preds[CONTROL], CONTROL)
    pub = a47.report(preds[PUBLIC_BASELINE], PUBLIC_BASELINE) if PUBLIC_BASELINE in preds else None

    rows, boots = [], {}
    for label, P in preds.items():
        r = a47.report(P, label, ctrl)
        if pub is not None:
            r['d_pooled_vs_public'] = r['pooled'] - pub['pooled']
        if label != CONTROL:
            b = a47.bootstrap_pair(preds[CONTROL], P)
            boots[label] = b
            r['boot3_dmse'] = b['b3d']['mean']
            r['boot3_lo'], r['boot3_hi'] = b['b3d']['lo'], b['b3d']['hi']
            r['boot3_blocks'] = b['b3d']['blocks']
            r['boot7_dmse'] = b['b7d']['mean']
            r['boot7_lo'], r['boot7_hi'] = b['b7d']['lo'], b['b7d']['hi']
            r['boot7_blocks'] = b['b7d']['blocks']
            r['days_improved'] = b['worst_day']['days_improved']
            r['days'] = b['worst_day']['days']
            r['worst_day'] = b['worst_day']['date']
            r['worst_day_dmse'] = b['worst_day']['d_mse']
        rows.append(r)

    R = pd.DataFrame(rows).sort_values('pooled').reset_index(drop=True)
    cols = ['candidate', 'pooled', 'B1_last15d', 'B2_prev15d', 'B3_shift7d', 'd_pooled',
            'd_B1_last15d', 'd_B2_prev15d', 'd_B3_shift7d', 'promotable']
    cols = [c for c in cols if c in R.columns]
    print('\nagainst the declared control (%s), section-180 bar\n' % CONTROL)
    print(R[cols].to_string(index=False))

    if 'd_pooled_vs_public' in R.columns:
        print('\ndelta against the configuration that scored 2.86595 in public (%s): '
              % PUBLIC_BASELINE)
        print(R[['candidate', 'pooled', 'd_pooled_vs_public']].to_string(index=False))

    print('\npaired calendar-block bootstrap of pooled dMSE, both block lengths')
    B = pd.DataFrame([dict(candidate=k, **{'3d_' + a: v['b3d'][a] for a in
                                           ('blocks', 'mean', 'lo', 'hi', 'p_worse')},
                           **{'7d_' + a: v['b7d'][a] for a in
                              ('blocks', 'mean', 'lo', 'hi', 'p_worse')},
                           days_improved=v['worst_day']['days_improved'],
                           days=v['worst_day']['days'],
                           worst_day=v['worst_day']['date'],
                           worst_day_dmse=v['worst_day']['d_mse'],
                           dmse_ex_best_day=v['worst_day']['d_mse_excluding_best_day'])
                      for k, v in boots.items()])
    print(B.to_string(index=False))

    passing = R.loc[R.get('promotable', pd.Series(False, index=R.index)).fillna(False)]
    passing = passing.loc[passing.candidate != CONTROL]
    print('\nPASSES THE SECTION-180 BAR AGAINST %s: %s'
          % (CONTROL, ', '.join(passing.candidate) if len(passing) else 'none'))

    R.to_csv(OUT / 'decision.csv', index=False)
    B.to_csv(OUT / 'decision_bootstrap.csv', index=False)
    (OUT / 'decision.json').write_text(json.dumps(dict(
        control=CONTROL, public_baseline=PUBLIC_BASELINE, bar=a47.BAR,
        not_run=missing, results=json.loads(R.to_json(orient='records')),
        bootstrap=boots, passing=list(passing.candidate)), indent=2, default=str))
    print('\nwrote decision.csv, decision_bootstrap.csv and decision.json to %s' % OUT)


if __name__ == '__main__':
    main()
