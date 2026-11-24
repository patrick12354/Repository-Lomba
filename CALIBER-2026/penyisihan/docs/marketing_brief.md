# PlantPulse — Marketing Brief

Terakhir diupdate: 3 Okt 2026 · Tim Heisenberg · CALIBER 2026 Case 2 (Intelligence Manufacturing)
Referensi klaim: [rancangan_solusi_plantpulse.md §2.3 dan §16](rancangan_solusi_plantpulse.md) · Brief video: [../videos/plantpulse-demo/BRIEF.md](../videos/plantpulse-demo/BRIEF.md) · Teknis: [technical_brief.md](technical_brief.md)

> Semua copy untuk juri ditulis dalam **bahasa Inggris**. Angka hanya boleh dari §2.3; kalimat klaim mengikuti tabel §16.

## 1. Inti pesan

**One-liner (EN):**
> PlantPulse brings equipment evidence, AI-assisted investigation, and accountable follow-up into one workspace, helping engineers make traceable decisions and verify that corrective and preventive actions are actually completed.

**Tagline (EN):**
> A repair is not a fix until the evidence says so.

**Pesan dalam satu napas:** mesin yang sudah jalan lagi belum tentu masalahnya selesai. PlantPulse memisahkan *repaired*, *recovered*, *prevention done*, dan *verified effective* — dan hanya mengizinkan status naik kalau buktinya ada.

## 2. Audiens

| Audiens | Yang mereka pedulikan | Yang harus mereka lihat |
|---|---|---|
| **Juri CALIBER** (Chandra Asri: operations, IT, OT engineer) | Pemahaman masalah, prototype yang terbukti, feasibility, relevansi industri kimia | Satu incident (KO-3201) dari KPI → root cause → action terverifikasi, dengan sumber di setiap angka |
| **Reliability engineer** (user utama) | Waktu menyusun paket keputusan, angka yang konsisten, follow-up yang jelas | Bukti lintas sumber dalam satu layar, konflik ditampilkan, AI yang menunjukkan batas buktinya |
| Maintenance planner / discipline owner | Owner, due date, bukti penyelesaian | Action dengan aturan bukti, reminder, export SAP PM |
| Plant manager | Status sebenarnya, bukan status "Closed" | Overview yang memisahkan actual vs potential loss dan status action |
| Data owner / IT-OT security | Governance, keamanan, tidak mengganggu plant | Read-only ke plant, RLS, audit log hash-chained, budget AI |

## 3. Masalah (cerita)

Di pabrik petrokimia, informasi kondisi, temuan RCA, dampak produksi, owner, dan status tindakan tersebar di sumber yang berbeda — dan sering tidak sepakat. Contoh nyata dari data lomba, **KO-3201 cracked gas compressor**:

- Repair tercatat **Closed**.
- Pemasangan sensor masih **In Progress**, lewat tanggal rencana.
- Retube dan roll-out ke aset serupa masih **Open**.
- Vibration mingguan dalam micron, per jam dalam MM/S; threshold berubah 60 → 45 tanpa tanggal berlaku.

Mesinnya pulih. Pencegahannya belum. Dashboard biasa akan menampilkan hijau.

**Konteks skala (kalimat yang diizinkan):**
- "The supplied incident dataset records US$61.89M actual and US$5.31M potential loss across 380 incidents in 12 plants."
- "Open-status records contain US$39.03M actual and US$5.31M potential loss."
- "183 open-status records have an RCA due date before the selected review date; action status requires separate review."
- "Five reference cases record US$2.58M estimated loss; avoided loss has not been measured."

## 4. Positioning

**Bukan** "alert → recommendation → action" — itu sudah dilakukan platform seperti SAP APM, dan kami tidak mengklaim lebih unggul.

**Fokus yang bisa dipertahankan:**
1. **Evidence reconciliation before decisions** — loss, unit, versi threshold, dan identitas incident tidak pernah digabung diam-diam.
2. **AI that shows the limits of its evidence** — observasi, temuan terdokumentasi, hipotesis, dan simulasi dipisahkan; setiap kalimat AI dicek Evidence Guard.
3. **Completion gated by evidence** — repaired ≠ recovered ≠ prevention done ≠ verified effective; closure butuh bukti dan reviewer, bukan tombol.
4. **Open evaluation against simple baselines** — hasil dilaporkan apa adanya, termasuk yang gagal.

**Sikap terhadap stack existing:** PlantPulse menawarkan workflow dan evidence model. Kalau bisa dikonfigurasi di sistem yang sudah dilisensi, itu yang dipilih — tidak mensyaratkan ganti platform.

## 5. Proof points (semua internal, sebut "internal")

