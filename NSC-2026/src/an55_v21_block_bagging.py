"""Session 27, Tahap C, mechanism 2: temporal block bagging for the increment models.

Section 152 averaged five SEEDS. Section 174 averaged five LEARNERS. Neither changes which days
the model is fitted on, and with about two months of data a handful of weather episodes decide
what an increment model believes. Seed averaging measures the optimiser's variance; it says
nothing about how much of the fit belongs to the last stretch of hot afternoons.

This resamples the CALENDAR. Three-day blocks before the origin are drawn with replacement, five
bags, and the drawn multiplicity becomes the LightGBM `sample_weight` of every training row whose
later endpoint falls in that block. Two rules make it a bootstrap of episodes rather than a
scrambling of the time axis:

* the increment pairs are built once, on the true calendar, before any resampling -- a lag
  computed after concatenating shuffled blocks would difference across a seam;
* the weight follows the LATER endpoint, so a pair is either in the bag or out of it, and no
  pair is half-weighted across a block boundary.

**The control has to be size-matched.** Five bags is five models, and the incumbent already
averages five seeds, so the comparison is five-against-five and a gain cannot be the ensemble
getting bigger. The de-shrink factor is held at the incumbent estimator throughout: this screen
varies one thing, and re-fitting the factor to a bagged ensemble on the same run would confound
the two. If bagging earns a second look, the factor is re-estimated to match it then, not now.

Every bag records the hash of its weight vector, how many distinct timestamps it kept, what
fraction of rows it zeroed, and the per-block multiplicities -- the point of the exercise is
sensitivity to episode dominance, which is invisible unless the draws are inspected.

    .venv/Scripts/python.exe src/an55_v21_block_bagging.py
"""
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import lightgbm as lgb

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
import final_pipeline as fp
import an47_v21_forward_benchmark as a47

OUT = a47.OUT_S27
BLOCK_DAYS = 3
BAGS = 5                      # matched to fp.INC_SEEDS, so the ensembles are the same size
BAG_SEED = 20260905           # bag b uses BAG_SEED + b, frozen here


