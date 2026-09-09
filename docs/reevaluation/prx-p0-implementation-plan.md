# PRX P0 Reevaluation Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this plan task-by-task after the new gate is committed. Steps use checkbox syntax. The parent coordinates commits and empirical execution.

**Goal:** Produce one provenance-pinned, development-only correction of the original PRX persistence diagnostic, without invoking either P1 engine.

**Architecture:** A new entry point has pure formation/month/scoring functions and an explicit read-only loader. It reuses the established AR(1), ADF and stationary-bootstrap primitives, but never calls the legacy PRX `main`, cache-building loaders, pair backtest, or shared registry mutation. All 50 monthly records survive to the output even when empty/incomplete.

**Tech Stack:** Python 3.13.13 from the sibling predlab environment, numpy/pandas, statsmodels `coint`, scipy Wilcoxon, existing `meanstats.stationary_bootstrap_means`, pytest.

**Spec:** `docs/reevaluation/triage-statistics-execution.md`, original `docs/superpowers/specs/2026-08-25-xfam-hunt-charter.md`, and committed `docs/superpowers/specs/2026-09-09-lead-reevaluation.md` / `gates.json[audit_reevaluation_2026_09_09]` (initial gate commit e3c0d63). The common RunContext owns provenance and output namespace. No empirical call is permitted until reviewed executable source is committed.

## Global constraints

- Own only `scripts/audit_reevaluate_prx_2026_09_09.py` and `tests/predlab/test_audit_reevaluate_prx.py`; no shared-registry edits.
- Months are exactly `pd.date_range('2021-01-01','2025-02-01',freq='MS',tz='UTC')`: 50 planned monthly evaluations. March2025 and all holdout dates are excluded.
- Formation is the preceding90 calendar days through month-start−1day; input warmup starts2020-10-03. Universe is top50 by that window's median quote volume. Pair ordering, seed42, top20 cap, half-life2–20 and max200 random attempts remain frozen.
- `coint(a,b,trend='c',maxlag=5,autolag=None)` supplies formation p; threshold strictly<.05. Next-month frozen-beta spread uses ordinary ADF with maxlag5/autolagNone, minimum25 observations and threshold<.10.
- Missing measurements are labelled; no implicit zero or dropped month. No automatic P1, ETHBTC trading, grid expansion, refitting, new data or holdout claim.
- Original ratio≥1.5 and Wilcoxon p<.05 are historical conditional diagnostics. Stationary-bootstrap paired-mean sensitivity uses mean block3, B2000, seed4242. Neither method selects, promotes or validates a strategy.

## Task 1: Pure monthly diagnostic and fixed-clock regressions

**Files:** Create the new script and test file above.

**Interfaces:**

```python
MONTHS: pd.DatetimeIndex

def formation_pairs(close: pd.DataFrame, qv: pd.DataFrame,
                    month: pd.Timestamp) -> dict: ...
def score_month(close: pd.DataFrame, qv: pd.DataFrame,
                month: pd.Timestamp, rng: np.random.Generator) -> dict: ...
def summarize_months(rows: list[dict]) -> dict: ...
def evaluate_p0(close: pd.DataFrame, qv: pd.DataFrame) -> dict: ...
```

- [ ] Write regression tests before implementation. Use synthetic independent random walks where ordinary residual ADF and augmented EG differ; compare formation p directly to `statsmodels.coint`, and spy on the exact trend/lag/autolag arguments. Do not use saved empirical outcomes as expected values.
- [ ] Add a future-data mutation test: modify prices/qv after a specified formation date and verify formation pairs/beta are identical. Modify rows after February2025 and verify the entire bounded result is identical. Verify pre2021 warmup is retained and that `len(MONTHS)==50`, endpoints are2021-01-01/2025-02-01.
- [ ] Add explicit empty and incomplete-month fixtures. Each row records month, top-universe count, formation candidates/test failures, selected count, selected scoreable/unavailable counts, random attempts/scoreable count, selected/random rates or null, paired difference or null and status. Exactly50 rows are returned regardless of missing prices or no selected pairs. An unavailable selected measurement is not scored false or removed without a count.
- [ ] Add fixed-RNG fixtures: seed42 reproduces pair attempts across months; selection results do not change the random draw stream except through the frozen random-arm retry logic. Report repeated/reversed random pairs without replacing them.
- [ ] Run the new tests and preserve the failing output in the parent-approved verification directory. The command is `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. ../TradingAgents-predlab/.venv/bin/python -m pytest tests/predlab/test_audit_reevaluate_prx.py -q -p no:cacheprovider`.
- [ ] Implement the pure functions. No pandas `dropna()` over the monthly result clock; only explicit per-pair observation masks with reported counts. Catch numerical fit/test failures as unavailable records. The original fixed-beta OOS statistic does not re-estimate beta during the scored month.
- [ ] For complete monthly pairs, report the historical equal-month selected/random means, their ratio, the paired one-sided Wilcoxon p, and the old compound flag under a key explicitly labelled `historical_conditional_gate`. Define all-zero paired differences as p=1; preserve the original max(random_mean,1e-9) denominator and explicitly flag a zero random baseline.
- [ ] Bootstrap chronological monthly `selected_rate-random_rate` using `stationary_bootstrap_means(x,n_boot=2000,mean_block=3,seed=4242)`; report observed mean, percentile95% interval and fraction of bootstrap means>0, explicitly not a posterior probability or strategy gate. Never choose between it and Wilcoxon.
- [ ] If any planned month lacks a complete paired measurement, keep the50-row calendar and mark the aggregate incomplete. Do not compress the bootstrap calendar. Available-only rates may be shown as conditional diagnostics with their n, but no all50 inference or gate satisfaction is asserted. Final coverage policy must match the committed parent gate.
- [ ] Run the focused suite green and inspect the diff. No empirical entry-point invocation.

