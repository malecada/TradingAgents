# Independent Q2 pre-execution review

Disposition: **PASS for the fixed source-only capture**, subject to the usual
commit and metadata admission before execution. No blocking defect was found.
No financial calculation, network request, registry mutation or experiment rerun
was performed by this reviewer. Only this review document was written.

Reviewed September 15, 2026:

- q2_source.py SHA256:
  `373b25da0cc2be9436a8ea6f28316f8c795b8d0fdde2d0c622aba6dd3ee31919`
- q2_transport.py SHA256:
  `db52ecded14fe86526d521b0a0f151d2465716907800149a46a0fff5286be034`

## Calendar, clocks and denominator

Independently reconstructed all1,096 target dates and candidate heights from
the retained seed. The grid is September2,2023 through September1,2026 inclusive.
Each specified cohort spans365 elapsed days and therefore contains366
boundary-inclusive marks. The shared cohort endpoints occur once in the unified
panel; these are not three independent samples.

`q2_source.py:44` checks returned header numbers, timestamps and hashes.
`q2_source.py:55` requires adjacent parent linkage and an exact bracket around
the target. State requests use the left block's canonical hash, never the
later block. The two-second arithmetic proposes a height; failed validation
does not authorize a search or substituted clock. Actual timestamps are retained.

Independent inventory arithmetic matches registration:

- HTTP:1 +1,096×2 =2,193 maximum requests.
- Logical RPC:1 +1,096×17 +4×14 =18,689 maximum subcalls.
- Cells:1 +1,096×19 +4×14 +9 =20,890.
- Outputs:3 +1,096×5 +1 =5,484.
- Raw reservation:2,193×262,144 =574,881,792 bytes, counted once per response.

The Q1 subcalls plus this reservation leave6,182 of25,000 acquisition subcalls;
Q1 raw bytes plus the Q2 maximum remain below2GiB. This headroom is not another
source/financial allowance. The first cohort's leap-year adjustment is explicit
and made before Q2 observations or financial outcomes.

## Decoder, transport and preservation checks

Independently verified inherited calldata against Q1, new selectors and complete
oracle address arguments, and the EIP1967 implementation slot as
Keccak("eip1967.proxy.implementation") minus one. Storage addresses must have
canonical padding and be nonzero. Missing contract code, nonpositive prices,
wrong units and malformed ABI remain unavailable. Normalized-income supply
reconciliation uses the frozen one-base-unit tolerance; it does not establish
the user's actual mint/burn rounding convention.

Batch IDs are matched independently of order. Unknown/duplicate/non-string IDs
invalidate the batch; absent members stay unavailable individually. There is no
single-call fallback. The transport permits only the fixed Base endpoint and
read-only methods, with32 members/32KiB request limits and256KiB/10-second
response limits. It has no aggregate elapsed-time kill, retry, redirect,
credential use or proxy route. HTTP denial stops subsequent requests.

Independent invented cases covered partial bodies, unknown IDs, malformed/zero
oracle prices, absent code, a mismatched oracle unit and a supply-identity
mismatch. Every case retained the entire two-date denominator and all prescribed
outputs; each transmitted49 subcalls in5 HTTP requests. Receipt bytes, hashes and
lengths reconciled. The named focused target passed11 tests, including denied
endpoints, wrong chains, bad brackets, reordered responses and absent members.

The final retained preflight binds the reviewed hashes. It exercised the full
1,096-date capture in memory:20,890 cells,5,483 outputs before summary,
2,193 HTTP requests and18,689 logical subcalls. Its separate compact real
main/ResearchRun fixture passed56 cells/1 unavailable/14 outputs. This is not a
claim that the complete5,484-file disk lifecycle was executed synthetically.

Intents precede transport; raw receipts precede parsing and daily results.
Expected missing cases retain all cells. Unexpected process/storage failures
preserve published evidence and consume the claim; they do not authorize an
automatic restart or imply a completed trailing matrix.

## Lineage and limits on interpretation

All imported Q1 family, dataset and experiment objects match unchanged.
Source, input, charter and ordinary runtime hashes match their gate. Q2 has the
terminal Q1 parent in the same source family. Prior1 +Q1 +Q2 exhausts cap3 and
uses successor source slot2/6; the original allocation remains188/189 and the44
related DeFi records are preserved overlapping history. No renamed financial
family or new confirmation is admitted.

Two nonblocking limitations need explicit downstream reporting:

1. At `q2_source.py:223`, cohort coverage uses the named daily field list.
   A complete daily-source cohort can coexist with unavailable boundary oracle
   unit/code/identity checks; an invented bad-unit case confirms this behavior.
   The current output limits itself to daily field coverage. Do not relabel it
   valuation-ready or executable without separately checking boundary and
   historical identity evidence.
2. Daily protocol-oracle readings are not executable bids or independently
   validated market marks. Caps, stale values and shared oracle mechanisms can
   distort measured volatility, drawdown and covariance. Four boundary source
   checks do not prove continuous pricing semantics; daily implementation-slot
   witnesses do not establish every intraday upgrade. These remain financial
   admission prerequisites, as do gas, funding, withdrawal, liquidation and
   contract-loss accounting. All executable-route cells remain unavailable here.

No deployed-version semantics, full LP tick/fee reconstruction, user access,
historical execution capacity, economic returns, risk estimates or statistical
power were validated. Base is selected for demonstrated source availability,
not an observed economic advantage; missing Ethereum/Arbitrum history remains
preserved. Q2 is admissible as a finite source question with these limits.
