"""Why nested CV said -0.10 and the test window said +0.11.

Section 106 justified removing the uniform floor by measuring the sd of the FITTED weights
across folds (0.012) and concluding the fit was stable, so shrinkage was insuring nothing.
That is the wrong statistic. Shrinkage does not insure against the fitted weights being
noisy; it insures against them being WRONG FOR THE TARGET WINDOW. The right measurement is
the distance from the fitted weights to the weights that would have been optimal on each
fold's own validation rows, and how that distance grows with regime distance.
"""
import pickle, sys, json
import numpy as np, pandas as pd
from scipy.optimize import nnls
sys.path[:0] = ['.', 'src']
import final_pipeline as fp

frame = pickle.load(open('outputs/robust_core_scored.pkl','rb'))['frame'].copy()
zoo = pickle.load(open('outputs/zoo17_oof.pkl','rb'))
frame['bag_nopress'] = np.nan
for (n, fam, fold), v in zoo.items():
    if n != 'bag_nopress': continue
    m = (frame.family==fam)&(frame.fold==fold)
    frame.loc[m,'bag_nopress'] = v.reindex(pd.DatetimeIndex(frame.loc[m,'datetime'])).values
M6 = list(fp.MODELS_L2)
U6 = np.ones(len(M6))/len(M6)

g = fp.load_grid(); F = fp.make_features(g)
is_tr = (g.is_test == 0).values & g[fp.TARGET].notna().values
is_te = (g.is_test == 1).values

def nn(A, y):
    w,_ = nnls(A, y); return w/w.sum() if w.sum() else np.ones(A.shape[1])/A.shape[1]

rows = []
for family, fold in frame[['family','fold']].drop_duplicates().itertuples(index=False, name=None):
    vm = (frame.family==family)&(frame.fold==fold)
    meta, valid = frame.loc[~vm], frame.loc[vm]
    w_fit = nn(meta[M6].values, meta.y.values)           # what the harness uses
    w_or  = nn(valid[M6].values, valid.y.values)         # oracle on the target window
    w_shr = 0.75*w_fit + 0.25*U6                         # the shipped v16 floor
    # regime distance: how far this validation window sits from its own training window,
    # measured target-free on the same descriptors the stress splits use
    vi = pd.DatetimeIndex(valid.datetime)
    tr_idx = F.index[is_tr & (F.index < vi.min())]
    if len(tr_idx) < 300: continue
    A, B = F.loc[tr_idx], F.loc[vi]
    lo, hi = A.quantile(.01), A.quantile(.99)
    support = float((((B>=lo)&(B<=hi))|B.isna()).mean().mean())
    rows.append(dict(family=family, fold=fold, support=support,
                     d_fit=float(np.linalg.norm(w_fit-w_or)),
                     d_shr=float(np.linalg.norm(w_shr-w_or)),
                     rmse_fit=fp.rmse(valid.y, np.clip(valid[M6].values@w_fit,5,100)),
                     rmse_shr=fp.rmse(valid.y, np.clip(valid[M6].values@w_shr,5,100)),
                     rmse_or=fp.rmse(valid.y, np.clip(valid[M6].values@w_or,5,100)),
                     hbt=w_fit[0], hbt_or=w_or[0]))
R = pd.DataFrame(rows)
R['gain_shrink'] = R.rmse_fit - R.rmse_shr      # positive => shrinkage helps this fold
print("18 folds. Distance from the fitted weight vector to the oracle one:\n")
print("  || w_fit - w_oracle ||   mean %.3f   (fitted-weight sd ACROSS folds was 0.012)"
      % R.d_fit.mean())
print("  || w_shrunk - w_oracle || mean %.3f" % R.d_shr.mean())
print("  the fitted weights sit %.1fx further from what the target window wanted than the"
      % (R.d_fit.mean()/0.012))
print("  spread of the fitted weights themselves -- section 106 measured the smaller number.\n")
print("  hbt weight: fitted %.3f +- %.3f   oracle on the target window %.3f +- %.3f"
      % (R.hbt.mean(), R.hbt.std(), R.hbt_or.mean(), R.hbt_or.std()))

# does the benefit of shrinkage grow as the validation window leaves training support?
R = R.sort_values('support')
print("\nfolds sorted by feature support of the validation window in its own training window:")
print("  (gain_shrink > 0 means the shrunk weights beat the fitted ones on that fold)\n")
for q, lab in ((3, 'lowest support third'), (2, 'middle third'), (1, 'highest support third')):
    sub = R.iloc[(3-q)*6:(4-q)*6]
    print("  %-24s support %.4f-%.4f   mean gain from shrinking %+.4f   folds helped %d/%d"
          % (lab, sub.support.min(), sub.support.max(), sub.gain_shrink.mean(),
             int((sub.gain_shrink>0).sum()), len(sub)))
sl = np.polyfit(R.support, R.gain_shrink, 1)
print("\n  slope of gain_shrink against support: %+.4f per unit support (r = %+.3f)"
      % (sl[0], np.corrcoef(R.support, R.gain_shrink)[0,1]))

# where does the actual test window sit on that axis?
A = F.loc[F.index[is_tr]]; lo, hi = A.quantile(.01), A.quantile(.99)
B = F.loc[F.index[is_te]]
sup_all = float((((B>=lo)&(B<=hi))|B.isna()).mean().mean())
sup_pub = float((((B.iloc[:220]>=lo)&(B.iloc[:220]<=hi))|B.iloc[:220].isna()).mean().mean())
sup_pri = float((((B.iloc[220:]>=lo)&(B.iloc[220:]<=hi))|B.iloc[220:].isna()).mean().mean())
print("\n  CV folds span support %.4f - %.4f" % (R.support.min(), R.support.max()))
print("  the real test window: whole %.4f   public 220 %.4f   private 514 %.4f"
      % (sup_all, sup_pub, sup_pri))
pred = np.polyval(sl, sup_pri)
print("\n  extrapolating the fitted line to the private slice's support gives a gain from")
print("  shrinking of %+.4f RMSE -- against %+.4f at the mean CV fold." % (pred, np.polyval(sl, R.support.mean())))
json.dump(dict(rows=R.to_dict('records'), slope=float(sl[0]),
               support=dict(all=sup_all, public=sup_pub, private=sup_pri,
                            cv_min=float(R.support.min()), cv_max=float(R.support.max()))),
          open('outputs/weight_transfer.json','w'), indent=2)