## Task 2: Read-only entry point, provenance and no-P1 boundary

**Interfaces:**

```python
def load_inputs(data_root: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict]: ...
def main(argv: list[str] | None = None) -> int: ...
```

- [ ] Add red tests proving a missing source stops execution before output, out-of-window Parquet rows never reach scoring, gate/window mismatch stops, and an existing output is never overwritten. Fixture result/provenance contains source commit, gate/correction-policy hashes and input SHA-256 values.
- [ ] Add a no-P1 regression: patch any legacy pair-backtest entry to raise; even a synthetic historical-P0 pass produces only persistence diagnostics. Assert explicit `strategy_validation=false`, `candidate_selected=false`, `forecast_models_refit=false` and `formation_regressions_recomputed=true`, `holdout_read=false` and `p1_executed=false`.
- [ ] Implement the CLI using existing read-only preflight/provenance utilities after inspecting their committed interfaces. Require the exact newly committed gate identifier and window; refuse uncommitted executable/gate/policy files through shared preflight. Read the original t7 close/qv Parquet files directly with date filtering2020-10-03→2025-02-28; never invoke `build_panels`, create source directories or write source caches. Hash original files read-only.
- [ ] Emit one exclusively-created JSON result under the registered new output namespace. Include all50 month records, frozen parameters, incomplete reasons and both labelled diagnostic summaries. Keep original result/ledger/gates untouched. The parent handles any append-only evidence integration after review.
- [ ] Run focused tests and the impacted existing `test_audit_evidence.py` and `test_xfam_lib.py` tests; inspect `git diff --check`. Submit implementation and tests to the parent for review/commit. Only the parent-authorised invocation after commit may evaluate actual pairs.

## Review checks

The final review must verify exact50-month support, causal formation warmup, estimated-residual null, immutable random seed, explicit unavailable denominators, unchanged legacy comparator and fixed bootstrap sensitivity. A numerical pass remains a lead for a separately registered trading protocol, never automatic strategy validation.

## Implementation verification (no empirical execution)

The assigned script and tests are implemented. Eleven initial regressions failed because the new module was absent; four further integration/edge-case regressions failed before their implementation; the zero-random-baseline regression separately failed before restoring the exact original denominator floor. Final focused suite:16 passed. Related PRX, evidence, XFAM and shared-context suite:58 passed in3.61s. Logs are `docs/reevaluation/verification/prx-red.log`, `prx-integration-red.log`, `prx-zero-baseline-red.log`, `prx-green.log`, and `prx-related-green.log`. `git diff --check` passed.

The wrapper reads only the original t7 daily close/qv caches, filtered before materialisation from2020-10-03 through2025-02-28, and hashes the saved original PRX result. It writes a50-row `monthly.parquet` plus full pair/attempt details in result JSON through RunContext. The single registered cell is retained on absent/invalid input as blocked. Empty/partial months leave the complete-panel comparison and chronological bootstrap unavailable; conditional historical rates remain labelled with their denominator. Bootstrap reports fixed-block sensitivity, not a posterior or a promotion gate. Metadata distinguishes the intrinsic recomputed formation regressions from forecast-model retraining. No legacy PRX main or P1 engine is reachable.

All tests use synthetic frames or temporary Parquet files; registry preflight/logging is stubbed only at the external boundary for real RunContext integration tests. No source market observations were evaluated, no gate/shared registry edited, and no commit performed by this owner. Actual-data execution remains pending the parent-reviewed executable commit.

## Final execution-fence and common-code review

Root review added an explicit `--execute` CLI fence. Default/help invocations do not construct RunContext, read inputs or consume the one-shot marker. The CLI has no data-root override; the wrapper obtains the original predlab root from the committed gate and rejects a mismatching programmatic override before reads. Calendar progress prints only completed month counts at5-month intervals; it never prints or acts on partial gate results. The callback does not change the pure calculation.

New regressions were recorded red in `prx-cli-red.log` (default invocation and replacement-root failures) and `prx-progress-red.log`. Final PRX/common suite:30 passed in2.70s (`prx-cli-common-green.log`). This includes20 PRX tests and10 shared-context tests. The unchanged evidence/XFAM suite had already passed in the58-test related run. Diff check passed; no empirical execution or commits.

Independent review of `audit_reeval_common.py` and its tests found the preflight/start ordering, exclusive run directory, Parquet date pushdown, resolved registered-root containment, before/after input and source checks, exact cell denominator and locked ledger append consistent with this charter. A remaining durability limitation was reported to the parent: ledger rows are appended before final JSON publication, so interrupted I/O can leave partial ledger evidence plus an unfinished marker. That state is not reported complete, and the exclusive marker prevents an automatic rerun; any such failure requires identity-aware recovery. No shared source was edited by this owner.
