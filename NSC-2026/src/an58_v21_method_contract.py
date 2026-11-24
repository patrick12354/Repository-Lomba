"""Reproduce the session-28 methodological findings without model fitting."""
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import an47_v21_forward_benchmark as a47
import an59_v21_candidate_contract as c


def main():
    c.OUT.mkdir(parents=True, exist_ok=True)
    cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
    leads = []
    for name, d in cache.loc[(cache.scope == 'inner') & cache.score].groupby('block'):
        h = c.lead_hours(d.datetime, pd.DatetimeIndex(d.origin)[0]) if d.origin.nunique() == 1 else (
            pd.to_datetime(d.datetime) - pd.to_datetime(d.origin)).dt.total_seconds().to_numpy()/3600
        leads.append(dict(block=name, n=len(d), min_lead_hours=float(h.min()),
                          max_lead_hours=float(h.max()), score_window_hours=48))
    pd.DataFrame(leads).to_csv(c.OUT / 'method_leads.csv', index=False)
    base = pd.read_pickle(a47.OUT_S27 / 'preds_v21_physics_deshrink_half.pkl')
    rows = []
    for file in ('preds_distributed_lag.pkl', 'preds_block_bagged.pkl',
                 'preds_v21_physics_forward_factor.pkl'):
        q = pd.read_pickle(a47.OUT_S27 / file)
        joined = c.join_predictions(base, q)
        for name, d in joined.groupby('block'):
            rows.append(dict(candidate=file, block=name, **c.direction(d.y, d.recon, d.recon_q)))
    pd.DataFrame(rows).to_csv(c.OUT / 'method_direction.csv', index=False)
    c.write_json(c.OUT / 'method_audit.json', dict(leads=leads, direction=rows,
        mask_fix='each horizon shifted from the original mask, not a cumulatively masked series',
        arms='fixed alpha100 blend0.25; adaptive solve selector tested but not searched this round'))
    print(pd.DataFrame(leads).to_string(index=False))
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == '__main__':
    main()
