# Offline options-policy preparation and disposition

September 11, 2026. This is an engineering decision, not a twentieth empirical
investigation. The nineteen empirical identities remain terminal, with sixteen
complete and three failed. Zero strategies are validated. No market input,
quote capture, account request, order, paper session or VPS change occurred in
this preparation.

## Accepted finite result

The pure `options_policy_engine.py` implements the proposed hourly unit-one
short-straddle/perpetual accounting contract on invented records. Separate
40/50/10 capital allocations, option-sale liability, quote-side fees, whole-order
size checks, nearest-lot rounding, funding-before-action ownership, missed
hedges and terminal closure are explicit. The nominal hourly slot differs from
the modeled action five seconds later; an initial funding event before entry
belongs to zero inventory. Missing later scheduled funding prevents complete
financial attribution. A missing mark affects valuation rather than creating a
substitute trade. Separate wallet risk flags are tri-state; a known deficit is
retained even when the other wallet is unknown.

Linear perpetual PnL uses the cumulative exact execution offset
`A = -sum(change_in_quantity * execution_price)`. This offset is **not cash
proceeds**. Marked derivative value is `A + quantity * mark`; separate perpetual
wallet equity adds initial reserve, known funding and negative commissions.
When flat, the offset equals total derivative trading PnL and enters terminal
cash once. Actual exchange realized/withdrawable cash while open is unavailable;
no transfer relies on the offset. Exact money never uses logarithmic returns.
The convention-swap diagnostic uses an explicitly approximate 60-digit Decimal
sum of simple returns and a floating logarithmic sum, solely as forensics.

The pure `options_policy_batch.py` validates sixteen fixed request/receipt slots,
8192-byte body bounds, exact URLs and hashes, own-venue clock intervals, typed
source clocks and transaction/output chronology. Source age is measured at the
fixed action; possible event time must also precede its own receipt plus the
stated tolerance. Partial model mark/delta fields have separate availability.
Entry, hedge, exit and each wallet's valuation use distinct dependencies.
Undocumented model event time stays unknown; this is a conditional arrived-model
policy, not proved Greek freshness. No transport or scheduler exists here.

## Failures retained and corrected

The initial average-basis representation accumulated large rational denominators
through partial reductions/additions. An extreme invented case and the ordinary
full-length eight-case rehearsal failed serialization. A named 4096-bit rational
limit made failure explicit but did not make a practical episode pass. The
first size report's byte-only true field excludes eight unavailable books and
must not be interpreted as practical feasibility.

Direct signed execution accounting removed the monetary basis growth. A second
full-length rehearsal then exposed denominator growth in the noncash sum of NAV
returns. Only that forensic sum was changed to declared bounded precision;
monetary fields remain exact. The v1/v2 reports and resource guards remain
unchanged, including all eight unavailable labels. These are uncommitted-code
engineering iterations, not rerun market experiments. Source hashes identify
the checked revisions; no claim of retained complete historical source packages
is made for those intermediate edits.

## Independent and resource evidence

- 68 focused synthetic tests pass under the pinned Python 3.13.13 runtime.
- Independent direct reconstruction uses incremental held-mark PnL and execution
  adjustments, independently of the engine's accumulator: 35,952 exact cash
  comparisons, eight full 1,057-slot cases, 8,456 NAV points and 132 funding
  events per case. The Decimal diagnostic agrees with a separate 100-digit
  calculation within 1e-55; logarithmic agreement is within 1e-11.
- Seven independent batch timing/missingness attacks pass. The earlier 296
  short-path comparisons and 504 normalized invented risk states remain scoped
  to their respective source versions and assumptions.
- The v3 guarded rehearsal completes all eight cases. The measured eight-book
  JSON is 6,845,005 bytes. Sixteen padded 8192-byte bodies produce 180,233 bytes
  of receipt JSON plus 9,100 bytes of normalized batch JSON; multiplied over
  1,057 slots and combined with the books, the measured routine footprint is
  206,969,986 bytes. Guard: 1.0265 seconds, 46,088,192 sampled aggregate RSS bytes.

This is one measured full-length fixture, not a universal 512 MiB proof. Initial
metadata, final funding retention, transport, atomic storage, source-history
validation and deployment remain outside that size measurement. A future writer
must enforce its actual cumulative byte cap and retain all cases on named
arithmetic or source unavailability. The prototype also does not implement all
auxiliary fields, monotonic-clock checks or capture durability proposed in the
source-contract note. Its scope is explicitly narrower.

## Next authorized work

Independent coverage finds that one complete prospective selling-policy path
still has information value despite adverse historical forecasting evidence.
Another short quote probe would not answer the hedge-path question. A single
future episode remains development evidence and cannot validate expected return,
true beta, tail probabilities, actual margin or account eligibility.

The user confirms an always-on VPS is available. Prepare the narrowly scoped
capture lifecycle, explicit cumulative options extension, pre-window financial
policy freeze and manual research-only rollout. Preserve the original options
family budget4/prior1 and its three consumed new claims; no extension exists yet.
The proposed source lifecycle must claim before networking, retain immutable
intents/raw receipts, handle interrupted and missed slots without retries, and
support independently verified final source bindings. The four frozen lifecycle
packages and all nineteen terminal runs remain unchanged.

The reviewed manual route forbids agent-issued VPS systemd edits over SSH.
Historical docs identify pck-preds-1 / 46.225.169.184, but current login and
persistent launch method are not verified. No production path, shared runtime,
service, secret or journal should be reused implicitly. These are concrete
operating prerequisites, not missing routine permission for research. Continue
local preparation while resolving them. No scheduler, capture grant, deployed
collector or unattended job has been created.
