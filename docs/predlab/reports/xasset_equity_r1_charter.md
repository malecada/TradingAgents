# xasset_equity_r1 — champion cross-asset replication charter (US equities)

Registered 2026-08-18 in `data/predlab/gates.json` (key `xasset_equity_r1`),
frozen before any equity strategy number existed. Pre-result amendment
2026-08-18 (enumeration + segmentation) declared in-file.

## Question

Does the Phase-O final champion — ewma_20 Parkinson low-vol eq-quintile
long-short on a monthly-PIT top-200 dollar-volume universe with the
vt15_naive20_b100 overlay — yield returns outside crypto, applied verbatim
to US equities?

## Design (Bybit-r1 precedent)

No strategy parameter was ever fitted to equity data, so the entire window
2017-01-03 → 2026-08-14 is virgin: a single one-shot full-window run,
n_trials = 1, no dev/holdout split. Sensitivity grid (borrow {0,1,3}%/yr ×
taker {2.5,5,10}bp) is disclosure-only.

Forced asset-class adaptations, everything else verbatim:
1. Annualization 365 → 252.
2. Funding carry → 0; short-leg borrow 1%/yr charged daily on scaled short
   gross (equity analogue of carry; rf on collateral ignored — conservative).
3. Taker 5bp/side kept.

## Data (all free)

Alpaca SIP daily bars 2016-01-01 → 2026-08-14, `adjustment=all`, incl.
delisted symbols (probe-verified: BBBY ends exactly 2023-05-02).
Enumeration = Alpaca assets active+inactive ∪ S&P500 ever-members 2016+
(fja05680) ∪ SEC company_tickers — Alpaca alone purges major deaths
(BBBY/SIVB/FRC/TWTR/ATVI). Ticker-recycling guard: series split into
independent segments at >90-day gaps (FB → Meta then a recycled ETF).
Store: `data/xsect_equity/`.

## Gate ladder

- **P0 probes**: crypto parity pin (ovl SR +1.892 ± 0.001 — engine reuse
  exact), return-oracle leaky canary, planted-alpha recovery.
- **P1 feasibility** (else INFEASIBLE, trial unspent): ≥2000 days with
  breadth ≥100; ≥100 dead symbols inside traded universe; split sanity
  (AAPL/TSLA 2020-08-31).
- **One-shot criteria** (hierarchical, frozen):
  - **U1 transfer**: ovl net SR ≥ 0.946 (=0.5× crypto dev, Bybit mirror)
    AND both placebo families p<0.05 @400 AND ≥3/4 subperiods positive.
  - **U2 yields-returns**: ovl net SR > 0 AND placebos p<0.05 AND
    3%-borrow stress SR > 0.
- **Stop rule**: one run; failure = clean negative; any equity re-tuning
  requires a new registered cycle.

## Artifacts

`scripts/predlab_xasset_register.py`, `scripts/predlab_xasset_fetch.py`,
`scripts/predlab_xasset_r1.py` (probes | integrity | run),
`data/predlab/xasset_r1_{probes,integrity,result}.json`, ledger row in
`data/predlab/trial_ledger.jsonl`.
