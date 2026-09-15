# Independent F1 proposal and source-routing review

## Disposition

**The70% proposal and sufficient-cap helper are suitable for further F1
preparation. No F1 source acquisition or financial book is admitted.** The final
indivisible recipe, source inventory, inherited counts, full denominator and
execution contract still need registration and independent review.

Reviewed `lending_math.py` SHA256:
`db25b11c1d2be15cef5e88f16696bd821385523e109b8cc26cc10f12f64de031`.
Eight named invented tests passed independently. An additional1,000 exact
Fraction cases checked the sufficient bound against an independently constructed
pending-interest/treasury amount. Every sufficient case respected the modeled
cap; false bounds remained inconclusive. Qualification flags, reserve-factor
limits and the disabled-cap branch were checked separately.

No empirical fields, prices or financial results were read or calculated. No
network operation, active F2 root/process inspection, code change or commit was
performed. Only this new review file was written.

## Allocation and stress reasoning

The proposed change from100% to70% of initial investable USDC occurs before F1
observations and follows an explicitly authored credit/depeg scenario. It is
coherent preparation rather than an outcome-selected weight. Preserve the earlier
proposal and this algebraic rejection in selection history; no empirical trial
was performed merely by considering the earlier draft.

The draft's leading-order expression is correct:

```
retention = 0.8 * (1 - 0.5*w)
loss = 0.2 + 0.4*w
```

Thus the stated50% loss threshold implies `w <= 0.75` when gas/costs are ignored.
The original full-investable-USDC deposit loses at least60% under this scenario.
For initial gas share `g` losing90%, the corresponding whole-account expression
before costs is:

```
loss = 0.2 + 0.4*w + g*(0.7 - 0.4*w)
w = 0.70  =>  loss = 0.48 + 0.42*g
```

This verifies a margin, not a passing risk result. At70%, even this simplified
margin is exhausted when `g > 1/21`; actual gas debits, liquidation friction and
drift must be evaluated from every funded state. The30% observed drawdown rule
remains distinct from the50% deterministic stress-loss rule. Neither is a
guarantee. No emergency rebalancing should be invented during the lock.

The50% credit haircut is an authored scenario, not an estimated maximum credit
loss or a new user preference. Ordinary credit impairment, depeg and withdrawal
congestion remain market stresses. They must not later be relabeled as exempt
contract exploits to obtain a pass. Native gas and all wallet cash remain part of
capital and stress; complete affected-position tails retain their separate
interpretation.

Under flat USD marks and zero costs, a70% lending sleeve would need approximately
`10% / 70% = 14.2857%` growth on that sleeve merely to produce10% on total capital;
gas funding and costs raise that requirement. This is algebra, not a forecast or
an observation of available rates. It makes endpoint claim growth an informative
prerequisite, but the current draft explicitly waits for its complete necessary
daily panel before financial calculation. A cheaper optimistic endpoint stop
would need to be specified before acquisition, with the unmeasured risk and
feasibility cells retained; it cannot be improvised after seeing a return.

## New sufficient-cap helper

`supply_cap_sufficient_bound` implements the previously reviewed inequality:
convert all current debt's conservative treasury bound to scaled units, add
stored scaled treasury and scaled token supply, convert once at the common next
index, then add the new underlying deposit. Half-up rounding is applied at the
correct places. It does not apply the reserve factor a second time or omit
existing treasury. A reserve factor exceeding100% is rejected and the external
qualification flag must be literally `True`.

For a successful nonzero-cap result, the6-decimal36-bit supply cap is below
`2^56` underlying atoms. Because the supported index is at least RAY, a successful
bound also places the summed scaled units, including the conservative treasury
bound, below that cap. Therefore the successful case fits uint128 treasury
storage; an omitted standalone uint128 test on the upper treasury sum does not
create a false successful case here. Extreme unsupported arithmetic remains
unavailable, not evidence that an actual cap failed.

The disabled-cap branch correctly avoids requiring unknown income/treasury/debt
for this cap-only question. It does not validate operational flags, mint units,
the reserve update, funding or withdrawal. Those checks must still occur in the
financial adapter. Likewise, `debt_bound_qualified=True` is an assertion whose
proof must be pinned, not a substitute for same-block current variable and
stable debt, index/timestamp consistency, source-version semantics and bounded
nonnegative interest. A loose bound above the cap is inconclusive.

## Prospective ownership of suppressed header slots

**A first attempt in F1 can be consistent with the existing contract for an
explicitly suppressed, never-sent F2 header slot, after F2 is terminal and its
source ledger has been independently reconciled. This is not an automatic
transfer of acquisition authority.** The F2 charter's one-owner/no-owned-failed-key
rule must continue to prevent duplicate requests and repair by renaming.

The distinction is between a planned unavailable cell and an actually attempted
request. A suppressed intent with `attempted:false` is not a failed network
attempt. F1's future exact registration may identify such a deterministic header
key as its sole first-acquisition responsibility, while retaining the immutable
F2 planned/suppressed provenance. That registration must state that:

1. F2 has closed; no concurrent owner is still entitled to send the key. Its
   source, charter, terminal result and all planned/suppressed cells stay intact.
2. The exact method/parameters have never been attempted anywhere in the imported
   history. F2's explicit suppression and the intent-before-send code are pinned.
   `attempted:true` without a receipt is uncertain attempted exposure and remains
   excluded. Missing or ambiguous records are not silently treated as unsent.
3. The first header observation is necessary for the already-frozen lending
   recipe, not for completing or recalculating F2. There is one acquisition
   owner, one first request, one charged resource allocation and no fallback.
4. The F1 claim imports F2's full failure/selection history and consumes F1 once
   whether the new prerequisites succeed or fail. Source-family and shared-repair
   budgets remain spent. Newly captured evidence cannot retroactively fill F2's
   output files or support an ungranted F2 rerun.
5. Any inherited endpoint denial, quota/access restriction or unresolved source
   defect is considered separately. A fresh key or family label cannot bypass an
   applicable endpoint stop. This advance review does not assume that any such
   future restriction has ended or authorize a probe to find out.

Actual failed header keys are strictly excluded, including transport failures,
RPC errors and uncertain/unreceipted sends. Their failed cells do not become
available by changing request IDs, encoding aliases or experiment names. This
interpretation covers headers only; it does not authorize recovering failed
oracle values through a changed method/vector or substituting a source.

The current F2 run is untouched, and this prospective rule neither predicts its
outcome nor changes its frozen first-missing-prerequisite stop. If the eventual
F1 packet cannot meet these conditions within the existing phase grant, it is
not admitted by this review. Complete economic/source registration and final
independent review remain necessary before any first request.
