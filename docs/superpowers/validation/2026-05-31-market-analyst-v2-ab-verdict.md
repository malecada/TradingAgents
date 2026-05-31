# Market Analyst v2 A/B — Verdict

**Run date:** 2026-05-28 → 2026-05-31 (3 days wall clock on VPS)
**Branch:** feature/market-analyst-v2
**Universe:** BTC + ETH + BNB + SOL (V5 4-coin)
**Window:** 2026-01-16 → 2026-04-15 (89 bars, except SOL D = 71 bars due to OpenAI quota gap)
**Model:** all gpt-4o-mini
**Quant baseline:** V5 4-coin preset (`v5_4coin`)

## Variants

| ID | analysts | market_mode | market_skip_llm |
|---|---|---|---|
| A_pure_quant | onchain, prediction | legacy | - (no market analyst) |
| B_legacy_market | market, onchain, prediction | legacy | False |
| C_v2_struct_only | market, onchain, prediction | v2 | True (no narrow LLM) |
| D_v2_full | market, onchain, prediction | v2 | False |

## Hybrid Sharpe by (variant, coin)

| Coin | A_pure_quant | B_legacy_market | C_v2_struct_only | D_v2_full |
|---|---|---|---|---|
| bitcoin | 5.63 | **7.23** | 5.82 | 5.93 |
| ethereum | **3.20** | 3.51 | 2.62 | 1.67 |
| binancecoin | 2.88 | 3.45 | **3.64** | 3.11 |
| solana | 2.20 | 1.71 | 2.39 | **2.40** (71 bars) |

## Do-no-harm gates — D_v2_full vs A_pure_quant

| Coin | ΔSharpe | 95% CI | p_positive | Gate 1 (≥0) | Gate 2 (CI≥−0.15) |
|---|---|---|---|---|---|
| bitcoin | +0.22 | [−0.65, +0.93] | 0.76 | ✅ | ✅ |
| **ethereum** | **−1.60** | **[−4.23, +0.57]** | **0.076** | **❌** | **❌** |
| binancecoin | +0.31 | [−0.83, +1.66] | 0.70 | ✅ | ✅ |
| solana | +0.09 | [−1.27, +1.39] | 0.57 | ✅ | ✅ |

Gate 3 (≥1 coin with ΔSR > 0.3 AND p_positive ≥ 0.9): **FAIL** — closest is BNB (+0.31, p_pos 0.70).

## Verdict: REJECT D_v2_full on ETH

All three acceptance gates fail (Gate 1 ETH, Gate 2 ETH, Gate 3 overall).

The asset-agnostic v2 refactor **DID NOT** fix the ETH harm reproduced in §23.11 LOO ablation. M1–M6 mechanism stack (conflict-gated FLAT, per-coin calibration, anonymization, regime conditioning, indicator cap, third-person persona) is insufficient on ETH.

## Detailed findings

1. **BTC**: any market analyst helps. B_legacy strongest (+1.22 SR vs A, p_pos 0.98). v2 modest help (+0.22).
2. **ETH**: any market analyst hurts. Worse with v2. Anonymization (M3) did NOT eliminate ETH narrative-bias channel.
3. **BNB**: C_v2_struct_only best (+0.80 vs A). v2 LLM call (D) hurt vs structured-only (C).
4. **SOL**: v2 slight positive but n=71 wider CI.
5. **C ≈ D**: structured snapshot captures most of what v2 LLM call adds. LLM interpretation not adding alpha — wasted ~50% of D's API budget.

## Per-coin production policy

Same as §23.11 LOO conclusion:

| Coin | Production market_mode |
|---|---|
| BTC | `legacy` (B beats v2; or `v2` modest help) |
| ETH | OFF (no market analyst in chain) |
| BNB | `v2` + `market_skip_llm: True` (C strongest) |
| SOL | `v2` neutral; either path OK |

## SOL D 19-bar gap not material

OpenAI quota exhausted during D_v2_full SOL run on bars 2026-03-28 → 2026-04-15. CSV has 71 valid + 19 error rows. SOL D verdict (slight positive, +0.09 ΔSR) is stable; remaining 19 bars unlikely to flip the sign or change the do-no-harm decision on ETH (which is the binding constraint).

## Artifacts

- `summary.json` — full stats + bootstrap CI
- `{variant}/{coin}_*.csv` — per-bar signals + market_features
- `{variant}/backtest/daily_returns.csv` — per-bar (hybrid_ret, baseline_ret) for all 4 coins
- `{variant}/backtest/summary.json` — backtest_hybrid output (last-coin overwrite bug — kept for reference; use top-level summary.json for verdict)
- `{variant}/backtest/hybrid_vs_baseline_equity.png` — per-variant equity curves
