# Slide 9 — Kesalahan masih memiliki pola waktu, script baru, v2

Dibuat 13 Oktober 2026 menggunakan built-in ImageGen. Output `09-pola-residual-script-baru-v2.png` berupa raster statis, bukan PPTX editable.

Dasar: script baru slide 9. Autokorelasi residual lag-1 sekitar 0,93 dikonfirmasi pada ekstraksi laporan final, bagian model level dan rekonsiliasi. `paper/figures/09-anatomi-galat.png` diperiksa sebagai konteks, bukan digunakan sebagai kurva residual ini. Tidak menjalankan ulang penghitungan autokorelasi.

QA visual: empat residual negatif bertetangga disorot di bawah garis nol, konsisten dengan residual = prediksi − aktual dan prediksi terlalu rendah. Grafik berlabel ilustrasi pola, bukan deret pengukuran. ≈0,93 dilabeli autokorelasi residual model level, tidak tertukar dengan autokorelasi target 0,979. Diagram increment mempunyai lima titik dan empat interval; 30 menit menghubungkan dua titik pertama, 2 jam menghubungkan titik pertama sampai kelima. Tidak memuat nilai RH atau target test rekaan. Catatan dua prediksi belum tentu cocok menjadi transisi menuju slide rekonsiliasi. Babak THE BREAKTHROUGH dan nomor 09 benar.

## Prompt final

Use case: productivity-visual / scientific-educational.
Create ONE finished scientific competition presentation slide 09, edge-to-edge 16:9 landscape, Indonesian. Continue current detective case-file aesthetic: charcoal-black subtly textured background, torn warm ivory evidence sheets, beige tape, restrained dark-red distressed stencil heading, clear ink typography, warm editorial magnifier and notebook cues. Purposeful visuals and large key number, no dashboard.

Current script slide 9 "The Pattern Nobody Noticed": residuals of the level ensemble remain strongly temporally structured. If a point is predicted too low, its neighbors often are too low too. Residual lag-1 autocorrelation is approximately 0,93. This motivates modeling changes (increments) over 30 minutes and two hours, alongside the level prediction. Level and increment predictions need not agree; reconciliation comes on the NEXT slide, not here.

Top 14%:
Small taped tag exact "BERKAS 734".
Main headline exact "KESALAHAN MASIH MEMILIKI POLA WAKTU".
Top-right act exact "THE BREAKTHROUGH".

Main left about 64% of body:
ONE dominant clean ivory sheet, heading exact "Residual bertetangga cenderung searah".
A LARGE simple time-series RESIDUAL graph, with horizontal axis exact "Waktu", vertical axis exact "Residual". A crisp horizontal dashed ZERO line with ONLY tick label exact "0". Do not show other numeric ticks, dates, humidity values or fake data.
Draw one smooth ink residual trace with around 10–12 conceptual markers: begins above zero, crosses into a longer negative run, then rises smoothly to above zero. Highlight FOUR successive neighbor points BELOW zero in deep red, emphasizing a negative residual run. All red highlighted points must remain below the zero reference. A red hand-drawn bracket spans those four points. Short label exact "Meleset terlalu rendah". Small formula at graph top exact "Residual = prediksi − aktual".
Place a magnifying glass centered on two or three of the highlighted negative neighbor points, but keep zero line and main axes visible. Magnifier makes temporal pattern clearer, not extra actual data.
Below graph readable caption exact "Ilustrasi pola residual, bukan deret pengukuran". This is a conceptual pattern graph, NOT a plot of actual experimental residuals, and must never imply missing test target values are known.
No invented RMSE, histogram or actual validation dates.

Main right about 31%:
ONE ivory evidence notebook page. Small heading exact "Autokorelasi residual".
Huge dominant number exact "≈0,93" in dark red, circled once with red ink.
Below clear exact "lag-1" and exact "Galat model level".
A tiny useful conceptual cue of two adjacent negative residual bars / same-direction arrows links lag-1 to neighboring error directions, no numeric values. Short takeaway exact "Kesalahan masih menyimpan struktur waktu".
Do not confuse this with 0,979 autocorrelation of the raw humidity target. This number is residual autocorrelation only.

Bottom content ~24%:
One clear ivory transition strip, heading exact "DARI NILAI KE PERUBAHAN".
Left small diagram: ONE humidity level point with short exact label "Level" and exact "Nilai pada satu waktu". A single droplet or simple pin is a conceptual humidity cue, no reading.
Right larger diagram: exactly FIVE time-ordered points on a horizontal conceptual timeline, representing equally spaced 30-minute intervals. No numeric humidity measurements, y-axis or actual waveform. A short red arrow between FIRST and SECOND point labelled exact "30 menit". A longer red bracket/arrow spanning FIRST to FIFTH point labelled exact "2 jam". Because there are FOUR 30-minute intervals across five points, the two-hour horizon must span all five, not only two neighbors. The two horizon connectors sit at different vertical heights to avoid overlap. One short exact "ΔRH" near each connector if readable.
Title on this diagram exact "Increment" and short exact "Perubahan antartitik". Small label exact "Skema horizon".
A restrained red question mark between conceptual level and increment cues, not a solved/checkmark reconciled output. One short note exact "Dua prediksi belum tentu cocok".
No formula for reconciliation, WLS, final reconstructed path or performance numbers on this slide.

Footer exact "Heisenberg · NSC 2026" left, exact "09" right. Source exact "Sumber angka: laporan Heisenberg, analisis galat model level." Small method label exact "Residual Autocorrelation Analysis" if space permits without competing with main content.
Constraints: printed figures only ≈0,93, 0 reference, lag-1, 30 menit, 2 jam, number09; no invented readings or score. Correct residual sign: too-low predictions yield negative residual. Correct two-hour connector spanning FOUR half-hour intervals. Label conceptual graphs explicitly. Meaningful detective cues, scientific content readable, no Pak Anton farm scene, guns, police tape, fingerprints, institution logos, excessive decorations, UI cards or paragraph copy. Return full polished slide image.

