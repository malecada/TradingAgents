# Dated spread pure book: independent synthetic accounting review

September 11, 2026. **PASS for the current pure engine; adapter, statistics,
full lifecycle and final registration remain separate pending reviews.** No
observed price, mark, funding or financial output was read or evaluated. The
checker imports the pure engine only for invented inputs; every expected cash
quantity, wallet, cost and stress value is independently reconstructed from raw
literal Fractions, without reusing engine accounting helpers.

Current reviewed dated_spread_book.py SHA256:
`e809bdb0240d3afd907c490e1054216d481181fe83c0d8dab9e992b8711f3b4b`.
The retained checker/report pass 28 invented scenarios and 7,432 independent
numeric assertions at absolute tolerance 1e-8 USDT. The eight declared asset/
capital/cost combinations each retain 56 daily rows, 168 funding observations
with 167 included, two diagnostic scalars and nine hypothetical stress states.
The checker also evaluates adversarial cases outside that primary denominator;
they are synthetic engineering checks, not research trials.

The independent algebra confirms that no futures notional is credited as cash
and no spot principal is debited. Entry fees reduce their respective 40% and
50% wallets. Long dated and short perpetual signed price cash, all four fees,
signed funding and idle 10% reconcile to final capital. The daily low/high
maintenance sensitivities retain separate wallets and negative funding order;
terminal trace wallets reconcile to released cash with zero holdings. Same-q
zero-funding and frictionless scalars, raw price decomposition and slippage
charges reconcile. Every hypothetical stress state's pre-exit wallets,
maintenance sensitivities and separately closed cash reconcile without charging
maintenance again as a closing fee.

Planted common-price changes produce zero raw two-leg price cash. Another
planted path has positive total wealth but a negative perpetual wallet, and the
independent wallet-deficit diagnostic catches it. Nonpositive intermediate NAV
retains signed cash while return/convention and modeled fraction diagnostics
remain unavailable. Six exact Decimal boundary checks at and 1e-20 either side
of one-lot and 3,995-lot capital thresholds verify that sizing respects the
declared joint-fee ceiling rather than floating rounding into a larger lot.

## Findings resolved before outcomes

The initial funding guard rejected the canonical entry event if its actual stamp
was just before START, despite the declared ±5-second calendar tolerance. The
current funding() at lines 45–62 identifies the first canonical slot by index,
allows its stamp through START±5000ms, excludes it and preserves its timestamp.
Every included event must satisfy the canonical tolerance and ownership rule.
First-event offsets -5000, -1, 0, +1 and +5000ms pass; +5001ms, an extra early
June26 event, a missing event and ambiguous included ownership reject. A later
canonical midnight event stamped five seconds early books to its actual prior
UTC day. That convention affects intraday wallet ordering and must remain
explicit in the adapter/charter. The adapter still needs independent proof that
it selects canonical Q2 indices 90:258 before this engine is called; the engine
test alone cannot prove the full 273-event parent calendar was re-admitted.

A separate concrete numerical issue was found in the convention diagnostic:
log1p applied to rounded simple returns could lose a tiny positive NAV ratio.
With invented zero funding and first perpetual mark 354.1735910138923, the first
NAV was positive 2.2737367544323206e-13. Initial source
`e62edccc937a93cc8582f08fb0cb42fefdf082a91ffd0e8e332ea8b3affe43de`
reported log sum -0.020902814919864687 instead of endpoint log return
0.0028137116974486323. Signed cash remained correct. The coordinator changed the
diagnostic to stable daily log(NAV)-log(previous NAV) differences before outcomes,
with explicit equivalent-log1p wording. The retained regression now reports
0.0028137116974491505, within 5.2e-16 of the endpoint identity. This is still an
invalid arithmetic-PnL shadow, not cash profit or an alternative return convention.

## Untested claims and remaining admission work

This review does not yet verify source adapters, checksum/contract identity,
full Q2 funding and event-mark coverage, BTC/ETH exposure inputs or HAC output.
It does not establish actual lot/fee applicability, order fills, exchange margin,
intraday liquidation, low empirical beta, confidence in expected profit or
graduation. Separate-wallet and daily-extrema sensitivities remain conditional
on the frozen linear model and provisional maintenance assumptions.

The runner must retain eight primary cells, 16 scalar statuses and 72 stress
statuses even if a source or primary case is unavailable. Exact output caps,
source loss behavior and guarded full CLI require review before the final
seventh-attempt gate/certificate. No financial execution is approved by this
pure-engine result, and no actual financial experiment has run in this review.
