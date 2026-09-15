# Independent synthetic wrapper-book review

Scope: pure engineering review of `wrapper_book.py` and its six invented tests.
Reviewed helper SHA256:
`5bfba46305fc95be8b7af7f4803becae4a13f767a737d0429413c7941f6a9b38`.
No empirical panel, source acquisition, financial experiment, registration or
production operation was executed. No implementation file was edited.

## Disposition

The tested signed ledger conserves full initial capital and funded gas. Changes
are required before financial freeze for consistent tail-loss accounting and
caller-visible evidence preservation on an incomplete book. The optional log
diagnostic also needs a bounded failure path. This is not financial admission.

## Findings

1. **Use the same net wealth basis for wrapper failure.**
   `wrapper_book.py:101` reports gross wrapper value as `loss_usd`, divided by
   the net liquidation origin. Other stress losses subtract post-shock net
   liquidation wealth. An independently invented wallet containing USDC7,500,
   ETH0.005 and WST1, at USD marks1/2,000/2,400 with primary costs, has initial
   liquidation wealth9,880.21517. After writing off WST and liquidating the
   surviving wallet it has7,499.760829: a net loss2,380.454341, whereas the
   helper reports2,400. The difference19.545659 is avoided wrapper-sale friction
   and gas. Re-liquidate a copy with WST zero for the comparable loss; retain
   gross affected-position value under a separate explicit name if useful.
   This does not turn the accepted separate catastrophe into a market-stress
   veto or grant any exemption for ordinary discounts/depegs.

2. **Expose funded partial books before admitting an empirical runner.**
   `wrapper_book.py:115` keeps the only book, events, states and attribution in
   local variables, returned only at line176. A late exception, including one
   raised by stress after a completed `convert` at lines137–144, leaves the
   caller unable to retain those completed postings. Add a caller-owned progress
   record or a failure snapshot with normalized literal postings, initial and
   current balances, completed observations, calculation stage and partial
   attribution. Preserve it before catchable failures and test an injected
   failure after a completed entry or first terminal sale. The eventual runner
   must retain this evidence while classifying the full cell as unavailable;
   it must not infer a terminal result from a partial account.

3. **Do not let a convention diagnostic invalidate supported exact cash math.**
   `wrapper_book.py:126` casts a positive exact ratio to float. A fully aligned
   invented wallet-cash panel with ETH marks1e-200 at inception/entry and1e200
   thereafter passes `validate_panel` but raises `OverflowError: integer
   division result too large for a float` in this diagnostic. Either use a
   bounded Decimal logarithm or retain diagnostic unavailability independently
   of exact PnL. This is robustness of the declared exact-input domain; no claim
   is made that such extreme marks are realistic source observations.

## Independent verification

- The six named synthetic tests passed independently.
- Nine additional invented books (all three policies and all three cost cases,
  with varying exact USDC/ETH/WST marks) were replayed from literal initial
  atoms, debits, credits and gas. Every before/after balance matched, no balance
  became negative, and terminal marked wealth less the authored USD route and
  initial USD10,000 equalled the exact reported profit.
- Gas is funded before receiving conversion output. The native terminal sale
  sells the balance less its own gas, with that gas charged once. Remaining
  native reserve has its own market gain/loss and exit cost in all policies.
- F2 spends one quarter of initial investable USDC atoms at the fixed second
  mark. Idle USDC and the initial ETH reserve remain in capital. WST quantity
  receives no additional native-staking accrual; the ETH control can therefore
  separate the conditional wrapper-price increment from common ETH movement.

## Required scope qualifications

The two WST haircuts versus one ETH haircut are a composite hypothetical
execution model. The code does not execute or reproduce two integer-rounded v3
pool hops, establish the wrapper route, or verify fee tiers, depth, MEV, approval
state or actual gas. State those limitations in the frozen contract. USDC
`terminal_atoms` are the balance before the separate USD-route charge, not a
recorded personal USD redemption or a post-route token balance.

Stress loss is measured against each origin's net wealth; the separate dynamic
peak drawdown must keep its distinct meaning. The retained stress row is chosen
by maximum loss fraction, so its `loss_usd` is not necessarily a separately
maximized dollar loss. Do not label it as such without independent maxima.
Delay scenarios report hypothetical eventual marks and explicitly leave cash at
the fixed horizon under a lock unavailable. They cannot establish successful
withdrawal, a drawdown guarantee or account feasibility. Gas-dust cases rejected
by `liquidation` are unavailable; the blanket docstring statement that all dust
is valued should not imply those rejected cases have an executable exit.

Source identity, causal mark availability, oracle adapter behavior, native
conversion ratio, actual staking yield, bridge discounts, executable redemption,
all inherited benchmark contrasts and complete unavailable-cell accounting were
not tested by this helper review. Same-block oracle inputs remain valuation
proxies even if their ABI and clock are subsequently qualified. Historical and
actual protocol failures remain outside this synthetic verification.
