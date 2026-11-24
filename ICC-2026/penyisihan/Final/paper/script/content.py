"""ISI PAPER. Edit teks di file ini, lalu jalankan `python build.py` untuk regenerate DOCX + PDF.

Versi bahasa Inggris lama ada di riwayat git (commit 9d84bfe, content.py). Versi ini bukan terjemahannya
kalimat per kalimat: paragrafnya disusun ulang mengikuti kebiasaan tulisan ilmiah berbahasa Indonesia
(kalimat topik di depan, satu gagasan per paragraf, pertanyaan retoris dihindari).

Aturan gaya (lihat ../README.md):
  - Bahasa Indonesia baku yang luwes. Istilah teknis yang lazim dibiarkan dalam bahasa Inggris
    (Dice, recall, lesion mask, window/level); istilah asing dimiringkan bila belum lazim.
  - DILARANG em dash (U+2014) dan en dash. Rentang ditulis "s.d." atau "hingga".
  - Angka hasil eksperimen jangan diketik manual: ambil dari R["..."] (results/*.json) lewat num().
  - Sitasi: {cite:kunci}. Gambar: {fig:kunci}. Tabel: {tab:kunci}. Tebal **x**, miring *x*.
"""
import json
from pathlib import Path

RES = Path(__file__).resolve().parent / "results"


def _load(n):
    p = RES / f"{n}.json"
    return json.load(open(p)) if p.exists() else {}


R = {"kohort": _load("kohort"), "seg": _load("segmentasi"), "nilai": _load("penilaian"), "bkt": _load("bkt"),
     "llm": _load("llm"), "ci": _load("ci"), "final": _load("final"), "e2e": _load("mvp_e2e")}

# Tautan MVP (Bab IV). GitHub: isi tautan repositori publik source code MVP sebelum dikumpulkan.
LINK_MVP = "https://mvp-lemon-ten.vercel.app"
LINK_GITHUB = "https://github.com/raphaeladikara/satu-data-final"


def num(x, nd=1):
    """Format angka gaya Indonesia: koma desimal, titik ribuan."""
    return f"{x:,.{nd}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x, nd=0):
    return num(100 * x, nd) + "%"


K, S, P, B, L, CI = R["kohort"], R["seg"], R["nilai"], R["bkt"], R["llm"], R["ci"]
# hasil uji MVP (analysis/a07-a10): F = ringkasan + IK, E = uji ujung ke ujung
F, E = R["final"], R["e2e"]
FT, FS, FE, FR = F.get("tutor", {}), F.get("seg", {}), F.get("e2e", {}), F.get("rules", {})
LTB = FT.get("latensi_berurutan", {})


def ik(v, f=lambda x: num(x, 2)):
    """'IK 95% a s.d. b' dari pasangan [a, b]."""
    return f"IK 95% {f(v[0])} s.d. {f(v[1])}" if v else ""


def ikp(v, nd=0):
    return ik(v, lambda x: pct(x, nd))
B_acak = B["acak"]["mean"] if B else [0] * 61
B_adap = B["adaptif"]["mean"] if B else [0] * 61
_gap = [r["adaptif"] - r["acak"] for r in B.get("sensitivitas", [])] or [0]
SENS_MIN, SENS_MAX = min(_gap), max(_gap)
TK = K.get("tingkat", {})
LA, LB = L.get("tanpa_fakta", {}), L.get("dengan_fakta", {})
LT, LBT = L.get("tanpa_fakta_tekanan", {}), L.get("dengan_fakta_tekanan", {})

# Asumsi estimasi biaya: sama dengan content.py (tarif per 1 juta token, US$)
TARIF_IN, TARIF_OUT, KURS = 0.20, 1.20, 16500
TOK_IN, TOK_OUT, INTERAKSI = 3000, 400, 300
BIAYA_MHS = (TOK_IN * TARIF_IN + TOK_OUT * TARIF_OUT) / 1e6 * INTERAKSI * KURS
BIAYA_SERVER = 600_000
BIAYA_PILOT = 60 * BIAYA_MHS + BIAYA_SERVER


def rp(x):
    return "Rp" + num(x, 0)


def ci(key, nd=2, persen=False, sub=None):
    """Teks interval kepercayaan 95% dari results/ci.json, mis. 'IK 95% 0,70 s.d. 0,85'."""
    v = (CI.get(sub, {}) if sub else CI).get(key)
    if not v:
        return ""
    f = (lambda x: pct(x)) if persen else (lambda x: num(x, nd))
    return f"IK 95% {f(v[0])} s.d. {f(v[1])}"


def cil(kondisi, key):
    v = CI.get("llm", {}).get(kondisi, {}).get(key)
    return f"IK 95% {pct(v[0])} s.d. {pct(v[1])}" if v else ""


# Estimasi waktu radiolog selama pilot (menit per item x jumlah item). Asumsi, bukan pengukuran.
JAM_RADIOLOG = [("memeriksa hasil registrasi atlas pada {n} kasus", 50, 2),
                ("memberi label usia lesi (K5) pada {n} kasus", 300, 1),
                ("menilai {n} anotasi mahasiswa untuk mengukur kesesuaian dengan aturan penilaian", 120, 1.5),
                ("memeriksa sampel {n} label K3 semi-otomatis", 150, 0.5)]
TOTAL_JAM_RADIOLOG = sum(n * m for _, n, m in JAM_RADIOLOG) / 60

ABS_LLM = (f" Pada uji {L.get('n', 30)} kasus, pemberian temuan terstruktur menaikkan ketepatan klaim tutor dari "
           f"{pct(LA.get('akurasi', 0))} menjadi {pct(LB.get('akurasi', 0))}, dan tutor yang diberi fakta tidak pernah "
           "ikut membenarkan jawaban keliru yang didesakkan mahasiswa.") if L else ""

# ------------------------------------------------------------------ META
META = dict(
    tim="Rizzz",
    judul="SINAPS: Tutor AI Adaptif untuk Menilai Interpretasi MRI Stroke Mahasiswa Kedokteran Berbasis Kunci Jawaban Tingkat Voxel",
    penulis=[
        dict(nama="Timotius Christopher Patrick Sihombing", nim="164241005", prodi="Sains Data", kampus="Universitas Airlangga", kota="Surabaya, Indonesia"),
        dict(nama="Aqila Malfa Zahira", nim="164231036", prodi="Sains Data", kampus="Universitas Airlangga", kota="Surabaya, Indonesia"),
        dict(nama="Radam Gumelar", nim="164231032", prodi="Sains Data", kampus="Universitas Airlangga", kota="Surabaya, Indonesia"),
        dict(nama="Raphael Angelo Adikara Purnama", nim="164251055", prodi="Sains Data", kampus="Universitas Airlangga", kota="Surabaya, Indonesia"),
    ],
    label_abstrak="Abstrak",
    abstrak=(
        "Stroke menyebabkan 18,5% kematian di Indonesia, dan penanganannya bergantung pada kemampuan dokter membaca "
        "citra otak. Mahasiswa kedokteran masih mempelajari keterampilan ini terutama dari gambar statis dan umpan balik "
        "radiolog, padahal Indonesia hanya memiliki sekitar 0,8 radiolog per 100.000 penduduk, sementara chatbot AI umum "
        "yang rutin dipakai mahasiswa belum andal membaca citra medis. Makalah ini merancang, membangun, dan menguji "
        "SINAPS, tutor neuroradiologi berbasis web yang menggabungkan viewer MRI, penilaian otomatis terhadap lesion "
        "mask ahli, personalisasi dengan Bayesian Knowledge Tracing (BKT), dan tutor model bahasa multimodal yang hanya "
        "menjelaskan temuan terstruktur. Prototipe (MVP) sudah berjalan daring dengan bank 36 kasus nyata dari dataset "
        f"terbuka SOOP ({num(K.get('n_participants', 1505), 0)} pasien stroke), dasbor dosen, dan log belajar "
        "berpseudonim. Pengujian terhadap kode yang di-deploy menunjukkan empat hasil. Seluruh "
        f"{num(E.get('n_panggilan', 0), 0)} panggilan API pada uji ujung ke ujung berhasil tanpa kebocoran kunci "
        "jawaban. Modul penilaian mengenali lima jenis kesalahan anotasi sintetis dengan akurasi "
        f"{pct(FE.get('akurasi', 0))} ({ikp(FE.get('ik95'))}), dibanding {pct(FR.get('dice_saja', 0))} bila hanya "
        f"memakai Dice. Pada {FT.get('semua', {}).get('n', 144)} jawaban tutor dalam empat skenario uji, termasuk "
        "mahasiswa yang mendesakkan jawaban keliru, tidak ada temuan di luar fakta "
        f"({ikp(FT.get('semua', {}).get('ik95'), 1)}), dengan latensi persentil ke-95 sebesar "
        f"{num(FT.get('latensi_paralel8', {}).get('p95', 0))} detik saat delapan permintaan berjalan bersamaan. U-Net 2.5D yang dilatih pada "
        f"{num(FS.get('n_train', 0), 0)} pasien mencapai rerata Dice {num(FS.get('dice_mean', 0), 2)} pada kasus bank, "
        f"tetapi hanya {num(FS.get('dice_lt5ml', 0), 2)} untuk lesi di bawah 5 ml. Pengujian juga menemukan "
        "kelemahan yang belum terlihat di rancangan, di antaranya kriteria lulus delineasi yang meloloskan jawaban "
        "terlalu luas; kelemahan ini sudah diperbaiki dan diuji ulang. Efek belajar pada mahasiswa sungguhan belum diukur dan menjadi tahap pilot berikutnya."
    ),
    label_kata_kunci="Kata Kunci",
    kata_kunci="pendidikan kedokteran, pendidikan radiologi, sistem tutor cerdas, knowledge tracing, segmentasi lesi stroke, model bahasa multimodal",
    label_gambar="Gambar",
    label_tabel="Tabel",
    label_pustaka="Daftar Pustaka",
)

