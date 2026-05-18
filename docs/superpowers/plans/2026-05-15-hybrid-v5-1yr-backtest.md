# Hybrid V5 1-Year Backtest Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the hybrid quant+LLM modulator over the V5 MIX per-coin LGB routing for a 1-year backtest (BTC+ETH staged; +BNB+SOL conditional), producing a 4-way comparison vs pure-V2 quant, pure-V5 quant, and hybrid-V2.

**Architecture:** Reuse the existing modulator graph and `generate_hybrid_signals.py` / `backtest_hybrid.py` pipeline. Add a `V5QuantSignalProvider` that wraps the V2 engine but plumbs a per-coin `pool_map` (dict of `coin → pred_dir`) into `_load_pred_row`. Expose `--quant-version v5` + `--quant-pool-map COIN=PATH` CLI flags. No changes to the LLM analysts, modulator, or sizing logic — V5 only swaps which precomputed LGB CSV each coin reads.

**Tech Stack:** Python, pandas, pytest, existing TradingAgents hybrid graph, gpt-4o-mini via OpenAI API (replay-cache enabled), tmux on Hetzner VPS for long-running gen.

---

## File Structure

**New files:**
- `tests/strategies/test_v5_pool_map.py` — unit tests for per-coin routing
- `scripts/smoke_hybrid_v5.py` — single-day smoke before full run

**Modified files:**
- `tradingagents/strategies/quant_engine.py` — extend `_candidate_pred_dirs`, `_load_pred_row`, `get_quant_signal` to accept `pool_map`
- `tradingagents/strategies/quant_signal_provider.py` — add `V5QuantSignalProvider`, extend `build_provider("v5", pool_map=...)`, extend `set_active_quant_version`, extend `get_active_quant_signal`
- `scripts/generate_hybrid_signals.py` — add `--quant-version v5`, `--quant-pool-map` CLI flag, wire provider
- `scripts/backtest_hybrid.py` — add `--baseline-pool-map` so baseline equity for V5 routing is computed from the same per-coin pools

**Reused as-is (no changes):**
- `tradingagents/strategies/modulator.py`, `effective_weight.py`, `rolling_edge.py`, `contracts.py`
- `tradingagents/graph/trading_graph.py::propagate_with_modulator`
- `scripts/baseline_strategy_v2.py::run_coin_backtest`

---

## Data Inventory (verified on disk)

| Coin | Pool | Path | Date range |
|---|---|---|---|
| bitcoin | V2 78f | `data/multi_2coins_v2` | 2025-04-18 → 2026-04-15 (1y) |
| ethereum | V4-B 193f | `data/multi_2coins_pit_wf` | 2021-04-07 → 2026-04-14 (4.5y) |
| binancecoin | V2 78f | `data/multi_3coins_bnb` | check via Task 0 |
| solana | V4-B 193f | `data/wf_v5_sol_193f` | check via Task 0 |

Window: **2025-04-18 → 2026-04-15** (363 bars per coin, matches existing `data/hybrid_signals_v2_1y/`).

---

## Task 0: Pre-flight data verification

**Files:**
- None (verification only)

- [ ] **Step 1: Verify each pool covers the 1y window**

Run:
```bash
python3 -c "
import pandas as pd
pools = {
    'BTC@v2':   'data/multi_2coins_v2/preds_lgb_h7.csv',
    'ETH@v4b':  'data/multi_2coins_pit_wf/preds_lgb_h7.csv',
    'BNB@v2':   'data/multi_3coins_bnb/preds_lgb_h7.csv',
    'SOL@v4b':  'data/wf_v5_sol_193f/preds_lgb_h7.csv',
}
for name, p in pools.items():
    try:
        df = pd.read_csv(p, parse_dates=['date'])
        df['date'] = df['date'].dt.tz_localize(None).dt.normalize()
        coin = name.split('@')[0].lower().replace('btc','bitcoin').replace('eth','ethereum').replace('bnb','binancecoin').replace('sol','solana')
        sub = df[df['coin_id']==coin]
        in_window = sub[(sub['date']>='2025-04-18')&(sub['date']<='2026-04-15')]
        print(f'{name}: {p} -> {len(sub)} rows ({sub.date.min().date()}..{sub.date.max().date()}), in-window: {len(in_window)}')
    except FileNotFoundError:
        print(f'{name}: MISSING {p}')
"
```

Expected: BTC@v2 ≥360 in-window rows, ETH@v4b ≥360, BNB@v2 + SOL@v4b each ≥360 OR explicitly flagged MISSING (acceptable — 4-coin is conditional on Phase 2 results).

- [ ] **Step 2: Confirm hybrid signal cache exists for V2 comparison baseline**

Run:
```bash
ls -la data/hybrid_signals_v2_1y/ data/hybrid_backtest_v2_1y/summary.json
```
Expected: both present. If not, the V2 baseline must be regenerated separately — flag and stop.

---

## Task 1: V5 pool routing in `quant_engine.py`

**Files:**
- Modify: `tradingagents/strategies/quant_engine.py:36-72`
- Test: `tests/strategies/test_v5_pool_map.py` (new)

