# Slide 5 — Kondisi pada periode uji berubah, script baru, v2

Dibuat 13 Oktober 2026 menggunakan built-in ImageGen, dengan koreksi lokal grafik rerata. Output `05-kondisi-berubah-script-baru-v2.png` berupa raster statis, bukan PPTX editable.

Dasar: script baru slide 5; suhu rerata 27,51 °C dan 24,64 °C serta konstan pada water_volume_* dicocokkan dengan ekstraksi laporan final Bagian II-E. Exhibit audit dukungan pada `paper/figures/05-audit-dukungan.png` diperiksa sebagai konteks keputusan fitur. Tidak menjalankan ulang eksperimen.

QA visual: angka dan kategori train/test benar; skema memperlihatkan test lebih dingin. Kurva irigasi bervariasi pada train dan konstan pada test, eksplisit berlabel skema. Fitur tanah dan irigasi dicoret dari konfigurasi akhir. Diagram rerata final tanpa tick kuantitatif karena posisi generatif tidak presisi; angka cetak menjadi acuan. Tidak mengarang histogram distribusi atau nilai volume irigasi. Ilustrasi kebun hangat/dingin merupakan konteks visual, bukan dokumentasi lokasi sebenarnya. Babak THE CLUES, sumber dan nomor 05 terbaca.

## Prompt generasi

Use case: productivity-visual / scientific-educational.
Create ONE finished scientific competition slide 05, edge-to-edge 16:9 landscape, Indonesian. Continue same detective case-file deck: subtly textured charcoal-black background, warm torn ivory evidence paper, beige masking tape, restrained deep-red distressed stencil headings, clean ink serif/sans typography, meaningful warm editorial sensor illustrations. Plenty of visual cues, large critical figures, no paragraphs or UI dashboard.

Current NEW script slide 5: conditions differ between train and test. Mean temperature train 27,51°C, test 24,64°C. Irrigation records vary in train but become constant during test. Distribution shift motivated Feature Distribution Analysis and removal of soil and irrigation feature groups from final configuration. No claim that irrigation measurements prove actual irrigation equipment physically stopped.

Top 14%:
Small case tag exact "BERKAS 734".
Main headline exact "KONDISI PADA PERIODE UJI BERUBAH".
Small top-right act label exact "THE CLUES".

Main top-middle ~46%:
ONE wide clean ivory comparison page. Heading exact "Suhu rata-rata". Two aligned sections left TRAIN, right TEST.
Left large exact "27,51 °C", right large exact "24,64 °C". Small exact "TRAIN" above left and "TEST" above right.
Meaningful nonnumeric illustrated thermometer beside each mean; warmer left thermometer, lower right thermometer, same scale and size. No extra display numbers.
Below both means ONE common horizontal temperature axis with exact ticks "20", "25", "30", axis label exact "Suhu rata-rata (°C)". This is a MEAN COMPARISON plot, not an invented histogram. Place dark TRAIN dot at 27.51 between 25 and 30, red TEST dot at 24.64 just below 25. Both dots sit on same clean axis and are directly labelled "Train" / "Test". A thin red LEFT-POINTING arrow from train dot toward test dot visualizes lower temperature in test; dots clearly positioned accurately. No decorative density curves, distributions, synthetic scatter clouds or fake uncertainty.
Small magnifying glass emphasizes TEST dot without blocking values. Short exact annotation "Rerata lebih rendah pada test".
Connect this temperature comparison with a short torn label exact "Distribution Shift".

Main lower-middle ~25%:
ONE horizontal irrigation comparison strip on cream paper aligned beneath the two period sections. Left header exact "Irigasi: bervariasi", right header exact "Irigasi: konstan".
Two simple schematic time traces on the SAME vertical scale and width: left black irregular record line, right red perfectly horizontal record line. Both small axes with no numeric ticks, no units or dates. A dashed vertical boundary at middle, or clear separation between TRAIN and TEST. Small caption exact "Skema perubahan catatan irigasi". NOT experimental measurement curves. Illustrate a small irrigation pipe or valve at right and soil sensor probe left, unnumbered. Do not show an irrigation pipe spraying water in one period versus broken in the other, since these are only recorded values.

Bottom ~12%:
A single feature-selection evidence note, exact heading "KONFIGURASI AKHIR". Two clear paper tags exact "Fitur tanah" and "Fitur irigasi", each marked with restrained red strike/cross. One short caption exact "Dikeluarkan setelah analisis distribusi fitur". Small exact method label "Feature Distribution Analysis".
These exclusions must be shown as model input choices, not sensors removed from farm or discarded all weather features. No extra retained-feature list, algorithm, score or numerical benefit.

Footer exact "Heisenberg · NSC 2026" left, exact "05" right. Source exact "Sumber angka: laporan Heisenberg, Bagian II-E." Keep source readable. A small footer note only if space exact "Kurva irigasi ilustratif."
Constraints: key figures 27,51 °C and 24,64 °C exact with comma decimal. Mean positions consistent with axis. Irrigation schematic clearly labelled and flat during TEST. Preserve balance and generous whitespace. No generated distributions claiming to be actual dataset, fake standard deviations, RH values, time labels, numeric sensor readings, crop health outcomes, causation or accuracy promises. No Pak Anton, fingerprints, guns, police tape, institution logos, extra paragraphs or UI cards. Full finished static slide image, scientific meaning precise.

## Koreksi posisi (percobaan)

Edit this full slide 05 with ONLY a precise correction to the two dots on the temperature axis. All other content, illustrations, text, numbers, layout, labels, curves and footer must remain unchanged.
The horizontal axis below the large means has equally spaced ticks 20, 25, 30. Use that exact axis scale:
- TRAIN dot must be at 27.51: 75.1% of the distance from tick 20 to tick 30 (approximately x=1037 in this 1672-wide image).
- TEST red dot must be at 24.64: 46.4% of the distance from tick 20 to tick 30 (approximately x=810), ONLY SLIGHTLY to the left of tick 25, not close to 24.
Maintain both dots at the same vertical height. Move the magnifying glass to center on the corrected TEST red dot. Reposition the nearby Test and Train labels accordingly, and resize the left-pointing arrow between them so its direction remains TRAIN toward TEST. Avoid hiding tick 25. Keep numbers 27,51 °C and 24,64 °C unchanged. Return full 16:9 slide.

## Koreksi final: diagram skematis

Edit ONLY the small horizontal mean comparison graphic below the two large temperature numbers on this full slide 05. Preserve every other element exactly.
Make this graphic an explicitly SCHEMATIC comparison so the generated dot placement is not a claimed numerical axis: remove ONLY the three numeric axis tick labels 20, 25, 30 and their three vertical tick marks. Keep the horizontal baseline, two dots, Test/Train labels, magnifier and left-pointing comparison arrow. Replace the axis caption "Suhu rata-rata (°C)" with exact "Skema perbandingan rerata". The large correct mean labels 27,51 °C and 24,64 °C above remain unchanged and authoritative. No new figures or text. Return entire slide 16:9.

