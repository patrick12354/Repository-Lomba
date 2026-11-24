"""Session 38: read the campaign ledger, apply the written rules, and say what to run next.

Two jobs. After the screen it applies section 4.2's selection rule and writes the confirmation
list BEFORE any confirmation runs, so the choice cannot be made after seeing confirmation scores.
After the confirmation stage it evaluates the full gate on the repaired populations and produces
the decision plus a failure map.

Nothing is adopted from a screen. The screen has two blocks and two seeds and exists to decide
where to spend five-seed compute.

    .venv/Scripts/python.exe src/an90_v21_campaign_report.py --stage screen
"""
import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47
import an59_v21_candidate_contract as c
import an77_v21_shape_report as rep
import v21_episode_anchors as ea
import v21_campaign_registry as reg

OUT = ROOT / 'outputs' / 'campaign_v21_s38'
PRIMARY = rep.PRIMARY
SEVEN = ('H1_last7d', 'H2_last14d', 'H3_last21d')
BAR = dict(pooled_gain=0.02, b3_tolerance=0.05, h_tolerance=0.02, h1_tolerance=0.0,
           breakthrough_mse_fraction=0.05)


def screen_table(L):
    ok = L.loc[L.status == 'ok']
    rows = []
    for tid, d in ok.groupby('id'):
        per = {r.block: r.d_vs_ctrl for r in d.itertuples()}
        sse_c = float(sum(((g.q * 0 + 0) if False else 0) for g in []))  # placeholder unused
        pooled_c = float(np.sqrt(np.average(d.rmse_z_ctrl ** 2, weights=d.n)))
        pooled_k = float(np.sqrt(np.average(d.rmse_z ** 2, weights=d.n)))
        rows.append(dict(id=tid, family=d.family.iloc[0], component=d.component.iloc[0],
                         kind=d.kind.iloc[0],
                         pooled_ctrl=pooled_c, pooled=pooled_k, d_pooled=pooled_k - pooled_c,
                         d_worst_block=max(per.values()), d_best_block=min(per.values()),
                         improves_both=bool(all(v < 0 for v in per.values())),
                         improves_any=bool(any(v < 0 for v in per.values())),
                         d_member=float((d.rmse_member - d.rmse_member_ctrl).mean()),
                         **{'d_' + b: v for b, v in per.items()}))
    return pd.DataFrame(rows).sort_values(['family', 'd_pooled'])


def primary_of(P, tid):
    d = P.loc[(P.id == tid) & P.score & P.block.isin(PRIMARY)].copy()
    assert not d.datetime.duplicated().any(), '%s: primary blocks share a timestamp' % tid
    return d.sort_values('datetime').reset_index(drop=True)


def confirm_table(P):
    rows = []
    for tid, _d in P.groupby('id'):
        prim = primary_of(P, tid)
        k = P.loc[(P.id == tid) & P.score]
        k7 = k.loc[k.block_family == '7d']
        per = {b: (fp.rmse(x.y, x.z_ctrl), fp.rmse(x.y, x.z)) for b, x in k.groupby('block')}
        guard = ea.global_best_day_guard(prim.y, prim.z_ctrl, prim.z, prim.datetime)
        direction = c.direction(prim.y.to_numpy(), prim.z_ctrl.to_numpy(), prim.z.to_numpy())
        want = pd.DatetimeIndex(k7.datetime).unique()
        m = prim.loc[prim.datetime.isin(want).to_numpy()]
        base = float(np.sqrt(np.mean((prim.z_ctrl - prim.y) ** 2)))
        cand = float(np.sqrt(np.mean((prim.z - prim.y) ** 2)))
        r = dict(id=tid, family=reg.family_of(tid), n_primary=len(prim),
                 pooled_base=base, pooled_cand=cand, d_pooled=cand - base,
                 d_mse_pooled=cand ** 2 - base ** 2,
                 matched_n=len(m), d_matched=(fp.rmse(m.y, m.z) - fp.rmse(m.y, m.z_ctrl)),
                 d_pooled7=(fp.rmse(k7.y, k7.z) - fp.rmse(k7.y, k7.z_ctrl)),
                 d_mse_excluding_best_day=guard['guard'], best_day=guard['dropped_day'],
                 d_member=float(fp.rmse(prim.y, prim.q) - fp.rmse(prim.y, prim.q_ctrl)),
                 **{'d_' + b: v[1] - v[0] for b, v in per.items()},
                 **{'direction_' + kk: v for kk, v in direction.items()})
        r['local_mse_reduction'] = -r['d_mse_pooled'] / base ** 2
        assert abs(r['direction_d_mse'] - r['d_mse_pooled']) < 1e-9, \
            '%s: direction and pooled disagree' % tid
        for days in (3, 7):
            for kk, v in rep.bootstrap(prim.rename(columns={'z_ctrl': 'z_new', 'z': 'z_new_q'}),
                                       days).items():
                r['boot%dd_%s' % (days, kk)] = v
        worst_h = max((r['d_' + b] for b in SEVEN if ('d_' + b) in r), default=0.0)
        r['worst_h'] = worst_h
        r['bar_pooled'] = bool(r['d_pooled'] <= -BAR['pooled_gain'])
        r['bar_primary_blocks'] = bool(all(r.get('d_' + b, 1) < 0 for b in PRIMARY))
        r['bar_b3'] = bool(r.get('d_B3_shift7d', 0.0) <= BAR['b3_tolerance'])
        r['bar_matched'] = bool(r['d_matched'] <= 0)
        r['bar_pooled7'] = bool(r['d_pooled7'] <= 0)
        r['bar_h1'] = bool(r.get('d_H1_last7d', 0.0) <= BAR['h1_tolerance'])
        r['bar_worst_h'] = bool(worst_h <= BAR['h_tolerance'])
        r['guard_best_day'] = bool(r['d_mse_excluding_best_day'] < 0)
        r['promotable'] = bool(r['bar_pooled'] and r['bar_primary_blocks'] and r['bar_b3']
                               and r['bar_matched'] and r['bar_pooled7'] and r['bar_h1']
                               and r['bar_worst_h'] and r['guard_best_day'])
        r['breakthrough'] = bool(r['promotable'] and
                                 r['local_mse_reduction'] >= BAR['breakthrough_mse_fraction'])
        rows.append(r)
    return pd.DataFrame(rows).sort_values('d_pooled')


