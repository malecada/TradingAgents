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
