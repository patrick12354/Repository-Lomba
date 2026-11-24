# PlantPulse — Technical Brief

Terakhir diupdate: 3 Okt 2026 · Tim Heisenberg · CALIBER 2026 Case 2 (Intelligence Manufacturing)
Live: <https://caliber-2026-heisenberg.vercel.app/> · Referensi: [rancangan_solusi_plantpulse.md](rancangan_solusi_plantpulse.md) · [RUNBOOK.md](RUNBOOK.md) · [../prototype/README.md](../prototype/README.md) · [../evaluation/results.md](../evaluation/results.md)

## 1. Ringkasan

PlantPulse adalah workspace keputusan dan follow-up reliability berbasis bukti. Setiap masalah equipment ditautkan ke sumber datanya, ketidakpastian, owner, dan kriteria penyelesaian. AI membantu membaca dan menyusun bukti lintas sumber; manusia yang memutuskan dan menutup action.

Batas sistem: **PlantPulse tidak pernah menulis ke DCS, SAP, atau sistem kontrol apa pun.** Sistem membaca snapshot yang di-govern dan menghasilkan keputusan, log, dan file export untuk manusia.

## 2. Masalah teknis yang diselesaikan

| Masalah di data | Konsekuensi desain |
|---|---|
| 380 `Serial No` unik, tapi hanya 153 AR berbeda; 226 baris AR `n/a` | AR bukan primary key; identitas baris sumber dipertahankan |
| KO-3201 weekly vibration dalam micron, hourly dalam MM/S | Tidak pernah di-overlay atau dikonversi diam-diam (conflict CF-06) |
| Threshold KO-3201 berubah 60 → 45 micron tanpa effective date | Threshold punya sumber/versi; konflik ditampilkan |
| Repair Closed, tapi sensor install, retube, roll-out masih terbuka | Repaired ≠ recovered ≠ prevention done ≠ verified effective |
| 85 baris `RUN_STATUS=OFF` masih punya arus bukan nol | Nilai asli dipertahankan, diberi flag kualitas |
| HE-3301 (heat exchanger) punya tag `MOTOR AMPERE` | Dikeluarkan dari demo energi motor |

## 3. Arsitektur

```text
File lomba (xlsx, pptx)            Upload data owner (Ingest page)
        │                                   │
        ▼                                   ▼
pipeline/extract_case2.py          server/ingest/{xlsx,pptx}.ts   ← parity 16/16 file identik
pipeline/validate_case2.py         server/ingest/validate.ts      ← quality gates sebelum publish
        │                                   │
        └──────────────► Supabase Postgres (snapshot terpublikasi, RLS read-only)
                                    │
     analytics/ (Python, GitHub Actions mingguan) ── patterns, anomaly, condition_forecast
                                    │
             Vercel Functions (prototype/api/router.ts → server/routes/*)
                 │            │                │
            OpenAI API   Supabase Storage   Resend (email due-date)
                                    │
                    React SPA (Vite) — 4 layar workflow + platform pages
```

### Stack

| Lapisan | Teknologi |
|---|---|
| Frontend | React 18, TypeScript, Vite 5, Tailwind 4, Radix, Recharts, React Three Fiber (ilustrasi mesin), dnd-kit |
| Backend | Vercel Functions (TypeScript), zod untuk validasi schema I/O |
| Data | Supabase: Postgres + RLS, Auth (email & anonymous), Storage (evidence, file sumber) |
| AI | OpenAI Responses API dengan structured output: `gpt-6.1-sol` (reasoning), `gpt-6-luna` (teks pendek); override via `OPENAI_MODEL`, `OPENAI_MODEL_LIGHT` |
| Analytics | Python 3.12: numpy, pandas, scikit-learn; Chronos-2 untuk forecast kondisi |
| Pipeline offline | openpyxl, python-pptx |
| CI/CD | GitHub Actions: `ci.yml` (vitest, build, pytest, extract + validate), `analytics.yml` (Senin 05:00 WIB) |
| Testing | Vitest (unit, parity), Playwright (`e2e/judge-path.spec.ts`), eval scripts terhadap model asli |

