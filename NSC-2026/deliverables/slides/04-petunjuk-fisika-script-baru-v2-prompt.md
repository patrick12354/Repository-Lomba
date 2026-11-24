# Slide 4 — Catatan harian menyimpan petunjuk, script baru, v2

Dibuat 13 Oktober 2026 dengan built-in ImageGen dan satu koreksi lokal label tab. Output `04-petunjuk-fisika-script-baru-v2.png` adalah raster statis, bukan PPTX editable.

Dasar: script baru slide 4. Dua persamaan dan SD selisih 0,047 °C dicocokkan dengan `docs/final/paper-submission-verified-extracted.md`, Bagian II-D, dan implementasi di `paper/script/make_figures.py`. Tujuh label tab dicocokkan dengan header `Dataset/train.csv`: gdd, standard_day_degree, daily_mean_temperature, daily_max_above_Tbase, daily_max, daily_max_reduction, ontario_units. Tidak menjalankan ulang eksperimen.

QA visual: tujuh tab memakai alias indeks dataset, tanpa Radiasi/Presipitasi/Durasi penyinaran rekaan. Kedua jalur persamaan, 0,047 °C, label SD selisih dua rekonstruksi, proksi titik embun dan formula RH benar. Kurva dua jalur secara eksplisit ilustratif, bukan plot eksperimen asli. Tidak menyatakan 0,047 sebagai galat terhadap titik embun. Sumber, babak THE CLUES dan nomor 04 terbaca. Ymax pada persamaan adalah komponen maksimum CHU, bukan indeks tersendiri.

## Prompt generasi

Use case: productivity-visual / scientific-educational.
Create ONE finished scientific competition slide 04, edge-to-edge 16:9 landscape, Indonesian. Continue the detective presentation: charcoal-black subtly textured background, torn warm ivory evidence papers, beige tape, restrained deep-red distressed stencil heading, ink typography and warm editorial cartoon illustrations. Visual cues dominate over prose, readable scientific equations and key numeric fact. No UI dashboard styling.

Current script slide 4, The Hidden Clue: SEVEN daily agronomic indices contain information allowing two algebraic inverse reconstructions of daily minimum temperature. First identity: Tmin = 2 × Tmean − Tmax. Second route from Ontario Crop Heat Units: Tmin = (2 × CHU − Ymax) / 1,8 + 4,4. The STANDARD DEVIATION OF THE DIFFERENCE BETWEEN THE TWO RECONSTRUCTIONS is 0,047 °C. This does NOT measure error against ground truth dew point. Minimum temperature is used as a PROXY for dew point, NOT the same thing as a verified dew point measurement. Relative humidity is 100 times actual vapor pressure divided by saturation vapor pressure at current temperature.

Top about 14%:
Small taped tag exact "BERKAS 734".
Main headline exact "CATATAN HARIAN MENYIMPAN PETUNJUK".
Small top-right act label exact "THE CLUES".

Main upper-middle about 54% is ONE coherent evidence investigation flow on a large continuous ivory sheet:
LEFT ~20%: open daily agronomy notebook, pencil, little plant and thermometer cues. Exactly SEVEN short paper index tabs visible at edge of notebook, no invented index values, dates or sensor readings. Large exact "7" and exact "indeks agronomi harian". A magnifier over a formula scribble on notebook signals hidden information, avoid illegible pseudo-body paragraphs. Two thin ink connector branches lead to center formula routes.
CENTER ~43%: two formula routes stacked vertically, visually separate but not UI cards. Route 1 label exact "JALUR 1" and short exact "Rerata dan maksimum", formula printed large and mathematically correct "Tmin = 2 × Tmean − Tmax". Route 2 label exact "JALUR 2" and exact "Ontario Crop Heat Unit", formula printed large "Tmin = (2 × CHU − Ymax) / 1,8 + 4,4". Ensure parentheses are around ENTIRE numerator and division applies to whole numerator. The second formula can wrap gently onto two lines only if correct. Both paths converge toward one thermometer / minimum-temperature symbol with exact short label "Suhu minimum". No numeric thermometer display.
RIGHT ~32%: big exact "0,047 °C", clear exact two-line label "SD selisih" / "dua rekonstruksi". Small underneath exact "Hampir identik". A small simple conceptual graph beneath it shows TWO gently varying, nearly overlapping lines, one ink-dark continuous, one red dashed. Label legend exact "Jalur 1" and "Jalur 2". Horizontal axis exact "Hari", vertical axis exact "Tmin". NO numeric axis ticks, timestamps, fake measured values. Caption exact "Ilustrasi kesesuaian dua jalur". Graph is explicitly illustrative; 0,047 fact comes from the report, not inferred from the drawn curve. Do not draw two totally identical flat straight lines.

Lower middle about 21%: one clean physics explanation strip on cream paper, useful visual illustration of thermometer, dew droplets on leaf, and vapor/air symbols, logically linked left to right, NOT implying an observed crop outcome.
Short label at left exact "Tmin sebagai proksi titik embun".
Then exact "Tekanan uap".
At right main equation clear "RH = 100 × e / es(T)" where es(T) means saturation vapor pressure at temperature T. Under it concise symbol legend exact "e: aktual" and "es(T): jenuh". Optional light air vapor particles near equation but not obscuring it. Don't equate Tmin and dew point with a mathematical equality. No numeric humidity or pressure values. Strong visual cue that physical relation yields engineered information, not magic model.

Small method ribbon below or footer-adjacent exact "Algebraic Inverse Reconstruction · Dew Point Proxy · Vapor Pressure".
Footer exact "Heisenberg · NSC 2026" left, exact "04" right. Readable source exact "Sumber angka: laporan Heisenberg, Bagian II-D." A small caveat near graph exact "Kurva ilustratif; angka dari laporan." only if necessary, avoid duplicating existing caption.
Constraints: maintain generous safe margins, large numbers and formula text, all labels unambiguous. No invented reconstruction error, correlation, score, dates, index values, temperature readings or model names. No harvest benefit, diagnosis, real farm claim, police tape, guns, fingerprint, Pak Anton portrait, extra panels, tiny explanatory paragraphs. The key message is TWO routes recover hidden physical information, with agreement 0,047 °C, then minimum temperature serves as a proxy in humidity physics. Finished polished slide image.

## Prompt koreksi

Edit this finished slide 04 with ONLY one localized scientific correction. Preserve all other content, equations, numeric fact 0,047 °C, illustrative graph, style, layout, caveats and footer exactly.
The notebook at the left has exactly SEVEN tabs, but some current labels are invented variables. Replace the SEVEN notebook tab texts, top to bottom, with these exact short labels:
1 "GDD"
2 "SDD"
3 "Tmean"
4 "Tmax − Tbase"
5 "Tmax"
6 "Reduksi Tmax"
7 "CHU"
These correspond respectively to the dataset fields gdd, standard_day_degree, daily_mean_temperature, daily_max_above_Tbase, daily_max, daily_max_reduction, ontario_units. Print ONLY the short quoted labels on tabs, not the long field names or numbering. Allow two lines in the fourth and sixth tabs if necessary. No tab named Radiasi, Presipitasi, Durasi penyinaran, or Ymax. Keep Ymax in the SECOND ROUTE EQUATION untouched, where it is mathematically correct. Keep large numeral 7 and all other notebook artwork unchanged. Return the complete 16:9 slide, not a crop.

