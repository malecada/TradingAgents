# Original value_rev null contract — bounded source audit

September 15, 2026. The original implementation's statistic, tail, finite-simulation formula, random stream and transformation index are now source-verified. **A shifts full daily dev rows, not the scheduled Monday decision index.** Moving the proposed A transform to weekly rows would be a material amendment; no such amendment or empirical inference is adopted by this audit.

Only the directly named source ranges and their constants/imports/calendar definition were inspected. No raw market body, panel, financial outcome, engine or external request was used. No historical source, gate or ledger was changed. Only this report was written. This is implementation evidence, not a calibration proof or source/financial admission.

## Exact observed source contract

| Component | Source-supported behavior |
| --- | --- |
| Dev index | `value_rev_dev.py:88` constructs UTC daily dates from June 1, 2020; `main_grid:145–149` selects every date from January 1, 2021 through March 31, 2025 inclusive. Signal S is sliced to that full daily dev index. Monday rebalances are passed separately to the portfolio function. |
| Statistic | `ls_common.py:67–75`, imported directly by the runner: daily portfolio return series, `dropna`, sample standard deviation `ddof=1`, mean/std multiplied by sqrt(365). Fewer than two observations, nonfinite standard deviation or zero standard deviation returns 0.0. This is the actual implementation, not a claim that dropping incomplete scored days is admissible. |
| Tail and formula | `portfolio.py:93–96`: count every supplied placebo statistic satisfying `p >= real_sr`, including ties; return `(1 + count) / (len(placebo_srs) + 1)`. No finite-value or exact-count validation occurs in this helper. |
| Draw count and gate | `value_rev_dev.py:42–46,169–176`: 500 A and 500 B statistics per cell; worse p is `max(pA,pB)` and compared inclusively with 0.05. |
| Cell/stream order | GRID is fees-tercile, fees-decile, revenue-tercile, revenue-decile. A single `np.random.default_rng(20260904)` is created before the grid loop. Within each cell all 500 A draws consume that stream, followed by all 500 B draws. It is not reset per cell or family, and breadths do not share a realized randomized panel. |
| A | `value_xs_dev.py:372–380`: loop through columns in their current order; draw an integer k uniformly from 1 through n-1 when n>1, otherwise k=0; `np.roll` the whole column by k, preserving the index and moving missingness with values. Here n is the number of full DAILY dev rows. Each draw uses a new offset per column. |
| B | `value_xs_dev.py:383–390`: for every row, shuffle an index over ALL columns and assign the permuted row, including any NaNs and any originally ineligible columns. |
| Validity after transform | Both nulls are passed with the original `M & S.notna()` validity mask. The ranker intersects that with transformed nonmissing scores. This can alter eligible counts and trigger its old minimum-name skip/holding behavior. It does not meet the subsequently proposed fixed-cohort unavailable contract; B does not ensure the charter's count-matching requirement. |

The stream's reproducibility also depends on the exact input shape, column/date order, NumPy generator implementation and call consumption. A changed B eligibility recipe, weekly A index, retained failure path or shared-breadth transform can change downstream random draws even if the numeric seed is unchanged. The new preparation policy's shared panel across breadths is an explicit new coupling, not the inherited stream. Any future source-pinned recipe must say which coupling it implements; it cannot claim byte-identical replay of the old one.

## Concrete limits and failure examples

An offset of one daily row can move a Sunday signal onto a Monday rebalance. An offset of one row in a Monday-only panel instead moves the preceding week's Monday. Their periodicity, missingness movement and induced temporal dependence differ. The earlier considered scheduled-decision-index proposal therefore cannot be called a faithful implementation repair of original A. Neither transformation uses holdout rows in the inspected code, because S was already sliced to dev.

The p helper does not turn invalid values into explicit unavailable draw records. Under ordinary numeric comparison, NaN >= a finite observed statistic is false; a list of 500 NaNs would therefore give 1/501 rather than an unavailable p result. NaN observed statistics also make each such comparison false. An empty list gives 1. These are direct algebraic consequences of the source, not executed empirical tests. Separately, the statistic's zero fallback can conceal undefined or incomplete paths before the p helper sees them. Correcting finite/full-span admission must retain these failures and their fixed draw identities; it is not permission to score a successful subset.

The plus-one formula, >= tie convention and fixed 500 count can be recorded as inherited numerical choices. Their presence does not prove exchangeability or a calibrated test for independent nonzero per-symbol circular shifts. The missingness/universe conditioning, exclusion of zero offsets, nonstationarity and altered cross-symbol dependence remain the scientific issues documented in the [null preparation review](value-rev-null-endpoint-preparation-review-20260915.md). No generic formula change resolves them.

## Smallest remaining work

