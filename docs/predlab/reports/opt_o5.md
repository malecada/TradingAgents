# Stage O5 — funding-carry tilt inside the book (predlab_opt)

Grid frozen pre-run (8 configs: λ{25,50,100}% × window{7,30}d + 2 reverse
mechanism checks). Base: ewma_20 raw book (SR +1.928, cumulative funding
carry −0.990 over the window — the book is a net funding PAYER).

## Results

| config | full | D | V | MaxDD | carry Σ | turn |
|---|---|---|---|---|---|---|
| carry_l25_w7 | +1.955 | +1.751 | +2.605 | 42.5% | −0.565 | 0.30 |
| carry_l25_w30 | +1.903 | +1.685 | +2.601 | 45.7% | −0.662 | 0.27 |
| **carry_l50_w7** | +1.960 | +1.815 | +2.420 | 40.9% | −0.141 | 0.35 |
| carry_l50_w30 | +1.861 | +1.686 | +2.418 | 45.2% | −0.335 | 0.30 |
| carry_l100_w7 | +1.916 | +1.891 | +1.997 | 37.8% | +0.708 | 0.45 |
| carry_l100_w30 | +1.739 | +1.653 | +2.010 | 47.2% | +0.321 | 0.35 |
| rev_l50_w7 | +1.756 | +1.406 | +2.889 | 54.4% | −1.839 | 0.36 |
| rev_l50_w30 | +1.895 | +1.569 | +2.938 | 48.3% | −1.646 | 0.31 |

## Verdict: NO ADOPTION — axis closed this cycle

Best carry_l50_w7 +1.960 (Δ+0.032 < +0.10 floor). Incumbent stands.

## Mechanism validated (even though below adoption floor)

- Carry response is monotone and in-direction: cumulative carry −0.990
  (ref) → −0.141 (λ50/7d) → +0.708 (λ100/7d). The tilt does exactly what
  it claims.
- Reverse mechanism check behaves: rev configs pay MORE funding (−1.84)
  and lose SR (−0.17 at λ50/7d twin) with worse DD — the small carry
  effect is genuinely carry, not noise.
- Net economics: carry recapture ≈ +0.85 cumulative log-return at λ50,
  but extra turnover (0.25→0.35) at 5bp eats most of it → ΔSR +0.032.
  **§43/§46 reconciliation from the inside**: the funding premium is
  real but too thin to clear costs even when membership costs are sunk.
- 7d funding window strictly dominates 30d at every λ.

Ledger: 8 rows (cumulative predlab_opt trials: 52; program n_trials: 68).
