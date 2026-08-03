# Stage O4 — vol-target overlay re-tune (predlab_opt)

Grid frozen pre-run (12 configs; gates = pp2 precedent: DD reduction ≥25%
AND SR ≥ 0.9×raw AND V-consistency; n_trials=12 disclosed). Base book:
ewma_20 champion (raw SR +1.928, MaxDD 46.3%). New claim set — the frozen
pp2 vt10 forward confirmation on the old S1 book is untouched.

## Results (full window)

| config | SR | D / V | MaxDD | ΔDD | scale |
|---|---|---|---|---|---|
| vt10_naive20 | +1.781 | +1.574/+2.515 | 12.1% | −74% | 0.22 |
| vt10_ewma20 | +1.823 | +1.594/+2.624 | 11.1% | −76% | 0.21 |
| vt10_har | +1.747 | +1.373/+2.792 | 6.9% | −85% | 0.15 |
| vt15_naive20 | +1.781 | +1.574/+2.515 | 17.6% | −62% | 0.33 |
| vt15_ewma20 | +1.823 | +1.594/+2.624 | 16.2% | −65% | 0.32 |
| vt15_har | +1.747 | +1.373/+2.792 | 10.2% | −78% | 0.22 |
| vt20_naive20 | +1.781 | +1.574/+2.515 | 22.9% | −51% | 0.44 |
| vt20_ewma20 | +1.823 | +1.594/+2.624 | 21.1% | −54% | 0.43 |
| vt20_har | +1.744 | +1.368/+2.792 | 13.4% | −71% | 0.30 |
| vt10/15_naive20_cap15 | = cap2.0 rows | | | | |
| **vt15_naive20_b100** | **+1.892** | **+1.713**/+2.515 | **17.6%** | −62% | 0.32 |

All 12 PASS the frozen gates. Selection rule (max SR, tie-break MaxDD):
**vt15_naive20_b100 ADOPTED (chain seq 2).**

## Reading

- **Breadth guard is the surprise winner** (O3 forensic lesson paying
  off): forcing exposure to 0 while <100 names listed costs nothing on V
  and RAISES full SR +1.781→+1.892 and D +1.574→+1.713 — the thin-2021
  regime was net-negative for the book, not just its DD source.
- HAR estimator = deepest DD cuts (−85% at vt10, MaxDD 6.9%) at ~0.08 SR
  cost — the pre-declared knob if a mandate needs single-digit DD.
- Caps never bind at these targets (cap15 rows identical); SR is
  target-invariant apart from cost drag, as expected for linear scaling.
- Overlay is a deterministic transform of the already-audited book —
  placebos N/A; PIT of the breadth count verified (signal-availability
  at t reflects t−1 info).

**New system (chain seq 2): ewma_20 eq-quintile top-200 + vt15 naive20
breadth-100 overlay — net SR +1.892, MaxDD 17.6%.**

Ledger: 12 rows (cumulative predlab_opt trials: 44; program n_trials: 60).
