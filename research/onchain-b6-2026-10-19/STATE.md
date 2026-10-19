# Branch B6 state

2026-10-19 — Registered (charter, config, pre-declared plan). No B6 pass output read yet.

2026-10-19 — Code complete (plan tasks 1–9; 29 B6 tests, 245 with B–B5). Labels frozen
(`research_artifacts/onchain-b6/labels/labels6.json`): exchange 35,297 addresses
(B2 4,961 ∪ eth-labels), DEX 353, bridge 332, MEV 3,749, funds 81; Tron exchange
addresses 149. Heavy-day probe (2025-06-02, fresh state): read 39 s, hourly rows 5.5 s,
peak 1.9 GB; 1,682 large transfers (841 deposits); mean per hour 33.7k active addresses,
2-core 21 %, giant component 77 %, 10.1k exchange counterparties.

Next safe action: implement plan tasks 2–9; freeze labels and fetch 1-minute bars
(B6-CP1); run the pass and the Tron stream (B6-CP2); forecasts (B6-CP3); events and
`RESULTS.md` (B6-CP4).
