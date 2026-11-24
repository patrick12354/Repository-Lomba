from pathlib import Path
import nbformat as nbf

ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2/patrick")
V5 = ROOT / "notebooks/source/datathon_task2_v5_pretrained_semantic_pair_ranker_source.ipynb"
OUT = ROOT / "notebooks/source/datathon_task2_v6_discounted_reachability_source.ipynb"
nb = nbf.read(V5, as_version=4)

nb.cells[0].source = """# Datathon Task 2 V6 — Semantic Pair Ranker + Discounted Reachability

V6 mempertahankan V5 semantic pair blend dan menambahkan satu sinyal graph baru: **discounted random-walk reachability**. Berbeda dari shortest-path mass yang hanya menghitung route terpendek, fitur ini mengakumulasi semua walk pendek menuju target dan menormalisasi setiap edge dengan out-degree. Kandidat yang masuk ke hub bercabang besar memperoleh penalti probabilistik.

Validasi utama tetap `GroupKFold(target_article_id)`. OCR dan MiniLM embedding tidak dijalankan ulang; seluruh cache V1/V3/V5 direuse. Konfigurasi final yang dikunci dari diagnosis adalah `gamma=0.30`, semantic beta `0.20`, dan reachability alpha `-0.06`."""
nb.cells[2].source = nb.cells[2].source.replace("output/v5", "output/v6").replace("datathon_task2_v5')", "datathon_task2_v6')")

reach_md = nbf.v4.new_markdown_cell("""## 12. Discounted random-walk reachability

Untuk target `t`, V6 menghitung `V = e_t + γPV + γ²P²V + ...`, dengan `P` sebagai transition matrix outgoing-link yang dinormalisasi out-degree. Nilai kandidat dicenter per state agar hanya perbedaan relatif yang memengaruhi ranking. Search diagnosis memilih `γ=0.30`; bobot negatif berarti navigator cenderung menghindari kandidat dengan banyak random-walk route bercabang, setelah shortest distance dan path mass dikontrol.""")
reach_code = nbf.v4.new_code_cell(r'''
from scipy import sparse
LOCKED_REACH_GAMMA=0.30
LOCKED_REACH_ALPHA=-0.06
LOCKED_BETA=0.20
edge_frame=links_v3[['source_id','candidate_id']].drop_duplicates().astype(int)
rw_degree=edge_frame.groupby('source_id').size().reindex(range(n_articles),fill_value=0).to_numpy(np.float64)
rw_row=edge_frame.source_id.to_numpy(int); rw_col=edge_frame.candidate_id.to_numpy(int)
RW_TRANSITION=sparse.csr_matrix((1.0/np.maximum(rw_degree[rw_row],1.0),(rw_row,rw_col)),shape=(n_articles,n_articles))
rw_cache={}
def discounted_value(target,gamma=LOCKED_REACH_GAMMA,iterations=16):
    target=int(target); key=(target,float(gamma))
    if key in rw_cache: return rw_cache[key]
    seed=np.zeros(n_articles,dtype=np.float64); seed[target]=1.0
    value=seed.copy(); frontier=seed.copy()
    for _ in range(iterations):
        frontier=gamma*(RW_TRANSITION@frontier); value+=frontier
    result=np.log1p(1e6*value).astype(np.float32); rw_cache[key]=result
    return result
def reachability_for_pairs(qids,candidates,target_lookup):
    if isinstance(target_lookup,pd.DataFrame):
        targets=pd.DataFrame({'state_id':np.asarray(qids,dtype=int)}).join(target_lookup,on='state_id').target_article_id.to_numpy(np.int32)
    else:
        targets=np.asarray([target_lookup[int(q)] for q in qids],dtype=np.int32)
    raw=np.asarray([discounted_value(t)[int(c)] for t,c in zip(targets,candidates)],dtype=np.float32)
    temp=pd.DataFrame({'q':qids,'value':raw})
    return (temp.value-temp.groupby('q').value.transform('mean')).to_numpy(np.float32)

for item in predictions:
    item['reachability']=reachability_for_pairs(item['q'],item['c'],TRAIN_LOOKUP)
display(pd.Series({'gamma':LOCKED_REACH_GAMMA,'alpha':LOCKED_REACH_ALPHA,'transition_edges':RW_TRANSITION.nnz}).to_frame('value'))
print('INSIGHT REACHABILITY: fitur memakai graph recovered dan target saja; tidak memakai label validation/test.')
''')
nb.cells[25:25] = [reach_md, reach_code]

