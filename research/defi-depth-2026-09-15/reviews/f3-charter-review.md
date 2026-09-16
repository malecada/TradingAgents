# Independent prospective F3 charter review

## Disposition and scope

The prospective recipe is coherent with the reviewed LP book. Correct the three
prose statements below before freezing the contract. No source builder/context
or exact empirical F3 gate was presented, so this review does not admit acquisition
or financial execution. Only this review file was written. No active F2 root,
empirical prices or source outcomes, financial experiment or network was accessed.

## Required contract clarifications

1. **Comparison denominator — initial `f3-charter.md:95`.** The charter describes
   39 primary-cost contrasts, 13 per cohort. `protocol_financial_results.py:37`
   and `:177` instead specify13 controls for the latest2026 cohort in each of
   three cost scenarios. Only the primary scenario decides. The36 book cells
   already retain all three cohorts, with older cohorts unavailable. Correct the
   prose to13 latest-cohort comparisons times three scenarios; preserve the
   existing79 cells and73 outputs. This is a description correction, not new
   trials or an alternate decision rule.

2. **Proof for new versus transferred source keys — initial charter:127.** A
   requirement for a prior suppression proof on every unattempted field would
   exclude genuinely new LP getters never owned by F1. Require exact terminal
   suppression proof for transferred shared header/price/USDC-witness slots;
   require complete terminal exclusion-union and semantic novelty proof for new
   LP-only getters. Actual or uncertain failed keys remain excluded in either
   case. Neither qualification grants a retry of F1/F2/R1 observations.

3. **Matched-control survival — initial charter:40.** The routing preserves the
   matched control when qualified mint-capacity observations show insufficient
   candidate headroom. Missing common LP panel or boundary-source evidence
   prevents `build_candidate_panel` and makes both candidate and matched-control
   books unavailable. Narrow the prose accordingly; do not claim that all missing
   capacity inputs preserve an independently computable matched control.

## Accounting and decision alignment

The fixed latest calendar is September1,2025 through September1,2026, with funded
entry September2. Half of initial investable USDC after the native gas reserve is
used for the largest integer liquidity fitting the sleeve budget. The binary
search solves a funding constraint and does not select on return. The remaining
cash, rounding residuals and0.005 native ETH reserve stay inside the$10000 account.
The matched control holds the exact acquired WETH atoms and corresponding USDC;
there is no fee-only profit or duplicate inventory-loss deduction.

Primary/doubled/frictionless costs match the existing model: gas0.0001/0.0002/0
ETH per modeled operation, sale/purchase fee0.3%/0.6%/0, adverse10bp/20bp/0 and
terminal USD route$10/$20/$10. Candidate transaction count10 and matched count5
match the event plan. Native gas is prefunded and its final sale funds its own
last gas. WETH/native identities are distinct and their valuation parity is
explicitly assumed. Integer burn principal and accumulated fee atoms are checked
before redemption; attributed fees enter the ledger once. Literal partial
receipts remain authoritative if later observations fail.

The authored ETH−50/80/90%, USDC−20%/30-day lock, ETH−50%/7-day outage/fivefold
adverse execution and combined ETH−90%/USDC−20%/30-day/fivefold scenarios match
the book. LP quantities follow the explicitly assumed operating arbitraged price
path while previously accrued fees remain held assets. The double-then−60% path
peak drawdown is separately reported. Wallet and pool-position total losses remain
separate catastrophic tails; delayed liquidation marks are not day365 usable cash.
The risk filter uses observed discrete drawdown<=30% and authored ordinary stress
loss<=50%; peak-path diagnostic is not silently substituted for either.

The fixed$1000 absolute and$200 incremental cash thresholds, primary scenario,
all13 controls, absolute-versus-relative reporting, B1 unavailability and absent
confirmation align with result routing. Known-comparator numerical success is
not implementation/adoption. Legacy CEX and new wallet valuation/route differences
remain disclosed by the comparison output. Older unavailable cohorts are retained
and do not become new historical attempts.

## Source, ancestry and unresolved qualification

The source inventory matches the proposed daily four fields and13 boundary
witnesses. The full-range spacing60 bounds yield29,575 usable ticks. An independent
local Ethereum-Keccak calculation gives `70cf754a` for
`maxLiquidityPerTick()`, and integer division gives
11505743598341114571880798222544994. No external documentation was opened.

A seven-predecessor imported source history and narrow prior7/cap8 LP family are
consistent only after F1 is terminal and its full actual/uncertain/suppressed
history is reconciled. All cumulative phase, financial, request and byte limits
still apply; no shared repair or documentary allowance is restored. Shared
observations must be raw-reparsed and hash-bound, including scalar/vector overlap;
new LP fields must be checked against the complete prior union before any send.
No F3 context/builder currently proves those facts for an actual run.

Boundary code equality and exact getter identities do not prove historical
implementation semantics. The historical global-fee path requires the stated
standard-v3 semantics and remains a price-taking attribution model: no finite
capital dilution, altered swaps/flash flows, or intraday capacity guarantee is
established. A future gate must preserve that conditional meaning rather than
claim deployed execution merely from a `source_model_qualified` boolean. Real
funding/exit routes, usable cash during locks, account eligibility and independent
confirmation remain unproved.

## Verification

Twenty-three named invented tests passed across protocol source collection,
financial result routing and LP accounting. This includes the new full366-day
LP source fixture:1,490 actual invented requests (366*4+2*13), all declared
outputs/cells retained, signed slot tick decoding and exact uint128 boundary
limit decoding. No financial book was rerun with empirical data. This bounded
review did not independently re-prove the previously reviewed general LP-fee
identity or audit a deployed contract version.

Initial reviewed SHA256 values:

- `f3-charter.md`: `bf3580a3af4ef6d495bf207d2558776976fdecf2949e0293353602bb87f745de`
- `lp_book.py`: `0f23c34aad58f9989730c80c7616c1f14cd71870354846b7c16f6511a2680420`
- `protocol_financial_results.py`: `f94f05e13a278f8e3b7eefeb7d372de63708eaf0f804dac7ce8d608f3e37589b`
- `protocol_financial_source.py`: `c2210a54981f958832db384168cb4b92188e56967bbc30ee19b0f02504e393b9`

## Prose correction disposition

**PASS for the prospective charter scope.** All three clarification requests
were applied without code, recipe or denominator changes and independently
re-read. The charter now states39 latest-cohort comparisons across three cost
scenarios, distinguishes transferred suppression proofs from new LP-only key
exclusion checks, and limits matched-control survival to qualified insufficient
headroom. The initial findings above remain as review history.

Corrected charter SHA256: `bf3580a3af4ef6d495bf207d2558776976fdecf2949e0293353602bb87f745de`. Exact terminal ownership, source context,
request/byte reservation, committed gate and empirical admission remain pending.
