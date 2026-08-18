# xasset_equity_r1 — result: NEGATIVE (2026-08-18)

One-shot verbatim replication of the Phase-O champion on US equities
(charter: `xasset_equity_r1_charter.md`; full narrative: main repo
`THESIS_FINDINGS.md` §66).

- P0: parity pin exact (+1.8921360, diff 0); oracle canary SR ≈ 38;
  planted 20bp alpha recovered (+1.81 SR uplift; probe threshold
  constant corrected pre-one-shot, v1 file preserved).
- P1: FEASIBLE — 2,417 days breadth ≥ 100; 128 delisted names inside
  traded universe; splits sane.
- One-shot: raw net SR +0.340 (DD 68.3%); ovl+1%-borrow SR +0.165
  (DD 37.1%); subperiods 3/4; placebo p_shift 0.2375 (FAIL), p_xshuffle
  0.000 (cost-confounded, not load-bearing); best-case grid +0.348.
- Verdicts: U1_transfer FAIL, U2_yields_returns FAIL. Champion edge is
  crypto-specific under verbatim transport; positive drift ≈ static
  low-vol exposure (same signature as trend_wide §45). Equity re-tuning
  = new registered cycle only.

Reusable asset: free survivorship-safe US equity daily store
(`data/xsect_equity/`, 7,972 symbols 2016-2026 incl. deaths + panels).
