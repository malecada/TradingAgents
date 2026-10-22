# Branch B7 state

2026-10-22 — Registered (charter, config, pre-declared plan). No B7 table built yet.

2026-10-22 — Code complete (plan tasks 1–6; 17 B7 tests, suite B–B7: 271 passed, 1 warning). Plan
rulings before execution: track B option-market columns read from B6's `features_B.parquet`
(same computation); set X1a (B4 transforms of all 15 series) and the comparison Y1 vs X1a
added to the pre-declared list; `__ex1` clipped to ±10 like every other engineered
feature. Fresh whole-branch review requested before any table is read.

B7-CP1 (2026-10-22 09:40) — tables built once (`cli features`, 15 s, peak 2.1 GB): 85,704 hours ×
379 columns (324 new-engineering, 32 B4 transforms, 13 market, 2 range, 2 event-time, 3
interactions, 3 option-market); targets V6 79,932, V24 79,428, J6 79,531 (base rate 1.9 %),
J24 79,507 (1.9 %), M6 68,005, M24 67,757 non-missing hours. Complete feature rows: track A′
47,119 of 50,448 window hours, track B 47,456 of 48,480 (most gaps from 168-hour price
windows after Binance outages, as in B4–B6). No forecast run yet.
