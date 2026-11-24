# -*- coding: utf-8 -*-
"""Pembangkit seluruh gambar naskah NSC 2026 - Prediksi Kelembapan Udara.

Letak     : NSC UB/paper/script/make_figures.py
Jalankan  : python make_figures.py
Keluaran  : NSC UB/paper/figures/*.png  (300 dpi)

Sumber angka, tiga kelompok, dan tidak ada yang lain:

  (a) Dataset mentah  NSC UB/Dataset/{train,test}.csv
      Gambar 1-6, 11, 12 dihitung ulang dari nol setiap kali skrip ini jalan.
      Rutin `hampel()` dan `es()` disalin verbatim dari `final_pipeline.py`
      supaya angkanya identik dengan pipeline produksi.

  (b) Artefak eksperimen  NSC UB/outputs/**.csv
      Gambar 7 dan 9 membaca berkas hasil audit yang dihasilkan pipeline.

  (c) Konstanta terukur yang tidak dapat dihitung ulang tanpa melatih ulang
      seluruh stack (bias bertanda per anggota) atau tanpa mengirim ulang
      berkas ke Kaggle (tangga papan peringkat). Keduanya dikumpulkan di blok
      MEASURED di bawah, masing-masing dengan penunjuk ke sumbernya.

Aturan angka: jangan mengetik angka dari ingatan. Kalau eksperimen dijalankan
ulang, perbarui MEASURED dari log yang bersangkutan, bukan sebaliknya.
"""
import os
import sys

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

HERE = os.path.dirname(os.path.abspath(__file__))
PAPER = os.path.dirname(HERE)
PROJECT = os.path.dirname(PAPER)
DATA = os.path.join(PROJECT, 'Dataset')
OUTPUTS = os.path.join(PROJECT, 'outputs')
FIGDIR = os.path.join(PAPER, 'figures')
os.makedirs(FIGDIR, exist_ok=True)

TARGET = 'air_humidity'

# ------------------------------------------------------------------ tampilan
# Naskah IEEE dua kolom: lebar satu kolom 3,30 inci, lebar penuh 6,85 inci.
# Gambar dibangkitkan pada lebar akhirnya supaya ukuran huruf di dalam gambar
# sama besar dengan huruf di badan naskah, bukan hasil penyusutan sembarang.
COL_IN = 3.30
FULL_IN = 6.85

plt.rcParams.update({
    'figure.dpi': 300, 'savefig.dpi': 300,
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif'],
    'font.size': 7.0, 'axes.titlesize': 7.5, 'axes.labelsize': 7.0,
    'xtick.labelsize': 6.3, 'ytick.labelsize': 6.3, 'legend.fontsize': 6.3,
    'axes.titleweight': 'bold',
    'axes.grid': True, 'grid.alpha': 0.28, 'grid.linewidth': 0.4,
    'axes.spines.top': False, 'axes.spines.right': False,
    'axes.linewidth': 0.6, 'xtick.major.width': 0.6, 'ytick.major.width': 0.6,
    'lines.linewidth': 1.0,
    'figure.facecolor': 'white', 'savefig.facecolor': 'white',
    'savefig.bbox': 'tight', 'savefig.pad_inches': 0.02,
})

def koma(x, pos=None):
    """Pemisah desimal Indonesia untuk label sumbu. Naskah memakai koma, jadi
    gambar harus memakai koma juga; angka bertitik di dalam gambar adalah cacat
    format yang mudah luput."""
    s = ('%g' % x) if abs(x - round(x)) > 1e-9 else ('%d' % round(x))
    return s.replace('.', ',').replace('-', '−')


FMT = matplotlib.ticker.FuncFormatter(koma)


def komafy(ax):
    """Pasang formatter koma, tetapi jangan menimpa label teks yang sudah diatur
    tangan (set_xticklabels memasang FixedFormatter; menimpanya akan mengubah
    label kategori kembali menjadi angka indeks)."""
    for a in (ax.xaxis, ax.yaxis):
        if a.get_scale() != 'linear':
            continue
        if isinstance(a.get_major_formatter(), matplotlib.ticker.ScalarFormatter):
            a.set_major_formatter(FMT)


def n(x, d=3):
    """Angka untuk anotasi di dalam gambar, gaya Indonesia."""
    return ('%.*f' % (d, x)).replace('.', ',').replace('-', '−')


C = {'obs': '#1b3a5c', 'pred': '#c1452b', 'aux': '#8b98a5', 'hi': '#d98c1f',
     'ok': '#2e7d5b', 'bad': '#a3282a', 'soft': '#dfe6ec', 'vio': '#6b4c9a'}


def kotak(leg, alpha=0.82):
    """Bingkai putih tembus pandang untuk legenda yang duduk di atas data.

    Tanpa ini, garis dan titik menembus huruf legenda dan naskah cetaknya jadi
    tidak terbaca. Alpha 0,82 cukup untuk memisahkan teks tanpa menyembunyikan
    data di belakangnya; pakai alpha 1,0 kalau yang lewat di belakang adalah
    garis hitam pekat, karena pada 0,82 ia masih terbaca menembus huruf.
    """
    f = leg.get_frame()
    f.set_facecolor('white')
    f.set_alpha(alpha)
    f.set_edgecolor('none')
    f.set_boxstyle('square,pad=0.25')
    # Garis bantu (axhline/axvline) digambar setelah legenda dan menembus
    # hurufnya kalau zorder legendanya tidak dinaikkan.
    leg.set_zorder(8)
    return leg


def simpan(fig, nama):
    for ax in fig.axes:
        if ax.get_label() != '<colorbar>':
            komafy(ax)
    p = os.path.join(FIGDIR, nama)
    fig.savefig(p, dpi=300, bbox_inches='tight')
    plt.close(fig)
    print('  %-28s %6.1f KB' % (nama, os.path.getsize(p) / 1024))


# =========================================================== (c) MEASURED
# Angka yang tidak dapat dihitung ulang oleh skrip ini. Setiap entri menyebut
# berkas asalnya.

# Rerata galat bertanda per anggota blend pada blok validasi maju, dibanding
# rerata galat bertanda di dalam sampel. Sumber: progress.md Sesi 47 §310, yang
# mengukurnya pada cache blok maju outputs/audit_v21_s27/forward_predictions.pkl
# (3 x 15 hari). Notebook Bagian 11.2 mencetak instrumen yang berbeda, yaitu
# rerata galat bertanda pada baris luar-lipatan, dan di sana `cat` ada di -1,86.
MEASURED_BIAS = [
    # (anggota, bias maju %RH, bias dalam sampel %RH, bobot blend)
    ('hbt',     +0.58, 0.000, 0.489),
    ('cat',     -2.89, -0.006, 0.217),
    ('enet',    +0.05, 0.000, 0.194),
    ('ridge_e', -0.38, 0.000, 0.050),
    ('l2',      +0.73, 0.000, 0.050),
]

