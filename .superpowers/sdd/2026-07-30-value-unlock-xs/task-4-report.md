# Task 4 Report: Monthly PIT universe for the value cross-section

## What was implemented

- `scripts/value_xs_universe.py` — builder script that intersects the monthly
  top-150 liquidity floor (`monthly_top_n(daily, "2021-01-01", "2025-03-31", n=150)`,
  `lookback` and `min_age_days` left at their defaults) with the 63 value
  candidates from `ASSET_TO_SYMBOL` (Task 3), and writes
  `data/xsect/value_xs_universe.json` as `{month_start_iso: [symbol, ...]}`.
- `tests/xsect/test_value_xs.py` — appended the four tests from the brief
  verbatim (shape, subset-of-candidates, holdout-margin, median-breadth-floor),
  without touching the 8 tests already present from Task 3.
- `data/xsect/value_xs_universe.json` — the generated universe file (51 months,
  2021-01-01 → 2025-03-01).

One deviation from the brief's literal script, made because the code as
written cannot run: `monthly_top_n()` returns a dict keyed by `pd.Timestamp`,
and `json.dumps` raises `TypeError: keys must be str, int, float, bool or
None, not Timestamp` on such a dict — confirmed directly before writing the
fix. The sibling script `scripts/liq_fade_universe.py` (which built the
already-tracked `data/xsect/liq_fade_universe.json` the tests compare shape
against) handles exactly this by converting keys with `str(k.date())`. I
applied the same one-line convention:

```python
out = {str(month.date()): sorted(set(syms) & allowed) for month, syms in liquid.items()}
```

instead of the brief's `out = {month: sorted(set(syms) & allowed) for month, syms in liquid.items()}`.
Nothing else in the builder or in the floor/window/lookback/min_age_days
values was changed from the brief.

## TDD evidence

**RED** — command:
```
uv run --no-sync python -m pytest tests/xsect/test_value_xs.py -k universe -v
```
Output (tail):
```
FAILED tests/xsect/test_value_xs.py::test_universe_file_shape - FileNotFoundError: [Errno 2] No such file or directory: '.../data/xsect/value_xs_universe.json'
FAILED tests/xsect/test_value_xs.py::test_universe_is_subset_of_value_candidates
FAILED tests/xsect/test_value_xs.py::test_universe_never_reaches_into_holdout
================== 3 failed, 1 passed, 8 deselected in 0.39s ===================
```
The 4th new test (`test_median_breadth_meets_registered_floor`) doesn't
contain "universe" in its name so `-k universe` didn't select it; the other
one that passed (`test_universe_cache_used_without_network_call`) is a
pre-existing Task-3 test unrelated to this builder. All three failures are
exactly the expected cause: the universe file does not exist yet.

**GREEN** — command:
```
uv run --no-sync python -m pytest tests/xsect/test_value_xs.py -v
```
Output (tail):
```
tests/xsect/test_value_xs.py::test_candidate_count_matches_registration PASSED
tests/xsect/test_value_xs.py::test_no_stablecoin_or_pegged_names PASSED
tests/xsect/test_value_xs.py::test_every_asset_maps_to_a_perp_symbol PASSED
tests/xsect/test_value_xs.py::test_mapped_symbols_exist_in_the_perp_store PASSED
tests/xsect/test_value_xs.py::test_write_vintage_records_date_and_source PASSED
tests/xsect/test_value_xs.py::test_empty_fetch_asset_round_trips_datetimeindex PASSED
tests/xsect/test_value_xs.py::test_end_past_holdout_margin_is_rejected PASSED
tests/xsect/test_value_xs.py::test_universe_cache_used_without_network_call PASSED
tests/xsect/test_value_xs.py::test_universe_file_shape PASSED
tests/xsect/test_value_xs.py::test_universe_is_subset_of_value_candidates PASSED
tests/xsect/test_value_xs.py::test_universe_never_reaches_into_holdout PASSED
tests/xsect/test_value_xs.py::test_median_breadth_meets_registered_floor PASSED

============================== 12 passed in 0.30s ==============================
```
(The brief's Step 5 said "Expected: 9 passed" — that's stale; Task 3 already
left 8 tests in the file before this task started, +4 new = 12. No warnings,
pristine output.)

