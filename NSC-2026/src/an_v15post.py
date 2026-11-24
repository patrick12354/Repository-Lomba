"""v15 = v12 + the wide-range correction and nothing else.  It scored 3.14901 against 3.02286.
This one IS attributable: what bias on the 27 affected public rows would produce that move?"""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'.'); import final_pipeline as fp
g=fp.load_grid(); F=fp.make_features(g); te=g.index[(g.is_test==1).values]
D=pd.DataFrame({n:pd.read_csv(f'outputs/submissions/{n}.csv',parse_dates=['datetime']).set_index('datetime')['air_humidity'].reindex(te).values
   for n in ['v12_harmbias','v15_rngonly']},index=te)
pub=np.r_[np.ones(220,bool),np.zeros(514,bool)]
d=(D.v15_rngonly-D.v12_harmbias).values
m=np.abs(d)>1e-9
print("rows the correction touches: public %d/220, private %d/514"%((m&pub).sum(),(m&~pub).sum()))
c=-d[m&pub][0]
print("correction subtracted: %.3f %%RH"%c)
obs=3.14901-3.02286
mse12=3.02286**2; mse15=3.14901**2
dmse=mse15-mse12
k=(m&pub).sum(); frac=k/220
print("\nobserved public move %+.5f  ->  MSE %.4f -> %.4f  (delta %+.4f)"%(obs,mse12,mse15,dmse))
b=(frac*c**2-dmse)/(2*frac*c)
print("implied true bias on those %d public rows: %+.2f %%RH"%(k,b))
print("   (training estimate was +2.74, 95%% CI [+1.56, +3.83])")
A=pd.read_pickle('outputs/an10_loo_oof.pkl'); res=A.res.values
rng=np.random.default_rng(0); BL=48
def sim(dd,n=220,reps=40000,bias=0.0):
    out=[];nb=int(np.ceil(n/BL))
    for _ in range(reps):
        st=rng.integers(0,len(res)-BL,nb); e=np.concatenate([res[s:s+BL] for s in st])[:n]
        e=e+bias*(np.abs(dd[:n])>1e-9)
        out.append(np.sqrt(np.mean((e+dd[:n])**2))-np.sqrt(np.mean(e**2)))
    return np.array(out)
dp=d[pub]
s0=sim(dp)
print("\nP(a public move this bad or worse | the correction is pure noise, bias 0) = %.3f"%np.mean(s0>=obs))
print("   that is %.2f standard errors"%((obs-s0.mean())/s0.std()))
for bb in (1.56,2.74,3.83):
    sb=sim(dp,bias=bb)
    print("P(this bad or worse | true bias on those rows = %+.2f) = %.4f"%(bb,np.mean(sb>=obs)))
print("\nprivate rows the correction touches: %d (%.1f%%)"%((m&~pub).sum(),100*(m&~pub).mean()/((~pub).mean())))
print("if the implied bias %+.2f also holds on the private band, the correction costs there too:"%b)
for base in (3.6,):
    fr=(m&~pub).sum()/514
    dm=fr*(c**2-2*b*c)
    print("   private %.2f -> %.2f  (%+.3f)"%(base,np.sqrt(base**2+dm),np.sqrt(base**2+dm)-base))
