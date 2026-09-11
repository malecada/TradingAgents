# Bitrue metadata independent saved-source review

September 11, 2026. **PASS for literal source admission only.** The fixed
unfiltered request returned a contract array during this capture despite the
documentation's required-parameter conflict. This resolves this request's
observed availability, not every version, historical period or account.

Independent checker: [check_bitrue_metadata.py](check_bitrue_metadata.py).
Machine result: [bitrue-metadata-review.json](bitrue-metadata-review.json).
No collector import, network request, financial calculation or external refresh
occurred in this review. Binance comparison was not necessary to determine
whether the fixed Bitrue source schema was admitted; no synchronized cross-venue
claim is made.

The checker verifies the two individual receipts against the aggregate, exact
registered request identities, literal true attempt/completeness flags, integer
HTTP 200 status, null errors, strict base64, byte counts and SHA256, strict UTF-8
JSON without duplicate keys/nonfinite values, request/retrieval clock ordering,
all rows and their frozen normalized admission rules, output hashes and source
commit contents. Receipt equality alone cannot prove disk-write timing; the
reviewed collector and synthetic lifecycle establish the immediate-write order.

Source commit `328b23f88357656a23ce5ba2874cf514f6fce547`, gate
`c8325be306f6a4faa4af5df94f8764d741c9550a81409ae01117195b51dba51c`,
collector `daadd2532952fb06a2789c70423c28835eece7d6622aa4a8a4a2444e5a7efab7`
and all pinned source/runtime/input/charter hashes agree with local committed
bytes. Remote equality before execution is coordinator evidence, not inferred
from local commit verification.

Two intended requests completed, zero unavailable source cells, four outputs.
Raw bodies total 250,390 bytes; actual outputs total 1,229,093 bytes.
Actual first request was **09:20:53.715470 UTC**, last retrieval
**09:20:56.132582 UTC**. These clocks are distinct from the earlier local
request-definition observation. The guard reports exit zero, no limit reason,
5.680 seconds and 61,349,888 bytes sampled aggregate RSS under 512 MiB/120 seconds.

All **755** unique contract rows are retained, and all 755 satisfy the frozen
row-field validity rules. Exactly the two fixed BTC/ETH names satisfy the
conditional target mapping. Literal target metadata follows; no quantity or
capital arithmetic is implied by this table.

| Field | E-BTC-USDT | E-ETH-USDT |
|---|---|---|
| type | E | E |
| side | 1 | 1 |
| status | 1 | 1 |
| multiplierCoin | BTC | ETH |
| multiplier | 0.0001 | 0.001 |
| minOrderVolume | 4 | 3 |
| minOrderMoney | 30 | 10 |
| pricePrecision | 1 | 2 |

The time source returned an object containing `serverTime` and `timezone`.
Its field units remain **unavailable under the frozen rules**; the numerical
length or timezone label is not interpreted into authoritative event time.
Status 1 and a conditional naming/unit match do not establish account
eligibility, linear cashflow/collateral rules, current fees or historical
contract continuity.

The acquisition removes one current metadata dependency. Public settled funding
events with associated marks and verified unit/clock semantics remain
unestablished within the bounded source review. No funding-profit book, rate
differential, expected return, exposure claim or family-wide rejection follows.
The next justified action is a coordinator disposition of that named history
gap; any prospective current-index capture needs separate registration and
proxy-only interpretation until settlement semantics are established.