- [ ] **Step 1: Write failing test for per-coin pool_map routing**

Create `tests/strategies/test_v5_pool_map.py`:
```python
"""Tests for per-coin pool_map routing in the V2 quant engine."""

from __future__ import annotations

import pandas as pd
import pytest


def test_candidate_pred_dirs_pool_map_overrides_altcoin_default():
    from tradingagents.strategies.quant_engine import _candidate_pred_dirs

    out = _candidate_pred_dirs(
        "ethereum",
        base_dir="data/multi_2coins_v2",
        pool_map={"ethereum": "data/multi_2coins_pit_wf"},
    )
    assert out[0] == "data/multi_2coins_pit_wf", \
        f"pool_map override must be first candidate, got {out}"


def test_candidate_pred_dirs_pool_map_misses_coin_falls_back():
    from tradingagents.strategies.quant_engine import _candidate_pred_dirs

    out = _candidate_pred_dirs(
        "bitcoin",
        base_dir="data/multi_2coins_v2",
        pool_map={"ethereum": "data/multi_2coins_pit_wf"},
    )
    # BTC not in map -> normal candidates only
    assert "data/multi_2coins_v2" in out
    assert "data/multi_2coins_pit_wf" not in out


def test_candidate_pred_dirs_pool_map_none_is_back_compat():
    from tradingagents.strategies.quant_engine import _candidate_pred_dirs

    out_old = _candidate_pred_dirs("bitcoin", base_dir="data/multi_2coins_v2")
    out_new = _candidate_pred_dirs("bitcoin", base_dir="data/multi_2coins_v2", pool_map=None)
    assert out_old == out_new
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/strategies/test_v5_pool_map.py -v`

Expected: 3 FAILs with `TypeError: _candidate_pred_dirs() got an unexpected keyword argument 'pool_map'`.

- [ ] **Step 3: Extend `_candidate_pred_dirs`, `_load_pred_row`, `get_quant_signal` with `pool_map`**

In `tradingagents/strategies/quant_engine.py`, change the three function signatures and bodies:

```python
def _candidate_pred_dirs(
    coin: str,
    base_dir: Optional[str] = None,
    pool_map: Optional[dict[str, str]] = None,
) -> list[str]:
    """Search order for precomputed LGB pools.

    pool_map (per-coin override) wins over altcoin defaults wins over base_dir.
    """
    cfg = get_config() if base_dir is None else {"quant_pred_dir": base_dir}
    primary = cfg.get("quant_pred_dir", "data/multi_2coins_v2")
    candidates = [primary]
    altcoin_pools = {
        "binancecoin": "data/multi_3coins_bnb",
        "solana": "data/multi_3coins_sol",
        "ripple": "data/multi_3coins_xrp",
        "cardano": "data/multi_3coins_ada",
    }
    if coin in altcoin_pools:
        candidates.insert(0, altcoin_pools[coin])
    if pool_map and coin in pool_map:
        candidates.insert(0, pool_map[coin])
    return candidates


def _load_pred_row(
    coin: str,
    date: str,
    base_dir: Optional[str] = None,
    pool_map: Optional[dict[str, str]] = None,
) -> Optional[dict]:
    target_date = pd.to_datetime(date).normalize()
    for pred_dir in _candidate_pred_dirs(coin, base_dir, pool_map=pool_map):
        # ... rest unchanged ...
```

And `get_quant_signal`:
```python
def get_quant_signal(
    coin: str,
    date: str,
    base_dir: Optional[str] = None,
    pool_map: Optional[dict[str, str]] = None,
) -> QuantSignal:
    # ...
    pred = _load_pred_row(coin, date, base_dir, pool_map=pool_map)
    # ... rest unchanged ...
```

- [ ] **Step 4: Run tests to verify pass**

Run: `pytest tests/strategies/test_v5_pool_map.py -v`

Expected: 3 PASS.

- [ ] **Step 5: Run existing V2 tests to verify no regression**

Run: `pytest tests/strategies/test_quant_signal_provider.py tests/strategies/test_hybrid_quant_flag.py -v`

Expected: all PASS (back-compat — `pool_map` defaults to `None`).

- [ ] **Step 6: Commit**

```bash
git add tradingagents/strategies/quant_engine.py tests/strategies/test_v5_pool_map.py
git commit -m "feat(quant): per-coin pool_map override in V2 quant engine

Adds optional pool_map dict (coin -> pred_dir) to _candidate_pred_dirs,
_load_pred_row, get_quant_signal. Override wins over altcoin defaults
and base_dir. Back-compat: pool_map=None reproduces prior behavior.

Enables V5 MIX routing in the hybrid stack."
```

---

## Task 2: `V5QuantSignalProvider` in `quant_signal_provider.py`

**Files:**
- Modify: `tradingagents/strategies/quant_signal_provider.py`
- Test: `tests/strategies/test_v5_pool_map.py`

- [ ] **Step 1: Add failing test for V5 provider**

