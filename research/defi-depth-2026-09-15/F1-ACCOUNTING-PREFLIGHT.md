# Lending accounting preflight: source model, no financial observation

The proposed unlevered USDC lending mechanism earns borrower-funded interest.
An advertised APR is insufficient: the account must receive transferable units,
retain funded gas, meet the supply cap and be able to withdraw by the horizon.
Stablecoin loss, credit shortfalls and withdrawal congestion compete with yield.
No capital increase fixes an inadequate percentage return by itself.

Two official source reads used documentary operations56–57 of60:
[Aave ValidationLogic](https://raw.githubusercontent.com/aave/aave-v3-core/master/contracts/protocol/libraries/logic/ValidationLogic.sol)
and [WadRayMath](https://raw.githubusercontent.com/aave/aave-v3-core/master/contracts/protocol/libraries/math/WadRayMath.sol).
These define the documented source model; neither establishes the deployed Base
implementation or unchanged historical semantics. The earlier reserve flags,
aToken and scaled-balance source reviews remain separately retained.

## Findings affecting the financial contract

- A supply-cap check includes scaled token supply **and accrued treasury units**,
  converted at the next liquidity index, plus the new deposit. Comparing only
  totalSupply with the cap omits a committed protocol claim. Treasury source
  availability and the next-index/observation-clock relation must be qualified.
- Integer ray operations use half-up rounding in this model. Receipt units and
  displayed underlying balances differ; the account cannot book index growth as
  an additional cash credit after already redeeming the grown claim.
- Freeze blocks new deposits but does not itself block withdrawals in this
  source model. Active/paused checks apply to withdrawal. A price series or
  unchanged contract address does not establish these operational conditions.
- Contract USDC cash must cover the withdrawal amount. A sufficient snapshot
  does not guarantee future withdrawal priority or solvency; missing cash stays
  unavailable, not zero costs or certain liquidation.

The pure lending_math.py helper checks6-decimal nativeUSDC, integer bounds,
scaled mint/full-burn round trips, treasury-inclusive caps and required reserve
flags. It does not calculate strategy profitability. Six invented tests cover
half-up rounding, interest units once, treasury capacity, freeze versus pause,
contract cash shortage, invalid units and overflow. All pass; independent review
is still required before reuse in an empirical F1 registration.

The remaining F1 contract must freeze the complete source inventory and financial
recipe together, including exact implementation/source qualification, quantities,
USD marks, cash/gas/exit events, matched controls, stress losses, cumulative history
and unavailable cases. F2 owns its planned common headers; no header retry or
source-family restart is allowed. This preflight is not an acquisition or a
financial trial and does not select a protocol from observed returns.
