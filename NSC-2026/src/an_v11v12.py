"""Can a 220-row public slice tell v11 from v12 at all?  Moving-block bootstrap on the
prediction difference, using the OOF residual scale and the measured lag-1 autocorrelation."""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'.'); import final_pipeline as fp
g=fp.load_grid(); te=g.index[(g.is_test==1).values]
S={n:pd.read_csv(f'outputs/submissions/{n}.csv',parse_dates=['datetime']).set_index('datetime')['air_humidity'].reindex(te).values
   for n in ['v11_seed5','v12_harmbias','v13_lowsupport']}
A=pd.read_pickle('outputs/an10_loo_oof.pkl')      # LOO OOF residuals of the shipped stack
res=A.res.values
print("OOF residual sd %.2f, lag-1 autocorr %.3f"%(res.std(),np.corrcoef(res[:-1],res[1:])[0,1]))
rng=np.random.default_rng(0); BL=48   # 1-day blocks, to respect the residual autocorrelation
def sim(d,n,reps=20000):
    """RMSE difference between two predictions that differ by d, given plausible errors."""
    out=[]
    nb=int(np.ceil(n/BL))
    for _ in range(reps):
        st=rng.integers(0,len(res)-BL,nb)
        e=np.concatenate([res[s:s+BL] for s in st])[:n]
        i=rng.integers(0,len(d)-n) if len(d)>n else 0
        dd=d[i:i+n]
        out.append(np.sqrt(np.mean((e+dd)**2))-np.sqrt(np.mean(e**2)))
    return np.array(out)
for a,b in [('v11_seed5','v12_harmbias'),('v11_seed5','v13_lowsupport'),('v12_harmbias','v13_lowsupport')]:
    d=S[b]-S[a]
    s=sim(d,220)
    print("\n%s -> %s : prediction RMS difference %.3f %%RH"%(a,b,np.sqrt((d**2).mean())))
    print("   if the change were pure noise, a 220-row public score would move by"
          " %+.3f on average, 90%% band [%+.3f, %+.3f]"%(s.mean(),np.percentile(s,5),np.percentile(s,95)))
    print("   standard error of a 220-row public comparison: +/-%.3f"%s.std())
d=S['v12_harmbias']-S['v11_seed5']; s=sim(d,220)
print("\nobserved v11->v12 public move: +0.01697")
print("that is %.2f standard errors from the nested-CV projection of -0.025"%((0.01697+0.025)/s.std()))
print("P(seeing a move this positive or worse if v12 really is 0.025 better) = %.2f"%np.mean(s-0.025>=0.01697))
