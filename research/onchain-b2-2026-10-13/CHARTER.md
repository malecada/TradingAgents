# Branch B2 charter — weekly on-chain graph screen

Registered 2026-10-13 before any B2 capture or outcome. Spec:
`docs/superpowers/specs/2026-10-13-onchain-b2-weekly-screen-design.md`; frozen
numbers in `config/b2.json`; decision rules in `gates.json`.

Questions: does on-chain activity (F1), exchange/whale role flow (F3a) or
motif structure (F2, F3b) improve price-only (F0) forecasts of next-day and
next-week ETH direction, next-week return, realised volatility and volume?

Development 2017-10 → 2024 with yearly walk-forward (2019–2024); sealed holdout
2025-01-06 → 2026-10-05 (92 weekly decisions), opened once, only for the
configurations committed in `selection.json`. Branch B's spent 2024 year is
development data here. No raw transaction storage; free public sources only.
