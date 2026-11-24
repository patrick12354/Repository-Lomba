from pathlib import Path
import nbformat


ROOT = Path("/Users/timotiuspatrick/Documents/Patrick/Kuliah & Coding/Dataton/day 2/patrick")
SOURCE = ROOT / "notebooks/source/datathon_task2_v6_discounted_reachability_source.ipynb"

nb = nbformat.read(SOURCE, as_version=4)

markdown = {
    0: """# Prediksi Next Click Wikipedia Menggunakan Hybrid Graph Routing, Semantic Pair Ranking, dan Discounted Reachability

## Tim RIZZZ

**Universitas Airlangga**

### Anggota Kelompok

- Timotius Christopher Patrick Sihombing
- Raphael Angelo Adikara Purnama
- Aqila Malfa Zahira

Notebook ini memprediksi artikel yang akan diklik berikutnya ketika navigator berada pada suatu artikel Wikipedia dan sedang menuju artikel target. Prediksi dibatasi pada link biru yang tersedia di halaman saat ini.

Pipeline final menggabungkan tiga sumber informasi:

1. **Graph routing:** reverse BFS mengukur jarak setiap kandidat menuju target dan shortest-path mass menilai banyaknya rute terpendek.
2. **Semantic pair ranking:** embedding judul dan kategori kandidat–target dipadukan dengan fitur tabular melalui LightGBM.
3. **Discounted reachability:** random walk terdiskonto mengukur kualitas seluruh rute pendek sambil memperhitungkan tingkat percabangan halaman.

Evaluasi menggunakan exact-match accuracy dan `GroupKFold(target_article_id)` agar artikel target pada validation tidak muncul dalam training fold. Notebook menghasilkan submission berformat `state_id,predicted_next_article_id`.""",
    1: """## 1. Konfigurasi dan Reproducibility

Bagian ini menetapkan seed, jumlah fold, lokasi dataset, mode lokal/Kaggle, dan direktori output. Local execution memakai environment proyek yang sudah tersedia, sedangkan Kaggle dapat membaca competition dataset serta cache preprocessing yang dilampirkan sebagai input.

Pipeline final berjalan di CPU. OCR dan encoding artikel tidak diulang karena hasil preprocessing telah disimpan sebagai artifact reusable.""",
    3: """## 2. Pengenalan Dataset dan Pemeriksaan Input

Dataset terdiri dari metadata artikel, kategori, state train berlabel, state test, screenshot setiap artikel, dan contoh submission. Pemeriksaan awal memastikan ID artikel valid, urutan `state_id` konsisten, target train dan test terpisah, serta reusable OCR bundle lengkap.

Setiap state direpresentasikan oleh `(current_article_id, target_article_id)`, sedangkan label train adalah `next_article_id`.""",
    5: """## 3. Preprocessing Link dari Screenshot

Link artikel sebelumnya diekstrak dari teks biru pada screenshot menggunakan deteksi region dan OCR. Cache yang digunakan di sini memuat accepted links serta recovery untuk region OCR yang menggabungkan beberapa judul.

Preprocessing ini menghasilkan directed hyperlink graph tanpa menjalankan OCR ulang. Recovery hanya memetakan teks yang terdeteksi ke artikel resmi dan tidak menggunakan label `next_article_id`.""",
    7: """## 4. Exploratory Data Analysis Graph dan Kualitas Kandidat

Setiap artikel menjadi node dan setiap link biru menjadi directed edge. Analisis memeriksa distribusi out-degree, cakupan halaman, posisi link, confidence OCR, dan jumlah edge hasil recovery.

Graph akhir memiliki candidate coverage yang sangat tinggi. Pada run tersimpan, jawaban benar tersedia dalam candidate pool untuk **99,39%** state, sehingga bottleneck utama berada pada pemilihan satu link di antara beberapa kandidat, bukan pada ekstraksi gambar.""",
    10: """## 5. Representasi Teks, Kategori, dan Jarak Graph

Judul artikel direpresentasikan menggunakan word dan character TF-IDF, sementara kategori diolah menjadi exact overlap dan token overlap. Reverse BFS dari target menghitung jarak seluruh artikel menuju target secara efisien.

Hasil EDA route menunjukkan **96,93%** label train berada pada kandidat dengan jarak graph minimum. Namun hanya **28,12%** state memiliki satu kandidat minimum yang unik, sehingga diperlukan tie-breaking berbasis struktur dan semantik.""",
    13: """## 6. Candidate-Pair Features dan Grouped Validation

Satu baris modeling mewakili pasangan `(state, candidate)`. Candidate pool berasal dari outgoing links halaman saat ini, kemudian setiap pasangan diberi fitur jarak, perubahan jarak, kemiripan teks, overlap kategori, degree, posisi link, click prior yang fold-safe, dan struktur neighborhood.

`GroupKFold(target_article_id)` digunakan agar seluruh state dengan target yang sama selalu berada pada fold yang sama. Ini mengukur kemampuan model melakukan generalisasi ke target baru seperti pada test set.""",
    16: """## 7. Skor Dasar Berbasis Shortest-Path Structure

Komponen graph memberi prioritas kuat kepada kandidat yang meminimalkan jarak menuju target. Ketika beberapa kandidat sama-sama minimum, skor tambahan menggunakan kemiripan judul/kategori, degree, link position, neighborhood overlap, dan **shortest-path mass**.

Shortest-path mass menghitung jumlah rute terpendek yang dapat dilanjutkan dari setiap kandidat. Transformasi log digunakan agar halaman dengan jumlah rute sangat besar tidak mendominasi skor.""",
    18: """## 8. Dasar Pemilihan Metode

Dataset memiliki karakteristik Wikispeedia: navigator cenderung bergerak menuju halaman hub pada fase awal dan menggunakan kedekatan isi ketika mendekati target. Karena itu metode final tidak memperlakukan screenshot sebagai klasifikasi gambar langsung.

Screenshot digunakan untuk memperoleh daftar aksi yang sah, graph digunakan untuk perencanaan rute, dan representasi teks digunakan untuk membedakan kandidat yang secara struktural setara. External navigation paths tidak digunakan sebagai label train maupun lookup submission.""",
    19: """## 9. Pretrained Article Embeddings

Setiap artikel direpresentasikan oleh embedding 384 dimensi dari `all-MiniLM-L6-v2` berdasarkan judul dan kategori. Embedding dinormalisasi, disimpan sebagai cache, kemudian direduksi menjadi 48 komponen menggunakan PCA yang di-fit pada seluruh corpus artikel tanpa label.

Cache membuat notebook dapat dijalankan ulang dengan cepat: model pretrained tidak perlu melakukan encoding ulang selama file embedding tersedia.""",
    21: """## 10. Semantic Candidate–Target Interaction

Model tidak hanya memakai cosine similarity. Untuk setiap kandidat dan target, dibuat fitur nonlinear berupa elementwise product, absolute difference, koordinat PCA kandidat/target, serta directional semantic progress dari current menuju target.

Fitur embedding digabungkan dengan fitur graph, OCR, kategori, dan click prior. LightGBM kemudian mempelajari probability bahwa suatu candidate merupakan next click. Sample weight diseimbangkan per state agar halaman dengan banyak link tidak mendominasi training.""",
    23: """## 11. Out-of-Fold Training Semantic Ranker

LightGBM dilatih pada minimum-distance candidates yang memiliki positive label di training fold. Prediksi validation tetap dibuat untuk seluruh kandidat agar evaluasi sama dengan inference sebenarnya.

Probability semantic ranker digunakan sebagai koreksi kecil terhadap graph-routing score. Graph tetap menjadi anchor karena candidate distance merupakan sinyal paling stabil, sedangkan semantic model terutama menyelesaikan sebagian shortest-path ties.""",
    25: """## 12. Discounted Random-Walk Reachability

Untuk target `t`, nilai reachability dihitung sebagai deret `eₜ + γPeₜ + γ²P²eₜ + ...`, dengan `P` berupa transition matrix outgoing-link yang dinormalisasi berdasarkan out-degree.

Fitur ini menilai seluruh walk pendek menuju target, bukan hanya rute yang tepat terpendek. Nilai dicenter di dalam setiap state sehingga hanya perbedaan antarkandidat yang memengaruhi ranking. Konfigurasi final menggunakan `γ=0,30`, 16 propagation steps, dan koefisien `−0,06`; tanda negatif mengoreksi kecenderungan memilih halaman yang terlalu bercabang setelah shortest distance dikontrol.""",
    27: """## 13. Evaluasi Model dan Penetapan Konfigurasi Final

Bagian ini membandingkan graph-routing baseline, penambahan semantic ranker, dan model hybrid lengkap menggunakan fold serta candidate pool yang identik. Parameter final dikunci pada semantic weight `0,20` dan reachability weight `−0,06`.

Pada run tersimpan, exact-match grouped OOF model final mencapai **77,62%**, top-3 **94,23%**, dan top-5 **97,24%**. Honest nested selection mencapai **77,51%**, menunjukkan konfigurasi tetap stabil ketika parameter dipilih tanpa melihat held-out fold.""",
    29: """## 14. Error Analysis

Analisis membandingkan final hybrid dengan semantic-only fallback pada state OOF yang sama. Reachability mengubah 145 prediksi: 62 kesalahan diperbaiki, 50 prediksi benar mengalami regression, dan 33 tetap salah. Perubahan bersih adalah **12 jawaban tambahan yang benar**.

Sisa kesalahan terutama berasal dari beberapa kandidat shortest-path yang sama-sama masuk akal. Karena candidate recall sudah 99,39%, peningkatan berikutnya lebih membutuhkan pemahaman konteks navigasi daripada OCR tambahan.""",
    31: """## 15. Pelatihan Final dan Prediksi Test

Setelah konfigurasi dikunci, PCA dan LightGBM di-fit menggunakan seluruh train. Untuk setiap state test, pipeline membentuk candidate pool, menghitung graph-routing score, semantic probability, serta discounted reachability, lalu memilih kandidat dengan skor akhir tertinggi.

Model final hanya memprediksi artikel valid dari candidate-generation pipeline. Semantic-only prediction tetap dihitung sebagai fallback dan untuk mengukur sensitivitas keputusan akhir.""",
    33: """## 16. Submission Audit dan Penyimpanan Artifact

Submission diperiksa terhadap jumlah baris, keunikan `state_id`, missing value, validitas article ID, dan kesesuaian urutan dengan `sample_submission.csv`. Model, PCA, configuration, CV table, nested validation, OOF error pack, diagnostics, serta submission disimpan agar eksperimen dapat direproduksi.

Audit run tersimpan menghasilkan 6.000 state unik tanpa NaN atau invalid article ID. Prediksi final berbeda dari semantic-only fallback pada **1,75%** test states.""",
    35: """## 17. Kesimpulan dan File Submission

Model final memprediksi next click menggunakan daftar link hasil screenshot OCR, shortest-path routing, shortest-path mass, semantic candidate–target interactions, dan discounted random-walk reachability.

Ringkasan hasil:

- Grouped OOF exact-match accuracy: **77,62%**
- Honest nested accuracy: **77,51%**
- Top-3 accuracy: **94,23%**
- Top-5 accuracy: **97,24%**
- Candidate recall: **99,39%**
- Runtime full local dengan cache: sekitar **1,16 menit**

Submission utama yang dihasilkan adalah `datathon_task2_v6_discounted_reachability.csv`. File memiliki kolom `state_id,predicted_next_article_id` dan telah lolos seluruh pemeriksaan format.""",
}