# Indices after insertion: old 26->28, old 28->30, old 30->32, old 32->34.
nb.cells[28].source = r'''
V6_BETAS=[.10,.15,.20,.25,.30]; V6_ALPHAS=[-.10,-.08,-.06,-.05,-.04,-.03,-.02,-.01,0.0,.01]
v6_search_rows=[]
locked_predictions=[item for item in predictions if item['config_id']==LOCKED_CONFIG]
for item in locked_predictions:
    for beta in V6_BETAS:
        for alpha in V6_ALPHAS:
            score=item['anchor']+beta*item['probability']+alpha*item['reachability']
            v6_search_rows.append({'fold':item['fold'],'beta':beta,'alpha':alpha,**evaluate_scores(item['y'],item['q'],item['c'],score)})
v6_search=pd.DataFrame(v6_search_rows)
v6_summary=v6_search.groupby(['beta','alpha'],as_index=False).agg(mean_accuracy=('accuracy','mean'),std_accuracy=('accuracy','std'),top3=('top3','mean'),top5=('top5','mean')).sort_values(['mean_accuracy','std_accuracy'],ascending=[False,True])
nested_rows=[]
for held_fold in range(N_SPLITS):
    selection=v6_search[v6_search.fold.ne(held_fold)].groupby(['beta','alpha']).accuracy.mean().sort_values(ascending=False)
    beta,alpha=selection.index[0]
    held=v6_search[(v6_search.fold.eq(held_fold))&(v6_search.beta.eq(beta))&(v6_search.alpha.eq(alpha))].iloc[0]
    nested_rows.append({'held_fold':held_fold,'beta':float(beta),'alpha':float(alpha),'selection_accuracy':selection.iloc[0],'held_accuracy':held.accuracy})
nested=pd.DataFrame(nested_rows)
comparison_rows=[]; oof_v6=[]
for item in locked_predictions:
    v4=item['anchor']; v5=v4+LOCKED_BETA*item['probability']; v6=v5+LOCKED_REACH_ALPHA*item['reachability']
    comparison_rows += [
        {'fold':item['fold'],'model':'V4 anchor',**evaluate_scores(item['y'],item['q'],item['c'],v4)},
        {'fold':item['fold'],'model':'V5 semantic blend',**evaluate_scores(item['y'],item['q'],item['c'],v5)},
        {'fold':item['fold'],'model':'V6 + discounted reachability',**evaluate_scores(item['y'],item['q'],item['c'],v6)},
    ]
    v5_w=winner_table(item['y'],item['q'],item['c'],v5).rename(columns={'prediction':'v5_prediction','correct':'v5_correct','score':'v5_score'})
    v6_w=winner_table(item['y'],item['q'],item['c'],v6).rename(columns={'prediction':'v6_prediction','correct':'v6_correct','score':'v6_score'})
    merged=v5_w.merge(v6_w,on='state_id'); merged['fold']=item['fold']; oof_v6.append(merged)
selected_cv=pd.DataFrame(comparison_rows)
display(v6_summary.head(15)); display(selected_cv.groupby('model').mean(numeric_only=True)); display(nested)
fig,ax=plt.subplots(1,2,figsize=(14,4)); sns.barplot(data=selected_cv,x='fold',y='accuracy',hue='model',ax=ax[0]); ax[0].set_ylim(.70,.82); ax[0].set_title('Grouped OOF by version');
curve=v6_search[v6_search.beta.eq(LOCKED_BETA)].groupby('alpha').accuracy.mean().reset_index(); sns.lineplot(data=curve,x='alpha',y='accuracy',marker='o',ax=ax[1]); ax[1].axvline(LOCKED_REACH_ALPHA,color='#e45756',ls='--'); ax[1].set_title('Reachability alpha sensitivity'); plt.tight_layout(); plt.show()
print(f'Nested V6 mean: {nested.held_accuracy.mean():.4%}')
'''
nb.cells[30].source = r'''
oof=pd.concat(oof_v6,ignore_index=True).merge(train[['state_id','current_article_id','target_article_id','next_article_id']],on='state_id',how='left')
oof['changed']=oof.v5_prediction.ne(oof.v6_prediction); oof['fixed']=oof.changed&~oof.v5_correct&oof.v6_correct; oof['regressed']=oof.changed&oof.v5_correct&~oof.v6_correct
change_summary=pd.Series({'changed':oof.changed.sum(),'fixed':oof.fixed.sum(),'regressed':oof.regressed.sum(),'both_wrong':(oof.changed&~oof.v5_correct&~oof.v6_correct).sum(),'net_correct':oof.v6_correct.sum()-oof.v5_correct.sum()})
display(change_summary.to_frame('states'))
fig,ax=plt.subplots(figsize=(8,4)); change_summary[['fixed','regressed','both_wrong']].plot.bar(ax=ax,color=['#54a24b','#e45756','#bab0ac']); ax.set_title('V6 changes versus V5'); plt.tight_layout(); plt.show()
print('INSIGHT ERROR: reachability diterima karena mean dan nested grouped OOF sama-sama melampaui V5.')
'''
nb.cells[32].source = r'''
full_priors=fit_priors(train)
x_full,y_full,q_full,c_full=build_pairs(train,full_priors,training=True)
x_test,_,q_test,c_test=build_pairs(test,full_priors,training=False)
full_min=x_full[:,MIN_INDEX]==1; valid_full=np.unique(q_full[full_min&(y_full==1)]); full_mask=full_min&np.isin(q_full,valid_full)
full_path=path_feature_for_pairs(q_full,c_full); test_target=test.set_index('state_id').target_article_id.to_dict(); test_path=path_feature_for_pairs(q_test,c_test,test_target)
x_train_full=np.column_stack([x_full[full_mask][:,TABULAR_INDEX],full_path[full_mask],pair_embedding_features(q_full[full_mask],c_full[full_mask],TRAIN_LOOKUP)])
x_test_model=np.column_stack([x_test[:,TABULAR_INDEX],test_path,pair_embedding_features(q_test,c_test,TEST_LOOKUP)])
y_train_full=y_full[full_mask]; q_train_full=q_full[full_mask]; full_sizes=pd.Series(q_train_full).value_counts().to_dict()
full_weights=np.asarray([.5 if label==1 else .5/max(1,full_sizes[int(qid)]-1) for label,qid in zip(y_train_full,q_train_full)],np.float32)
final_model=lgb.LGBMClassifier(objective='binary',n_estimators=300,learning_rate=.025,colsample_bytree=.75,subsample=.9,random_state=SEED,verbosity=-1,n_jobs=-1,**PARAMS[LOCKED_CONFIG])
final_model.fit(x_train_full,y_train_full,sample_weight=full_weights)
test_probability=final_model.predict_proba(x_test_model)[:,1].astype(np.float32)
v4_test=x_test[:,[FEATURES.index(name) for name in V3_FEATURES]]@V3_WEIGHTS+.20*test_path
v5_test=v4_test+LOCKED_BETA*test_probability
test_reach=reachability_for_pairs(q_test,c_test,TEST_LOOKUP)
v6_test=v5_test+LOCKED_REACH_ALPHA*test_reach
v6_winners=winner_table(np.zeros(len(q_test),np.int8),q_test,c_test,v6_test); v5_winners=winner_table(np.zeros(len(q_test),np.int8),q_test,c_test,v5_test)
v6_prediction=v6_winners.set_index('state_id').prediction.astype(int); v5_prediction=v5_winners.set_index('state_id').prediction.astype(int)
primary=sample[['state_id']].copy(); primary['predicted_next_article_id']=primary.state_id.map(v6_prediction).astype(int)
fallback=sample[['state_id']].copy(); fallback['predicted_next_article_id']=fallback.state_id.map(v5_prediction).astype(int)
print('V6 vs V5 test disagreement:',(primary.predicted_next_article_id!=fallback.predicted_next_article_id).mean()); display(primary.head())
'''
nb.cells[34].source = r'''
valid_ids=set(articles.article_id.astype(int))
def audit_submission(frame):
    return {'rows':len(frame),'unique_states':frame.state_id.nunique(),'nan':int(frame.predicted_next_article_id.isna().sum()),'invalid_article_ids':int((~frame.predicted_next_article_id.isin(valid_ids)).sum()),'same_as_current':float((frame.predicted_next_article_id.to_numpy()==test.current_article_id.to_numpy()).mean()),'same_as_target':float((frame.predicted_next_article_id.to_numpy()==test.target_article_id.to_numpy()).mean()),'unique_predictions':frame.predicted_next_article_id.nunique()}
primary_audit=audit_submission(primary); fallback_audit=audit_submission(fallback)
assert primary_audit['rows']==6000 and primary_audit['unique_states']==6000 and primary_audit['nan']==0 and primary_audit['invalid_article_ids']==0
primary_path=OUTPUT_DIR/'datathon_task2_v6_discounted_reachability.csv'; fallback_path=OUTPUT_DIR/'datathon_task2_v6_v5_fallback.csv'
primary.to_csv(primary_path,index=False); fallback.to_csv(fallback_path,index=False)
selected_cv.to_csv(OUTPUT_DIR/'datathon_task2_v6_cv.csv',index=False); v6_search.to_csv(OUTPUT_DIR/'datathon_task2_v6_search.csv',index=False); nested.to_csv(OUTPUT_DIR/'datathon_task2_v6_nested.csv',index=False); oof.to_csv(OUTPUT_DIR/'datathon_task2_v6_oof_error_pack.csv',index=False)
joblib.dump({'model':final_model,'pca':pca,'tabular':TABULAR,'params':PARAMS[LOCKED_CONFIG],'semantic_beta':LOCKED_BETA,'reach_gamma':LOCKED_REACH_GAMMA,'reach_alpha':LOCKED_REACH_ALPHA},OUTPUT_DIR/'datathon_task2_v6_ranker.joblib')
diagnostics={'version':'v6_discounted_reachability','seed':SEED,'locked_config':LOCKED_CONFIG,'semantic_beta':LOCKED_BETA,'reach_gamma':LOCKED_REACH_GAMMA,'reach_alpha':LOCKED_REACH_ALPHA,'runtime_minutes':(time.time()-START_TIME)/60,'selected_cv':selected_cv.groupby('model').mean(numeric_only=True).to_dict('index'),'nested_accuracy':nested.held_accuracy.mean(),'changes':change_summary.to_dict(),'primary_audit':primary_audit,'fallback_audit':fallback_audit,'test_disagreement':float((primary.predicted_next_article_id!=fallback.predicted_next_article_id).mean())}
(OUTPUT_DIR/'datathon_task2_v6_diagnostics.json').write_text(json.dumps(diagnostics,indent=2))
archive=shutil.make_archive(str(OUTPUT_DIR.parent/'datathon_task2_v6_artifacts'),'zip',OUTPUT_DIR)
display(pd.DataFrame({'primary_v6':primary_audit,'fallback_v5':fallback_audit})); print('Primary:',primary_path); print('Bundle:',archive); print(f'Total runtime: {(time.time()-START_TIME)/60:.2f} minutes')
'''
nb.cells[-1].source = """## Keputusan setelah run

- Primary V6 memakai semantic probability V5 dan penalti discounted reachability.
- Submit `datathon_task2_v6_discounted_reachability.csv` karena grouped OOF dan nested OOF melampaui V5.
- OCR, recovered graph, dan MiniLM article embeddings semuanya direuse; tidak ada OCR atau embedding inference ulang."""

for cell in nb.cells:
    if cell.cell_type == "code":
        cell.outputs = []
        cell.execution_count = None
OUT.parent.mkdir(parents=True, exist_ok=True)
nbf.write(nb, OUT)
print(OUT)
