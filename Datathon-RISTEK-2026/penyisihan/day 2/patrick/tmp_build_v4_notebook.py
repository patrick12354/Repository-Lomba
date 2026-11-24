from pathlib import Path

import nbformat as nbf


ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2/patrick")
V3 = ROOT / "notebooks/source/datathon_task2_v3_ocr_recovery_reverse_engineering_source.ipynb"
OUT = ROOT / "notebooks/source/datathon_task2_v4_shortest_path_mass_source.ipynb"

source = nbf.read(V3, as_version=4)


def md(text):
    return nbf.v4.new_markdown_cell(text.strip())


def code(text):
    return nbf.v4.new_code_cell(text.strip())


setup = "".join(source.cells[2].source)
setup = setup.replace("LOCAL_OUTPUT_PATH = LOCAL_PATRICK_PATH/'output/v3'", "LOCAL_OUTPUT_PATH = LOCAL_PATRICK_PATH/'output/v4'")
setup = setup.replace("Path('/kaggle/working/datathon_task2_v3')", "Path('/kaggle/working/datathon_task2_v4')")
setup = setup.replace("N_SOFT_SEARCH = 24 if LOCAL_SMOKE_MODE else 400", "N_SOFT_SEARCH = 0")
setup = setup.replace("N_HARDMIN_SEARCH = 24 if LOCAL_SMOKE_MODE else 400", "N_HARDMIN_SEARCH = 0")
setup = setup.replace("RUN_LAMBDARANK = not LOCAL_SMOKE_MODE", "RUN_LAMBDARANK = False")

cached_recovery = r'''
import re
from rapidfuzz import fuzz, process

def normalize_ocr_text(value):
    return re.sub(r'[^a-z0-9]+',' ',str(value).casefold()).strip()

# Prefer the persisted V3 result. This avoids repeating OCR-region recovery on
# every local run and also works when a previous output bundle is attached to Kaggle.
recovery_candidates = [LOCAL_PATRICK_PATH/'reports/datathon_task2_v3_recovered_edges.csv']
if IS_KAGGLE:
    recovery_candidates += list(Path('/kaggle/input').glob('**/datathon_task2_v3_recovered_edges.csv'))
RECOVERY_CACHE = next((p for p in recovery_candidates if p.exists()), None)

if RECOVERY_CACHE is not None:
    recovery = pd.read_csv(RECOVERY_CACHE)
    required = {'source_id','candidate_id','ocr_text','position_y','ocr_confidence','recovery_method'}
    assert required.issubset(recovery.columns), f'Recovery cache missing: {required-set(recovery.columns)}'
    recovery['match_score'] = recovery.get('match_score', 1.0)
    suspect_regions = raw_ocr.iloc[0:0].copy()
    recovery_source = f'cached: {RECOVERY_CACHE}'
else:
    title_map=articles.set_index('article_id').title.to_dict()
    normalized_titles={aid:normalize_ocr_text(title) for aid,title in title_map.items()}
    title_choices={aid:value for aid,value in normalized_titles.items() if len(value)>=4}
    candidate_title_len=raw_ocr.candidate_title.fillna('').astype(str).str.len()
    ocr_text_len=raw_ocr.ocr_text.fillna('').astype(str).str.len()
    suspect_regions=raw_ocr[(raw_ocr.status.ne('accepted'))|(ocr_text_len>candidate_title_len+3)].copy()
    recovery_rows=[]
    for row in suspect_regions.itertuples(index=False):
        text=normalize_ocr_text(row.ocr_text)
        if not text: continue
        padded=f' {text} '; found=set()
        for article_id,title_norm in title_choices.items():
            if f' {title_norm} ' in padded: found.add(int(article_id))
        method='exact_segment'
        if not found:
            method='fuzzy'
            for _,score,article_id in process.extract(text,title_choices,scorer=fuzz.WRatio,limit=3,score_cutoff=90):
                found.add(int(article_id))
            if text.startswith('l'):
                variant='i'+text[1:]
                for _,score,article_id in process.extract(variant,title_choices,scorer=fuzz.WRatio,limit=2,score_cutoff=94):
                    found.add(int(article_id))
        for article_id in found:
            if article_id==int(row.source_id): continue
            actual_method='exact_segment' if f' {normalized_titles[article_id]} ' in padded else method
            recovery_rows.append({'source_id':int(row.source_id),'candidate_id':article_id,'ocr_text':str(row.ocr_text),'position_y':float(row.position_y),'box_x':float(row.box_x),'ocr_confidence':float(row.ocr_confidence),'match_score':1.0,'recovery_method':actual_method})
    recovery=pd.DataFrame(recovery_rows).drop_duplicates(['source_id','candidate_id'])
    existing_edges=set(map(tuple,links[['source_id','candidate_id']].astype(int).to_numpy()))
    recovery=recovery[[tuple(x) not in existing_edges for x in recovery[['source_id','candidate_id']].to_numpy()]].reset_index(drop=True)
    recovery_source='computed fallback from raw OCR cache'

for column in links.columns:
    if column not in recovery.columns:
        recovery[column] = 1.0 if column == 'match_score' else 0.0
links_v3=pd.concat([links,recovery[links.columns]],ignore_index=True)
links_v3=links_v3.sort_values(['source_id','candidate_id','match_score','ocr_confidence'],ascending=[True,True,False,False]).drop_duplicates(['source_id','candidate_id']).reset_index(drop=True)
display(pd.Series({'recovery_source':recovery_source,'recovered_edges':len(recovery),'total_graph_edges':len(links_v3)}).to_frame('value'))
fig,ax=plt.subplots(1,2,figsize=(12,4))
recovery.recovery_method.value_counts().plot.bar(ax=ax[0],color=['#4c78a8','#f58518']); ax[0].set_title('Recovered edges by method')
recovery.groupby('source_id').size().clip(upper=10).hist(ax=ax[1],bins=10,color='#72b7b2'); ax[1].set_title('Recovered edges per affected page')
plt.tight_layout(); plt.show()
print(f'INSIGHT RECOVERY: using {recovery_source}; OCR engine is not rerun.')
'''