for index, text in markdown.items():
    assert nb.cells[index].cell_type == "markdown", index
    nb.cells[index].source = text.strip()

# User-facing labels describe model components instead of development versions.
replacements = {
    28: {
        "'V4 anchor'": "'Graph routing baseline'",
        "'V5 semantic blend'": "'Graph + semantic ranker'",
        "'V6 + discounted reachability'": "'Final hybrid model'",
        "'Nested V6 mean:": "'Nested final-model mean:",
    },
    30: {
        "'V6 changes versus V5'": "'Final hybrid changes versus semantic-only fallback'",
        "INSIGHT ERROR: reachability diterima karena mean dan nested grouped OOF sama-sama melampaui V5.": "INSIGHT ERROR: reachability dipertahankan karena mean dan nested grouped OOF sama-sama meningkat.",
    },
    32: {
        "'V6 vs V5 test disagreement:'": "'Final model vs semantic-only fallback disagreement:'",
    },
    34: {
        "'primary_v6'": "'final_hybrid'",
        "'fallback_v5'": "'semantic_fallback'",
    },
}

for index, mapping in replacements.items():
    assert nb.cells[index].cell_type == "code", index
    source = nb.cells[index].source
    for old, new in mapping.items():
        assert old in source, (index, old)
        source = source.replace(old, new)
    nb.cells[index].source = source

# Style rule: final notebook does not use em dash or en dash characters.
for cell in nb.cells:
    cell.source = cell.source.replace("—", "-").replace("–", "-")

# Source notebook stays clean; the executed final notebook is regenerated separately.
for cell in nb.cells:
    if cell.cell_type == "code":
        cell.outputs = []
        cell.execution_count = None

nbformat.write(nb, SOURCE)
print(SOURCE)
