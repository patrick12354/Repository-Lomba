"""v14 scored 3.31777 against v12's 3.02286.  But v14 = v12 + drop85 + rng-bias, two changes
bundled into one submission.  What can a 220-row slice attribute to which?"""
import numpy as np, pandas as pd, sys
sys.path.insert(0,'.'); import final_pipeline as fp
g=fp.load_grid(); te=g.index[(g.is_test==1).values]
D=pd.DataFrame({n:pd.read_csv(f'outputs/submissions/{n}.csv',parse_dates=['datetime']).set_index('datetime')['air_humidity'].reindex(te).values
   for n in ['v11_seed5','v12_harmbias','v13_lowsupport','v14_rngbias']},index=te)
pub=np.r_[np.ones(220,bool),np.zeros(514,bool)]
A=pd.read_pickle('outputs/an10_loo_oof.pkl'); res=A.res.values
rng=np.random.default_rng(0); BL=48
def sim(d,n=220,reps=40000):
    out=[];nb=int(np.ceil(n/BL))
    for _ in range(reps):
        st=rng.integers(0,len(res)-BL,nb)
        e=np.concatenate([res[s:s+BL] for s in st])[:n]
        i=rng.integers(0,len(d)-n) if len(d)>n else 0
        dd=d[i:i+n]
        out.append(np.sqrt(np.mean((e+dd)**2))-np.sqrt(np.mean(e**2)))
    return np.array(out)
print("public-slice perturbation of each step, and what a 220-row score does with it:")
steps=[('v12 -> v13  (low-support filter only)','v12_harmbias','v13_lowsupport'),
       ('v13 -> v14  (wide-range correction only)','v13_lowsupport','v14_rngbias'),
       ('v12 -> v14  (BOTH, what was submitted)','v12_harmbias','v14_rngbias')]
S={}
for lab,a,b in steps:
    d=(D[b]-D[a]).values
    dp=d[pub]
    s=sim(dp)
    S[lab]=(s.mean(),s.std())
    print("\n%s"%lab)
    print("   public rows changed %3d/220, RMS %.4f"%((np.abs(dp)>1e-9).sum(),np.sqrt((dp**2).mean())))
    print("   if the change were pure noise the public score moves %+.3f, SE +/-%.3f"%(s.mean(),s.std()))
obs=3.31777-3.02286
m,se=S['v12 -> v14  (BOTH, what was submitted)']
print("\nOBSERVED v12 -> v14 public move: %+.5f"%obs)
print("   pure-noise expectation %+.3f  =>  excess %+.3f  =  %.2f standard errors"%(m,obs-m,(obs-m)/se))
print("   P(a move this bad or worse if BOTH changes were pure noise)      = %.2f"%np.mean(sim((D.v14_rngbias-D.v12_harmbias).values[pub])>=obs))
for helps in (0.05,0.10,0.20):
    print("   P(a move this bad or worse if the pair really helped by %.2f)   = %.3f"%(
        helps,np.mean(sim((D.v14_rngbias-D.v12_harmbias).values[pub])-helps>=obs)))
m2,se2=S['v13 -> v14  (wide-range correction only)']
print("\nWhat the public slice can say about the wide-range correction ALONE:")
print("   it moves 27 of 220 public rows; SE of a public verdict on it = +/-%.3f"%se2)
print("   the bundled +0.295 is %.0fx that, so essentially ALL of it is attributable to"%(obs/se2))
print("   the low-support filter, which perturbs the public slice %.1fx harder."%(
    np.sqrt(((D.v13_lowsupport-D.v12_harmbias).values[pub]**2).mean())/
    np.sqrt(((D.v14_rngbias-D.v13_lowsupport).values[pub]**2).mean())))