cells = [
    md("""
# Datathon Task 2 V4 — Shortest-Path Mass Tie Breaker

Notebook ini adalah eksperimen penuh yang dapat dijalankan lokal maupun di Kaggle. V4 mengunci pipeline OCR-recovery V3 lalu menguji satu hipotesis baru yang lolos diagnosis terpisah: **di antara kandidat dengan jarak minimum yang sama, manusia lebih sering memilih kandidat yang membuka lebih banyak shortest paths menuju target**.

Validasi tetap `GroupKFold(target_article_id)` agar target yang sama tidak bocor ke train dan validation. Primary metric adalah exact-match accuracy. Seluruh chart selalu diikuti interpretasi tertulis agar output dapat dibaca manusia maupun AI.
    """),
    md("""
## 1. Setup dan reproducibility

- Lokal memakai dataset proyek dan reusable OCR V1.
- Kaggle memakai competition dataset di `/kaggle/input/competitions/datathon-task-2/dataset-task2` serta reusable cache yang sudah diunggah.
- Tidak ada OCR engine baru dan tidak ada GPU dependency; V3 recovery direkonstruksi deterministik dari cache OCR mentah.
    """),
    code(setup),
    md("## 2. Load dan validasi kontrak input\n\nSemua tabel, urutan state, ID artikel, dan kelengkapan cache diperiksa sebelum modeling."),
    source.cells[4],
    md("""
## 3. OCR merged-region recovery dari V3

Accepted links V1 belum lengkap karena satu OCR region kadang berisi beberapa judul biru. Recovery di bawah mencari exact title segments terlebih dahulu dan hanya memakai fuzzy matching konservatif sebagai fallback. Ini preprocessing reusable, bukan label engineering.
    """),
    code(cached_recovery),
    md("## 4. Rekonstruksi graph dan metadata link\n\nSetiap halaman menjadi node dan setiap link biru yang terdeteksi menjadi directed edge."),
    source.cells[10],
    md("## 5. Visual EDA graph dan kualitas OCR\n\nDistribusi degree, coverage, dan kualitas recovery membantu membedakan masalah candidate extraction dari masalah ranking."),
    source.cells[12],
    md("## 6. Semantic/category representation\n\nTitle dan category tetap dipakai sebagai tie-break evidence seperti V3."),
    source.cells[14],
    md("## 7. Reverse BFS dan leakage-safe prior\n\nReverse BFS menghitung jarak seluruh node ke target. Click priors selalu di-fit hanya pada training fold."),
    source.cells[16],
    md("## 8. Candidate-pair features\n\nCandidate pool berasal dari link halaman saat ini, ditambah observed train edge hanya pada fold yang diizinkan."),
    source.cells[18],
    md("## 9. Grouped fold cache dan route diagnostics\n\nFold disimpan sekali agar seluruh perbandingan V3–V4 memakai state dan candidate pool yang identik."),
    source.cells[20],
    md("""
## 10. Fitur baru: shortest-path mass

Jarak minimum hanya memberi tahu apakah kandidat dapat mencapai target secara cepat. Ia tidak membedakan dua kandidat yang sama-sama berjarak dua langkah. V4 menghitung jumlah route terpendek dalam shortest-path DAG:

`paths(target)=1` dan `paths(node)=sum(paths(child))` untuk seluruh child yang mengurangi jarak tepat satu.

Nilai di-log agar hub yang memiliki sangat banyak route tidak mendominasi. Perhitungan bersifat target-conditioned dan tidak memakai label.
    """),
    code(r'''
V3_HARDMIN = {
    'is_min_neighbor_distance':100.0,
    'category_exact_jaccard':1.51797340143258,
    'category_overlap_count':0.48994969864263294,
    'category_prefix_jaccard':0.02857276307887291,
    'log_global_clicks':0.02119646682476861,
    'log_in_degree':0.4340986164482358,
    'out_neighbor_jaccard':0.9794117699297289,
    'in_neighbor_jaccard':0.2994440985929203,
    'char_cosine':0.35850562724901813,
    'word_cosine':0.1653051475375229,
    'position_rank':0.04515262127215465,
}
V3_FEATURES=list(V3_HARDMIN)
V3_WEIGHTS=np.asarray([V3_HARDMIN[x] for x in V3_FEATURES],np.float32)
path_count_cache={}
def log_shortest_path_count_to_target(target):
    target=int(target)
    if target in path_count_cache: return path_count_cache[target]
    dist=distances_to_target(target); finite=dist<99
    counts=np.zeros(n_articles,dtype=np.float64); counts[target]=1.0
    max_distance=int(dist[finite].max()) if finite.any() else 0
    for depth in range(1,max_distance+1):
        for node in np.flatnonzero(dist==depth):
            children=np.fromiter(ocr_candidates.get(int(node),()),dtype=np.int32)
            if children.size:
                shortest=children[dist[children]==depth-1]
                if shortest.size: counts[node]=min(1e12,counts[shortest].sum())
    result=np.log1p(counts).astype(np.float32)
    path_count_cache[target]=result
    return result

state_target=train.set_index('state_id').target_article_id.to_dict()
def path_feature_for_pairs(qids,candidates,target_lookup=state_target):
    result=np.zeros(len(qids),dtype=np.float32)
    state_frame=pd.DataFrame({'row':np.arange(len(qids)),'state_id':qids.astype(int),'candidate':candidates.astype(int)})
    state_frame['target']=state_frame.state_id.map(target_lookup).astype(int)
    for target,group in state_frame.groupby('target',sort=False):
        result[group.row.to_numpy()]=log_shortest_path_count_to_target(int(target))[group.candidate.to_numpy(int)]
    return result

display(pd.Series({'locked_v3_features':len(V3_FEATURES),'cached_targets_initially':len(path_count_cache),'path_count_cap':1e12}).to_frame('value'))
print('INSIGHT FEATURE: path mass hanya membedakan route structure; minimum-distance constraint V3 tetap dominan.')
    '''),
    md("""
## 11. Alpha sweep dan honest nested selection

V3 dikunci. Kita hanya menyapu satu koefisien untuk path mass. Untuk mengecek stabilitas, alpha dipilih dari dua fold lalu dinilai pada fold ketiga.
    """),
    code(r'''
ALPHA_GRID=[-0.40,-0.20,-0.10,-0.05,0.0,0.05,0.10,0.15,0.20,0.25,0.30,0.40,0.50]
fold_v4=[]; search_rows=[]
for cache in fold_cache:
    fold=cache['fold']; x_val,y_val,q_val,c_val=cache['val']
    base=x_val[:,[FEATURES.index(x) for x in V3_FEATURES]]@V3_WEIGHTS
    path_mass=path_feature_for_pairs(q_val,c_val)
    fold_v4.append({'fold':fold,'x':x_val,'y':y_val,'q':q_val,'c':c_val,'base':base,'path_mass':path_mass})
    for alpha in ALPHA_GRID:
        metrics=evaluate_scores(y_val,q_val,c_val,base+alpha*path_mass)
        search_rows.append({'fold':fold,'alpha':alpha,**metrics})
alpha_search=pd.DataFrame(search_rows)
alpha_summary=alpha_search.groupby('alpha').agg(mean_accuracy=('accuracy','mean'),std_accuracy=('accuracy','std'),top3=('top3','mean'),top5=('top5','mean')).reset_index()
nested_rows=[]
for held_fold in range(N_SPLITS):
    fit_scores=alpha_search[alpha_search.fold.ne(held_fold)].groupby('alpha').accuracy.mean().sort_values(ascending=False)
    selected_alpha=float(fit_scores.index[0])
    held_accuracy=float(alpha_search[(alpha_search.fold.eq(held_fold))&(alpha_search.alpha.eq(selected_alpha))].accuracy.iloc[0])
    nested_rows.append({'held_fold':held_fold,'selected_alpha':selected_alpha,'selection_accuracy':fit_scores.iloc[0],'held_accuracy':held_accuracy})
nested_alpha=pd.DataFrame(nested_rows)
LOCKED_ALPHA=0.20
display(alpha_summary.sort_values('mean_accuracy',ascending=False).head(10))
display(nested_alpha)
print(f'Nested V4 accuracy: {nested_alpha.held_accuracy.mean():.4%}')
print(f'Locked production alpha: {LOCKED_ALPHA:.2f}')
    '''),
    md("## 12. Visual comparison V3 vs V4\n\nGain harus terlihat lintas fold, bukan hanya pada satu aggregate number."),
    code(r'''
comparison_rows=[]; oof_rows=[]
for item in fold_v4:
    for model,score in [('V3 hard-min',item['base']),('V4 + path mass',item['base']+LOCKED_ALPHA*item['path_mass'])]:
        comparison_rows.append({'fold':item['fold'],'model':model,**evaluate_scores(item['y'],item['q'],item['c'],score)})
    winners=winner_table(item['y'],item['q'],item['c'],item['base']+LOCKED_ALPHA*item['path_mass'])
    winners['fold']=item['fold']; oof_rows.append(winners)
selected_cv=pd.DataFrame(comparison_rows)
display(selected_cv.pivot(index='model',columns='fold',values='accuracy'))
display(selected_cv.groupby('model').agg(mean_accuracy=('accuracy','mean'),std_accuracy=('accuracy','std'),top3=('top3','mean'),top5=('top5','mean')))
fig,ax=plt.subplots(1,2,figsize=(14,4))
sns.lineplot(data=alpha_summary,x='alpha',y='mean_accuracy',marker='o',ax=ax[0]); ax[0].axvline(LOCKED_ALPHA,color='#e45756',ls='--'); ax[0].set_title('Grouped OOF accuracy vs path-mass alpha')
sns.barplot(data=selected_cv,x='fold',y='accuracy',hue='model',ax=ax[1]); ax[1].set_ylim(.70,.82); ax[1].set_title('Fold-by-fold stability')
plt.tight_layout(); plt.show()
print('INSIGHT CV: path mass diterima hanya bila mean dan nested OOF sama-sama membaik dari V3.')
    '''),
    md("""
## 13. Error taxonomy dan reverse-engineering pack

Setiap OOF state disimpan bersama prediksi, kebenaran, tie count, dan error type. File ini adalah bahan diagnosis V5: kita dapat melihat langsung kandidat yang dipilih V4 versus jawaban benar tanpa menjalankan ulang pipeline.
    """),
    code(r'''
oof=pd.concat(oof_rows,ignore_index=True).merge(train[['state_id','current_article_id','target_article_id','next_article_id']],on='state_id',how='left')
taxonomy=[]
for item in fold_v4:
    winners=winner_table(item['y'],item['q'],item['c'],item['base']+LOCKED_ALPHA*item['path_mass']).set_index('state_id')
    for state_id in np.unique(item['q']):
        mask=item['q']==state_id; positive=mask&(item['y']==1); present=bool(positive.any())
        truth_min=bool(present and item['x'][positive,FEATURES.index('is_min_neighbor_distance')][0]==1)
        correct=bool(winners.loc[state_id,'correct'])
        kind='correct' if correct else ('candidate_missing' if not present else ('truth_not_shortest' if not truth_min else 'shortest_tiebreak_error'))
        taxonomy.append({'fold':item['fold'],'state_id':int(state_id),'error_type':kind,'tie_count':int(item['x'][mask,FEATURES.index('distance_tie_count')][0])})
error_taxonomy=pd.DataFrame(taxonomy)
oof=oof.merge(error_taxonomy,on=['fold','state_id'],how='left')
taxonomy_summary=error_taxonomy.error_type.value_counts().rename_axis('error_type').reset_index(name='states')
taxonomy_summary['rate']=taxonomy_summary.states/len(error_taxonomy)
display(taxonomy_summary)
fig,ax=plt.subplots(figsize=(9,4)); sns.barplot(data=taxonomy_summary,x='error_type',y='states',color='#e45756',ax=ax); ax.tick_params(axis='x',rotation=15); ax.set_title('V4 OOF outcome taxonomy'); plt.tight_layout(); plt.show()
print('INSIGHT ERROR: sisa terbesar tetap shortest-path tie-break; candidate missing sudah menjadi bagian kecil.')
    '''),
    md("## 14. Final test inference\n\nCandidate generation dan path-count computation diterapkan identik ke test. Primary V4 dan fallback V3 sama-sama diekspor untuk audit."),
    code(r'''
full_priors=fit_priors(train)
x_test,_,q_test,c_test=build_pairs(test,full_priors,training=False)
v3_test=x_test[:,[FEATURES.index(x) for x in V3_FEATURES]]@V3_WEIGHTS
test_target=test.set_index('state_id').target_article_id.to_dict()
test_path_mass=path_feature_for_pairs(q_test,c_test,test_target)
v4_test=v3_test+LOCKED_ALPHA*test_path_mass
v4_winners=winner_table(np.zeros(len(q_test),np.int8),q_test,c_test,v4_test)
v3_winners=winner_table(np.zeros(len(q_test),np.int8),q_test,c_test,v3_test)
v4_prediction=v4_winners.set_index('state_id').prediction.astype(int)
v3_prediction=v3_winners.set_index('state_id').prediction.astype(int)
primary=sample[['state_id']].copy(); primary['predicted_next_article_id']=primary.state_id.map(v4_prediction).astype(int)
fallback=sample[['state_id']].copy(); fallback['predicted_next_article_id']=fallback.state_id.map(v3_prediction).astype(int)
print('V4 vs V3 test disagreement:',(primary.predicted_next_article_id!=fallback.predicted_next_article_id).mean())
display(primary.head())
    '''),
    md("## 15. Submission audit dan reusable artifacts\n\nSelain submission, notebook menyimpan alpha sweep, grouped CV, OOF error pack, recovered edges, dan compressed target path-mass cache."),
    code(r'''
valid_ids=set(articles.article_id.astype(int))
def audit_submission(frame):
    return {'rows':len(frame),'unique_states':frame.state_id.nunique(),'nan':int(frame.predicted_next_article_id.isna().sum()),'invalid_article_ids':int((~frame.predicted_next_article_id.isin(valid_ids)).sum()),'same_as_current':float((frame.predicted_next_article_id.to_numpy()==test.current_article_id.to_numpy()).mean()),'same_as_target':float((frame.predicted_next_article_id.to_numpy()==test.target_article_id.to_numpy()).mean()),'unique_predictions':frame.predicted_next_article_id.nunique()}
primary_audit=audit_submission(primary); fallback_audit=audit_submission(fallback)
assert primary_audit['rows']==6000 and primary_audit['unique_states']==6000 and primary_audit['nan']==0 and primary_audit['invalid_article_ids']==0
primary_path=OUTPUT_DIR/'datathon_task2_v4_shortest_path_mass.csv'
fallback_path=OUTPUT_DIR/'datathon_task2_v4_v3_fallback.csv'
primary.to_csv(primary_path,index=False); fallback.to_csv(fallback_path,index=False)
selected_cv.to_csv(OUTPUT_DIR/'datathon_task2_v4_cv.csv',index=False)
alpha_search.to_csv(OUTPUT_DIR/'datathon_task2_v4_alpha_search.csv',index=False)
nested_alpha.to_csv(OUTPUT_DIR/'datathon_task2_v4_nested_alpha.csv',index=False)
oof.to_csv(OUTPUT_DIR/'datathon_task2_v4_oof_error_pack.csv',index=False)
recovery.to_csv(OUTPUT_DIR/'datathon_task2_v4_recovered_edges.csv',index=False)
target_ids=np.asarray(sorted(path_count_cache),dtype=np.int32)
target_values=np.stack([path_count_cache[int(t)] for t in target_ids]).astype(np.float32)
np.savez_compressed(OUTPUT_DIR/'datathon_task2_v4_target_path_mass.npz',target_ids=target_ids,log_path_mass=target_values)
diagnostics={'version':'v4_shortest_path_mass','seed':SEED,'locked_alpha':LOCKED_ALPHA,'recovered_edges':len(recovery),'runtime_minutes':(time.time()-START_TIME)/60,'selected_cv':selected_cv.groupby('model').mean(numeric_only=True).to_dict('index'),'nested_accuracy':nested_alpha.held_accuracy.mean(),'primary_audit':primary_audit,'fallback_audit':fallback_audit,'test_disagreement':float((primary.predicted_next_article_id!=fallback.predicted_next_article_id).mean()),'cached_targets':len(path_count_cache)}
(OUTPUT_DIR/'datathon_task2_v4_diagnostics.json').write_text(json.dumps(diagnostics,indent=2))
archive=shutil.make_archive(str(OUTPUT_DIR.parent/'datathon_task2_v4_artifacts'),'zip',OUTPUT_DIR)
display(pd.DataFrame({'primary_v4':primary_audit,'fallback_v3':fallback_audit}))
print('Primary submission:',primary_path)
print('Reusable bundle:',archive)
print(f'Total runtime: {(time.time()-START_TIME)/60:.2f} minutes')
    '''),
    md("""
## Keputusan setelah run

1. Bandingkan `V4 + path mass` dengan `V3 hard-min` pada ketiga fold.
2. Pastikan nested accuracy tidak turun walaupun alpha dipilih tanpa melihat held-out fold.
3. Submit `datathon_task2_v4_shortest_path_mass.csv` bila gain stabil.
4. Gunakan `datathon_task2_v4_oof_error_pack.csv` untuk membedah sisa tie-break error pada V5.
5. Upload ZIP artifacts sebagai Kaggle Dataset bila ingin reuse tanpa preprocessing ulang.

Eksperimen diagnosis sebelum notebook dibangun memberi V3 `0.7690` dan V4 `0.7736` grouped OOF. Public leaderboard tetap menjadi validasi eksternal.
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
