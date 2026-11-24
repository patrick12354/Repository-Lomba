"""Session 21, steps 2 and 3 of the session-20 recommendation: rebuild everything from the
official CSVs on holdout windows that the cached folds never touched, with the two
conditions the cache could not satisfy.

1. **Feature horizon respected.** Every feature is rebuilt from a grid TRUNCATED at the end
   of the validation window, so no centered rolling window reaches past the horizon it is
   forecasting. The cached folds were built from the full grid, which quietly let a
   validation row average sensor readings from days that had not happened yet at the
   simulated origin. Production has the same shape -- the grid ends at the last test row --
   so truncating here reproduces the real constraint rather than inventing a new one.
2. **Seed counts matched to final inference.** Members are refitted on everything before the
   origin with `SEEDS_FIT` (five seeds), the same count the shipped fit uses, instead of the
   three-seed cross-validation setting.

The meta weights come from an inner rolling-origin cross-validation that lies ENTIRELY
before the holdout origin, so no label from the scored window can reach the blend. That is
the fix for the section-145 leak, applied to a fresh evaluation rather than to a cache.

One deviation, stated because it matters: the inner protocol uses 8-day validation windows
at a 2-day step rather than production's 15 at 2. A 15-day inner window leaves a single
usable fold on the earlier block, which is too thin to fit per-time-of-day weights on. The
outer horizon is the full 15 days either way, and the deviation applies identically to the
baseline and to the candidate, so it cannot manufacture a delta between them.

The blocks are not independent evidence. B1 and B2 do not overlap each other, but B3 is a
7-day shift that overlaps both, and all three sit in the same calendar as every earlier
experiment in this log.

    .venv/Scripts/python.exe src/an36_increment_production.py
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import nnls

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import final_pipeline as fp

OUT = ROOT / 'outputs' / 'audit_v20'
HOLD_DAYS = 15
BACKBONES = {'v12': (fp.MODELS, fp.BLEND_SHRINK),
             'v16': (fp.MODELS_L2, fp.BLEND_SHRINK),
             'v20': (fp.MODELS_L2, 0.0)}


def member_preds(F, y, t_idx, v_idx, models, seeds):
    """Every blend member fitted on `t_idx`, predicting `v_idx`, exactly as the pipeline
    does it -- same estimators, same clip, same vapour-pressure detour for `ridge_e`."""
    esT_t = pd.Series(fp.es(F.loc[t_idx, 'T'].values), index=t_idx)
    E_t = y.loc[t_idx] * esT_t / 100.0
    esv = fp.es(F.loc[v_idx, 'T'].values)
    out = {}
    for m in models:
        # `final_pipeline` averages seeds for the two tree members only, so `l2` gets a
        # single seed at the final fit even though cross-validation gave it three.
        # Mirrored rather than corrected: the point here is to score what ships.
        sd = seeds if fp.base_model(m) in ('hbt', 'cat') else (0,)
        out[m] = np.clip(fp.predict(fp.base_model(m), F.loc[t_idx], y.loc[t_idx],
                                    F.loc[v_idx], esv, E_t, sd), 5, 100)
    return pd.DataFrame(out, index=v_idx)


def stack(O, V, models, shrink):
    """The v12/v16/v20 blend: NNLS weights, per-time-of-day bands, harmonic diurnal bias.
    `O` is the inner out-of-fold frame, `V` the holdout member matrix; both carry `tod`."""
    w, _ = nnls(O[models].to_numpy(), O.y.to_numpy())
    w = w / w.sum() if w.sum() > 0 else np.ones(len(models)) / len(models)
    w = (1 - shrink) * w + shrink * np.ones(len(models)) / len(models)
    edges, W = fp.tod_blend_weights(O, w, models=models, blend_shrink=shrink)
    work = O.copy()
    work['blend'] = np.clip(fp.apply_tod_blend(O[models].to_numpy(), O.tod.to_numpy(),
                                               edges, W), 5, 100)
    p = np.clip(fp.apply_tod_blend(V[models].to_numpy(), V.tod.to_numpy(), edges, W), 5, 100)
    return np.clip(fp.apply_harm_bias(p, V.tod.to_numpy(), fp.harm_bias(work)), 5, 100)


def inner_origins(idx, val_days=8, step_days=2, n=8, min_train_days=18):
    """Rolling origins for the inner meta cross-validation, all inside the pre-holdout
    data. Shorter and closer together than production's 15-day/2-day grid because the
    earlier blocks have only about a month of history to spend."""
    d0, end, out = idx.min(), idx.max(), []
    for i in range(n):
        cut = end - pd.Timedelta(days=step_days * i)
        vs = cut - pd.Timedelta(days=val_days)
        if (vs - d0).days < min_train_days:
            break
        out.append((vs, cut))
    return out[::-1]


def run_block(g, y, name, hs, he, seeds_oof, seeds_fit):
    """One holdout. Features are rebuilt from the grid truncated at `he`."""
    gh = g.loc[g.index <= he]
    F = fp.make_features(gh)
    labelled = pd.Series((gh.is_test == 0).values, index=gh.index) & y.reindex(gh.index).notna()
    lab_idx = gh.index[labelled.to_numpy()]
    pre = lab_idx[lab_idx <= hs]
    hold = lab_idx[(lab_idx > hs) & (lab_idx <= he)]
    assert len(hold) > 400 and len(pre) > 900, (len(pre), len(hold))
    assert pre.max() <= hs < hold.min()

    # ---- inner chronological OOF, entirely before the origin -> the meta training set ----
    oof = []
    for fi, (vs, ve) in enumerate(inner_origins(pre)):
        v = pre[(pre > vs) & (pre <= ve)]
        t = pre[pre <= vs]
        if len(t) < 300 or len(v) < 50:
            continue
        d = member_preds(F, y, t, v, fp.MODELS_L2, seeds_oof)
        d['y'] = y.loc[v].to_numpy()
        d['tod'] = F.loc[v, 'tod'].to_numpy()
        d['fold'] = fi
        oof.append(d.reset_index(names='dt'))
    O = pd.concat(oof, ignore_index=True)
    assert O.dt.max() <= hs, 'meta training reaches past the origin'

    # ---- members refitted on everything before the origin, at the final-fit seed count ---
    V = member_preds(F, y, pre, hold, fp.MODELS_L2, seeds_fit)
    V['y'] = y.loc[hold].to_numpy()
    V['tod'] = F.loc[hold, 'tod'].to_numpy()

    inc = fp.fit_increments(F, y, labelled & (gh.index <= hs))

    rows, preds = [], []
    for tag, (models, shrink) in BACKBONES.items():
        p = stack(O, V, models, shrink)
        z = fp.reconcile(p, hold, F, inc)
        rows.append(dict(block=name, origin=str(hs), n=len(hold), meta_rows=len(O),
                         meta_folds=int(O.fold.nunique()), model=tag,
                         base=fp.rmse(V.y, p), increment=fp.rmse(V.y, z),
                         moved_rms=float(np.sqrt(np.mean((z - p) ** 2)))))
        preds.append(pd.DataFrame({'block': name, 'model': tag, 'datetime': hold,
                                   'y': V.y.to_numpy(), 'base': p, 'increment': z}))
        print('  %-4s base %.5f  increment %.5f  delta %+.5f'
              % (tag, rows[-1]['base'], rows[-1]['increment'],
                 rows[-1]['increment'] - rows[-1]['base']), flush=True)
    return rows, preds


def main():
    g = fp.load_grid()
    y = g[fp.TARGET]
    boundary = g.index[(g.is_test == 0).to_numpy()].max()
    day = pd.Timedelta(days=HOLD_DAYS)
    blocks = [('B1_last15d', boundary - day, boundary),
              ('B2_prev15d', boundary - 2 * day, boundary - day),
              ('B3_shift7d', boundary - day - pd.Timedelta(days=7),
               boundary - pd.Timedelta(days=7))]

    rows, preds = [], []
    for name, hs, he in blocks:
        print('\n%s  origin %s  horizon ends %s' % (name, hs, he), flush=True)
        r, p = run_block(g, y, name, hs, he,
                         tuple(range(len(fp.SEEDS_OOF))), tuple(range(len(fp.SEEDS_FIT))))
        rows += r
        preds += p
        pd.DataFrame(rows).to_csv(OUT / 'increment_production_scores.csv', index=False)
        pd.concat(preds).to_pickle(OUT / 'increment_production_predictions.pkl')

    r = pd.DataFrame(rows)
    r['delta'] = r.increment - r.base
    P = pd.concat(preds, ignore_index=True)
    print('\n' + r.to_string(index=False))

    summary = {}
    for tag, d in r.groupby('model'):
        q = P.loc[P.model == tag]
        clean = d.loc[d.block != 'B3_shift7d']
        summary[tag] = dict(
            blocks=int(len(d)), blocks_improved=int((d.delta < 0).sum()),
            mean_delta=float(d.delta.mean()),
            mean_delta_nonoverlapping=float(clean.delta.mean()),
            pooled_base=fp.rmse(q.y, q.base), pooled_increment=fp.rmse(q.y, q.increment),
            worst_block_base=float(d.base.max()), worst_block_increment=float(d.increment.max()),
            moved_rms=float(d.moved_rms.mean()))
    (OUT / 'increment_production_summary.json').write_text(json.dumps(summary, indent=2))
    print('\n' + json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
