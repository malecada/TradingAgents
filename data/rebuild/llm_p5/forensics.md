# llm_p5_hybrid forensic verification — gate FAIL (2026-07-28)

Verdict: **FAIL VERIFIED**. p_pos = 0.065 vs gate 0.90 (one-shot, registered
`d30842f` before any run). ΔSR = −0.465 [95% CI −1.04, +0.07], quant SR 0.699
→ hybrid 0.234 over 125 paired bars (2026-01-16 → 2026-05-21, causal engine,
causal costs, 3% intrabar price stop).

## Run integrity

- 126/126 decision bars generated, 0 propagate errors, 126/126 multiplier
  extractions (0 fallbacks), 0 missing slot factors. Runtime 20,485 s.
- Modulator behavior: mean multiplier 0.789 (σ 0.302), 100% of bars ≠ 1.0,
  75.4% of slots effectively modulated (factor ≠ 1), factor range [0.30, 1.14],
  mean effective_weight 0.427. The modulator is ACTIVE, not degenerate — the
  negative is not an inert-layer artifact.

## Probes

**P1 — parity (registered pre-condition for trusting the result).** The A/B's
cross-day probe read 65.9%; decomposition: CSV `quant_direction` vs pred-CSV
h7/h14 consensus SAME-day = **125/125 = 100%** — Layer 1 in the generator is
exactly the audited quant leg. The 34% cross-day divergence equals the
consensus's own 34.9% day-over-day sign churn. Harness fidelity confirmed;
the D−1 slot alignment (LLM info ≤ close d modulates the bar accrued on d+1)
is the live 00:05-UTC contract.

**P2 — alignment robustness (leaky legacy convention).** Applying factor d to
slot d (same-bar LLM information leak — the pre-audit harness convention):
ΔSR −0.006, p_pos 0.500. The modulator is neutral even WITH the leak on
causal legs. Conclusion robust to the alignment choice, and the legacy 1-yr
"ETH ΔSR +1.10" does not reproduce once the base legs are causal — the
apparent LLM alpha lived in the same-bar quant legs, not in the modulator.

**P3 — mechanism.** Mean quant daily return on dampened slots +7.5 bp
(n=69) vs −1.1 bp on neutral slots (n=56): the modulator systematically
dampened the profitable days. Return 4.2% → 1.0% while vol fell only
13.2% → 11.1%; maxDD improved a trivial 0.61 pp (5.70% → 5.09%).

**Power.** 125 paired bars, CI width ≈ 1.1 SR — wide, but the point estimate
is far on the wrong side; the gate asked for p_pos ≥ 0.90 and got 0.065.
This is not an underpowered null: it is directional evidence of harm at
p ≈ 0.94.

## Conclusion

Per the pre-registered stop rule: the LLM modulator layer remains
thesis-only, reported as **no-effect-to-harmful on honest legs** (Phase-5
wording: "base-dependent / no-effect on honest legs" — the measured sign is
negative). No prompt retuning, no second window, no second model. The
positive legacy hybrid results are now doubly closed: engine audit (same-bar
confirmed in `backtesting/engine.py`) + this re-measurement.