# Tangga papan peringkat publik Kaggle. Sumber: README.md proyek, tabel
# "Riwayat leaderboard"; setiap baris adalah skor yang dikembalikan Kaggle atas
# satu berkas submission yang tersimpan di outputs/submissions/.
MEASURED_LB = [
    ('dasar 5 anggota\n+ NNLS',        3.04904),
    ('+ anggota L2\nkeenam',           3.02586),
    ('+ rekonsiliasi\nincrement',      2.86595),
    ('− anggota\nridge',               2.85383),
    ('+ bias diurnal\nper pita',       2.84953),
    ('+ de-bias level\nanggota cat',   2.82744),
]

# Anatomi galat, seluruhnya dari SATU frame: 6.480 baris luar-lipatan yang
# dihasilkan sembilan lipatan titik-asal bergulir, yaitu baris yang sama yang
# dipakai memasang bobot blend. Sumber: notebook Bagian 12.1, sel yang mencetak
# tabel pita 3 jam dan ketiga kemiringan kalibrasi. Satu frame dipakai untuk
# seluruh sub-bagian VI-B supaya naskah dan notebook tidak pernah berselisih
# angka; audit blok maju di outputs/audit_v21/breakdown.csv memberi 39,9 % pada
# frame lain dan sengaja tidak dicampur ke sini.
MEASURED_SLOPE = {'harian': 1.1475, 'dalam_hari': 1.0543, 'per_baris': 1.0628}
MEASURED_SHARE = {'harian': 0.389, 'dalam_hari': 0.611}

# Pita tiga jam pada baris luar-lipatan yang sama. (awal pita, bias %RH, RMSE,
# bagian SSE). Sumber: notebook Bagian 12.1.
MEASURED_PITA = [
    (0,  -1.0480, 6.2018, 0.2080),
    (3,  -0.5299, 5.6573, 0.1731),
    (6,  +0.8378, 4.5179, 0.1104),
    (9,  +0.9727, 3.7564, 0.0763),
    (12, +1.1105, 4.0422, 0.0884),
    (15, +0.4958, 4.0554, 0.0889),
    (18, -0.5961, 4.3399, 0.1018),
    (21, -1.0429, 5.3220, 0.1532),
]

# Pembanding sejawat. Setiap metode dipasang HANYA pada baris sebelum titik
# potong tiap lipatan lalu dinilai pada 15 hari berikutnya, pada sembilan
# lipatan dan 6.480 baris yang persis sama dengan stack. Enam baris pertama
# dihitung oleh outputs/baselines_summary.json; baris terakhir adalah stack yang
# dikapalkan, dari notebook Bagian 11.3.
MEASURED_PEMBANDING = [
    # (label, RMSE terkumpul, rerata lipatan, kelas)
    ('Rerata latih',                        18.8169, 18.8100, 'naif'),
    ('Persistensi profil hari terakhir',    13.3831, 13.0621, 'naif'),
    ('Proksi titik embun, tanpa parameter', 10.9333, 10.9098, 'fisis'),
    ('Klimatologi jam-hari',                10.1621, 10.0633, 'naif'),
    ('Regresi linear berganda, 24 kanal',    8.0840,  7.8410, 'statistik'),
    ('LightGBM tunggal, parameter bawaan',   5.7090,  5.6291, 'mesin'),
    ('Stack lengkap (naskah ini)',           4.8080,  4.6890, 'kami'),
]
# RMSE per lipatan untuk tiga metode teratas, dipakai panel (b).
# Sumber: outputs/baselines_summary.json dan notebook Bagian 11.3.
MEASURED_PERLIPATAN = {
    'Regresi linear berganda':  [9.8627, 10.5301, 9.9710, 8.7975, 7.8997,
                                 5.5269, 5.3249, 5.3832, 7.2730],
    'LightGBM tunggal':         [6.7828, 6.8255, 6.5959, 6.2539, 5.3783,
                                 4.4963, 4.2894, 4.7216, 5.3187],
    'Stack lengkap':            [5.9840, 6.0290, 5.7220, 5.4650, 4.5090,
                                 3.6770, 3.2610, 3.4070, 4.1480],
}

# Harga menjadikan seluruh jendela bergulir kausal, diukur dengan mengganti
# setiap jendela terpusat menjadi ekor-belakang dan membuang 12 kolom yang
# melihat ke depan, lalu melatih LightGBM yang sama pada lipatan yang sama.
# Sumber: outputs/causal_cost.json.
MEASURED_KAUSAL = {'terpusat': 5.7087, 'kausal': 8.2234, 'kolom_dibuang': 12}


# ====================================================== (a) DATASET MENTAH

def es(t):
    """Tekanan uap jenuh (hPa), rumus Magnus-Bolton. Verbatim dari pipeline."""
    return 6.112 * np.exp(17.67 * t / (t + 243.5))


def hampel(s, w=7, k=6.0, scale_win=289):
    """Penapis Hampel terpusat, verbatim dari final_pipeline.py.

    Skala diambil dari IQR bergulir yang panjang supaya penggal tenang tidak
    membuat setiap riak ditandai pencilan. Ambang k = 6 sengaja longgar.
    """
    med = s.rolling(w, center=True, min_periods=3).median()
    dev = (s - med).abs()
    scale = dev.rolling(scale_win, center=True, min_periods=48).quantile(0.75) * 2.5
    return s.mask(dev > (k * scale).clip(lower=1e-9))


def loo_quadratic_residual(v):
    """Residu tinggalkan-satu dari parabola pada 4 tetangga (t-2,t-1,t+1,t+2)."""
    v = np.asarray(v, float)
    out = np.full(len(v), np.nan)
    x = np.array([-2., -1., 1., 2.])
    for i in range(2, len(v) - 2):
        w = np.array([v[i - 2], v[i - 1], v[i + 1], v[i + 2]])
        if np.isnan(w).any() or np.isnan(v[i]):
            continue
        out[i] = v[i] - np.polyval(np.polyfit(x, w, 2), 0.0)
    return out


def muat():
    for f in ('train.csv', 'test.csv'):
        if not os.path.exists(os.path.join(DATA, f)):
            sys.exit('Dataset tidak ditemukan di %s' % DATA)
    tr = pd.read_csv(os.path.join(DATA, 'train.csv'), parse_dates=['datetime'])
    te = pd.read_csv(os.path.join(DATA, 'test.csv'), parse_dates=['datetime'])
    tr['is_test'], te['is_test'] = 0, 1
    te[TARGET] = np.nan
    al = pd.concat([tr, te], ignore_index=True).sort_values('datetime')
    g = al.set_index('datetime').asfreq('30min')
    g['is_test'] = g['is_test'].fillna(-1)
    is_tr = (g.is_test == 0).to_numpy() & g[TARGET].notna().to_numpy()
    is_te = (g.is_test == 1).to_numpy()
    return tr, te, g, is_tr, is_te


