# Current minimum-lot option entry component

Proposed identity options-entry-20260911, parentoptions-eoh-schema-20260911,
familyoptions-volatility: third/final new options investigation, plus the known
prior RVIV administrative gate/twelve rows. Both earlier source attempts and
unknown broader multiplicity remain. This does not reopen or reinterpret the
historical EOHSummary result and is not a new three-attempt family.

## Distinct prerequisite

Can fixed representative BTC/ETH calls expose current public price/size and
quantity inputs sufficient to calculate the minimum-lot option-entry cash
component, and does that component fit within1,000/10,000USDT under the two
explicit fee scenarios? This resolves a capital prerequisite previously left
unmeasured; quantity-only metadata and unknown old CSV semantics cannot answer
it. It is not a volatility-premium performance test, a recommendation to buy
calls, or affordability of the complete hedged account.

Plausible option risk-premium mechanisms involve convexity demand paying for
risk-bearing. Both performance and seller entry requirements remain separate
questions; a minimum buyer ticket does not establish either. The component
screen can weaken an unsupported blanket small-account exclusion while keeping
hedge collateral, dynamic costs and product access unavailable. No option or
hedge order, account-mode change, model fit or prospective performance session.
Primary sources and current/historical distinction are recorded in
reviews/options-prospective-gap.md and options-prospective-design.md.

## Fixed public acquisition and contract recipe

Use the hash-pinned existing options metadata capture/admission and its original
raw exchange-info receipt, revalidating exact bytes and normalization. No new
metadata refresh or full-chain scan. Preserve old enum ambiguity rather than
silently changing it into historical product permission. Saved fields may be
stale; a failed selected contract is not replaced.

Exactly seven public slots: current options server time; BTCUSDT and ETHUSDT
index; one selected BTC and ETH depth(limit10); one selected BTC and ETH mark.
URLs and bounded transport behavior are frozen in the specification. No
credentials, redirects, proxy, retries, extra requests, hedge quote, paid data
or alternative venue. Same-host denial suppresses remaining requests, retaining
unattempted receipts and all dependent unavailability.

Selection is the sole allowed pre-capture-completion numerical operation.
Require admitted server time consistent with its local request/retrieval clocks;
no local-clock substitute for an unavailable server response. Use independently
admitted positive corresponding index as the strike reference. Select literal
CALL symbols with matching BTCUSDT/ETHUSDT underlying, USDT quote, positive unit,
and a unique optionContracts parent with matching underlying/baseAsset and
USDT quoteAsset/settleAsset. Settlement is a parent field; do not require a
nonexistent leaf settleAsset or infer parent nakedSell as user permission.
Require consistent minQty/maxQty/LOT_SIZE min/step and symbol/expiry/strike identity.
Explicit non-TRADING status, if supplied, excludes a candidate. Absent status
is recorded as unverified; public quote selection never implies tradability.
No inferred numeric underlyingType/contractType enum overrides the old ambiguity.

Within expiries7–45days after the server reference, inclusive, choose closest
to30days, earlier expiry as tie. At that expiry choose strike closest to index,
then lower strike, then lexical symbol. Retain the full eligible identifier/count
and tie evidence; do not select by premium, Greeks, spread or apparent fit.
Missing time/index/metadata leaves the fixed dependent slots unavailable. Do
not substitute another strike after a failed depth/mark response.

Persist raw response receipts before parsing. Only time/index/metadata needed
for deterministic request construction may be interpreted during capture.
All quote/Greek/premium/fee/size/capital interpretation waits until capture
closes. Preserve exact source identity, server/transaction/request/retrieval
clocks and hashes. Separate REST responses are asynchronous; no quote-age or
fill proof follows from a timestamp label.

## Entry accounting and fixed cases

Require strict JSON, complete HTTP bodies, matching requested symbols, ordered
noncrossed bid/ask rows with finite positive prices and nonnegative quantities.
Depth rows are preserved; only best ask prices the minimum buyer quantity.
The saved minQty must be an exact valid LOT_SIZE step and fit both bounds.
A displayed ask smaller than minQty fails visible-size sufficiency; do not
optimize through deeper levels or shrink the lot. Missing best ask makes the
entry component unavailable. Mark/Greeks are model values, never substitutes
for the executable side. Missing mark does not erase a valid buyer component.

For minimum option quantity q, best ask A, captured index S and unit U, premium
outlay is A*q. The fee illustration is min(r*S*U,0.10*A)*q; do not multiply
premium by U again. Two frozen r values:0.00024 (general FAQ illustration) and
0.00030 (previously documented unresolved fee-table alternative). Neither is
asserted to be the user's rate, and neither is chosen after results. Entry
component=premium+that transaction fee. No exit/exercise/hedge fee is omitted
from a return claim because no return or completed trade is being claimed.

Eight component cases: two assets × capital1,000/10,000 × both fee scenarios.
All seven source cells and eight component cells are retained. Component
calculability and necessary conditions (entrycomponent≤capital; bestasksize≥q)
are separate; source/structural completion is not a strategy passing verdict.
A comparison that fits concerns this option-entry component only. Full hedged-
account affordability, short-sale opening margin, actual commissions, account
mode/access, true delta, liquidity/impact and clearing applicability remain
unavailable. Do not apply a position-margin FAQ formula as sell-to-open cash
requirements or assume cross-wallet netting.

Expected profit, confidence intervals, power, beta, annual relevance, liquidation
risk and graduation are unavailable. No source/price snapshot can establish
an option volatility strategy's expected net performance. Apparent fits name
further access/hedge/time-path dependencies; failures concern these selected
representatives/scenarios only, not every contract or future date.

## Limits, proof and next decision

One foreground registered attempt, seven source slots, two CPUs,512MiB sampled
aggregate RSS,180seconds cooperative capture and240seconds overall hard wall.
Each request has a20second whole-request deadline and256KiB raw-body cap, with
one overflow byte permitted solely to detect truncation; retain only the bounded
prefix and mark incomplete. Preserve every timeout/denial/partial body.
Ten immutable JSON outputs: seven raw receipts plus capture.json, entry.json
and summary.json, capped at12MiB combined actual lifecycle encoding. The capture
aggregate stores normalized source/selection evidence and receipt references,
not another copy of every raw body. Bound normalized projections before write.
Use a narrowly reviewed bounded transport equivalent; no monkeypatch of frozen
old transport constants and no unregistered read of larger source bodies.

Synthetic validation must cover deterministic expiry/strike/ties, stale/absent
metadata status, symbol mismatch, lot/step conflicts, nonfinite/duplicate JSON,
missing index/time dependencies, asynchronous clocks, raw-before-parse order,
no premium-selected contract, fee unit/cap arithmetic, insufficient size and
all source/component denominators. An exact guarded lifecycle at worst admitted
payload must pass before independent implementation/source/gate review and
commit/push/remote-equality freeze.

After the sole real capture, independently reconstruct selection, source and
cash-component arithmetic, verify receipt/resources, retain all cells, diagnose,
update findings/map/state and back up the branch. No uncounted follow-up book or
automatic prospective collection follows. Review all map dispositions and
remaining affordable gaps; stopping requires the launch prompt's substantive
criteria, not exhausted administrative slots alone. Zero validated strategies.
