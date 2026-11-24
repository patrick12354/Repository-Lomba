# Orang 3 — Edge Hunter

**Misi:** temukan 1–3 edge baru yang **terbukti dari data**, tidak tertulis di brief, dan hampir pasti tidak ditemukan tim lain. Edge terbaik sebelum **01.00** masuk ke app. Setelah itu, edge hanya masuk deck dan bank Q&A.

Kamu **tidak** menulis kode app. Kamu menulis script analisis dan kartu edge.

## Baca dulu (supaya tidak mengulang)

- `docs/03_EDGE_PROPOSALS.md`: E1–E5 yang sudah lolos, plus **daftar ide yang sudah gugur**. Jangan diuji ulang.
- `docs/01_EDA_FINDINGS.md`: F1–F11. Bagian 3 berisi daftar jebakan kualitas data.
- `analysis/build_mat.py`: `build()` menghasilkan tabel level material yang sudah benar.
  - Harga = `PO-Item Amount` adalah **harga satuan**.
  - Lead time = PR-Date → PO-Delivery Date.
- Brief: `docs/CALIBER 2026 - Final Case Brief.pdf`, hal. 5–6 (poin "participants should consider").

## Standar bukti (wajib, karena data ini dummy dan banyak relasinya acak)

Setiap edge harus melewati 4 cek berikut:

1. **Angka dari script.** Simpan di `analysis/edge_<nama>.py`, jalankan dengan `py analysis/edge_<nama>.py`, dan simpan outputnya ke `analysis/edge_<nama>_output.txt`.
2. **Dibandingkan dengan baseline.** Contohnya acak, popularitas, atau metode klasik. Sinyal yang tidak lebih baik dari baseline berarti gugur. Contoh nyata: teks notif → part hanya 37,6% vs baseline popularitas 49,7%, jadi gugur.
3. **Tanpa leakage waktu.** Kalau berupa prediksi, latih di masa lalu dan uji di masa depan. Stok di `BoM` adalah snapshot *akhir*, jadi jangan dipakai sebagai fitur masa lalu.
4. **Ada "so what" + fitur + momen demo 1 kalimat.** Kalau tidak bisa didemokan atau tidak mengubah keputusan stok, edge itu cuma trivia.

Ide yang gugur juga ditulis di tabel "gugur", lengkap dengan angkanya. Ini mencegah tim membuat klaim yang salah.

## Daftar hipotesis yang belum diuji (urut dari yang paling menjanjikan)

1. **Tipe order lain = event lain?**
   - Order 2090 melonjak di Jul–Agu 2025 (223 dan 222 baris) dan Jun 2026 (144 baris). Apakah ini siklus decoking furnace atau mini-shutdown dengan periode sekitar 11 bulan?
   - Kalau periodik, berarti ada **event kedua yang bisa diprediksi tanggalnya**, sehingga E1 bisa diperluas jadi "event calendar".
   - Cek juga arti order 2040/2050/2060 dari jenis material dan qty-nya.
2. **Siklus furnace (F10).**
   - Notif "Decoking follow" (57), "Peep door", "Hot spot", dan "Burner" di BF-1xx.
   - Apakah konsumsi refractory/firebrick mengikuti jeda antar-notif decoking per furnace? Kalau iya, demand refractory bisa diprediksi per furnace.
3. **Emergency must-stock list.**
   - Part apa yang di-issue ≤ 1 hari setelah notif N2 (Emergency)?
   - Bandingkan dengan stok sekarang: berapa yang stoknya 0 atau di bawah Min?
   - Output yang diharapkan: daftar insurance spare yang wajib ada, ini sinyal reliability yang kuat.
4. **Orphan stock / obsolescence.**
   - Material yang semua FL tempat terpasangnya tidak punya PM maupun notif selama 17 bulan, tapi stoknya > 0.
   - Berapa nilainya (harga × stok)? Apakah ini kandidat dispose yang valid?
   - Ini melengkapi Inventory Health di brief, bagian "potentially obsolete".
5. **Gelombang overhaul PM 2027.**
   - Banyak cycle 5 / 10 YEARLY. Apakah ada bulan di 2027 di mana banyak overhaul besar (pump, CV, HE) jatuh bersamaan?
   - Kalau ada, itu "shutdown tersembunyi" yang belum masuk perencanaan stok.
6. **Drift lead time supplier.**
   - Apakah lead time atau slip supplier memburuk dari 2025 ke 2026?
   - Kalau iya, lead time statis di Min–Max makin salah. Ini bisa jadi argumen untuk *dynamic lead time*.
7. **Konsistensi kit per FL.**
   - FL yang diservis berulang kali: apakah set material per order mirip (Jaccard)?
   - Kalau mirip, bisa dibuat "kit otomatis per equipment" untuk pre-staging di gudang.
8. **Pooling PX vs PY.** Material yang sama dipakai di plant PX dan PY. Hitung berapa safety stock yang bisa dihemat kalau Min dipool (√n effect).
9. **Rekomendasi PR otomatis vs keputusan historis.**
   - Kalau aturan ROP kita diterapkan mundur di 2025–2026, berapa PR historis yang akan kita tahan (karena stok sudah cukup) dan berapa yang akan kita majukan?
   - Hati-hati: tidak ada histori stok. Gunakan rekonstruksi E5 dengan caveat.

Hipotesis milikmu sendiri juga boleh. Prioritaskan yang langsung menjawab poin-poin di brief hal. 5–6.

## Output yang diserahkan

**Kartu edge** ditambahkan ke `docs/03_EDGE_PROPOSALS.md` dengan format yang sama seperti E1–E5:

```
## E6 <Nama>
**Temuan:** angka + pembanding baseline (sumber: analysis/edge_<nama>_output.txt)
**So what:** keputusan stok apa yang berubah
**Fitur:** apa yang ditampilkan di app (tabel db / endpoint apa yang dibutuhkan)
**Kenapa tim lain tidak punya:** ...
**Momen demo:** 1 kalimat bahasa Inggris
**Biaya bangun:** S / M / L untuk Orang 1 & 2
```

**Jadwal:**
- **23.00**: kirim 1–2 kartu terbaik ke grup, tag Orang 1 dan 2. Mereka memutuskan masuk app atau tidak.
- **01.00**: cut-off app. Setelah ini, alihkan fokus ke:
  - **Bank Q&A juri** di `docs/04_QA_BANK.md`. Minimal 15 pertanyaan dengan jawaban 30 detik berbasis angka, per persona: praktisi Maintenance/Warehouse, Procurement, IT/Data, Manajemen. Wajib mencakup:
    - "Data kalian dummy, kenapa kami harus percaya?"
    - "Dari mana angka downtime cost?"
    - "Bagaimana integrasi ke SAP?"
    - "Kenapa tidak pakai LSTM/Prophet?"
  - **Red-team deck** jam 04.30: cek setiap angka di deck terhadap file output.

Commit dan push setiap kali satu kartu atau script selesai. Selalu `git pull --rebase` dulu sebelum push.