TR, TE, G, IS_TR, IS_TE = muat()
T_CLEAN = hampel(G.air_temperature).interpolate('time', limit_direction='both')
E_VAP = G[TARGET] * es(T_CLEAN) / 100.0          # tekanan uap aktual, hPa
ANGKA = {}                                        # dikumpulkan untuk dicetak


# --------------------------------------------------------------- Gambar 1
def gambar_01_target():
    fig, ax = plt.subplots(2, 1, figsize=(FULL_IN, 1.44), sharex=True,
                           gridspec_kw={'height_ratios': [1.35, 1.0], 'hspace': 0.46})
    ax[0].plot(G.index[IS_TR], G[TARGET][IS_TR], lw=0.45, color=C['obs'],
               label='air_humidity terlabel (2.933 baris latih)')
    ax[0].axvspan(G.index[IS_TE][0], G.index[IS_TE][-1], color=C['hi'], alpha=0.20,
                  label='jendela uji: 734 baris, tanpa label, 15,3 hari')
    ax[0].set_ylabel('%RH')
    ax[0].set_ylim(12, 104)
    ax[0].set_title('(a) Target sepanjang kalender dan blok yang harus diramalkan')

    ax[1].plot(G.index, G.air_temperature, lw=0.4, color=C['aux'], label='mentah')
    ax[1].axvspan(G.index[IS_TE][0], G.index[IS_TE][-1], color=C['hi'], alpha=0.20)
    ex = G.air_temperature[(G.air_temperature < 5) | (G.air_temperature > 45)]
    ax[1].scatter(ex.index, ex.values, s=7, color=C['bad'], zorder=3, linewidths=0,
                  label='ekskursi mustahil secara fisis (%d titik)' % len(ex))
    ax[1].set_ylabel('suhu (°C)')
    ax[1].set_ylim(-9, 70)
    ax[1].set_title('(b) Suhu udara mentah: prediktor terkuat sekaligus yang paling terkorupsi')
    ax[1].tick_params(axis='x', labelrotation=0)

    # Satu baris legenda untuk kedua panel, di luar sumbu. Lihat docstring
    # gambar ini: di dalam sumbu, kotaknya selalu menutupi data.
    h0, l0 = ax[0].get_legend_handles_labels()
    h1, l1 = ax[1].get_legend_handles_labels()
    fig.legend(h0 + h1, l0 + l1, loc='lower center', bbox_to_anchor=(0.5, -0.10),
               ncol=4, frameon=False, fontsize=5.8, handlelength=1.4,
               columnspacing=1.4, borderaxespad=0.0)
    simpan(fig, '01-target-dan-jendela.png')
    ANGKA['n_ekskursi_suhu'] = len(ex)


# --------------------------------------------------------------- Gambar 2
def gambar_02_residu_loo():
    kolom = [(TARGET, 'air_humidity: target'),
             ('air_temperature', 'air_temperature: prediktor'),
             ('pressure', 'pressure: prediktor')]
    fig, ax = plt.subplots(1, 3, figsize=(FULL_IN, 1.25))
    for a, (col, judul) in zip(ax, kolom):
        r = loo_quadratic_residual(G[col].to_numpy())
        r = r[np.isfinite(r)]
        rsd = 1.4826 * np.median(np.abs(r))
        rasio = np.std(r) / rsd
        warna = C['ok'] if rasio < 2 else C['bad']
        a.hist(np.clip(r / rsd, -12, 12), bins=90, color=warna, alpha=0.85)
        a.set_yscale('log')
        for s in (-6, 6):
            a.axvline(s, color='k', ls='--', lw=0.7)
        a.set_title('%s\nsd / sd$_{robus}$ = %s' % (judul, n(rasio, 2)))
        a.set_xlabel('residu LOO / sd robus')
        ANGKA['rasio_' + col] = round(float(rasio), 2)
    ax[0].set_ylabel('cacah (skala log)')
    simpan(fig, '02-residu-loo.png')


# --------------------------------------------------------------- Gambar 3
def kurva_oracle():
    """RMSE yang dicapai kalau `e` diketahui sempurna pada resolusi tertentu."""
    rows = []
    for w in [3, 5, 9, 13, 25, 49, 97, 193]:
        e_s = E_VAP.rolling(w, center=True, min_periods=2).mean()
        p = 100 * e_s / es(T_CLEAN)
        m = IS_TR & np.isfinite(p.to_numpy())
        rows.append((w / 2.0, float(np.sqrt(np.mean((p[m] - G[TARGET][m]) ** 2)))))
    day = G.index.normalize()
    sub = pd.DataFrame({'e': E_VAP, 'day': day})[IS_TR]
    dm = sub.groupby('day').e.mean()
    p_day = 100 * pd.Series(day, index=G.index).map(dm) / es(T_CLEAN)
    m = IS_TR & np.isfinite(p_day.to_numpy())
    rmse_day = float(np.sqrt(np.mean((p_day[m] - G[TARGET][m]) ** 2)))
    return pd.DataFrame(rows, columns=['jam', 'rmse']), rmse_day


def gambar_03_oracle():
    orc, rmse_day = kurva_oracle()
    fig, ax = plt.subplots(figsize=(COL_IN, 1.85))
    ax.plot(orc.jam, orc.rmse, 'o-', color=C['obs'], ms=3, lw=1.2,
            label='oracle: $e$ diketahui persis pada resolusi ini')
    ax.axhline(2.82744, color=C['pred'], ls='--', lw=1.1,
               label='model kami (RMSE publik 2,827)')
    ax.axhline(rmse_day, color=C['aux'], ls=':', lw=1.1,
               label='oracle satu tingkat per hari (%s)' % n(rmse_day, 2))
    # tempat model kami mendarat pada sumbu resolusi
    x = np.interp(2.82744, orc.rmse.values, orc.jam.values)
    ax.plot([x], [2.82744], marker='*', ms=9, color=C['pred'], zorder=5, ls='none')
    ax.annotate('setara mengetahui $e$\npada resolusi %s jam' % n(x, 1),
                xy=(x, 2.60), xytext=(26, 0.95), fontsize=6.0, ha='center',
                va='center',
                arrowprops=dict(arrowstyle='->', lw=0.6, color=C['pred'],
                                connectionstyle='arc3,rad=-0.25',
                                shrinkA=1, shrinkB=2),
                color=C['pred'])
    ax.set_xscale('log')
    ax.set_xticks([1.5, 3, 6, 12, 24, 48, 96])
    ax.set_xticklabels(['1,5', '3', '6', '12', '24', '48', '96'])
    ax.set_xlabel('resolusi waktu pengetahuan tentang $e$ (jam)')
    ax.set_ylabel('RMSE (%RH)')
    ax.set_title('Batas oracle tekanan uap')
    ax.legend(frameon=False, loc='upper left', bbox_to_anchor=(-0.02, 1.03),
              handlelength=1.6, borderaxespad=0.1, labelspacing=0.35)
    ax.set_ylim(0.10, 13.2)
    simpan(fig, '03-kurva-oracle.png')
    for _, r in orc.iterrows():
        ANGKA['oracle_%.1fj' % r.jam] = round(r.rmse, 3)
    ANGKA['oracle_harian'] = round(rmse_day, 3)
    ANGKA['resolusi_setara_model'] = round(float(x), 2)


