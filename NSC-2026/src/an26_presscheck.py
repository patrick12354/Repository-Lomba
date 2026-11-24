"""Is section 78's support claim still true, and did v18/v19 remove pressure from most of
the blend?

v19's members carry the pressure level block as follows: `bag_nopress` (weight 0.591) does
not, `robust_hbt` (0.129 of the evening band) does not, and only `cat` (0.212), `enet`
(0.197) and the band-level `l2`/`ridge_e` do. So the change took the block out of roughly
60 % of the blend. That is only a good idea if the block really is out of support on the
test window, and section 97 has already caught one stale support claim in this log.
"""
import sys, json
import numpy as np, pandas as pd
sys.path[:0] = ['.', 'src']
import final_pipeline as fp

g = fp.load_grid(); F = fp.make_features(g)
y = g[fp.TARGET]
is_tr = (g.is_test == 0).values & y.notna().values
is_te = (g.is_test == 1).values
PRESS = sorted(set(F.columns) - set(fp.no_pressure(F)))
tr = F[is_tr]; lo, hi = tr.quantile(.01), tr.quantile(.99)
def cov(B): return (((B>=lo)&(B<=hi))|B.isna()).mean()
te = F[is_te]
d = pd.DataFrame({'whole_test': cov(te), 'public_220': cov(te.iloc[:220]),
                  'private_514': cov(te.iloc[220:])}).loc[PRESS]
print("support of the ten pressure level/lag columns, current cleaning (section 78 bar 0.916):")
print(d.round(3).to_string())
print("\n  mean support: whole %.3f  public %.3f  private %.3f"
      % (d.whole_test.mean(), d.public_220.mean(), d.private_514.mean()))
print("  section 78 reported private 0.69-0.82 for this block.")
print("  columns below the 0.916 bar now: whole %d, public %d, private %d, of %d"
      % ((d.whole_test<0.916).sum(), (d.public_220<0.916).sum(),
         (d.private_514<0.916).sum(), len(d)))

allc = pd.DataFrame({'whole': cov(te), 'public': cov(te.iloc[:220]), 'private': cov(te.iloc[220:])})
print("\n  across all %d features, columns below 0.916: whole %d, public %d, private %d"
      % (len(allc), (allc.whole<0.916).sum(), (allc.public<0.916).sum(), (allc.private<0.916).sum()))

# how much of v19's blend still sees the pressure levels?
W = {'bag_nopress':0.5907, 'cat':0.2123, 'enet':0.1971, 'hbt':0.0, 'ridge_e':0.0,
     'l2':0.0, 'robust_hbt':0.0}
has = {'bag_nopress':0, 'robust_hbt':0, 'cat':1, 'enet':1, 'hbt':1, 'ridge_e':1, 'l2':1}
print("\n  share of v19's GLOBAL blend weight held by members that can see the pressure"
      " levels: %.3f" % sum(W[m]*has[m] for m in W))
# every v16 member is fitted on all 118 columns, so its exposure is 1.000 by construction
print("  the same share in v16: %.3f" % 1.000)

# is bag_nopress actually better than hbt on the folds CLOSEST to the test window?
import pickle
frame = pickle.load(open('outputs/robust_core_scored.pkl','rb'))['frame'].copy()
zoo = pickle.load(open('outputs/zoo17_oof.pkl','rb'))
frame['bag_nopress'] = np.nan
for (n, fam, fold), v in zoo.items():
    if n != 'bag_nopress': continue
    m = (frame.family==fam)&(frame.fold==fold)
    frame.loc[m,'bag_nopress'] = v.reindex(pd.DatetimeIndex(frame.loc[m,'datetime'])).values
per = frame.groupby(['family','fold']).apply(
    lambda d: pd.Series({'start': d.datetime.min(),
                         'hbt': fp.rmse(d.y, d.hbt),
                         'bag': fp.rmse(d.y, d.bag_nopress)}), include_groups=False)
per['delta'] = per.bag - per.hbt
per = per.sort_values('start')
print("\n  bag_nopress minus hbt, folds ordered by validation start date:")
print("    earliest 9 folds %+.4f (%d/9 better)   latest 9 folds %+.4f (%d/9 better)"
      % (per.delta.iloc[:9].mean(), int((per.delta.iloc[:9]<0).sum()),
         per.delta.iloc[9:].mean(), int((per.delta.iloc[9:]<0).sum())))
print("    last 3 folds (closest to the test window): %s"
      % np.round(per.delta.iloc[-3:].values, 4))
json.dump(dict(press_support=d.to_dict(), n_below=int((allc.private<0.916).sum())),
          open('outputs/presscheck.json','w'), indent=2)