Full suite before commit:
```
uv run --no-sync python -m pytest -q
```
```
FAILED tests/execution/live/test_parity_script.py::test_parity_routes_cover_four_v5_coins
FAILED tests/execution/live/test_parity_script.py::test_regenerate_predictions_builds_routing_to_sandbox
FAILED tests/execution/live/test_runner_ban.py::test_run_cycle_catches_BinanceIPBan_and_alerts_BAN
3 failed, 788 passed, 3 skipped, 1 deselected, 796 warnings, 27 subtests passed in 165.41s (0:02:45)
```
These are exactly the three pre-existing, unrelated failures called out in
the task instructions. No new failures were introduced. (The 796 warnings are
all pre-existing pandas/sklearn `FutureWarning`/`PerformanceWarning`/`UserWarning`
noise from unrelated modules (`onchain_features.py`, `model_utils.py`,
sklearn feature-name validation), not from anything touched in this task.)

## Step 4 build output (verbatim)

```
uv run --no-sync python scripts/value_xs_universe.py
months=51 breadth min/median/max=29/45/50
```

## Per-year breadth breakdown

| Year | months | min | median | max |
|------|--------|-----|--------|-----|
| 2021 | 12 | 40 | 44.5 | 45 |
| 2022 | 12 | 45 | 48.5 | 49 |
| 2023 | 12 | 43 | 47.5 | 50 |
| 2024 | 12 | 29 | 33.5 | 43 |
| 2025 | 3  | 31 | 34.0 | 39 |

Overall: 51 month keys, min/median/max = 29/45/50. First key `2021-01-01`,
last key `2025-03-01`. No year comes anywhere close to the 20-name floor;
2024 is the thinnest year (still 29 min / 33.5 median) — plausibly reflecting
new-listing dilution of the top-150 liquidity ranks as the perp universe grew,
not a candidate-coverage problem.

## Verdict

**No breadth STOP.** Realized median breadth (45) is more than double the
registered floor (20), and the worst single month (29, in 2024) is still
above the floor. The known gaps (3 zero-coverage assets `bnb`/`eos_eth`/`trx_eth`,
3 assets stopping in 2022–2023: `xtz`/`dot`/`bsv`) reduce the effective
candidate pool from 63 to 57, but the intersection with top-150 liquidity
still comfortably clears 20 names every single month in the 2021-01 →
2025-03 dev window.

## Files changed

- `/home/malecada/master_thesis/TradingAgents/scripts/value_xs_universe.py` (new)
- `/home/malecada/master_thesis/TradingAgents/tests/xsect/test_value_xs.py` (appended, 4 new tests, 8 existing untouched)
- `/home/malecada/master_thesis/TradingAgents/data/xsect/value_xs_universe.json` (new, generated; force-added past `.gitignore` to match the existing convention used by `data/xsect/liq_fade_universe.json`, `data/rebuild/gates.json`, etc.)

Commit: `daa8e61` — `data(value-xs): monthly PIT universe, candidates INTERSECT top-150`

## Self-review

- **Completeness**: JSON shape confirmed identical to `liq_fade_universe.json`
  (`{"YYYY-MM-DD": [symbols...]}`, plain string keys, list-of-str values,
  `indent=1, sort_keys=True`). All four new tests appended after the last
  existing test; diff shows a pure append (31 insertions, 0 deletions/changes
  to the existing 8 tests).
- **Correctness**: every symbol in the output comes from `set(ranked_top_150) &
  set(ASSET_TO_SYMBOL.values())`, so by construction every symbol is both a
  value candidate and inside that month's top-150. Max key is `2025-03-01 <
  2025-04-01`, confirmed by test and by direct inspection — the file never
  reaches into the sealed holdout.
- **Discipline**: no floor, window, `n`, `lookback`, or `min_age_days` was
  tuned. The only deviation from the brief's literal code is the
  Timestamp-to-string key fix, which is necessary for the script to run at
  all (verified the crash directly) and follows the exact convention already
  established in the sibling script that built the file this task's shape
  test compares against. `gates.json` was not modified. Nothing was built
  beyond scripts/value_xs_universe.py + the 4 tests + the generated JSON.
- **Testing**: focused-file run is pristine (12 passed, 0 warnings). Full
  suite run before commit shows only the three pre-registered
  unrelated failures, no new ones.

## Concerns

None. Breadth clears the registered floor by a wide margin in every year of
the dev window; Phase B (the value_xs_t1 grid) is unblocked by this universe.

---

## Fix round 1/5

### Finding 1 (Important) — breadth gate test hardcoded the registered floor

Changed `test_median_breadth_meets_registered_floor` in
`tests/xsect/test_value_xs.py` to read `min_median_breadth` from
`data/rebuild/gates.json` (`gates["value_xs_t1"]["universe"]["min_median_breadth"]`)
instead of asserting against the literal `20`, mirroring the sibling pattern
already used by `test_candidate_count_matches_registration`:

```python
def test_median_breadth_meets_registered_floor():
    import statistics
    gates = json.loads((ROOT / "data" / "rebuild" / "gates.json").read_text())
    floor = gates["value_xs_t1"]["universe"]["min_median_breadth"]
    u = json.loads(UNIV.read_text())
    med = statistics.median(len(v) for v in u.values())
    assert med >= floor, f"breadth STOP: median {med} < registered floor {floor}"
