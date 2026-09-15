# Options episode integration review — September 15, 2026

Status: pre-freeze integration requirements; implementation review pending. The
September 15 instruction resumes the research. No source request, financial
experiment, registration change or historical ledger write was performed for
this review. The earlier nineteen terminal investigations and four frozen
runtimes remain outside the mutation scope.

The actual accepted engine, batch assembler and selector were read independently
alongside the checkpoint, protocol draft, admission decision and prospective
funding/rule memorandum. Research-governance and market-data-provenance skills
were applied. The engine's earlier independent arithmetic proofs were inspected
for scope, not taken as proof of complete source or execution admission.

## Material requirements before freeze

1. **Freeze numeric costs and the scope of price assumptions.**
   `options-episode-protocol-draft.md:15` names base/stress without numeric costs.
   `options_policy_engine.py:130` charges each option leg
   `q * min(option_fee_rate * index, execution_price / 10)` and applies one
   absolute adverse option-price increment. The final contract must specify
   exact base/stress fee and perpetual slippage values, and translate the stress
   increment from the selected tick. Existing invented examples are not an
   account fee schedule. Entry and exit option prices must satisfy their frozen
   side-specific min/max/tick-offset rules; costs cannot be selected after data.

2. **Bind perpetual execution admissibility rather than overstating the engine.**
   `options_policy_engine.py:141` checks min quantity, modeled execution notional
   and first-level size; it has no max quantity, minimum-offset grid, dynamic
   rule-vintage or market-order filter input. A source-only adapter cannot test
   the eventual order change without prior inventory. Either a reviewed frozen
   execution check is needed or the admitted instrument subset must make the
   invariant provable. For example, require a minimum divisible by the step and
   bound all possible changes by `2 * nearest_lot(q, step)` (not `2*q`, because
   rounding can increase the hedge). Full market-order admissibility additionally
   needs relevant market-lot/notional semantics; quote-side conditional fills
   must remain explicitly qualified where those are unavailable. New rules
   cannot be used retrospectively to legalize old decisions. A further distinction
   is needed for perpetual slippage: `100.1 * 1.0002 = 100.12002` is off a 0.1
   price grid. Exact tick checks on the effective slippage price would disable
   ordinary decisions. Either freeze quote-price compliance with the extra
   slippage explicitly treated as an effective economic cost, or use a separately
   reviewed tick-rounded execution implementation. An adapter must not round
   prices while claiming an unchanged engine executes those rounded prices.

3. **Preserve funding expectation evidence separately from batch valuation.**
   `options_policy_batch.py:94` intentionally discards premiumIndex funding
   fields. The semantic adapter must parse the retained original response to
   preserve nextFundingTime, its observation clocks and source hash. The ledger
   at `options_policy_engine.py:104` trusts the caller's expected calendar;
   passing an empty calendar after missing source observations could falsely
   produce cash-complete status. Reconcile all announced due timestamps and all
   returned event identities, preserving unexplained events, conflicting
   versions and missing expectations. Absence of an announced event is not
   evidence of zero funding. A separate typed economic-coverage result must
   invalidate complete cash when the source calendar remains ambiguous.

4. **Specify funding time domain and boundary ownership.**
   `options_policy_engine.py:163` compares funding times with local modeled action
   clocks directly. Provider fundingTime and controller wall time are distinct
   clocks. Freeze a justified mapping/uncertainty rule or explicitly declare a
   conditional raw-time alignment assumption. An event-time interval that
   crosses an inventory-changing action makes ownership ambiguous. Final
   history supplies publication evidence but cannot independently calibrate an
   earlier provider clock. Do not backdate first local history availability or
   shift cash membership merely to fit hourly labels.

5. **Preserve per-asset deterministic closure and rule vintages.**
   `options-episode-protocol-draft.md:62` fixes each exit at expiry minus 24 hours.
   Pass the complete hourly sequence ending at that asset's selected exit to the
   ledger, including missing placeholders. The longer shared source calendar
   and post-exit slots remain retained but cannot become extra hedge decisions.
   Initial/daily rules apply only after their actual receipt time and within the
   frozen age tolerance. A relevant change or stale rules disables subsequent
   dependent decisions while preserving inventory and source collection;
   terminal missing-rule/quote evidence leaves cash unavailable. A later return
   to old rules must not silently clear a frozen permanent-stop policy.

