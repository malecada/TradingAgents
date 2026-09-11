# Independent WBETH book engineering and gate review

Disposition: **PASS for one registered conditional development calculation**,
subject to the required committed and remotely verified source freeze. No real
WBETH financial outcome was read or calculated for this review. No network call,
financial claim, source edit or gate edit was performed by the reviewer.

## Material finding resolved before outcomes

The initial gate omitted `carry_book.py` despite the dynamic import in
`wbeth_book.py:8`, which supplies costs, clocks, input validators and funding
arithmetic. Without its hash, those financial dependencies would not be checked
as this target's committed sources. The coordinator added the unchanged file,
SHA-256 `8ad2a08b14653800d7c34a6a391a36fcb43717c7083ec7398f6bdbf8f5a72d55`.
No financial or source code changed. The corrected gate and retained synthetic
CLI source map agree on the dependency. No unresolved material finding remains.

## Cash and hedge conventions

The engine buys WBETH and shorts a distinct ETH perpetual quantity. Its analytical
40% joint-entry formula conservatively includes WBETH principal plus both entry
fees, then floors WBETH and ETH quantities separately. The two actual quantities
are positive, initial spend remains at most 40%, futures reserve is 50% and idle
cash remains at least 10%. The futures short creates no fictitious principal
inflow. All four fees apply to their respective asset quantities and slipped
prices. Terminal cash releases spot sale proceeds and futures reserve plus
signed futures PnL, applies exit costs, and reconciles to signed price PnL plus
funding minus fees. Final trace wallets are flat and reconcile to final cash;
pre-exit marked components remain visible.

The hedge ratio uses only first-open WBETH and ETH spot prices and remains fixed.
It is market-value matching, not a contractual WBETH conversion factor or true
ETH delta. The code and charter preserve that distinction. In particular,
`wbeth_book_run.py:152` leaves the realized net-base-delta ≤1% NAV gate unavailable;
market-value mismatch does not substitute for it. Neither a small measured beta
nor similar currency notionals establish eligibility for that gate.

Funding uses the ETH short quantity, each recorded event mark and signed rate.
All 273 conditional events are validated; the opening-boundary event is excluded,
including a timestamp up to five seconds after entry. The remaining 272 events
are assigned to their actual settlement day. Each zero-funding counterfactual
validates the same source and retains exactly its primary's initial quantities,
prices and fees, while retaining observed cash separately. Its difference from
the primary identifies the removed modeled funding cashflow only, not pure
staking yield. WBETH price PnL can include accrual, basis, demand and depeg effects.

NAV uses WBETH trade close and ETH perpetual mark close plus settled funding.
The mark-high minus all negative daily funding calculation is a lower-bound
scenario for the fixed-quantity, assumed 1% maintenance model; actual liquidation
rules and costs remain unavailable. Half/double common-price and isolated WBETH
depeg illustrations retain fixed quantities and zero funding and make no universal
loss-bound claim. Log arithmetic remains an explicitly invalid cash shadow.

## Independent synthetic verification

The separate `check_wbeth_engine_synthetic.py` builds invented varying prices,
distinct WBETH/ETH quantities and alternating positive/negative funding at varying
event marks. A large funding payment at entry plus five seconds is excluded.
An independent 60-digit Decimal oracle reconstructs quantities, all entry costs,
reserve/idle cash, all primary and zero-funding daily wallets and terminal signed
cash. **3,708 comparisons passed**, with maximum absolute discrepancy
`1.8189894035458565e-12`. All four primary/zero pairs reconcile; no empirical input
was opened. Details are retained in `wbeth-engine-synthetic-review.json`.

The focused engine/runner tests also passed **39 tests in 9.95 seconds** in the
reviewer's run. They include planted relative appreciation, exact common-price
cancellation, lot residuals, constant-price round-trip costs, depeg illustrations,
nonpositive NAV, missing/invalid data, duplicate raw JSON fields, normalized
source tampering, unavailable BTC benchmarks, irrelevant-source failures and
the actual combined 20 MiB output limit before either output is published.
The invented source pipeline uses real HAC calculations and retains all eight
cases when required inputs fail. Missing BTC spot retains cash results and makes
joint exposure unavailable.

## Source, inference, denominator and resources

The runner reconstructs every cell of the two-request WBETH and ten-request carry
parents, checking fixed request specification, identity, raw size/hash, strict
JSON, attempted complete HTTP 200 response, UTC clocks and normalized admission
equality. Required price/funding sources are explicit; optional failures remain
reported. The engine has no network calls and the runner uses saved envelopes.
Current metadata and positive reported trade activity do not establish historical
lot/fee rules, account access or actual fills.

The eight cases are four primary capital/cost combinations plus four paired
zero-funding diagnostics. Joint 91-day OLS exposure uses initial-open benchmark
returns, HAC7 and 97.5% individual intervals; these give within-book Bonferroni
coverage only. The code calls only `carry_statistics.market_exposure`, not its
expected-profit/bootstrap helpers. Singular, nonfinite or nonpositive-NAV exposure
is unavailable. Expected-profit confidence and power remain unavailable for this
single holding episode. Primary cash screens use both cost scenarios at each
capital; zero-funding rows explicitly report their primary pair's screen. No
graduation flag can become true.

The durable CLI preflight reports show eight complete cases, eight complete
exposure calculations, two outputs totaling 963,219 bytes, two CPUs, exit zero,
no limit reason, 4.49239 seconds and 430,174,208 bytes peak sampled aggregate RSS.
The reviewed v2 guard retains the 512 MiB/120-second limits, nominal 20 ms sampling
and process-exit retry qualifications. It does not claim instantaneous hard RSS
enforcement. The actual lifecycle encoding of the two outputs is capped at
20 MiB before publication. Abrupt process failure can retain an incomplete claim,
which remains a spent attempt under the original lifecycle.

## Final gate binding

Reviewed corrected gate SHA-256:
`9e92592a79b88716a15e7d5bba2a1b0e3c3b0891fdc415ee245c3136142c2afa`.
Target `wbeth-book-20260911` has parent `wbeth-inputs-20260911`, exploratory
development reuse and no selection object. All ancestors, datasets and family
objects from `gates-dated-amended.json`, including the consumed dated amendment,
remain identical. The WBETH family has one retained source claim, original
prior_attempts 0 and cap 3; this is its second new administrative question.
No target claim exists at review.

All nine source hashes, six original runtime hashes, four input byte hashes and
the charter hash match current files. All seven actual Python modules named in
the retained full-CLI preflight match the corrected gate. The gate additionally
pins the reviewed guard and `uv.lock`. Cells and the two-output denominator match
the runner exactly. Principal current hashes are:

- Engine: `b5268397ce1e52b4eb8b92845d95a38cd655b11aaac17eaabf54cbff0a624290`.
- Runner: `11ec4c010c9c939840b732d48c3cbd229afe7828900186dfcd05da35373c6a48`.
- Charter: `b9fd243aaeaa14d4feb941d4b1b5b424e325afe1ad4a01a34c2246c265f80fc5`.

No expected return, actual staking attribution, contractual delta, executable
fees/fills, liquidation survival, future tail bound, fresh confirmation or real
financial result was established here. After the committed remote freeze and
single execution, independent reconstruction of actual cash, source timing,
counterfactual differences and exposure remains required. No paper or real orders
are approved by this engineering review.
