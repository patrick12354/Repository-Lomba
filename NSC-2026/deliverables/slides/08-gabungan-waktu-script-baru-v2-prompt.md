# Slide 8 — Waktu membantu penggabungan model, script baru, v2

Dibuat 13 Oktober 2026 menggunakan built-in ImageGen, diikuti satu koreksi wording dan proporsi batang kontrol. Output `08-gabungan-waktu-script-baru-v2.png` berupa raster statis, bukan PPTX editable.

Dasar: script baru slide 8. Tiga pita waktu-hari dan perubahan RMSE −0,080 untuk pembagian waktu versus −0,007 untuk kontrol acak dikonfirmasi pada ekstraksi laporan final, subbagian bobot per pita waktu-hari. Tidak menjalankan ulang audit validasi.

QA visual: lima sumber model dan tiga pita terlihat; tidak menambahkan batas jam atau bobot numerik. NNLS dengan bobot ≥ 0, shrinkage, dan kontrol kompleksitas setara tercantum. Grafik menyajikan MAGNITUDO penurunan RMSE positif 0,080 dan 0,007, bukan RMSE absolut, persentase atau skor publik. Batang acak diperpendek mendekati 8,75% batang waktu. Label audit validasi bersarang jelas. Diagram, kurva prediksi dan sky cues bersifat ilustratif; pita visual tidak menetapkan batas jam kuantil. Babak THE INVESTIGATION dan nomor 08 benar.

## Prompt generasi

Use case: productivity-visual / scientific-educational.
Create ONE finished scientific competition presentation slide 08, edge-to-edge 16:9 landscape, Indonesian. Continue established detective case-file deck: charcoal-black subtly textured background, torn warm ivory evidence sheets, beige tape, restrained deep-red stencil heading, clean large ink text, warm editorial visual cues. Visual explanation dominates, not a dashboard. No farmer scene.

Current NEW script slide 8: models differ in accuracy across parts of the day. Use Time-Banded Ensemble with Non-Negative Least Squares (NNLS); weights nonnegative. Learn weights per time band, apply shrinkage. Equal-Parameter Random Control tests whether improvement comes from temporal information rather than adding parameters. Nested-validation RMSE reduction: time-based grouping 0,080, random grouping 0,007. These are VALIDATION improvements, not public leaderboard scores or percentage changes.
The final report describes THREE time bands with hour-of-day quantile boundaries. Show exactly three abstract time bands labelled Pita 1, Pita 2, Pita 3 without inventing exact time intervals or measured weights.

Top 14%:
Small taped tag exact "BERKAS 734".
Headline exact "WAKTU MEMBANTU PENGGABUNGAN MODEL".
Top-right act exact "THE INVESTIGATION".

Left about 60% of content: ONE continuous warm ivory mechanism sheet, title exact "Time-Banded Ensemble".
At left edge a small stack of FIVE prediction strips, each with exact abbreviated name "LightGBM Huber", "CatBoost Huber", "ElasticNet", "Ridge-e", "LightGBM L2". Each strip contains a tiny conceptual ink trace, no axes, timestamps or values. Caption exact "Prediksi model".
All five strands feed a shared blending mechanism extending across THREE adjacent time-band sections. Each section has a clear exact short label "Pita 1", "Pita 2", "Pita 3". Above the sections small editorial sky/time cues: moon with morning light for first, sun for second, sunset/moon for third. These are conceptual parts of day, NOT fixed hour ranges. Do not print morning/evening labels implying exact quantile boundaries.
Within each time-band section draw a simple paper mixing knot / joining strands, same five inputs and a resulting single line. Put exact "NNLS" on mechanism and large exact "bobot ≥ 0" in clear spot just below. Different bands may use different abstract joining patterns, but DO NOT display numeric weight values, percentages, pie charts, bars of fictitious weight magnitude or a model contribution ranking.
The output is ONE continuous conceptual predicted line running through three time bands, with each band boundary visible. No fake humidity numeric data, no actual unknown test target. Caption exact "Skema mekanisme".
Below blending mechanism a meaningful analog cue of a small spring tether anchoring three weight notes toward a common reference, labelled exact "Shrinkage". Short exact caption "Menahan bobot terlalu mengikuti validasi". This is a conceptual regularization cue, not a decorative spring unrelated to the process or an interactive slider.
Small unnumbered clock and a magnifying glass focused on the changing time bands can be integrated without blocking names or connectors.

Right about 35%: ONE clean ivory EVIDENCE page, exact title "APA INFORMASI WAKTU MEMBANTU?".
A label exact "Kontrol dengan kompleksitas setara".
A simple TWO-BAR horizontal comparison chart with shared left zero and common scale. Heading exact "Penurunan RMSE".
First bar label exact "Berdasarkan waktu", numeric value BIG exact "0,080", deep red bar.
Second bar label exact "Pembagian acak", numeric value BIG exact "0,007", dark ink bar.
First bar long, second bar approximately 8.75% of first length. NO numeric axis ticks, NO percentages, NO absolute RMSE score, no minus signs because these figures are MAGNITUDE OF REDUCTION. Values large and separate from labels. Both bars aligned at same starting edge.
Below chart exact "Audit validasi bersarang".
Small evidence-control cue: a shuffled set of anonymous paper fragments beside the random-control row, no dice displaying fake numbers, and a clock/time cue by time-control row. Don't make these imply random train/test splitting; this is random grouping control of the ensemble structure.
A short takeaway exact "Informasi waktu memberi manfaat lebih besar".

Bottom strip: short method name exact "Non-Negative Least Squares" and exact "Equal-Parameter Random Control", separated with generous space, no explanatory paragraphs.
Footer exact "Heisenberg · NSC 2026" left, exact "08" right. Source exact "Sumber angka: laporan Heisenberg, bobot per pita waktu-hari." Small caveat exact "Diagram mekanisme ilustratif.".
Constraints: maintain three time bands, five model sources, nonnegative weight constraint and shrinkage. No fictitious weight numbers or score, false sum-to-one derived solely from NNLS, extra bins, exact hour values, leaderboard claims, experimental independence claim, temperature sensor readings, actual target data, model ranking, fingerprint, guns, police tape, institution logos, UI cards, verbose copy. Important numbers and caveat legible at presentation size. Full finished slide image.

## Prompt koreksi

Edit only TWO small details in this finished slide 08; preserve everything else, including all numbers, band diagram, method labels, layout and styling.
1. Right-side heading currently says "APA INFORMASI WAKTU MEMBANTU?". Change only its first word to exact "APAKAH", so full heading is "APAKAH INFORMASI WAKTU MEMBANTU?".
2. Correct the lower dark random-control bar length on the shared-zero chart. Its value is 0,007 while upper red bar is 0,080. Lower dark bar MUST be ONLY 8.75% of upper red bar length, approximately ONE ELEVENTH as long, not one fifth. The red bar is roughly 166 pixels long in this image, so dark bar should be roughly 15 pixels from same zero axis. Keep numeric labels 0,080 and 0,007 unchanged, clear and readable. If needed move 0,007 label to just right of shortened bar, keeping all label typography unchanged. Do not alter upper red bar, axes or add new values. Return full 16:9 slide.

