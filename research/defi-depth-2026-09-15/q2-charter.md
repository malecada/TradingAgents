# Q2 — fixed Base daily protocol-state history

This source question follows independently reviewed Q1 availability, not measured
returns. Q1 supports one old Base state; continuity is untested. Ethereum and
Arbitrum history at their frozen endpoints remains unavailable. No provider
substitution, return comparison or event replay is admitted in this question.

## Inheritance and exact cohorts

Q2 is the second and last new claim in the unchanged protocol-state-source
family: imported prior1 + Q1 + Q2 = cap3. Both new claims consume successor source
slots, not financial recipes. The imported predecessor already overlaps old188.
The old allocation objects, old44 related DeFi records, full ancestry crosswalks
and source/financial results remain preserved. New source observations are
exposed development, never untouched confirmation.

The chronological panel is 1,096 UTC daily targets, September2,2023 through
September1,2026 inclusive. Three fixed365-day cohorts end September1 in2024,
2025 and2026. The first begins September2,2023 because the interval contains
February29. All cohorts remain, including pre-deployment and missing periods.
The source choice and dates are not conditioned on a yield, fee or price ratio.
No profit, accrued return, allocation, strategy ranking or annualization occurs.

## Canonical clocks and complete request inventory

Use only https://mainnet.base.org and expected chain8453. One chain-identity RPC
subcall precedes the daily matrix. The retained Base20,000,000 anchor and its
1726789347 timestamp give a candidate height by floor division at two seconds.
This is a candidate mapping, not an assumed historical clock. Every daily target
requests that header and the next height. Both exact numbers and valid clocks
must return, the second must reference the first hash, timestamps must differ by
two seconds, and left.timestamp <= target < right.timestamp. State uses the LEFT
(last block at or before target) canonical blockHash with requireCanonical=true.
No interpolation, forward block, adaptive height search or latest fallback.
Failure retains the date and all dependent unavailable fields.

Fifteen daily state subcalls: Aave native-USDC normalized income, raw configuration,
public aToken USDC cash, scaled supply and total supply; the inherited Uniswapv3
WETH/native-USDC0.3% pool's slot0, active liquidity, both global fee counters and
both fixed boundary ticks; AaveOracle USDC and WETH asset prices; EIP1967 Pool
and aToken implementation addresses. Four cohort boundaries add fourteen fields:
nine original token/pool identities, oracle base/unit, two source addresses and
oracle bytecode. Exact addresses, signatures, ABI and dates are in q2-spec.json.

The boundary oracle is the retained official Base address-book candidate.
The expected zero-address USD base and1e8unit must be verified, not inferred from
an integer price. Oracle source or implementation addresses must be nonzero;
absent deployments are unavailable. Current official code documents the EIP1967
slot, but a storage word does not prove deployed behavior. The daily witnesses
identify further version-review needs; boundary oracle bytecode/source checks
cannot establish full historical source continuity, staleness or uncapped prices.
Those uncertainties remain explicit prerequisites for any financial use.

Headers retain L2 base fees as source fields. They do not measure total transaction
gas, L1 data fees, user fees, price impact, slippage, minimum trade sizes, funding,
transfer/withdrawal delays or terminal liquidations. Oracle levels are protocol
valuation proxies, never executable USD bids. Public reserve cash is not a
permission or guarantee to withdraw. Raw configuration is not decoded with an
unverified modern layout. No missing field becomes zero or an unchanged price.

## Strict batching, availability and resource reservation

There are at most2,193 actual HTTP requests and18,689 logical RPC subcalls.
Every transmitted batch member consumes the latter reservation. The conservative
phase acquisition budget is charged by RPC subcalls, not the cheaper HTTP count.
The chain request is a one-member batch. Each day has one two-header batch and
one fifteen-member state batch (twenty-nine at the four boundaries). Max32members,
32KiB request body,256KiB received body,10-second individual HTTP wall deadline.
No aggregate elapsed-time or CPU-duration kill. Single synchronous owner.

Each batch has one attempt. No individual-call retry, batch-format fallback,
provider change or denial workaround is admitted. Strict JSON disallows duplicate
keys. Response IDs are mapped independently of response order; extra, duplicate
or invalid IDs invalidate the batch. Missing expected members remain individually
unavailable. RPC error/null fields remain unavailable even with HTTP200.
HTTP403/418/429/451 stops remaining endpoint requests while publishing all pending
unavailable cells. A transport/body failure affects that batch; no automatic retry.

Worst-case raw reservation is2,193*262,144 =574,881,792bytes. Raw bytes are counted
once per HTTP response, not once per alias or decoded field. Added to Q1's129
actual subcalls/100,951rawbytes this stays within25,000subcalls/2GiB. The remaining
source questions have at least6,182subcalls and the unused bytes; documentary
usage at registration is35/60. No time budget is substituted for these limits.

Every HTTP intent is published before transport and every raw-byte receipt before
parsing or proceeding. A day's decoded vector is then published. This gives
three chain outputs, five outputs per day and a summary =5,484outputs. The raw
receipts include all payloads and exact received bytes, UTC, status, errors,
completeness and hashes. Dependent unattempted batches retain explicit reasons.
A process/storage failure preserves published evidence and consumes this claim;
it must not be silently restarted. A long valid run remains in progress.

## Source checks, denominators and financial boundaries

Each day has two header cells, one bracket cell, fifteen state cells and one
Aave supply identity cell. Four boundaries add fourteen cells each. With the
chain cell and nine cohort cells, total20,890cells. Scaled supply times observed
normalized income is reconciled with total supply using Q1's one-base-unit
rounding tolerance. This is an observational identity, not the eventual user's
mint/burn rounding rule. LP slot0 receives the frozen basic initialization checks;
full tick/fee accounting and counterfactual liquidity dilution are not proved.

For each cohort, lending and LP source coverage require all fixed daily fields
listed in the spec. A complete source-coverage cell establishes those fields
only. It does not promote an investment or certify all versions/identities.
Every cohort's executable-route cell is unavailable unless another separately
admitted contract establishes the missing route; Q2 itself cannot mark it complete.
Missing dates are reported explicitly, without dropping a cohort or filling gaps.

Before capture: focused invented fixtures test ID permutation, missing/extra/
duplicate/envelope errors, wrong chain/headers/adjacency, absent deployment,
noncanonical values, byte constraints, and preserved unavailable denominators.
Independent design/code review and committed registration precede actual requests.
After capture: structural verification and independent raw reconstruction review
coverage, ABI, chronology, costs/valuation limits and all unavailable cases.

F1 lending and F3 static LP remain unregistered financial reservations. Their
cash books must separately freeze entry/exit and full-capital costs, applicable
versions, losses, benchmark comparisons, stress/decision rules, cumulative
contrast count and independent accounting checks. An informative conditional
negative may be possible; implementation and confirmation still require their
own evidence. Q3–Q6 continue independently under the existing finite grant.
