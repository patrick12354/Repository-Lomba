from pathlib import Path

import nbformat as nbf


ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2/patrick")
V4 = ROOT / "notebooks/source/datathon_task2_v4_shortest_path_mass_source.ipynb"
OUT = ROOT / "notebooks/source/datathon_task2_v5_pretrained_semantic_pair_ranker_source.ipynb"
source = nbf.read(V4, as_version=4)


def md(text):
    return nbf.v4.new_markdown_cell(text.strip())


def code(text):
    return nbf.v4.new_code_cell(text.strip())


setup = "".join(source.cells[2].source)
setup = setup.replace("LOCAL_OUTPUT_PATH = LOCAL_PATRICK_PATH/'output/v4'", "LOCAL_OUTPUT_PATH = LOCAL_PATRICK_PATH/'output/v5'")
setup = setup.replace("Path('/kaggle/working/datathon_task2_v4')", "Path('/kaggle/working/datathon_task2_v5')")

cells = [
    md("""
# Datathon Task 2 V5 — Pretrained Semantic Pair Ranker

V5 mempertahankan V4 shortest-path mass sebagai anchor, lalu menambahkan pretrained semantic embeddings melalui **pairwise nonlinear interactions**. MiniLM tidak di-fine-tune dan tidak menghasilkan teks; article embeddings sudah di-cache sehingga full notebook tetap CPU-friendly.

Success criteria:

- grouped OOF harus melampaui V4 `0.7736`;
- nested configuration selection tidak boleh turun dari V4;
- source tidak memakai Wikispeedia navigation ground truth atau lookup test state;
- submission dan reusable artifacts harus lolos audit.
    """),
    md("## 1. Setup dan reproducibility\n\nLocal run memakai existing `.venv`; Kaggle dapat memakai attached V5 embedding cache tanpa internet atau GPU."),
    code(setup),
    md("## 2. Load dan input contract\n\nDataset kompetisi dan reusable OCR cache divalidasi sebelum feature engineering."),
    source.cells[4],
    md("## 3. Reuse OCR recovery\n\nV5 tidak menjalankan OCR ulang. Persisted recovered edges V3 dipakai bila tersedia."),
    source.cells[6],
    md("## 4. Graph, OCR metadata, dan visual EDA\n\nGraph recovered V3 tetap menjadi graph utama karena official full graph justru menurunkan diagnostic OOF."),
    source.cells[8],
    source.cells[10],
    md("## 5. Competition-only semantic/category features dan reverse BFS"),
    source.cells[12],
    source.cells[14],
    md("## 6. Candidate-pair features dan grouped fold cache"),
    source.cells[16],
    source.cells[18],
    md("## 7. Locked V4 shortest-path mass anchor"),
    source.cells[20],
    md("""
## 8. Research findings yang membentuk V5

Dataset cocok dengan statistik Wikispeedia: 4.604 artikel dan sekitar 120 ribu links. Studi human wayfinding menemukan strategi **zoom-out** menuju high-degree hubs pada fase awal dan **homing-in** berbasis content similarity pada fase akhir. Studi article structure juga menemukan bias ke lead/infobox dan link di bagian atas halaman.

Diagnostic lokal V5 menguji semua implikasi tersebut:

- MiniLM cosine tunggal: tidak stabil;
- surrounding-context MiniLM: hanya 50,97% memilih truth pada V4 errors;
- phase-aware degree/semantic/layout: tidak mengalahkan nested V4;
- official Wikispeedia graph: hanya 69,09%, sehingga tidak dipakai;
- external navigation paths: tidak dimuat di notebook ini.

Yang bertahan adalah nonlinear embedding interaction: model dapat mempelajari dimensi hubungan candidate–target yang hilang ketika 384 dimensi dipadatkan menjadi satu cosine.

Referensi: [Human Wayfinding in Information Networks](https://ai.stanford.edu/~jure/pubs/wayfinding-www12.pdf), [article-structure navigation study](https://pmc.ncbi.nlm.nih.gov/articles/PMC5468769/), dan [official SNAP Wikispeedia description](https://snap.stanford.edu/data/wikispeedia.html).
    """),
    md("## 9. Load cached MiniLM article embeddings\n\nCache berisi satu normalized 384-D vector per article. Encoding tidak diulang dalam notebook."),
    code(r'''
EMBEDDING_NAME='datathon_task2_v5_minilm_article_embeddings.npz'
embedding_candidates=[OUTPUT_DIR/EMBEDDING_NAME,LOCAL_PATRICK_PATH/'output/v5'/EMBEDDING_NAME]
if IS_KAGGLE:
    embedding_candidates += list(Path('/kaggle/input').glob(f'**/{EMBEDDING_NAME}'))
EMBEDDING_PATH=next((p for p in embedding_candidates if p.exists()),None)
if EMBEDDING_PATH is None:
    raise FileNotFoundError(f'Attach V5 reusable bundle containing {EMBEDDING_NAME}. No model download is required when cache is attached.')
article_embedding=np.load(EMBEDDING_PATH)['embeddings'].astype(np.float32)
assert article_embedding.shape==(n_articles,384)
article_embedding/=np.maximum(np.linalg.norm(article_embedding,axis=1,keepdims=True),1e-8)
from sklearn.decomposition import PCA
pca=PCA(n_components=48,whiten=True,random_state=SEED)
embedding_pca=pca.fit_transform(article_embedding).astype(np.float32)
embedding_pca/=np.maximum(np.linalg.norm(embedding_pca,axis=1,keepdims=True),1e-8)
display(pd.Series({'embedding_path':str(EMBEDDING_PATH),'articles':len(article_embedding),'original_dimensions':384,'pair_ranker_dimensions':48,'pca_explained_variance':pca.explained_variance_ratio_.sum()}).to_frame('value'))
print('INSIGHT CACHE: pretrained encoder inference is skipped; only cached vectors and CPU PCA are used.')
    '''),
    md("""
## 10. Pairwise embedding interactions

For each `(current, candidate, target)` pair, V5 builds:

- candidate × target elementwise product;
- absolute candidate–target difference;
- candidate and target PCA coordinates;
- directional progress from current toward target;
- V4 graph/category/layout features.

Training is restricted to minimum-distance candidates whose truth is present. Every query contributes equal positive and negative mass.
    """),
    code(r'''
TABULAR=['word_cosine','char_cosine','category_exact_jaccard','category_token_jaccard','log_global_clicks','log_current_clicks','log_in_degree','log_out_degree','word_rank','char_rank','position_rank','category_overlap_count','category_prefix_jaccard','out_neighbor_jaccard','in_neighbor_jaccard','reciprocal_link']
TABULAR_INDEX=[FEATURES.index(name) for name in TABULAR]
MIN_INDEX=FEATURES.index('is_min_neighbor_distance')
TRAIN_LOOKUP=train.set_index('state_id')[['current_article_id','target_article_id']]
TEST_LOOKUP=test.set_index('state_id')[['current_article_id','target_article_id']]
def pair_embedding_features(qids,candidates,lookup):
    frame=pd.DataFrame({'state_id':qids.astype(int),'candidate':candidates.astype(int)}).join(lookup,on='state_id')
    candidate=embedding_pca[frame.candidate.to_numpy(int)]; target=embedding_pca[frame.target_article_id.to_numpy(int)]; current=embedding_pca[frame.current_article_id.to_numpy(int)]
    product=candidate*target; absolute=np.abs(candidate-target); direction=candidate-current; target_direction=target-current
    scalar=np.column_stack([np.sum(candidate*target,axis=1),np.sum(candidate*current,axis=1),np.sum(current*target,axis=1),np.sum(direction*target_direction,axis=1),np.linalg.norm(target_direction,axis=1)-np.linalg.norm(target-candidate,axis=1)]).astype(np.float32)
    return np.column_stack([product,absolute,candidate,target,scalar]).astype(np.float32)
def query_rank(values,qids):
    return pd.DataFrame({'value':values,'qid':qids}).groupby('qid').value.rank(pct=True,method='average').to_numpy(np.float32)
PARAMS=[
 {'num_leaves':7,'min_child_samples':30,'reg_lambda':8.0},
 {'num_leaves':15,'min_child_samples':30,'reg_lambda':10.0},
 {'num_leaves':15,'min_child_samples':60,'reg_lambda':15.0},
 {'num_leaves':31,'min_child_samples':50,'reg_lambda':20.0},
]
BETAS=[0.0,.05,.1,.2,.3,.5,.8,1.2,2.0]
LOCKED_CONFIG=3; LOCKED_BETA=.20
    '''),
    md("## 11. Grouped OOF training dan blend search\n\nMiniLM is frozen. Only lightweight LightGBM classifiers are trained on CPU."),
    code(r'''
import lightgbm as lgb
predictions=[]; fold_models=[]
for cache in fold_cache:
    fold=cache['fold']; x_fit,y_fit,q_fit,c_fit=cache['fit']; x_val,y_val,q_val,c_val=cache['val']
    fit_min=x_fit[:,MIN_INDEX]==1; valid_queries=np.unique(q_fit[fit_min&(y_fit==1)]); fit_mask=fit_min&np.isin(q_fit,valid_queries)
    fit_path=path_feature_for_pairs(q_fit,c_fit); val_path=path_feature_for_pairs(q_val,c_val)
    x_train=np.column_stack([x_fit[fit_mask][:,TABULAR_INDEX],fit_path[fit_mask],pair_embedding_features(q_fit[fit_mask],c_fit[fit_mask],TRAIN_LOOKUP)])
    x_valid=np.column_stack([x_val[:,TABULAR_INDEX],val_path,pair_embedding_features(q_val,c_val,TRAIN_LOOKUP)])
    y_train=y_fit[fit_mask]; q_train=q_fit[fit_mask]; sizes=pd.Series(q_train).value_counts().to_dict()
    weights=np.asarray([.5 if label==1 else .5/max(1,sizes[int(qid)]-1) for label,qid in zip(y_train,q_train)],np.float32)
    anchor=x_val[:,[FEATURES.index(name) for name in V3_FEATURES]]@V3_WEIGHTS+.20*val_path
    for config_id,params in enumerate(PARAMS):
        model=lgb.LGBMClassifier(objective='binary',n_estimators=300,learning_rate=.025,colsample_bytree=.75,subsample=.9,random_state=SEED+fold,verbosity=-1,n_jobs=-1,**params)
        model.fit(x_train,y_train,sample_weight=weights)
        probability=model.predict_proba(x_valid)[:,1].astype(np.float32)
        predictions.append({'fold':fold,'config_id':config_id,'y':y_val,'q':q_val,'c':c_val,'x':x_val,'anchor':anchor,'probability':probability,'rank':query_rank(probability,q_val)})
        if config_id==LOCKED_CONFIG: fold_models.append(model)
    print(f'Fold {fold}: train={len(x_train):,} minimum-distance pairs | validation={len(x_valid):,} all pairs')
search_rows=[]
for item in predictions:
    for signal in ['probability','rank']:
        for beta in BETAS:
            search_rows.append({'fold':item['fold'],'config_id':item['config_id'],'signal':signal,'beta':beta,**evaluate_scores(item['y'],item['q'],item['c'],item['anchor']+beta*item[signal])})
search=pd.DataFrame(search_rows)
summary=search.groupby(['config_id','signal','beta'],as_index=False).agg(mean_accuracy=('accuracy','mean'),std_accuracy=('accuracy','std'),top3=('top3','mean'),top5=('top5','mean')).sort_values(['mean_accuracy','std_accuracy'],ascending=[False,True])
display(summary.head(15))
    '''),
    md("## 12. Nested stability dan V4 comparison"),
    code(r'''
nested_rows=[]
for held_fold in range(N_SPLITS):
    selection=search[search.fold.ne(held_fold)].groupby(['config_id','signal','beta']).accuracy.mean().sort_values(ascending=False)
    config_id,signal,beta=selection.index[0]
    held=search[(search.fold.eq(held_fold))&(search.config_id.eq(config_id))&(search.signal.eq(signal))&(search.beta.eq(beta))].iloc[0]
    nested_rows.append({'held_fold':held_fold,'config_id':int(config_id),'signal':signal,'beta':float(beta),'selection_accuracy':selection.iloc[0],'held_accuracy':held.accuracy})
nested=pd.DataFrame(nested_rows)
comparison_rows=[]; oof_v5=[]; change_rows=[]
for item in [x for x in predictions if x['config_id']==LOCKED_CONFIG]:
    v4=item['anchor']; v5=v4+LOCKED_BETA*item['probability']
    comparison_rows += [{'fold':item['fold'],'model':'V4 anchor',**evaluate_scores(item['y'],item['q'],item['c'],v4)},{'fold':item['fold'],'model':'V5 semantic pair blend',**evaluate_scores(item['y'],item['q'],item['c'],v5)}]
    v4_w=winner_table(item['y'],item['q'],item['c'],v4).rename(columns={'prediction':'v4_prediction','correct':'v4_correct','score':'v4_score'})
    v5_w=winner_table(item['y'],item['q'],item['c'],v5).rename(columns={'prediction':'v5_prediction','correct':'v5_correct','score':'v5_score'})
    merged=v4_w.merge(v5_w,on='state_id'); merged['fold']=item['fold']; oof_v5.append(merged)
selected_cv=pd.DataFrame(comparison_rows)
display(selected_cv.pivot(index='model',columns='fold',values='accuracy')); display(selected_cv.groupby('model').mean(numeric_only=True)); display(nested)
fig,ax=plt.subplots(1,2,figsize=(14,4)); sns.barplot(data=selected_cv,x='fold',y='accuracy',hue='model',ax=ax[0]); ax[0].set_ylim(.70,.82); ax[0].set_title('Fold-by-fold grouped OOF')
beta_curve=search[search.config_id.eq(LOCKED_CONFIG)&search.signal.eq('probability')].groupby('beta').accuracy.mean().reset_index(); sns.lineplot(data=beta_curve,x='beta',y='accuracy',marker='o',ax=ax[1]); ax[1].axvline(LOCKED_BETA,color='#e45756',ls='--'); ax[1].set_title('V5 blend sensitivity'); plt.tight_layout(); plt.show()
print(f'Nested mean: {nested.held_accuracy.mean():.4%}')
    '''),
    md("## 13. Error-level reverse engineering\n\nChanged predictions, fixes, regressions, and remaining taxonomy are persisted for V6."),
    code(r'''
oof=pd.concat(oof_v5,ignore_index=True).merge(train[['state_id','current_article_id','target_article_id','next_article_id']],on='state_id',how='left')
oof['changed']=oof.v4_prediction.ne(oof.v5_prediction); oof['fixed']=oof.changed&~oof.v4_correct&oof.v5_correct; oof['regressed']=oof.changed&oof.v4_correct&~oof.v5_correct
change_summary=pd.Series({'changed':oof.changed.sum(),'fixed':oof.fixed.sum(),'regressed':oof.regressed.sum(),'both_wrong':(oof.changed&~oof.v4_correct&~oof.v5_correct).sum(),'net_correct':oof.v5_correct.sum()-oof.v4_correct.sum()})
display(change_summary.to_frame('states'))
fig,ax=plt.subplots(figsize=(8,4)); change_summary[['fixed','regressed','both_wrong']].plot.bar(ax=ax,color=['#54a24b','#e45756','#bab0ac']); ax.set_title('V5 changes versus V4'); plt.tight_layout(); plt.show()
print('INSIGHT ERROR: only a small semantic correction is trusted; shortest-path anchor remains dominant.')
    '''),
    md("## 14. Train full model dan test inference"),
    code(r'''
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
v5_winners=winner_table(np.zeros(len(q_test),np.int8),q_test,c_test,v5_test); v4_winners=winner_table(np.zeros(len(q_test),np.int8),q_test,c_test,v4_test)
v5_prediction=v5_winners.set_index('state_id').prediction.astype(int); v4_prediction=v4_winners.set_index('state_id').prediction.astype(int)
primary=sample[['state_id']].copy(); primary['predicted_next_article_id']=primary.state_id.map(v5_prediction).astype(int)
fallback=sample[['state_id']].copy(); fallback['predicted_next_article_id']=fallback.state_id.map(v4_prediction).astype(int)
print('V5 vs V4 test disagreement:',(primary.predicted_next_article_id!=fallback.predicted_next_article_id).mean()); display(primary.head())
    '''),
    md("## 15. Audit, submission, dan reusable artifacts"),
    code(r'''
valid_ids=set(articles.article_id.astype(int))
def audit_submission(frame):
    return {'rows':len(frame),'unique_states':frame.state_id.nunique(),'nan':int(frame.predicted_next_article_id.isna().sum()),'invalid_article_ids':int((~frame.predicted_next_article_id.isin(valid_ids)).sum()),'same_as_current':float((frame.predicted_next_article_id.to_numpy()==test.current_article_id.to_numpy()).mean()),'same_as_target':float((frame.predicted_next_article_id.to_numpy()==test.target_article_id.to_numpy()).mean()),'unique_predictions':frame.predicted_next_article_id.nunique()}
primary_audit=audit_submission(primary); fallback_audit=audit_submission(fallback)
assert primary_audit['rows']==6000 and primary_audit['unique_states']==6000 and primary_audit['nan']==0 and primary_audit['invalid_article_ids']==0
primary_path=OUTPUT_DIR/'datathon_task2_v5_semantic_pair_blend.csv'; fallback_path=OUTPUT_DIR/'datathon_task2_v5_v4_fallback.csv'
primary.to_csv(primary_path,index=False); fallback.to_csv(fallback_path,index=False)
selected_cv.to_csv(OUTPUT_DIR/'datathon_task2_v5_cv.csv',index=False); search.to_csv(OUTPUT_DIR/'datathon_task2_v5_blend_search.csv',index=False); nested.to_csv(OUTPUT_DIR/'datathon_task2_v5_nested.csv',index=False); oof.to_csv(OUTPUT_DIR/'datathon_task2_v5_oof_error_pack.csv',index=False)
joblib.dump({'model':final_model,'pca':pca,'tabular':TABULAR,'params':PARAMS[LOCKED_CONFIG],'beta':LOCKED_BETA},OUTPUT_DIR/'datathon_task2_v5_semantic_pair_ranker.joblib')
diagnostics={'version':'v5_pretrained_semantic_pair_ranker','seed':SEED,'embedding_path':str(EMBEDDING_PATH),'locked_config':LOCKED_CONFIG,'locked_beta':LOCKED_BETA,'runtime_minutes':(time.time()-START_TIME)/60,'selected_cv':selected_cv.groupby('model').mean(numeric_only=True).to_dict('index'),'nested_accuracy':nested.held_accuracy.mean(),'changes':change_summary.to_dict(),'primary_audit':primary_audit,'fallback_audit':fallback_audit,'test_disagreement':float((primary.predicted_next_article_id!=fallback.predicted_next_article_id).mean())}
(OUTPUT_DIR/'datathon_task2_v5_diagnostics.json').write_text(json.dumps(diagnostics,indent=2))
archive=shutil.make_archive(str(OUTPUT_DIR.parent/'datathon_task2_v5_artifacts'),'zip',OUTPUT_DIR)
display(pd.DataFrame({'primary_v5':primary_audit,'fallback_v4':fallback_audit})); print('Primary:',primary_path); print('Bundle:',archive); print(f'Total runtime: {(time.time()-START_TIME)/60:.2f} minutes')
    '''),
    md("""
## Keputusan setelah run

- Primary V5: `datathon_task2_v5_semantic_pair_blend.csv` bila grouped dan nested OOF melampaui V4.
- V4 fallback tetap diekspor karena expected gain V5 kecil.
- Upload `datathon_task2_v5_artifacts.zip` sebagai Kaggle Dataset untuk reuse embedding tanpa download/model inference.
- External Wikispeedia navigation ground truth tidak digunakan oleh notebook atau submission.
    """),
]

for cell in cells:
    if cell.cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []

metadata = source.metadata.copy()
metadata["kernelspec"] = {"display_name": "Dataton (.venv)", "language": "python", "name": "python3"}
notebook = nbf.v4.new_notebook(cells=cells, metadata=metadata)
nbf.write(notebook, OUT)
print(OUT)
