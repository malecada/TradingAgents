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

2026-10-22 10:05 — Fresh whole-branch review (fable): causality, alignment, row-set fairness,
criteria, bootstrap, serialization and resume verified on the real tables; one Critical
(positive-free validation tail → 600 iterations on first-fold J targets) fixed with a test and
recorded as PLAN.md amendment 1 before any forecast run; per-year support added to the
tables. Minors deferred (ledger). Forecast unit launched after the fix.

B7-CP2 (2026-10-22 10:52) — forecast unit `onchain-b7-forecast` complete in 16 minutes (12 units,
56–134 s each, peak 1.5 GB): 198 comparison rows in `TABLES.md` with per-year support and
per-fold alphas, iteration counts and tail support.

B7-CP3 (2026-10-22) — `RESULTS.md`: new engineering (Y1) null or worse against B4's columns;
B6 series (Y2) worse; early-stopped larger trees worse than B4's fixed trees for V and M
targets; tail targets null; the flow block (X1 vs X0) passes for V6 and M6 in track B in both
families (1.4–3.3 % of squared error) and nothing in track A′ once range features are in the
baseline. B7 closed.