# ------------------------------------------------------------------ REFERENSI (format IEEE)
REFS = {
    "kemkes2024": "Kementerian Kesehatan Republik Indonesia, “Cegah stroke dengan aktivitas fisik, bagaimana caranya?” kemkes.go.id, 25 Okt. 2024. [Daring]. Tersedia: https://www.kemkes.go.id/id/cegah-stroke-dengan-aktivitas-fisik",
    "kemkes2024b": "Kementerian Kesehatan Republik Indonesia, “Strategi Kemenkes tingkatkan rasio dokter di Indonesia,” kemkes.go.id, 24 Apr. 2024. [Daring]. Tersedia: https://www.kemkes.go.id/id/strategi-kemenkes-tingkatkan-rasio-dokter-di-indonesia",
    "ski2023": "Badan Kebijakan Pembangunan Kesehatan, *Survei Kesehatan Indonesia (SKI) 2023 dalam Angka*. Jakarta: Kementerian Kesehatan Republik Indonesia, 2023.",
    "gbd2021": "GBD 2021 Stroke Risk Factor Collaborators, “Global, regional, and national burden of stroke and its risk factors, 1990-2021: a systematic analysis for the Global Burden of Disease Study 2021,” *Lancet Neurol.*, vol. 23, no. 10, pp. 973-1003, 2024.",
    "saver2006": "J. L. Saver, “Time is brain, quantified,” *Stroke*, vol. 37, no. 1, pp. 263-266, 2006.",
    "yunus2024": "R. E. Yunus, “Radiology loading and coverage hours in Indonesia,” *Korean J. Radiol.*, vol. 25, no. 7, pp. 597-599, 2024, doi: 10.3348/kjr.2024.0267.",
    "daraghma2026": "M. Daraghma *et al.*, “Confidence in radiological skills and perceived adequacy of radiology training among medical students and interns in Palestine,” *J. Med. Educ. Curric. Dev.*, vol. 13, art. 23821205261441364, 2026.",
    "fontaine2019": "G. Fontaine *et al.*, “Efficacy of adaptive e-learning for health professionals and students: a systematic review and meta-analysis,” *BMJ Open*, vol. 9, no. 8, art. e025252, 2019.",
    "chen2026": "Y. Chen *et al.*, “Using large language model to aid in teaching medical imaging report writing,” *Med. Teach.*, vol. 48, no. 6, pp. 957-966, 2026.",
    "chen2025": "S. Chen *et al.*, “When helpfulness backfires: LLMs and the risk of false medical information due to sycophantic behavior,” *npj Digit. Med.*, vol. 8, art. 605, 2025.",
    "orr2024": "M. E. Orr *et al.*, “Patterns of contouring mistakes in the novice resident: a qualitative analysis to guide future educational efforts,” *Int. J. Radiat. Oncol. Biol. Phys.*, 2024, doi: 10.1016/j.ijrobp.2024.07.2199.",
    "rohren2022": "S. A. Rohren *et al.*, “Canadian medical student’s perception toward undergraduate radiology education,” *Can. Assoc. Radiol. J.*, vol. 73, no. 2, pp. 419-421, 2022.",
    "brady2025": "A. P. Brady *et al.*, “Current status of radiologist staffing, education and training in the 27 EU Member States,” *Insights Imaging*, vol. 16, no. 1, art. 59, 2025.",
    "esr2011": "European Society of Radiology, “Undergraduate education in radiology. A white paper by the European Society of Radiology,” *Insights Imaging*, vol. 2, no. 4, pp. 363-374, 2011.",
    "chegg2025": "Chegg.org, “Global Student Survey 2025,” survei terhadap 11.706 mahasiswa di 15 negara oleh Yonder Consulting, Jan. 2025. [Daring]. Tersedia: https://www.chegg.org/global-student-survey-2025",
    "brin2025": "D. Brin *et al.*, “Assessing GPT-4 multimodal performance in radiological image analysis,” *Eur. Radiol.*, vol. 35, no. 4, pp. 1959-1965, 2025.",
    "vds2026": "M. S. von der Stück *et al.*, “Visual large language models in radiology: a systematic multimodel evaluation of diagnostic accuracy and hallucinations,” *Life*, vol. 16, no. 1, art. 66, 2026.",
    "kung2023": "T. H. Kung *et al.*, “Performance of ChatGPT on USMLE: potential for AI-assisted medical education using large language models,” *PLOS Digit. Health*, vol. 2, no. 2, art. e0000198, 2023.",
    "ericsson2004": "K. A. Ericsson, “Deliberate practice and the acquisition and maintenance of expert performance in medicine and related domains,” *Acad. Med.*, vol. 79, no. 10 Suppl., pp. S70-S81, 2004.",
    "pusic2011": "M. V. Pusic, M. Pecaric, and K. Boutis, “How much practice is enough? Using learning curves to assess the deliberate practice of radiograph interpretation,” *Acad. Med.*, vol. 86, no. 6, pp. 731-736, 2011.",
    "boutis2010": "K. Boutis, M. Pecaric, B. Seeto, and M. Pusic, “Using signal detection theory to model changes in serial learning of radiological image interpretation,” *Adv. Health Sci. Educ.*, vol. 15, no. 5, pp. 647-658, 2010.",
    "econtour2019": "M. V. Sherer *et al.*, “Development and usage of eContour, a novel, three-dimensional, image-based web site to facilitate access to contouring guidelines at the point of care,” *JCO Clin. Cancer Inform.*, vol. 3, pp. 1-9, 2019, doi: 10.1200/CCI.19.00041.",
    "icontour2025": "M. E. Orr *et al.*, “Evaluating an interactive online contouring education platform for radiation oncology residents: results of an international longitudinal randomized controlled trial,” dipresentasikan di *ASTRO Annual Meeting*, San Francisco, CA, 29 Sep. 2025, abstrak 1022. [Daring]. Tersedia: https://am25.astro.org/sessions/qp-04-21571",
    "hidayat2025": "R. Hidayat *et al.*, “The necessity of using MRI as an imaging modality in acute code stroke in Indonesia,” *Vasc. Health Risk Manag.*, vol. 21, pp. 207-215, 2025, doi: 10.2147/VHRM.S503362.",
    "chalela2007": "J. A. Chalela *et al.*, “Magnetic resonance imaging and computed tomography in emergency assessment of patients with suspected acute stroke: a prospective comparison,” *Lancet*, vol. 369, no. 9558, pp. 293-298, 2007.",
    "radiopaedia": "Radiopaedia.org, “Radiopaedia: the wiki-based collaborative radiology resource.” [Daring]. Tersedia: https://radiopaedia.org (diakses 29 Sep. 2026).",
    "khanmigo": "Khan Academy, “Khanmigo: AI-powered tutor and teaching assistant.” [Daring]. Tersedia: https://www.khanmigo.ai (diakses 29 Sep. 2026).",
    "bloom1984": "B. S. Bloom, “The 2 sigma problem: the search for methods of group instruction as effective as one-to-one tutoring,” *Educ. Res.*, vol. 13, no. 6, pp. 4-16, 1984.",
    "kulik2016": "J. A. Kulik and J. D. Fletcher, “Effectiveness of intelligent tutoring systems: a meta-analytic review,” *Rev. Educ. Res.*, vol. 86, no. 1, pp. 42-78, 2016.",
    "corbett1994": "A. T. Corbett and J. R. Anderson, “Knowledge tracing: modeling the acquisition of procedural knowledge,” *User Model. User-Adapt. Interact.*, vol. 4, no. 4, pp. 253-278, 1994.",
    "pybkt2021": "A. Badrinath, F. Wang, and Z. Pardos, “pyBKT: an accessible Python library of Bayesian knowledge tracing models,” in *Proc. 14th Int. Conf. Educational Data Mining*, 2021, pp. 468-474.",
    "embretson2000": "S. E. Embretson and S. P. Reise, *Item Response Theory for Psychologists*. Mahwah, NJ: Lawrence Erlbaum, 2000.",
    "absher2024": "J. Absher *et al.*, “The stroke outcome optimization project: acute ischemic strokes from a comprehensive stroke center,” *Sci. Data*, vol. 11, 2024, doi: 10.1038/s41597-024-03667-5.",
    "isles2022": "M. R. Hernandez Petzsche *et al.*, “ISLES 2022: a multi-center magnetic resonance imaging stroke lesion segmentation dataset,” *Sci. Data*, vol. 9, art. 762, 2022.",
    "isensee2021": "F. Isensee, P. F. Jaeger, S. A. A. Kohl, J. Petersen, and K. H. Maier-Hein, “nnU-Net: a self-configuring method for deep learning-based biomedical image segmentation,” *Nat. Methods*, vol. 18, no. 2, pp. 203-211, 2021.",
    "deepisles2025": "E. de la Rosa *et al.*, “DeepISLES: a clinically validated ischemic stroke segmentation model from the ISLES'22 challenge,” *Nat. Commun.*, vol. 16, art. 7357, 2025.",
    "taha2015": "A. A. Taha and A. Hanbury, “Metrics for evaluating 3D medical image segmentation: analysis, selection, and tool,” *BMC Med. Imaging*, vol. 15, art. 29, 2015.",
    "maierhein2024": "L. Maier-Hein *et al.*, “Metrics reloaded: recommendations for image analysis validation,” *Nat. Methods*, vol. 21, no. 2, pp. 195-212, 2024.",
    "liu2023": "C.-F. Liu *et al.*, “Digital 3D brain MRI arterial territories atlas,” *Sci. Data*, vol. 10, art. 74, 2023.",
    "avants2008": "B. B. Avants, C. L. Epstein, M. Grossman, and J. C. Gee, “Symmetric diffeomorphic image registration with cross-correlation: evaluating automated labeling of elderly and neurodegenerative brain,” *Med. Image Anal.*, vol. 12, no. 1, pp. 26-41, 2008.",
    "thomalla2011": "G. Thomalla *et al.*, “DWI-FLAIR mismatch for the identification of patients with acute ischaemic stroke within 4.5 h of symptom onset (PRE-FLAIR): a multicentre observational study,” *Lancet Neurol.*, vol. 10, no. 11, pp. 978-986, 2011.",
    "lewis2020": "P. Lewis *et al.*, “Retrieval-augmented generation for knowledge-intensive NLP tasks,” in *Advances in Neural Information Processing Systems*, vol. 33, 2020, pp. 9459-9474.",
    "ohif2020": "E. Ziegler *et al.*, “Open Health Imaging Foundation Viewer: an extensible open-source framework for building web-based imaging applications to support cancer research,” *JCO Clin. Cancer Inform.*, vol. 4, pp. 336-345, 2020.",
    "fedorov2012": "A. Fedorov *et al.*, “3D Slicer as an image computing platform for the Quantitative Imaging Network,” *Magn. Reson. Imaging*, vol. 30, no. 9, pp. 1323-1341, 2012.",
    "openai2026": "OpenAI, “API pricing: gpt-5.6-luna,” dokumentasi pengembang OpenAI, 2026. [Daring]. Tersedia: https://developers.openai.com/api/docs/pricing (diakses 30 Sep. 2026).",
    "pnpk2019": "Kementerian Kesehatan Republik Indonesia, *Pedoman Nasional Pelayanan Kedokteran Tata Laksana Stroke*, Keputusan Menteri Kesehatan No. HK.01.07/MENKES/394/2019, 2019.",
    "skdi2012": "Konsil Kedokteran Indonesia, *Standar Kompetensi Dokter Indonesia*. Jakarta: KKI, 2012.",
    "uupdp2022": "Republik Indonesia, *Undang-Undang No. 27 Tahun 2022 tentang Pelindungan Data Pribadi*, 2022.",
    "brooke1996": "J. Brooke, “SUS: a quick and dirty usability scale,” in *Usability Evaluation in Industry*, P. W. Jordan *et al.*, Eds. London: Taylor & Francis, 1996, pp. 189-194.",
    "senn2002": "S. Senn, *Cross-over Trials in Clinical Research*, 2nd ed. Chichester: Wiley, 2002.",
    "cohen1988": "J. Cohen, *Statistical Power Analysis for the Behavioral Sciences*, 2nd ed. Hillsdale, NJ: Lawrence Erlbaum, 1988.",
}

# ------------------------------------------------------------------ paragraf uji tutor LLM (hasil atau protokol)
if L:
    _n_klaim = CI.get('llm', {}).get('tanpa_fakta', {}).get('n_klaim', 90)
    P_LLM = [
        ("p", f"Premis tersebut kami uji pada {L['n']} subjek sampel SOOP dengan GPT-5.6 Luna. Setiap kasus diwakili "
              "satu gambar berisi slice DWI dan ADC dengan lesi terbesar, lalu diberikan dalam dua kondisi: tanpa fakta "
              "(setara dengan yang dilihat chatbot umum) dan dengan temuan terstruktur disertai larangan menyebut apa pun "
              "yang tidak ada dalam data. Model diminta mengeluarkan klaim yang dapat dicocokkan dengan lesion mask, yaitu "
              "hemisfer, multifokalitas, dan kategori volume. Model juga ditanya teritori arteri, yang sengaja tidak "
              "dimasukkan ke data sehingga jawaban yang benar adalah \"tidak diketahui\"."),
        ("p", f"Hasilnya ditunjukkan pada {{fig:llm_uji}}. Tanpa fakta, hanya {pct(LA['akurasi'])} dari {_n_klaim} klaim "
              f"yang dapat diperiksa ternyata benar ({cil('tanpa_fakta', 'akurasi')}), {pct(LA['klaim_salah'])} keliru, "
              "dan sisanya tidak dijawab. Hemisfer masih ditebak benar pada "
              f"{pct(LA['akurasi_per_kunci']['hemisfer'])} kasus, tetapi multifokalitas dan kategori volume, yang menuntut "
              f"penalaran lintas slice, hanya benar pada {pct(LA['akurasi_per_kunci']['multifokal'])} dan "
              f"{pct(LA['akurasi_per_kunci']['kategori_volume'])} kasus. Dari sisi pengajaran, yang lebih mengkhawatirkan "
              f"adalah model tetap menebak teritori arteri pada {pct(LA['klaim_teritori_tanpa_dasar'])} kasus meski data "
              f"tidak memberi dasar apa pun. Dengan fakta, ketepatan klaim naik menjadi {pct(LB['akurasi'])} "
              f"({cil('dengan_fakta', 'akurasi')}), klaim keliru turun menjadi {pct(LB['klaim_salah'])}, tebakan teritori "
              f"turun menjadi {pct(LB['klaim_teritori_tanpa_dasar'])}, dan latensi persentil ke-95 sebesar "
              f"{num(LB['latensi_p95'])} detik. Ketepatan pada kondisi ini sebagian besar mencerminkan kesetiaan model "
              "menyampaikan ulang data. Sifat itu memang diharapkan dari tutor, tetapi hampir terjamin oleh rancangan "
              "ujinya sendiri."),
        ("p", "Pertanyaan yang lebih berat adalah apakah tutor tetap berpegang pada fakta ketika mahasiswa membantah, yaitu "
              "kegagalan sikofansi yang dibahas pada Subbab II.D. Karena itu kedua kondisi diulang dengan pesan mahasiswa "
              "yang mengusulkan hemisfer dan multifokalitas yang salah lalu meminta tutor sekadar mengiyakan. Tanpa fakta, "
              f"model mengikuti klaim keliru mahasiswa pada {pct(LT.get('ikut_saran_salah', 0))} klaim "
              f"({cil('tanpa_fakta_tekanan', 'ikut_saran_salah')}) dan tidak mampu menjawab sebagian besar sisanya. Dengan "
              f"fakta, model tidak pernah ikut ({pct(LBT.get('ikut_saran_salah', 0))}; "
              f"{cil('dengan_fakta_tekanan', 'ikut_saran_salah')}), ketepatan klaimnya tetap {pct(LBT.get('akurasi', 0))}, "
              "dan ia secara eksplisit mengoreksi mahasiswa, misalnya dengan menjelaskan bahwa penanda R berada di sisi kiri "
              "gambar menurut konvensi radiologis. Kedua uji ini belum menilai mutu pedagogis penjelasan tutor; hal itu "
              "diukur melalui hasil belajar pada {tab:evaluasi}."),
        ("fig", "llm_uji", f"Uji tutor LLM pada {L['n']} kasus SOOP: proporsi klaim benar dan keliru (hemisfer, "
                           "multifokalitas, kategori volume), proporsi kasus yang teritori arterinya ditebak tanpa dasar "
                           "data, dan (*) proporsi klaim ketika tutor ikut membenarkan jawaban keliru yang diusulkan mahasiswa."),
    ]
else:
    P_LLM = [
        ("p", "Premis tersebut akan diuji dengan protokol yang skripnya sudah disiapkan. Tiga puluh subjek sampel SOOP "
              "masing-masing diwakili satu gambar slice DWI dan ADC dengan lesi terbesar, lalu diberikan kepada model dalam "
              "dua kondisi: tanpa fakta dan dengan temuan terstruktur beserta larangan menyebut apa pun di luar data. Model "
              "harus mengeluarkan klaim yang dapat diperiksa otomatis terhadap lesion mask (hemisfer, multifokalitas, "
              "kategori volume), ditambah teritori arteri yang sengaja tidak disertakan sehingga jawaban benarnya adalah "
              "\"tidak diketahui\". Metrik utamanya adalah proporsi klaim keliru, proporsi penolakan yang tepat, dan "
              "latensi persentil ke-95."),
    ]

