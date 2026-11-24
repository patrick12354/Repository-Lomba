"""Does the test file's tail artefact (47 slots with the whole daily block missing,
plus no grid beyond the last row) cost RMSE?  Measured inside training."""
import numpy as np, pandas as pd, sys, time
sys.path.insert(0,'.')
import final_pipeline as fp

DAILY_ALL = fp.DAILY + ['gdd']
g = fp.load_grid()
IDX = g.index
tr_idx = IDX[(g.is_test==0).values & g[fp.TARGET].notna().values]
y = g[fp.TARGET]

F_norm = fp.make_features(g)
end_all = tr_idx.max()

def testlike_features(vend, ntail=47, do_trunc=True, do_null=True):
    g2 = g.copy()
    if do_null:
        tail = IDX[(IDX<=vend)][-ntail:]
        g2.loc[tail, DAILY_ALL] = np.nan
    if do_trunc:
        g2 = g2[IDX<=vend]
    return fp.make_features(g2)[F_norm.columns]

def fit_blend(t, v, Ftr, Fva):
    esv = fp.es(Fva.loc[v,'T'].values)
    esT_tr = pd.Series(fp.es(Ftr.loc[t,'T'].values), index=t)
    E = y.loc[t]*esT_tr/100.0
    P={}
    for m in fp.MODELS:
        P[m]=np.clip(fp.predict(m, Ftr.loc[t], y.loc[t], Fva.loc[v], esv, E, (0,)),5,100)
    return pd.DataFrame(P)[fp.MODELS].values

W_GLOBAL = np.array([0.480,0.228,0.050,0.192,0.050])   # shipped v8 weights (progress §61)

rows=[]
t0=time.time()
for k in range(5):
    vend = end_all - pd.Timedelta(days=3*k)
    vs   = vend - pd.Timedelta(days=15, hours=6)
    v = tr_idx[(tr_idx>vs)&(tr_idx<=vend)]
    t = tr_idx[tr_idx<=vs]
    if len(t)<400 or len(v)<400: continue
    arms = {'normal':F_norm,
            'trunc':testlike_features(vend, do_null=False),
            'trunc+null':testlike_features(vend, do_null=True)}
    tail = v[-47:]; main = v[:-47]
    for name,Fva in arms.items():
        Pm = fit_blend(t, v, F_norm, Fva)
        pred = pd.Series(Pm@W_GLOBAL, index=v)
        rows.append(dict(fold=k, arm=name, vend=str(vend.date()),
                         rmse_all=fp.rmse(y.loc[v],pred),
                         rmse_main=fp.rmse(y.loc[main],pred.loc[main]),
                         rmse_tail47=fp.rmse(y.loc[tail],pred.loc[tail])))
    print(f"  fold {k} done  {time.time()-t0:.0f}s", flush=True)

d=pd.DataFrame(rows)
pd.set_option('display.width',200)
print("\nper fold:\n", d.round(4).to_string(index=False))
print("\nmeans by arm:\n", d.groupby('arm')[['rmse_all','rmse_main','rmse_tail47']].mean().round(4).to_string())
b=d.pivot(index='fold',columns='arm',values='rmse_tail47')
print("\ntail-47 RMSE, per fold:\n", b.round(3).to_string())
print("\ndelta on the tail 47 rows vs normal:")
print((b[['trunc','trunc+null']].sub(b['normal'],axis=0)).round(3).to_string())
a=d.pivot(index='fold',columns='arm',values='rmse_all')
print("\ndelta on the WHOLE 15-day window vs normal:")
print((a[['trunc','trunc+null']].sub(a['normal'],axis=0)).round(4).to_string())
d.to_csv('outputs/exp_tail_artifact.csv',index=False)
