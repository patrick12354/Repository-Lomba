# Caliber Final

> Babak final Chandra Asri Innovation and Business Strategy Challenge (CALIBER) 2026 — 🥇 **Juara 1 dari 120 tim**. Repo asli: [raphaeladikara/caliber-final](https://github.com/raphaeladikara/caliber-final)

CALIBER 2026 Final — Case 3: Spare Part Intelligence & Inventory Optimization.

## Struktur

- `docs/`
  - `CALIBER 2026 - Final Case Brief.pdf` — brief resmi case
  - `Data Context & Relationship Diagram.pdf` — relasi & join key antar dataset
  - `01_EDA_FINDINGS.md` — temuan EDA (F1–F11) dipetakan ke Key Questions
- `data/` — dataset mentah (Excel, dummy):
  - `BoM.xlsx` — Bill of Materials + posisi stok
  - `FuncLoc list.xlsx` — daftar Functional Location + criticality
  - `Mitem & Mplan.xlsx` — Maintenance Item & Maintenance Plan
  - `Movement Material.xlsx` — pengeluaran (issue) material
  - `Notif History.xlsx` — riwayat notifikasi maintenance
  - `PR PO.xlsx` — Purchase Requisition & Purchase Order
- `analysis/` — script EDA (`py analysis/eda.py` dari root) dan `eda_output.txt`

## Pembagian tugas tim

Mulai dari [docs/tasks/00_TEAM_PLAN.md](docs/tasks/00_TEAM_PLAN.md), lalu buka brief masing-masing:
- Orang 1, Engine Data: [docs/tasks/ORANG_1_ENGINE.md](docs/tasks/ORANG_1_ENGINE.md)
- Orang 2, App + Deploy + Deck: [docs/tasks/ORANG_2_APP_DECK.md](docs/tasks/ORANG_2_APP_DECK.md)
- Orang 3, Edge Hunter: [docs/tasks/ORANG_3_EDGE_HUNTER.md](docs/tasks/ORANG_3_EDGE_HUNTER.md)
- Note Orang 3 untuk tim (stress test E1–E4, perbaikan engine): [docs/tasks/ORANG_3_NOTE_TO_TEAM.md](docs/tasks/ORANG_3_NOTE_TO_TEAM.md)
