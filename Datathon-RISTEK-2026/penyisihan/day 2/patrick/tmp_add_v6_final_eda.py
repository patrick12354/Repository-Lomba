from pathlib import Path
import nbformat


ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2/patrick")
SOURCE = ROOT / "notebooks/source/datathon_task2_v6_discounted_reachability_source.ipynb"
nb = nbformat.read(SOURCE, as_version=4)

# Make room for two new early EDA sections.
for cell in nb.cells:
    if cell.cell_type != "markdown":
        continue
    for section in range(17, 2, -1):
        cell.source = cell.source.replace(f"## {section}.", f"## {section + 2}.")

state_md = nbformat.v4.new_markdown_cell("""## 3. Exploratory Data Analysis State dan Label

EDA pertama memeriksa bagaimana state dibentuk, seberapa sering artikel muncul sebagai current page, konsentrasi label next click, serta pembagian target train dan test.

Empat visual berikut menjawab pertanyaan penting sebelum modeling:

1. Apakah ukuran train dan test seimbang?
2. Apakah beberapa current article jauh lebih sering muncul?
3. Seberapa berat long tail pada label `next_article_id`?
4. Apakah jumlah state per target konsisten dan apakah target train terpisah dari test?""")

state_code = nbformat.v4.new_code_cell(r'''
train_current_freq=train.current_article_id.value_counts()
next_freq=train.next_article_id.value_counts()
train_target_size=train.groupby('target_article_id').size()
test_target_size=test.groupby('target_article_id').size()
target_overlap=len(set(train.target_article_id)&set(test.target_article_id))

fig,ax=plt.subplots(2,2,figsize=(15,10))
pd.Series({'Train states':len(train),'Test states':len(test)}).plot.bar(
    ax=ax[0,0],color=['#4c78a8','#f58518'],rot=0
)
ax[0,0].set_title('Jumlah state train dan test'); ax[0,0].set_ylabel('State')

sns.histplot(train_current_freq.clip(upper=20),bins=20,discrete=True,ax=ax[0,1],color='#72b7b2')
ax[0,1].set_title('Frekuensi current article pada train (20=20+)')
ax[0,1].set_xlabel('Jumlah kemunculan'); ax[0,1].set_ylabel('Artikel')

rank=np.arange(1,len(next_freq)+1)
ax[1,0].plot(rank,next_freq.to_numpy(),color='#e45756',lw=2)
ax[1,0].set_xscale('log'); ax[1,0].set_yscale('log')
ax[1,0].set_title('Long tail label next click'); ax[1,0].set_xlabel('Rank artikel'); ax[1,0].set_ylabel('Frekuensi label')

target_size_frame=pd.DataFrame({
    'states':pd.concat([train_target_size,test_target_size]).to_numpy(),
    'split':['Train']*len(train_target_size)+['Test']*len(test_target_size),
})
sns.histplot(data=target_size_frame,x='states',hue='split',multiple='dodge',discrete=True,ax=ax[1,1])
ax[1,1].set_title('Jumlah state per target'); ax[1,1].set_xlabel('State dalam satu target group')
plt.tight_layout(); plt.show()

state_eda=pd.Series({
    'unique_train_targets':train.target_article_id.nunique(),
    'unique_test_targets':test.target_article_id.nunique(),
    'target_overlap':target_overlap,
    'unique_train_currents':train.current_article_id.nunique(),
    'unique_test_currents':test.current_article_id.nunique(),
    'unique_next_labels':train.next_article_id.nunique(),
    'direct_target_rate':(train.next_article_id==train.target_article_id).mean(),
    'top_1_next_label_share':next_freq.iloc[0]/len(train),
    'top_10_next_label_share':next_freq.head(10).sum()/len(train),
})
display(state_eda.to_frame('value'))
''')

state_interpretation = nbformat.v4.new_markdown_cell("""### Interpretasi EDA State

- Train berisi **9.000 state** dan test berisi **6.000 state**.
- Terdapat **360 target train** dan **240 target test**, masing-masing tepat memiliki 25 state. Tidak ada target yang overlap antara kedua split. Karena itu random row split akan memberi validasi yang terlalu optimistis, sehingga validation wajib dikelompokkan berdasarkan target.
- Train mencakup 3.866 current articles, tetapi hanya **1.023 artikel** pernah menjadi label next click. Distribusinya sangat long tail.
- Satu label terpopuler mencakup sekitar **11,64%** train dan sepuluh label teratas mencakup **36,39%**. Popularity berguna sebagai fitur, tetapi tidak cukup sebagai model karena sebagian besar label jarang muncul.
- Next click langsung menuju target hanya terjadi pada sekitar **0,74%** state. Model harus benar-benar mempelajari routing multi-step, bukan sekadar memilih target ketika tersedia.""")

article_md = nbformat.v4.new_markdown_cell("""## 4. Exploratory Data Analysis Artikel dan Kategori

EDA metadata memeriksa panjang judul, jumlah kategori per artikel, kategori paling umum, serta cakupan article ID pada peran current, target, dan next click.

Analisis ini menentukan bagaimana teks dan kategori sebaiknya direpresentasikan. Judul yang pendek cocok dipadukan dengan character n-gram, sedangkan kategori memberikan konteks tambahan untuk artikel yang namanya ambigu.""")

