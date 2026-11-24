"""Does bag_nopress earn its keep BECAUSE the pressure block loses support?

Section 130 read the late-fold trend (+0.008 early, -0.070 late) as the pressure block
falling out of support as the folds march toward the test window. That is an interpretation,
not a measurement. If it is right, the per-fold gain from removing the block must track the
per-fold SUPPORT of the block. If the gain tracks the calendar instead, the mechanism is
something else and section 130 is a story.

Section 66b is the reason to doubt it: clipping every test feature into the training band
moved the ridge member by 0.09 %RH, and section 81 says trees saturate on out-of-support
values anyway.
"""
import pickle, sys, json
import numpy as np, pandas as pd
sys.path[:0] = ['.', 'src']
import final_pipeline as fp

g = fp.load_grid(); F = fp.make_features(g); y = g[fp.TARGET]
is_tr = (g.is_test == 0).values & y.notna().values
PRESS = sorted(set(F.columns) - set(fp.no_pressure(F)))

frame = pickle.load(open('outputs/robust_core_scored.pkl','rb'))['frame'].copy()
zoo = pickle.load(open('outputs/zoo17_oof.pkl','rb'))
frame['bag_nopress'] = np.nan
for (n, fam, fold), v in zoo.items():
    if n != 'bag_nopress': continue
    m = (frame.family==fam)&(frame.fold==fold)
    frame.loc[m,'bag_nopress'] = v.reindex(pd.DatetimeIndex(frame.loc[m,'datetime'])).values

rows = []
for family, fold in frame[['family','fold']].drop_duplicates().itertuples(index=False, name=None):
    d = frame[(frame.family==family)&(frame.fold==fold)]
    vi = pd.DatetimeIndex(d.datetime)
    tr_idx = F.index[is_tr & (F.index < vi.min())]
    if len(tr_idx) < 300: continue
    A, B = F.loc[tr_idx, PRESS], F.loc[vi, PRESS]
    lo, hi = A.quantile(.01), A.quantile(.99)
    sup_press = float((((B>=lo)&(B<=hi))|B.isna()).mean().mean())
    Aa, Bb = F.loc[tr_idx], F.loc[vi]
    lo2, hi2 = Aa.quantile(.01), Aa.quantile(.99)
    sup_all = float((((Bb>=lo2)&(Bb<=hi2))|Bb.isna()).mean().mean())
    rows.append(dict(family=family, fold=fold, start=vi.min(),
                     day=(vi.min()-F.index.min()).days,
                     sup_press=sup_press, sup_all=sup_all,
                     gain=fp.rmse(d.y, d.bag_nopress) - fp.rmse(d.y, d.hbt)))
R = pd.DataFrame(rows).sort_values('start')
print("per fold: gain = RMSE(bag_nopress) - RMSE(hbt); negative means removing pressure helps\n")
print(R[['family','fold','day','sup_press','sup_all','gain']].round(4).to_string(index=False))

def rep(x, nm):
    r = np.corrcoef(R[x], R.gain)[0,1]
    print("  corr(gain, %-12s) = %+.3f" % (nm, r)); return r
print()
r_press = rep('sup_press', 'pressure support')
r_all   = rep('sup_all', 'overall support')
r_day   = rep('day', 'calendar day')
# partial: does pressure support explain the gain once the calendar is removed?
from numpy.polynomial import polynomial as Pn
def resid(a, b):
    c = np.polyfit(b, a, 1); return a - np.polyval(c, b)
rg = resid(R.gain.values, R.day.values)
rp = resid(R.sup_press.values, R.day.values)
print("  partial corr(gain, pressure support | calendar day) = %+.3f"
      % np.corrcoef(rp, rg)[0,1])
rg2 = resid(R.gain.values, R.sup_press.values)
rd2 = resid(R.day.values, R.sup_press.values)
print("  partial corr(gain, calendar day | pressure support) = %+.3f"
      % np.corrcoef(rd2, rg2)[0,1])

# where does the test window sit on the pressure-support axis?
A = F.loc[F.index[is_tr], PRESS]; lo, hi = A.quantile(.01), A.quantile(.99)
te = F.loc[(g.is_test==1).values, PRESS]
def c(B): return float((((B>=lo)&(B<=hi))|B.isna()).mean().mean())
print("\n  CV folds span pressure support %.3f - %.3f" % (R.sup_press.min(), R.sup_press.max()))
print("  test window: whole %.3f   public 220 %.3f   private 514 %.3f"
      % (c(te), c(te.iloc[:220]), c(te.iloc[220:])))
sl = np.polyfit(R.sup_press, R.gain, 1)
for nm, v in (('public', c(te.iloc[:220])), ('private', c(te.iloc[220:]))):
    print("  line through the folds predicts gain %+.4f on the %s slice" % (np.polyval(sl, v), nm))
json.dump(dict(rows=R.assign(start=R.start.astype(str)).to_dict('records'),
               corr=dict(press=float(r_press), all=float(r_all), day=float(r_day)),
               slope=float(sl[0])), open('outputs/pressmech.json','w'), indent=2)
