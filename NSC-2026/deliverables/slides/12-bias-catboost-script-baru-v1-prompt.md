# Slide 12 — Bias muncul pada audit maju, script baru, v1

Dibuat 13 Oktober 2026 menggunakan built-in ImageGen. Output `12-bias-catboost-script-baru-v1.png` berupa raster statis, bukan PPTX editable.

Dasar: script baru slide 12. Bias CatBoost −0,006 %RH in-sample dan −2,89 %RH pada audit maju dicocokkan dengan laporan Bagian V-C dan `paper/figures/08-bias-anggota.png`. Koreksi parsial 50% dari estimasi OOF dan dua negative control mengikuti script. Tidak menjalankan ulang audit atau menghitung offset.

QA visual: tanda negatif, nilai bias, kategori dan satuan benar. Marker in-sample hampir nol dibanding batang audit negatif. Arah bias prediksi rendah diperlihatkan lewat cue berlabel ilustrasi. Alur koreksi dimulai dari envelope OOF, lalu 50% estimasi koreksi, lalu CatBoost; tidak ada pengambilan langsung angka −2,89 untuk offset. Kalimat angka audit bukan besar koreksi tampil jelas. Dua kontrol bertanda tidak membaik, tanpa skor atau corrected bias rekaan. Babak THE BREAKTHROUGH, sumber dan nomor 12 benar.

## Prompt final

Use case: productivity-visual / scientific-educational.
Create ONE finished scientific competition presentation slide 12, edge-to-edge 16:9 landscape, Indonesian. Continue established detective case-file style: charcoal-black textured backdrop, torn warm ivory evidence paper, beige tape, restrained deep-red stencil headline, clear ink typography, purposeful editorial magnifier, envelope and measuring-tool cues. Scientific content and key figures dominate, not an app dashboard.

Current NEW script slide 12: CatBoost member has in-sample mean residual bias −0,006 %RH, but forward audit bias −2,89 %RH. Residual = prediction minus actual, so negative bias means predictions too low. Partial Bias Correction uses an estimate from OUT-OF-FOLD predictions, applying HALF (50%) of that estimate to reduce overcorrection risk. The −2,89 forward audit figure is NOT the offset used for correction, and the correction must NOT be depicted as half of −2,89. Negative controls correcting in the wrong direction and correcting a nearly unbiased model did not improve results. No score or exact corrected bias claimed.

Top 14%:
Small taped tag exact "BERKAS 734".
Main headline exact "BIAS MUNCUL PADA AUDIT MAJU".
Top-right act exact "THE BREAKTHROUGH".

Left ~53% of body:
ONE large clean ivory diagnostic evidence sheet. Heading exact "CatBoost: bias residual".
Small definition exact "Residual = prediksi − aktual".
A clear comparison exhibit using two categories, same vertical signed scale: first "In-sample", second "Audit maju". Horizontal ZERO baseline across both categories with exact tick label "0". Y-axis label exact "Bias (%RH)", no invented intermediate tick numbers.
First category: tiny dark hollow diamond very close to zero and slightly below, with short leader to large exact annotation "−0,006 %RH". Do not make in-sample appear same size as forward bias.
Second category: one strong deep-red bar extends DOWN below zero, labelled at its lower end BIG exact "−2,89 %RH". Height should visually dominate first category. Both marks referenced to same zero. This chart depicts mean bias, NOT actual time-series residual measurements.
A small magnifier reveals near-zero first diamond but does not change its true plotted location or imply the marker is exactly zero. No exaggerated in-sample bar.
Bottom takeaway exact "Bias negatif: prediksi cenderung rendah". One small two-point concept cue shows reference point above predicted point, with labels exact "Aktual" and "Prediksi". Caption exact "Ilustrasi arah bias". These are conceptual points, NOT unknown test truth or a measured crop humidity value.

Right ~41%:
ONE coherent ivory correction process sheet, heading exact "Partial Bias Correction".
Start at TOP with an editorial sealed evidence envelope exact "OOF" and short exact "Estimasi dari prediksi OOF".
A downward arrow from THIS envelope to a large torn note exact "50%" and exact "estimasi koreksi". A half-filled analogue measuring spoon / restrained ruler cue may symbolize partial magnitude, WITHOUT numeric offset reading or full correction slider.
Another arrow to an illustrated CatBoost prediction paper / branching-model sketch, label exact "Koreksi parsial CatBoost".
Clear short purpose exact "Mengurangi risiko overcorrection".
Critical readable note on this sheet exact "Angka audit bukan besar koreksi." This must be visible, not tiny footer. No connector from left audit value −2,89 directly into 50% or the correction step. No formula −2,89 × 50%, no invented corrected bias, no exact zero after correction.
Small method label exact "Residual Bias Analysis" can appear at lower edge.

Bottom ribbon ~17%:
Heading exact "NEGATIVE CONTROL".
Two short experimental control notes side by side:
exact "Koreksi arah salah" with a red incorrect-direction arrow,
exact "Model hampir tidak bias" with small near-zero cue.
Shared red stamp exact "TIDAK MEMBAIK", or each note gets exact "Tidak membaik".
These are checks on controls, not a rejection of the main model or a score chart. No numerical outcomes.

Footer exact "Heisenberg · NSC 2026" left, exact "12" right. Readable source exact "Sumber: laporan Heisenberg, Bagian V-C." Small concept caveat exact "Cue arah bias ilustratif.".
Constraints: EXACT negative signs and comma decimal values −0,006 %RH and −2,89 %RH. 50% refers to the OOF-estimated correction only. In-sample and forward audit distinct. Don't turn %RH into relative percentage reduction. No RMSE, score, ranking, raw humidity value, target test data, invented correction offset, corrected residual result, all-five-model audit plot, harvest outcome, police tape, fingerprints, guns, institution logos, UI controls or paragraphs. Generous whitespace, large typography, scientific meaning precise. Return full finished slide image.

