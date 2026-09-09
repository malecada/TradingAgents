# combo_c1 — Thin-edge combination one-shot (registered 2026-09-02)

Status: **REGISTERED pre-result.** Gates key `combo_c1` in `data/rebuild/gates.json`
is written in the same commit as this file, before any sleeve series on the
holdout exists. Source charter: `master_thesis/LEADS_SCOPE_2026-09-02.md` Lead 1;
audit basis: `AUDIT_RESEARCH_PROGRAM_2026-09-02.md` §4.1, §6 item 1.

## Goal (falsifiable)

Four dev-selected, placebo-clearing sleeves — frozen exactly as their parent
cycles selected them, priced under simple returns — combined by a formulaic,
pre-declared weight rule, earn a positive net Sharpe on the sealed
2025-04-01 → 2026-07-01 window that none of the four ever touched.
Null: the combination is ≤ 0 or fails the timing placebos.

## Sleeves (frozen; parent config verbatim; engines = lead-0 fixed versions)

| id | sleeve | config | parent | dev net SR (simple) | placebo |
|---|---|---|---|---:|---|
| S1 `liq_fade` | intraday liquidation-cascade long-fade | top-50 PIT monthly, 1h, thr 3.5, H 48, w_per 0.1, cap 1.0, 10 bp, rf 4.5 % full capital | §49 liq_fade_i1 | 1.3047 | .002 |
| S2 `carry` | XS funding carry L/S | top-50 monthly PIT, L 30, leg 0.2, daily, 10 bp, rf 4.5 % full capital | §46 carry_xs_t1 | 0.9234 | .025 |
| S3 `momentum` | XS momentum long-only | top-100 weekly PIT, L 28, skip 0, K 10, 10 bp, no rf (fully invested) | §43 xs_mom_p1 | 0.6918 | .020 |
| S4 `value` | NVT-proxy tercile L/S | weekly Monday, top-150 ∩ CoinMetrics-community names, lag 2, 10 bp, rf 4.5 % | §51 value_xs_t1 | 0.4173 | .014 |

Excluded with reasons: trend_wide (placebo fail = exposure), S3 hourly sign
filter (cost-dead at taker; lead 2), C3-P (LLM; own cycle).

Dev pins (P0 parity, 1e-6): S1 `data/rebuild/liq_fade/dev_results.json`
(thr 3.5, H 48); S2/S3 Sep-2 forensic simple numbers
(`master_thesis/data/audit_2026-09-02/convswap_results.json`); S4
`data/rebuild/value_xs/grid.json` (nvt_proxy, tercile).

## Weight rule (pre-declared)

- **W1 inverse-vol capital allocation (primary, gated):** w_i ∝ 1/σ_i, σ_i =
  dev-window daily SD (ddof 1) of the sleeve's net return on the ALIGNED dev
  calendar (2021-01-01 → 2025-03-31, zero-filled where a sleeve is not yet
  active); Σw_i = 1; no leverage.
- **W2 equal capital (sensitivity, reported not gated):** w_i = 0.25.
- Sleeve series are daily; S1 hourly PnL is aggregated to UTC days by its own
  engine. Constant-mix: fixed capital weights on daily sleeve returns, no
  cross-sleeve rebalancing cost (deployment contract, stated).
- rf: S1, S2, S4 charge rf 4.5 %/yr on their allocated capital inside their
  engines; S3 is fully invested in coins and charges none. The book therefore
  charges rf on (w1 + w2 + w4) of capital — disclosed, not corrected.
- Dev combined SR (W1, W2), σ_i, w_i and the 4×4 dev correlation matrix are
  computed by `scripts/combo_c1_register.py` and written into the gates key
  under `registered_dev` before probes run; the ≥ 0.5×dev criterion refers to
  W1's dev number.

## Windows and data

- Dev 2021-01-01 → 2025-03-31 (reference only; weights and pins).
- Holdout **H1 virgin** 2025-04-01 → 2026-07-01, one evaluation of one frozen
  book; `scripts/combo_c1_holdout.py` refuses to run if
  `data/rebuild/combo_c1/holdout_verdict.json` exists.
- Stores: 799-sym daily klines (→ 2026-07-02), 1h klines (333 symbols →
  2026-07-28), funding (→ 2026-07-03), CoinMetrics community fundamentals.
- **Data deviation from the scoping charter:** the fundamentals store on disk
  is capped at 2025-04-15 by design (value_xs_t1 seal). A separate vintage
  store `data/xsect/fundamentals_h1/` (2020-06-01 → 2026-07-01, own manifest
  and vintage stamp, pulled 2026-09-02) serves S4 on the holdout. The sealed
  default store is untouched and keeps dev parity. Restatement between the two
  stores on the dev overlap is measured and reported in P1. Holdout rows are
  as-of the 2026-09-02 pull — a PIT caveat (vendor restatement only), disclosed.