Append to `tests/strategies/test_v5_pool_map.py`:
```python
def test_v5_provider_passes_pool_map(monkeypatch):
    from tradingagents.strategies import quant_signal_provider as qsp
    from tradingagents.strategies.contracts import QuantSignal

    captured = {}
    def _fake_impl(coin, date, base_dir=None, pool_map=None):
        captured["call"] = (coin, date, base_dir, pool_map)
        return QuantSignal(
            coin=coin, direction="long", magnitude=0.5,
            regime="bull", regime_confidence=0.7, hurst=0.55,
            deterministic_signals={}, as_of_date=date,
        )
    monkeypatch.setattr(
        "tradingagents.strategies.quant_engine.get_quant_signal",
        _fake_impl,
    )

    provider = qsp.build_provider(
        "v5",
        pool_map={"ethereum": "data/multi_2coins_pit_wf"},
    )
    sig = provider.signal("ethereum", pd.Timestamp("2025-06-01"))
    assert sig.direction == "long"
    assert captured["call"][3] == {"ethereum": "data/multi_2coins_pit_wf"}


def test_build_provider_v5_requires_pool_map():
    from tradingagents.strategies.quant_signal_provider import build_provider
    with pytest.raises(ValueError, match="pool_map"):
        build_provider("v5")


def test_get_active_quant_signal_v5_uses_pool_map(monkeypatch):
    from tradingagents.strategies import quant_signal_provider as qsp
    from tradingagents.strategies.contracts import QuantSignal

    captured = {}
    def _fake_impl(coin, date, base_dir=None, pool_map=None):
        captured["pool_map"] = pool_map
        return QuantSignal(
            coin=coin, direction="flat", magnitude=0.0,
            regime="sideways", regime_confidence=0.5, hurst=0.5,
            deterministic_signals={}, as_of_date=date,
        )
    monkeypatch.setattr(
        "tradingagents.strategies.quant_engine.get_quant_signal",
        _fake_impl,
    )

    qsp.set_active_quant_version("v5", pool_map={"bitcoin": "p1", "ethereum": "p2"})
    try:
        qsp.get_active_quant_signal("bitcoin", pd.Timestamp("2025-06-01"))
        assert captured["pool_map"] == {"bitcoin": "p1", "ethereum": "p2"}
    finally:
        qsp.set_active_quant_version("v2")
```

- [ ] **Step 2: Run tests, verify FAIL**

Run: `pytest tests/strategies/test_v5_pool_map.py -v`

Expected: 3 new FAILs (`Unknown quant version: 'v5'`).

- [ ] **Step 3: Implement V5 provider**

In `tradingagents/strategies/quant_signal_provider.py`:

3a. Replace `_v2_get_quant_signal` to accept pool_map:
```python
def _v2_get_quant_signal(coin, date, base_dir=None, pool_map=None):
    from tradingagents.strategies.quant_engine import get_quant_signal as _impl
    return _impl(coin, date, base_dir, pool_map=pool_map)
```

3b. Update `V2QuantSignalProvider.signal` — no change to signature; keeps pool_map=None.

3c. Add new class after `V3QuantSignalProvider`:
```python
class V5QuantSignalProvider:
    """V5 provider: V2 engine + per-coin pool_map (route each coin to its own LGB CSV)."""

    def __init__(self, pool_map: dict[str, str], base_dir: Optional[str] = None) -> None:
        if not pool_map:
            raise ValueError("V5QuantSignalProvider requires non-empty pool_map")
        self.pool_map = dict(pool_map)
        self.base_dir = base_dir

    def signal(self, coin: str, as_of: pd.Timestamp) -> QuantSignal:
        date_str = pd.Timestamp(as_of).strftime("%Y-%m-%d")
        return _v2_get_quant_signal(
            coin=coin, date=date_str,
            base_dir=self.base_dir, pool_map=self.pool_map,
        )
```

3d. Extend `build_provider`:
```python
def build_provider(version: str, **kwargs) -> QuantSignalProvider:
    version = version.lower()
    if version == "v2":
        return V2QuantSignalProvider(base_dir=kwargs.get("base_dir"))
    if version == "v5":
        pool_map = kwargs.get("pool_map")
        if not pool_map:
            raise ValueError(
                "V5QuantSignalProvider missing required kwarg: pool_map"
            )
        return V5QuantSignalProvider(
            pool_map=pool_map, base_dir=kwargs.get("base_dir"),
        )
    if version == "v3":
        # ... existing v3 branch unchanged ...
    raise ValueError(f"Unknown quant version: {version!r} (expected 'v2', 'v3', or 'v5')")
```

3e. Extend module-level active-version state:
```python
_V5_POOL_MAP: Optional[dict[str, str]] = None
_V5_BASE_DIR: Optional[str] = None


def set_active_quant_version(version: str, *, pool_map=None, base_dir=None) -> None:
    global _ACTIVE_QUANT_VERSION, _V5_POOL_MAP, _V5_BASE_DIR
    version = version.lower()
    if version not in ("v2", "v3", "v5"):
        raise ValueError(f"Unknown quant version: {version!r}")
    if version == "v5" and not pool_map:
        raise ValueError("v5 requires pool_map={coin: pred_dir}")
    _ACTIVE_QUANT_VERSION = version
    _V5_POOL_MAP = dict(pool_map) if pool_map else None
    _V5_BASE_DIR = base_dir
    logger.info("Active quant version set to %s (pool_map=%s)", version, _V5_POOL_MAP)
```

