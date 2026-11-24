# -*- coding: utf-8 -*-
"""Pembanding sejawat dan kendali kausalitas untuk Bagian VI-A dan VI-F.

Skrip ini menghasilkan angka yang dikutip Tabel IV dan Gambar 6 naskah, lalu
menuliskannya ke `outputs/baselines_summary.json` dan `outputs/causal_cost.json`.
`make_figures.py` membaca kedua berkas itu lewat blok MEASURED_PEMBANDING,
MEASURED_PERLIPATAN, dan MEASURED_KAUSAL.

Yang membuat angkanya sebanding: setiap metode memakai `rolling_origins()` dan
`make_features()` dari `final_pipeline.py`, dipasang hanya pada baris sebelum
titik potong tiap lipatan, lalu dinilai pada 15 hari berikutnya. Baris yang
dinilai karena itu identik dengan 6.480 baris luar-lipatan yang dipakai stack
untuk memasang bobot blend, sehingga RMSE terkumpulnya dapat diletakkan
berdampingan dengan 4,8080 milik stack tanpa penyesuaian apa pun.

RMSE stack sendiri TIDAK dihitung di sini. Ia datang dari notebook Bagian 11.3,
karena melatih ulang seluruh stack hanya untuk satu angka yang sudah tercetak
di sana adalah pemborosan yang juga membuka peluang angkanya berbeda.

Jalankan dari folder `paper/script/`:

    python pembanding.py

Kira-kira satu menit; hasilnya deterministik.
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(os.path.dirname(HERE))     # ...\NSC UB
sys.path.insert(0, PROJECT)
os.chdir(PROJECT)                                    # final_pipeline membaca 'Dataset/'

import lightgbm as lgb                                        # noqa: E402
from sklearn.impute import SimpleImputer                      # noqa: E402
from sklearn.linear_model import LinearRegression             # noqa: E402
from sklearn.pipeline import make_pipeline                    # noqa: E402
from sklearn.preprocessing import StandardScaler              # noqa: E402

import final_pipeline as fp                                   # noqa: E402

OUTPUTS = os.path.join(PROJECT, 'outputs')

# RMSE stack pada baris dan lipatan yang sama, dari notebook Bagian 11.3
# ("terkumpul 4.9040 -> 4.8080" dan "CV setelah rekonsiliasi: rerata 4.6890").
STACK_POOLED = 4.8080
STACK_MEAN_FOLD = 4.6890


def siapkan():
    g = fp.load_grid()
    idx = g.index
    is_tr = (g.is_test == 0).values
    y = g[fp.TARGET]
    tr_idx = idx[is_tr & y.notna().values]
    return g, y, tr_idx, fp.rolling_origins(tr_idx)


def pembanding():
    """Enam metode pembanding pada protokol yang sama."""
    t0 = time.time()
    g, y, tr_idx, folds = siapkan()
    F = fp.make_features(g)
    bersih = fp.clean_exog(g)
    exo = [c for c in fp.FAST + fp.SOIL + fp.DAILY if c in g.columns]
    tod = pd.Series(F['tod'].values, index=g.index)

    baris = []
    for fi, (vs, ve) in enumerate(folds):
        v = tr_idx[(tr_idx > vs) & (tr_idx <= ve)]
        t = tr_idx[tr_idx <= vs]
        if len(t) < 300 or len(v) < 50:
            continue
        yt = y.loc[t]
        d = pd.DataFrame({'fold': fi, 'dt': v, 'y': y.loc[v].values})

        # 1. rerata latih
        d['naif'] = yt.mean()

        # 2. klimatologi jam-hari: satu rerata per slot setengah-jaman
        prof = yt.groupby(tod.loc[t].values).mean()
        d['klim'] = pd.Series(tod.loc[v].values).map(prof).ffill().bfill().values

        # 3. persistensi: profil diurnal hari penuh terakhir sebelum titik potong
        awal = t[-1].normalize() - pd.Timedelta(days=1)
        hari = yt[(t >= awal) & (t < awal + pd.Timedelta(days=1))]
        prof2 = hari.groupby(tod.loc[hari.index].values).mean()
        s = pd.Series(tod.loc[v].values)
        d['persist'] = s.map(prof2).fillna(s.map(prof)).ffill().bfill().values

        # 4. proksi titik embun bebas-parameter, Persamaan (4) naskah
        Tc = bersih['air_temperature']
        tmin = Tc.rolling(48, center=True, min_periods=6).min()
        d['fisis'] = np.clip(100 * fp.es(tmin.loc[v].values) / fp.es(Tc.loc[v].values), 5, 100)

        # 5. regresi linear berganda atas kanal eksogen yang sudah dibersihkan
        ols = make_pipeline(SimpleImputer(strategy='median'), StandardScaler(),
                            LinearRegression())
        ols.fit(bersih.loc[t, exo], yt)
        d['ols'] = np.clip(ols.predict(bersih.loc[v, exo]), 5, 100)

        # 6. LightGBM tunggal, parameter bawaan, matriks fitur yang sama
        m = lgb.LGBMRegressor(random_state=0, verbose=-1)
        m.fit(F.loc[t], yt)
        d['lgbm1'] = np.clip(m.predict(F.loc[v]), 5, 100)

        baris.append(d)
        print('  lipatan %d: latih %d  val %d  [%.0f s]'
              % (fi, len(t), len(v), time.time() - t0), flush=True)

    D = pd.concat(baris, ignore_index=True)
    D.to_csv(os.path.join(OUTPUTS, 'baselines_oof.csv'), index=False)

    METODE = [('naif', 'Rerata latih'),
              ('persist', 'Persistensi profil hari terakhir'),
              ('fisis', 'Proksi titik embun, tanpa parameter'),
              ('klim', 'Klimatologi jam-hari'),
              ('ols', 'Regresi linear berganda, 24 kanal'),
              ('lgbm1', 'LightGBM tunggal, parameter bawaan')]
    hasil = {}
    print('\n%-40s %10s %10s' % ('metode', 'terkumpul', 'rerata lipatan'))
    for k, lab in METODE:
        pooled = fp.rmse(D.y, D[k])
        perf = D.groupby('fold').apply(lambda x, k=k: fp.rmse(x.y, x[k]))
        hasil[k] = dict(label=lab, pooled=round(pooled, 4),
                        mean_fold=round(float(perf.mean()), 4),
                        per_fold=[round(x, 4) for x in perf.values])
        print('%-40s %10.4f %10.4f' % (lab, pooled, perf.mean()))
    print('%-40s %10.4f %10.4f  (notebook Bagian 11.3)'
          % ('Stack lengkap', STACK_POOLED, STACK_MEAN_FOLD))
    print('baris dinilai: %d' % len(D))

    with open(os.path.join(OUTPUTS, 'baselines_summary.json'), 'w') as f:
        json.dump(hasil, f, indent=1)
    return hasil


def kausal():
    """Harga menjadikan seluruh jendela bergulir kausal.

    Dua hal harus diubah sekaligus, karena mengubah salah satunya saja tidak
    menghasilkan pipeline yang benar-benar kausal: setiap jendela `rolling`
    dipaksa ekor-belakang, dan kolom yang memuat geseran ke depan dibuang.
    Pembandingnya satu LightGBM parameter bawaan pada lipatan yang sama, supaya
    selisih yang terukur murni efek jendela dan bukan efek model.
    """
    t0 = time.time()
    g, y, tr_idx, folds = siapkan()

    asli = pd.core.generic.NDFrame.rolling

    def rolling_kausal(self, *a, **k):
        k = dict(k)
        k['center'] = False
        return asli(self, *a, **k)

    F_pusat = fp.make_features(g)
    pd.core.generic.NDFrame.rolling = rolling_kausal
    try:
        F_kausal = fp.make_features(g)[F_pusat.columns]
    finally:
        pd.core.generic.NDFrame.rolling = asli

    depan = [c for c in F_pusat.columns
             if any(c.endswith('_s%d' % l) for l in (-4, -2, -1)) or c.endswith('_slope')]
    kol_kausal = [c for c in F_pusat.columns if c not in depan]
    print('kolom yang melihat ke depan, dibuang di varian kausal: %d' % len(depan))

    hasil = {}
    for nama, F, cols in (('terpusat', F_pusat, list(F_pusat.columns)),
                          ('kausal', F_kausal, kol_kausal)):
        per = []
        for fi, (vs, ve) in enumerate(folds):
            v = tr_idx[(tr_idx > vs) & (tr_idx <= ve)]
            t = tr_idx[tr_idx <= vs]
            if len(t) < 300 or len(v) < 50:
                continue
            m = lgb.LGBMRegressor(random_state=0, verbose=-1)
            m.fit(F.loc[t, cols], y.loc[t])
            per.append((v, np.clip(m.predict(F.loc[v, cols]), 5, 100)))
        yy = np.concatenate([y.loc[v].values for v, _ in per])
        pp = np.concatenate([p for _, p in per])
        hasil[nama] = dict(pooled=round(fp.rmse(yy, pp), 4),
                           per_fold=[round(fp.rmse(y.loc[v].values, p), 4) for v, p in per])
        print('%-9s terkumpul %.4f  [%.0f s]' % (nama, hasil[nama]['pooled'],
                                                 time.time() - t0))
    hasil['kolom_dibuang'] = len(depan)
    hasil['delta'] = round(hasil['kausal']['pooled'] - hasil['terpusat']['pooled'], 4)
    hasil['delta_persen'] = round(100 * hasil['delta'] / hasil['terpusat']['pooled'], 1)
    print('harga kausalitas: %+.4f RMSE (%+.1f %%)' % (hasil['delta'], hasil['delta_persen']))

    with open(os.path.join(OUTPUTS, 'causal_cost.json'), 'w') as f:
        json.dump(hasil, f, indent=1)
    return hasil


if __name__ == '__main__':
    print('=== pembanding sejawat ===')
    pembanding()
    print('\n=== kendali kausalitas ===')
    kausal()
    print('\nSelesai. Perbarui blok MEASURED_* di make_figures.py kalau angkanya berubah.')