# --------------------------------------------------------------- Gambar 4
def gambar_04_dekomposisi():
    sl = (G.index >= '2023-07-20') & (G.index <= '2023-07-30')
    fig, ax = plt.subplots(3, 1, figsize=(COL_IN, 2.9), sharex=True,
                           gridspec_kw={'hspace': 0.42})
    ax[0].plot(G.index[sl], G[TARGET][sl], lw=0.9, color=C['obs'])
    ax[0].set_ylabel('RH (%)')
    ax[0].set_title('(a) RH: bergerak cepat, ayunan 40 %RH per hari', fontsize=6.8)
    ax[1].plot(G.index[sl], es(T_CLEAN)[sl], lw=0.9, color=C['bad'])
    ax[1].set_ylabel('$e_s(T)$ (hPa)')
    ax[1].set_title('(b) Penyebut: diketahui persis di jendela uji', fontsize=6.8)
    ax[2].plot(G.index[sl], E_VAP[sl], lw=0.9, color=C['ok'])
    ax[2].set_ylabel('$e$ (hPa)')
    ax[2].set_title('(c) Pembilang: satu-satunya yang tidak diketahui', fontsize=6.8)
    ax[2].tick_params(axis='x', labelrotation=20)
    for a in ax:
        a.tick_params(labelsize=5.8)
    simpan(fig, '04-dekomposisi-fisis.png')
    sub = pd.DataFrame({'e': E_VAP, 'day': G.index.normalize()})[IS_TR]
    ANGKA['sd_rh'] = round(float(G[TARGET][IS_TR].std()), 2)
    ANGKA['sd_e'] = round(float(sub.e.std()), 2)
    ANGKA['sd_e_antar_hari'] = round(float(sub.groupby('day').e.mean().std()), 2)
    ANGKA['sd_e_dalam_hari'] = round(float(sub.groupby('day').e.std().mean()), 2)


# --------------------------------------------------------------- Gambar 5
def audit_dukungan():
    """Seberapa jauh setiap kolom eksogen bergeser dari latih ke uji."""
    kols = [c for c in TE.columns if c not in ('datetime', 'is_test')]
    rows = []
    for c in kols:
        a = TR[c].astype(float).dropna()
        b = TE[c].astype(float).dropna()
        if len(a) < 50 or len(b) < 20 or c in ('env_id', 'env_battery'):
            continue
        lo, hi = a.quantile(0.005), a.quantile(0.995)
        luar = float(((b < lo) | (b > hi)).mean())
        rasio_sd = float(b.std() / a.std()) if a.std() > 0 else 0.0
        rows.append(dict(kolom=c, luar_dukungan=luar, rasio_sd=rasio_sd))
    return pd.DataFrame(rows).sort_values('rasio_sd')


def gambar_05_dukungan():
    d = audit_dukungan()
    SOIL = [c for c in d.kolom if c.startswith('soil_')]
    WATER = [c for c in d.kolom if c.startswith('water_')]
    warna = [C['bad'] if c in SOIL + WATER else C['obs'] for c in d.kolom]
    fig, ax = plt.subplots(figsize=(COL_IN, 2.45))
    y = np.arange(len(d))
    ax.barh(y, d.rasio_sd, color=warna, height=0.72)
    ax.axvline(1.0, color='k', lw=0.7, ls='--')
    ax.set_yticks(y)
    ax.set_yticklabels(d.kolom, fontsize=5.4)
    ax.set_xlabel('sd(uji) / sd(latih)')
    ax.set_title('Audit dukungan per kolom eksogen')
    ax.grid(axis='y', alpha=0)
    from matplotlib.patches import Patch
    ax.set_xlim(0, 1.24)
    kotak(ax.legend(handles=[Patch(color=C['bad'], label='blok tanah & irigasi, dibuang'),
                             Patch(color=C['obs'], label='dipertahankan')],
              frameon=True, loc='lower right', fontsize=5.5,
              handlelength=1.1, handleheight=0.9, borderaxespad=0.15), alpha=1.0)
    simpan(fig, '05-audit-dukungan.png')
    ANGKA['n_kolom_hilang_dukungan'] = int((d.rasio_sd < 0.65).sum())


# --------------------------------------------------------------- Gambar 6
def gambar_06_rolling_origin():
    """Diagram skematis protokol titik-asal bergulir (9 lipatan, langkah 2 hari)."""
    fig, ax = plt.subplots(figsize=(COL_IN, 1.85))
    n_fold, step, val = 9, 2, 15
    mulai_min = 30
    for i in range(n_fold):
        origin = mulai_min + i * step
        y = n_fold - i
        ax.barh(y, origin, left=0, height=0.62, color=C['obs'], alpha=0.85)
        ax.barh(y, val, left=origin, height=0.62, color=C['hi'], alpha=0.95)
    ax.barh(0, 61, left=0, height=0.62, color=C['obs'], alpha=0.35)
    ax.barh(0, 15.3, left=61, height=0.62, color=C['pred'], alpha=0.85)
    ax.set_yticks(list(range(n_fold + 1)))
    ax.set_yticklabels(['tugas asli'] + ['lipatan %d' % i for i in range(n_fold, 0, -1)],
                       fontsize=5.8)
    ax.set_xlabel('hari sejak awal rekaman')
    ax.set_title('Validasi titik-asal bergulir')
    ax.grid(axis='y', alpha=0)
    from matplotlib.patches import Patch
    ax.set_xlim(0, 80)
    ax.legend(handles=[Patch(color=C['obs'], label='latih'),
                       Patch(color=C['hi'], label='validasi 15 hari'),
                       Patch(color=C['pred'], label='jendela uji sebenarnya')],
              frameon=False, ncol=3, fontsize=5.8, handlelength=1.1,
              handleheight=0.9, columnspacing=1.0,
              loc='upper center', bbox_to_anchor=(0.5, -0.32))
    simpan(fig, '06-titik-asal-bergulir.png')