3f. Extend `get_active_quant_signal`:
```python
def get_active_quant_signal(coin: str, as_of) -> QuantSignal:
    version = _ACTIVE_QUANT_VERSION
    as_of_ts = pd.Timestamp(as_of)
    if version == "v2":
        return V2QuantSignalProvider(base_dir=None).signal(coin=coin, as_of=as_of_ts)
    if version == "v5":
        return V5QuantSignalProvider(
            pool_map=_V5_POOL_MAP or {}, base_dir=_V5_BASE_DIR,
        ).signal(coin=coin, as_of=as_of_ts)
    if version == "v3":
        # ... existing v3 branch unchanged ...
    raise ValueError(f"Unknown active quant version: {version!r}")
```

- [ ] **Step 4: Run tests, verify pass**

Run: `pytest tests/strategies/test_v5_pool_map.py tests/strategies/test_quant_signal_provider.py tests/strategies/test_hybrid_quant_flag.py -v`

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add tradingagents/strategies/quant_signal_provider.py tests/strategies/test_v5_pool_map.py
git commit -m "feat(quant): V5QuantSignalProvider with per-coin pool_map

Adds 'v5' option to build_provider / set_active_quant_version
/ get_active_quant_signal. V5 = V2 engine + per-coin pred_dir
routing (e.g. BTC->multi_2coins_v2, ETH->multi_2coins_pit_wf).

Hybrid generate/backtest scripts will use this in the next commit."
```

---

## Task 3: CLI plumbing in `generate_hybrid_signals.py`

**Files:**
- Modify: `scripts/generate_hybrid_signals.py`

- [ ] **Step 1: Add `--quant-version v5` and `--quant-pool-map` flags**

In `scripts/generate_hybrid_signals.py`, in `parse_args()` (around the existing `--quant-version` arg):

Replace:
```python
    p.add_argument("--quant-version", choices=("v2", "v3"), default="v2",
                   help="Quant signal version. ...")
```

with:
```python
    p.add_argument("--quant-version", choices=("v2", "v3", "v5"), default="v2",
                   help="Quant signal version. v3 requires per-coin regime + "
                        "multi-horizon bundles (pickles) and OHLCV prices "
                        "(parquet/CSV) to be present in --v3-state-dir. "
                        "v5 requires --quant-pool-map COIN=PATH ...")
    p.add_argument("--quant-pool-map", nargs="+", default=None,
                   help="(v5 only) Per-coin pred_dir overrides as COIN=PATH pairs. "
                        "Example: --quant-pool-map bitcoin=data/multi_2coins_v2 "
                        "ethereum=data/multi_2coins_pit_wf")
    p.add_argument("--quant-pool-preset", choices=("v5_2coin", "v5_4coin"), default=None,
                   help="(v5 only) Convenience preset for pool_map. "
                        "v5_2coin = BTC->V2 78f, ETH->V4-B 193f. "
                        "v5_4coin = adds BNB->V2 78f, SOL->V4-B 193f.")
```

- [ ] **Step 2: Wire the active version, parse pool_map, set provider state**

Find the existing block (around lines 183–187 per earlier grep):
```python
    from tradingagents.strategies.quant_signal_provider import set_active_quant_version
    set_active_quant_version(args.quant_version)

    if args.quant_version == "v3":
        # ... v3 state init ...
```

Replace with:
```python
    from tradingagents.strategies.quant_signal_provider import set_active_quant_version

    pool_map = None
    if args.quant_version == "v5":
        presets = {
            "v5_2coin": {
                "bitcoin": "data/multi_2coins_v2",
                "ethereum": "data/multi_2coins_pit_wf",
            },
            "v5_4coin": {
                "bitcoin": "data/multi_2coins_v2",
                "ethereum": "data/multi_2coins_pit_wf",
                "binancecoin": "data/multi_3coins_bnb",
                "solana": "data/wf_v5_sol_193f",
            },
        }
        if args.quant_pool_preset:
            pool_map = dict(presets[args.quant_pool_preset])
        else:
            pool_map = {}
        if args.quant_pool_map:
            for item in args.quant_pool_map:
                if "=" not in item:
                    raise SystemExit(
                        f"--quant-pool-map entry {item!r} must be COIN=PATH"
                    )
                k, v = item.split("=", 1)
                pool_map[k.strip()] = v.strip()
        if not pool_map:
            raise SystemExit(
                "--quant-version v5 requires --quant-pool-map or --quant-pool-preset"
            )
        set_active_quant_version("v5", pool_map=pool_map)
    else:
        set_active_quant_version(args.quant_version)

    if args.quant_version == "v3":
        # ... v3 state init unchanged ...