# ------------------------------------------------------------------ BODY
sd = S.get
BODY = [
    # =============================================================== BAB I
    ("h1", "Pendahuluan"),
    ("h2", "Latar Belakang"),
    ("p", "Membaca citra medis merupakan keterampilan yang dibutuhkan hampir semua dokter, bukan hanya radiolog "
          "{cite:esr2011}. Namun, cara mahasiswa kedokteran mempelajarinya masih jauh dari memadai. Survei terhadap 545 "
          "mahasiswa dari ke-17 fakultas kedokteran di Kanada menemukan bahwa kuliah didaktik adalah metode yang paling "
          "banyak dipakai (74%), dan 87% responden merasa paparan radiologinya kurang. Untuk setiap kelainan yang "
          "ditanyakan, kurang dari separuh responden yakin mampu menilainya {cite:rohren2022}. Kondisi di Eropa serupa: "
          "radiologi hanya mendapat porsi kecil dalam kurikulum dan umumnya diajarkan lewat potongan gambar statis "
          "{cite:esr2011}. Di lingkungan dengan sumber daya terbatas, masalahnya lebih tajam. Survei tahun 2026 terhadap "
          "431 mahasiswa klinik dan dokter internsip di Palestina mendapati hanya 43,2% yang menilai pendidikan "
          "radiologinya cukup dan hanya 26,9% yang yakin mampu membaca CT atau MRI kepala {cite:daraghma2026}."),
    ("p", "Kesenjangan ini penting karena interpretasi MRI adalah keterampilan prosedural, bukan hafalan visual. "
          "Mahasiswa harus menggulir puluhan slice, mengatur kontras, membandingkan DWI dengan peta ADC, lalu menandai "
          "batas lesi. Keterampilan semacam ini terbentuk melalui latihan terarah (*deliberate practice*) dengan umpan "
          "balik langsung {cite:ericsson2004}, dan studi kurva belajar pada interpretasi radiografi menunjukkan bahwa "
          "kompetensi baru tercapai setelah ratusan kasus {cite:pusic2011}."),
    ("p", "Di Indonesia, kekurangan pengajar memperparah kesenjangan tersebut. Rasio dokter nasional hanya 0,47 per 1.000 "
          "penduduk, peringkat ke-147 di dunia {cite:kemkes2024b}. Jumlah radiolog terdaftar hanya 2.161 orang untuk "
          "sekitar 280 juta penduduk, atau kira-kira 0,8 per 100.000, dan sebagian besar terkumpul di Jawa dan Sumatra. "
          "Dengan sekitar 100 lulusan baru per tahun, dibutuhkan lebih dari satu abad untuk menyamai kepadatan radiolog "
          "Singapura {cite:yunus2024}. Sebagai pembanding, rerata di 27 negara Uni Eropa adalah 12,7 per 100.000, dan "
          "negara terendah di kawasan itu pun masih memiliki 5,1 {cite:brady2025}. Radiolog yang sedikit ini harus "
          "membagi waktu antara pelayanan klinis dan mengajar, sehingga mustahil memberi setiap mahasiswa umpan balik "
          "pribadi atas ratusan kasus latihan ({fig:masalah})."),
    ("p", "Kekurangan yang sama juga berdampak langsung pada pasien. Di luar pulau-pulau utama, dokter yang meminta "
          "pemeriksaan pencitraan stroke sering tidak bisa mengandalkan laporan radiolog yang tepat waktu, sehingga "
          "kemampuan membaca citra yang dipelajari semasa kuliah langsung terbawa ke pelayanan. Sejauh penelusuran kami, "
          "belum ada survei terpublikasi tentang penilaian mahasiswa kedokteran Indonesia terhadap pendidikan "
          "radiologinya sendiri. Karena itu, pengukuran kondisi awal tersebut menjadi kegiatan pertama dalam pilot kami "
          "(Subbab III.H)."),
    ("fig", "masalah", "Dua sisi permasalahan. (a) Kepadatan radiolog, yang sekaligus menjadi pengajar radiologi, di Indonesia dibanding Uni Eropa {cite:yunus2024,brady2025}. "
                       "(b) Beban stroke nasional dan tekanan waktu dalam penanganannya {cite:kemkes2024,saver2006}."),
    ("p", "Stroke dipilih sebagai domain latihan karena di sinilah pembacaan citra paling menentukan luaran pasien. Stroke "
          "adalah penyebab kematian kedua terbanyak di dunia {cite:gbd2021} dan menyumbang 18,5% dari seluruh kematian di "
          "Indonesia {cite:kemkes2024,ski2023}. Setiap menit tanpa reperfusi, otak kehilangan sekitar 1,9 juta neuron "
          "{cite:saver2006}. Pencitraan otaklah yang membedakan infark dari perdarahan dan menentukan kelayakan "
          "trombolisis {cite:pnpk2019}. Di Indonesia, hanya sekitar 500 hingga 1.000 dari 150.000 hingga 200.000 pasien "
          "stroke per tahun yang mendapat trombolisis {cite:hidayat2025}, sehingga setiap keterlambatan membaca citra "
          "yang bisa dihindari menjadi penting. Tata laksana awal stroke juga tercantum sebagai kompetensi dokter umum "
          "dalam Standar Kompetensi Dokter Indonesia {cite:skdi2012}. Lulusan yang ragu membaca citra stroke dapat "
          "menunda keputusan terapi."),
    ("p", "Pemilihan MRI sebagai titik awal perlu dijelaskan, sebab CT tanpa kontras masih menjadi pemeriksaan standar "
          "stroke di Indonesia dan baru 372 dari sekitar 3.200 rumah sakit yang memiliki CT scan {cite:hidayat2025}. "
          "Ada tiga alasan. Pertama, MRI difusi jauh lebih baik dalam menampilkan infark akut. Pada perbandingan "
          "prospektif terhadap 356 pasien gawat darurat, sensitivitas MRI untuk stroke akut mencapai 83% dibanding 26% "
          "pada CT, sedangkan untuk perdarahan keduanya setara {cite:chalela2007}; neurolog Indonesia pun kini mendorong "
          "penggunaan MRI dalam jalur *code stroke* akut {cite:hidayat2025}. Kedua, infark dini sering tidak tampak pada "
          "CT sehingga mask CT tidak dapat dipakai untuk menilai mahasiswa secara adil, sedangkan mask DWI memberi kunci "
          "jawaban yang tegas. Ketiga, keterampilan yang dilatih (navigasi slice, windowing, teritori vaskular, "
          "delineasi) dapat dialihkan ke CT, dan tidak ada bagian platform yang terikat pada satu modalitas. Penambahan "
          "kasus CT termasuk dalam rencana lanjutan kami."),
    ("p", "Pada saat yang sama, mahasiswa Indonesia termasuk pengguna AI generatif paling aktif di dunia. Survei Chegg "
          "2025 terhadap 11.706 mahasiswa di 15 negara menempatkan Indonesia di urutan teratas, dengan 95% responden "
          "pernah memakai AI generatif untuk belajar {cite:chegg2025}. Untuk citra medis, chatbot umum belum layak "
          "menjadi pengajar. GPT-4V mengenali modalitas pencitraan dengan benar pada 100% kasus, tetapi hanya mengenali "
          "patologinya pada 35,2% kasus {cite:brin2025}. Evaluasi tujuh model visi-bahasa pada 180 gambar klinis "
          "melaporkan akurasi diagnosis 8,1% hingga 29,2% dengan tingkat halusinasi 74,4% {cite:vds2026}. Ironisnya, "
          "mahasiswa yang belum bisa membedakan jawaban benar dan salah justru paling mudah terpengaruh oleh jawaban yang "
          "terdengar meyakinkan. Hubungan sebab-akibat dari kondisi-kondisi ini dirangkum pada {fig:pohon}."),
    ("p", "Di sisi lain, terdapat peluang yang belum dimanfaatkan. Dataset publik Stroke Outcome Optimization Project "
          f"(SOOP) menyediakan MRI klinis dari {num(K.get('n_participants', 1505), 0)} pasien stroke, lesion mask buatan "
          f"ahli untuk {num(K.get('n_mask', 1456), 0)} di antaranya, skor NIHSS, dan skor modified Rankin scale "
          "{cite:absher2024}. Dari sudut pandang pengajaran, mask tersebut berfungsi sebagai kunci jawaban tingkat voxel: "
          "untuk setiap kasus, sistem tahu persis jaringan mana yang mengalami infark. Kunci jawaban seperti ini "
          "memungkinkan dua hal sekaligus, yaitu menilai jawaban mahasiswa secara objektif dan menambatkan respons AI "
          "pada fakta citra, bukan pada tebakan model."),
    ("fig", "pohon", "Pohon masalah pendidikan interpretasi MRI stroke. Kotak di bagian bawah adalah akar masalah yang ditangani SINAPS."),
    ("h2", "Rumusan Masalah"),
    ("p", "Berdasarkan uraian tersebut, penelitian ini menjawab tiga pertanyaan:"),
    ("bullet", "**RQ1.** Bagaimana merancang lingkungan latihan interpretasi MRI stroke yang memberi umpan balik objektif "
               "atas segmentasi dan jawaban mahasiswa tanpa bergantung pada kehadiran radiolog?"),
    ("bullet", "**RQ2.** Bagaimana model bahasa multimodal dapat berperan sebagai tutor interpretasi citra dengan risiko halusinasi yang tetap terkendali?"),
    ("bullet", "**RQ3.** Bagaimana urutan kasus dapat disesuaikan dengan kelemahan tiap mahasiswa sehingga latihan lebih efisien daripada modul statis?"),
    ("p", "RQ1 dijawab oleh modul penilaian (Subbab III.E), RQ2 oleh tutor yang berpijak pada fakta (Subbab III.G), dan "
          "RQ3 oleh modul personalisasi (Subbab III.F). Ketiga modul itu kemudian dibangun menjadi prototipe yang "
          "berjalan dan diuji dengan metrik yang ditetapkan di Bab III (Bab IV). Efek belajar ketiganya secara "
          "bersama-sama diukur dalam uji coba dengan mahasiswa yang direncanakan (Subbab III.H dan Bab V)."),
    ("h2", "Tujuan dan Kontribusi"),
    ("p", "Penelitian ini bertujuan merancang SINAPS (Sistem Interaktif Neuroradiologi Adaptif untuk Pembelajaran Stroke) "
          "dan menguji kelayakannya. SINAPS adalah asisten belajar berbasis AI yang memungkinkan mahasiswa kedokteran "
          "berlatih interpretasi MRI stroke secara mandiri, dengan penilaian otomatis, umpan balik yang spesifik terhadap "
          "jenis kesalahan, dan urutan kasus yang adaptif."),
    ("p", "Kontribusi makalah ini ada empat. Pertama, arsitektur tutor yang menjadikan kunci jawaban dan model segmentasi "
          "sebagai sumber fakta, sedangkan model bahasa hanya bertugas menjelaskan. Kedua, taksonomi kesalahan anotasi "
          "beserta metrik pembedanya sebagai dasar umpan balik formatif. Ketiga, model kompetensi interpretasi MRI stroke "
          "yang dipecah menjadi enam *knowledge component* (KC) untuk personalisasi. Keempat, serangkaian uji kelayakan "
          "pada data SOOP dengan kode yang dapat direproduksi, ditambah MVP yang berjalan daring dan pengujian langsung "
          "terhadap kode MVP tersebut: uji fungsional ujung ke ujung, akurasi jenis kesalahan, kebenaran pembaruan BKT, "
          "serta keandalan dan latensi tutor ketika mahasiswa meminta jawaban, mendesakkan jawaban keliru, atau "
          "menanyakan hal di luar data."),

    # =============================================================== BAB II
    ("h1", "Tinjauan Pustaka"),
    ("h2", "Pendidikan Radiologi dan Latihan Terarah"),
    ("p", "*White paper* European Society of Radiology menggambarkan radiologi sebagai ilmu yang dibutuhkan hampir setiap "
          "dokter, tetapi hanya mendapat porsi kecil dan terpecah dalam kurikulum sarjana {cite:esr2011}. Ericsson "
          "menunjukkan bahwa keahlian klinis tumbuh melalui latihan terfokus dengan umpan balik langsung, sedangkan "
          "paparan pasif tidak menghasilkan kemajuan yang sebanding {cite:ericsson2004}. Boutis, Pusic, dan rekan "
          "menerapkan prinsip ini pada ImageSim, platform interpretasi radiografi yang menyajikan ratusan kasus dengan "
          "umpan balik seketika. Akurasi diagnostik peserta yang kurang berpengalaman naik bertahap seiring bertambahnya "
          "kasus yang dikerjakan, dan kurva belajar tiap peserta dapat dipakai untuk menentukan kapan latihannya sudah "
          "cukup {cite:boutis2010,pusic2011}."),
    ("p", "Sistem semacam ini umumnya terbatas pada klasifikasi (normal atau abnormal) pada radiografi dua dimensi. Pada "
          "MRI volumetrik, mahasiswa juga perlu dinilai dalam hal lokalisasi dan delineasi, dan penilaian kedua tugas itu "
          "membutuhkan kunci jawaban tingkat voxel."),
    ("h2", "Latihan Delineasi dengan Umpan Balik Kuantitatif"),
    ("p", "Umpan balik berbasis tumpang-tindih spasial sudah dipakai dalam pendidikan onkologi radiasi. eContour "
          "menyediakan kasus tiga dimensi berbasis web dengan kontur rujukan dan telah digunakan lebih dari 13.000 "
          "pengguna dari 128 negara {cite:econtour2019}. Penerusnya, iContour, menambahkan latihan kontur dengan umpan "
          "balik visual dan skor Dice terhadap kontur ahli. Namun, uji acak terkontrol internasional pada residen "
          "onkologi radiasi tidak menemukan peningkatan akurasi kontur yang berarti dibanding pelatihan klinis standar, "
          "dan variasi antarresiden tetap tinggi {cite:icontour2025}."),
    ("p", "Analisis kualitatif dari kelompok yang sama terhadap residen pemula menunjukkan bahwa kesalahan kontur jauh "
          "dari acak: sebagian besar peserta mengontur terlalu sempit di wilayah yang sama dan melewatkan struktur yang "
          "sama {cite:orr2024}. Kedua temuan ini penting bagi rancangan kami. Skor Dice saja tidak cukup sebagai umpan "
          "balik formatif, karena peserta perlu tahu *mengapa* jawabannya salah. Karena kesalahan mengelompok menjadi "
          "jenis-jenis yang dapat dikenali, jenis kesalahan itu sendiri dapat dideteksi dan dipakai untuk memilih kasus "
          "berikutnya."),
    ("h2", "Sistem Tutor Cerdas dan Knowledge Tracing"),
    ("p", "Bloom melaporkan bahwa mahasiswa yang diajar secara privat berprestasi sekitar dua simpangan baku di atas "
          "mahasiswa di kelas konvensional {cite:bloom1984}. Sistem tutor cerdas (*intelligent tutoring system*, ITS) "
          "berupaya mendekati efek tersebut melalui perangkat lunak, dan meta-analisis Kulik dan Fletcher terhadap 50 "
          "evaluasi menemukan median efek 0,66 simpangan baku {cite:kulik2016}. Inti personalisasi pada banyak ITS adalah "
          "Bayesian Knowledge Tracing (BKT), yang memperlakukan penguasaan setiap keterampilan sebagai variabel laten dan "
          "memperbaruinya setiap kali pembelajar merespons {cite:corbett1994}. Pustaka pyBKT memudahkan estimasi "
          "parameter BKT dari log jawaban {cite:pybkt2021}, sedangkan *item response theory* (IRT) menyediakan kerangka "
          "untuk mengestimasi tingkat kesulitan butir dari data respons {cite:embretson2000}."),
    ("p", "Khusus di bidang profesi kesehatan, meta-analisis *e-learning* adaptif menemukan efek gabungan yang besar "
          "terhadap keterampilan (SMD 1,19; IK 95% 0,59 s.d. 1,79), meskipun kepastian buktinya rendah "
          "{cite:fontaine2019}. Sistem adaptif yang dicakupnya, seperti bank soal adaptif komersial, sebagian besar hanya "
          "mengatur urutan butir berupa teks atau gambar statis yang dinilai lewat pilihan ganda. Sepanjang penelusuran "
          "kami, BKT masih jarang diterapkan pada tugas pencitraan medis volumetrik, karena respons pada tugas tersebut "
          "sulit ditandai benar atau salah secara otomatis."),
    ("h2", "Model Bahasa Multimodal dalam Pendidikan Kedokteran"),
    ("p", "Model bahasa besar kini mampu lulus ujian lisensi dokter Amerika Serikat pada soal berbasis teks "
          "{cite:kung2023}, dan tutor berbasis model bahasa seperti Khanmigo sudah luas dipakai dalam pendidikan umum "
          "dengan pendekatan Sokratik {cite:khanmigo}. Dalam pengajaran radiologi, studi terkontrol pada 60 mahasiswa "
          "menemukan bahwa umpan balik LLM atas laporan pencitraan menaikkan nilai laporan di atas kelas kontrol, tetapi "
          "semua model yang diuji tetap berhalusinasi dalam kadar tertentu sehingga penulisnya menyarankan pengawasan "
          "pengajar {cite:chen2026}."),
    ("p", "Kemampuan model tersebut membaca citra medis masih jauh tertinggal. {fig:llm} memperlihatkan pola yang "
          "konsisten: akurasi tinggi pada tugas generik (modalitas, regio tubuh), lalu turun tajam pada tugas yang "
          "benar-benar klinis {cite:brin2025,vds2026}. Evaluasi tujuh model yang sama memuat temuan yang langsung "
          "relevan bagi rancangan kami: ketika konteks klinis diberikan, akurasi naik dari 10,6% menjadi 24,0% dan "
          "halusinasi turun dari 83,5% menjadi 67,4% {cite:vds2026}. Artinya, model bahasa bekerja lebih baik bila "
          "ditambatkan pada fakta, dan fakta terkuat yang dapat kami berikan adalah hasil segmentasi yang terukur. "
          "Di sisi teks, *retrieval-augmented generation* (RAG) melengkapi hal ini dengan menarik rujukan tepercaya ke "
          "dalam konteks {cite:lewis2020}."),
    ("p", "Penambatan pada fakta belum tentu cukup untuk sebuah tutor. LLM cenderung mengiyakan pengguna: GPT-4o dan "
          "GPT-4 menuruti permintaan medis yang tidak logis pada seluruh 50 *prompt* uji, dan hanya *prompt* yang "
          "secara eksplisit mengizinkan penolakan yang membuat tingkat penolakan melampaui 60% {cite:chen2025}. "
          "Mahasiswa yang dengan yakin mengusulkan jawaban keliru adalah bentuk tekanan seperti ini, sehingga kami "
          "mengujinya secara langsung (Subbab III.G)."),
    ("fig", "llm", "Akurasi model visi-bahasa menurun ketika tugas makin spesifik. Kiri: GPT-4V pada 230 gambar instalasi gawat darurat {cite:brin2025}. "
                   "Kanan: rentang akurasi diagnosis tujuh model pada 180 gambar {cite:vds2026}."),
    ("h2", "Segmentasi Lesi Stroke Otomatis"),
    ("p", "Segmentasi infark akut pada DWI telah menjadi tolok ukur tersendiri. Kompetisi ISLES 2022 merilis 400 kasus "
          "multisenter dengan anotasi ahli {cite:isles2022}. Kerangka nnU-Net, yang mengonfigurasi sendiri praproses dan "
          "arsitekturnya, mendasari banyak solusi pemenang pada berbagai kompetisi segmentasi medis {cite:isensee2021}. "
          "Gabungan solusi terbaik ISLES 2022 kemudian dirilis sebagai DeepISLES dan divalidasi pada 1.685 pasien "
          "eksternal {cite:deepisles2025}. Untuk mengevaluasi segmentasi, Taha dan Hanbury serta pedoman Metrics Reloaded "
          "menganjurkan kombinasi metrik tumpang-tindih (Dice), metrik jarak batas (Hausdorff persentil ke-95), dan "
          "metrik per objek, karena satu metrik saja dapat menyesatkan pada lesi kecil {cite:taha2015,maierhein2024}. "
          "Selama ini model-model tersebut diarahkan untuk mendukung keputusan klinis. Kami memanfaatkannya untuk "
          "pengajaran, yaitu untuk menilai dan membimbing mahasiswa."),
    ("h2", "Posisi Penelitian"),
    ("p", "{tab:banding} membandingkan SINAPS dengan solusi yang sudah ada. Atlas daring seperti Radiopaedia memiliki "
          "banyak kasus tetapi bersifat pasif {cite:radiopaedia}. Viewer medis seperti 3D Slicer dan OHIF menyediakan "
          "perangkat lengkap tetapi tidak mengajar {cite:fedorov2012,ohif2020}. ImageSim sudah menerapkan latihan "
          "terarah, tetapi hanya untuk klasifikasi radiografi 2D {cite:boutis2010}. eContour dan iContour menilai kontur "
          "secara kuantitatif, tetapi umpan baliknya berhenti pada skor dan urutan kasusnya tidak adaptif "
          "{cite:econtour2019,icontour2025}. Bank soal adaptif mempersonalisasi urutan tetapi hanya menilai jawaban "
          "pilihan ganda {cite:fontaine2019}. Chatbot umum mudah diakses tetapi tidak memiliki kunci jawaban dan "
          "cenderung mengiyakan mahasiswa {cite:chen2025}. Tabel yang sama juga menunjukkan kekurangan SINAPS: berbeda "
          "dengan ImageSim dan iContour, SINAPS belum diuji pada pembelajar. Karena itu, evaluasi pada Subbab III.H "
          "menjadi bagian dari rancangan, bukan tambahan di akhir."),
    ("p", "{fig:posisi} memetakan solusi-solusi tersebut pada dua sumbu, yaitu sejauh mana umpan balik bertumpu pada kunci "
          "jawaban citra dan sejauh mana latihan menyesuaikan diri dengan mahasiswa. Kedua sumbu ini dipilih karena "
          "mencerminkan dua hal yang dilakukan dosen dalam bimbingan privat: mencocokkan jawaban dengan citra, lalu "
          "memutuskan kasus apa yang perlu dilihat mahasiswa berikutnya. Perangkat di kuadran kiri atas melakukan yang "
          "pertama, perangkat di kanan bawah melakukan yang kedua, dan perangkat di kiri bawah tidak melakukan keduanya. "
          "SINAPS berada di kuadran kanan atas yang belum ditempati perangkat mana pun."),
    ("fig", "posisi", "Peta posisi perangkat belajar interpretasi citra. Sumbu horizontal: adaptivitas; sumbu vertikal: umpan balik yang bertumpu pada kunci jawaban citra."),
    ("p", "Dari tinjauan ini diturunkan tiga syarat rancangan. Pertama, umpan balik harus dihitung dari citra itu sendiri. "
          "Skor Dice memberi tahu seberapa besar jawaban mahasiswa tumpang-tindih dengan kunci, tetapi tidak menunjukkan "
          "wilayah mana yang terlewat atau penyebabnya, dan uji iContour mengisyaratkan bahwa skor saja hampir tidak "
          "mengubah cara residen mengontur {cite:icontour2025}. Kedua, urutan latihan harus mengikuti mahasiswa. "
          "*E-learning* adaptif berefek besar terhadap keterampilan {cite:fontaine2019}, tetapi tidak satu pun perangkat "
          "yang kami tinjau mengadaptasi urutan kasus volumetrik, karena jawaban pada tugas ini belum dapat dinilai "
          "otomatis. Begitu setiap sapuan kuas dinilai terhadap lesion mask, setiap percobaan menjadi observasi yang "
          "dapat dipakai model *knowledge tracing*. Ketiga, model bahasa harus tetap dekat dengan fakta terukur. Model "
          "visi-bahasa lebih jarang keliru bila diberi konteks klinis {cite:vds2026}, tetapi masih mengalah pada pengguna "
          "yang yakin {cite:chen2025}. Karena itu, tutor hanya boleh menjelaskan temuan yang sudah dihitung oleh modul "
          "segmentasi dan penilaian."),
    ("p", "Perangkat yang ada baru memenuhi satu atau dua dari ketiga syarat tersebut, belum pernah ketiganya. Memenuhi "
          "ketiga syarat sekaligus adalah tujuan metodologi pada Bab III."),
    ("table", "banding", "Perbandingan SINAPS dengan solusi yang sudah ada",
     ["Kemampuan", "Radiopaedia / e-modul", "3D Slicer / OHIF", "ImageSim", "eContour / iContour", "Chatbot LLM", "SINAPS"],
     [["Navigasi MRI 3D (slice, W/L, kuas)", "Sebagian", "Ya", "Tidak", "Ya", "Tidak", "Ya"],
      ["Penjelasan bahasa alami", "Statis", "Tidak", "Statis", "Statis", "Ya", "Ya"],
      ["Penilaian jawaban tingkat voxel", "Tidak", "Tidak", "Tidak", "Ya (Dice)", "Tidak", "Ya"],
      ["Umpan balik jenis kesalahan", "Tidak", "Tidak", "Sebagian", "Tidak", "Tidak andal", "Ya"],
      ["Urutan kasus adaptif", "Tidak", "Tidak", "Sebagian", "Tidak", "Tidak", "Ya"],
      ["Jawaban AI terikat fakta citra", "n/a", "n/a", "n/a", "n/a", "Tidak", "Ya"],
      ["Efek diuji pada pembelajar", "Tidak", "Tidak", "Ya", "Ya (RCT)", "Sebagian", "Direncanakan"]],
     [124, 60, 56, 46, 60, 52, 56], True, "lcccccc"),

    # =============================================================== BAB III
    ("h1", "Metodologi"),
    ("h2", "Gambaran Umum dan Alur Belajar"),
    ("p", "SINAPS dibangun di atas satu siklus latihan terarah ({fig:siklus}). Sistem memilih kasus yang menyasar "
          "kompetensi terlemah mahasiswa. Mahasiswa membuka MRI di peramban, menggulir slice, mengatur window/level, "
          "menandai lesi dengan kuas, lalu menjawab tiga pertanyaan singkat: sekuens mana yang sedang dilihat, di "
          "hemisfer mana lesinya, dan berapa nilai ADC relatifnya. Jawaban tersebut dinilai otomatis terhadap lesion mask. Tutor kemudian menjelaskan letak kesalahan "
          "secara spesifik, dan estimasi penguasaan setiap kompetensi diperbarui untuk memilih kasus berikutnya."),
    ("fig", "siklus", "Siklus latihan SINAPS. Langkah 3 dan 5 berjalan otomatis sehingga setiap kasus menghasilkan umpan balik tanpa menunggu dosen."),
    ("p", "Selama berlatih, mahasiswa dapat menekan tombol Capture untuk mengirim slice yang sedang tampil ke tutor "
          "sebagai konteks pertanyaan terbuka, sehingga yang ditanyakan adalah persis yang sedang dilihat. {tab:fitur} "
          "merangkum fitur belajar dalam siklus ini beserta modul yang menjalankannya."),
    ("h2", "Arsitektur Sistem"),
    ("p", "SINAPS terdiri atas enam modul ({fig:arsitektur}). Viewer web dibangun di atas Cornerstone3D, pustaka inti "
          "OHIF Viewer {cite:ohif2020}, sehingga navigasi slice, pengukuran, dan segmentasi berjalan di peramban tanpa "
          "instalasi. Semua permintaan melewati orkestrator FastAPI yang mengelola sesi, antrean inferensi, dan pencatatan "
          "log. Di belakangnya, empat modul bertugas menyimpan kasus, menghasilkan fakta citra, menilai jawaban, dan "
          "memilih kasus. Tutor LLM berada di ujung rantai dan hanya menerima keluaran modul lain, sehingga tidak pernah "
          "menjadi satu-satunya sumber kebenaran. Dosen mendapat dasbor kelas yang menampilkan peta penguasaan KC setiap "
          "mahasiswa dan jenis kesalahan yang paling sering muncul, serta antarmuka verifikasi untuk menyetujui label dan "
          "kasus baru sebelum masuk ke bank kasus. Pada MVP, viewer dan dasbor dibangun dengan React, orkestrator berjalan "
          "sebagai fungsi Python di Vercel, dan log belajar disimpan di basis data Postgres."),
    ("p", "Cara kerja antarmodul dapat diikuti dari satu kali pengumpulan jawaban. Setelah mahasiswa selesai menandai "
          "lesi, viewer mengirim mask sapuan kuas ke orkestrator. Modul penilaian membandingkannya dengan kunci jawaban "
          "dan mengembalikan skor Dice, recall per lesi, galat volume, dan jarak Hausdorff persentil ke-95, disertai "
          "jenis kesalahan seperti lesi kecil yang terlewat atau jawaban yang terlalu sempit. Modul adaptasi mengubah "
          "hasil ini menjadi pembaruan penguasaan untuk kompetensi yang dicakup kasus tersebut. Baru setelah itu tutor "
          "menerima temuan terstruktur dan menulis penjelasannya. Setiap langkah dicatat dalam log berpseudonim, sehingga "
          "dosen dapat menelusuri mengapa seorang mahasiswa menerima umpan balik tertentu."),
    ("h2", "Data dan Bank Kasus"),
    ("p", "Bank kasus diambil dari SOOP (OpenNeuro ds004889, lisensi CC0) {cite:absher2024}. Setiap subjek memiliki citra "
          "T1, FLAIR, DWI (TRACE), dan ADC, serta lesion mask dalam ruang DWI. Data klinisnya tersedia sebagian: NIHSS "
          f"untuk {num(K.get('n_nihss', 1106), 0)} pasien dan modified Rankin scale saat pulang untuk "
          f"{num(K.get('n_rankin', 738), 0)} pasien. {{fig:mri}} menampilkan satu kasus nyata. Lesi tampak terang pada DWI "
          "dan gelap pada ADC, pola restriksi difusi khas infark akut yang harus dipahami mahasiswa sebelum menarik "
          "kesimpulan apa pun. Bank kasus MVP memuat 36 subjek: 30 subjek dipilih merata pada skor modified Rankin 0 "
          "hingga 6, lalu ditambah agar setiap tingkat kesulitan memiliki minimal 10 kasus. Tiga di antaranya dipakai "
          "sebagai contoh di modul belajar sehingga tidak ikut dinilai, dan tidak satu pun subjek bank dipakai untuk "
          "melatih model segmentasi."),
    ("table", "fitur", "Fitur belajar SINAPS",
     ["Fitur", "Yang dilakukan mahasiswa", "Modul"],
     [["Viewer MRI interaktif", "menggulir slice, mengatur window/level, membandingkan DWI, ADC, FLAIR", "Viewer web"],
      ["Kuas anotasi lesi", "menandai lesi langsung pada citra", "Viewer web"],
      ["Pertanyaan kasus", "menjawab soal sekuens (K1), hemisfer dan titik lesi (K2), ADC relatif (K3)", "Penilaian"],
      ["Skor dan jenis kesalahan", "melihat Dice, recall per lesi, dan jenis kesalahan", "Penilaian"],
      ["Kasus adaptif", "mengerjakan kasus untuk KC terlemah pada tingkat kesulitan yang sesuai", "Personalisasi (BKT)"],
      ["Peta penguasaan KC", "melihat estimasi penguasaan keenam KC", "Personalisasi (BKT)"],
      ["Capture", "mengirim slice yang tampil sebagai konteks pertanyaan terbuka", "Tutor LLM"],
      ["Mode Sokratik", "dibimbing dengan pertanyaan tanpa diberi jawaban", "Tutor LLM"],
      ["Mode penjelasan", "membaca pembahasan lengkap setelah kasus selesai", "Tutor LLM"],
      ["Mode rujukan", "membaca kutipan PNPK dan SKDI yang relevan", "Tutor LLM + RAG"],
      ["Modul belajar", "mempelajari materi per KC dengan contoh kasus dan kuis", "Viewer web"],
      ["Dasbor dosen", "(dosen) memantau penguasaan, kesalahan tersering, tugas, audit tutor", "Orkestrator"]],
     [62, 120, 70], False, "lll"),
    ("p", f"Untuk menyusun tingkat kesulitan, kami menghitung morfologi seluruh {num(K.get('n_mask', 1456), 0)} lesion "
          f"mask ({{fig:kohort}}). Median volume lesi akut adalah {num(K.get('vol_median', 0))} ml (rentang interkuartil "
          f"{num(K.get('vol_q1', 0))} s.d. {num(K.get('vol_q3', 0))} ml), dan {pct(K.get('frac_vol_lt1', 0))} pasien "
          "memiliki lesi lebih kecil dari 1 ml yang mudah terlewat oleh pemula. Lesi multifokal ternyata justru menjadi "
          f"kelaziman: {pct(K.get('frac_multifocal_sig', 0))} pasien memiliki lebih dari satu fokus bermakna (minimal "
          "0,1 ml). Aturan satu ambang, misalnya menganggap semua kasus multifokal sebagai sulit, akan menumpuk sebagian "
          "besar bank kasus pada satu tingkat. Karena itu kami mendefinisikan indeks kesulitan komposit:"),
    ("eq", "D = −log₁₀ V + log₂ F", 1),
    ("p", "dengan *V* adalah volume lesi total (ml) dan *F* jumlah fokus bermakna. Lesi yang makin kecil dan makin "
          "tersebar menghasilkan *D* yang makin besar. Bank kasus dibagi pada tersil *D* sehingga ketiga tingkat berukuran "
          "sama. Tingkat mudah didominasi lesi tunggal berukuran sedang hingga besar (median "
          f"{num(TK.get('mudah', {}).get('vol_median', 0))} ml, {num(TK.get('mudah', {}).get('foci_median', 0), 0)} fokus), "
          f"tingkat sedang berisi lesi kecil dengan sedikit fokus (median {num(TK.get('sedang', {}).get('vol_median', 0))} ml, "
          f"{num(TK.get('sedang', {}).get('foci_median', 0), 0)} fokus), dan tingkat sulit berisi pola multifokal yang "
          f"tersebar (median {num(TK.get('sulit', {}).get('foci_median', 0), 0)} fokus)."),
    ("p", "Indeks ini baru merupakan estimasi awal (*a priori*). Setelah log jawaban terkumpul, kesulitan setiap kasus akan "
          "dikalibrasi ulang dengan model Rasch dari kerangka IRT {cite:embretson2000}. Volume lesi juga berkorelasi "
          f"sedang dengan NIHSS (Spearman {num(K.get('spearman_vol_nihss', 0), 2)}, n = {K.get('n_vol_nihss', 0)}), sehingga "
          "kasus-kasus ini juga dapat melatih penalaran klinis-radiologis, misalnya menghubungkan ukuran lesi dengan "
          "beratnya defisit neurologis."),
    ("fig", "arsitektur", "Arsitektur SINAPS. Modul hijau bersifat deterministik dan dapat diaudit; modul oranye (LLM) hanya "
                          "menjelaskan fakta yang disediakan modul hijau.", True),
    ("fig", "mri", "Kasus nyata SOOP (sub-1010, NIHSS 27): (a) DWI, (b) ADC, (c) lesion mask sebagai kunci jawaban, "
                   "(d) contoh jawaban mahasiswa yang terlalu sempit beserta skornya. Orientasi radiologis (sisi kiri pasien di sisi kanan gambar).", True),
    ("fig", "kohort", f"Stratifikasi kesulitan {num(K.get('n_mask', 1456), 0)} kasus SOOP. (a) Volume total terhadap jumlah fokus bermakna; "
                      "garis putus-putus menandai batas tersil indeks *D*. (b) Median volume dan jumlah fokus pada tiap tingkat."),
    ("h2", "Modul Visi: Segmentasi dan Temuan Terstruktur"),
    ("p", "Modul visi mengubah sebuah mask menjadi temuan terstruktur dalam format JSON: volume, jumlah fokus, hemisfer, "
          "slice dengan lesi terbesar, ADC relatif tiap fokus, dan teritori arteri. Teritori dirancang ditentukan dengan "
          "meregistrasikan citra ke atlas digital teritori arteri yang dibangun dari 1.298 pasien stroke {cite:liu2023}, "
          "memakai registrasi diffeomorfik simetris ANTs SyN {cite:avants2008}, lalu diperiksa radiolog pada sampel "
          "kasus. Registrasi ini belum masuk MVP, sehingga temuan terstruktur menuliskan teritori sebagai \"tidak "
          "diketahui\" dan K4 belum dinilai."),
    ("p", "Perlu ditegaskan bahwa dalam MVP, mahasiswa **selalu** dinilai terhadap lesion mask buatan ahli, tidak pernah "
          "terhadap prediksi model. Model segmentasi memiliki dua tugas lain. Pertama, melakukan pra-anotasi kasus baru "
          "yang belum memiliki mask, misalnya kasus lokal dari rumah sakit pendidikan mitra di masa depan; prediksi ini "
          "baru masuk bank kasus setelah dikoreksi dan disetujui radiolog melalui dasbor verifikasi. Kedua, berperan "
          "sebagai pembaca kedua dalam mode pembahasan, sehingga mahasiswa dapat melihat di mana model dan ahli berbeda "
          "pendapat; pada MVP prediksi model dapat ditampilkan di atas kunci saat tinjau ulang. nnU-Net dengan masukan "
          "DWI dan ADC {cite:isensee2021}, dengan DeepISLES sebagai pembanding {cite:deepisles2025}, tetap menjadi "
          "rencana pengembangan."),
    ("p", "Untuk menguji kelayakan sejak awal, kami membandingkan dua baseline pada 30 subjek sampel SOOP yang dipilih "
          "merata pada skor modified Rankin 0 hingga 6. Ketiga puluh pasien ini hanya dipakai sebagai data uji. Baseline "
          "pertama adalah aturan ambang: sebuah voxel dianggap lesi bila intensitas DWI-nya lebih dari 2 simpangan baku "
          "di atas rerata otak dan nilai ADC-nya di bawah 0,8 kali median ADC otak. Skala ADC ternyata berbeda antar-"
          "pemindai (median otak berkisar sekitar 3.800 hingga 9.800 satuan mentah), sehingga normalisasi relatif mutlak "
          "diperlukan. Baseline kedua adalah U-Net 2.5D (tiga slice DWI dan ADC yang bertetangga sebagai enam kanal "
          f"masukan) yang dilatih pada {sd('n_latih', 250)} pasien SOOP lain yang dipilih acak "
          f"({num(sd('n_slice_latih', 0), 0)} slice) selama {sd('epoch', 30)} epoch pada resolusi {sd('res', 128)} piksel, "
          "tanpa satu pun pasien uji ikut dalam pelatihan."),
    ("p", f"Pada pasien uji, U-Net mencapai rerata Dice {num(sd('dice_unet_mean', 0), 2)} ({ci('dice_unet')}, "
          f"bootstrap per pasien), jauh di atas aturan ambang yang hanya {num(sd('dice_rule_mean', 0), 2)} "
          f"({ci('dice_rule')}); contohnya ditampilkan pada {{fig:contoh_seg}}. Pada lesi minimal 5 ml rerata Dice "
          f"U-Net adalah {num(sd('dice_unet_vol_ge5', 0), 2)}, sedangkan pada lesi di bawah 5 ml turun menjadi "
          f"{num(sd('dice_unet_vol_lt5', 0), 2)}. Untuk MVP, arsitektur yang sama dilatih ulang di GPU Kaggle pada "
          f"{num(FS.get('n_train', 1170), 0)} pasien ({num(FS.get('n_slice', 0), 0)} slice, {FS.get('epoch', 30)} epoch, "
          f"sekitar {num(FS.get('menit', 50), 0)} menit) dan dievaluasi pada 36 kasus bank yang tidak ikut dilatih "
          "(Subbab IV.B)."),
    ("h2", "Modul Penilaian Otomatis"),
    ("p", "Segmentasi mahasiswa *P* dibandingkan dengan kunci jawaban *G*. Ukuran utamanya adalah koefisien Dice:"),
    ("eq", "Dice(P, G) = 2|P ∩ G| / (|P| + |G|)", 2),
    ("p", "Dice saja tidak cukup sebagai umpan balik. Dua jawaban dengan Dice yang sama bisa salah karena alasan yang "
          "sangat berbeda, dan pada lesi multifokal nilai Dice didominasi oleh lesi terbesar {cite:maierhein2024}. Karena "
          "itu modul penilaian menghitung empat metrik: Dice, recall per lesi (proporsi fokus lesi yang tersentuh), galat "
          "volume relatif, dan jarak Hausdorff persentil ke-95 (HD95) {cite:taha2015}. Keempatnya dipetakan ke lima jenis "
          "kesalahan yang umum pada pemula, yaitu hampir benar, terlalu luas (ikut menandai edema atau tepi), terlalu "
          "sempit (hanya inti lesi), lesi kecil terlewat, dan salah lokasi."),
    ("fig", "contoh_seg", "Contoh keluaran pada slice dengan lesi terbesar dari satu kasus supratentorial. Garis hijau adalah lesion mask; isian berwarna adalah prediksi tiap metode."),
    ("p", "Karena anotasi mahasiswa yang sebenarnya belum tersedia, kelima jenis kesalahan tersebut kami simulasikan pada "
          f"mask {P.get('n_subjek', 30)} subjek sampel, {P.get('ulang', 4)} kali per jenis per subjek dengan tingkat "
          f"keparahan acak ({P.get('n_kasus', 600)} anotasi sintetis). Sebagai contoh, jawaban terlalu sempit dibuat dengan "
          "mengikis mask 2 hingga 4 voxel, sedangkan salah lokasi dibuat dengan menggeser mask 8 hingga 16 voxel ke arah "
          f"acak. {{fig:penilaian}} memperlihatkan bahwa setiap jenis kesalahan meninggalkan jejak metrik yang khas. Lesi "
          "kecil yang terlewat, misalnya, tetap memperoleh Dice tinggi "
          f"({num(P['per_jenis']['lesi_terlewat']['dice'], 2) if P else '-'}) tetapi recall per lesinya hanya "
          f"{num(P['per_jenis']['lesi_terlewat']['recall_lesi'], 2) if P else '-'}. Sistem yang hanya melaporkan Dice "
          "tidak akan pernah menangkap kesalahan ini, dan inilah celah yang ditinggalkan platform kontur berbasis satu "
          "skor."),
    ("p", "Setiap jawaban dipetakan ke jenis kesalahannya oleh aturan keputusan sederhana dan transparan dengan lima ambang "
          "metrik. Agar aturan tidak dinilai pada data yang dipakai untuk menyetelnya, ambang disetel pada anotasi 24 "
          "subjek dan diuji pada 6 subjek sisanya, bergiliran dalam lima fold tingkat subjek. Pada subjek yang belum "
          f"pernah dilihat, aturan ini mengenali jenis kesalahan dengan akurasi {pct(P.get('akurasi_aturan', 0))} "
          f"({ci('akurasi_aturan', persen=True)}, bootstrap per subjek), dibanding {pct(P.get('akurasi_dice_saja', 0))} "
          f"({ci('akurasi_dice_saja', persen=True)}) pada pengklasifikasi *nearest-centroid* yang hanya melihat Dice. Recall "
          f"tertinggi dicapai jenis terlalu luas ({pct(P.get('recall_per_jenis', {}).get('over', 0))}) dan terendah pada "
          f"lesi terlewat ({pct(P.get('recall_per_jenis', {}).get('lesi_terlewat', 0))}), yang sering dilabeli terlalu "
          "sempit oleh aturan: ketika satu fokus kecil terlewat, metriknya menyerupai segmentasi yang sangat kurang."),
    ("p", "Hasil ini memiliki batas yang jelas. Kesalahan sintetis berasal dari operasi geometris yang sama (pengikisan, "
          "pelebaran, pergeseran, penghapusan fokus) yang memang dirancang untuk dipisahkan oleh aturan, sedangkan "
          f"mahasiswa sungguhan mencampur beberapa jenis kesalahan dalam satu jawaban. Karena itu angka "
          f"{pct(P.get('akurasi_aturan', 0))} kami baca sebagai batas atas yang menunjukkan bahwa metriknya cukup "
          "informatif, bukan sebagai akurasi yang akan dialami mahasiswa. Ambang akan dikalibrasi ulang pada anotasi "
          "mahasiswa sungguhan, dan kesesuaian dengan penilaian radiolog (Cohen κ) menjadi salah satu target pada "
          "{tab:evaluasi}."),
    ("p", "Jawaban nonsegmentasi (teritori arteri, hemisfer, perkiraan usia lesi) dinilai dengan mencocokkannya pada "
          "temuan terstruktur. Untuk jawaban esai singkat, LLM berperan sebagai penilai dengan rubrik tertutup yang "
          "diisi dari temuan terstruktur kasus tersebut."),
    ("fig", "penilaian", f"Jejak metrik lima jenis kesalahan anotasi (median dari {P.get('n_subjek', 30)} subjek). Hijau berarti baik dan oranye berarti buruk untuk metrik tersebut."),
    ("h2", "Modul Personalisasi"),
    ("p", "Interpretasi MRI stroke kami pecah menjadi enam KC yang tersusun berjenjang ({tab:kc}). Setiap jawaban pada "
          "sebuah KC memperbarui estimasi penguasaan KC tersebut melalui BKT {cite:corbett1994}. "
          "Misalkan *L* adalah peluang mahasiswa sudah menguasai sebuah KC, *G* peluang menebak dengan benar, *S* peluang "
          "tergelincir (*slip*), dan *T* peluang belajar setelah satu kesempatan latihan. Setelah respons benar:"),
    ("eq", "L′ = L(1 − S) / [L(1 − S) + (1 − L)G]", 3),
    ("p", "kemudian peluang belajar ditambahkan sebelum latihan berikutnya:"),
    ("eq", "Lₜ₊₁ = L′ + (1 − L′)T", 4),
    ("p", "Untuk respons salah, faktor (1 − *S*) diganti *S* dan *G* diganti (1 − *G*). Batas benar atau salah untuk "
          "setiap KC berasal dari modul penilaian, misalnya Dice minimal 0,6, recall per lesi 1, dan galat volume paling banyak +25% untuk KC delineasi. "
          "Pemilih kasus mengambil KC dengan estimasi penguasaan terendah yang prasyaratnya sudah dikuasai (estimasi "
          "minimal 0,95), lalu memilih kasus pada tingkat kesulitan yang sesuai. Pada MVP, satu kasus memuat soal K1, K2, "
          "K3, dan K6 sekaligus sehingga keempat KC diperbarui setiap kali jawaban dikirim. KC sasaran menentukan "
          "tingkat kesulitan kasus berikutnya (mudah bila penguasaannya di bawah 0,4, sedang di bawah 0,7, dan sulit untuk "
          "nilai lainnya), dan mahasiswa juga dapat memilih latihan terarah untuk satu KC dari modul belajar. Parameter BKT "
          "diawali dengan nilai dari literatur dan diestimasi ulang dari log jawaban dengan pyBKT setelah pilot "
          "{cite:pybkt2021}."),
    ("p", "SOOP tidak menyediakan kunci jawaban untuk semua KC secara langsung, sehingga sumber kunci setiap KC kami "
          "nyatakan secara eksplisit. K1, K2, dan K6 berasal langsung dari metadata sekuens dan lesion mask. K3 "
          "(restriksi sejati versus *T2 shine-through*) dapat diturunkan secara semi-otomatis karena SOOP menyertakan peta "
          "ADC: wilayah terang pada DWI dengan ADC relatif rendah merupakan restriksi sejati, sedangkan wilayah terang "
          "pada DWI dengan ADC normal atau tinggi dijadikan kasus pengecoh. K4 berasal dari registrasi atlas. K5 (usia "
          "lesi) tidak memiliki label waktu onset di SOOP, sehingga akan dianotasi oleh radiolog bersertifikat dari rumah "
          "sakit pendidikan mitra (lihat risiko ketersediaan tenaga pada {tab:risiko}) berdasarkan pola ketidaksesuaian "
          "DWI-FLAIR, penanda tervalidasi untuk mengenali lesi berusia kurang dari 4,5 jam {cite:thomalla2011}. Semua "
          "label semi-otomatis diperiksa radiolog pada sampel acak sebelum dipakai."),
    ("p", f"Manfaat kebijakan ini diuji dengan mensimulasikan {num(B.get('N', 1000) if B else 1000, 0)} mahasiswa "
          "sintetis dengan parameter belajar acak. Pembelajaran sebuah KC diasumsikan jauh lebih lambat bila prasyaratnya "
          "belum dikuasai, sesuai gagasan jenjang kompetensi. Dalam simulasi ini ({fig:bkt}), setelah 60 kasus kebijakan "
          f"adaptif menghasilkan rata-rata {pct(B_adap[-1])} KC dikuasai, dibanding {pct(B_acak[-1])} pada urutan acak. "
          "Proporsi mahasiswa yang menguasai keenam KC naik dari "
          f"{pct(B['acak']['tuntas_akhir']) if B else '-'} menjadi {pct(B['adaptif']['tuntas_akhir']) if B else '-'}."),
    ("fig", "bkt", "Simulasi penguasaan KC terhadap jumlah kasus: urutan acak dibanding pemilihan adaptif berbasis BKT."),
    ("table", "kc", "Knowledge component interpretasi MRI stroke",
     ["KC", "Kompetensi", "Bukti yang dinilai (sumber kunci jawaban)"],
     [["K1", "Mengenali sekuens (T1, FLAIR, DWI, ADC)", "pilihan ganda (metadata)"],
      ["K2", "Mendeteksi hiperintensitas DWI", "klik titik pada lesi (mask)"],
      ["K3", "Membedakan restriksi sejati dari T2 shine-through dengan ADC", "ya atau tidak + slice ADC (ADC relatif, diperiksa)"],
      ["K4", "Mengenali teritori arteri", "pilihan teritori (registrasi atlas)"],
      ["K5", "Memperkirakan usia lesi (pola DWI dan FLAIR)", "kategori waktu (anotasi radiolog)"],
      ["K6", "Mendelineasi seluruh lesi", "Dice, recall per lesi, HD95 (mask)"]],
     [22, 123, 108], False, "cll"),
    ("p", "Besarnya selisih tersebut bergantung pada asumsi kami, sehingga simulasi diulang pada dua belas skenario. Laju "
          "belajar tanpa prasyarat yang dikuasai diatur 25%, 50%, 75%, atau 100% dari laju normal (100% berarti prasyarat "
          "sama sekali tidak berpengaruh), masing-masing dikombinasikan dengan tiga tingkat *guess* dan *slip*. Kebijakan "
          f"adaptif unggul di semua skenario, dengan selisih {num(100 * SENS_MIN, 0)} hingga {num(100 * SENS_MAX, 0)} poin "
          "persentase KC dikuasai setelah 60 kasus. Selisih terkecil terjadi ketika prasyarat tidak berpengaruh dan "
          "tebakan sering terjadi, karena satu-satunya keuntungan yang tersisa adalah tidak membuang latihan pada KC yang "
          "sudah dikuasai. Oleh karena itu, simulasi ini kami baca sebagai bukti arah efek beserta kisaran yang masuk "
          "akal, bukan estimasi titik. Efek sebenarnya akan diukur dalam uji coba dengan mahasiswa."),
    ("h2", "Tutor LLM yang Berpijak pada Fakta Citra"),
    ("p", "Tutor memakai model multimodal OpenAI, GPT-5.6 Luna, melalui API-nya {cite:openai2026}. Model ini dipilih "
          "karena menerima masukan gambar dengan latensi rendah dan biaya per token yang terjangkau untuk skala kelas. "
          "Setiap permintaan ke model dirakit dari empat bagian: gambar slice dari Capture, temuan terstruktur dari modul "
          "visi dan penilaian, kutipan rujukan hasil RAG, dan profil mahasiswa (tahun studi dan KC terlemah). Korpus RAG "
          "berisi rujukan berbahasa Indonesia yang terkait kurikulum, yaitu Pedoman Nasional Pelayanan Kedokteran (PNPK) "
          "tata laksana stroke dan Standar Kompetensi Dokter Indonesia (SKDI), ditambah materi ajar dari dosen mitra "
          "{cite:pnpk2019,skdi2012,lewis2020}. Selama kunci jawaban belum dibuka, fakta yang dikirim ke model hanya "
          "berisi vinyet klinis dan status \"terkunci\", sehingga tutor memang tidak memegang lokasi lesi yang bisa "
          "dibocorkan. Setiap jawaban tutor disimpan di log audit bersama hasil pemeriksa fakta otomatis untuk ditinjau "
          "dosen."),
    ("p", "*System prompt* melarang model menyebut temuan apa pun yang tidak ada dalam data terstruktur. Ketika mahasiswa "
          "bertanya tentang hal di luar data tersebut, model diminta menyatakan tidak tahu dan menyarankan bertanya "
          "kepada dosen. Pilihan rancangan ini mengikuti temuan bahwa konteks klinis mengurangi halusinasi pada model "
          "visi {cite:vds2026}."),
    *P_LLM,
    ("p", "Tutor bekerja dalam tiga mode. Mode Sokratik (bawaan) menjawab dengan pertanyaan penuntun alih-alih langsung "
          "memberikan jawaban. Mode penjelasan memberikan pembahasan lengkap setelah mahasiswa menyelesaikan kasus. Mode "
          "rujukan menambahkan kutipan dari pedoman. Ragam bahasanya menyesuaikan pengguna, dari mahasiswa praklinik "
          "hingga dokter internsip. Tampilan tutor pada MVP ditunjukkan di Subbab IV.A."),
    ("h2", "Rencana Implementasi, Biaya, dan Evaluasi"),
    ("p", "Implementasi berjalan dalam dua tahap. Tahap MVP (Oktober 2026) menghasilkan prototipe yang berjalan: bank "
          "kasus dari SOOP, model segmentasi terlatih, modul penilaian, BKT, tutor LLM, dan dasbor dosen (Bab IV). "
          "Tahap pilot (November 2026 hingga pertengahan 2027, Subbab V.B) diawali survei kebutuhan terhadap mahasiswa klinik di "
          "fakultas kedokteran mitra. Survei ini memakai instrumen keyakinan dan kecukupan dari {cite:daraghma2026} agar "
          "kondisi awal di Indonesia dapat dibandingkan dengan data terpublikasi, serta menghimpun masukan dosen tentang "
          "KC yang paling penting. Tahap pilot kemudian mencakup validasi konten dan label oleh radiolog serta uji "
          "crossover."),
    ("p", "Seluruh komponen memakai perangkat lunak sumber terbuka (Cornerstone3D, FastAPI, PyTorch, nnU-Net, ANTs, "
          "pyBKT), sehingga biaya operasional terutama berasal dari panggilan API LLM dan satu server. Estimasinya "
          f"memakai beberapa asumsi: satu interaksi tutor memakan sekitar {num(TOK_IN, 0)} token masukan (termasuk "
          f"gambar) dan {num(TOK_OUT, 0)} token keluaran, harga resmi US${num(TARIF_IN, 2)} dan US${num(TARIF_OUT, 2)} "
          f"per sejuta token {{cite:openai2026}}, kurs {rp(KURS)} per dolar AS, dan {INTERAKSI} interaksi per mahasiswa "
          f"per bulan. Dengan asumsi tersebut, biaya LLM sekitar {rp(round(BIAYA_MHS, -3))} per mahasiswa per bulan; "
          f"kenaikan harga lima kali lipat pun hanya membawanya ke sekitar {rp(round(5 * BIAYA_MHS, -3))}. Ditambah server "
          f"virtual sekitar {rp(BIAYA_SERVER)} per bulan, pilot dengan 60 mahasiswa membutuhkan kira-kira "
          f"{rp(round(BIAYA_PILOT, -5))} per bulan. Inferensi segmentasi tidak memerlukan GPU khusus karena hanya "
          "dijalankan saat kasus baru ditambahkan."),
    ("p", "Tim kami terdiri atas empat mahasiswa sains data, sehingga sisi klinis rencana ini bergantung pada mitra yang "
          "mudah kami jangkau, yaitu Fakultas Kedokteran Universitas Airlangga dan rumah sakit pendidikannya, RSUD "
          "Dr. Soetomo, yang berada di kota yang sama. Permintaan kami kepada mereka dibuat kecil dan spesifik. Dosen "
          "meninjau keenam KC dan pertanyaan kasus, sedangkan satu radiolog menangani tugas yang memerlukan penilaian "
          "ahli, yaitu "
          + "; ".join(t.format(n=n) + f" (sekitar {num(m, 1).rstrip('0').rstrip(',')} menit per item)" for t, n, m in JAM_RADIOLOG)
          + f". Menurut estimasi kami, totalnya sekitar {num(TOTAL_JAM_RADIOLOG, 0)} jam selama seluruh pilot dan dapat "
          "dibagi ke dalam beberapa sesi singkat. Tidak satu pun tugas ini dibutuhkan untuk MVP, yang cukup berjalan "
          "dengan kunci jawaban hasil perhitungan dari mask."),
    ("p", "Risiko utama rencana ini beserta mitigasinya tercantum pada {tab:risiko}. Tenggat MVP adalah batasan paling "
          "ketat. Karena itu setiap modul sudah memiliki baseline yang berjalan dari uji kelayakan di atas, dan demo dapat "
          "kembali ke baseline tersebut bila peningkatan modul terlambat."),
    ("p", "Rencana evaluasi dirangkum pada {tab:evaluasi}. Evaluasi teknis mengukur mutu model dan keandalan tutor. "
          "Evaluasi pendidikan memakai desain crossover AB/BA {cite:senn2002}: setiap mahasiswa berlatih dengan SINAPS "
          "pada satu set kasus dan dengan modul statis berisi kasus setara pada set lainnya. Urutan kondisi diacak, dan "
          "kedua set disetarakan berdasarkan indeks kesulitan *D*. Luaran utamanya adalah selisih nilai post-test "
          "antarkondisi di dalam subjek yang sama."),
    ("p", "Dengan uji t berpasangan dua sisi (α = 0,05), deteksi efek *d* = 0,5 dengan kuasa 0,80 membutuhkan 34 "
          "mahasiswa {cite:cohen1988}. Target kami sebanyak 60 mahasiswa klinik memberi kuasa sekitar 0,97 dan cukup untuk "
          "mendeteksi efek sekecil 0,37. Sebagai pembanding, desain paralel dua kelompok membutuhkan 64 mahasiswa per "
          "kelompok untuk efek yang sama. Efek periode dan efek bawaan (*carryover*) diuji dalam model campuran, dan "
          "kebergunaan diukur dengan System Usability Scale {cite:brooke1996}."),
    ("table", "risiko", "Risiko utama dan mitigasinya",
     ["Risiko", "Mitigasi"],
     [["MVP belum siap per 23 Okt", "cakupan dikunci pada siklus delineasi (K2, K6) dan tutor; baseline di atas sudah berjalan dari awal hingga akhir"],
      ["Radiolog tidak sempat memberi label", f"MVP hanya memakai kunci dari mask dan ADC (K1, K2, K3, K6); pilot butuh total sekitar {num(TOTAL_JAM_RADIOLOG, 0)} jam radiolog, hanya pada sampel"],
      ["Segmentasi buruk pada lesi kecil", "penilaian selalu memakai mask ahli; keluaran model ditandai bila lesi < 5 ml"],
      ["Tutor menyebut temuan keliru", "prompt khusus fakta, aturan penolakan, audit log jawaban terhadap kunci jawaban"],
      ["Biaya atau latensi LLM naik", "batas token per mahasiswa; dapat diganti model visi lain dengan kontrak JSON yang sama"],
      ["Perbedaan pemindai dan populasi", "normalisasi ADC relatif; kasus lokal ditambahkan hanya setelah disetujui radiolog"]],
     [85, 168], False, "ll"),
    ("p", "Aspek etika dan privasi ditangani sejak tahap rancangan. SOOP sudah dianonimkan dan dirilis dengan lisensi CC0 "
          "{cite:absher2024}. Log belajar mahasiswa disimpan dengan pseudonim dan hanya dipakai untuk personalisasi dan "
          "evaluasi, sesuai Undang-Undang Pelindungan Data Pribadi {cite:uupdp2022}. Uji coba akan diajukan ke komisi "
          "etik universitas mitra. SINAPS adalah alat bantu belajar dan tidak ditujukan untuk mendiagnosis pasien; "
          "pernyataan ini ditampilkan di setiap sesi."),
    ("table", "evaluasi", "Rencana evaluasi dan target",
     ["Aspek", "Metrik", "Target"],
     [["Segmentasi", "rerata Dice pada data uji terpisah (semua lesi / lesi < 5 ml)", "≥ 0,80 / ≥ 0,65"],
      ["Teritori", "kesesuaian registrasi atlas dengan radiolog (Cohen κ)", "κ ≥ 0,6"],
      ["Penilaian", "kesesuaian jenis kesalahan dengan penilaian radiolog (Cohen κ)", "κ ≥ 0,6"],
      ["Tutor LLM", "proporsi jawaban yang memuat temuan di luar data", "< 5%"],
      ["Tutor LLM", "latensi respons (persentil ke-95)", "< 8 dtk"],
      ["Belajar", "selisih nilai post-test, SINAPS vs modul statis (crossover, n = 60)", "d ≥ 0,5"],
      ["Kebergunaan", "System Usability Scale", "≥ 70"],
      ["Kebutuhan", "proporsi mahasiswa yang yakin membaca CT/MRI kepala (survei awal)", "dilaporkan"]],
     [48, 150, 55], False, "llc"),
    # =============================================================== BAB IV
    ("h1", "Hasil dan Pembahasan"),
    ("h2", "Hasil Implementasi"),
    ("p", f"Seluruh siklus pada {{fig:siklus}} kini berjalan sebagai aplikasi web yang dapat diakses di {LINK_MVP}, "
          f"dengan source code di {LINK_GITHUB}. {{tab:impl}} memetakan setiap modul Bab III ke implementasinya. "
          "Sebagian besar komponen berjalan penuh. Modul visi, personalisasi, dan tutor berjalan dengan cakupan yang "
          "sudah dikunci di tabel risiko ({tab:risiko}): K1, K2, K3, dan K6 dinilai dari mask dan peta ADC, sedangkan K4 "
          "dan K5 tampil di peta penguasaan dengan keterangan \"belum di MVP\"."),
    ("table", "impl", "Modul rancangan dan implementasinya di MVP",
     ["Modul", "Implementasi di MVP", "Status"],
     [["Viewer web", "Cornerstone3D: gulir slice, window/level, zoom, kuas dan penghapus, titik, probe ADC relatif, Capture", "berjalan"],
      ["Orkestrator", "FastAPI di Vercel; akun, kelas, dan log berpseudonim (hash NIM) di Postgres", "berjalan"],
      ["Bank kasus", "36 kasus SOOP (16 mudah, 10 sedang, 10 sulit); kunci jawaban hanya di server", "berjalan"],
      ["Visi", f"U-Net 2.5D ({num(FS.get('n_train', 1170), 0)} pasien) dan temuan terstruktur JSON; atlas teritori belum", "sebagian"],
      ["Penilaian", "Dice, recall per lesi, galat volume, HD95, lima jenis kesalahan; soal K1 sampai K3", "berjalan"],
      ["Personalisasi", "BKT pers. (3) dan (4), prasyarat, tingkat kesulitan; K4 dan K5 belum", "sebagian"],
      ["Tutor", "GPT-5.6 Luna, tiga mode, kunci terkunci sebelum submit, log audit; korpus RAG belum memuat PNPK/SKDI", "sebagian"],
      ["Dasbor dosen", "penguasaan kelas, kesalahan tersering, tugas, verifikasi kasus, audit tutor, ekspor CSV", "berjalan"],
      ["Modul belajar", "enam modul per KC dengan contoh kasus interaktif dan kuis", "berjalan"]],
     [60, 150, 43], False, "llc"),
    ("p", "{fig:layar_latihan} memperlihatkan satu sesi latihan. Sistem memilih kasus sub-1517 karena K6 adalah KC "
          "terlemah akun tersebut, lalu mahasiswa membuka seri DWI dan menggulir ke slice dengan lesi terbesar. Ketika "
          "mahasiswa meminta tutor langsung menyebut hemisfer lesi, tutor tidak menyebutnya karena kunci jawaban masih "
          "terkunci. Tutor justru bertanya balik tentang posisi lesi terhadap penanda R dan meminta mahasiswa mencocokkan "
          "DWI dengan peta ADC. Jawaban itu ditulis GPT-5.6 Luna dalam 2,8 detik, bukan templat."),
    ("fig", "layar_latihan", "Halaman latihan MVP (kasus SOOP sub-1517, seri DWI). Kiri: alat viewer dan pemilih seri. "
                             "Kanan: tombol kirim jawaban (soal K1 sampai K6 di atasnya tidak tampak), peta penguasaan "
                             "BKT, dan tutor mode Sokratik yang menolak menyebut hemisfer sebelum jawaban dikirim. Ruang "
                             "hitam di kiri dan kanan citra dipangkas.", True),
    ("p", "Setelah jawaban dikirim, penilaian dan pembaruan BKT selesai dalam satu permintaan, lalu anotasi ditampilkan "
          "di atas kunci jawaban ({fig:layar_tinjau}). Contoh pada gambar ini menunjukkan mengapa modul penilaian tidak "
          "berhenti pada Dice. Anotasi tersebut memperoleh Dice 0,99, angka yang pada platform berbasis satu skor akan "
          "dibaca hampir sempurna, padahal hanya 3 dari 7 fokus lesi yang ditandai. Sistem melabelinya lesi kecil "
          "terlewat dan mendaftar volume serta slice keempat fokus yang terlewat, sehingga mahasiswa tahu ke mana harus "
          "kembali."),
    ("fig", "layar_tinjau", "Tinjau ulang satu percobaan yang sudah dinilai, dilihat dari akun dosen (kasus sub-1150). "
                            "Anotasi akun demo ini dibuat dari mask ahli yang sengaja diganggu, bukan anotasi mahasiswa. "
                            "Dice 0,99, tetapi hanya 3 dari 7 fokus ditemukan; keempat fokus yang terlewat didaftar "
                            "beserta slice-nya.", True),
    ("p", "Di sisi dosen, jawaban mahasiswa terkumpul menjadi dasbor kelas ({fig:layar_dosen}) yang berisi rata-rata "
          "penguasaan tiap KC, jenis kesalahan tersering, daftar mahasiswa yang perlu perhatian, tugas, verifikasi kasus, "
          "dan audit jawaban tutor. Data pada gambar adalah data demo 15 mahasiswa fiktif yang percobaannya disimulasikan "
          "lewat API yang sama, jadi angkanya hanya memperlihatkan fungsi dasbor. Dosen hanya melihat mahasiswa di "
          "kelasnya sendiri."),
    ("fig", "layar_dosen", "Potongan dasbor dosen MVP dengan data demo: penguasaan rata-rata kelas per KC menurut BKT "
                           "dan sebaran jenis kesalahan delineasi."),
    ("h2", "Pengujian"),
    ("p", "Pengujian memakai metrik yang ditetapkan pada {tab:evaluasi} dan dijalankan langsung terhadap kode MVP yang "
          "sama dengan yang di-deploy. Hasilnya dirangkum pada {tab:hasil}. Dari delapan target, dua tercapai, satu belum "
          "tercapai, dan lima belum dapat diukur karena membutuhkan radiolog atau mahasiswa sungguhan. Beberapa angka di "
          "bawah adalah hasil putaran uji kedua, setelah kelemahan yang ditemukan pada putaran pertama diperbaiki; kedua "
          "angka dilaporkan bila keduanya penting."),
    ("table", "hasil", "Hasil pengujian MVP terhadap target Bab III",
     ["Aspek", "Target", "Hasil MVP", "Status"],
     [["Segmentasi", "Dice ≥ 0,80 / ≥ 0,65 (lesi < 5 ml)",
       f"{num(FS.get('dice_mean', 0), 2)} / {num(FS.get('dice_lt5ml', 0), 2)} (36 kasus bank)", "belum tercapai"],
      ["Teritori", "κ ≥ 0,6", "registrasi atlas belum di MVP", "belum diuji"],
      ["Penilaian", "κ ≥ 0,6 terhadap radiolog",
       f"pengganti: akurasi {pct(FE.get('akurasi', 0), 1)} pada {FE.get('n', 165)} anotasi sintetis", "belum diuji"],
      ["Tutor", "< 5% jawaban di luar data",
       f"0 dari {FT.get('semua', {}).get('n', 144)} ({ikp(FT.get('semua', {}).get('ik95'), 1)})", "tercapai"],
      ["Latensi tutor", "p95 < 8 dtk",
       f"{num(LTB.get('semua', {}).get('p95', 0))} dtk berurutan; {num(FT.get('latensi_paralel8', {}).get('p95', 0))} dtk saat 8 paralel",
       "tercapai" if max(LTB.get('semua', {}).get('p95', 99), FT.get('latensi_paralel8', {}).get('p95', 99)) < 8
       else "sebagian"],
      ["Belajar", "d ≥ 0,5 (crossover, n = 60)", "tahap pilot", "belum diuji"],
      ["Kebergunaan", "SUS ≥ 70", "tahap pilot", "belum diuji"],
      ["Kebutuhan", "survei awal mahasiswa", "tahap pilot", "belum diuji"]],
     [56, 62, 92, 43], False, "lllc"),
    ("p", f"**Uji fungsional ujung ke ujung.** API dijalankan dengan basis data sementara, lalu {E.get('n_akun', 5)} "
          f"akun mahasiswa uji mengerjakan seluruh {E.get('n_kasus_latihan', 33)} kasus latihan lewat endpoint yang sama "
          "dengan yang dipanggil peramban. Setiap akun mewakili satu jenis kesalahan anotasi, dan jawaban K1, K2, dan K3 "
          "dibuat benar dengan peluang 85%, 75%, dan 60% agar penguasaan tiap KC bergerak berbeda. Seluruh "
          f"{num(E.get('n_panggilan', 0), 0)} panggilan berhasil, tidak ada kasus yang muncul dua kali untuk akun yang "
          "sama, dan tidak satu pun respons sebelum jawaban dikirim memuat temuan atau mask. Folder publik "
          f"({E.get('n_file_publik', 0)} berkas) juga hanya berisi citra. Waktu proses server median "
          f"{num(E['latensi_server_ms']['next']['median'], 0)} ms untuk memilih kasus dan "
          f"{num(E['latensi_server_ms']['submit']['median'], 0)} ms untuk menilai jawaban (persentil ke-95 "
          f"{num(E['latensi_server_ms']['submit']['p95'] / 1000, 2)} detik, didominasi perhitungan HD95 pada lesi besar). "
          f"Dari luar, deployment Vercel menjawab dengan latensi median "
          f"{num(E['latensi_vercel']['/api/health']['median_ms'] / 1000, 2)} detik."),
    ("p", f"**Segmentasi.** Pada 36 kasus bank, U-Net MVP mencapai rerata Dice {num(FS.get('dice_mean', 0), 2)} "
          f"({ik(FS.get('dice_ci95'))}) dengan median {num(FS.get('dice_median', 0), 2)} dan recall per lesi "
          f"{num(FS.get('lesion_recall_mean', 0), 2)} ({{fig:seg_mvp}}). Target untuk lesi besar terpenuhi (Dice "
          f"{num(FS.get('dice_ge5ml', 0), 2)} pada {FS.get('n_ge5ml', 28)} kasus minimal 5 ml), tetapi pada "
          f"{FS.get('n_lt5ml', 8)} kasus di bawah 5 ml rerata Dice hanya {num(FS.get('dice_lt5ml', 0), 2)}, dan dua di "
          "antaranya sama sekali tidak terdeteksi. Hasil ini membenarkan keputusan rancangan bahwa mahasiswa selalu "
          "dinilai terhadap mask ahli. Pada lesi kecil, model belum layak dipakai sebagai kunci jawaban dan hanya berperan "
          "sebagai pembaca kedua."),
    ("fig", "seg_mvp", f"Dice U-Net MVP pada 36 kasus bank yang tidak ikut dilatih, terhadap volume lesi. Model dilatih "
                       f"pada {num(FS.get('n_train', 1170), 0)} pasien SOOP lain."),
    ("p", f"**Penilaian.** Pada {FE.get('n', 165)} anotasi sintetis yang dikirim lewat API, modul penilaian dengan "
          f"ambang bawaan aplikasi mengenali jenis kesalahan dengan akurasi {pct(FE.get('akurasi', 0), 1)} "
          f"({ikp(FE.get('ik95'), 1)}, bootstrap per kasus), seperti terlihat pada {{fig:uji_penilaian}}. Angka ini "
          f"sejalan dengan validasi silang lima fold pada {num(FR.get('n', 672), 0)} anotasi dari "
          f"{FR.get('n_subjek', 36)} subjek bank ({pct(FR.get('akurasi', 0), 1)}; {ikp(FR.get('ik95'), 1)}) dan jauh di "
          f"atas {pct(FR.get('dice_saja', 0), 1)} bila hanya memakai Dice."),
    ("p", "Pengujian ini juga menemukan dua masalah yang tidak terlihat di rancangan, dan keduanya sudah diperbaiki di "
          "MVP sebelum angka di atas dihitung ulang. Pertama, aturan lama membedakan lesi terlewat dari terlalu sempit "
          "hanya lewat galat volume, sehingga fokus terlewat yang besar ikut dilabeli terlalu sempit. Aturan sekarang "
          "juga menghitung Dice pada fokus yang tersentuh saja: bila fokus yang ditandai tertutup rapi (Dice minimal 0,9), "
          "jawabannya dilabeli lesi terlewat. Pada validasi silang yang sama, akurasi naik dari "
          f"{pct(FR.get('akurasi_lama', 0), 1)} ({ikp(FR.get('ik95_lama'), 1)}) menjadi {pct(FR.get('akurasi', 0), 1)}. "
          "Kedua, kriteria benar K6 pada rancangan (Dice minimal 0,6 dan recall per lesi 1) meloloskan "
          f"{FE.get('luas_lolos_k6_lama', 0)} dari {FE.get('n_luas', 33)} anotasi terlalu luas, sehingga mahasiswa yang "
          "selalu ikut menandai tepi atau edema tetap dianggap menguasai delineasi. Kriteria sekarang menambah syarat "
          "galat volume paling banyak +25%. Ambang ini dipilih pada anotasi sintetis terpisah dari data uji, dan dengan "
          f"ambang ini anotasi terlalu luas yang lolos tinggal {FE.get('luas_lolos_k6', 0)} dari {FE.get('n_luas', 33)}, "
          f"sementara {FE.get('hampir_benar_lolos_k6', 0)} dari {FE.get('n_hampir_benar', 33)} anotasi hampir benar tetap "
          "lolos."),
    ("fig", "uji_penilaian", f"Matriks kebingungan jenis kesalahan pada uji ujung ke ujung ({FE.get('n', 165)} anotasi "
                             "sintetis, 33 kasus). Diagonal adalah jawaban yang dilabeli benar."),
    ("p", f"**Personalisasi.** {{fig:uji_bkt}} menunjukkan lintasan penguasaan K6 kelima akun. Pada seluruh "
          f"{E.get('n_target', 165)} pemilihan kasus, KC sasaran sama dengan aturan KC terlemah yang prasyaratnya "
          f"terpenuhi, dan seluruh {E.get('n_bkt', 660)} pembaruan penguasaan cocok dengan persamaan (3) dan (4). "
          "Perilakunya sesuai harapan. Akun dengan anotasi hampir benar menguasai K6 dalam tiga kasus lalu "
          "dialihkan ke K3, KC terlemahnya, sedangkan akun yang terus salah lokasi tetap diarahkan ke K6 sampai kasus "
          "terakhir. Grafik yang sama memperlihatkan akibat perbaikan kriteria K6: akun yang selalu menandai terlalu "
          "luas tidak lagi dianggap menguasai K6 dan terus diarahkan ke K6, padahal dengan kriteria lama akun ini "
          "menguasai K6 hampir secepat akun hampir benar. Uji ini membuktikan bahwa modul personalisasi berjalan benar, "
          "tetapi tidak membuktikan bahwa urutan adaptif mempercepat belajar. Bukti untuk klaim kedua sejauh ini masih "
          "berupa simulasi pada Subbab III.F."),
    ("fig", "uji_bkt", "Uji modul personalisasi MVP. Atas: penguasaan K6 per akun uji (satu akun per jenis kesalahan "
                       "anotasi). Bawah: KC sasaran yang dipilih sistem untuk setiap kasus."),
    ("p", "**Tutor.** Tutor diuji dengan empat skenario pada ke-36 kasus bank, masing-masing dengan tiga rumusan pesan "
          f"yang berbeda ({FT.get('semua', {}).get('n', 432)} jawaban), memakai fungsi tutor yang sama dengan endpoint "
          "aplikasi. Pada skenario A, mahasiswa meminta hemisfer, jumlah fokus, slice, atau volume lesi sebelum jawaban "
          "dikirim. Pada skenario B, mahasiswa meminta pembahasan setelah anotasinya terlalu sempit atau melewatkan "
          "fokus. Pada skenario C, mahasiswa mendesakkan hemisfer dan multifokalitas yang salah sambil mengatasnamakan "
          "dosen, menuduh kunci jawaban salah, atau mengutip teman sekelompok. Pada skenario D, mahasiswa menanyakan "
          "teritori arteri dan usia lesi yang tidak ada di data. Setiap jawaban dinilai dua lapis, yaitu oleh penilai "
          "LLM dengan rubrik tertutup dan oleh pemeriksa berbasis aturan. Penilai LLM memakai model lain "
          f"({FT.get('judge_model', 'gpt-5.5')}) supaya tutor tidak menilai jawabannya sendiri. Ke-"
          f"{FT.get('n_ditandai', 0)} jawaban yang ditandai salah satu lapis kami baca satu per satu, ditambah sampel acak "
          f"{FT.get('sampel_tidak_ditandai', {}).get('n', 30)} jawaban yang tidak ditandai."),
    ("p", "Tidak ada yang benar-benar gagal. Penilai LLM tidak menandai satu jawaban pun, dan hampir semua tanda berasal "
          f"dari pemeriksa aturan yang sengaja longgar: {FT.get('n_ditandai_regex_D', 0)} jawaban skenario D menyebut "
          "\"arteri serebri media\" atau \"subakut\" justru di dalam kalimat penolakan. Dari "
          f"{FT.get('semua', {}).get('n', 432)} jawaban, tidak ada temuan di luar fakta "
          f"({ikp(FT.get('semua', {}).get('ik95'), 1)}). Dengan 108 jawaban per skenario, batas atas interval tiap "
          f"skenario kini {pct(FT.get('ikut_klaim_salah', {}).get('ik95', [0, 0])[1], 1)}, di bawah target 5% "
          "({fig:uji_tutor}). Sampel acak memperlihatkan masalah yang tidak dicari kedua lapis penilai. Dua jawaban "
          "diakhiri token sampah yang tidak berhubungan dengan isi, yaitu satu kata asing dan satu string berhuruf "
          "Mandarin. Isinya tetap benar, tetapi teks seperti itu tidak layak tampil. Karena itu MVP kini menyaring aksara "
          "asing dan potongan kata yatim di akhir jawaban, lalu mencatatnya di log audit. Penyaring ini menangkap kedua "
          "kasus tersebut tanpa alarm palsu pada 576 jawaban tersimpan dari kedua putaran uji."),
    ("p", "Untuk menekan latensi, tutor kini memakai tingkat penalaran rendah dan mengirim jawaban secara bertahap, "
          "sehingga kalimat pertama tampil sebelum seluruh jawaban selesai. Ketika delapan permintaan berjalan "
          "bersamaan, latensi persentil ke-95 turun dari "
          f"{num(FT.get('v1', {}).get('latensi_paralel8', {}).get('p95', 0))} detik pada uji pertama menjadi "
          f"{num(FT.get('latensi_paralel8', {}).get('p95', 0))} detik, dan kalimat pertama sudah tampil pada persentil "
          f"ke-95 {num(FT.get('kata_pertama_paralel8', {}).get('p95', 0))} detik. Ketika permintaan dikirim berurutan, "
          f"persentil ke-95 sebesar {num(LTB.get('sokratik', {}).get('p95', 0))} detik untuk mode Sokratik dan "
          f"{num(LTB.get('penjelasan', {}).get('p95', 0))} detik untuk mode penjelasan."),
    ("fig", "uji_tutor", f"Uji tutor MVP pada 36 kasus x 4 skenario x 3 rumusan pesan. Kiri: proporsi jawaban gagal per "
                         "skenario setelah dibaca manual, dengan batas atas IK 95% Wilson. Kanan: latensi persentil "
                         f"ke-95 ({LTB.get('semua', {}).get('n', 20)} permintaan berurutan; "
                         f"{FT.get('semua', {}).get('n', 432)} permintaan dengan 8 berjalan bersamaan, uji pertama "
                         "dan sekarang)."),
    ("h2", "Pembahasan"),
    ("p", "**RQ1: umpan balik objektif tanpa radiolog.** Pertanyaan ini terjawab untuk tugas yang kuncinya tersedia di "
          "mask. Jawaban K1, K2, K3, dan K6 dinilai otomatis dalam waktu kurang dari satu detik, dan umpan baliknya "
          "menyebut jenis kesalahan beserta lokasi fokus yang terlewat, bukan hanya skor. Hal ini menjawab kelemahan "
          "platform kontur berbasis Dice yang dibahas pada Subbab II.B {cite:icontour2025,orr2024}, dan contoh pada "
          "{fig:layar_tinjau} adalah jawaban yang akan lolos sebagai hampir sempurna bila hanya Dice yang dilihat. "
          f"Ada dua batasan. Akurasi {pct(FE.get('akurasi', 0))} diukur pada kesalahan sintetis, sehingga kesesuaiannya "
          "dengan penilaian radiolog atas anotasi mahasiswa sungguhan belum diketahui. Kriteria lulus K6 sudah ditambah "
          "syarat galat volume sehingga jawaban terlalu luas tidak lagi dihitung sebagai penguasaan, tetapi jawaban "
          f"terlalu sempit yang Dice-nya masih di atas 0,6 tetap lolos ({FE.get('sempit_lolos_k6', 0)} dari "
          f"{FE.get('n_sempit', 45)} pada uji ujung ke ujung)."),
    ("p", "**RQ2: tutor dengan halusinasi terkendali.** Pertanyaan ini terjawab pada pengujian ini, dan kuncinya ada pada "
          "arsitektur, bukan semata pada kepatuhan model. Sebelum jawaban dikirim, tutor tidak memegang lokasi lesi sama "
          "sekali. Setelahnya, tutor hanya menerima temuan terstruktur yang dihitung dari mask. Dalam kondisi itu, model "
          "tidak menambah temuan, tidak menebak teritori, dan tidak mengalah pada mahasiswa yang mendesak. Tanpa fakta, "
          f"model yang sama keliru pada {pct(LA.get('klaim_salah', 0))} klaim dan mengikuti klaim keliru mahasiswa pada "
          f"{pct(LT.get('ikut_saran_salah', 0))} klaim (Subbab III.G). Mutu pedagogis penjelasannya belum dinilai. "
          "Pemeriksa fakta bawaan MVP kini mengenali kalimat koreksi, sehingga alarm palsu pada skenario C turun dari "
          f"{FT.get('v1', {}).get('C_fact_check', {}).get('k', 5)} dari {FT.get('v1', {}).get('C_fact_check', {}).get('n', 36)} "
          f"menjadi {FT.get('ditandai_fact_check_mvp_skenario_C', 0)} dari 108. Angkanya belum nol karena koreksi dapat "
          "dirumuskan dengan banyak cara, misalnya \"tanpa gambaran multifokal\", jadi audit dosen masih memuat sedikit "
          "alarm palsu."),
    ("p", "**RQ3: urutan kasus yang adaptif.** Pertanyaan ini baru terjawab sebagian. Mekanismenya sudah berjalan dan "
          "terbukti benar: kasus selalu diarahkan ke KC terlemah yang prasyaratnya terpenuhi, dan tingkat kesulitannya "
          "naik seiring penguasaan. Klaim bahwa urutan ini lebih efisien daripada modul statis masih bertumpu pada "
          "simulasi. Implementasinya juga sedikit berbeda dari rancangan semifinal. Karena satu kasus menilai empat KC "
          "sekaligus, adaptasi bekerja terutama lewat tingkat kesulitan, bukan lewat pemilihan satu KC per kasus. Uji "
          "crossover pada tahap pilot akan menunjukkan apakah mekanisme ini memang mempercepat belajar."),
    ("p", "Secara keseluruhan, MVP menunjukkan bahwa ketiga syarat rancangan pada Subbab II.F dapat dipenuhi bersamaan "
          "dalam satu aplikasi: umpan balik dihitung dari citra, urutan latihan mengikuti mahasiswa, dan model bahasa "
          "tetap dekat dengan fakta terukur. Pada {fig:posisi}, kuadran kanan atas kini ditempati perangkat yang "
          "berjalan, bukan lagi rancangan. Yang belum terbukti adalah dampaknya terhadap belajar."),
    ("h2", "Keterbatasan"),
    ("p", "Beberapa bagian belum berjalan atau belum diuji. Pertama, belum ada pengguna sungguhan. Semua anotasi dalam "
          "pengujian dibuat dari mask ahli dengan operasi geometris, sehingga belum mencakup kesalahan campuran yang "
          "dibuat mahasiswa, dan kebergunaan serta efek belajar belum diukur. Kedua, K4 (teritori arteri) dan K5 (usia "
          "lesi) belum dinilai karena registrasi atlas dan label radiolog belum tersedia. Ketiga, korpus RAG pada MVP "
          "baru berisi delapan potongan catatan ajar tim yang belum diverifikasi dosen. Kutipan PNPK dan SKDI baru akan "
          "ditambahkan setelah ditinjau dosen mitra, sehingga mode rujukan belum diuji. Keempat, segmentasi pada lesi "
          "di bawah 5 ml masih lemah."),
    ("p", "Kelima, penilai LLM pada uji tutor sudah memakai model yang berbeda dari tutor, tetapi keduanya berasal dari "
          "penyedia yang sama, dan dari jawaban yang tidak ditandai baru sampel "
          f"{FT.get('sampel_tidak_ditandai', {}).get('n', 30)} jawaban yang dibaca manual. Keenam, tingkat penalaran yang "
          "lebih rendah mempercepat tutor, tetapi pada uji yang sama muncul dua jawaban bertoken sampah yang tidak muncul "
          "pada uji pertama dengan penalaran bawaan. Penyaring menutup gejalanya, sedangkan sebabnya belum dipastikan. "
          "Latensi juga baru diuji sampai delapan permintaan bersamaan, belum pada satu kelas penuh. Terakhir, semua "
          "kasus berasal dari satu pusat stroke di Amerika Serikat, dan lesion mask SOOP tetap mengandung variabilitas "
          "antarpembaca."),

    # =============================================================== BAB V
    ("h1", "Penutup"),
    ("h2", "Kesimpulan"),
    ("p", "SINAPS sudah berjalan sebagai prototipe yang menghubungkan viewer MRI, penilaian otomatis, BKT, dan tutor LLM "
          "dalam satu siklus latihan. Untuk RQ1, umpan balik objektif tanpa radiolog dapat diberikan dengan menilai "
          "jawaban terhadap lesion mask melalui empat metrik yang dipetakan ke jenis kesalahan; pada kesalahan sintetis "
          f"akurasinya {pct(FE.get('akurasi', 0))}, dua kali lipat penilaian dengan Dice saja. Untuk RQ2, tutor yang "
          f"hanya menerima temuan terstruktur tidak menghasilkan temuan di luar fakta pada "
          f"{FT.get('semua', {}).get('n', 144)} jawaban, termasuk ketika mahasiswa mendesakkan jawaban keliru. Untuk "
          "RQ3, pemilihan kasus berbasis BKT berjalan benar dan menyasar KC terlemah, tetapi keunggulannya atas modul "
          "statis baru ditunjukkan lewat simulasi dan masih harus diuji pada mahasiswa."),
    ("h2", "Rencana Pengembangan"),
    ("p", "Langkah berikutnya disusun dari temuan pengujian dan dari bagian yang belum berjalan ({fig:gantt}):"),
    ("bullet", "**Perbaikan langsung.** Korpus PNPK dan SKDI yang sudah ditinjau dosen beserta uji mode rujukan, "
               "kriteria K6 yang juga menolak jawaban terlalu sempit, dan uji beban tutor pada satu kelas penuh. "
               "Syarat galat volume K6, pemeriksa fakta yang mengenali kalimat koreksi, aturan lesi terlewat, penyaring "
               "token sampah, dan jawaban bertahap sudah diterapkan setelah uji pertama (Subbab IV.B)."),
    ("bullet", "**Melengkapi kompetensi.** Registrasi atlas untuk K4, label usia lesi K5 oleh radiolog, dan nnU-Net 3D "
               "pada 1.421 pasien dengan penanda keyakinan untuk lesi di bawah 5 ml {cite:isensee2021}."),
    ("bullet", f"**Pilot di FK mitra.** Survei kebutuhan, validasi radiolog (sekitar {num(TOTAL_JAM_RADIOLOG, 0)} jam), "
               "uji crossover dengan 60 mahasiswa klinik, System Usability Scale, lalu kalibrasi parameter BKT dan "
               "tingkat kesulitan Rasch dari log nyata."),
    ("bullet", "**Kasus lokal.** Kasus MRI dan CT tanpa kontras yang dianonimkan dari rumah sakit pendidikan mitra, "
               "masuk ke bank kasus hanya setelah disetujui radiolog melalui dasbor verifikasi."),
    ("fig", "gantt", "Peta jalan pengembangan. Batang berarsir adalah tahap MVP yang sudah selesai; garis merah menandai babak final."),
    ("h2", "Dampak"),
    ("p", "Bagi mahasiswa kedokteran, SINAPS memberi sesuatu yang selama ini hanya didapat lewat bimbingan privat: "
          "kesempatan mengerjakan banyak kasus MRI nyata dengan umpan balik spesifik dalam hitungan detik, kapan saja, "
          "tanpa menunggu radiolog. Hal ini penting karena kompetensi interpretasi citra baru terbentuk setelah ratusan "
          "kasus {cite:pusic2011}. Tutor yang tidak bisa didesak untuk membenarkan jawaban keliru juga lebih aman "
          "daripada chatbot umum yang sudah dipakai 95% mahasiswa Indonesia untuk belajar {cite:chegg2025}."),
    ("p", "Bagi dosen dan radiolog pengajar, pekerjaan yang paling menyita waktu, yaitu memeriksa anotasi satu per satu, "
          "berpindah ke sistem. Waktu dosen dapat dipusatkan pada mahasiswa yang ditandai dasbor dan pada jenis "
          "kesalahan yang paling sering muncul di kelasnya, sedangkan radiolog cukup menangani tugas yang memang "
          f"membutuhkan keahlian, sekitar {num(TOTAL_JAM_RADIOLOG, 0)} jam selama pilot."),
    ("p", "Bagi fakultas kedokteran, terutama di luar Jawa yang paling kekurangan radiolog {cite:yunus2024}, biaya "
          f"operasionalnya sekitar {rp(round(BIAYA_MHS, -3))} per mahasiswa per bulan dan seluruh perangkat lunaknya "
          "sumber terbuka. Dalam jangka panjang, lulusan yang lebih yakin membaca citra stroke dapat mempercepat "
          "keputusan terapi di fasilitas yang tidak memiliki radiolog jaga. Semua dampak ini masih berupa potensi yang "
          "perlu dibuktikan lewat pilot, bukan hasil yang sudah diukur."),
]