6. **Keep economic and risk claims within measured scope.**
   `options_policy_engine.py:248` explicitly does not establish actual margin,
   intrahour risk, beta or expected returns. The final eight-case report must
   retain full capital and 40/50/10 wallets, annualized-simple relevance and
   0/3/5-percent cash benchmarks, all missing NAV slots and unavailable cells.
   BTC/ETH capital alternatives reuse observations and are not eight independent
   samples or a jointly funded portfolio. Provider model delta/residual is not
   measured true beta. A positive terminal cash result with incomplete path
   marks cannot establish drawdown, wallet safety or low exposure. The program's
   advancement screens stay unavailable unless separately implemented with a
   frozen dependence/multiplicity treatment; one episode cannot establish an
   expected-return edge.

## Claims not tested

No empirical strategy result, provider payload, endpoint reachability, account
eligibility, actual commissions, realized fills, historical effective rules,
actual margin, intrahour losses or expected return was tested. No current market
request or web query was made. The new schedule, worker, independent return
verifier, source adapter, final registration, package, VPS behavior and complete
resource envelope await concrete source review. This report is not capture or
financial admission, and does not authorize an allowance or execution.

## Concrete implementation findings (initial September 15 revision)

- **Blocking: prefixed source keys prevent every real selection.**
  `tradingagents/research_options_capture/worker.py:177` supplies keys such as
  `h0000-options-time` to `select_initial`, while
  `tradingagents/research_options_capture/adapter.py:105` requires exactly the
  unprefixed eight role names. Both assets therefore become unavailable after
  the initial eleven requests. The synthetic worker tests replace `choose` and
  miss this integration. The restart path at worker line 128 has the same
  mismatch. Preserve prefixed raw hash bindings while passing the exact frozen
  unprefixed view to the selector; test with the actual adapter.

- **Blocking: an assignment can authorize duplicate workers in different roots.**
  `tradingagents/research_options_capture/worker.py:106` accepts an arbitrary data
  directory and line 116 locks only that directory. Its assignment schema at
  line 53 binds neither the data root nor host identity. Two invocations using
  one expected assignment hash but different data paths can each issue the
  same source slots. Bind the dedicated canonical data path and host, reject
  mismatched launch arguments before acquisition, and prove duplicate locking.

- **Material source identity omission in rule vintages.**
  `tradingagents/research_options_capture/adapter.py:155` checks a selected symbol,
  unit and some row status fields but does not preserve expiryDate, strikePrice,
  side, parent settlement identity or the status-presence distinction in its
  rule signature. A same-symbol metadata identity change can therefore leave
  the signature unchanged and permit later decisions/valuation. Bind these
  relevant identities to the initial selection and latch inconsistent vintages.

The review also identified two release-boundary requirements: exact package
inventory must be verified before Python imports any unpinned `__init__.py`, and
the supervisor's kill/exit reason must survive in a bounded durable report/log.
The reviewed worker revision discards child stderr and has no durable supervisor
result of its own. An outer reviewed launcher may satisfy these requirements;
no broader hostile-host confinement is requested.

The controller and independent protocol verifier were read through their
prospective-window, nineteen-history, immutable analysis-intent, output-cap and
external-quiescence checks. No additional material defect was established in
that reading. Their external source/quiescence reviews remain trusted inputs;
neither proves returned raw-source semantics or actual remote process death by
itself. A transient apparent output-name regex concern was directly probed with
the pinned interpreter: ordinary `books.json` was accepted and a backslash name
was refused. It is not a finding.

### Corrected adapter review