```

- [ ] **Step 3: Persist pool_map in the run manifest**

Find where the script writes a manifest/config JSON next to the output CSVs (search for `output_dir` and a `json.dump` call). Add `"pool_map": pool_map` to the dict so the run is reproducible. If no manifest exists, add a `_write_run_manifest(output_dir, args, pool_map)` helper near the top of `main()` that dumps `{cmd_args, pool_map, started_at}` to `<output_dir>/run_manifest.json`.

- [ ] **Step 4: Smoke-test CLI parsing only**

Run:
```bash
python scripts/generate_hybrid_signals.py --help | grep -A1 "quant-version\|pool"
```
Expected: shows `v5` in choices and the two new args.

Run (no execution, just argparse error path):
```bash
python scripts/generate_hybrid_signals.py --coins bitcoin --start 2025-06-01 --end 2025-06-01 --quant-version v5 2>&1 | head -3
```
Expected: `SystemExit: --quant-version v5 requires --quant-pool-map or --quant-pool-preset`.

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_hybrid_signals.py
git commit -m "feat(hybrid): --quant-version v5 + pool_map CLI in signal gen

Adds v5 choice and --quant-pool-map / --quant-pool-preset flags.
Two presets: v5_2coin (BTC+ETH), v5_4coin (+BNB+SOL).
Writes pool_map into run_manifest.json for reproducibility."
```

---

## Task 4: CLI plumbing in `backtest_hybrid.py`

**Files:**
- Modify: `scripts/backtest_hybrid.py`

- [ ] **Step 1: Add `--baseline-pool-map` and `--baseline-preset`**

In `scripts/backtest_hybrid.py`, add to `parse_args()`:

```python
    p.add_argument("--baseline-pool-map", nargs="+", default=None,
                   help="Per-coin pred_dir overrides for the pure-quant baseline "
                        "equity curve. Format: COIN=PATH. If set, the baseline "
                        "matches V5 MIX routing instead of a single base_dir.")
    p.add_argument("--baseline-preset", choices=("v5_2coin", "v5_4coin"), default=None,
                   help="Convenience preset for --baseline-pool-map.")
```

- [ ] **Step 2: Use pool_map when computing baseline equity**

Find where baseline equity is loaded (search for `baseline_pred_dir` and `preds_lgb`). Refactor the per-coin loop to consult a `pool_map` dict first, falling back to `args.baseline_pred_dir`:

```python
def _resolve_baseline_dir(coin: str, default_dir: str, pool_map: dict | None) -> str:
    if pool_map and coin in pool_map:
        return pool_map[coin]
    return default_dir
```

In `main()`:
```python
    presets = {
        "v5_2coin": {
            "bitcoin": "data/multi_2coins_v2",
            "ethereum": "data/multi_2coins_pit_wf",
        },
        "v5_4coin": {
            "bitcoin": "data/multi_2coins_v2",
            "ethereum": "data/multi_2coins_pit_wf",
            "binancecoin": "data/multi_3coins_bnb",
            "solana": "data/wf_v5_sol_193f",
        },
    }
    pool_map = dict(presets[args.baseline_preset]) if args.baseline_preset else {}
    if args.baseline_pool_map:
        for item in args.baseline_pool_map:
            k, v = item.split("=", 1)
            pool_map[k.strip()] = v.strip()
    # ... in the per-coin loop:
    base_dir = _resolve_baseline_dir(coin, args.baseline_pred_dir, pool_map)
```

- [ ] **Step 3: Write pool_map into the backtest summary JSON**

Where the script writes `summary.json`, add `"baseline_pool_map": pool_map`.

- [ ] **Step 4: Smoke-test CLI parsing**

Run:
```bash
python scripts/backtest_hybrid.py --help | grep -A1 "baseline-pool\|baseline-preset"
```
Expected: both flags listed.

- [ ] **Step 5: Commit**

```bash
git add scripts/backtest_hybrid.py
git commit -m "feat(hybrid): --baseline-pool-map for V5 routing in backtester

Allows the pure-quant baseline curve to use the same per-coin
pool routing as the hybrid run, so the hybrid-vs-baseline delta
isolates LLM contribution rather than pool change."
```

---

## Task 5: Single-bar smoke run

**Files:**
- Create: `scripts/smoke_hybrid_v5.py` (one-off shell-style, deleted in cleanup)

- [ ] **Step 1: Write the smoke script**

```python
#!/usr/bin/env python
"""Smoke: one BTC + one ETH bar through V5 hybrid path. ~5 min on gpt-4o-mini."""
import subprocess, sys
cmd = [
    sys.executable, "scripts/generate_hybrid_signals.py",
    "--coins", "bitcoin", "ethereum",
    "--start", "2025-06-02", "--end", "2025-06-02",
    "--quant-version", "v5",
    "--quant-pool-preset", "v5_2coin",
    "--output-dir", "data/hybrid_smoke_v5",
    "--force",
]
print(" ".join(cmd))
subprocess.check_call(cmd)
```

- [ ] **Step 2: Run smoke**

Run: `python scripts/smoke_hybrid_v5.py`

Expected: completes without exception; produces `data/hybrid_smoke_v5/bitcoin_2025-06-02_2025-06-02.csv` and `data/hybrid_smoke_v5/ethereum_2025-06-02_2025-06-02.csv`, each with one row.

