"""Session 31: frozen-prediction solver reachability and calibration-origin audit.

No model fitting, target corrections, or submission generation.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47

OUT = ROOT / 'outputs/audit_v21_s31'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, spectrum, chronology = [], [], []
    paths = [ROOT / 'outputs/audit_v21_s29/preds_v21.pkl',
             ROOT / 'outputs/audit_v21_s29/preds_7d_v21.pkl']
    for path in paths:
        P = pd.read_pickle(path)
        protocol = '7d' if '_7d_' in path.name else '15d'
        P = P[P.score]
        if protocol == '15d':
            P = P[P.block.str.startswith(('B1_', 'B2_'))]
        assert not P.datetime.duplicated().any()
        for block, d in P.groupby('block'):
            d = d.sort_values('datetime')
            idx = pd.DatetimeIndex(d.datetime)
            e = d.recon.to_numpy() - d.y.to_numpy()
            assert ((d.recon > 5) & (d.recon < 100)).all(), 'Reassess preclip interpretation'
            n = len(e)
            L = np.zeros((n, n))
            for h, lam in fp.INC_SPEC:
                D, _ = fp.diff_operator(idx, h)
                if D is not None:
                    L += lam * (D.T @ D).toarray()
            assert np.max(np.abs(L @ np.ones(n))) < 1e-10
            nc, labels = connected_components(csr_matrix(L), directed=False)
            null = pd.Series(e).groupby(labels).transform('mean').to_numpy()
            daily = pd.Series(e, index=idx).groupby(idx.floor('D')).transform('mean').to_numpy()
            vals, vecs = np.linalg.eigh(L)
            mass = (vecs.T @ e)**2
            assert np.isclose(mass.sum(), e @ e, atol=1e-7)
            assert int((vals < 1e-9).sum()) == nc
            assert np.isclose(mass[vals < 1e-9].sum(), null @ null, atol=1e-7)
            rows.append(dict(protocol=protocol, block=block, n=n, components=nc,
                             sse=float(e@e), null_sse=float(null@null),
                             daily_sse=float(daily@daily)))
            masks = {'null': vals < 1e-9,
                     'low_0_to_0.085': (vals >= 1e-9) & (vals <= .085),
                     'mid_0.085_to_0.337': (vals > .085) & (vals <= .337),
                     'high_above_0.337': vals > .337}
            for band, mask in masks.items():
                spectrum.append(dict(protocol=protocol, block=block, n=n, band=band,
                                     modes=int(mask.sum()), sse=float(mass[mask].sum())))
    cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
    for block, d in cache[(cache.scope == 'inner') & ~cache.meta_fallback].groupby('block'):
        d = d.sort_values(['datetime', 'origin']).drop_duplicates('datetime', keep='last')
        d = d.sort_values('datetime')
        enabled = len(d) >= 288 and d.origin.nunique() >= 3
        chunks = [d.iloc[x] for x in np.array_split(np.arange(len(d)), 3)]
        for i in (1, 2):
            tr = pd.concat(chunks[:i])
            va = chunks[i]
            cutoff = tr.datetime.max()
            chronology.append(dict(block=block, active_gate=bool(enabled), split=i,
                                   n_validation=len(va), calibration_end=str(cutoff),
                                   min_prediction_origin=str(va.origin.min()),
                                   max_prediction_origin=str(va.origin.max()),
                                   rows_origin_before_calibration_end=int((va.origin < cutoff).sum()),
                                   overlapping_target_timestamps=int(va.datetime.isin(tr.datetime).sum())))
    E = pd.DataFrame(rows)
    E.to_csv(OUT/'solver_reachability.csv', index=False)
    S = pd.DataFrame(spectrum)
    S.to_csv(OUT/'solver_spectrum.csv', index=False)
    pd.DataFrame(chronology).to_csv(OUT/'calibration_origin_audit.csv', index=False)
    sensor_dir = ROOT/'outputs/audit_v21_s30'
    b15 = pd.read_pickle(sensor_dir/'preds_sensor_v21.pkl')
    b7 = pd.read_pickle(sensor_dir/'preds_sensor_7d_v21.pkl').set_index('datetime')
    reported_rows = len(b15.set_index('datetime').loc[b7.index])
    b15 = b15[b15.block.str.startswith(('B1_', 'B2_'))].set_index('datetime')
    assert not b15.index.duplicated().any() and not b7.index.duplicated().any()
    corrected = []
    for arm in ('drop_pressure_abs', 'drop_co2_abs', 'drop_both_abs'):
        q = pd.read_pickle(sensor_dir/('preds_sensor_%s.pkl' % arm))
        q = q[q.block.str.startswith(('B1_', 'B2_'))].set_index('datetime')
        for label, idx in [('15d_all', b15.index), ('15d_matched', b7.index)]:
            x, b = q.loc[idx], b15.loc[idx]
            assert np.array_equal(x.y, b.y) and len(x) == len(idx)
            em = np.mean((x.recon-x.y)**2)
            eb = np.mean((b.recon-b.y)**2)
            corrected.append(dict(arm=arm, protocol=label, n=len(x),
                                  delta_rmse=float(np.sqrt(em)-np.sqrt(eb)),
                                  delta_mse=float(em-eb)))
    pd.DataFrame(corrected).to_csv(OUT/'sensor_calendar_corrected.csv', index=False)
    print('an69 original matched selection rows:', reported_rows, '; unique requested:', len(b7))
    print(pd.DataFrame(corrected).to_string(index=False))
    for protocol, d in E.groupby('protocol'):
        total = d.sse.sum()
        print(protocol, dict(n=int(d.n.sum()), mse=total/d.n.sum(),
                             null_fraction=d.null_sse.sum()/total,
                             daily_fraction=d.daily_sse.sum()/total))
        print(S[S.protocol == protocol].groupby('band').sse.sum()/total)
    print(pd.DataFrame(chronology).to_string(index=False))
    progress = (ROOT/'progress.md').read_text(encoding='utf-8')
    index = []
    for line, title in enumerate(progress.splitlines(), 1):
        m = re.match(r'^## (\d+)\. (.*)', title)
        if m:
            index.append(dict(section=int(m[1]), line=line, title=m[2]))
    pd.DataFrame(index).to_csv(OUT/'progress_section_index.csv', index=False)
    provenance_paths = paths + [a47.CACHE_S27, ROOT/'src/an70_v21_slow_member_correction.py',
                               ROOT/'src/an69_v21_sensor_ablation.py',
                               ROOT/'final_pipeline.py', ROOT/'progress.md', Path(__file__)]
    provenance_paths += list(sensor_dir.glob('preds_sensor*.pkl'))
    (OUT/'provenance.json').write_text(json.dumps({str(p.relative_to(ROOT)):
        hashlib.md5(p.read_bytes()).hexdigest() for p in provenance_paths}, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
