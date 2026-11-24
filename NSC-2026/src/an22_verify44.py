"""Independent re-check of exp44's robust-core verdict from its saved artefacts:
paired fold table, family split, bootstrap, and the two gate items the code does not
check -- dispersion ratio and per-member weight movement."""
import pickle, numpy as np, pandas as pd, sys
sys.path[:0] = ['.', 'src']
import final_pipeline as fp
from exp43_robust_baseline import fit_meta_predict, score_stack

A = pickle.load(open('outputs/robust_core_scored.pkl', 'rb'))
frame, base, cand, standard = A['frame'], A['base'], A['candidate'], A['standard']
print("frame rows %d  unique (family,fold,datetime) %d"
      % (len(frame), frame[['family','fold','datetime']].drop_duplicates().shape[0]))
print("robust_hbt NaNs:", int(frame['robust_hbt'].isna().sum()))

# re-derive the paired table from the scored predictions rather than trusting the json
from robust_eval import paired_summary
ps = paired_summary(base, cand)
print("\nrecomputed paired summary: mean delta %+.6f  folds won %d/%d"
      % (ps.delta.mean(), (ps.delta < 0).sum(), len(ps)))
print(ps.groupby('family').agg(delta=('delta','mean'), won=('delta', lambda s:(s<0).sum()),
                               n=('delta','size'), worst_base=('base','max'),
                               worst_cand=('candidate','max')).round(4).to_string())
print("\nmatches stored standard table:", np.allclose(np.sort(ps.delta.values),
                                                      np.sort(standard.delta.values)))

# paired bootstrap on fold deltas, and a per-family sign test
rng = np.random.default_rng(1)
b = np.array([rng.choice(ps.delta.values, len(ps), True).mean() for _ in range(20000)])
print("bootstrap mean %+.5f  95%% CI [%+.5f, %+.5f]  P(delta>=0) %.4f"
      % (b.mean(), np.percentile(b,2.5), np.percentile(b,97.5), (b >= 0).mean()))

# dispersion guard (section 69.1): ratio of predicted diurnal amplitude to the
# target-free referee amplitude, base vs candidate, on the fold rows
def amp(d, col):
    t = (d.datetime.dt.hour + d.datetime.dt.minute/60).round(0)
    m = d.groupby(t)[col].mean()
    return m.max() - m.min()
for nm, d in (('base', base), ('candidate', cand)):
    print("%-10s pred diurnal amplitude %.3f   truth %.3f   ratio %.4f"
          % (nm, amp(d,'pred'), amp(d,'y'), amp(d,'pred')/amp(d,'y')))

# what weight does the new member actually get, and what does it displace?
MODELS = list(fp.MODELS_L2)
w0, _ = None, None
_, info0 = fit_meta_predict(frame, frame.head(1), MODELS)
_, info1 = fit_meta_predict(frame, frame.head(1), MODELS + ['robust_hbt'])
print("\nglobal blend weights (all folds pooled, indicative only):")
print("  6-member:", dict(zip(MODELS, np.round(info0['weights'],3))))
print("  7-member:", dict(zip(MODELS+['robust_hbt'], np.round(info1['weights'],3))))
