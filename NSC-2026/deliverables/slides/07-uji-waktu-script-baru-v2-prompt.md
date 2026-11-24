# Slide 7 — Model diuji pada waktu berikutnya, script baru, v2

Dibuat 13 Oktober 2026 menggunakan built-in ImageGen. Output `07-uji-waktu-script-baru-v2.png` berupa raster statis, bukan PPTX editable.

Dasar: script baru slide 7. Protokol rolling-origin, sembilan titik awal dan horizon 15 hari dicocokkan dengan laporan Bagian II-F serta `paper/figures/06-titik-asal-bergulir.png`. Tidak menjalankan ulang validasi.

QA visual: tepat sembilan baris Fold 1–9. Training memiliki awal yang sama dan meluas ke origin lebih akhir. Validation selalu setelah training masing-masing fold dan memiliki lebar kira-kira sama dalam skema generatif. Angka 15 hari dan 9 titik awal jelas. Rumus RMSE benar; arah semakin kecil semakin baik tercantum. OOF dihubungkan ke pembelajaran penggabungan. Caveat jendela tumpang tindih dan bukan sembilan eksperimen independen tampil jelas. Timeline berlabel ilustratif, tanpa tanggal atau skor buatan. Babak THE INVESTIGATION, sumber dan nomor 07 benar.

## Prompt final

Use case: productivity-visual / scientific-educational.
Create ONE finished scientific competition presentation slide 07, full 16:9 landscape, Indonesian. Continue established detective case-file aesthetic: charcoal-black subtly textured backdrop, torn warm ivory evidence sheet, beige tape, restrained dark-red stencil heading, readable ink typography and warm editorial tool illustrations. Rich purposeful visual cues, clear timeline, limited prose. This is a scientific presentation, no interactive dashboard.

Slide 7 current script: environmental time series are tested using Rolling-Origin Cross-Validation, NOT random row splitting. At each origin, training uses PAST data only, validation is the FOLLOWING 15 days. Repeat from NINE origins. OOF predictions support learning ensemble components. Nine validation windows overlap, so these are consistency checks, not nine independent experiments. RMSE = square root of mean squared error, smaller is better.

Top 14%:
Small taped tag exact "BERKAS 734".
Main headline exact "MODEL DIUJI PADA WAKTU BERIKUTNYA".
Top-right act exact "THE INVESTIGATION".

Central-left approx 68% of body:
One dominant clean ivory evidence page, title exact "Rolling-Origin Cross-Validation".
Draw EXACTLY NINE horizontal rows, clearly labelled "Fold 1" through "Fold 9" once each, in strict order.
Shared horizontal time direction from left to right. All dark training segments start at the SAME left boundary. Each successive row has a longer training segment: origins advance slightly from one row to next. At the end of EACH train block starts a RED validation block, adjacent with NO gap and NO overlap of train and validation within the same fold. All NINE red validation blocks have the SAME WIDTH because every validation horizon is 15 days. Shift each red block slightly to the right in successive rows, enough that most dates overlap among neighboring validation windows. Draw a fine dashed boundary marker at each training end if needed. No train segment after validation and no future training data within a row.
Above FIRST red validation block, a brace with large exact "15 hari". Above training section short exact "Masa lalu". Above validation side exact "Waktu berikutnya".
At bottom, clean horizontal arrow exact "Waktu". No dates, quantitative ticks, fake sensor data or invented scores. Caption exact "Skema sembilan jendela validasi".
A single small magnifying glass near first origin zooms the train-to-validation boundary but doesn't obscure any fold, interval, text or axis. A small unnumbered clock near forward time direction, useful physical cue, not huge decoration.
Legend beneath chart: dark swatch exact "Training"; red swatch exact "Validation". Dark text on cream background, red validation easily distinguishable.
At lower edge of chart a conspicuous short note exact "Jendela validasi tumpang tindih". A fine translucent bracket across a couple validation intervals may highlight temporal overlap; avoid connecting validation to future training wrongly.

Central-right approx 27%:
One continuous ivory notes sheet, not stacked UI cards. At top a calendar illustration with BIG exact "15" and exact "hari per jendela". Below separate BIG exact "9" with exact "titik awal pengujian".
Lower on this sheet large exact "RMSE". Display mathematically correct equation either as readable sqrt fraction or exact "RMSE = √mean((prediksi − aktual)²)". Do not lose square, parentheses or root. Formula can span two lines with root visibly covering the entire mean-squared error expression.
Below exact "Semakin kecil, semakin baik". Small ruler and two conceptual points showing a prediction-vs-reference gap, no numeric error values. Keep concept subordinate to formula.

Bottom content strip ~12%:
One paper ribbon with small labelled envelope / evidence packet exact "OOF", a clean arrow to a simple joining-strands illustration with exact "Mempelajari penggabungan". Add one prominent caveat exact "9 jendela bukan 9 eksperimen independen". Do not claim OOF alone removes all tuning bias or uses hidden actual test target. No in-sample training scores.
Footer exact "Heisenberg · NSC 2026" left, exact "07" right. Source exact "Sumber protokol: laporan Heisenberg, Bagian II-F dan Gambar 6." Small note if needed exact "Timeline ilustratif."
Constraints: EXACTLY NINE fold rows, equal red validation widths, train grows from common past start, all prediction testing happens strictly after train in each row. No random shuffled diagram dominating slide, no numerical scores, fabricated dates, plots of unknown test truth, model weights, actual test horizon labelled as a validation fold, ninth fold win claim, police tape, fingerprints, guns, institution logos, extra paragraphs or decorative crop borders. Legible on projector, clear strong hierarchy, preserved room around chart and mathematical notation. Full static finished slide.

