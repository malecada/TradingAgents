# Branch B6 state

2026-10-19 — Registered (charter, config, pre-declared plan). No B6 pass output read yet.

2026-10-19 — Code complete (plan tasks 1–9; 29 B6 tests, 245 with B–B5). Labels frozen
(`research_artifacts/onchain-b6/labels/labels6.json`): exchange 35,297 addresses
(B2 4,961 ∪ eth-labels), DEX 353, bridge 332, MEV 3,749, funds 81; Tron exchange
addresses 149. Heavy-day probe (2025-06-02, fresh state): read 39 s, hourly rows 5.5 s,
peak 1.9 GB; 1,682 large transfers (841 deposits); mean per hour 33.7k active addresses,
2-core 21 %, giant component 77 %, 10.1k exchange counterparties.

Pre-pass review (fresh reviewer): 2 Critical + 5 Important, all fixed with tests
(`b6d2f0b1a` before the pass: canonical exchange entities, issuer out of flows, atomic
state bundle; `4723adba8` after launch: Tron block isolated on its own sub-sample,
placebo gap over all events and linear-time placebo, pre-event windows ending before the
block minute, Tron back-off and bundle). Labels re-frozen before the pass: 35,296
exchange addresses in 324 canonical entities.

B6-CP1 (2026-10-20) — labels frozen, `PLAN.md` committed, Binance 1-minute closes stored
for ETH and BTC: 4,088,369 minutes each, 2019-01-01 → 2026-10-12 23:59, 4,111 missing
minutes (exchange outages). Pass running (`onchain-b6-pass`, resumable; interrupted by
two reboots and resumed from snapshots); Tron stream running but portal-throttled
(≈ 25 days of blocks per hour), expected not to finish before the forecast stage.

B6-CP2 (2026-10-21 03:40) — pass complete: 3,570 days built, 1 unavailable (2020-11-01,
no token_transfers partition); 23.6 s per day on average, peak 6.2 GB; three watchdog
restarts and two reboot resumes, all from snapshots. Large transfers (≥ $1M stablecoin
or ≥ 500 ETH to or from an exchange): 2.65M records (2021 341k … 2025 574k). Feature
tables: 85,704 hours, 39 raw series → 78 B6 columns + 22 B4 flow columns (track A) + 3
option-market columns (track B). Tron block not run (stream at ≈ 2021 after
portal throttling; reported as not run per spec §7).

B6-CP3 (2026-10-21) — forecast comparisons run once (`TABLES.md`): 48 rows (track A
16, track B 32 over two groups). Pre-declared criteria met only by the flows block
against the option-market baseline for next-6-hour volatility (track B, X1 vs X0, both
families); structure (X2) and entity detail (X3, X4) pass nowhere; linear models with the
entity block are far worse in track A. Event study run once: 100,078 events. Tron stream
stopped at ≈ 2021 (portal throttled); block reported as not run.

B6-CP4 (2026-10-21) — `RESULTS.md`: structure (X2) and entity detail (X3, X4) pass no
criterion in either track; the flow block passes against the option-market baseline for
next-6-hour volatility (2–4 % of error, both families, both periods); the linear entity
rows in track A are a first-fold extrapolation artefact (diagnostics.txt); 100,078
minute-level events show no return, no anticipation and no volatility reaction beyond
coinciding with active periods; Tron not run.

B6 is closed: negative for graph structure and entity detail. The on-chain graph line of
the programme is closed (M2, B2, B3, B4, B5, B6).