### Mode operasi

| | Offline demo | Live open (trial) | Live sign-in |
|---|---|---|---|
| Trigger | `VITE_SUPABASE_URL` kosong / `?offline=1` | `AUTH_MODE=open` | `AUTH_MODE=required` |
| Data | `src/data/case2.json` (bundled) | Snapshot Supabase | Snapshot Supabase |
| Action | Simulasi di `localStorage` | Server guard + hash-chained log | Sama, dengan role |
| AI | Off (brief terekam) | On | On |

## 4. Model data

21 tabel di `prototype/supabase/migrations/0001`–`0005`:

- **Snapshot & sumber:** `snapshots`, `sources`, `incidents`, `equipment`, `hourly_series`, `rca_documents`
- **Bukti & konflik:** `evidence`, `conflicts`
- **Action & audit:** `actions`, `action_evidence`, `review_events` (append-only, hash-chained; `verify_review_chain()` mendeteksi entri rusak)
- **AI:** `ai_runs` (biaya, latensi, model per run), `rca_audits`, `rca_drafts`, `copilot_threads`, `copilot_messages`
- **Analytics:** `failure_patterns`, `anomaly_events`, `business_scenarios`
- **Lainnya:** `profiles` (role: viewer, engineer, reviewer, manager, data_owner), `notifications`

Prinsip: setiap fakta membawa sumber, waktu, unit, dan status kualitas. Snapshot lama diarsipkan, tidak dihapus.

## 5. Komponen fungsional

### Workflow (4 layar)
1. **Executive Overview** — KPI ledger (actual vs potential loss terpisah), filter plant mengubah numerator dan denominator, cakupan dan kualitas sumber.
2. **Problem Tank** — 220 record open-status, lima dengan bukti lengkap; prioritas, chart kondisi, conflict registry, evidence drawer.
3. **Root Cause Investigation** — fakta vs hipotesis AI vs pembanding historis, differential diagnosis, forecast window, kontradiksi, pemeriksaan yang masih dibutuhkan.
4. **Actions & Verification** — owner, due date, progres; transisi status dijaga aturan bukti (`src/domain/actionTransitions.ts`), reviewer wajib, export CSV SAP PM untuk import manual.

### Fitur AI
| Fitur | Cara kerja | Guardrail |
|---|---|---|
| RCA auditor | Model mengekstrak klaim yang bisa dicek beserta kutipan verbatim; kode mencocokkan ke condition record | Filter kutipan verbatim; kontradiksi masuk conflict registry; tahan prompt injection |
| Ask PlantPulse (copilot) | Tool read-only atas snapshot (termasuk `get_hourly`) | **Evidence Guard**: ref harus dari tool di run itu, angka/tanggal harus ada di excerpt, judge call menilai dukungan |
| Closure evidence reader | Upload PDF/foto pada action, model mengklasifikasi terhadap aturan action | Hanya advisory; tidak bisa menutup action |
| RCA backlog | Starter RCA (4P, 4M+1E) untuk 183 record lewat RCA due date | Setiap baris "Not assessed" sampai manusia mengisi |
| Failure patterns | Clustering 380 record jadi 16 family; model memberi nama | Diberi label hipotesis |
| Anomaly windows | Detektor MAD di data PI per jam + penjelasan AI per window | MAD tetap primer; Chronos band sekunder |
| Masked investigator | Diagnosis tanpa melihat RCA, gold pre-registered | Allowlist input (`input_manifest.json`), cek leakage |

### Analytics deterministik (tanpa LLM)
`analytics/patterns.py`, `anomaly.py`, `condition_forecast.py` (Chronos-2 vs linear), `fleet_predictability.py`. Energi = **proxy berbasis arus motor**, bukan kWh.

