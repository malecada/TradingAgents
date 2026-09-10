# Accounting and execution contracts

No single implementation below models every instrument. Reuse an engine only
when its quantities, timing, fees and missing-data behavior fit the registered
claim. Passing code tests does not validate trading profitability or venue fills.

| Implementation | Contract and useful boundary | Limits that a new run must admit |
|---|---|---|
| [Linear holdings book](../../tradingagents/accounting.py) | Signed linear notionals marked from previous price; targets use pretrade NAV, traded notional pays fees, simple returns mark retained quantities. `None` target retains holdings; explicit zero closes. Missing held return/funding raises. | `funding=None` is an explicit zero-funding assumption, not evidence of no funding. Inputs supply timing, price and funding conventions. No automatic recovery of settlement or pathwise margin events. |
| [USDT-linear event book](../../tradingagents/event_accounting.py) | Explicit contract identity/multiplier/lifetime, signed quantities, event ordering, fee/rounding evidence, funding calendar and settlement events. Returns a cashflow/quantity ledger. | Inputs must be admitted; historical venue rules are not inferred. Supports its declared linear contract type, not arbitrary inverse/coin-margined instruments or a full exchange liquidation simulation. `funding=None` explicitly excludes funding. |
| [Dated-carry Decimal calculator](../../scripts/carry_feasibility_math_2026_09_10.py) | Pure arithmetic for depth-limited spot/futures matching, spot base-fee gross-up, lot limits, full-budget reserve/idle cash and registered terminal cash scenarios. | Frozen conditional USDT-linear terminal model. Does not model the entire margin path, realized fills, live fee applicability or all fiat/transfer costs. Futures sale notional is not spot cash proceeds. |
| Predlab [Phase P](../../tradingagents/predlab/pp.py)/[Phase O](../../tradingagents/predlab/opt.py), [xsect portfolio](../../tradingagents/xsect/portfolio.py) and [trend](../../tradingagents/xsect/trend.py) | Strategy wrappers and portfolio evaluation using their declared data/selection rules and accounting hooks. | Audit status is family/date-specific; price proxies, aggregate or omitted funding, availability and sample spending remain qualified. A wrapper is not an admission bypass. |
| [Execution package](../../tradingagents/execution) and [monitor package](../../tradingagents/monitor) | Venue adapters, paper/live order handling, reconciliation and journal/monitor measurements. | Account actions and production operation require separate authority. Existing journal entries do not prove reconciled fills or corrected net returns. Follow the [operations](../operations/OPERATIONAL_INTEGRATION_2026-09-10.md) and [funding](../funding-capture/FUNDING_CAPTURE_2026-09-10.md) records. |

Before extending an engine, write down the economically necessary cash/base
quantities, units, fee currencies/bases, funding and settlement events, action
clock, missing-input behavior, collateral/reserve and residual exposure. Test
the changed boundary with synthetic cases and independent literal cashflow
reconstruction. Keep the convention-swap check as a disclosed diagnostic;
there is never a choice to book log returns as arithmetic PnL.

Preserve the old implementation and outcomes when a new economic assumption is
needed. A common run lifecycle can share admission/retention plumbing without
merging these distinct financial contracts or reexecuting historical runners.