article_code = nbformat.v4.new_code_cell(r'''
article_eda=articles[['article_id','title']].copy()
article_eda['title_length']=article_eda.title.astype(str).str.len()
categories_per_article=categories.groupby('article_id').size().reindex(articles.article_id,fill_value=0)
top_categories=categories.category.value_counts().head(15).sort_values()
role_coverage=pd.Series({
    'Train current':train.current_article_id.nunique(),
    'Test current':test.current_article_id.nunique(),
    'Train target':train.target_article_id.nunique(),
    'Test target':test.target_article_id.nunique(),
    'Train next label':train.next_article_id.nunique(),
})

fig,ax=plt.subplots(2,2,figsize=(16,11))
sns.histplot(article_eda.title_length,bins=35,ax=ax[0,0],color='#4c78a8')
ax[0,0].axvline(article_eda.title_length.median(),color='#e45756',ls='--',label='Median')
ax[0,0].set_title('Distribusi panjang judul artikel'); ax[0,0].set_xlabel('Jumlah karakter'); ax[0,0].legend()

sns.histplot(categories_per_article,bins=np.arange(-.5,categories_per_article.max()+1.5,1),discrete=True,ax=ax[0,1],color='#54a24b')
ax[0,1].set_title('Jumlah kategori per artikel'); ax[0,1].set_xlabel('Kategori')

top_categories.index=top_categories.index.str.replace('subject.','',regex=False).str.replace('_',' ',regex=False)
top_categories.plot.barh(ax=ax[1,0],color='#f58518')
ax[1,0].set_title('15 kategori dengan artikel terbanyak'); ax[1,0].set_xlabel('Artikel')

role_coverage.sort_values().plot.barh(ax=ax[1,1],color='#72b7b2')
ax[1,1].axvline(len(articles),color='#555555',ls='--',label='Seluruh artikel')
ax[1,1].set_title('Cakupan artikel menurut peran'); ax[1,1].set_xlabel('Unique article ID'); ax[1,1].legend()
plt.tight_layout(); plt.show()

metadata_summary=pd.Series({
    'articles':len(articles),
    'category_rows':len(categories),
    'unique_categories':categories.category.nunique(),
    'median_title_length':article_eda.title_length.median(),
    'p95_title_length':article_eda.title_length.quantile(.95),
    'mean_categories_per_article':categories_per_article.mean(),
    'articles_without_category':int((categories_per_article==0).sum()),
})
display(metadata_summary.to_frame('value'))
''')

article_interpretation = nbformat.v4.new_markdown_cell("""### Interpretasi EDA Artikel dan Kategori

- Corpus memuat **4.604 artikel**, 5.204 pasangan article-category, dan 129 kategori unik.
- Median panjang judul hanya **12 karakter**, sedangkan persentil ke-95 adalah 28 karakter. Word TF-IDF perlu dilengkapi character n-gram agar judul pendek, variasi ejaan, dan named entity tetap dapat dibandingkan.
- Rata-rata artikel memiliki **1,13 kategori**, median satu, dan hanya enam artikel tanpa kategori. Kategori cukup lengkap untuk menjadi semantic context tambahan.
- Cakupan next-click label jauh lebih sempit daripada cakupan current article. Temuan ini mendukung penggunaan click popularity sebagai fitur kecil, tetapi target split yang benar-benar terpisah tetap menuntut fitur graph dan semantic yang dapat melakukan generalisasi.""")

nb.cells[5:5] = [state_md, state_code, state_interpretation, article_md, article_code, article_interpretation]

# Original graph visualization is now at index 15.
graph_interpretation = nbformat.v4.new_markdown_cell("""### Interpretasi EDA OCR dan Hyperlink Graph

- Graph hasil OCR dan recovery memiliki **95.418 directed edges**. Sebanyak 4.546 dari 4.604 halaman memiliki outgoing link, sedangkan 58 halaman tidak menghasilkan kandidat.
- Median out-degree adalah **16** dan persentil ke-95 sekitar **55**. Distribusi degree memiliki long tail, sehingga candidate cap diperlukan untuk menjaga ukuran pair table tetap terkendali.
- Mean OCR matcher accepted rate adalah **99,05%** dan mediannya 100%. Angka ini menunjukkan keberhasilan mapping pada region yang terdeteksi, bukan precision terhadap seluruh link asli.
- Recovery menambahkan 1.482 exact-segment edges dan 680 fuzzy edges. Dengan candidate recall akhir 99,39%, OCR cukup kuat untuk dipakai sebagai preprocessing reusable dan tidak perlu dijalankan ulang ketika model direrun.""")
nb.cells[16:16] = [graph_interpretation]

# Original grouped route EDA is now at index 22 after the earlier insertion.
route_interpretation = nbformat.v4.new_markdown_cell("""### Interpretasi EDA Routing

- Jawaban benar tersedia dalam candidate pool untuk **99,39%** validation states.
- Sebanyak **96,93%** jawaban berada pada kandidat dengan graph distance minimum menuju target. Ini menjadikan reverse BFS sebagai anchor yang sangat kuat.
- Hanya **28,12%** state mempunyai satu kandidat minimum yang unik. Sebagian besar state membutuhkan tie-breaking di antara beberapa shortest-path candidates.
- Histogram tie size menunjukkan bahwa masalah utama bukan menemukan rute yang dapat mencapai target, melainkan memilih rute yang paling mungkin dipilih navigator. Karena itu model final menambahkan shortest-path mass, semantic pair features, dan discounted reachability.""")
nb.cells[23:23] = [route_interpretation]

for cell in nb.cells:
    cell.source = cell.source.replace("—", "-").replace("–", "-")
    if cell.cell_type == "code":
        cell.outputs = []
        cell.execution_count = None

nbformat.write(nb, SOURCE)
print(SOURCE)