- [ ] **Step 3: Verify routing actually happened**

Run:
```bash
cat data/hybrid_smoke_v5/run_manifest.json | python -m json.tool
```
Expected: `pool_map` contains `bitcoin: data/multi_2coins_v2` and `ethereum: data/multi_2coins_pit_wf`.

Run:
```bash
python -c "
import pandas as pd
btc_v2 = pd.read_csv('data/multi_2coins_v2/preds_lgb_h7.csv', parse_dates=['date'])
eth_v4b = pd.read_csv('data/multi_2coins_pit_wf/preds_lgb_h7.csv', parse_dates=['date'])
btc_v2['date'] = btc_v2['date'].dt.tz_localize(None).dt.normalize()
eth_v4b['date'] = eth_v4b['date'].dt.tz_localize(None).dt.normalize()
btc_pred = btc_v2[(btc_v2.coin_id=='bitcoin')&(btc_v2.date=='2025-06-02')]['prediction'].iloc[0]
eth_pred = eth_v4b[(eth_v4b.coin_id=='ethereum')&(eth_v4b.date=='2025-06-02')]['prediction'].iloc[0]
btc_smoke = pd.read_csv('data/hybrid_smoke_v5/bitcoin_2025-06-02_2025-06-02.csv')
eth_smoke = pd.read_csv('data/hybrid_smoke_v5/ethereum_2025-06-02_2025-06-02.csv')
print('BTC ref_price expected (V2):', btc_pred, 'smoke quant_magnitude:', btc_smoke['quant_magnitude'].iloc[0])
print('ETH ref_price expected (V4-B):', eth_pred, 'smoke quant_magnitude:', eth_smoke['quant_magnitude'].iloc[0])
"
```
Expected: BTC + ETH smoke signals reflect the V2 / V4-B prediction differences (ETH magnitude should differ from a V2-baseline ETH run — verify by comparing against `data/hybrid_signals_v2_1y/ethereum_*.csv` for 2025-06-02 if available).

- [ ] **Step 4: Commit smoke script**

```bash
git add scripts/smoke_hybrid_v5.py
git commit -m "test(hybrid): single-bar V5 smoke runner"
```

---

## Task 6: Full 1-year 2-coin generation (long-running)

**Files:** none (data-only).

This step takes ~30–36 hours wall-clock. Run on Hetzner VPS in tmux.

- [ ] **Step 1: Sync code + data to VPS**

Run (from local laptop, NOT the agent shell — operator-only step):
```bash
rsync -av --delete \
  --exclude='.git' --exclude='.worktrees/*/data' --exclude='__pycache__' \
  /home/malecada/master_thesis/TradingAgents/.worktrees/hybrid-modulator/ \
  root@46.225.169.184:/opt/tradingagents/hybrid-modulator/
rsync -av data/multi_2coins_v2 data/multi_2coins_pit_wf data/multi_2coins_pit_wf \
  root@46.225.169.184:/opt/tradingagents/hybrid-modulator/data/
```
(operator confirms before agent proceeds with later tasks)

- [ ] **Step 2: Kick off generation in tmux on VPS**

On VPS:
```bash
ssh root@46.225.169.184
cd /opt/tradingagents/hybrid-modulator
tmux new -s hybrid_v5 -d "python scripts/generate_hybrid_signals.py \
  --coins bitcoin ethereum \
  --start 2025-04-18 --end 2026-04-15 \
  --quant-version v5 \
  --quant-pool-preset v5_2coin \
  --analysts market onchain crypto_sentiment prediction \
  --llm-provider openai --deep-think gpt-4o-mini --quick-think gpt-4o-mini \
  --output-dir data/hybrid_signals_v5_2coin_1y \
  2>&1 | tee logs/hybrid_v5_2coin_1y.log"
```
Expected: tmux session `hybrid_v5` running. Check with `tmux ls`.

- [ ] **Step 3: Monitor every 6h** (operator only, not the implementation agent)

```bash
tail -n 50 /opt/tradingagents/hybrid-modulator/logs/hybrid_v5_2coin_1y.log
ls -la /opt/tradingagents/hybrid-modulator/data/hybrid_signals_v5_2coin_1y/
```
Expected progress: ~12 bars/hour/coin. Full 363 bars × 2 coins ≈ 30h.

- [ ] **Step 4: Pull results back when done**

```bash
rsync -av root@46.225.169.184:/opt/tradingagents/hybrid-modulator/data/hybrid_signals_v5_2coin_1y/ \
  /home/malecada/master_thesis/TradingAgents/.worktrees/hybrid-modulator/data/hybrid_signals_v5_2coin_1y/
```

- [ ] **Step 5: Sanity-check output**

```bash
python -c "
import pandas as pd, glob
for f in sorted(glob.glob('data/hybrid_signals_v5_2coin_1y/*.csv')):
    df = pd.read_csv(f, parse_dates=['date'])
    print(f, len(df), 'dates:', df.date.min().date(), '->', df.date.max().date(),
          'flat:', (df.quant_direction=='flat').sum(),
          'NaN pos:', df.position.isna().sum())
"
```
Expected: each coin CSV has ~360 rows, no large NaN block, dates span the window.

