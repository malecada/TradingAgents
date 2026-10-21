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

Next safe action: implement plan tasks 2–9; freeze labels and fetch 1-minute bars
(B6-CP1); run the pass and the Tron stream (B6-CP2); forecasts (B6-CP3); events and
`RESULTS.md` (B6-CP4).
