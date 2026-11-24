"""Session 42: split the third bundle — the increment package that was only ever scored whole.

`v21_increment_v16_phys_dsh_lags.csv` scored public **2.93028** against v21's 2.86595 and the whole
increment line was set aside. §206 said in as many words why that verdict cannot be attributed:
"The public comparison changes THREE components; physics and physics/deshrink have no reported
public scores. It therefore cannot identify lag alone as the cause."

Its own stagewise decomposition points at the middle component:

| step | B1 | B2 | B3 |
|---|---:|---:|---:|
| v21 -> physics | −0.006975 | −0.014756 | −0.000852 |
| physics -> half deshrink | −0.025502 | −0.031503 | **+0.029994** |
| half deshrink -> lags | −0.009698 | −0.035808 | +0.004561 |

And the log's own later verdicts disagree with the file it shipped: §170 **adopted** `--inc-physics`,
§202 **adopted** `--inc-lags`, and §192 **rejected** `--inc-deshrink` on the repaired forward harness
("the de-shrink factor is too small, measured forward"). So the adopted set is {physics, lags} and
the only configuration ever scored was {physics, **deshrink**, lags} — a bundle carrying the one
component that was subsequently thrown out. `_phys_lags` has never been built.

That is the same shape as §281: a component judged by the behaviour of the bundle it rode in. It
cost this log the drop-`ridge` gain for twenty-three sessions, and §285 is what recovering one such
component was worth.

**The backbone here is the current one** — `MODELS_L2` without `ridge`, the stack that scored
2.85383 — so every arm is measured against what is actually shipped rather than against the
superseded six-member blend.

    .venv/Scripts/python.exe src/an96_v21_increment_bundle_split.py
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
import an76_v21_level_shape as a76
import an91_v21_seq_member_arm as arm

OUT = ROOT / 'outputs' / 'audit_v21_s42'
M = list(fp.MODELS_L2)
MR = [m for m in M if m != 'ridge']          # the shipped backbone since section 285
BLOCKS = ['B1_last15d', 'B2_prev15d', 'B3_shift7d', 'H1_last7d', 'H2_last14d', 'H3_last21d']
PRIMARY = ('B1_last15d', 'B2_prev15d')
SEVEN = ('H1_last7d', 'H2_last14d', 'H3_last21d')

# (label, physics, lags, deshrink strength). `plain` is what is shipped; `phys_dsh_lags` is the
# configuration that actually scored 2.93028 and is carried as a NEGATIVE control -- if it does
# not come out worst here, the harness disagrees with the leaderboard and the run is suspect.
ARMS = (('plain', False, False, 0.0),
        ('phys', True, False, 0.0),
        ('phys_lags', True, True, 0.0),
        ('lags', False, True, 0.0),
        ('phys_dsh_lags', True, True, fp.INC_DESHRINK))


def block_frames(g, y, name, c15, c7, oof7):
    if name.startswith('B'):
        blk = c15[c15.block == name]
        return arm.frames_from_cache(blk, M)
    d = c7[(c7.block == name) & (c7.scope == 'outer')].sort_values('datetime')
    V = pd.DataFrame({m: d['m_' + m].to_numpy() for m in M},
                     index=pd.DatetimeIndex(d.datetime))
    V['y'] = d.y.to_numpy()
    V['origin'] = d.origin.to_numpy()
    V['horizon_end'] = d.horizon_end.to_numpy()
    V['datetime'] = pd.DatetimeIndex(d.datetime)
    V['tod'] = V.index.hour + V.index.minute / 60.0
    return oof7[name], V


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    g = fp.load_grid()
    y = g[fp.TARGET]
    c15 = a47.load_cache(a76.CACHE_15, a76.MANIFEST_15)
    c7 = a76.load_validated(a76.CACHE_7, a76.MANIFEST_7, '7-day forward')
    oof7 = a76.load_validated(a76.OOF7, a76.OOF7_MANIFEST, 'rebuilt 7-day OOF')
    feats, res = {}, {a[0]: [] for a in ARMS}

    for name in BLOCKS:
        t0 = time.time()
        O, V = block_frames(g, y, name, c15, c7, oof7)
        level = a36.stack(O, V, MR, fp.BLEND_SHRINK)          # the shipped backbone
        idx = pd.DatetimeIndex(V.datetime)
        gh, F = a47.frame_at(g, V.horizon_end.iloc[0], feats)
        mask = a47.train_mask_before(g, gh, y, pd.Timestamp(V.origin.iloc[0]))
        yh = y.reindex(gh.index)
        for label, phys, lags, dsh in ARMS:
            inc = fp.fit_increments(F, yh, mask, a47.SEEDS_INC,
                                    physics=phys, deshrink=bool(dsh), lags=lags)
            z = a47.solve(level, idx, a47.increment_terms(F, idx, inc, None, dsh))
            res[label].append((name, V.y.to_numpy(), z))
        print('  %-12s [%.0f s]  %s' % (name, time.time() - t0,
                                        '  '.join('%s %.5f' % (l, fp.rmse(res[l][-1][1],
                                                                          res[l][-1][2]))
                                                  for l, *_ in ARMS)), flush=True)

    def pooled(label, sel):
        yy = np.concatenate([b for n, b, _ in res[label] if n in sel])
        zz = np.concatenate([c for n, _, c in res[label] if n in sel])
        return float(np.sqrt(np.mean((yy - zz) ** 2)))

    summary = {}
    print('\n%-14s %10s %10s %10s %10s' % ('arm', 'd_primary', 'd_7d', 'worst_H', 'd_B3'))
    for label, *_ in ARMS:
        dp = pooled(label, PRIMARY) - pooled('plain', PRIMARY)
        d7 = pooled(label, SEVEN) - pooled('plain', SEVEN)
        per = {n: fp.rmse(b, c) - fp.rmse(b2, c2)
               for (n, b, c), (_n2, b2, c2) in zip(res[label], res['plain'])}
        wh = max(per[n] for n in SEVEN)
        summary[label] = dict(d_primary=dp, d_pooled7=d7, worst_h=wh, per_block=per)
        print('%-14s %+10.6f %+10.6f %+10.6f %+10.6f' % (label, dp, d7, wh, per['B3_shift7d']))
        print('   per block: %s' % {k: round(v, 5) for k, v in per.items()})
    (OUT / 'increment_bundle_split.json').write_text(json.dumps(summary, indent=2, default=str))
    print('\nnegative control `phys_dsh_lags` scored public 2.93028 against 2.86595; it should be'
          ' the worst arm here or this harness disagrees with the leaderboard.')
    return summary


if __name__ == '__main__':
    run()
