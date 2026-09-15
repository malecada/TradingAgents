# Independent lending-math review

## Disposition and scope

**PASS as bounded pure source-model arithmetic, with the scope qualifications
below. This does not admit F1.** Reviewed `lending_math.py` SHA256:
`a4ec8c3fac720e46ef7be78db7c098d644dec76f582befd6df395d6ac7e6e326`.
The six named invented tests passed independently. No empirical lending fields,
prices, account state or financial experiment were opened or calculated. No
network/documentary operation was used and no implementation file was edited.

The reviewed equations describe the declared Aave V3 source model. They are not
proof of the deployed Base implementation, historical upgrades, transaction
success, contract solvency or personal access. The preflight document correctly
leaves the full source and financial contract unfinished.

## Arithmetic and operational checks

- `lending_math.py:13–21`: half-up ray multiplication/division and their checked
  uint256 intermediate bounds are consistent with the stated arithmetic model.
  Independent Fraction calculations covered2,000 invented ray operations and
  both sides of16 exact overflow thresholds, including odd denominators.
- `lending_math.py:23–26`: the declared decimals, active, frozen, paused and
  36-bit cap fields are decoded without adjacent-bit contamination. All16
  deposit/withdrawal combinations of the three operational flags were checked.
  Frozen alone prevents supply but allows withdrawal under this model.
- `lending_math.py:38–45`: treasury is included in scaled units before index
  conversion. A hand-authored case with scaled supply400,000,000, treasury
  100,000,000, index1.2RAY and a1,000,000,000-atom cap permits a400,000,000-atom
  deposit and rejects one atom more. This checks capacity, not profitability.
- `lending_math.py:47–58`:1,000 independently generated uint128 positions and
  indices at least RAY yielded the exact expected half-up underlying balance
  and a complete scaled-unit burn. Mathematically, rounding the underlying
  balance introduces at most half an underlying atom; dividing by an index at
  least one cannot move the reconstructed scaled balance past a half-unit
  boundary. The explicit round-trip check is appropriately fail-closed.
- Withdrawal cash shortage remains unavailable. A sufficient contract balance
  is merely a necessary condition; it is not priority, solvency or future cash
  proof. This helper does not add index growth a second time after redemption.

One conservative domain difference should remain explicit: lines38–39 evaluate
treasury-inclusive total supply even when the configured cap is zero. In the
stated ValidationLogic model the disabled-cap branch can short-circuit that cap
calculation. An invented uncapped scaled supply just above
`floor((MAX_UINT256−RAY/2)/RAY)`, at index RAY, is rejected by the helper's extra
diagnostic multiplication. This is an extra rejection, not a false acceptance
or an observed reserve problem. Either document the narrower supported domain
or separate the optional supply diagnostic from a disabled cap before claiming
exact behavioral equivalence to the complete contract. Such an unsupported
source-model case must not be called an economic failure.

## Minimum treasury/index consistency required by F1

`deposit_preview` cannot establish that its supplied `income` and
`accrued_treasury` belong to the same state transition. A newly normalized index
combined with stale stored treasury may understate capacity use. The preflight's
timing qualification is material, not optional.

For the sole frozen entry, obtain or prove the following at one qualified
canonical pre-action state and one explicitly authored execution timestamp:

1. The asset/decimals, operational flags, cap and deployed source/version needed
   to identify the relevant reserve-update, validation and receipt paths.
2. `S`, scaled aToken total supply, and `T`, stored scaled accrued treasury,
   without omitting or double-counting treasury already minted into supply.
3. `I`, the liquidity index that the hypothetical supply's state update would
   actually pass to validation/mint. A normalized-income view is usable only
   after proving its equivalence at that same timestamp in the selected model.
4. Either the exact pending treasury increment, or a valid conservative bound.
   Exact reconstruction needs the version-specific variable/stable debt accrual
   state, indices/rates and timestamps, reserve factor and all intermediate
   rounding/cast rules used by that update. A storage getter for old `T` alone
   does not reconstruct this increment.
5. All arithmetic/storage bounds, the fixed new deposit amount, funded gas and
   the assumptions that no intervening transaction changes this pre-action
   state. Public snapshots cannot promise actual priority.

Only the entry needs a new-deposit cap check if the recipe has no further
deposits. Acquiring treasury/cap reconstruction for366 dates is not required by
that fixed supply decision. Withdrawal and interim liquidation constraints are
separate and cannot be inferred from entry headroom.

## Conservative headroom proof without exact pending-interest replay

A sufficient conditional bound can be cheaper than reproducing every debt
accrual intermediate. Let `D` upper-bound **all current underlying variable plus
stable debt** at the same timestamp, in the reserve's underlying atoms. Require
the selected source model to have nonnegative accrued interest no greater than
that current debt and a reserve factor between0 and10,000 inclusive. Its
percentage rounding then cannot allocate more than `D` underlying atoms to
treasury. If those conditions are unproved, this bound is unavailable.

With the reviewed monotone half-up ray operations, define:

```
U = ray_div(D, I)
capacity_upper = ray_mul(S + T + U, I) + deposit_atoms
```

If `capacity_upper <= cap_atoms`, and every relevant uint256 operation and
uint128 treasury/index cast is qualified, the cap passes even under this loose
treasury bound. The index conversion is inside the bound: simply adding `D` to
an already rounded supply value without accounting for scaled-unit rounding is
not the proposed proof.1,000 additional invented cases independently confirmed
the monotone percentage/ray inequality. This is a mathematical sufficient
condition under the stated model, not observed headroom.

Current debt can be obtained through appropriately qualified same-block debt
supply views or a provider view whose exact semantics are established. Principal
debt, variable debt alone where stable debt exists, or differently timed debt
figures do not supply the stated bound. A zero component needs evidence. If the
bound exceeds the cap or itself exceeds a storage limit, the result is
**inconclusive**, not proof that actual supply would fail. Do not spend another
repair or tune the bound after financial results. With a genuinely disabled cap,
the cap test itself requires no treasury bound, although reserve updating, mint
semantics and the other entry conditions still require qualification.

## Cheapest informative contract and interpretation

Before any acquisition, F1 can freeze a staged source/financial question that
checks indispensable endpoint index/mark evidence and entry flags/cap first.
For a nonzero cap, the conservative proof above can be an explicitly sufficient
entry test. Missing proof retains capacity as unavailable; it does not justify
substitute providers, repeated owned requests or an extra source repair. F2's
ownership of common headers and all earlier attempted keys remains binding.

An interest-only screen can instead report a conditional grown claim in
underlying units, assuming entry and redemption. That quantity is useful but
does not itself equal dollar cash profit. Dollar P/D requires the fixed entire
wallet, gas/residual balances, USD marks, signed receipt conversion, terminal
route and matched cash control. Without a complete implementation proof it must
remain a conditional screen; lack of capacity evidence is not negative evidence
about the interest mechanism.

A predeclared optimistic endpoint economic bound could stop further measurement
if even that bound fails a necessary financial hurdle, retaining risk and
feasibility as unmeasured. This requires a separate exact F1 contract before
outcomes: no post-outcome choice of which costs, currency convention or metric
to drop. A passing interest/endpoint screen cannot bypass the remaining
source, whole-capital, drawdown, stress, benchmark or confirmation requirements.
No such financial registration or acquisition is approved by this review.
