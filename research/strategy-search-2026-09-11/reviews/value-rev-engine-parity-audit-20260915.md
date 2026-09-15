# value_rev engine parity — source-only audit

September 15, 2026. **The legacy runner does not implement identical control pipelines for the four registered cells.** Moving the controls inside the breadth loop would correct only one of several differences. Financial/source admission remains unavailable; no empirical impact was measured.

Scope: the frozen September 4 charter, only `data/rebuild/gates.json:value_rev`, the September 15 pre-outcome interpretation and readiness review, and the directly called source functions were read. No raw market body, normalized panel, P0/P1/P2 result, historical financial output or ledger value was read. No legacy main, portfolio or financial engine was executed. This audit creates only this report. Numerical illustrations below are invented algebra, not executed books or empirical observations.

## Actual paths for cells and controls

All paths start with a static file-availability intersection of fundamentals, fee panels and klines (`scripts/value_rev_dev.py:83–95`). The daily calendar begins June 2020 and the evaluated slice is the frozen dev window. Neither a monthly universe nor a liquidity/age filter is called. The charter does not explicitly import those parent-strategy filters, so adding them would require clarification rather than an undocumented repair.

Let `M(t)` mean a nonmissing market-cap value on the decision date; `S_f/S_r` are two-day-shifted fee/revenue log-ratio z-scores; `C_v/C_r` are independently constructed control z-scores. Actual comparisons are:

| Registered value cell | Value-valid mask | Value leg fraction | C1/C2 used for its delta |
| --- | --- | --- | --- |
| fees / tercile | M AND S_f.notna | 1/3 | Two global decile books on M AND own control notna |
| fees / decile | Same fee mask | 0.1 | Same two global decile books |
| revenue / tercile | M AND S_r.notna | 1/3 | Same two global decile books |
| revenue / decile | Same revenue mask | 0.1 | Same two global decile books |

`notna` is the actual predicate; it does not itself enforce finite or positive values. The control books are computed once at lines 156–159, outside the cell loop at 163–180. The resulting two Sharpe numbers are reused for all four deltas at 175. There are consequently no metric-specific or tercile control portfolios in this implementation.

Shared downstream mechanics are real source facts: the `port` closure at 152–154 sends each path through `ls_weights`, the same return/funding matrices, 10 bp per side and `RF_DAILY`. They do not establish equivalence of the upstream masks or resulting rebalance schedules.

## Defects and unresolved contracts

### 1. Breadth and eligible universe both differ

Tercile value books are compared with decile controls, contrary to the registered identical-pipeline requirement. With 24 eligible names, the inherited rounding rule requests eight names per tercile leg versus two per decile leg; this is a different exposure/turnover construction, not an innocuous benchmark label.

Even a decile value cell has a different eligible universe from its controls. Missing or invalid 90-day denominator histories can exclude a token from value while its price history admits it to either control. Conversely, a missing 30-day price window can exclude a control name still admitted by the value mask. Fees and revenue can have different missingness. The current common column list does not make these date-specific masks identical.

The smallest correction is cell-paired controls with the same frozen breadth and matched decision universe. **The precise matching rule still needs registration:** for example, a joint intersection of admitted value/C1/C2 inputs per metric and date, versus declaring the comparison unavailable if a control is absent on the value universe. The charter requires identical pipelines but does not settle this missing-control policy. Computing each book on its own available subset cannot prove that requirement. A joint intersection would also change the breadth population and must be reflected in the ordered P1 interpretation; it cannot be installed after outcomes. The two controls can be reused across cells only when full universe, clocks, breadth and accounting input identities are proven equal.

### 2. Missingness can change holding schedules, including placebos

`ls_common.py:47–64` ranks `valid AND S.notna`, requires at least five names and skips a rebalance when that minimum fails. It records only successful rebalance dates; previous contracts remain held. Different control/value masks can therefore change not only names and leg counts but also rebalance execution dates and holding intervals.

The placebo wrappers at runner lines 169–170 retain the original value-valid mask. `circular_shift_columns` moves entire arrays including NaNs; `rank_shuffle_columns` permutes entire rows including NaNs (`scripts/value_xs_dev.py:372–390`). Intersecting either transformed signal with the old mask need not preserve the original eligible-name count. An invented row `[1,2,NA,NA]` with original validity `[true,true,false,false]` can shuffle to `[NA,NA,1,2]`, leaving zero usable original names despite two observed inputs. At larger breadth the same operation can cross the five-name threshold and suppress a rebalance.

