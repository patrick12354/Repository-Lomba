import numpy as np, pandas as pd, sys
sys.path.insert(0,'.'); import final_pipeline as fp
g=fp.load_grid(); F=fp.make_features(g); y=g[fp.TARGET]; IDX=F.index
tr=IDX[(g.is_test==0).values & y.notna().values]; te=IDX[(g.is_test==1).values]
P=pd.read_csv('outputs/an9_test_members.csv',index_col=0,parse_dates=True)[fp.MODELS]
W=dict(zip(fp.MODELS,[0.480,0.228,0.050,0.192,0.050]))
w=np.array([W[m] for m in fp.MODELS])
P['blend']=P[fp.MODELS].values@w

# --- physics referees (parameter-free, target-free) -------------------------------
for nm in ['rh_tmin48','rh_q48','rh_tmin96','rh_q96']:
    P[nm]=F.loc[te,nm].values
REF=['rh_tmin48','rh_q48']
# calibrate each referee on TRAIN (single slope+intercept), then read it on test
cal={}
for nm in REF:
    x=F.loc[tr,nm].values; t=y.loc[tr].values
    m=np.isfinite(x)&np.isfinite(t); b=np.polyfit(x[m],t[m],1)
    cal[nm]=b
    print(f"train fit: RH ~ {b[0]:.3f}*{nm} + {b[1]:.2f}   resid RMSE {np.sqrt(np.mean((np.polyval(b,x[m])-t[m])**2)):.2f}")
    P[nm+'_cal']=np.polyval(b,P[nm].values)

pub=np.r_[np.ones(220,bool),np.zeros(514,bool)]
cols=fp.MODELS+['blend']+[n+'_cal' for n in REF]
print("\nmean prediction by slice:")
s=pd.DataFrame({'public':P.loc[pub,cols].mean(),'private':P.loc[~pub,cols].mean()})
s['shift']=s.private-s.public
print(s.round(2).to_string())

# per-day: blend vs referee
D=P.copy(); D['d']=D.index.date
gg=D.groupby('d')[['hbt','cat','ridge','enet','ridge_e','blend','rh_tmin48_cal','rh_q48_cal']].mean()
gg['tree']=gg[['hbt','cat']].mean(1); gg['lin']=gg[['ridge','enet','ridge_e']].mean(1)
gg['ref']=gg[['rh_tmin48_cal','rh_q48_cal']].mean(1)
gg['blend-ref']=gg.blend-gg.ref; gg['tree-ref']=gg.tree-gg.ref; gg['lin-ref']=gg.lin-gg.ref
print("\nper-day, blend / trees / linears against the physics referee:")
print(gg[['tree','lin','blend','ref','tree-ref','lin-ref','blend-ref']].round(2).to_string())
print("\nmean |gap| vs referee:  public / private")
for c in ['tree-ref','lin-ref','blend-ref']:
    a=gg[c].iloc[:5].abs().mean(); b=gg[c].iloc[5:].abs().mean()
    print(f"  {c:10s} {a:6.2f} {b:6.2f}")

# weighted member spread (the §57c estimator), recomputed
sp=np.sqrt(((P[fp.MODELS].values-P['blend'].values[:,None])**2*w).sum(1))
print("\nweighted member spread:  public %.3f   private %.3f  (progress §57c: 2.106 / 1.980)"%(sp[:220].mean(),sp[220:].mean()))
dsp=pd.Series(sp,index=te); print("\nspread by day:"); print(dsp.groupby(dsp.index.date).mean().round(2).to_string())
