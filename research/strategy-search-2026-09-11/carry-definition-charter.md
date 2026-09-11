# Carry definition diagnostic — frozen contract

Experiment `carry-definition-20260911`. Development/exploratory, within existing
BTC/ETH spot/perpetual funding-carry mechanism. Administrative/nonfinancial
saved-result diagnostic; no financial trial appended to historical ledgers.

Hypothesis: the old opportunity-cost-inclusive NO-GO and negative index result
need not imply negative modeled trading-cost index returns. Competing explanation:
trading and rebalance costs already remove all modeled cash-income contribution.
This diagnosis does not adjudicate real executable cash profit because the old
index lacks a complete quantity/principal/collateral book. Section 41 already
reveals a positive pre-opportunity-cost Sharpe; this is result-informed
forensics, not an unseen test or an independent discovery.

Four inputs: exact saved dev/holdout costs JSON and stressed daily CSV. Windows
are [2021-11-08,2025-03-31) and [2025-04-01,2026-07-01), both exposed, latter spent.
Six complete cases: each window × BTC, ETH, fixed 50/50 sleeve. No selection,
optimization, fitting, seeds, new observations, account calls or alternative
parameters. One lifecycle run, two seconds expected compute, hard 60 seconds,
one CPU, less than 256 MiB; network forbidden. All cells retained if unavailable.

For each index day add the saved constant `rf_daily * margin_fraction_of_perp_notional`
to the saved stressed return. Report additive sum, mean, compounded index and
sample-standard-deviation Sharpe on the historical sqrt(252) convention for
reconciliation only. No resulting percentage is called full-capital cash return.
Both 1,000/10,000 cash profit and BTC/ETH beta/risk gates are explicitly unavailable
from these inputs. Cash, opportunity cost, conversion, principal, reserves and
realized filling cannot be established by algebra on old indices.

Admission: exact hashes, frozen cost-window labels, positive declared target
notional exactly one, finite numbers, chronological unique complete UTC daily
clock, no missing rows, and sleeve equals 50/50 input series. Recomputed blended
stressed Sharpe must agree with saved result within 1e-9. Zero variance produces
an undefined statistic, not a fabricated pass. No missing values are filled.
An unavailable window retains three unavailable cells and its reason.

Inference is deterministic algebra on already observed records. No null p-value,
power claim, annual forecast or statistical rejection is made. Unknown historical
multiplicity is disclosed and bars confirmation. Sign change weakens only the
inference from opportunity-cost-inclusive loss to negative modeled cash index.
No sign change would support switching families unless another documented
measurement defect supplies greater information value.

Forensics: independent reviewer reconstructs sums, means, compounding and
Sharpe from the raw saved series without importing this implementation; verifies
the rf charge and no actual capital denominator. Synthetic constant, missing,
nonfinite, chronology and blend-corruption cases. Required convention diagnostic:
sum(log1p(index returns)) is retained as an explicitly invalid arithmetic-booking
shadow, never financial PnL. No price-level book exists to perform a genuine
hedge cashflow convention swap; report that limitation rather than invent one.

If the definition difference is confirmed, the next eligible action is a
separately registered data/quantity-book feasibility investigation with actual
funding-event marks and complete capital. If data cannot be admitted, mark
unavailable and proceed into the next family. The historical NO-GO remains
unchanged in every branch. Neither outcome advances to paper or strategy use.
