# Independent factor correction result data review

**PASS — no material provenance, denominator, saved-clock or report discrepancy found.** Saved artifacts were inspected without rerunning any strategy, signal, sizing, backtest, financial metric, data retrieval or holdout evaluation. BEST stream values were compared directly; saved scalar-parity deltas were validated without recomputing strategy performance. Report tables and headline counts were checked against the existing result fields.

Executed source: `27640882822d812c6d0478340495e033a11d3915`. Result SHA256: `a6886a55966f78d8e9bb36f694212fa626484a3088104bd53c48589a27b4309d`. The start record identifies the same source, gate and correction policy and precedes completion at `2026-09-10T12:31:45.655675+00:00`.

## Provenance and input preservation

All **16 pinned inputs/archive/charter files** match both current bytes and the execution commit. Both original external cache hashes remain unchanged. The gate equals its execution-commit version; canonical SHA256: `f371fdc5d6f66580147a0bbcbf311f67d0db86e8b9403a1f2e77641c913b1a1c`. The recorded policy hash matches the policy at execution source. Later completion-policy documentation is intentionally distinguished from the executed policy.

All **289 recorded sibling output hashes** match: 288 Parquets plus `started.json`. The result JSON is separately hashed above; the directory has exactly 290 files and no unlisted artifact. Reviewed runner, repaired V2 engine, sizing module and registry match the execution commit.

BTC retains 2,179 daily rows from 2019-04-14; ETH retains 2,178 from 2019-04-15, both through 2025-03-31. Entire retained calendars are contiguous, unique and midnight-labeled, with finite positive coherent OHLC and positive volume. Both development slices retain all **1,241 valuation dates** and more than 200 prior days. All available prior history remains in the inputs. Each of the 36 target files has the full valuation clock and price fields equal to its corresponding snapshot. Original caches were read only as bytes for hashing; no post-cutoff source price was parsed.

## Registered denominator, chronology and ledger

All **18 exact registered configurations, 90 measured variants and 18 invalid-log shadows** are present in frozen order. Every variant and both associated sleeve summaries report 1,240 returns. All 90 return files and 18 shadow files have the exact **2021-11-08..2025-03-31** daily clock with finite observations. All 144 repaired traces retain the same clock and initial sleeve NAV 10,000. Financial trace values are finite; nullable entry-price fields occur only on zero-exposure rows, as the declared trace schema permits. Actual halt bars and stop counts agree with the recorded sleeve details. Full post-halt cash tails are retained; saved tail counts agree with the saved primary return streams.

All 18 scalar-parity flags are true, reference metrics equal the pinned comparison artifact, and every recorded delta is within the frozen absolute tolerance 1e-10. Maximum recorded scalar delta: `1.1102230246251565e-16`. The archived BEST also passes direct comparison of BTC, ETH **and the portfolio column** across all 1,240 dates; maximum absolute difference: `9.9855020085914958e-17`.

The central ledger retains its exact **730-row, 428,150-byte prefix**, SHA256 `710a4f087325bfb408ed8d051963a473e8d8a47b445ffae0238c565aff6dc791`, identical to the execution commit. Exactly 18 unique records follow it. Their configuration, source/gate/policy identity, nested variant/shadow payload and result hash match every result cell. Final ledger: **748 rows, 569,325 bytes**, SHA256 `4d176acf273cacc5ada30abd02a0e7317c579968f29b2918196d88ebe3140601`.

## Published report consistency and qualifications

All 54 configuration rows across the comparison, sensitivity and halt tables match the saved result with the documented display precision. Headline counts match: 16 Sharpe improvements, 7 positive primary versus 6 positive legacy configurations, 36/36 halted primary sleeves, cash tails 238..1157 days, and no primary stop fill outside its recorded daily envelope. The descriptive largest-primary-Sharpe values for 30-day long/short momentum agree with the saved fields; this comparison introduces no new selection or adoption rule. Reviewed report SHA256: `423fcb1d4eb7c4fed9220f93015131554116283f26688600e9c08bf1ab7dadb9`.

Primary records remain `qualified_benchmark_measurement` with `validated=false`; the result records zero validated strategies, no holdout and no model refit. Pinned documentation explicitly retains the **unverified present spot/mixed-provider cache proxy**, absent July data hashes and unavailable contemporaneous raw receipts. Numerical parity establishes agreement with preserved references, not unavailable historical lineage or actual perpetual/funding provenance. The 50/50 aggregate is a benchmark index, not a reconciled pooled executable account. Assumed daily funding, threshold stop fills and frozen-exposure invalid-log diagnostics retain their qualifications. Positive development results do not establish strategy validation.

Review completed `2026-09-10T12:38:57.785993+00:00`. All inspected immutable inputs/outputs and the reviewed report were rehashed unchanged before this review file was written.