This directly contradicts B's registered **count-matched** rank reassignment. B needs a fixed eligible index and permutation within that index, preserving scheduled decisions and leg counts. A's required circular-shift operation needs an explicit missingness/availability contract; silently replacing it with a different null is not authorized. Preserve 500 draws per family, the worse-p gate and four-cell trial denominator. A correction must retain all unavailable draws rather than reducing the denominator through successful-only selection.

### 3. Reversal meaning, sign and return aggregation are not interchangeable

The gate names C2 as `reversal (-30d return) sort`. Inherited `value_xs.control_signal:88–105` uses the **positive sum of 30 simple daily returns**, standardizes it and then shorts high values via `ls_weights`. That produces the intended economic direction of short recent winners and long recent losers. Simply negating this score would instead short losers under the same high-is-short convention.

Separately, a sum of daily simple returns is not a compounded 30-day return; the distinction can change rankings. These are two distinct questions: economic long/short orientation and the registered lookback-return definition. The parent function's existing implementation does not resolve the gate's literal minus sign. Freeze the intended C2 contract before changing code. Do not introduce a momentum control accidentally, and do not describe summed simple returns as a compounded holding-period return.

C1 uses sample standard deviation of 30 complete daily simple returns and both inherited controls use a fixed default two-day lag. Value instead uses the runner's `LAG`. If P2 triggers the charter's logged widening route, changing only `LAG` widens value but leaves both controls at two days unless the common lag is passed explicitly. This is a prospective parity defect, not evidence that widening has occurred.

### 4. Accounting is shared, but its limitations must remain explicit

`carry_xs.run_ls_portfolio:73–86` recognizes successful rebalance metadata, suppresses non-rebalance targets and shifts targets by one day. `accounting.run_target_book:112–153` then holds signed contracts between explicit instructions. Thus a Monday-close decision becomes effective on the following daily bar. This follows the inherited machinery's stated timing; the short charter phrase “weekly Monday” alone should not be rewritten as a different execution clock.

`ls_weights` allocates +0.5/-0.5 at a successful target, with equal weights within each leg. There is no separate BTC/ETH beta hedge or continuous neutrality maintenance. Signed marked notionals drift between rebalances. All books share that mechanism, but dollar neutrality at targets does not prove persistently low crypto-market exposure.

The shared accounting uses simple returns, signed position PnL, turnover fees against pretrade NAV and a single full-NAV capital charge `1.045**(1/365)-1` per daily bar. Missing held returns or supplied missing held funding raise errors (`accounting.py:29–46`); the current inspected code does not silently zero those held inputs. No claim is made here about old results produced before this accounting source version.

However, the runner's funding adapter (`value_rev_dev.py:104–113`) sums provider rows by UTC day. Default summation can turn an all-NaN group into zero, partial/missing within-day prints are not checked against an expected event denominator, and duplicate prints are not independently rejected. Applying the daily sum to one daily marked notional is not an event-level reconstruction of funding if prices or holdings change within that day. This is common to all paths, but common treatment does not establish complete or correctly valued realized funding. Freeze a supported event/completeness contract or retain the approximation as insufficient for financial admission; no silent zero-funding or substitution is allowed.

`run_ls_portfolio` unconditionally returns `result.net.iloc[1:]`. The first requested dev day is therefore absent from every scored path even though accounting processes its capital charge. Exact calendar accounting needs an explicit warm-up/anchor row outside the scored window or retention of that first dev row; identical truncation across controls is not a full-span proof. There is no explicit terminal liquidation target at the dev endpoint. Marked continuation versus closed-book terminal fees needs a declared endpoint convention; this audit does not impose a new close policy.

### 5. Upstream validity and durable result admission remain prerequisites

Current `M` is same-date market-cap nonmissingness, while the value signal is lagged. It is not proof of contemporaneous publication availability, positive/finite market cap or tradable price/funding support. The existing `.fillna(0)` denominator defect and source/stage identity problems remain as documented in the pre-outcome review. No engine comparison repairs those source defects.