# ------------------------------------------------------------------ LAMPIRAN (sebelum Daftar Pustaka, sesuai templat)
# Hasil cek Turnitin. tanggal/id_submission opsional (None = tidak disebut di teks).
# Ringkasan (tangkapan layar Integrity Overview) ada di script/lampiran/turnitin_ringkasan.png dan masuk ke DOCX.
# Laporan lengkap (PDF dari Turnitin), kalau ada: simpan sebagai script/lampiran/turnitin.pdf, build.py menempelkannya di akhir PDF.
TURNITIN = dict(skor=11, tanggal=None, id_submission=None)


def _turnitin():
    t = TURNITIN
    skor = f"{num(t['skor'], 0)}%" if t["skor"] is not None else "[skor]%"
    tgl = " pada " + t["tanggal"] if t["tanggal"] else ""
    sid = f" (ID submission {t['id_submission']})" if t["id_submission"] else ""
    return ("**Laporan similarity Turnitin.** Naskah ini diperiksa dengan Turnitin" + tgl + sid + ". Skor overall "
            "similarity yang diperoleh adalah " + skor + ", di bawah batas 15% yang ditetapkan panitia. Ringkasan "
            "hasil pemeriksaan ditampilkan di bawah.")


LAMPIRAN = [
    ("unh", "Lampiran"),
    ("p", "**Pernyataan penggunaan AI.** Tim memakai ChatGPT (OpenAI) dan Claude (Anthropic) sebagai alat bantu untuk "
          "curah gagasan, penelusuran penelitian terdahulu, dan pengujian prototipe. Sumber yang dikutip dicek ke "
          "publikasi aslinya, dan semua angka hasil berasal dari eksperimen yang dijalankan tim. GPT-5.6 Luna (OpenAI) adalah komponen tutor SINAPS, "
          "sedangkan GPT-5.5 (OpenAI) dipakai sebagai penilai otomatis pada uji tutor (Subbab IV.B). Tanggung jawab atas isi makalah sepenuhnya "
          "berada pada penulis."),
    ("p", _turnitin()),
    ("img", "lampiran/turnitin_ringkasan.png"),
]
