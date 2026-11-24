import numpy as np, pandas as pd, sys
sys.path.insert(0,'.'); import final_pipeline as fp
A=pd.read_pickle('outputs/an10_loo_oof.pkl')
g=fp.load_grid(); F=fp.make_features(g); te=g.index[(g.is_test==1).values]
v10=pd.read_csv('outputs/submissions/v10_todblend.csv',parse_dates=['datetime']).set_index('datetime')['air_humidity'].reindex(te)
pub=np.r_[np.ones(220,bool),np.zeros(514,bool)]
# where do the test rows sit on the axes where the model is weak?
bins={'T':[0,20.17,23.03,27.05,32.28,36.02,99],'pressure':[0,1005.6,1010.4,1012.0,1013.1,1014.6,9999]}
print("share of rows per band, and the OOF RMSE of that band")
for k,ed in bins.items():
    oof=pd.cut(A[k],ed); tev=pd.cut(F.loc[te,k],ed)
    t=pd.DataFrame({'oof_rmse':A.groupby(oof,observed=True).se.apply(lambda s:np.sqrt(s.mean())),
                    'train_share':A.groupby(oof,observed=True).size()/len(A),
                    'public_share':pd.Series(tev[pub]).value_counts(normalize=True),
                    'private_share':pd.Series(tev[~pub]).value_counts(normalize=True)})
    print(f"\n--- {k} ---"); print(t.round(3).to_string())
    for s in ['public_share','private_share']:
        print(f"   difficulty-weighted expectation ({s}): RMSE ~ {np.sqrt((t[s].fillna(0)*t.oof_rmse**2).sum()/t[s].fillna(0).sum()):.3f}")
# predicted-RH band exposure (the under-dispersion axis)
ed=[0,36.49,43.25,54.61,66.02,77.55,101]
oof=pd.cut(A.pred,ed); tev=pd.cut(v10,ed)
t=pd.DataFrame({'oof_rmse':A.groupby(oof,observed=True).se.apply(lambda s:np.sqrt(s.mean())),
                'oof_bias':A.groupby(oof,observed=True).res.mean(),
                'train_share':A.groupby(oof,observed=True).size()/len(A),
                'public_share':pd.Series(tev[pub]).value_counts(normalize=True),
                'private_share':pd.Series(tev[~pub]).value_counts(normalize=True)})
print("\n--- by PREDICTED RH (the under-dispersion axis) ---"); print(t.round(3).to_string())
print("\nprediction std: OOF %.2f | v10 public %.2f | v10 private %.2f"%(A.pred.std(),v10[pub].std(),v10[~pub].std()))
