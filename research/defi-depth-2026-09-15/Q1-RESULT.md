# Q1 — protocol state source result

The registered capture completed once from source `4c09857`. All 141 cells and
400 outputs are retained. Structural verification passes; independent raw-data
review is recorded separately in `reviews/q1-postexecution-review.md`.

| Source | Historical calls complete | Finalized calls complete | Coherence cells complete |
| --- | ---: | ---: | ---: |
| Ethereum | 0/20 | 20/20 | 2/4 |
| Base | 20/20 | 20/20 | 4/4 |
| Arbitrum | 0/20 | 20/20 | 2/4 |

All nine chain/header cells completed. Total: 97 complete and 44 unavailable.
The unavailable denominator comprises 40 historical state calls and four
dependent coherence checks. Raw RPC errors identify pruned or unavailable state
at the selected Ethereum and Arbitrum endpoints. They are not economic failures
or evidence that every archive source on those chains is unavailable.

Base's two observed states satisfy the registered normalized-income/scaled-supply
identity and LP source checks. Finalized Ethereum and Arbitrum supply identities
differ by one base unit, within the frozen rounding tolerance. These checks do
not establish historical continuity, executable withdrawals, fee earnings,
account eligibility or an implementable investment.

129 actual requests retained 100,951 raw bytes. Recorded capture elapsed time was
541.4126 seconds, with no overall duration cutoff. This is elapsed time, not a
CPU or peak-memory measurement. No financial outcomes were computed.

Q1 consumes one of six successor source questions and one of eleven possible
successor claims. The narrow source family has effective count 2/3, including
its already-counted original DEX predecessor. The original allocation count
188/189 and its four failed financial recipes remain unchanged. No family import
is added twice to global history.

The next justified question is a complete chronological Base source panel.
Selection is based on state availability alone. Lending needs full index,
reserve, valuation and withdrawal evidence; LP additionally needs inventory,
range fee accounting and a price-taking/capacity assessment. Two endpoints do
not supply annual performance. Event-only replay on other chains remains
unqualified because completeness of all index/fee mutation paths is unproved.
