# Independent full usable-range fee attribution proof

Reviewer: separate research-reviewer broader_design_review. Pure source/mathematical
review; no real R1 observations, profit calculation or new financial recipe.
Two official source opens were used, bringing documentary usage to49/60.

## Result and precise domain

For standard immutable v3 semantics with spacing60, continuously held virtual
liquidity over the exact usable range[-887220,887220] has the same change in
inside fee growth as historical global fee growth, modulo2^256, **on the frozen
historical fee/price/liquidity path**. This is a fee-index attribution identity,
not a theorem about actual earnings after adding that liquidity to the pool.

1. Every valid historical position boundary lies inside the usable range.
   Positive historical active liquidity therefore implies the virtual full-range
   position is active too, with the pool's exact-boundary tick convention.
2. Swap fee growth increments only when historical liquidity is positive, after
   protocol fees are removed and before the next tick is crossed. Fee-only steps
   obey the same liquidity condition. Flash accounting requires positive liquidity.
3. Consequently, global LP fee growth is constant while the virtual position is
   outside its range. Its virtual boundary counters remain initialized for the
   entire position lifetime; historical boundary clearing does not clear them.
4. Initialization excludes pre-entry growth. Crossing outside and returning,
   while global growth stays constant there, preserves the same inside/global
   increment. Therefore deltaG_inside_virtual = deltaG_global modulo2^256.
5. For unchanged virtual L with one terminal position update, attributed fees
   per token are floor(L * deltaG_global / 2^128). Do not separately round every
   daily observation or credit historical pre-entry fees.

The virtual initialization/crossing conclusion is an inference from the linked
contract rules. Actual deployed bytecode and immutable spacing must still be
qualified before applying it to a historical pool.

## Scope limits retained

- Qualifying flash payments/donations are reflected in global fee growth;
  unsolicited token transfers do not automatically become distributable fees.
- Other positions' mint/burn activity changes liquidity but does not itself
  create global fee growth. Virtual liquidity changes or intermediate position
  updates/collections require their own accounting.
- Preserve modular growth subtraction and conservative owed-balance overflow
  rejection. An incorrectly joined/reset source counter is not a valid wrap.
- Added liquidity changes fee denominators and potentially swaps, prices and
  flash activity. It can enable activity during historical zero-liquidity
  intervals inside the range. The identity proves no counterfactual capacity or
  realized return for a $10,000 investor.
- Entry mint capacity, gas/costs, underlying inventory and liquidation remain
  separate requirements. The LP-versus-identical-held-inventory comparison is
  still necessary; attributed fees alone are not net profit.

## Consequence for the remaining research

Uninterrupted **historical** boundary-counter reconstruction is no longer a
necessary prerequisite for this exact full-range historical-path attribution.
It remains necessary for arbitrary ranges unless another valid proof supplies
their inside-growth history. Preserve all frozen Q1/Q2/R1 source captures and
unavailable boundary cells; this new reasoning does not relabel those cells.
The financial gate must identify whether it uses the conditional attribution
or a source-qualified counterfactual execution model before any outcome.

Sources:
[UniswapV3Pool](https://raw.githubusercontent.com/Uniswap/v3-core/main/contracts/UniswapV3Pool.sol),
[Tick](https://raw.githubusercontent.com/Uniswap/v3-core/main/contracts/libraries/Tick.sol).
