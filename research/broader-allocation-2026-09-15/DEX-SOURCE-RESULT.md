# Three-chain source result — September 15, 2026

**Source capture complete:16/18 fields qualified, two explicitly unavailable.
No implementation, liquidity, cost or profitability claim.**
Run: `research_runs/allocation-dex-source-20260915`, execution source5f0cacf,
preregistered packetdc95d64. All18fixed requests were attempted once, with no
replacement/retry;19outputs reconcile under the standard verifier.

| Chain | Identity / finalized header / chosen pool / gas field | Requested historical state | Narrow finding |
| --- | --- | --- | --- |
| Ethereum | All four source fields returned and validated | Header21,000,000:2024-10-19T13:45:47UTC. Code query returned historical-state-unavailable | Current factory mapping available; this exact old-state query unavailable on this endpoint |
| Base | All four source fields returned and validated | Header20,000,000:2024-09-19T23:42:27UTC.24,535code bytes returned | One old canonical-hash code lookup supported; full archive/pool-event coverage untested |
| Arbitrum One | All four source fields returned and validated | Header280,000,000:2024-11-30T21:06:05UTC. Code query returned missing-trie-node/state-unavailable | Current factory mapping available; this exact old-state query unavailable on this endpoint |

Every HTTP response was200; the two failures were explicit JSON-RPC state errors.
All three factories returned nonzero mappings for the fixed WETH/native-USDC
0.3% fee tier. A mapping is not an executable quote or pool-liquidity admission.
Finalized blocks and code were provider assertions; no independent chain witness
or code audit was performed. The different historical heights/dates are source
probes, not matched return windows or a chain performance comparison.

Gas-price integers remain raw receipt-time wei suggestions. They omit swap gas
units, pool/interface/transfer charges, L2 data charges and executable impact;
no cheapest-chain or transaction-cost ranking is inferred. No capital constraint
at$10,000 or justified larger amount was measured. Absolute net profit and
benchmark-relative value both remain **unmeasured**, rather than zero or failed.

The current network configuration reached all three endpoints. The user reports
NordVPN via Finland; its actual egress was not independently measured or changed.
This result does not diagnose every endpoint or account-access restriction.

## Preservation, resources and cumulative accounting

Raw receipt bodies total129,209bytes, each retained with request/receipt UTC,
method/params, HTTP status, base64 and SHA256. All eighteen hashes reconstruct.
The guard exited0 with no limit reason,26.4669seconds and69,263,360bytes sampled
aggregate RSS, within240seconds/512MiB/twoCPU. Sampled limits remain qualified.
No test/capture process remains running from this experiment.

Effective usage180/189:179administrative import including the earlier unclaimed
custody failure, plus this one new lifecycle claim. Admission2/6 consumed; four
admission slots, four financial recipe slots and one confirmation remain.
Public acquisition budget18/100used,82remaining. The2unavailable cells stay in
both source output and terminal denominator. The old custody claim was not
retried; original source/gates/ledgers/options/data remain unchanged.

## Next justified work

Independent raw-evidence review precedes the already prepared Binance USDC
spot-source child. That child answers a separate venue/source question and uses
four fixed requests. The DEX branch retains these source distinctions: do not
assume Ethereum/Arbitrum archives are globally impossible, promote Base from one
code lookup, fetch replacement providers, or use current listings as a historical
low-cap universe. Further executable or full-history evidence needs a separate
registered question within the cumulative finite budget.