The rule-identity finding is resolved in the subsequent adapter revision:
selected expiry, strike, side, top-level lot consistency, parent settlement and
status presence/value are now bound. Five independent invented same-symbol or
parent mutations latch unavailable; an unrelated extra symbol does not. An
independent rational grid check covered 1,000 quantity/step combinations and
confirmed `2 * nearest_lot(q, step) <= 2*q + step`, the conservative max-change
bound used by this supported subset. Total independent checks: 1,006, all pass;
zero market requests. These are synthetic rule/accounting checks only.

The effective perpetual slippage cost is now explicitly distinct from the
literal quote price, whose tick/min/max compliance is checked. Both option price
bounds are conservatively required, a documented stricter subset of the prior
side-specific source rule. This can reject otherwise legal venue prices and is
not a false execution-admission claim. No new material defect was established
in the corrected initial-selection and rule-vintage functions. Funding and
outer episode normalization remain outside this partial acceptance.

Reviewed adapter SHA256:
`f8583d1cbaccf437f5efbfbdd1e70b79d39543eedf5d1dc8617765dc55df78a7`.

### Initial analysis and release review

`analysis.py:40` initially divided modeled net/gross exposure by initial capital,
although the program's residual screen is per NAV. At NAV 500, residual notional
8 and initial capital 1,000, those ratios are 1.6% and 0.8%, respectively. The
ratio name and screen denominator must match. The initial implementation also
read retained index/delta values without independently checking their source
availability, allowing stale values to produce a complete exposure maximum.
Both findings were sent to the coordinator before freeze. Missing or invalid
held-state inputs must make the associated exposure metric unavailable.

A linked source-policy issue is that suppressing each asset's index immediately
after its own exit leaves the longer-lived other asset's counterpart beta
benchmark incomplete. The existing reserved index slots can continue through
the later selected exit, or the corresponding longer-book beta must be declared
unavailable by design. No replacement observation or additional slot is needed.

The marginal OLS/Newey-West implementation was independently reconstructed with
full two-column design matrices and covariance sandwiches, rather than its
centered scalar formula. Twelve invented noisy paths of 72, 145, 697 and 1,056
observations produced 24 matching slope/standard-error comparisons, maximum
standard-error difference below 4.17e-17. The Bonferroni-two normal multiplier is
correct for its stated nominal simultaneous interval convention. This numerical
proof does not validate normal asymptotics for a single dependent episode or
provide expected-profit inference.

The standalone bootstrap was independently tested with five invented package
states: complete inventory accepted; unlisted `__init__.py`, symlink member,
wrong data root and wrong external assignment hash rejected. No package code
was imported for these probes. This resolves the reviewed pre-import inventory
requirement within its cooperative-filesystem scope; actual isolated runtime
identity and deployed bytes remain separate proof obligations.

### Funding normalization review in progress

The initial funding adapter checked `nextFundingTime > provider time`, which
alone did not prove observation before the announced due time. An invented
provider timestamp 250 ms into a slot, due timestamp 260 ms into the same slot,
and controller receipt at 300 ms demonstrates the gap. The owner has added a
check against the contemporaneous venue-time upper bound at actual receipt,
without extrapolating a calibration to a long-horizon future event. Its targeted
regression is pending review. Union of announcements and published identities,
retention of conflicting versions, two final partitions and conditional
ownership intervals were read; calendar completeness remains explicitly
conditional on hourly observations and the declared clock-drift premise.

### Corrected analysis and funding

The exposure findings are resolved in analysis SHA256
`af84494179d7cfdd0fae940ed9e786d86054e9869054ea764b0d98c1dabc3417`.
The exact NAV-500/residual-8/capital-1,000 counterexample now reports both 0.008
initial-capital and 0.016 NAV fractions; a stale index makes the NAV maximum
unavailable. Three direct independent checks pass. True-delta and option
repricing/liquidation/margin stress screens explicitly remain unavailable.

The locally stale funding-announcement finding is resolved by comparison with
the contemporaneous venue-time upper bound at controller receipt. Long-horizon
next-event timestamps are not forced through a nonexistent future calibration.
The funding owner additionally verified the primary documentation's literal
`Regular`/`Special` types; missing type remains a separately labelled conditional
COIN-metadata compatibility rule. This review made no market requests.