# --------------------------------------------------------------- Gambar 11
def gambar_11_despiking():
    raw, cl = G.air_temperature, T_CLEAN
    # Jendela 12 hari dengan kepadatan penolakan tertinggi (4 titik dari 16).
    sl = (G.index >= '2023-08-05') & (G.index <= '2023-08-19')
    bad = (raw - cl).abs() > 0.01
    fig, ax = plt.subplots(figsize=(COL_IN, 1.55))
    ax.plot(G.index[sl], raw[sl], lw=0.8, color=C['aux'], label='mentah')
    ax.plot(G.index[sl], cl[sl], lw=0.8, color=C['obs'],
            label='Hampel ($k=6$) + interpolasi waktu')
    ax.scatter(G.index[sl & bad.to_numpy()], raw[sl & bad.to_numpy()],
               s=12, color=C['bad'], zorder=3, linewidths=0, label='titik ditolak')
    ax.set_ylabel('suhu (°C)')
    ax.tick_params(axis='x', labelrotation=20, labelsize=5.8)
    ax.set_ylim(-13, 78)
    ax.set_title('Despiking pada penggal dengan penolakan terpadat')
    ax.legend(frameon=False, ncol=3, loc='upper left', handlelength=1.2,
              columnspacing=0.9, borderaxespad=0.15, fontsize=5.8)
    simpan(fig, '11-despiking.png')

    r_raw = loo_quadratic_residual(raw.to_numpy())
    r_cl = loo_quadratic_residual(cl.to_numpy())
    ANGKA['despike_sd_sebelum'] = round(float(np.nanstd(r_raw)), 3)
    ANGKA['despike_sd_sesudah'] = round(float(np.nanstd(r_cl)), 3)
    ANGKA['despike_sdrobus_sebelum'] = round(float(1.4826 * np.nanmedian(np.abs(r_raw))), 3)
    ANGKA['despike_sdrobus_sesudah'] = round(float(1.4826 * np.nanmedian(np.abs(r_cl))), 3)
    ANGKA['despike_ekskursi_sebelum'] = int(np.nansum(np.abs(r_raw) > 2.5))
    ANGKA['despike_ekskursi_sesudah'] = int(np.nansum(np.abs(r_cl) > 2.5))
    ANGKA['despike_diubah'] = int(((raw.notna()) & ((raw - cl).abs() > 0.01)).sum())
    ANGKA['despike_persen'] = round(100 * ANGKA['despike_diubah'] / int(raw.notna().sum()), 2)
    ANGKA['despike_sisa_uji'] = int(np.nansum((np.abs(r_cl) > 2.5) & IS_TE))


# --------------------------------------------------------------- Gambar 12
def gambar_12_diurnal():
    tod = G.index.hour + G.index.minute / 60.0
    d = pd.DataFrame({'tod': tod, 'y': G[TARGET], 'T': T_CLEAN, 'co2': G.co2},
                     index=G.index)[IS_TR]
    prof = d.groupby('tod').agg(['mean', 'std'])
    fig, ax = plt.subplots(1, 3, figsize=(FULL_IN, 1.55))
    for a, (col, lab, c) in zip(ax, [('y', 'air_humidity (%RH)', C['obs']),
                                     ('T', 'air_temperature (°C)', C['bad']),
                                     ('co2', 'co2 (ppm)', C['ok'])]):
        m, s = prof[(col, 'mean')], prof[(col, 'std')]
        a.plot(m.index, m.values, color=c, lw=1.2)
        a.fill_between(m.index, m - s, m + s, color=c, alpha=0.16)
        a.set_xlim(0, 24)
        a.xaxis.set_major_locator(MultipleLocator(6))
        a.set_xlabel('jam-hari')
        a.set_title(lab)
    ax[0].set_ylabel('rerata ± 1 sd')
    simpan(fig, '12-klimatologi-diurnal.png')
    amp = prof[('y', 'mean')].max() - prof[('y', 'mean')].min()
    ANGKA['amplitudo_diurnal'] = round(float(amp), 2)
    ANGKA['ragam_dijelaskan_jam'] = round(
        float(d.groupby('tod').y.transform('mean').var() / d.y.var()), 3)
    ANGKA['korelasi_rh_suhu'] = round(float(d[['y', 'T']].corr().iloc[0, 1]), 4)


# --------------------------------------------------------------- Gambar 13
def gambar_13_proksi():
    Tmin = T_CLEAN.rolling(97, center=True, min_periods=6).min()
    proxy = 100 * es(Tmin) / es(T_CLEAN)
    m = IS_TR & np.isfinite(proxy.to_numpy())
    r = float(np.corrcoef(proxy[m], G[TARGET][m])[0, 1])
    rmse = float(np.sqrt(np.mean((proxy[m] - G[TARGET][m]) ** 2)))
    fig, ax = plt.subplots(1, 2, figsize=(FULL_IN, 1.28),
                           gridspec_kw={'width_ratios': [1.0, 1.55], 'wspace': 0.22})
    hb = ax[0].hexbin(proxy[m], G[TARGET][m], gridsize=42, cmap='Blues', mincnt=1,
                      linewidths=0)
    ax[0].plot([15, 100], [15, 100], color=C['bad'], lw=0.9, ls='--')
    ax[0].set_xlabel('proksi $100\\,e_s(T_{\\min,48\\mathrm{j}})/e_s(T)$')
    ax[0].set_ylabel('air_humidity (%RH)')
    ax[0].set_title('(a) Tanpa satu pun parameter terpasang: $r$ = %s' % n(r, 3))
    cb = fig.colorbar(hb, ax=ax[0], pad=0.02)
    cb.ax.tick_params(labelsize=5.4)
    cb.outline.set_linewidth(0.4)
    sl = (G.index >= '2023-07-20') & (G.index <= '2023-07-30')
    ax[1].plot(G.index[sl], G[TARGET][sl], lw=0.9, color=C['obs'], label='target')
    ax[1].plot(G.index[sl], proxy[sl], lw=0.9, color=C['hi'], label='proksi titik embun')
    kotak(ax[1].legend(frameon=True, ncol=2, loc='upper center',
                       borderaxespad=0.2))
    ax[1].set_ylabel('%RH')
    # Ruang di atas puncak 100 %RH supaya kotak legenda tidak memucatkan
    # puncak proksi yang justru sedang dibandingkan.
    ax[1].set_ylim(18, 122)
    ax[1].tick_params(axis='x', labelrotation=20, labelsize=5.8)
    ax[1].set_title('(b) Sepuluh hari, berdampingan')
    simpan(fig, '13-proksi-titik-embun.png')
    ANGKA['proksi_r'] = round(r, 3)
    ANGKA['proksi_rmse'] = round(rmse, 2)


# ================================================== (b) ARTEFAK EKSPERIMEN

