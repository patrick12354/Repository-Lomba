# NOTE — slide 10 v2 (storyline vektor)

## Ide
Rekonsiliasi diceritakan sebagai kerja investigasi Berkas 734 di dunia yang sama dengan slide 1. Rumah kaca Pak Anton (kode vektornya disalin persis dari slide 1), lalu papan gabus: pin, benang, kaca pembesar, stempel, dan gulungan kertas grafik. Mekanismenya diperagakan dengan benda di papan, bukan ditulis sebagai caption. Penutupnya menyambung ke slide 1: celah "? ? ?" di catatan sensor terisi garis merah.

## Beat dan fungsinya
| Waktu | Beat | Fungsi |
|---|---|---|
| 0–2 | Sensor di rumah kaca mengirim data, Pak Anton menatapnya, whip pan | Penonton paham datanya berasal dari sensor yang sama seperti di slide 1 |
| 2–4,3 | Catatan sensor bercabang lewat benang ke dua kartu | Ada dua jalur prediksi dari satu sumber |
| 4,3–10 | Kartu Level digarisbawahi, benang membawa kamera ke timeline, 5 pin abu ditancapkan | Level = satu nilai per waktu |
| 10–18 | Kartu Increment, 4 benang 30 menit di atas, benang 2 jam menggantung di bawah | Increment = perubahan antartitik pada dua horizon |
| 18–29,4 | Kaca pembesar (tangan Pak Anton): selisih level ≠ prediksi perubahan, stempel BELUM KONSISTEN | Kedua sumber tidak cocok |
| 29,4–45 | Kartu TEMPORAL RECONCILIATION, lingkaran spidol mengelilingi semua titik, dua kriteria disorot | Satu optimasi untuk semua titik, dengan dua kriteria |
| 45,5–49,6 | Pin merah + benang merah bergerak serentak, tether ke posisi awal | Semua titik disesuaikan bersama, ada yang naik ada yang turun |
| 49,8–56 | Tether tebal (posisi), benang merah tebal (dinamika) | Level menjaga posisi, increment menjaga dinamika |
| 56–65 | Garis abu rata dicoret, kamera mundur, manik mengalir dari dua kartu, legend | Ini bukan smoothing, hasilnya gabungan dua sumber |
| 65–75 | Gulungan grafik dibuka: 734 titik prediksi asli → disambung jadi satu lintasan, celah di catatan terisi | 734 titik menjadi satu lintasan yang terhubung |

## Apa yang asli, apa yang ilustrasi
- Asli: 734 prediksi submission (`assets/pred.js`), tanggal awal dan akhir, teks VO.
- Ilustrasi: 5 nilai level dan increment (skematis). Posisi hasil dihitung benar dengan WLS (w_level=1, w_increment=2) lalu dibekukan; gerakannya cuma interpolasi visual. Label "Ilustrasi mekanisme" ada di kertas timeline dan terukir di bingkai kaca pembesar.
- Generated: SFX dari ElevenLabs (`tools/sfx.mjs`). Tekstur gabus, grain, dan kertas grafik dibuat prosedural (`shared/make_cork.py`). Tidak ada gambar AI.

## Gate (dari script, pada render final)
- look.py: G0 PASS (75,00 s, audio ada), G2 PASS (tidak ada lebih dari 3 frame datar berturut-turut), G3 PASS (end hold 1,20 s). Loudness −13,7 LUFS, true peak −1,2 dBFS. Gerak rata-rata 0,9/255, di bawah rentang film buatan manusia (median 6,8). Itu wajar untuk penjelasan ber-VO yang sengaja diam supaya bisa dibaca, tapi tetap saya catat di sini. Ada dropout senyap di antara kalimat VO (asalnya dari assemble-vo, bukan masalah baru).
- lint.mjs: G5 FAIL (C1, C6). Semua temuannya label sumbu/tick grafik (t, +30 mnt, Waktu, tanggal), sub-teks kartu, dan "Ilustrasi mekanisme" yang diwajibkan dokumen keputusan. Tidak ada HUD, counter, atau timecode. Tetap saya laporkan sebagai FAIL sesuai output script.
- G1/G4 dinilai mata di `look/sheet.jpg`: tiap frame punya satu fokus (kartu, pin, kaca pembesar, gulungan). Frame lebar di 61–75 s menampilkan papan penuh, dengan grafik 734 sebagai hero.

## Yang masih bisa diperbaiki
- Bentuk busur 30 menit tidak seragam (pin4→pin5 berbentuk tetesan tinggi).
- Antara 32 dan 47 s gambar cukup diam (hanya drift pelan dan sorotan kriteria).
- Teks kecil di kartu kiri pada frame lebar sekitar 19 px di layar.