### Returned-source integration

Early returned-source code had a wrong assembler key (`assets` instead of
`records`) and passed a lazy Mapping into funding code that accepted only dict.
Both were corrected. Early compact metadata validation also erased valid ETH
rules when BTC's selected metadata was invalid; compact projection now preserves
all matching rows/duplicates for independent per-asset admission. Unparseable
or transport-unadmitted daily JSON is a missing refresh; decoded selected
identity/rule malformation latches affected modeled decisions. The frozen policy
must state that distinction.

A remaining material clock-admission issue was reported: `adapter.decode`
initially trusted recorded `clock_consistent` and `within_controller_deadline`
booleans without independently reconstructing their retained raw monotonic and
wall clocks. Generic journal hash verification does not validate those time
relations. True booleans paired with contradictory raw clocks must be rejected;
reconstruct request/worker/controller ordering, wall-versus-monotonic duration
consistency and the fixed acquisition deadline. Exact controller deadline
reconstruction may require retaining its monotonic anchor. This is a source
admission prerequisite, not a claim that any empirical receipt was affected.

Corrected worker code now binds host/data root and uses the frozen unprefixed
selection view, with separate supervisor/worker locks and bounded exit records.
Index roles continue to the later selected exit for both benchmark paths. Full
runtime/resource and staged-return proofs are still pending; earlier synthetic
resource fixtures do not establish real assignment-callback cost or VPS timing.

### Raw-clock correction and current disposition

The raw-clock finding is resolved by retaining the controller's wall/monotonic
window anchor and absolute deadline, then reconstructing those relations in
`adapter.decode`. Eleven independent invented checks passed: a valid baseline;
missing/bool monotonic field; reversed worker/controller order; controller before
request; drift exceeding 100 ms; anchor after request; altered wall/monotonic
deadline; controller wall time outside the slot; and worker wall time before
request. All malformed cases retained forged true verdict flags and were still
rejected. No empirical receipt or market request was involved.

The complete returned-source implementation was read after its integration
corrections. Its staged-path provenance is distinct from the original host/data
root; the whole structural scan and production-fragmentation bound precede
content hashing and generic journal reconstruction. Selection, journal seals,
conceptual unresolved roles, per-asset hourly placeholders, fresh benchmark
indices and conditional funding inputs are retained. Source seals explicitly do
not assert independently observed quiescence. No further material source or
financial correctness defect was established in this reading.

Current disposition: the identified implementation defects above are corrected
or explicitly qualified in the integration policy. This is partial engineering
acceptance, not permission to capture. Representative real assignment-callback
resource measurement, complete staged-return/output resource measurement,
committed final grant/source pins, isolated deployed-runtime/release identities
and independently demonstrated launch/stop/backup behavior still require their
specific evidence. Earlier resource fixtures must not be represented as those
proofs. Zero strategies are validated; actual fees, fills, access, margin,
intrahour losses, true delta and positive expected returns remain untested.

Reviewed source hashes at that disposition:

| Member | SHA256 |
| --- | --- |
| adapter.py | 33604759509332850a2b2255da8ebc5ba8d5db296bf2a2ada3ebf2826d604b27 |
| analysis.py | af84494179d7cfdd0fae940ed9e786d86054e9869054ea764b0d98c1dabc3417 |
| funding.py | 246742b0b56b5734949677462885040d7094ee67fb5c3a181f1ac03d959f6595 |
| returned.py | c1e68f426fdb825f3a4a22b8cb68bd95270bda8948a93dea535c440314d3e6cc |
| worker.py | c597074eb022acad0edbc5676c93ea177098eac375451acffc11b39162625315 |
| schedule.py | debe91112302449d1fa9ffe04dfc806e4cd9a179286d35cb7b2a91bdc8cff4e9 |
| transport.py | 0c96d542101a5455c8674b76ac8f2964de66ed28b09cafb69bbc82ce197e8b4e |
| scripts/options_release_bootstrap.py | 07b53240e7967d209e98de426f50da05865cc4f4f203357e05e5ba1008cd33a3 |