---

## Task 7: 2-coin backtest + 4-way comparison

**Files:**
- Create: `data/hybrid_backtest_v5_2coin_1y/` (output)
- Create: `scripts/compare_hybrid_v5_vs_v2.py` (one-off comparison)

- [ ] **Step 1: Run V5 hybrid backtest**

```bash
python scripts/backtest_hybrid.py \
  --signals-dir data/hybrid_signals_v5_2coin_1y \
  --coins bitcoin ethereum \
  --start 2025-04-18 --end 2026-04-15 \
  --v2-sizing \
  --baseline-preset v5_2coin \
  --output-dir data/hybrid_backtest_v5_2coin_1y
```
Expected: `data/hybrid_backtest_v5_2coin_1y/{summary.json, daily_returns.csv, hybrid_vs_baseline_equity.png}` produced.

- [ ] **Step 2: Write the comparison script**

Create `scripts/compare_hybrid_v5_vs_v2.py`:
```python
#!/usr/bin/env python
"""4-way summary: V2-quant / V5-quant / Hybrid-V2 / Hybrid-V5 over 1y window."""
import json, sys
from pathlib import Path

runs = {
    "V2 quant (baseline_v5_mix kelly=0.25)": "data/v5_mix_kelly_025/summary.json",  # placeholder; substitute actual V2-only 1y summary path if different
    "V5 quant (V5 MIX 4.5y -> 1y slice)":   "data/v5_mix_production/summary.json",
    "Hybrid V2 (1y)":                        "data/hybrid_backtest_v2_1y/summary.json",
    "Hybrid V5 (1y)":                        "data/hybrid_backtest_v5_2coin_1y/summary.json",
}
rows = []
for label, p in runs.items():
    try:
        s = json.loads(Path(p).read_text())
        sr = s.get("sharpe") or s.get("portfolio_sharpe") or s.get("portfolio", {}).get("sharpe")
        ret = s.get("return") or s.get("compounded_return") or s.get("portfolio", {}).get("return")
        dd = s.get("max_dd") or s.get("portfolio", {}).get("max_dd")
        rows.append((label, sr, ret, dd, p))
    except FileNotFoundError:
        rows.append((label, None, None, None, f"MISSING {p}"))

print(f"{'Run':45} {'SR':>8} {'Return':>10} {'MaxDD':>8}  Source")
for label, sr, ret, dd, p in rows:
    sr_s  = f"{sr:+.2f}" if isinstance(sr,(int,float)) else "-"
    ret_s = f"{ret:+.2%}" if isinstance(ret,(int,float)) else "-"
    dd_s  = f"{dd:+.2%}" if isinstance(dd,(int,float)) else "-"
    print(f"{label:45} {sr_s:>8} {ret_s:>10} {dd_s:>8}  {p}")
```

Run:
```bash
python scripts/compare_hybrid_v5_vs_v2.py
```
Expected: 4-row table. Verify each summary path exists; substitute actual paths in the dict if `summary.json` keys differ across runs (operator may need to inspect schemas).

- [ ] **Step 3: Go/no-go gate**

Verdict criteria for proceeding to 4-coin:
- **GO** if Hybrid V5 SR > Hybrid V2 SR by ≥ +0.30 OR Hybrid V5 SR > V5-quant SR (LLM adds alpha on top of V5 routing).
- **NO-GO** if Hybrid V5 SR ≤ Hybrid V2 SR (LLM modulator does not benefit from V5 routing). In that case STOP and document.

- [ ] **Step 4: Commit results + comparison**

```bash
git add scripts/compare_hybrid_v5_vs_v2.py data/hybrid_backtest_v5_2coin_1y/summary.json
git commit -m "eval(hybrid): V5 1y 2-coin backtest results

4-way comparison: V2 quant / V5 quant / Hybrid V2 / Hybrid V5
over 2025-04-18..2026-04-15. See summary.json for figures."
```

---

## Task 8: 4-coin extension (CONDITIONAL — only if Task 7 Step 3 = GO)

**Files:** none new; reuses everything.

- [ ] **Step 1: Verify BNB + SOL data coverage in window**

Run (from Task 0 Step 1 with stricter check):
```bash
python -c "
import pandas as pd
for coin, path in [('binancecoin','data/multi_3coins_bnb/preds_lgb_h7.csv'),
                   ('solana','data/wf_v5_sol_193f/preds_lgb_h7.csv')]:
    df = pd.read_csv(path, parse_dates=['date'])
    df['date'] = df['date'].dt.tz_localize(None).dt.normalize()
    sub = df[(df.coin_id==coin)&(df.date>='2025-04-18')&(df.date<='2026-04-15')]
    print(f'{coin}: {len(sub)} in-window rows')
    assert len(sub) >= 350, f'INSUFFICIENT: need >= 350 in-window rows for {coin}'
"
```
Expected: both ≥ 350. If SOL is short, STOP — note in thesis that 4-coin hybrid was data-limited and report 2-coin only.

- [ ] **Step 2: Verify analyst pipelines support BNB+SOL**

