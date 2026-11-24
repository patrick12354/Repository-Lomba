import pandas as pd, numpy as np
tr = pd.read_csv('Dataset/train.csv', parse_dates=['datetime'])
te = pd.read_csv('Dataset/test.csv',  parse_dates=['datetime'])
print("train", tr.datetime.min(), "->", tr.datetime.max(), len(tr))
print("test ", te.datetime.min(), "->", te.datetime.max(), len(te))
# assume temporal public/private split at 30%
n = len(te); k = int(round(0.30*n))
print(f"\nif temporal 30/70: public = rows 0..{k-1}  ({te.datetime.iloc[0]} -> {te.datetime.iloc[k-1]})")
print(f"                   private= rows {k}..{n-1} ({te.datetime.iloc[k]} -> {te.datetime.iloc[n-1]})")

cols = [c for c in te.columns if c!='datetime']
near = te.iloc[:k]; far = te.iloc[k:]
rows=[]
def longest_nan_run(s):
    m = s.isna().values; best=cur=0
    for v in m:
        cur = cur+1 if v else 0
        best = max(best,cur)
    return best
for c in cols:
    rows.append(dict(col=c,
        tr_na=tr[c].isna().mean() if c in tr else np.nan,
        te_na=te[c].isna().mean(),
        near_na=near[c].isna().mean(), far_na=far[c].isna().mean(),
        near_run=longest_nan_run(near[c]), far_run=longest_nan_run(far[c]),
        near_std=near[c].std(), far_std=far[c].std()))
d = pd.DataFrame(rows)
d['dna'] = d.far_na - d.near_na
pd.set_option('display.width',200); pd.set_option('display.max_rows',60)
print("\n", d.sort_values('dna', ascending=False).round(3).to_string(index=False))