def gambar_07_increment():
    """RMSE per blok validasi maju, sebelum vs sesudah rekonsiliasi increment."""
    p = os.path.join(OUTPUTS, 'audit_v20', 'increment_production_scores.csv')
    if not os.path.exists(p):
        print('  LEWAT 07: %s tidak ada' % p)
        return
    d = pd.read_csv(p)
    d = d[d.model == 'v16'].copy()
    label = {'B1_last15d': 'B1\n15 hari terakhir',
             'B2_prev15d': 'B2\n15 hari sebelumnya',
             'B3_shift7d': 'B3\ngeser 7 hari'}
    d['lab'] = d.block.map(label).fillna(d.block)
    x = np.arange(len(d))
    fig, ax = plt.subplots(figsize=(COL_IN, 1.75))
    ax.bar(x - 0.19, d.base, width=0.36, color=C['aux'], label='stack level saja')
    ax.bar(x + 0.19, d.increment, width=0.36, color=C['ok'],
           label='+ rekonsiliasi increment')
    for xi, (b, inc) in enumerate(zip(d.base, d.increment)):
        ax.annotate('−%s' % n(b - inc, 3), xy=(xi, max(b, inc)), xytext=(0, 3),
                    textcoords='offset points', ha='center', fontsize=5.8,
                    color=C['ok'], fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(d.lab, fontsize=5.8)
    ax.set_ylabel('RMSE (%RH)')
    ax.set_ylim(0, max(d.base) * 1.42)
    ax.set_title('Rekonsiliasi increment pada blok maju')
    ax.legend(frameon=False, loc='upper left', ncol=2, handlelength=1.1,
              columnspacing=0.9, borderaxespad=0.15)
    simpan(fig, '07-rekonsiliasi-increment.png')
    ANGKA['inc_delta_blok'] = [round(float(b - i), 3) for b, i in zip(d.base, d.increment)]


def gambar_09_anatomi():
    """Ke mana galat yang tersisa pergi.

    Ketiga panel dibaca dari satu frame: 6.480 baris luar-lipatan. Versi
    sebelumnya mencampur audit blok maju untuk panel (a) dan (b) dengan
    kemiringan dari frame luar-lipatan untuk panel (c); satu frame membuat
    setiap angka di sub-bagian VI-B dapat dicocokkan langsung dengan notebook.
    """
    jam = [p[0] for p in MEASURED_PITA]
    bias = [p[1] for p in MEASURED_PITA]
    share = [p[3] for p in MEASURED_PITA]
    lab = ['%02d' % j for j in jam]

    fig, ax = plt.subplots(1, 3, figsize=(FULL_IN, 1.20),
                           gridspec_kw={'wspace': 0.34})
    x = np.arange(len(jam))
    malam = [i for i, j in enumerate(jam) if j >= 21 or j < 6]
    warna = [C['bad'] if i in malam else C['obs'] for i in range(len(jam))]
    ax[0].bar(x, [s * 100 for s in share], color=warna, width=0.68)
    ax[0].set_xticks(x)
    ax[0].set_xticklabels(lab, fontsize=6.0)
    ax[0].set_ylabel('bagian dari total SSE (%)')
    ax[0].set_xlabel('awal pita 3 jam')
    ax[0].set_title('(a) Galat menumpuk pada pita malam')

    ax[1].bar(x, bias, color=[C['bad'] if b < 0 else C['ok'] for b in bias],
              width=0.68)
    ax[1].axhline(0, color='k', lw=0.6)
    ax[1].set_xticks(x)
    ax[1].set_xticklabels(lab, fontsize=6.0)
    ax[1].set_ylabel('galat bertanda (%RH)')
    ax[1].set_xlabel('awal pita 3 jam')
    ax[1].set_title('(b) Bias diurnal yang tersisa')

    sh = [MEASURED_SHARE['harian'], MEASURED_SHARE['dalam_hari']]
    ax[2].bar([0, 1], [s * 100 for s in sh], color=[C['pred'], C['soft']], width=0.6)
    for i, s in enumerate(sh):
        ax[2].annotate('%.0f %%' % (s * 100), xy=(i, s * 100), xytext=(0, 3),
                       textcoords='offset points', ha='center', fontsize=6.6,
                       fontweight='bold')
    ax[2].set_xticks([0, 1])
    ax[2].set_xticklabels(['offset per hari\n(kemiringan %s)'
                           % n(MEASURED_SLOPE['harian'], 3),
                           'bentuk di dalam hari\n(kemiringan %s)'
                           % n(MEASURED_SLOPE['dalam_hari'], 3)], fontsize=6.0)
    ax[2].set_ylabel('bagian dari total SSE (%)')
    ax[2].set_ylim(0, 78)
    ax[2].set_title('(c) Pemadatan seluruhnya di tingkat harian')
    simpan(fig, '09-anatomi-galat.png')
    ANGKA['day_level_share'] = MEASURED_SHARE['harian']
    ANGKA['within_day_share'] = MEASURED_SHARE['dalam_hari']
    ANGKA['sse_malam'] = round(sum(share[i] for i in malam), 3)
    ANGKA['sse_siang'] = round(share[3] + share[4], 3)
    ANGKA['sse_share_pita'] = {l: round(s, 3) for l, s in zip(lab, share)}


def gambar_14_pembanding():
    """Ladder pembanding sejawat pada protokol dan baris yang persis sama."""
    lab = [p[0] for p in MEASURED_PEMBANDING]
    val = [p[1] for p in MEASURED_PEMBANDING]
    kls = [p[3] for p in MEASURED_PEMBANDING]
    warna = {'naif': C['aux'], 'fisis': C['hi'], 'statistik': C['obs'],
             'mesin': C['ok'], 'kami': C['pred']}

    fig, ax = plt.subplots(1, 2, figsize=(FULL_IN, 1.28),
                           gridspec_kw={'wspace': 0.30, 'width_ratios': [1.32, 1.0]})
    y = np.arange(len(lab))[::-1]
    ax[0].barh(y, val, color=[warna[k] for k in kls], height=0.66)
    for yi, v in zip(y, val):
        ax[0].annotate(n(v, 2), xy=(v, yi), xytext=(3, 0), textcoords='offset points',
                       va='center', fontsize=6.0,
                       fontweight='bold' if v == val[-1] else 'normal')
    ax[0].set_yticks(y)
    ax[0].set_yticklabels(lab, fontsize=6.0)
    ax[0].set_xlabel('RMSE terkumpul pada 6.480 baris luar-lipatan (%RH)')
    ax[0].set_xlim(0, max(val) * 1.16)
    ax[0].grid(axis='y', visible=False)
    ax[0].set_title('(a) Setiap metode dinilai pada lipatan yang sama')

    gaya = {'Regresi linear berganda': (C['obs'], 'o', '-'),
            'LightGBM tunggal': (C['ok'], 's', '-'),
            'Stack lengkap': (C['pred'], 'D', '-')}
    x = np.arange(1, 10)
    for nm, seri in MEASURED_PERLIPATAN.items():
        c, mk, ls = gaya[nm]
        ax[1].plot(x, seri, ls, color=c, marker=mk, ms=2.6, lw=1.0, label=nm)
    ax[1].set_xticks(x)
    ax[1].set_xlabel('lipatan titik-asal bergulir')
    ax[1].set_ylabel('RMSE (%RH)')
    # Label ditulis langsung di ujung kanan tiap garis. Kotak legenda sebesar
    # tiga baris menutupi kurva teratas pada panel setipis ini, dan ketiga garis
    # sudah terpisah jelas di lipatan terakhir.
    for nm, seri in MEASURED_PERLIPATAN.items():
        c = gaya[nm][0]
        ax[1].annotate(nm, xy=(9.25, seri[-1]), fontsize=5.6, color=c,
                       va='center', ha='left')
    ax[1].set_xlim(0.5, 15.6)
    ax[1].set_title('(b) Urutannya sama di sembilan lipatan')
    simpan(fig, '14-pembanding.png')
    for p in MEASURED_PEMBANDING:
        ANGKA['pemb_' + p[0][:18]] = p[1]
    ANGKA['pemb_margin_lgbm'] = round(
        100 * (MEASURED_PEMBANDING[-2][1] - MEASURED_PEMBANDING[-1][1])
        / MEASURED_PEMBANDING[-2][1], 1)
    ANGKA['kausal_delta'] = round(MEASURED_KAUSAL['kausal']
                                  - MEASURED_KAUSAL['terpusat'], 3)
    ANGKA['kausal_persen'] = round(100 * ANGKA['kausal_delta']
                                   / MEASURED_KAUSAL['terpusat'], 1)



# ======================================================= (c) KONSTANTA UKUR

def gambar_08_bias_anggota():
    nama = [b[0] for b in MEASURED_BIAS]
    maju = [b[1] for b in MEASURED_BIAS]
    dalam = [b[2] for b in MEASURED_BIAS]
    bobot = [b[3] for b in MEASURED_BIAS]
    x = np.arange(len(nama))
    fig, ax = plt.subplots(figsize=(COL_IN, 1.75))
    warna = [C['bad'] if abs(v) > 1.5 else C['obs'] for v in maju]
    ax.bar(x, maju, width=0.52, color=warna, label='bias maju (luar-lipatan)')
    # Bias di dalam sampel praktis nol untuk kelima anggota; digambar sebagai
    # penanda, bukan batang, supaya tetap terlihat pada skala ini.
    ax.plot(x, dalam, 'D', ms=3.2, color='k', mfc='white', mew=0.8, ls='none',
            label='bias di dalam sampel (≈ 0)')
    ax.axhline(0, color='k', lw=0.6)
    # Keterangan dinaikkan ke ruang kosong di kanan atas batang `cat`; versi
    # sebelumnya duduk sejajar legenda di kiri bawah dan keduanya bertabrakan.
    ax.annotate('−2,89 %RH: cacat yang tidak\nterlihat instrumen mana pun',
                xy=(1.30, -2.30), xytext=(2.05, -1.35), fontsize=5.6, color=C['bad'],
                va='center', ha='left',
                arrowprops=dict(arrowstyle='->', lw=0.6, color=C['bad'],
                                shrinkA=0, shrinkB=2))
    ax.set_xticks(x)
    ax.set_xticklabels(['%s\n$w$ = %s' % (a, n(b, 3)) for a, b in zip(nama, bobot)],
                       fontsize=5.8)
    ax.set_ylabel('rerata galat bertanda (%RH)')
    # Legenda naik ke pita kosong di atas batang. Di kiri bawah ia menutupi
    # ujung batang `cat`, yaitu justru angka yang sedang dibicarakan gambar ini.
    ax.set_ylim(-3.4, 2.5)
    ax.set_title('Bias level per anggota blend')
    kotak(ax.legend(frameon=True, loc='upper left', ncol=2, fontsize=5.8,
                    handlelength=1.2, columnspacing=1.0, borderaxespad=0.15))
    simpan(fig, '08-bias-anggota.png')


def gambar_10_leaderboard():
    lab = [a for a, _ in MEASURED_LB]
    sk = [b for _, b in MEASURED_LB]
    x = np.arange(len(sk))
    fig, ax = plt.subplots(figsize=(COL_IN, 1.75))
    ax.step(x, sk, where='mid', color=C['obs'], lw=1.1)
    ax.plot(x, sk, 'o', color=C['obs'], ms=3.4)
    for i in range(1, len(sk)):
        d = sk[i] - sk[i - 1]
        ax.annotate(('+' if d > 0 else '−') + n(abs(d), 3),
                    xy=(i, sk[i]), xytext=(0, -11),
                    textcoords='offset points', ha='center', fontsize=5.8,
                    fontweight='bold',
                    color=C['ok'] if d < 0 else C['bad'])
    ax.plot([2], [sk[2]], marker='*', ms=11, color=C['pred'], ls='none', zorder=5)
    ax.set_xticks(x)
    ax.set_xticklabels(lab, fontsize=5.4)
    ax.set_ylabel('RMSE papan peringkat publik')
    ax.set_ylim(2.76, 3.10)
    ax.set_title('Tangga skor: satu langkah struktural, sisanya orde kedua')
    simpan(fig, '10-tangga-leaderboard.png')


# ============================================ angka untuk tabel di naskah
# Tidak menghasilkan gambar, tetapi setiap angka yang muncul di tabel naskah
# harus keluar dari sini supaya dapat diperiksa ulang.

AGRO = ['gdd', 'standard_day_degree', 'daily_mean_temperature',
        'daily_max_above_Tbase', 'daily_max', 'daily_max_reduction',
        'ontario_units']


def angka_anatomi():
    kol = [c for c in TE.columns if c not in ('datetime', 'is_test', TARGET)]
    ANGKA['n_latih'] = len(TR)
    ANGKA['n_uji'] = len(TE)
    ANGKA['n_eksogen'] = len(kol)
    ANGKA['rentang_latih'] = '%s -> %s' % (TR.datetime.min(), TR.datetime.max())
    ANGKA['rentang_uji'] = '%s -> %s' % (TE.datetime.min(), TE.datetime.max())
    ANGKA['target_mean'] = round(float(TR[TARGET].mean()), 2)
    ANGKA['target_sd'] = round(float(TR[TARGET].std()), 2)
    ANGKA['target_min'] = round(float(TR[TARGET].min()), 2)
    ANGKA['target_maks'] = round(float(TR[TARGET].max()), 2)
    inti = [c for c in kol if c not in ('env_id', 'env_battery')]
    ANGKA['hilang_latih_pct'] = (round(float(TR[inti].isna().mean().min() * 100), 1),
                                 round(float(TR[inti].isna().mean().max() * 100), 1))
    ANGKA['hilang_uji_pct'] = (round(float(TE[inti].isna().mean().min() * 100), 1),
                               round(float(TE[inti].isna().mean().max() * 100), 1))
    ANGKA['battery_hilang_pct'] = round(float(TR.env_battery.isna().mean() * 100), 1)


def angka_pergeseran():
    ANGKA['T_latih'] = round(float(T_CLEAN[IS_TR].mean()), 2)
    ANGKA['T_uji'] = round(float(T_CLEAN[IS_TE].mean()), 2)
    q1 = float(np.nanquantile(T_CLEAN[IS_TR], 0.25))
    ANGKA['frac_uji_kuartil_dingin'] = round(float((T_CLEAN[IS_TE] < q1).mean()), 3)
    for lab, m in (('latih', IS_TR), ('uji', IS_TE)):
        s = pd.Series(T_CLEAN[m].values, index=G.index[m])
        ANGKA['Tmin_harian_' + lab] = round(float(s.resample('D').min().mean()), 2)
        ANGKA['Tmaks_harian_' + lab] = round(float(s.resample('D').max().mean()), 2)


def angka_agronomi():
    """Rekayasa balik blok agronomi: dua rekonstruksi bebas atas T_min harian."""
    terbaik = None
    for off in range(24):
        key = (G.index - pd.Timedelta(hours=off)).normalize()
        w = float(G.loc[IS_TR, AGRO].groupby(key[IS_TR]).std().mean().mean())
        if terbaik is None or w < terbaik[1]:
            terbaik = (off, w)
    ANGKA['batas_hari_agro'] = '%02d:00' % terbaik[0]

    key = (G.index - pd.Timedelta(hours=terbaik[0])).normalize()
    D = G[AGRO].groupby(key).median()
    # Identitas 1: daily_mean_temperature = (T_max + T_min)/2
    D['Tmin_a'] = 2 * D.daily_mean_temperature - D.daily_max
    # Identitas 2: Ontario Crop Heat Unit, CHU = (Y_max + Y_min)/2 dipecahkan
    # untuk T_min. Y_max = 3,33(T-10) - 0,084(T-10)^2 ; Y_min = 1,8(T - 4,4).
    ymax = 3.33 * (D.daily_max - 10) - 0.084 * (D.daily_max - 10) ** 2
    D['Tmin_b'] = (2 * D.ontario_units - ymax) / 1.8 + 4.4
    D = D.join(G.air_temperature.groupby(key).min().rename('sensor_mentah'))
    D = D.join(T_CLEAN.groupby(key).min().rename('sensor_bersih'))
    D = D.join(G.groupby(key).size().rename('n'))
    D = D[D.n >= 40]
    ANGKA['agro_n_hari'] = int(len(D))
    ANGKA['agro_r_dua_jalur'] = round(float(D[['Tmin_a', 'Tmin_b']].corr().iloc[0, 1]), 5)
    ANGKA['agro_sd_dua_jalur'] = round(float((D.Tmin_a - D.Tmin_b).std()), 4)
    ANGKA['agro_r_sensor_mentah'] = round(float(D[['Tmin_a', 'sensor_mentah']]
                                                .corr().iloc[0, 1]), 3)
    ANGKA['agro_r_sensor_bersih'] = round(float(D[['Tmin_a', 'sensor_bersih']]
                                                .corr().iloc[0, 1]), 3)
    ANGKA['agro_sd_vs_sensor'] = round(float((D.Tmin_a - D.sensor_bersih).std()), 3)
    d1 = (G.daily_max - G.daily_max_above_Tbase)
    d2 = (G.daily_mean_temperature - G.standard_day_degree)
    ANGKA['agro_identitas_1'] = (round(float(d1.mean()), 3), round(float(d1.std()), 3))
    ANGKA['agro_identitas_2'] = (round(float(d2.mean()), 3), round(float(d2.std()), 3))
    dalam = G[AGRO].groupby(key).std().drop(columns=['gdd']).mean()
    ANGKA['agro_derau_dalam_hari'] = (round(float(dalam.min()), 3),
                                      round(float(dalam.max()), 3))
    # Terjemahan derau sensor menjadi derau %RH pada proksi titik embun:
    # dRH/dT sekitar -3,6 %RH per °C pada RH 60 %.
    ANGKA['agro_derau_dalam_RH'] = round(ANGKA['agro_sd_vs_sensor'] * 3.6, 2)


def tulis_tabel_kanal():
    """Audit per kanal untuk tabel lampiran, ditulis sebagai JSON.

    Tabelnya 24 baris; menyalinnya dengan tangan ke `tables.py` adalah undangan
    salah ketik yang tidak akan pernah ketahuan. `tables.py` membacanya dari
    sini, jadi angkanya tetap berasal dari satu tempat.
    """
    import json
    kols = [c for c in TE.columns if c not in ('datetime', 'is_test', TARGET)]
    baris = []
    for c in kols:
        a = TR[c].astype(float)
        b = TE[c].astype(float)
        ad, bd = a.dropna(), b.dropna()
        rasio = float(bd.std() / ad.std()) if len(ad) > 1 and ad.std() > 0 else 0.0
        baris.append({
            'kolom': c,
            'hilang_latih': round(float(a.isna().mean() * 100), 1),
            'hilang_uji': round(float(b.isna().mean() * 100), 1),
            'rerata_latih': round(float(ad.mean()), 2) if len(ad) else None,
            'rerata_uji': round(float(bd.mean()), 2) if len(bd) else None,
            'rasio_sd': round(rasio, 2),
            'dipakai': not (c.startswith('soil_') or c.startswith('water_')
                            or c in ('env_id', 'env_battery')),
        })
    p = os.path.join(FIGDIR, 'tabel_kanal.json')
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(baris, f, indent=1, ensure_ascii=False)
    print('  %-28s %6.1f KB' % ('tabel_kanal.json', os.path.getsize(p) / 1024))


def angka_autokorelasi():
    y = pd.Series(G[TARGET][IS_TR].values)
    ANGKA['autokorelasi_lag1_target'] = round(float(y.autocorr(1)), 3)
    hari = pd.Series(G[TARGET][IS_TR].values, index=G.index[IS_TR]).resample('D').mean()
    ANGKA['n_hari_efektif'] = int(hari.notna().sum())


# ------------------------------------------------------------------- utama
def main():
    print('Dataset : %s' % DATA)
    print('Keluaran: %s\n' % FIGDIR)
    gambar_01_target()
    gambar_02_residu_loo()
    gambar_03_oracle()
    gambar_04_dekomposisi()
    gambar_05_dukungan()
    gambar_06_rolling_origin()
    gambar_07_increment()
    gambar_08_bias_anggota()
    gambar_09_anatomi()
    gambar_14_pembanding()
    gambar_10_leaderboard()
    gambar_11_despiking()
    gambar_12_diurnal()
    gambar_13_proksi()

    tulis_tabel_kanal()

    angka_anatomi()
    angka_pergeseran()
    angka_agronomi()
    angka_autokorelasi()

    print('\nAngka yang dihitung ulang skrip ini (salin ke content.py bila berubah):')
    for k in sorted(ANGKA):
        print('  %-26s %s' % (k, ANGKA[k]))


if __name__ == '__main__':
    main()
