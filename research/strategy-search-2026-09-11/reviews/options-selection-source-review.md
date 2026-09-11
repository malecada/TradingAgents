# Options policy selector source review — 2026-09-11

Scope: source and invented fixtures only. No actual metadata, index, premium,
Greek, or other observed market payload was opened. No network request occurred.
This is not financial admission or independent accounting approval. Only this
review file was written; implementation and gate ownership remain elsewhere.

Reviewed source `options_policy_selection.py` SHA-256
`dbfc1ff9703c9b799c5fe5e6e26f46354000b40f927ab1de437bda89feca7e98`;
test source `tests/research/test_options_policy_selection.py` SHA-256
`a9a4b81f804aa45113df7c45fc1cbba9fe73f1a4f0cdd3d753daa221282b0ad8`.
The exact named synthetic target passed **9 tests**. That result does not resolve
the following contract issue because an existing expectation encodes it.

## Finding requiring resolution before freeze

The common-quantity calculation intersects zero-anchored step multiples without
establishing the applicable LOT_SIZE anchor. The invented test with call minimum
0.03/step 0.02 and put minimum 0.04/step 0.03 returns 0.06. Under an offset rule
`(quantity - minQty) % stepSize == 0`, its lot counts are respectively 3/2 and
2/3, both invalid. Quantity 0.07 gives integer counts 2 and 1. These exact
Fraction checks were independently executed without the selector or real inputs.

The earlier source interpretation of Options filters uses the offset rule, but
the retained review Markdown inspected in this bounded task does not reproduce
that precise official sentence. Consequently the claim that every completed
selection obeys venue lot rules needs either exact source reconciliation or a
conservative implementation restriction. Rejecting a chosen pair whenever either
minimum is not an integral step makes zero- and minimum-anchored quantity grids
coincide; it is a supported-scope restriction, not a claim that the venue rejects
all offset lots. Alternatively implement the documented rational congruences.
Do not choose a different contract after this chosen-pair failure. Preserve the
original failing fixture and its correction history.

## Other policy and scope observations

- Expiry selection is nearest to entry plus 30 days among eligible shared
  call/put candidates in the inclusive 7–45 day band, with earlier expiry on a
  tie. Strike selection then minimizes absolute distance from the supplied index,
  taking the lower strike on a tie. No premium field is read; the synthetic
  premium perturbation leaves the result unchanged.
- Literal symbol/date/strike/side binding and unique underlying parent with
  base/quote/settlement checks are present. Expiry hour alignment is an explicit
  policy restriction. Missing status remains `unverified`; status, if supplied,
  must be `TRADING`. Neither route establishes account access.
- Unit, lot, and tick validation occurs after the selected identities are
  retained. A failure leaves those identities unavailable without selecting a
  farther date or strike. Different call/put ticks are explicitly unsupported by
  the current common-tick engine; this is not evidence against the contracts.
- Identity-invalid and duplicate-symbol rows are removed before candidate
  ranking. Thus a farther eligible identity can be selected after identity
  exclusion, while a selected rule failure cannot fall back. Freeze this
  distinction explicitly. `excluded_counts` only counts qualifying-underlying
  CALL/PUT rows that enter the identity checks, not every metadata row or every
  incomplete group; it is not a full metadata inventory denominator.
- Only the PRICE_FILTER tick is projected. Price minima, maxima and any
  price-grid anchor remain outside this selector. Downstream proposed order
  prices require separate applicable filter admission or a declared unsupported
  status. Tick equality alone does not establish complete order-rule compliance.
- Raw-source identity, completeness, availability time, retrieval clock and
  metadata freshness are explicitly caller responsibilities. A literal pure
  selection result cannot certify that entry rules were available at entry or
  valid throughout a prospective holding interval.

Disposition: **resolution required**, limited to the grid contract above. The
fixed date/strike ranking and no-premium/no-selected-rule-fallback behavior are
consistent with the proposed prospective policy. No economic edge, full order
eligibility, or live-source admission follows from this review.

## Resolution and independent recheck — 2026-09-11

The coordinator retrieved two primary URLs with zero search queries. The legacy
`https://developers.binance.com/docs/derivatives/option/common-definition`
redirected to the USD-M futures product (reported modification September 8), so
it is not authoritative for Options filters. The exact
[Options common definition](https://developers.binance.com/en/docs/products/derivatives-trading-options/common-definition)
(reported modification September 10, retrieved September 11) confirms the
minimum-anchored quantity rule and the price-offset rule. This paragraph records
the coordinator's source adjudication; this reviewer made **zero** additional
web requests. The original uncertainty and finding above remain as history.

Corrected source SHA-256:
`54f09c9c9ed28955bca5a9b74b49c08ee2a83fd6c880e3fdbfb6b5cd2ff6208e`.
Corrected test SHA-256:
`3e05973a2ec4e1c68a62ec0ca5e39990b7cdc88cce5a43a01b4370bc5f459333`.
The named synthetic target now passes **11 tests**. The implementation solves
the rational minimum-anchored congruences on a common integer scale, rejects
incompatible grids and respects the smaller maximum. The corrected offset
fixture selects 0.07; incompatible grids retain the selected identities and
return unavailable. Price-filter compliance is now explicitly unavailable in
the completed selection projection, pending execution-specific admission.

An independent bounded enumeration checked **2,592 invented cases**: both minima
and both steps each range from 1 through 6 in units of 1/100 and then 1/1000;
the quantity cap is 25 such units. An ascending integer scan from the larger
minimum to the cap, checking both modulo equations directly, supplies the
expected answer without calling the implementation's congruence arithmetic.
All **2,000 complete** and **592 unavailable** results agree, with zero
mismatches; each case retains the same chosen strike. Only invented fixtures and
the pure selector were loaded. No observed metadata or economic calculation was
used. The verifier was executed inline, without modifying implementation/tests.

Current disposition: **PASS for bounded selector scope**, resolving the original
lot-grid blocker. Raw metadata admission, clocks, actual execution price filters,
account access and economic validation remain separate. The identity-exclusion
versus selected-rule-failure distinction above should remain explicit in the
prospective policy.
