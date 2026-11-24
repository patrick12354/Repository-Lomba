"""Frozen session-28 nightly vapour-state gate and conditional reconciliation arm.

Run: .venv/Scripts/python.exe src/an61_v21_night_state.py
The gate uses only complete labelled nights before each outer origin. Each inner
forecast cleans exogenous sensors only through its own validation horizon.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'src')]
import final_pipeline as fp
import an47_v21_forward_benchmark as a47

OUT = ROOT / 'outputs/audit_v21_s28'
FEATURES = ['T_min', 'T_range', 'co2_mean', 'co2_change', 'pressure_change', 'proxy']
CONFIG = dict(night_start='18:00', night_end_exclusive='06:00', samples=24,
              features=FEATURES, ridge_alpha=100., min_train_nights=10,
              validation_chunks=3, mu=.25, required_winning_chunks=2,
              gate='exactly 3 validation chunks; pooled SSE lower than both baselines; >=2 chunks beating both; all origins pass',
              feature_policy='make_features on raw grid truncated at each forecast horizon',
              training_target='mean(RH * es(cleaned T) / 100); all labels present; night end <= origin',
              increment_seeds=list(a47.SEEDS_INC), physics=True, deshrink=.5)


def complete_nights(idx):
    """Return (18:00 start, 24 timestamps), assigning midnight to the prior day."""
    idx = pd.DatetimeIndex(idx).sort_values()
    night = idx[(idx.hour >= 18) | (idx.hour < 6)]
    starts = (night - pd.Timedelta(hours=18)).normalize() + pd.Timedelta(hours=18)
    result = []
    for start in starts.unique():
        current = night[starts == start]
        expected = pd.date_range(start, periods=24, freq='30min')
        if current.equals(expected):
            result.append((start, current))
    return result


def night_features(F):
    rows = []
    for start, idx in complete_nights(F.index):
        d = F.loc[idx]
        if not np.isfinite(d[['T', 'co2', 'pressure']].to_numpy()).all():
            continue
        rows.append(dict(start=start, end=start + pd.Timedelta(hours=12),
                         T_min=d['T'].min(),
                         T_range=d['T'].max() - d['T'].min(),
                         co2_mean=d.co2.mean(), co2_change=d.co2.iloc[-1] - d.co2.iloc[0],
                         pressure_change=d.pressure.iloc[-1] - d.pressure.iloc[0],
                         proxy=float(fp.es(d['T'].min()))))
    return pd.DataFrame(rows, columns=['start', 'end'] + FEATURES).set_index('start')


def training_nights(F, y, labelled, origin):
    table = night_features(F)
    table = table.loc[table.end <= pd.Timestamp(origin)].copy()
    targets = {}
    for start in table.index:
        idx = pd.date_range(start, periods=24, freq='30min')
        rh = y.reindex(idx)
        if labelled.reindex(idx).fillna(False).all() and np.isfinite(rh).all():
            targets[start] = float(np.mean(rh.to_numpy() * fp.es(F.loc[idx, 'T']) / 100.))
    table['target'] = pd.Series(targets, dtype=float)
    return table.loc[table.target.notna()]


def features_at(g, end):
    return fp.make_features(g.loc[g.index <= pd.Timestamp(end)])


def gate_decision(rows):
    if rows.empty:
        return dict(passed=False, chunks=0, winning_chunks=0, nights=0)
    errors = pd.DataFrame({name: (rows[name] - rows.target) ** 2
                           for name in ['ridge', 'proxy', 'mean']})
    totals = errors.sum()
    chunks = errors.groupby(rows.chunk).sum()
    wins = int(((chunks.ridge < chunks.proxy) & (chunks.ridge < chunks['mean'])).sum())
    return dict(passed=bool(len(chunks) == CONFIG['validation_chunks']
                            and totals.ridge < totals.proxy and totals.ridge < totals['mean']
                            and wins >= CONFIG['required_winning_chunks']),
                chunks=len(chunks), winning_chunks=wins, nights=len(rows),
                **{k + '_sse': float(v) for k, v in totals.items()},
                **{k + '_rmse': float(np.sqrt(v / len(rows))) for k, v in totals.items()})


def gate_origin(g, y, origin):
    labelled = g.is_test.eq(0)
    eligible = training_nights(features_at(g, origin), y, labelled, origin)
    chunks = np.array_split(np.arange(CONFIG['min_train_nights'], len(eligible)),
                           CONFIG['validation_chunks'])
    rows, folds = [], []
    for k, positions in enumerate(chunks):
        if not len(positions):
            continue
        starts = eligible.index[positions]
        inner_origin = starts[0] - pd.Timedelta(minutes=30)
        horizon = starts[-1] + pd.Timedelta(hours=11, minutes=30)
        assert horizon < origin
        F = features_at(g, horizon)
        train = training_nights(F, y, labelled, inner_origin)
        valid = training_nights(F, y, labelled, origin).reindex(starts).dropna()
        if len(train) < CONFIG['min_train_nights'] or valid.empty:
            continue
        model = make_pipeline(StandardScaler(), Ridge(alpha=CONFIG['ridge_alpha']))
        model.fit(train[FEATURES], train.target)
        prediction = model.predict(valid[FEATURES])
        rows.append(pd.DataFrame(dict(start=valid.index, end=valid.end, chunk=k,
                                      target=valid.target, ridge=prediction,
                                      proxy=valid.proxy, mean=train.target.mean(),
                                      inner_origin=inner_origin, horizon_end=horizon,
                                      training_nights=len(train))).reset_index(drop=True))
        folds.append(dict(chunk=k, origin=str(inner_origin), horizon_end=str(horizon),
                          train_nights=len(train), validation_nights=len(valid),
                          max_training_night_end=str(train.end.max()),
                          max_training_label=str(train.end.max() - pd.Timedelta(minutes=30))))
    predictions = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    decision = gate_decision(predictions)
    decision.update(origin=str(origin), available_training_nights=len(eligible), folds=folds)
    return decision, predictions


def night_term(F, idx, predicted):
    rows, cols, values, targets = [], [], [], []
    idx = pd.DatetimeIndex(idx)
    for start, timestamps in complete_nights(idx):
        if start not in predicted.index:
            continue
        weights = np.asarray(fp.es(F.loc[timestamps, 'T']), float) / (100. * 24)
        norm = np.linalg.norm(weights)
        row = len(targets)
        rows.extend([row] * 24)
        cols.extend(idx.get_indexer(timestamps))
        values.extend(weights / norm)
        targets.append(float(predicted.loc[start]) / norm)
    M = csr_matrix((values, (rows, cols)), shape=(len(targets), len(idx)))
    return M, np.asarray(targets), CONFIG['mu']


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
    g = fp.load_grid()
    y = g[fp.TARGET]
    gates, gate_rows = {}, []
    for name, origin, horizon in a47.blocks_of(g):
        decision, rows = gate_origin(g, y, origin)
        outer_idx = pd.DatetimeIndex(cache.loc[(cache.block == name) &
                                               (cache.scope == 'outer'), 'datetime'])
        decision['complete_outer_nights'] = len(complete_nights(outer_idx))
        decision['outer_rows_outside_complete_nights'] = len(outer_idx) - 24 * decision['complete_outer_nights']
        gates[name] = decision
        if not rows.empty:
            gate_rows.append(rows.assign(block=name, outer_origin=origin))
        print(name, json.dumps({k: v for k, v in decision.items() if k != 'folds'}), flush=True)
    gate_frame = pd.concat(gate_rows, ignore_index=True) if gate_rows else pd.DataFrame()
    gate_frame.to_csv(OUT / 'night_gate_predictions.csv', index=False)
    chunk_rows = []
    if not gate_frame.empty:
        for (block, chunk), d in gate_frame.groupby(['block', 'chunk'], sort=False):
            score = gate_decision(d)
            chunk_rows.append(dict(block=block, chunk=int(chunk), nights=len(d),
                                   beats_both=score['winning_chunks'] == 1,
                                   **{k: v for k, v in score.items()
                                      if k.endswith('_sse') or k.endswith('_rmse')}))
    pd.DataFrame(chunk_rows).to_csv(OUT / 'night_gate_chunks.csv', index=False)
    pd.DataFrame([{k: v for k, v in d.items() if k != 'folds'} | {'block': b}
                  for b, d in gates.items()]).to_csv(OUT / 'night_gate.csv', index=False)
    passed = all(d['passed'] for d in gates.values())
    baseline_path = a47.OUT_S27 / 'preds_v21_physics_deshrink_half.pkl'
    baseline = pd.read_pickle(baseline_path)
    baseline = baseline.loc[baseline.scope == 'outer']
    reference = a47.report(baseline, 'v21_physics_deshrink_half')
    report = dict(status='gate_passed' if passed else 'rejected_at_predictability_gate',
                  gate_passed=passed, gates=gates, config=CONFIG,
                  config_sha256=hashlib.sha256(json.dumps(CONFIG, sort_keys=True).encode()).hexdigest(),
                  code={str(p.relative_to(ROOT)): sha256(p) for p in
                        [Path(__file__), ROOT / 'final_pipeline.py',
                         ROOT / 'tests/test_v21_night_state.py',
                         ROOT / 'src/an47_v21_forward_benchmark.py']},
                  inputs=a47.input_hashes(), cache_sha256=sha256(a47.CACHE_S27),
                  manifest_sha256=sha256(a47.MANIFEST_S27),
                  baseline_sha256=sha256(baseline_path), baseline=reference,
                  outer_reconciliation_run=False,
                  reason=None if passed else 'Frozen gate failed; no outer night arm fitted or scored.')
    if passed:
        predictions, counts = [], {}
        for name, d in cache.loc[cache.scope == 'outer'].groupby('block', sort=False):
            d = d.sort_values('datetime')
            origin, horizon = d.origin.iloc[0], d.horizon_end.iloc[0]
            gh, F = a47.frame_at(g, horizon)
            train = training_nights(F, y, g.is_test.eq(0), origin)
            model = make_pipeline(StandardScaler(), Ridge(alpha=CONFIG['ridge_alpha']))
            model.fit(train[FEATURES], train.target)
            idx = pd.DatetimeIndex(d.datetime)
            valid = night_features(F.loc[idx])
            predicted = pd.Series(model.predict(valid[FEATURES]), index=valid.index)
            mask = a47.train_mask_before(g, gh, y, origin)
            inc = fp.fit_increments(F, y.reindex(gh.index), mask, a47.SEEDS_INC,
                                    physics=True, deshrink=True)
            terms = a47.increment_terms(F, idx, inc, deshrink=.5)
            terms.append(night_term(F, idx, predicted))
            predictions.append(d.assign(recon=a47.solve(d.level.to_numpy(), idx, terms)))
            counts[name] = dict(train_nights=len(train), constrained_nights=len(valid))
        P = pd.concat(predictions, ignore_index=True)
        P.to_pickle(OUT / 'preds_night_state.pkl')
        report.update(status='outer_evaluated', outer_reconciliation_run=True, counts=counts,
                      result=a47.report(P, 'night_state', reference),
                      bootstrap=a47.bootstrap_pair(baseline, P))
    (OUT / 'night_gate.json').write_text(json.dumps(report, indent=2, default=str))
    print(report['status'], flush=True)


if __name__ == '__main__':
    main()
