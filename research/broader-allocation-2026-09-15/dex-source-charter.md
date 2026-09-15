# Three-chain DEX source-capability measurement

Experiment `allocation-dex-source-20260915`, discovery/exploratory, admission
question 2/6. A distinct source question following an unclaimed monitor failure;
not a custody rerun, low-cap selection or return test. Commit this charter,
exact spec, source and gate before capture. Existing options and old claims stay
unchanged. No wallet, auth, account, signing, transaction or paid request.

## Question and finite denominator

Can the fixed free public RPC route on each of Ethereum mainnet, Base and
Arbitrum One identify the chain, disclose a finalized block, locate the declared
Uniswap v3 WETH/native-USDC pool, provide a gas-price field and return one
historical factory-code state using canonical block hashes?

Exactly six ordered cells per chain,18 total. Each cell permits at most one
single RPC POST; no batches, retries, replacement endpoint, alternate fee tier,
extra contract, block or chain. Each unattempted/unavailable case remains in the
18-cell denominator. Registered spec gives exact addresses and endpoints.

| Cell suffix | Request and success rule | Limitation |
| --- | --- | --- |
| chain | eth_chainId equals fixed expected ID | Provider assertion, not account eligibility |
| finalized | eth_getBlockByNumber(finalized,false): parse valid nonzero hash, quantity number, nonfuture positive timestamp | Finality is the provider's assertion, not an independent witness |
| pool | eth_call factory.getPool(WETH,USDC,3000) at finalized blockHash with requireCanonical=true; decode exact ABI address | Zero means no pool at that tier, not a missing request. Nonzero does not establish code identity, reserves, tradability or safety |
| gas | eth_gasPrice, valid nonnegative hexadecimal quantity | Retrieval-time suggestion in wei, unanchored; not transaction gas units, swap cost or L2 data charge |
| history_header | eth_getBlockByNumber at exact fixed height; validate returned height, hash and timestamp | ETH21,000,000; Base20,000,000; Arbitrum280,000,000. Coarse old-state probes, not matched dates or return windows; timestamps learned only after capture |
| history_code | eth_getCode(factory,{blockHash: historical hash, requireCanonical:true}) must return nonempty valid bytes | Tests one canonical-hash code retrieval. An EIP-1898 error is exact-method unavailability, not proof that all historical APIs fail |

The anchor precedes dependent calls. All requests after a failed chain identity
are skipped on that chain. Pool requires admitted finalized header; old code
requires admitted historical header. History header is compared with finalized
height/time when that anchor is available. Other independent cells can proceed
after a method-specific error. Any HTTP403/418/429/451 stops further requests on
that endpoint; retain reasons for all remaining cells. No number-tag fallback
when hash-tag calls are unsupported. Transport failures are unavailable and not
repeated; the next predeclared independent cell may still be attempted unless a
denial or time bound stops that chain. Cross-chain receipt times are not matched.

This source question does not measure token contract/decimals, full swap gas,
reserves, current depth, historical price/swap arrays, all-history availability,
rug survivors, deposit/withdrawal costs or personal access. Such missing evidence
is named in the result, never silently treated as zero. No chain or strategy can
receive an implementation or economic pass. Complete means only the exact field
query passed its narrow validation. Code bytes are hashed, not audited.

## Accounting, history and decision

$10,000 and the10% absolute/2% proposed incremental thresholds retain their
meaning in DESIGN; this capability check calculates no PnL, cash benefit, APR,
Sharpe, capital requirement or investment sizing. Gas quantities stay in wei;
no ETH/USD conversion, claimed fee comparison or annualization. Cash, passive
holdings and allocation comparators are therefore unmeasured, not zero-return
results. Signed cash books and the full stress/confirmation rule are later
requirements. No log-return convention diagnostic applies to metadata.

The retained history is178scoped allocation records plus44related DeFi records
in separate crosswalks (222 scoped union, not independent hypotheses). This
source question inherits allocation implementation and DEX source history;
it grants no NLST/SMW/staking/carry trial. All historical arrays remain spent.
Parent is null because the earlier launch made no lifecycle claim or result.
The separate failed-launch receipt is referenced explicitly rather than creating
a fabricated parent. New gate imports179administrative attempts:178core records
plus the one failed unclaimed custody launch. Cap189 and category caps remain.
This claim consumes admission slot2/6; failure still consumes it. After claiming,
effective usage180/189, with four admission slots, four financial recipes and one
confirmation left. The44related DeFi records are not fresh alpha allowances.

