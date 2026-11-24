# Failure-pattern clustering — internal run

Date: 2026-10-02 · Job: `analytics/patterns.py` (TF-IDF over type/component/mechanism/title, KMeans with k chosen by silhouette in 6–20, seed 42). Input: 380 register records.

16 families. Labels are generated later by `scripts/label-patterns.ts` (Claude) and must be reviewed by a human; coherence per human review: _not yet reviewed_.

| Key | Records | Plants | Recorded actual loss (US$) | Open | Top terms |
|---|---|---|---|---|---|
| FP-01 | 50 | 12 | 7,523,790 | 28 | comp_bearing, bearing, vibration, out, overheat, mech_overheat |
| FP-02 | 36 | 11 | 5,472,060 | 22 | comp_coupling, coupling, out, mech_loose, loose, mech_worn |
| FP-03 | 39 | 11 | 4,841,200 | 19 | comp_valve, control, valve, stuck, mech_stuck, leakage |
| FP-04 | 20 | 10 | 3,419,330 | 10 | comp_transmitter, mech_error, error, transmitter, type_rx, type_co |
| FP-05 | 22 | 10 | 2,727,300 | 9 | comp_motor, performance, mech_low, low, motor, type_pz |
| FP-06 | 24 | 9 | 4,147,800 | 19 | comp_seal, seal, leakage, mech_leakage, type_em, type_pz |
| FP-07 | 21 | 9 | 3,767,080 | 11 | comp_tube_bundle, fouling, mech_fouling, exchanger, type_pu, type_bl |
| FP-08 | 15 | 9 | 3,094,860 | 6 | comp_gearbox, vibration, gearbox, mech_high, high, type_bl |
| FP-09 | 15 | 9 | 2,313,040 | 6 | comp_blade, mech_breakage, breakage, blade, type_cd, type_bl |
| FP-10 | 20 | 8 | 6,302,380 | 13 | comp_shaft, crack, mech_crack, shaft, type_rx, type_tx |
| FP-11 | 21 | 8 | 3,816,610 | 14 | comp_rotor, vibration, rotor, high, mech_high, type_tx |
| FP-12 | 18 | 8 | 3,024,680 | 14 | comp_impeller, out, impeller, mech_worn, worn, type_em |
| FP-13 | 16 | 8 | 2,808,390 | 14 | comp_gasket, gasket, leakage, mech_leakage, type_tx, type_hb |
| FP-14 | 25 | 8 | 2,492,540 | 15 | comp_solenoid, solenoid, malfunction, mech_malfunction, type_va, cv |
| FP-15 | 15 | 8 | 2,227,950 | 8 | comp_mechanical_seal, mechanical, leak, seal, mech_leakage, type_em |
| FP-16 | 23 | 7 | 3,907,450 | 12 | comp_oil_seal, oil, seal, leakage, mech_leakage, type_sx |