def block_ids(idx, days=BLOCK_DAYS):
    """Calendar block index for each timestamp: contiguous `days`-long bins anchored at the
    earliest timestamp, so the bins are a property of the calendar and not of the row order."""
    idx = pd.DatetimeIndex(idx)
    origin = idx.min().normalize()
    return ((idx.normalize() - origin).days // days).to_numpy()


def bag_weights(idx, bag, days=BLOCK_DAYS, seed=BAG_SEED):
    """Multiplicity weights for one bag, plus its provenance record."""
    b = block_ids(idx, days)
    uniq = np.unique(b)
    rng = np.random.default_rng(seed + bag)
    drawn = rng.integers(0, len(uniq), len(uniq))
    mult = np.bincount(drawn, minlength=len(uniq)).astype(float)
    w = mult[np.searchsorted(uniq, b)]
    prov = dict(bag=bag, blocks=len(uniq), rows=len(idx),
                weight_md5=hashlib.md5(w.tobytes()).hexdigest(),
                nonzero_rows=int((w > 0).sum()),
                zero_fraction=float((w == 0).mean()),
                distinct_timestamps=int(pd.DatetimeIndex(idx)[w > 0].nunique()),
                max_block_weight=float(mult.max()),
                block_multiplicity=[int(x) for x in mult])
    return w, prov


def make_bagged_builder(log, bags=BAGS, days=BLOCK_DAYS):
    """An `inc_builder` for `a47.score_config`: bagged increment models, incumbent factor."""
    def build(F, yh, mask, seeds):
        # One cheap pass through the shipped path to get the de-shrink factors, which stay the
        # control. Its single-seed models are discarded.
        inc = fp.fit_increments(F, yh, mask, (fp.INC_SEED,), physics=True, deshrink=True)
        for h, _ in fp.INC_SPEC:
            X = fp.inc_design(F, h, inc['cols'], True)
            tgt = (yh - yh.shift(h)).reindex(X.index)
            m = mask.reindex(X.index, fill_value=False)
            m = m & tgt.notna() & m.shift(h, fill_value=False)
            rows = X.index[m]
            models = []
            for b in range(bags):
                w, prov = bag_weights(rows, b, days)
                prov.update(h=h, end=str(rows.max()))
                log.append(prov)
                models.append(lgb.LGBMRegressor(random_state=fp.INC_SEED + b, **fp.INC_KW)
                              .fit(X.loc[rows], tgt.loc[rows], sample_weight=w))
            inc[h] = models
        return inc
    return build


def check_bags(rows, bags=BAGS, days=BLOCK_DAYS):
    """The draws are different from one another, and none of them reaches past the origin."""
    ws = [bag_weights(rows, b, days)[0] for b in range(bags)]
    md5s = {hashlib.md5(w.tobytes()).hexdigest() for w in ws}
    assert len(md5s) == bags, 'two bags drew identical weights: %d distinct' % len(md5s)
    assert all(w.sum() > 0 for w in ws)
    return len(md5s)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    cache = a47.load_cache(a47.CACHE_S27, a47.MANIFEST_S27)
    seeds = a47.SEEDS_INC
    feats, log = {}, []

    print('control  : v21 physics + half de-shrink, %d increment seeds' % len(seeds))
    t = time.time()
    base = a47.score_config(g, y, cache, physics=True, deshrink=fp.INC_DESHRINK, seeds=seeds,
                            scopes=('outer',), feature_cache=feats)
    ref = a47.report(base, 'incumbent_5seed')
    print('  pooled %.5f  (%.0f s)' % (ref['pooled'], time.time() - t), flush=True)

    print('candidate: same, increments bagged over %d-day calendar blocks, %d bags'
          % (BLOCK_DAYS, BAGS))
    t = time.time()
    P = a47.score_config(g, y, cache, physics=True, deshrink=fp.INC_DESHRINK, seeds=seeds,
                         scopes=('outer',), inc_builder=make_bagged_builder(log),
                         feature_cache=feats)
    r = a47.report(P, 'block_bagged_5bag', ref)
    print('  pooled %.5f  (%.0f s)' % (r['pooled'], time.time() - t), flush=True)

    bs = a47.bootstrap(base, P)
    print('  bootstrap dMSE %+.4f [%+.4f, %+.4f] over %d blocks, worse in %.0f%% of draws'
          % (bs['mean'], bs['lo'], bs['hi'], bs['blocks'], 100 * bs['p_worse']))
    for k in ('mean', 'lo', 'hi', 'p_worse'):
        r['boot_' + k] = bs[k]

    R = pd.DataFrame([ref, r])
    R.to_csv(OUT / 'block_bagging.csv', index=False)
    B = pd.DataFrame(log)
    B.to_csv(OUT / 'block_bagging_bags.csv', index=False)
    print('\n' + R.to_string(index=False))
    print('\nbag provenance (one row per bag per horizon per origin, %d in all)' % len(B))
    print(B.groupby('bag')[['blocks', 'rows', 'nonzero_rows', 'zero_fraction',
                            'max_block_weight']].mean().to_string())
    print('\ndistinct weight hashes per origin: %d expected %d'
          % (B.groupby(['h', 'end']).weight_md5.nunique().min(), BAGS))
    assert B.groupby(['h', 'end']).weight_md5.nunique().min() == BAGS, \
        'bags are not distinct at some origin'
    assert (B.zero_fraction > 0).all(), 'a bag kept every block; that is not a resample'

    (OUT / 'block_bagging.json').write_text(json.dumps(dict(
        block_days=BLOCK_DAYS, bags=BAGS, bag_seed=BAG_SEED,
        results=json.loads(R.to_json(orient='records')), bootstrap=bs,
        bag_summary=json.loads(B.groupby('bag')[['blocks', 'zero_fraction',
                                                 'max_block_weight']].mean()
                               .reset_index().to_json(orient='records'))), indent=2))
    P.to_pickle(OUT / 'preds_block_bagged.pkl')
    print('\nwrote block_bagging.csv, block_bagging_bags.csv and the predictions to %s' % OUT)


if __name__ == '__main__':
    main()