Retain every field result and classify the exact cause: unsupported schema/RPC,
HTTP denial, network/timeout, invalid identity/chronology, missing dependency or
qualified narrow progression. Passing all18fields supports preparing a later
registered executable-source contract, not launching a financial backtest.
Failure of historical state retains prospective collection as a potential route;
no observer is launched or archive endpoint changed under this contract.
Continue to the separate EEA spot-source question within the unchanged budget.

## Capture, bytes, clocks and resources

Inputs are the authored exact spec,44-row metadata crosswalk and failed-launch
receipt; their registry interval denotes authored exposed configuration, not a
market sample. The actual external observations are receipt-time source outputs,
all explicitly exploratory. Registry capture windows do not create confirmatory
freshness. Historical heights/hashes/UTC timestamps and contemporaneous gas/
finalized timestamps are retained in outputs. Full chain/source data identity is
(chain ID, RPC URL, method, params, response hash, request/retrieval UTC).
A future financial registration must separately import these exposures.

At most18 HTTP POST and18 RPC operations,10second hard deadline per request,
256KiB response prefix cap, no compression request, proxies, retries or redirects.
System-level NordVPN via Finland is user-reported, not independently checked or
changed. Refusing application proxy variables does not disable a system VPN.
No credentials/environment files or request headers from private accounts read.
The alarm bounds DNS/connect/body reading on the main thread. Existing timers
are refused, not overwritten. Partial/oversized bodies retain exact bytes/hash
and are not parsed as complete. Date/Content-Type response headers only.

Cooperative capture200seconds; outer v2 guard240seconds,512MiB sampled aggregate
RSS,twoCPU affinity and synchronous main-thread helpers only. Default guard
implementation is reused with an explicit240second wrapper.18×10=180seconds
leaves cooperative and outer allowance for metadata/receipt publication. Max
pretty-encoded retained outputs8MiB; raw response total at most4.5MiB before base64.
Each receipt is published immutably immediately, including attempted=false cases;
terminal source-summary.json plus every18receipt is the output denominator.
Raw prefixes/errors survive a later failure. Total program ceilings100public
requests/500MiB/eightCPUhours remain; charge every attempted request, not only
successful ones. Documentation navigation is recorded as design orientation,
separately from this empirical acquisition budget.

## Verification and independent review

Use pinned Python3.13.13. Before capture, verify malformed/duplicate/null/ID and
quantity/ABI errors; wrong chains; absent pools; unsupported hash tags; future or
wrong historical blocks; HTTP denial propagation; complete18cell retention;
partial/oversized bytes; and a no-network lifecycle path through the exact guard.
Existing reviewed transport/guard patterns are reused; old files are unchanged.
Independent review must inspect packet, literal source mapping and input hashes,
then reconstruct retained bytes/results/denominators after the run. Run standard
lifecycle verification as well. Tests use invented data or disposable temporary
registrations, never repeat an actual claim. Named offline profile remains the
broad check; no legacy experiment mains.

## Public documentation used before capture

- [Ethereum deployment and WETH](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-ethereum-deployments)
- [Base deployment and WETH](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-base-deployments)
- [Arbitrum deployment and WETH](https://developers.uniswap.org/docs/protocols/v3/deployments/v3-arbitrum-deployments)
- [Circle-issued native USDC addresses](https://developers.circle.com/stablecoins/usdc-contract-addresses)
- [Base RPC and ID](https://docs.base.org/get-started/connect-to-base)
- [Arbitrum RPC and ID](https://docs.arbitrum.io/for-devs/dev-tools-and-resources/chain-info)
- [PublicNode Ethereum endpoint](https://ethereum.publicnode.com/)
- [Canonical block-hash calls, EIP-1898](https://eips.ethereum.org/EIPS/eip-1898)

Accessed September15,2026 for source orientation; these are documentary mappings,
not immutable raw deployment witnesses or independent on-chain attestations.
The ABI selector1698ee82 was independently derived from
getPool(address,address,uint24) using pinned eth-utils Keccak, never SHA3-256.
Runtime only encodes the frozen calldata; it does not import a wallet library.
