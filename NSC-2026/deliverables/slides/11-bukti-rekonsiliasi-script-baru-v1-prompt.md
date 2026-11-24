# Slide 11 — Rekonsiliasi memperbaiki hasil pengujian, script baru, v1

Dibuat 13 Oktober 2026 menggunakan built-in ImageGen. Output `11-bukti-rekonsiliasi-script-baru-v1.png` berupa raster statis, bukan PPTX editable.

Dasar: script baru slide 11. Angka RMSE perubahan OOF 30 menit 1,91 dan 1,81 dikonfirmasi pada laporan Bagian V-D. Skor publik 3,02586 dan 2,86595 serta delta −0,15991 dikonfirmasi pada Tabel A.IV; besaran penurunan dibulatkan ≈0,160. Konsistensi arah tiga blok audit maju dikonfirmasi pada caption hasil rekonsiliasi. Tidak menjalankan ulang audit atau memeriksa leaderboard langsung.

QA visual: Bukti 1 berlabel Validasi OOF, horizon 30 menit, dan RMSE perubahan. Bukti 2 berlabel RMSE PUBLIK. Angka cetak dan arah perbaikan benar; batang increment hampir sama panjang dengan selisih level, tanpa kontras berlebihan. Keduanya tidak memakai skala gabungan. Blok audit hanya memuat cue arah perbaikan, tanpa skor rekaan. Diagram delta merupakan cue konseptual. Tidak menampilkan kurva aktual test yang tidak tersedia atau skor akhir 2,82744. Babak THE BREAKTHROUGH, sumber dan nomor 11 benar.

## Prompt final

Use case: productivity-visual / scientific-educational.
Create ONE finished scientific competition presentation slide 11, full 16:9 landscape, Indonesian. Continue established detective case-file aesthetic: charcoal-black textured backdrop, torn warm ivory evidence sheets, beige masking tape, restrained deep-red stencil heading, readable ink typography, warm editorial magnifying glass / measurement-tool cues. Rich meaningful visuals but the measured RESULTS and their provenance dominate. No dashboard.

Current NEW script slide 11 "The Breakthrough Is Real": two tests support temporal reconciliation. First: 30-minute increment RMSE on OOF data is 1,91 if computed by differencing level predictions, versus 1,81 from the dedicated increment model. These are RMSE of CHANGES, not final level RMSE. Thirty-minute information receives greater relative weight than two-hour information. Second: PUBLIC leaderboard RMSE before temporal reconciliation 3,02586, after 2,86595, improvement approximately 0,160. Improvement direction consistent on three forward audit blocks. Do not include closing final score 2,82744 yet. The two evaluation domains MUST have separate labels and no common numerical axis.

Top 14%:
Small taped tag exact "BERKAS 734".
Main headline exact "REKONSILIASI MEMPERBAIKI HASIL PENGUJIAN".
Top-right act exact "THE BREAKTHROUGH".

Main LEFT ~39%:
One large ivory evidence sheet, small red stamp exact "BUKTI 1".
Heading exact "Akurasi perubahan".
Clear evaluation label exact "Validasi OOF · horizon 30 menit".
Two-row horizontal chart on common zero, SAME SCALE, with no numerical axis ticks; lengths nearly equal, NOT dramatic falsely truncated contrast:
Row 1 exact label "Selisih prediksi level", large exact "1,91", ink-dark bar.
Row 2 exact label "Model increment", large exact "1,81", deep-red bar. Lower bar length approximately 94.8% of upper bar, because 1.81/1.91. Do not exaggerate gap or draw a bar half as long.
Chart heading exact "RMSE perubahan".
Useful small conceptual cue: two time nodes with a Δ bracket and a magnifier comparing their change, no measured RH values. Any cue is clearly schematic and smaller than the chart.
Short bottom label exact "30 menit diberi bobot relatif lebih besar". No invented two-hour RMSE number, no weight ratio, no confidence interval or percentage.

Main RIGHT ~55%:
Larger ivory result exhibit, small red stamp exact "BUKTI 2".
Heading exact "Dampak pada hasil akhir".
Prominent evaluation label exact "RMSE PUBLIK".
Very large two values on separate clearly labelled score sheets / ledger marks, not UI cards:
Before exact "3,02586", label exact "Sebelum rekonsiliasi".
After exact "2,86595", label exact "Sesudah rekonsiliasi".
Arrange as a simple descending STEP from first value left/top to second right/lower, a thick restrained arrow links them downward/right. This is a score comparison illustration without numeric plot axes or fabricated prediction curves.
Below prominently exact "≈0,160" with clear exact "penurunan RMSE". The approx symbol must be visible.
Small editorial measuring caliper / ruler measures the score gap conceptually, no additional reading.
No final-score label, no crop result, no trajectory claimed as actual unknown test truth.

Bottom content ~15%:
One coherent audit evidence ribbon with exactly THREE labelled small signed sheets, exact "Blok 1", "Blok 2", "Blok 3". Each contains ONLY a downward comparison arrow or a simple checkmark, NOT a fake numerical RMSE or experimental waveform. Shared caption exact "Arah perbaikan konsisten pada tiga blok audit maju".
Small universal note exact "RMSE lebih kecil berarti lebih baik".
Footer exact "Heisenberg · NSC 2026" left, exact "11" right. Readable source exact "Sumber: laporan Heisenberg, rekonsiliasi dan Tabel A.IV." A tiny note if needed exact "Angka evaluasi, tanpa kurva prediksi rekaan."
Constraints: EXACT numeric spelling 1,91 / 1,81 / 3,02586 / 2,86595 / ≈0,160. Distinct OOF increment evaluation versus public target level evaluation. Do not invent 2-hour results, actual before/after prediction curves, hidden test target, scores for three audit blocks, final 2,82744, harvest benefit, percent gains, statistical significance or independence. Do not show model increment replacing level predictor entirely. Bars use common zero with near-equal lengths. No fingerprint, guns, police tape, farmer scene, institution logos, UI controls or verbose paragraphs. Full finished static scientific slide.