| Klaim | Bukti |
|---|---|
| Data direkonsiliasi, bukan ditebak | 23/23 check reproduksi data lulus; 10/10 reference task |
| AI menolak mengarang | Copilot 6/6 pertanyaan referensi, 0 kalimat tak didukung (internal) |
| AI bisa diagnosis tanpa melihat jawaban | Masked investigator: top-3 9/9, top-1 7/9, 0 leakage (internal blind test) |
| AI mengaudit RCA | RCA auditor menemukan 3 dari 5 konflik yang ditemukan manual di KO-3201; tahan prompt injection |
| Murah dijalankan | Audit lima deck RCA ±US$0.25; tiga eval ±US$0.60 |
| Aman untuk OT | Read-only ke plant; audit log tidak bisa diubah |

Selalu sertakan kegagalan yang relevan (mis. PM-4405B tidak ter-flag anomaly detector; 2 dari 5 konflik RCA terlewat). Kejujuran ini adalah bagian dari positioning poin 4.

## 6. Klaim: boleh vs dilarang

| Jangan | Pakai |
|---|---|
| "AI predicts failures" / "detects earlier than DCS" | "Historical condition signals are presented with source-linked investigation and follow-up." |
| "Saves US$2.58M" | "Five reference cases record US$2.58M estimated loss; avoided loss has not been measured." |
| "US$44.3M future risk" | "Open-status records contain US$39.03M actual and US$5.31M potential loss." |
| "183 CAPA overdue" | "183 open-status records have an RCA due date before the review date." |
| "Zero hallucination" | "Evidence checks, bounded outputs, and human review; residual errors are measured and reported." |
| "Real-time plant energy" | "Current-based proxy forecast on a supplied equipment series." |
| "Better than SAP" | "A focused implementation for the CALIBER workflow, evaluated against explicit baselines." |
| Persentase hemat waktu / downtime | Tidak ada — belum diukur. Tawarkan formula business case + input pilot. |

## 7. Business value (tanpa angka karangan)

Tiga kategori yang selalu dipisah:
1. **Historical context** — recorded loss/downtime dari dataset.
2. **Measured process benefit** — setelah task study (waktu menyusun paket keputusan, kelengkapan action).
3. **Projected operational benefit** — skenario dengan input perusahaan, bukan realised savings.

Halaman **Business case** di app hanya menghitung dari input perusahaan. Narasi: *"We show you the formula and the inputs we need from the pilot, not a fake ROI."*

KPI pilot yang diusulkan: waktu menyiapkan paket keputusan lengkap; % action dengan owner, due date, dan bukti; % keputusan dengan angka/sumber yang konsisten; jumlah action ditutup tanpa bukti (target: nol).

## 8. Tone dan gaya

- **Tenang, presisi, jujur.** Seperti engineer senior yang menunjukkan bukti, bukan sales yang menjanjikan.
- Kalimat pendek, istilah plant yang benar (trip, alarm, RCA, CAPA, 4M+1E), tanpa hype AI.
- Setiap angka di layar membawa sumbernya.
- Bahasa Inggris untuk semua materi juri.

## 9. Identitas visual

Detail: [../prototype/DESIGN.md](../prototype/DESIGN.md).

- **Light "Pipo" (default):** kertas `#FAF9EF`, mesh apricot `#E6B093` + sky `#A3CEFF`, panel frosted putih, ink navy, accent biru `#2f62e0`.
- **Dark "Prado mesh":** hitam murni, kartu graphite, shader Mesh drift hijau (`#0E7C5A`, `#7CE577`).
- **Warna status konsisten:** merah = trip/overdue/conflict, amber = alarm, accent = interaktif.
- **Brand object:** equipment tag — nomor tag mono di plat dengan lubang dan status band menyala.
- **Maskot:** Pipo.
- Tipografi: Google Sans Flex dan Google Sans Code.

## 10. Kanal dan deliverable

| Deliverable | Batas | Pesan utama |
|---|---|---|
| Deck PDF | Maks 7 slide + appendix; total materi ≤10 MB | Cover → Problem → Solution → Business Impact → Feasibility & Roadmap → Conclusion → Team |
| Video demo | ≤180 detik, YouTube, 1920×1080 | Ikuti KO-3201 end to end; jawab KQ1–KQ3 di layar; VO bahasa Inggris |
| Prototype live | <https://caliber-2026-heisenberg.vercel.app/> | Juri bisa menjelajah sendiri (mode open, tanpa login) |
| Landing page | Bagian dari app | Hook masalah → screenshot workflow → masuk workspace |

**Deadline submission:** 4 Okt 2026, 23.59 WIB. Hanya submission pertama yang dinilai.

## 11. Call to action

Untuk juri: *"Open the live workspace and follow KO-3201 yourself."*
Untuk Chandra Asri (pasca-lomba): *"Start with a discovery pilot: we map your data and roles, measure today's baseline, then run PlantPulse in shadow mode — no writeback, no plant risk."*