def failure_map(T, stage):
    """One measured reason per family, never the sentence 'it did not work'."""
    lines = ['# Campaign failure map (%s)\n' % stage]
    for fam in reg.FAMILIES:
        d = T.loc[T.family == fam] if 'family' in T else T.loc[T.id.str.startswith(fam)]
        if not len(d):
            lines.append('## %s\n\nnot reached in this stage.\n' % fam)
            continue
        best = d.loc[d.d_pooled.idxmin()]
        lines.append('## %s\n' % fam)
        lines.append('- configurations: %d; best `%s` at pooled %+.6f, worst block %+.6f'
                     % (len(d), best.id, best.d_pooled,
                        best.get('d_worst_block', best.get('worst_h', float('nan')))))
        lines.append('- member delta of the best配置: %+.6f' % best.get('d_member', float('nan')))
        lines.append('- direction: %s\n'
                     % ('at least one configuration improved the pooled score'
                        if (d.d_pooled < 0).any() else
                        'every configuration was worse than the control on pooled'))
    return '\n'.join(lines).replace('配置', ' configuration')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', default='screen', choices=('screen', 'confirm', 'refine', 'stability'))
    ap.add_argument('--out', default=str(OUT))
    a = ap.parse_args()
    out = Path(a.out)
    L = pd.read_csv(out / ('ledger_%s.csv' % a.stage))

    if a.stage == 'screen':
        T = screen_table(L)
        T.to_csv(out / 'screen_table.csv', index=False)
        chosen, skipped = reg.select_for_confirmation(T.to_dict('records'))
        ids = [r['id'] for r in chosen]
        c.write_json(out / 'confirm_selection.json', dict(
            created=pd.Timestamp.now().isoformat(timespec='seconds'),
            rule='docs/6.md section 4.2, applied before any confirmation run',
            ids=ids, chosen=chosen, skipped_families=skipped,
            max_per_family=reg.MAX_CONFIRM_PER_FAMILY))
        (out / 'failure_map.md').write_text(failure_map(T, 'screen'), encoding='utf-8')
        cols = ['id', 'family', 'kind', 'd_pooled', 'd_worst_block', 'improves_both', 'd_member']
        print(T[cols].to_string(index=False))
        print('\nselected for confirmation (%d): %s' % (len(ids), ', '.join(ids)))
        for f, why in skipped.items():
            print('  family %s skipped: %s' % (f, why))
        return

    P = pd.read_pickle(out / ('preds_%s.pkl' % a.stage))
    T = confirm_table(P)
    T.to_csv(out / ('metrics_%s.csv' % a.stage), index=False)
    (out / 'failure_map.md').write_text(failure_map(T, a.stage), encoding='utf-8')
    passing = T.loc[T.promotable]
    if not len(passing):
        verdict, chosen = 'keep_v21', None
        why = 'no configuration cleared the engineering bar against the five-seed control'
    else:
        best = passing.loc[passing.d_pooled.idxmin()]
        chosen = best.id
        verdict = 'local_candidate' if not bool(best.breakthrough) else 'production_ready_candidate'
        why = '%s clears every gate; pooled %+.6f' % (best.id, best.d_pooled)
    c.write_json(out / ('decision_%s.json' % a.stage), dict(
        created=pd.Timestamp.now().isoformat(timespec='seconds'), stage=a.stage,
        verdict=verdict, chosen=chosen, reason=why, bar=BAR,
        populations=dict(primary='B1+B2 unique timestamps', sensitivity_15d='B3',
                         holdout_7d='H1+H2+H3'),
        arms=T.to_dict('records'), source_md5=a47.md5(out / ('preds_%s.pkl' % a.stage))))
    cols = ['id', 'family', 'pooled_base', 'pooled_cand', 'd_pooled', 'd_matched', 'd_pooled7',
            'worst_h', 'd_member', 'promotable']
    print(T[cols].to_string(index=False))
    print('\nverdict: %s (%s)\n  %s' % (verdict, chosen, why))


if __name__ == '__main__':
    main()