1. Bind these exact source facts into the next pre-outcome inference decision. Keep original numerical gates and four-cell/cumulative accounting; distinguish inherited daily A from any proposed weekly replacement. The current [control policy](../value-rev-control-policy-20260915.md) correctly leaves A unadopted.
2. Review a concrete DAILY circular-shift law under the fixed-cohort and source-availability constraints, including whether its assumptions support the intended inference. If that cannot be justified without changing the registered question, retain explicit A deferral. Do not automatically switch to weekly shifts, successful-only offsets, complete-case cohorts or a new block null.
3. Before any draws, freeze the generator/version, ordering, domain/coupling rules, 500 identities and durable failure behavior. Retain the source-supported statistic/tail/formula only with explicit full-span finite-input admission; undefined statistics and unavailable paths block a complete gate. Reproducibility and calibration are separate requirements.
4. Pure invented transformation/count/invalid-statistic checks become meaningful after that contract is settled. They need no financial engine, new empirical allowance or market request. Source day semantics, actual vintage clocks, P0/P1/P2 and event-funding admission remain independent blockers.

No broad inference platform, alternate strategy search or financial replay is proposed. This finite source audit closes the unknown-original-formula question while preserving the unresolved scientific boundary.

## Useful bounded next preparation question

A finite exact calibration counterexample is useful now because it can distinguish an actual limitation of nonzero sampling plus the inherited formula from a generic warning about nonstationarity. It requires no market data, portfolio or simulation platform. The question is: **does sampling 500 nonzero circular offsets with replacement and applying `(1+ge)/501` control a 5% rejection rate even under an invented uniform-phase circular null?**

Use one invented six-position circular vector with distinct phases. Let the null observation be uniform over its six phases, and define a fixed abstract statistic equal to 1 at one designated phase and 0 at the other five. This statistic is an algebraic ranking witness, not Sharpe or a trading result. When the designated phase is observed, every permitted nonzero shift has statistic 0; all 500 draws therefore give p=1/501, deterministically, although that observation occurs with probability 1/6 under the uniform-phase null. This exposes that omitting the observed phase and repeatedly sampling only the other phases can yield an anti-conservative Monte Carlo formula on a small finite orbit. The plus-one constant does not substitute for sampling the complete transformation law. It does not prove that the actual daily value_rev Sharpe null has the same rejection rate or that every circular-shift test fails.

A bounded follow-up could independently enumerate exactly six observation phases and five allowed offsets per phase, compare the inherited rule with full-orbit rank including the observed phase, and retain all 30 abstract comparisons. Stop after verifying or refuting that one stated counterexample and documenting its limited relevance; do not tune T, a statistic or a trading strategy, run real source arrays, or extend it into an empirical rejection-rate search. This would support a specific inference-design correction or continued deferral, not authorize a replacement null. No such calculation or code was executed by this report.

## Inspected source pins

| File | SHA-256 |
| --- | --- |
| `scripts/value_rev_dev.py` | `cad50077e4a6f7a807e282541094ae1e1e025ebefc92e77fb07e75571d7a29d2` |
| `scripts/value_xs_dev.py` | `498dc275138b7c9e4d56f12849766b8084db014c2e4773178b36ae7ce753ed0e` |
| `tradingagents/xsect/ls_common.py` | `f2c1d2c50dc0f2b38a9d68b2b7762db6aed86280aaf1ccf44bc4fc1bc13472c5` |
| `tradingagents/xsect/portfolio.py` | `e720f6a71d1748791fe4bdc6f8bceae82b6842bbcf1e60ae99dba0ecd123831c` |

## Independent validation of the retained abstract witness

The coordinator subsequently executed the sole proposed witness in [value-rev-abstract-null-counterexample-20260915.json](value-rev-abstract-null-counterexample-20260915.json), SHA-256 `fc3344c8a4e96b893e7b35c114114e38b43970e1f05dbdde18605a974bc31416`. An independent exact-rational check reconstructed all 30 comparisons as statistic `1[(phase-offset) mod 6 = 0]`, verified six observation phases, 500 balanced illustrative draws per phase, the inherited >= tail and every recorded verdict. All checks passed: the designated phase gives 1/501, every other phase gives 1, and uniform observation yields rejection probability 1/6 > 1/20.

The balanced repetition is an illustration, not a claim of a sampled IID realization. The conclusion holds for any sequence of permitted nonzero offsets: at the high phase all comparisons fail the >= tail, and at every low phase all comparisons satisfy it. This validates the stated counterexample to universal finite-orbit calibration; it does not measure actual Sharpe or value_rev calibration, adopt a replacement null, or grant an empirical run. No additional experiment was performed. This bounded witness review is complete.
