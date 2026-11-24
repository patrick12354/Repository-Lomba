import numpy as np, lab_common as C
class Scorer:
    """eb_twmae cepat via bincount, untuk banyak realisasi event + subset record."""
    def __init__(self, evs, keep):
        self.parts=[]
        for dec,f in ((True,C.FD),(False,1-C.FD)):
            m = keep & ((~C.rnd_tr) if dec else C.rnd_tr)
            idx=np.where(m)[0]
            per=[]
            for e in evs:
                _,inv=np.unique(e[idx],return_inverse=True)
                nrec=np.bincount(inv).astype(float)
                mm=np.zeros(len(nrec)); mm[inv]=C.y[idx]
                w=C.mag_weight(mm)
                per.append((inv,nrec,w,w.sum(),len(nrec)))
            self.parts.append((idx,f,per))
        self.n=len(evs)
    def __call__(self, p):
        tot=0.0
        for idx,f,per in self.parts:
            err=np.abs(C.y[idx]-p[idx]); s=0.0
            for inv,nrec,w,wsum,ne in per:
                mae=np.bincount(inv,weights=err,minlength=ne)/nrec
                s+=(w*mae).sum()/wsum
            tot+=f*s/self.n
        return tot

class Post:
    """smoothing + ekspansi per-subset versi cepat (precompute slice grup depth)."""
    def __init__(self, dep, lam_dec=0.95, lam_deep=0.35, T_deep=100, a_dec=1.15, a_rnd=1.05):
        r=np.isclose(dep,np.round(dep))
        self.lam=np.where(~r, lam_dec, np.where(dep>=T_deep, lam_deep, 0.0))
        order=np.argsort(dep,kind="stable"); self.order=order
        ds=dep[order]; bnd=np.flatnonzero(np.diff(ds))+1
        self.slices=np.concatenate([[0],bnd,[len(ds)]])
        self.active=self.lam>0
        self.r=r; self.a_dec=a_dec; self.a_rnd=a_rnd
    def __call__(self, p):
        ps=p[self.order]; gm=np.empty_like(ps)
        sl=self.slices
        for i in range(len(sl)-1):
            gm[sl[i]:sl[i+1]]=np.median(ps[sl[i]:sl[i+1]])
        g=np.empty_like(p); g[self.order]=gm
        q=(1-self.lam)*p+self.lam*g
        out=q.copy()
        for m,a in ((self.r,self.a_rnd),(~self.r,self.a_dec)):
            mu=q[m].mean(); out[m]=mu+a*(q[m]-mu)
        return out
