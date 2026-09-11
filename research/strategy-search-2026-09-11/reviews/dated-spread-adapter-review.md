# Dated spread adapter, summary and exposure: independent review

September 11, 2026. **PASS for current source adapters, case retention and
descriptive statistics; full successor lifecycle and final gate remain pending.**
Only invented raw envelopes, planted benchmark returns and source were used.
No actual source inputs, financial observations, network or ledger were accessed.

Current SHA256 values:

- dated_spread_sources.py:
  `c3eb7278f23e0a34c54154bcb9918fb8bd266588f5822e2b18b60260059550e9`.
- dated_spread_statistics.py:
  `5fb0b7cf6a584c388706374e05bba79398e29047af8bb5ad05e85bb67d819283`.
- dated_spread_run.py:
  `a416ffa611d662f388ec9aa8674f34146a4a9660d6517b8efabcbff75442817e`.

The independent checker check_dated_spread_adapter.py and its report pass 14
scenarios plus 18 direct statistical-value comparisons. Full source re-admission
retains all 20 source identities: ten carry responses, eight dated ZIP/checksum
responses and two new daily-mark responses. It compares fixed specifications,
request identity, raw body size/hash/completeness, HTTP success and receipt clocks,
then reconstructs and compares complete parent admissions. ZIP checksum/member
validation precedes CSV extraction; mark receipt-file references and capture
closure are checked before accepting literal daily rows. There is no network
call or fallback in the adapter.

Funding is re-admitted against the full 273-event conditional Q2 calendar before
selecting canonical indices 90:258. The audit retains 90 prior, 168 selected and
15 later canonical slots. An independent hostile fixture moves the May1 first
event to START-5000ms and the June26 event to END-5000ms with an exaggerated rate.
The former remains the explicitly excluded first slot; the latter stays outside
the selected 168 despite its early actual clock. No price/rate criterion chooses
events. The pure engine separately excludes the first canonical slot, validates
all included ownership times and books later events by their actual UTC day.

Full invented input yields eight primary cases, 16 scalar diagnostics and 72
stress states. Entire carry, archive or mark envelope loss retains all eight,
16 and 72 unavailable identities and all 20 source statuses. An unavailable
source cannot disappear from the primary or subordinate denominators. Engine
exceptions are recorded per case; MemoryError is deliberately left to the
guarded failed-run lifecycle rather than disguised as a source verdict.

## Findings resolved before outcomes

Initial source assembly created an asset data object only after all its cash-
book sources passed. The runner required both asset objects to compute any joint
exposure. Therefore a BTC-only funding failure also hid the valid BTC spot
benchmark and suppressed a valid ETH book's exposure. Current sources.py:164–168
retains independently admitted benchmarks before cash-book dependencies, and
run.py:44–46 uses that separate set. The independent fixture now confirms four
BTC cases unavailable while all four valid ETH exposure estimates remain
complete. A BTC spot failure correctly makes the joint exposures unavailable.

Initial joint relevance used all(...) and returned false when all primary
results were unavailable. Current run.py:49–50 preserves three states: false
when an observed result fails the joint necessary condition, true only when both
cost cases are observed and pass, otherwise null. Independent whole-parent loss
tests verify null rather than a fabricated economic failure. The modeled net-
base fraction screen likewise retains null when its engine diagnostic is
undefined, rather than silently treating unknown as a measured threshold breach.

## Independent statistical reconstruction

For a planted noncollinear 56-day BTC/ETH design and noisy NAV series, the checker
directly forms X, solves (X'X)^-1X'y, constructs residual score products and adds
the Bartlett-weighted lag1–7 autocovariances. It then constructs the sandwich
covariance without finite-sample rescaling, standard errors and Student-t53
critical value at 0.9875. All three coefficients, nine covariance entries, two
standard errors and four interval endpoints agree with the implementation.
Expected values are not obtained from statsmodels. First-day benchmark returns
reference each series' entry open; later returns reference prior closes, while
NAV starts from the full capital. Singular design, zero NAV and missing day
fixtures correctly produce unavailable exposure.

These are exploratory descriptive HAC intervals for one 56-day path, with
nominal within-book Bonferroni comparison only. They are neither calibrated
finite-sample guarantees nor family-wide confirmation. Expected-profit confidence,
power, actual margin/execution and graduation remain explicitly unavailable or
false independently of numeric screen results.

This review does not establish semantic truth beyond the declared parent-source
schemas, historical fees/lots, fills, event-calendar exceptions or intraday
liquidation. Actual independently admitted parent bytes will be bound by the
gate; additional observed source consistency remains subject to the final raw
review. The new seven-module grant and nested historical verifier, exact source
dependency pins, complete input bindings, output cap and maximum-size guarded
full financial CLI still need final review. No empirical execution is approved
by this adapter result.