Run a 1-bar smoke for each new coin in isolation:
```bash
python scripts/generate_hybrid_signals.py \
  --coins binancecoin --start 2025-06-02 --end 2025-06-02 \
  --quant-version v5 --quant-pool-preset v5_4coin \
  --output-dir data/hybrid_smoke_v5_bnb --force
python scripts/generate_hybrid_signals.py \
  --coins solana --start 2025-06-02 --end 2025-06-02 \
  --quant-version v5 --quant-pool-preset v5_4coin \
  --output-dir data/hybrid_smoke_v5_sol --force
```
Expected: both produce a 1-row CSV without uncaught exceptions. Onchain analyst output for SOL is allowed to be sparse (CM Community empty for SOL is a known limitation per `project_v5_mix_per_coin_routing.md`); the analyst should degrade gracefully.

- [ ] **Step 3: Full 4-coin generation (VPS, tmux)**

Same as Task 6 Step 2, but:
```bash
tmux new -s hybrid_v5_4c -d "python scripts/generate_hybrid_signals.py \
  --coins bitcoin ethereum binancecoin solana \
  --start 2025-04-18 --end 2026-04-15 \
  --quant-version v5 \
  --quant-pool-preset v5_4coin \
  --analysts market onchain crypto_sentiment prediction \
  --llm-provider openai --deep-think gpt-4o-mini --quick-think gpt-4o-mini \
  --output-dir data/hybrid_signals_v5_4coin_1y \
  2>&1 | tee logs/hybrid_v5_4coin_1y.log"
```
Wall clock: ~60h. Cost: ~$20.

- [ ] **Step 4: Pull + backtest 4-coin**

```bash
rsync -av root@46.225.169.184:/opt/.../data/hybrid_signals_v5_4coin_1y/ data/hybrid_signals_v5_4coin_1y/

python scripts/backtest_hybrid.py \
  --signals-dir data/hybrid_signals_v5_4coin_1y \
  --coins bitcoin ethereum binancecoin solana \
  --start 2025-04-18 --end 2026-04-15 \
  --v2-sizing \
  --baseline-preset v5_4coin \
  --output-dir data/hybrid_backtest_v5_4coin_1y
```

- [ ] **Step 5: Extend comparison script with 4-coin row + commit**

Add `"Hybrid V5 4-coin (1y)": "data/hybrid_backtest_v5_4coin_1y/summary.json"` to `scripts/compare_hybrid_v5_vs_v2.py`, rerun, and:

```bash
git add scripts/compare_hybrid_v5_vs_v2.py data/hybrid_backtest_v5_4coin_1y/summary.json
git commit -m "eval(hybrid): V5 1y 4-coin backtest results

Adds BNB+SOL to the hybrid V5 backtest. Comparison table extended."
```

---

## Task 9: Document in THESIS_FINDINGS

**Files:**
- Modify: `THESIS_FINDINGS.md` (append new section)

- [ ] **Step 1: Append a "Hybrid V5 1-year backtest" section**

Section structure (fill in actual numbers from `data/hybrid_backtest_v5_*/summary.json`):

```markdown
## §23 Hybrid V5 1-year backtest (2025-04-18 → 2026-04-15)

**Quant base:** V5 MIX per-coin LGB routing (BTC→V2 78f, ETH→V4-B 193f
[, BNB→V2 78f, SOL→V4-B 193f]).
**LLM modulator:** Self-MoA + Skeptic-Quant + CVRF + Hybrid RAG on gpt-4o-mini.

### Results table
| Run | SR | Return | MaxDD |
|---|---|---|---|
| V2 quant only | ... | ... | ... |
| V5 quant only | ... | ... | ... |
| Hybrid V2     | ... | ... | ... |
| Hybrid V5     | ... | ... | ... |
| Hybrid V5 4-coin (if Task 8 ran) | ... | ... | ... |

### Verdict
[Did the LLM modulator add alpha on top of V5 routing? One paragraph.]

### Cost
gpt-4o-mini API spend: $X. Wall clock: Y h on Hetzner CX22.
```

- [ ] **Step 2: Commit**

```bash
git add THESIS_FINDINGS.md
git commit -m "docs(thesis): §23 hybrid V5 1-year backtest results"
```

---

## Self-Review Notes

- **Spec coverage:** routing patch (T1), provider class (T2), gen CLI (T3), backtest CLI (T4), smoke (T5), full gen (T6), 2-coin backtest+compare (T7), conditional 4-coin extension (T8), thesis doc (T9) — covers the request fully.
- **Placeholders:** the THESIS_FINDINGS table values are necessarily TBD until the run completes; that's a results placeholder, not a plan placeholder. No code-step placeholders.
- **Type consistency:** `pool_map: dict[str, str]` used uniformly across all functions, providers, CLI parsing, and presets. Preset keys (`v5_2coin`, `v5_4coin`) used consistently in T3, T4, T8.
- **Spec gap check:** user's request was "deploy similar backtest to test on one year of data with hybrid system" using V5 quant. Covered. 4-coin extension added as conditional follow-up matching V5 MIX canonical, gated on a clear go/no-go in Task 7 Step 3.
