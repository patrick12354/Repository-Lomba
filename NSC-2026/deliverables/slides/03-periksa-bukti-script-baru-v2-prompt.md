# Slide 3 — Sebagian bukti perlu diperiksa, script baru, v2

Dibuat 13 Oktober 2026 menggunakan built-in ImageGen. Output `03-periksa-bukti-script-baru-v2.png` berupa raster statis, bukan PPTX editable.

Dasar: slide 3 pada script baru di root workspace. Rasio 5,75 untuk suhu, 6,86 untuk tekanan, dan 1,20 untuk kelembapan dicocokkan dengan `paper/figures/02-residu-loo.png` dan bagian uji residu pada `docs/final/paper-submission-verified-extracted.md`. Tidak menjalankan ulang perhitungan.

QA visual: empat titik tetangga terlihat, dua sebelum dan dua sesudah titik pusat. Nilai asli dan perkiraan mempunyai posisi waktu sama. Residual ditandai sebagai selisih vertikal. Kurva kuadratik dan contoh penanganan Hampel berlabel ilustrasi, bukan pengukuran. Rasio dan kategori benar; batang merupakan representasi grafis generatif, sehingga angka cetak tetap acuan presisi. Nama metode, babak THE CLUES, sumber, dan nomor 03 terbaca. Tidak ada pembacaan sensor rekaan atau skor model.

## Prompt final

Use case: productivity-visual / scientific-educational.
Create ONE finished scientific competition presentation slide 03, edge-to-edge 16:9 landscape, Indonesian. Match the current detective deck: charcoal-black subtly textured background, torn warm ivory evidence paper, beige tape, restrained dark-red distressed stencil heading, clean ink typography, warm editorial illustrations. Meaningful visual cues, minimum prose, strong hierarchy. Not a dashboard or a web interface.

Slide 3 story from the current script: unexpected sensor spikes require investigation. Leave-One-Out Quadratic Interpolation hides one point and fits a quadratic using FOUR nearby points, two before and two after. The difference between the real hidden point and estimated value is a residual. The residual standard deviation compared with a robust scale based on MAD is 5,75 for temperature, 6,86 for pressure, and 1,20 for target humidity. Selective Hampel filter treats sensor spikes, not flattening all data.

Top 15%: compact taped case tag exact "BERKAS 734", main headline exact "SEBAGIAN BUKTI PERLU DIPERIKSA", small top-right act label exact "THE CLUES". Generous margins.
Left approximately 64% of body: ONE dominant clean ivory sheet with a large explanatory graph. Heading exact "Periksa satu titik".
Graph is an EXPLICIT SCHEMATIC of temperature spike checking, NOT a real dataset plot. No numerical y-axis measurements or timestamps. Horizontal axis exact "Waktu", vertical axis exact "Suhu".
Draw exactly FOUR dark filled neighbor points forming a gently curved near-baseline pattern, TWO to left and TWO to right of a central target time. A thin ink line can show local pattern.
At the central target time, one RED filled point is well above local pattern, representing the suspicious observed spike. Circle this red spike with one handwritten red evidence circle. Short exact label near it "Nilai asli".
At the SAME central time and SAME x-position directly below the spike, one HOLLOW circle sits on the quadratic estimate. Label exact "Perkiraan". Add a thin smooth dashed QUADRATIC curve through vicinity of FOUR neighbors and hollow central estimate. The red spike must NOT be part of this fitted curve.
Vertical dashed gap or bracket between hollow estimate and red spike, label exact "Residual". Make the gap obvious and labels nonoverlapping. Under four neighbor points, a small brace and exact text "4 titik tetangga". No extra filled points that confuse this count.
Small readable subtitle below graph exact "Ilustrasi pemeriksaan, bukan deret pengukuran".
Near this exhibit a small meaningful magnifying glass enlarges just the central hollow point and red spike relationship WITHOUT duplicating extra points. A small sensor device illustration in a corner has no numeric display. Keep illustration smaller than chart and clear of graph axes.

Right approximately 31% of body: one continuous ivory results sheet, heading exact "RASIO RESIDUAL". Small definition exact "SD residual / skala robust MAD". Three clearly spaced horizontal entries each with a simple accurate bar starting at shared zero, a label, and BIG numeric value:
"Suhu" with "5,75" in deep red,
"Tekanan" with "6,86" in deep red,
"Kelembapan" with "1,20" in ink dark.
Bars lengths proportional to 5.75, 6.86, 1.20, aligned common starts and identical scale. No fake extra numbers or axis ticks. Pressure bar longest; temperature about 84% of pressure; humidity about 17.5% of pressure. The numbers represent dimensionless residual ratios, never temperature readings or percentages. Clear large label below exact "Lonjakan lebih dominan pada sensor masukan".

Lower strip 12%: concise process on one paper ribbon, exact text "Leave-One-Out Quadratic Interpolation", then "MAD", then "Hampel Filter", spaced with small connector arrows. Add short bold note exact "Tangani lonjakan secara selektif". One small before/after conceptual cue: a small jagged segment with ONE anomalous red peak, alongside the same segment with that peak replaced while other bends remain. Label this mini cue exact "Ilustrasi penanganan". Do not imply sensor curves all become flat or show real experimental cleaning result. Do not crowd ribbon with more explanations.

Footer exact "Heisenberg · NSC 2026" left, exact "03" right. Readable source exact "Sumber rasio: laporan Heisenberg, Gambar 2 dan Tabel I." Keep footer apart from plot illustration caveat.
Constraints: exact comma decimal spelling 5,75; 6,86; 1,20. No RMSE, no classifier models, no target values, no invented thresholds, fake measurements, fake disease claim, fake timestamps, police tape, fingerprints, guns, portraits, crops filling margins, extra paragraphs or UI cards. Text and scientific diagram must remain legible on projector, no overlapping labels. The visual must communicate checking a point from four neighbors before selective filtering. Full finished slide image.

