# Slide 8 — Gabungan yang benar-benar membantu

Dibuat 12 Oktober 2026 dengan built-in ImageGen. Output `08-gabungan-kontrol-waktu-v1.png`; preview PNG statis, bukan PPTX editable.

QA: ΔRMSE −0,080 vs −0,007, validasi bersarang dengan kontrol jumlah parameter sama, sesuai laporan §V-B PDF p.5. Semua anggota tetap ada pada tiap pita waktu; yang dipelajari adalah bobot, bukan memilih satu model per jam. Kontrol acak mengelompokkan baris OOF untuk pembobotan, bukan mengacak split train/test atau urutan anggota. Cue jam dan kelompok observasi ilustratif; tidak ada angka bobot atau panjang bar kontribusi buatan. Nama model dan tanda negatif diperiksa visual. Tidak disebut sebagai skor publik.

## Prompt utama

Generate ONE finished scientific presentation slide 08 in Indonesian, 16:9 flat slide canvas. Use supplied slides as style references: dark charcoal grunge detective scrapbook, taped torn ivory papers, warm expressive editorial cartoon visual cues, dark red stencil heading, clean large sans-serif numerical evidence, small tomato-greenhouse motifs only at corners. Stage changes to BUKTI.
Upper-left taped "BERKAS 734"; upper-right "BUKTI"; lower-right "08". Modestly sized exact headline over cream paper "GABUNGAN YANG BENAR-BENAR MEMBANTU".
Main composition: two parallel evidence routes on a large cream investigation sheet; two clean big measured-result numbers, sparse labels and rich illustrations, no numeric bar chart.
UPPER route labeled "Bobot menurut waktu": illustrated clock face WITHOUT numeral hours, sun/moon/sunset motif, five tiny model dossier papers as in prior lineup. Grouping by time is indicated by arranging identical model sheets near small time-of-day motifs; do not show fabricated numeric weights or manual tuning. A thin red arrow leads to one large evidence note with small label "ΔRMSE" and exact VERY LARGE black value "−0,080". Use a true minus sign U+2212, decimal comma, THREE decimals. Small label beneath the number "Validasi bersarang".
LOWER route labeled "Kelompok bobot acak": same five model dossier papers, now shuffled into abstract groups using a shuffle-arrow icon and a small dice motif with no visible numbered face. It represents random group assignment for WEIGHT FITTING, NOT random train/test folds. A thin muted-gray arrow leads to a second equally sized note with small "ΔRMSE" and exact VERY LARGE dark gray value "−0,007". Same minus sign and three decimals. Beneath "Validasi bersarang".
Both result notes same size and typography: number magnitude is presented textually, not invented bar lengths. No performance bar chart, no fake axis or curves, no quantitative mark heights. The magnitude comes from exact text. Do not write percentages or make results positive.
Between these two routes, prominent investigator fairness cue: clean illustration of a balanced scale with identical bundles of configuration gears / model parameter sheets on both pans. Short label exact "Jumlah parameter sama". This visually establishes controlled capacity; not weighting accuracy manually. Keep it separate from result values.
Small annotated logbook icon at left-bottom exact label "Bobot dipelajari dari OOF". Logbook has abstract dots only and no numerical data. A magnifying glass near the time-group route highlights time as the extra information, without distorting or covering measured numbers.
Bottom one flat torn-paper insight "Waktu memberi informasi pada gabungan." Nearby a small downward arrow icon and text "ΔRMSE negatif = membaik". No universal guarantee claims. Do NOT imply models manually adjusted to get lower score.
Readable source footer exact "Sumber: laporan Heisenberg, §V-B, hlm. 5."
Second footer exact "Kontrol pada setup yang dilaporkan; bukan skor publik."
Tiny final footer "Ilustrasi kelompok bobot; angka sesuai laporan."
No paragraphs, bullets, hyperparameters, model percentages, model importance claims, absolute RMSE values, public leaderboard scores, dates, sensor readings, fake curves, red police tape or crime faces. Do not copy numbers from references. Keep major imagery expressive and clear, labels very readable, no confusion between RANDOM WEIGHT GROUPS and time-based evaluation folds. Empirical figures must be exactly −0,080 and −0,007 from same reported nested-validation context. This slide compares learned time-grouped ensemble weights against an equal-parameter random grouping control.

## Perbaikan cue kelompok

Precisely correct group semantics in this existing slide; preserve headline, theme, measured values −0,080 and −0,007, equal-parameter scale illustration, footers, note about negative ΔRMSE and all other layout.
1. REMOVE the five separate day/night sky rectangles above the five model cards in TOP route. They incorrectly suggest each model exclusively belongs to a different time. Replace that entire area with plain cream paper and ONE shared thin label above ALL five cards: "Semua anggota di tiap pita waktu". Keep left magnifying glass showing time-of-day divisions as grouping cue. All five model cards remain.
2. In BOTTOM route, retain the cards but arrange their order to match the top exactly: LightGBM Huber, CatBoost Huber, ElasticNet, Ridge-e, LightGBM L2. Random grouping applies to OOF observations, not shuffling models.
3. Replace dice icon below "Kelompok bobot acak" with a small abstract notebook/dot-group icon: same gray and colored observation dots redistributed into small groups, no numerical values or graph axes. Keep shuffle arrows around this dot-group icon, not around model order.
4. Add a very small readable label above the bottom five model cards: "Baris OOF dikelompokkan acak". No new long text.
Avoid any implication of random train/test validation split, model selection by time, exclusive per-model time assignment or manually chosen weights. Keep exact empirical figures, numerical typography and context "Validasi bersarang" unchanged. Same 16:9 slide.

