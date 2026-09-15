# Independent Q3 postexecution review

Disposition: the retained partial evidence reconciles. Q3 remains **failed**, with
an execution-root HEAD change as the terminal engineering cause. No economic
result or completed historical source panel follows.

## Scope and evidence

Read-only review inspected the exact Q3 claim, terminal, all129 retained outputs,
raw RPC envelopes, frozen collector and lifecycle source. It checked output and
claim hashes, raw-body lengths and SHA256 hashes, request/response IDs, attempted
and suppressed requests, and published cell classifications. No network request,
financial experiment, process inspection, options inspection or source mutation
was performed.

- Claim source: `1d3491fd6f04d98d84228031749072703ff8af24`.
- Claim SHA256: `c92d317466fd36561667ef5fb3713aa6fd683e3087840469e28fe64ee3bc212d`.
- Terminal: `failed`, ended `2026-09-15T18:35:26.673051+00:00`.
- Recorded reason: `ValueError: source must equal the full current HEAD`.
- All129 retained output hashes and the terminal's claim binding match.

## Acquisition and denominator

There are59 durable intent/receipt pairs:48 actual single RPC/HTTP requests and
11 suppressed requests. All pairs are complete; no unpaired intent was found.
Raw bodies total117,101 bytes. All48 actual responses have HTTP200. They contain
15 Ethereum historical-state-unavailable errors and one execution revert. No
recognized RPC throttling response was observed in this capture.

The collector published four boundary vectors and September3–6 interior vectors.
September7 has two suppressed state receipts but no published day vector.
The Ethereum summary, history metadata and boundary/cohort decision document
also remain intact.

The frozen5,363-cell denominator separates as follows:

| Retained evidence | Cells |
| --- | ---: |
| Published classifications |70:33 complete,37 unavailable |
| Direct receipt only, classification unpublished |9:7 attempted,2 suppressed |
| Unclassified without a direct Q3 RPC receipt |5,284 |

The70 classifications comprise63 entries in published `cells` arrays and seven
explicit decisions in `boundaries.json`: four boundary decisions and three
cohort eligibility decisions, mapped to their registered cell IDs. This mapping
does not create or write a missing Q3 output.

The nine receipt-only cells are the Base chain ID, six headers at the three later
boundary dates, and the two suppressed September7 oracle-field cells. Their raw
evidence is retained; this review does not manufacture their missing normalized
cell outputs.

The final category includes derived and imported-history cells. It is not5,284
failed or unattempted RPC calls. Of4,243 potential request slots,48 were attempted,
11 were explicitly suppressed and4,184 have no intent. All unclassified cells
remain in the original denominator.

The September2,2023 boundary is unavailable. September1 boundaries in2024,2025
and2026 pass the collector's source-observability checks. Accordingly, the first
cohort is ineligible and the two later cohorts were eligible for interior source
acquisition. Eligibility is not completed coverage, semantic qualification,
executable valuation or investment admission.

## Root cause and preservation

`tradingagents/research/lifecycle.py:134` checks source identity before publishing
each output. Its `_check_source()` calls `admit()` with `_own_claim` supplied.
`tradingagents/research/admission.py:128` still unconditionally requires the
current checkout HEAD to equal the claim's source. `_own_claim` affects claim
accounting; it does not exempt HEAD equality.

Commit `b3037548d75e03ddab2405414fda935b45f78b4b` occurred at18:35:25UTC,
immediately before the terminal failure. The scoped comparison found no change
to the frozen Q3 design, gate, charter, collector, protocol helper or ordinary
lifecycle source. That byte preservation does not satisfy the stronger HEAD
invariant. The failure is consistent with committing unrelated preparation into
the execution checkout while Q3 was active.

Retain the failed claim, exact source, raw receipts, published decisions and
remaining denominator unchanged. The spent Q3 allowance and shared repair1/1
remain spent. No restart, replacement ID, terminal rewrite or new repair is
approved by this review.

## Future execution and narrow continuation

Future claims should start in an isolated detached checkout at their exact
committed source, containing all necessary predecessor claims and inputs. Its
HEAD must remain fixed until terminal closure. Import the exact resulting claim
and evidence before a later admission. Do not weaken the existing invariant or
change the failed Q3 runtime.

Unused financial slots can support separately reviewed, indivisible first
financial attempts under the existing phase grant. Their complete financial
rules and necessary acquisition inventory must be frozen before acquisition;
failed prerequisites retain an unavailable financial attempt. The182 historical
header keys already attempted across R1 and Q3 remain excluded from new requests.
Qualified existing receipts may be reused, including through separate downstream
qualification of retained raw bytes, without rewriting either failed run.

Giving each new shared header one owner avoids duplicate acquisition across
financial recipes. Missing or failed predecessor observations cannot be silently
retried under another recipe. Moving unfinished Q2/R1/Q3 source reconnaissance
into a financial filename, then choosing economics afterward, would require an
explicit additional source allowance; unused financial slots do not grant it.

This review approves neither a concrete financial registration nor any new
acquisition. Semantic compatibility, actual costs, full-capital accounting,
comparators, risk/stress, cumulative selection and confirmation requirements
remain applicable.