- Holdout PIT universes: S1 `data/xsect/liq_fade_universe_h1.json` (monthly
  top-50 by trailing-30d median quote volume, min age 60d, months 2025-04 →
  2026-06), S4 `data/xsect/value_xs_universe_h1.json` (monthly top-150 ∩
  CoinMetrics-mapped names), both from the daily store by the parents' own
  functions; S2 monthly and S3 weekly eligibility computed in-run.
- Hourly panel for S1 loaded from 2024-09-01 (z-window 2160 bars fully warm
  by 2025-04-01); daily value features from 2024-09-01.

## Blocking probes (in order; each has an abort verdict)

- **P0 engine parity** — each sleeve's dev series under the fixed engines
  reproduces its pin to 1e-6; else STOP (harness).
- **P1 coverage** — every store spans the holdout through 2026-07-01; PIT
  eligibility ≥ 20 names at every S2/S3 rebalance and ≥ 20 S1 universe names
  every month; S4 weekly signal-valid breadth median ≥ 20; else STOP (data).
  Reports the fundamentals_h1 vs sealed-store restatement on the overlap.
- **P2 leakage canary** — advancing each sleeve's weight path by one bar
  (W.shift(-1): today's weights use tomorrow's decision) raises its dev SR by
  ≥ +1.0; else STOP (harness cannot see leakage).
- **P3 correlation sanity** — dev pairwise |ρ| ≤ 0.6 for all pairs; else the
  "independent mechanisms" premise is false: disclosed, cycle continues with
  W1 unchanged.

## Gates (one-shot, ALL required; metrics defined in `tradingagents/xsect/combo.py`)

1. net SR_H(W1) ≥ 0.5 × SR_D(W1) AND net SR_H ≥ 0.5 (absolute floor, §41 convention);
2. same sign as dev;
3. dual-family weight-path placebo on the holdout, 500 draws each, costs and
   rf re-applied by the sleeve engines, p = (1 + #{placebo SR ≥ real}) / 501,
   gate on the WORSE family p < 0.10:
   (A) per-column independent circular shift within every sleeve (min offset
   30 days; 720 bars for the hourly sleeve), seeds 0..499;
   (B) one shared offset in days (30 ≤ k ≤ n−30, seeds 0..499) applied to
   every sleeve and column (×24 for the hourly sleeve);
4. every sleeve's holdout contribution w_i·mean_i ≥ 0;
5. max drawdown_H ≤ 25 % on compounded simple returns;
6. top single-name |gross PnL| share ≤ 50 %, pooled across sleeves by symbol,
   denominator Σ_s |PnL_s|;
7. convention-swap: feeding log returns to every PnL step does not flip gates 1–2.

Reported, not gated: W2 book on all of the above; 2× cost stress; per-sleeve
holdout SR; sub-period (two halves) SR; DSR at n_trials 1 (declared),
family denominator 28 (6 + 6 + 12 + 4 parent configs) and cumulative
ledger denominator (unique config hashes + 1).

## Multiplicity

Confirmatory `n_trials = 1`: frozen book, virgin data, one evaluation.

## Stop rule

FAIL on any gate ⇒ the thin-edge stratum is closed as a combination; no
re-weighting, no sleeve dropping, no second look; H1 is SPENT for S1–S4
(irreversible). PASS ⇒ stop-and-decide with the user: paper-journal the
frozen book from the F window (2026-07-02 →) forward; deployment decisions
remain the user's.

## Decisions (resolved 2026-09-02 on "go ahead with the first open lead")

(a) W1 inverse-vol primary; (b) absolute holdout floor 0.5; (c) H1 spend for
S1–S4 accepted (forecloses later per-sleeve holdout claims).

## Mechanics

Branch `feature/combo-c1` off `feature/llm-event-xs` (`main` carries no xsect
code). Engine `tradingagents/xsect/combo.py` (pure) + `combo_sleeves.py`
(sleeve builders on the frozen parent engines); scripts
`combo_c1_data.py` (holdout universes; fundamentals_h1 pull via
`fetch_xsect_fundamentals.py --out-dir --allow-past-holdout combo_c1`),
`combo_c1_register.py` (gates key + dev numbers), `combo_c1_probes.py`,
`combo_c1_holdout.py` (verdict-file lock, ledger row with allow_holdout).
Ledger experiment `combo_c1`. THESIS §76.
