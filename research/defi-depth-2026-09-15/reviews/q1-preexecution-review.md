# Independent Q1 pre-execution review

Disposition: **PASS for the registered source-only capture**, after two validation
fixes below. No financial recipe, yield estimate, historical reconstruction or
implementation decision is admitted. Review date: September 15, 2026.

Reviewed source SHA256:
`66e638fe02e648cf83967ca65b85ade928cbb0b6c32bb52ee8ea05c9cc9a8675`.
The current gate and final disposable preflight bind this same source. The
charter hash matches its gate. Commit and ordinary metadata admission remain
required before the actual capture.

## Findings resolved before outcomes

1. **Finalized chronology depended on a successful historical reread.** At
   `q1_source.py:73`, the initial implementation accepted an invented finalized
   block 99/time999 against a frozen historical block100/time1000 when the
   historical context was missing. It now compares against the frozen historical
   anchor unconditionally. This prevents a missing historical response from
   weakening the chronology rule.
2. **Impossible slot state could qualify as coherent.** The initial LP check
   accepted sqrt-price `2**96` and tick900000. `q1_source.py:81` now checks the
   tick domain and initialized oracle index/cardinality constraints, and
   `q1_source.py:210` applies that check to LP coherence. Raw source observations
   remain retained when the coherence check fails.

The added counterexamples and the full focused invented-input target passed:
18 tests. No actual RPC or financial experiment was run by this reviewer.

## Independent checks

- Recomputed every selector with Keccak and reconstructed the complete calldata
  for all60 authored actions, including each public aToken balance argument,
  the factory token/fee tuple, and sign-extended ticks -887220/+887220. The ABI
  tuple widths for slot0 and ticks match the declared v3 interfaces. Reviewed
  canonical integer, Boolean and address decoding.
- Decoded all three retained official address-book snapshots, verified their raw
  body hashes, and matched the Pool, native-USDC and corresponding aToken
  identities. Arbitrum uses USDCn. Matched the three exact old headers and named
  pools to the retained original DEX source summary. Current documentation does
  not establish historical implementation identity.
- Independently counted three chains × (three header/identity requests +
  two epochs ×20 state requests) =129 requests; twelve coherence cells give141
  cells. Three artifacts per request plus twelve coherence artifacts and summary
  give400 outputs. Registered inventories agree.
- Exercised invented wrong-chain, historical-header-error, partial-body and
  mid-chain HTTP429 cases. Every case retained141 cells and399 capture artifacts
  before the separately written summary, with matching receipt byte lengths and
  SHA256 hashes. Their actual request counts were87,109,129 and94 respectively.
  Denied endpoints stopped; other chains continued. Missing historical headers
  blocked their dependent state calls while finalized observations could remain
  separately available. Calls use EIP1898 canonical block hashes.
- Reviewed the frozen transport: fixed public endpoints, no authentication,
  redirects, proxies, hidden batch, replacement or retry; received prefixes
  survive ordinary timeout/body failures. The source loop has no aggregate
  elapsed or CPU-duration kill. Durable intent precedes transport, and receipt
  and result precede the next request. An unexpected process/storage failure
  remains a consumed, incomplete claim rather than an evaluated full matrix.
- Checked source/runtime/input/charter hashes and compared every imported old
  family, dataset and experiment object against the final H5 registry: no
  differences. The two small source fixes were then bound by refreshed source
  and charter hashes and the final synthetic lifecycle receipt.

## Scope and cumulative history

The new source family imports the one known direct DEX lifecycle predecessor
and permits exactly two new claims (`prior_attempts=1`, `attempt_budget=3`). A
null structural parent is appropriate because the ordinary lifecycle requires
same-family parents; the actual predecessor claim/output and complete overlapping
history are pinned inputs. The imported one is already within the old188 and is
not an additional global trial. It is not a claim that all historical source
acquisition or statistical multiplicity has been enumerated.

The original188/189 allocation closure, failed custody charge and44 related DeFi
records remain preserved. Q1/Q2 jointly consume two of six successor source
slots. Q3 staking, Q4 causal small-token sources, Q5 carry forensics and Q6
information provenance fill the remaining four. Costs and executable routes
are prerequisites within those questions, not a seventh source slot. Four
financial recipes and one evidenced-defect repair are ceilings, not permission
to repeat an exhausted mechanism or revise an economic failure. The original
confirmation slot is unchanged; the old88 contrasts do not cover new DeFi
selection. Later claims need their own reviewed ancestry and exact gates.

The source envelope is finite: Q1 reserves129 requests and33,816,576 raw bytes.
Phase-wide25,000 requests,2GiB and60 documentary operations require cumulative
tracking in subsequent packets. Their remaining headroom grants no additional
recipe, source retry or confirmation.

## Limits and untested claims

No live endpoint behavior, independent chain finality, historical upgrades,
withdrawal access, protocol solvency, actual user account or fee terms, cash/USD
marks, gas economics, full LP inventory/fee accounting, strategy returns or
power were tested. Aave reconciliation is an index/scaled-supply identity, not
withdrawable cash. LP validation is basic source identity/domain/cardinality;
it does not prove complete tick/sqrt coherence or all boundary-state invariants.
Those semantics must be established before a financial reconstruction uses
them. No chain ranking follows from current or old-state availability.

No original registration, ledger, guard, financial book or options worker was
modified or rerun. The initial failed synthetic fixture remains historical
engineering evidence; it was not an actual source claim or market request.