The one-shot grid guard checks only final `grid.json`. Earlier cells can already have been logged when a later cell or placebo raises; the final file is written only after all cells. No immutable per-cell intent/resume binding is present. Shared missing-data exceptions can therefore leave a partially spent grid without its final grid artifact. The additive implementation needs retained failed/unavailable cells and attempt identity before calculation, not an empirical rerun of the legacy main. Hardcoded thresholds currently match the named gate but the declared `GATES` path is not used to bind admission.

## Smallest justified additive engineering step

Do not patch or run the legacy runner. The unresolved matching, C2 orientation/aggregation, common lag, funding and endpoint conventions require independent review and registration before empirical admission. Numerical thresholds, four metric/breadth cells and multiplicity remain unchanged. Pure assembly validation can be implemented now without resolving those choices.

Add a small, isolated **pure control-assembly helper** on invented inputs. The caller supplies each registered metric/breadth identity, exact metric-eligible names by scheduled date, proposed breadth and decision schedule, explicit high/low long-short orientation for each supplied signal, and one common frozen execution-input reference (calendar, lag/action clocks, return-input identity, funding-input identity, fee and capital-charge policy identity). The helper does not calculate a ratio, choose a universe/intersection, infer a reversal sign, widen a lag, aggregate funding or compute a return.

Restrict each supplied control to the caller's explicit metric cohort; if required signal coverage, dimensions, date identities or execution references fail to align, return a clearly unavailable comparison rather than shrinking the cohort or replacing a control. Preserve the requested cell and both control roles in output. Emit paired control assembly descriptions with identical supplied breadth, cohort and execution contract. Invalid/missing orientation is unavailable, not a guessed default. Any successful result remains `readiness-only; pending registered interpretation`, with source/financial admission false: accepting caller-supplied contracts does not establish their provenance or that unresolved choices have been approved.

Implement this as one narrow pure module plus synthetic tests, not a framework or full legacy rewrite. Immediate tests can check metric-specific masks, differing breadth, explicit orientation retention, missing required control names, mismatched clock/cost/funding references, deterministic identity, and complete unavailable-role retention. No actual return arrays, source fetcher, portfolio, P0 stage, ledger or original main is needed. More detailed rank/count/holding tests can follow only when their contracts are frozen.

Meaningful synthetic cases are: unequal fee/revenue coverage; a missing control history; tercile versus decile rounding; the five-name threshold and held-contract schedule; NaN permutations preserving B's exact eligible counts; widened lag applied to all roles; known winner/loser orientation; compounded-return versus daily-sum ordering; first/last dev dates; missing/duplicate funding events. Subsequent signed-contract accounting verification belongs to a separately bounded additive adapter after those contracts are frozen. This is engineering preparation, not a new financial-research allowance.

## Inspected source pins

| Source | SHA-256 |
| --- | --- |
| `scripts/value_rev_dev.py` | `cad50077e4a6f7a807e282541094ae1e1e025ebefc92e77fb07e75571d7a29d2` |
| `tradingagents/xsect/ls_common.py` | `f2c1d2c50dc0f2b38a9d68b2b7762db6aed86280aaf1ccf44bc4fc1bc13472c5` |
| `tradingagents/xsect/value_xs.py` | `9f4dbac14a5f8ff4f216f5d79f8d39749f26530db4609d9ade1c1c136e1c1ed1` |
| `tradingagents/xsect/carry_xs.py` | `f603d19ae7dbb52c99a8e6ed24dbd975cff8395f0b74a2452d4067967253c103` |
| `tradingagents/accounting.py` | `4ed1f01dda1b17ed3fe413996413704b6810af383ac1beb4a0acfeca226d4d3c` |
| `scripts/value_xs_dev.py` | `498dc275138b7c9e4d56f12849766b8084db014c2e4773178b36ae7ce753ed0e` |
| September 4 charter | `9a4fdb142af4ad259d3485bcb00fa4e704262b9246b14660b5e8d7710ab0252a` |
| Named gate object, sorted compact JSON | `01cb96c80f16b4df5cee5787441bbe47ade1741896ae3043b49eb1d8240c127b` |

No execution-based parity proof was attempted: the observed source differences already refute identical pipelines, and the unresolved contracts must precede an implementation. The readiness helper's earlier 20 synthetic tests and independent review cover source/stage readiness only, not this engine.
