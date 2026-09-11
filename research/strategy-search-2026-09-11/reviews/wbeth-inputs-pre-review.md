# WBETH source-input independent pre-result review

September 11, 2026. Source/parser review passes; **full guarded maximum-payload
CLI/lifecycle preflight and final gate freeze remain pending**. No actual WBETH
response, market outcome, network request or financial arithmetic was inspected.

Independent targeted run: `tests/research/test_wbeth_inputs.py`, **20 tests pass
in 0.05 seconds** using the pinned Python runtime. Canonical request-spec digest
`58104f4558710b80fd1228406dae9fe2777aad4f41ef2927bbfc904c051e4ead`
and literal April 1–July 1, 2026 exclusive millisecond boundaries were verified.
Reviewed file SHA256 values: collector
`049cad5ef286188f43c8b24f157f9c6f89ae2425a0dc4e2f024a5e643f0cb44a`,
charter `a7b9667f8c5ad99bad06671fc05e4d0c6d60db356d69bcce74f2ea334b306a1a`,
request-spec file
`0e78e138fc1541438b3112b30ac68771fad4960742238edc58934d88fe9dacb8`.

The two fixed requests, complete 91-day/12-field array and exact consecutive
open/close clocks agree with the charter. Strict JSON and standalone-wrapper
checks reject duplicate keys, nonfinite JSON and injected extra fields. Positive
finite OHLC ordering, nonnegative volume fields, literal integer nonnegative
trade counts and zero-activity indices are checked. Raw bars remain preserved
in receipts, with no return/ratio/hedge calculation. The ignored twelfth field
is retained without semantic interpretation. Taker-volume-versus-total or
zero-volume/positive-trades economic consistency is not a frozen admission test;
successful admission must not be described as validating those properties.

Metadata requires exactly one WBETHUSDT row, exact asset identities, TRADING,
literal true spot-enabled status and uniquely named literal filter objects.
Unknown fields remain preserved, without interpreting filters as historical
lot/fee/account authority. The inherited receipt engine saves raw before parse
and next request, enforces the spec digest, suppresses same-host denial and
retains both intended cells on cooperative failures. Abrupt resource failures
remain failed attempts with partial artifacts, not automatic retries.

Source-admission scope is a legitimate distinct prerequisite for a separately
fixed market-value hedge with spot exit. It does not assert contractual ETH
delta, redemption value, staking attribution, fills or positive returns. The
spent ETH/Q2 chronology and prior PRX/carry/DEX ancestry remain relevant; a
three-question allowance is administrative, not independent-trial accounting.

Recommended invented maximum-payload shape for the pending full lifecycle:
one near-5 MiB metadata symbol containing a preserved extra string or unknown
filter fields, plus 91 valid bars padded through ignored-field strings to near
5 MiB. This exercises normalized output as well as duplicated raw receipt bytes;
whitespace-only payloads exercise raw size but little normalized expansion.
Verify actual pretty-encoded four-output sizes, guard exit/limits and full
two-cell retention. A separate expansion case should become unavailable under
the normalization bound rather than violate output resources. No implementation
change was requested by this review.

## Final gate and full lifecycle — PASS

Final gate SHA256
`38f0038210d7e368c7bf807473500f1accb723c9741b2ef7e322cb6fa1a0d4ea`;
collector, charter and request-spec hashes above are unchanged. All pinned
source/helper/transport/guard/runtime/lockfile, marker, charter and input hashes
match local bytes. Every ancestor family/dataset/experiment object matches
`gates-bitrue-metadata.json` exactly. The new mechanism has zero known exact
prior WBETH gates and three administrative questions, explicitly preserving
PRX/DEX/carry ancestry and unknown broader multiplicity. Two source cells and
four outputs match the fixed request specification.

The exposed request-definition window and pinned marker both use September 11,
09:30:47.099732–09:30:47.099983 UTC, with the matching request-spec digest.
These are local document-observation clocks only; future source-response clocks
must remain actual retrieval times. The charter separately preserves the
exposed 2026 Q2 source period and prohibits financial calculations at this stage.

The added lifecycle tests cover the requested large structured metadata and
ignored-bar-field payloads, plus a million-element normalization expansion.
Both run actual ResearchRun writes in disposable Git repositories through the
frozen 512 MiB/two-CPU/120-second guard. Structured fixtures preserve 10 MiB raw,
two complete cells and 33,209,267 actual output bytes. Expansion preserves the
same raw denominator, marks metadata unavailable while retaining the complete
bar cell, and writes 27,966,086 bytes. Copied guard reports show no limit or
child-exit failure, with sampled aggregate RSS 81,424,384 and 105,250,816 bytes.
The reviewer independently reran the targeted parser and lifecycle tests:
**22 tests pass in 1.86 seconds**.

No remaining pre-result blocker was identified. This is source/synthetic
admission only; no actual WBETH response or financial outcome was inspected.
Coordinator commit, verified remote preservation, guarded acquisition and
independent raw/schema review remain required lifecycle steps.