```

`data/rebuild/gates.json` itself was not touched.

### Finding 2 (Minor) — printed median wrong for even-length populations

Changed `scripts/value_xs_universe.py` to import `statistics` and print
`statistics.median(sizes)` instead of `sorted(sizes)[len(sizes)//2]`, so the
printed figure always matches the true median (and therefore always matches
what the gate test computes), regardless of whether the month count is odd
or even. `data/xsect/value_xs_universe.json` was **not** regenerated (per
instruction, since it is already correct and a rerun would only churn the
diff); the fix was verified by AST-parsing the script and independently
confirming `statistics.median([1,2,3,4]) == 2.5` (the old `sorted(sizes)[len//2]`
would have printed `3`) while `statistics.median([1,2,3]) == 2` still matches
the old odd-case behavior — i.e. the change is a strict correctness fix with
no effect on the already-generated (odd, 51-month) output.

### Demonstrating the gate can genuinely fail

Per instruction, verified without mutating the real `data/rebuild/gates.json`
on disk. Method: wrote a standalone script (scratchpad only, not part of the
repo) that imports the real `tests.xsect.test_value_xs` module, builds a
scratch directory containing (a) a copy of the real `gates.json` with
`min_median_breadth` programmatically inflated in-memory to
`realized_median + 1 = 46`, and (b) an unmodified copy of the real
`value_xs_universe.json`; monkeypatches the test module's `ROOT`/`UNIV`
globals to point at that scratch directory via `pytest.MonkeyPatch`; then
calls the actual `tvx.test_median_breadth_meets_registered_floor()` function
directly (not a reimplementation) inside a try/except and confirms it raises
`AssertionError`. Before/after SHA-256 of the real `data/rebuild/gates.json`
on disk was compared to prove it was never written to.

Command:
```
uv run --no-sync python /tmp/.../scratchpad/gate_verify/verify_gate.py
```
Output:
```
real registered floor = 20, real realized median = 45
EXPECTED FAILURE (gate fired correctly): breadth STOP: median 45 < registered floor 46
real data/rebuild/gates.json byte-for-byte unchanged: True
scratch dir cleaned up
```
This confirms the test genuinely gates on the registration: at the real
floor (20) it passes, and if the registration were ever amended past the
realized median (46), the same code path — with a floor read live from
`gates.json` rather than a duplicated literal — would fail with an
informative message carrying both numbers, as Finding 1 required.

### Covering tests run (this fix round)

```
uv run --no-sync python -m pytest tests/xsect/test_value_xs.py -v
```
```
tests/xsect/test_value_xs.py::test_candidate_count_matches_registration PASSED
tests/xsect/test_value_xs.py::test_no_stablecoin_or_pegged_names PASSED
tests/xsect/test_value_xs.py::test_every_asset_maps_to_a_perp_symbol PASSED
tests/xsect/test_value_xs.py::test_mapped_symbols_exist_in_the_perp_store PASSED
tests/xsect/test_value_xs.py::test_write_vintage_records_date_and_source PASSED
tests/xsect/test_value_xs.py::test_empty_fetch_asset_round_trips_datetimeindex PASSED
tests/xsect/test_value_xs.py::test_end_past_holdout_margin_is_rejected PASSED
tests/xsect/test_value_xs.py::test_universe_cache_used_without_network_call PASSED
tests/xsect/test_value_xs.py::test_universe_file_shape PASSED
tests/xsect/test_value_xs.py::test_universe_is_subset_of_value_candidates PASSED
tests/xsect/test_value_xs.py::test_universe_never_reaches_into_holdout PASSED
tests/xsect/test_value_xs.py::test_median_breadth_meets_registered_floor PASSED

============================== 12 passed in 0.35s ==============================
```
Pristine, no warnings, no new failures. `git diff data/rebuild/gates.json`
and `git diff data/xsect/value_xs_universe.json` both confirmed empty before
committing — only `scripts/value_xs_universe.py` and
`tests/xsect/test_value_xs.py` were changed. Finding 2 (deferred: duplicate
function-scope `ASSET_TO_SYMBOL` import in
`test_universe_is_subset_of_value_candidates`) was left untouched, out of
scope for this round per instruction.

Commit: `eb4f5c9` — `test(value-xs): read breadth floor from gates.json, fix median print`