## 6. Keamanan dan governance

- **Read-only ke plant:** tidak ada writeback ke DCS/SAP; SAP PM berupa CSV.
- **Secret:** `SUPABASE_SERVICE_ROLE_KEY` dan `OPENAI_API_KEY` hanya di server; tidak pernah ber-prefix `VITE_`.
- **RLS:** browser hanya read; upload lewat signed URL.
- **Audit:** `review_events` menolak UPDATE/DELETE; rantai hash bisa diverifikasi.
- **Budget AI:** cap rolling 24 jam (`AI_DAILY_BUDGET_USD`, default 20); estimasi biaya direservasi sebelum model dipanggil; cap per jam 30 member / 10 guest / 60 akun open; guest maks 25% budget.
- **Role-based access:** publish snapshot hanya `data_owner`; penutupan action butuh `reviewer`.
- **Produksi (usulan):** model via private endpoint di tenant perusahaan, SSO, audit log terpusat; jalur OT read-only sesuai NIST SP 800-82 Rev. 3. Ini keputusan arsitektur, bukan sertifikasi.

## 7. Evaluasi (internal, 2–3 Okt 2026)

Semua hasil adalah pemeriksaan internal tim; belum ada reviewer independen, user study, atau pilot.

| Area | Hasil |
|---|---|
| Data invariants | 23/23 check reproduksi lulus |
| Reference tasks G01–G10 | 10/10 pass (G08 terkontaminasi, tidak dihitung sebagai blind test) |
| Ingestion TS vs Python | 16/16 file identik |
| Anomaly detection | 4/5 series ter-flag sebelum shutdown (KO-3201 46 jam; PM-4405B miss) |
| RCA auditor | 3/5 konflik KO-3201 ditemukan; prompt injection lulus; US$0.25 untuk 5 deck |
| Copilot + Evidence Guard | 6/6 setelah perbaikan tool (run pertama 5/6), 0 kalimat tak didukung |
| Evidence reader | 3/4 fixture sintetis |
| Masked investigator | Top-1 7/9, top-3 9/9, 0 leakage |
| Forecast kondisi | Chronos P50 MAE 1.38 minggu vs linear 1.55; headline tetap estimasi linear |
| Energy proxy (WAPE 168 jam) | Lebih baik dari naive di 3/4 aset; KO-3201 setara |

## 8. Menjalankan

```bash
cd prototype && npm install && npm run dev      # offline demo, tanpa .env
npm test && npm run build                        # unit/parity test + type-check
npm run check:ai && npm run check:db && npm run check:live
npm run eval:rca && npm run eval:copilot && npm run eval:evidence   # ±US$0.60
```

Setup penuh (migrasi, seed, analytics): [RUNBOOK.md](RUNBOOK.md).

## 9. Keterbatasan yang diketahui

- Hanya lima kasus dengan bukti lengkap; semua TRIP di minggu 21 — tidak cukup untuk klaim generalisasi prediksi.
- Flag tren linear tidak lebih awal dari label ALARM pada kelima seri.
- Snapshot tidak memuat histori transisi action; waktu ack/verifikasi butuh event log saat pilot.
- Energi absolut dan emisi butuh meter kW/kWh dan emission factor yang disetujui.
- Belum ada pengukuran waktu kerja, downtime, atau savings.

## 10. Roadmap teknis

| Tahap | Output teknis | Syarat lanjut |
|---|---|---|
| Discovery | Mapping data/role, review stack existing (mis. SAP APM), daftar akses | Sponsor dan data owner sepakat |
| Shadow mode | Connector read-only, paket rekomendasi tanpa writeback | Quality gate berjalan, reviewer bisa mengoreksi |
| Assisted execution | Action yang disetujui dikirim ke system of record | Authority, audit, rollback teruji |
| Perluasan | Aset/unit tambahan | Manfaat proses terukur |
