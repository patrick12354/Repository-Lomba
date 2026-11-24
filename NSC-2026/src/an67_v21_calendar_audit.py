"""Read-only session-30 diagnostics on frozen session-29 predictions; no fitting."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'outputs/audit_v21_s29'
OUT = ROOT / 'outputs/audit_v21_s30'
ARMS = ('v21', 'physics_dsh', 'physics_dsh_lags', 'physics_lags',
        'v21_lags', 'relative_dynamics')


def read(arm, short=False):
    path = SOURCE / ('preds_%s%s.pkl' % ('7d_' if short else '', arm))
    d = pd.read_pickle(path)
    if not short:
        d = d[d.block.isin(['B1_last15d', 'B2_prev15d'])]
        # Resolve historical block spelling without silently accepting B3 overlap.
        if len(d) != 1440:
            raw = pd.read_pickle(path)
            d = raw[raw.block.str.startswith(('B1_', 'B2_'))]
    assert len(d) == (1008 if short else 1440)
    assert not d.datetime.duplicated().any()
    assert np.isfinite(d[['y', 'recon', 'level']].to_numpy()).all()
    return d.set_index('datetime').sort_index()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((SOURCE / 'forward_7d_manifest.json').read_text())
    digest = hashlib.md5((SOURCE / 'forward_7d.pkl').read_bytes()).hexdigest()
    assert digest == manifest['cache_md5']
    baseline = read('v21')
    short = read('v21', True)
    assert short.index.isin(baseline.index).all()
    assert np.array_equal(short.y, baseline.loc[short.index, 'y'])
    rows, excluded = [], []
    for arm in ARMS:
        long = read(arm)
        seven = read(arm, True)
        delta = (long.recon-long.y)**2-(baseline.recon-baseline.y)**2
        for outside in (False, True):
            mask = (~long.index.isin(short.index)) == outside
            excluded.append(dict(arm=arm, outside_7d=outside, n=int(mask.sum()),
                                 delta_mse=float(delta.loc[mask].mean())))
        for label, d, ref in [
            ('15d_all', long, baseline),
            ('15d_matched_calendar', long.loc[short.index], baseline.loc[short.index]),
            ('7d_matched_calendar', seven, short),
        ]:
            assert d.index.equals(ref.index) and np.array_equal(d.y, ref.y)
            err = d.recon - d.y
            referr = ref.recon - ref.y
            rows.append(dict(arm=arm, protocol=label, n=len(d),
                             rmse=float(np.sqrt(np.mean(err**2))),
                             delta_rmse=float(np.sqrt(np.mean(err**2)) - np.sqrt(np.mean(referr**2))),
                             delta_mse=float(np.mean(err**2-referr**2))))
    table = pd.DataFrame(rows)
    table.to_csv(OUT / 'matched_calendar.csv', index=False)
    pd.DataFrame(excluded).to_csv(OUT / 'calendar_exclusion.csv', index=False)
    energy = []
    for protocol, d in [('15d', baseline), ('7d', short)]:
        for pred in ['level', 'recon']:
            e = d[pred] - d.y
            # Equal calendar bins within each origin, no mixing duplicated predictions.
            keys = [d.block, d.index.floor('D')]
            daily_mean = e.groupby(keys).transform('mean')
            total = float(np.mean(e**2))
            low = float(np.mean(daily_mean**2))
            within = float(np.mean((e-daily_mean)**2))
            assert abs(total-low-within) < 1e-10
            energy.append(dict(protocol=protocol, prediction=pred, mse=total,
                               daily_bias_mse=low, within_day_mse=within,
                               daily_bias_fraction=low/total))
    pd.DataFrame(energy).to_csv(OUT / 'residual_energy.csv', index=False)
    sources = {p.name: hashlib.md5(p.read_bytes()).hexdigest()
               for p in SOURCE.glob('preds_*.pkl')}
    (OUT / 'provenance.json').write_text(json.dumps(dict(
        sources=sources, verified_7d_cache_md5=digest,
        production_md5=hashlib.md5((ROOT/'final_pipeline.py').read_bytes()).hexdigest(),
        note='Fixed predictions; calendar standardization is not a causal isolation of history or horizon.'
    ), indent=2), encoding='utf-8')
    print(table.to_string(index=False))
    print(pd.DataFrame(energy).to_string(index=False))
    print('Required public MSE reduction to 2.6:', 1-(2.6/2.86595)**2)


if __name__ == '__main__':
    main()
