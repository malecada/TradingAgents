# Primary-source orientation — September 15, 2026

Documentation preparation only. No new quote, index, fee-growth or financial
book has been captured or computed. Current documentation cannot establish
historical deployment or implementation versions; subsequent RPC evidence must
be pinned to block number/hash and decoded under the appropriate ABI.

- [Aave V3 Pool](https://aave.com/docs/aave-v3/smart-contracts/pool): supplies
  receive aTokens, withdrawals burn claims, and normalized reserve income is
  denominated in ray units (10^27). A balance index can support accrual accounting
  but does not prove withdrawable cash or the price of USDC in dollars.
- [Aave withdrawal mechanics](https://aave.com/help/supplying/withdraw-tokens):
  withdrawal depends on unborrowed liquidity. No borrowing is proposed for this
  program. Supply/withdraw pause flags, caps, liquidity and bad-debt exposure
  require separate source admission.
- [Aave address catalogue](https://aave.com/docs/resources/addresses) and
  [Base address book](https://github.com/aave-dao/aave-address-book/blob/main/src/AaveV3Base.sol):
  identify candidate read-only contract calls. Current addresses are proposed
  identities, not proof that the same implementation existed throughout history.
- [Uniswap liquidity overview](https://developers.uniswap.org/docs/liquidity/overview)
  and [v3 state interface](https://github.com/Uniswap/v3-core/blob/main/contracts/interfaces/pool/IUniswapV3PoolState.sol):
  a range changes token composition and fee eligibility. A v3 fee-growth/position
  reconstruction is required; advertised APR or volume times a current TVL share
  is insufficient. This phase retains v3 and does not silently substitute v4.
- [Lido wstETH](https://docs.lido.fi/contracts/wsteth/): the wrapper represents
  stETH through a conversion ratio. That ratio is distinct from ETH cash proceeds.
  [Withdrawal queue source](https://github.com/lidofinance/docs/blob/main/docs/contracts/withdrawal-queue-erc721.md)
  records an asynchronous claim path; exit waiting and lost rewards during queue
  processing must enter a later executable cash book.

Document access inventory so far: three search queries, four initial URL opens,
then two additional URL opens and three find operations. One Uniswap developer
interface URL returned an internal error; the official v3-core interface was
then opened. The address-book URL redirected from bgd-labs to aave-dao.
Search results included unrequested third-party performance snippets, which are
exposed orientation only and are not used as a dataset, return estimate, recipe
selection criterion or independent confirmation. No claimed financial evidence
rests on those snippets. This inventory counts tool operations, not hidden
search-engine HTTP requests. Further documentary accesses append to this log.

Continuation: two official Ethereum/Arbitrum address-book page opens, eight
additional find operations across already opened official pages, and three
raw official address-book document captures. Total so far: 25 documentary tool
operations (3 search queries, 8 page opens, 11 finds, 3 raw-document requests).
The raw three source snapshots retain URL, UTC clocks, exact bytes and hashes
under documents/. They provide candidate ABI/address configuration only.
The Arbitrum native-USDC aToken is USDCn_A_TOKEN; USDC_A_TOKEN is not substituted.

Independent Q2 design review used seven additional documentary operations:
four official source opens and three finds on the already opened Uniswap source.
Cumulative documentary operations32/60. No RPC or financial observations were
made by that review. Sources:
- https://raw.githubusercontent.com/aave/aave-v3-core/master/contracts/protocol/libraries/logic/ReserveLogic.sol
- https://raw.githubusercontent.com/aave/aave-v3-core/master/contracts/protocol/libraries/math/MathUtils.sol
- https://raw.githubusercontent.com/aave-dao/aave-v3-origin/main/src/contracts/protocol/libraries/logic/ReserveLogic.sol
- https://raw.githubusercontent.com/Uniswap/v3-core/main/contracts/UniswapV3Pool.sol
The review identifies separately mutated interest indices/timestamps, historical
instantaneous index changes, and LP intra-swap/flash fee changes. Event-only
reconstruction requires a version-complete mutation proof; one matching endpoint
or a ReserveDataUpdated-only trace is not enough. Q1's newly qualified Base state
route may avoid that replay; its full-calendar coverage still needs Q2 admission.

Q2 root preparation added three official opens (35/60 total): the incorrect
protocol/configuration/AaveOracle.sol path returned404; the correct
contracts/misc/AaveOracle.sol establishes USD zero-address base and immutable
unit plus fallback semantics; BaseUpgradeabilityProxy.sol documents the EIP1967
implementation slot. Sources:
https://raw.githubusercontent.com/aave/aave-v3-core/master/contracts/misc/AaveOracle.sol
and https://raw.githubusercontent.com/aave/aave-v3-core/master/contracts/dependencies/openzeppelin/upgradeability/BaseUpgradeabilityProxy.sol .
These are interface witnesses, not deployed-version proof or executable marks.

Q3 orientation added six documentary operations (41/60): four opens and two
finds on the official Lido deployed-contracts and wstETH interface pages. Two
proposed integration/token-guide paths failed; neither is evidence. Mainnet
Ethereum wstETH exposes stETH conversion methods. Base's listed wstETH is a
bridged ERC20; the Ethereum methods must not be assumed present on that wrapper.
A conversion balance is distinct from ETH redemption and two-way market value.
Primary pages: https://docs.lido.fi/deployed-contracts/ and
https://docs.lido.fi/contracts/wsteth/ . No staking market/rate query occurred.

Protocol-accounting preparation added four official source opens,45/60total:
Uniswap v3 Position.sol, SqrtPriceMath.sol, Tick.sol and periphery
LiquidityAmounts.sol. See PROTOCOL-ACCOUNTING.md for links and bounded mathematical
scope. No real source values or profitability were calculated by that work.

One additional official Lido WithdrawalQueueERC721 page open brings the total
to46/60. It documents aggregate queue views, request/finalization/claim ownership
and the distinction between accrued wrapper value and delayed ETH redemption.
URL: https://docs.lido.fi/contracts/withdrawal-queue-erc721/ . No queue state,
account, protocol yield or financial outcome was queried.
