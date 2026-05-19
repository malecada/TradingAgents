# V5 MIX TP/SL Walk-Forward Parameter Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a walk-forward orchestrator that runs the §29 + §30 378-cell sweeps on TRAIN (2021-11→2024-12) + TEST (2025-01→2026-04), identifies the train-best cell per engine, and reports whether the train-best's OOS Sharpe beats the V5 baseline cell's OOS Sharpe.

**Architecture:** No engine change — both existing sweep scripts already accept arbitrary windows. A new orchestrator script invokes each sweep 2× (train + test) for each of the 2 engines (4 sweeps total ≈ 60 s wall), joins the per-cell IS / OOS results, computes the verdict per engine, writes `wf_results.csv` + `wf_summary.json` + `wf_report.md`. Existing sweep scripts are imported and called programmatically (not via subprocess).

**Tech Stack:** Python 3.10, pandas, numpy, pytest, existing modules (`scripts/v5_mix_sltp_sweep.py`, `scripts/v5_mix_sltp_sweep_intrabar.py`).

**Spec:** `docs/superpowers/specs/2026-05-19-v5-sltp-wf-split-design.md`

**Branch:** `feature/v5-sltp-wf-split` (already created, spec committed at `b0235d7`)

---

## File Map

| Path | Status | Responsibility |
|---|---|---|
| `scripts/v5_sltp_wf_orchestrator.py` | Create | Run 4 sweeps (CO/IB × train/test), join cells, compute per-engine verdict, write WF artifacts |
| `tests/strategies/test_sltp_wf.py` | Create | 5 tests: schema, window non-overlap, verdict shape, cell-join correctness, slow end-to-end |
| `THESIS_FINDINGS.md` | Modify | Append §31 (joint verdict) + cross-reference line to §30 |
| `data/v5_sltp_wf/` | Runtime | `{co,ib}_{train,test}/` subdirs (4× sweep output) + wf_results.csv + wf_summary.json + wf_report.md + wf_sweep.log |

---

## Task 1: Orchestrator skeleton with TDD (schema test)

**Files:**
- Create: `scripts/v5_sltp_wf_orchestrator.py`
- Create: `tests/strategies/test_sltp_wf.py`

- [ ] **Step 1.1: Write the failing schema test (with shared module-scoped fixture)**

Create `tests/strategies/test_sltp_wf.py`:

```python
# tests/strategies/test_sltp_wf.py
"""Tests for V5 MIX TP/SL walk-forward orchestrator."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="module")
def smoke_dir(tmp_path_factory):
    """Run the orchestrator in smoke mode ONCE, shared across all fast tests.

    Smoke runs 4 small sweeps (each loads coin OHLC) so it's ~20-40s. Sharing
    via module scope keeps default test runtime tolerable.
    """
    out_dir = tmp_path_factory.mktemp("wf_smoke")
    if (out_dir / "wf_summary.json").exists():
        shutil.rmtree(out_dir)
        out_dir = tmp_path_factory.mktemp("wf_smoke")
    subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "v5_sltp_wf_orchestrator.py"),
            "--smoke",
            "--output-dir", str(out_dir),
        ],
        cwd=str(PROJECT_ROOT),
        check=True,
    )
    return out_dir


def test_orchestrator_smoke_produces_expected_files(smoke_dir):
    """Smoke run must create all 4 sweep subdirs + 3 root artifacts."""
    out_dir = smoke_dir

    # 4 sweep subdirs
    for sub in ("co_train", "co_test", "ib_train", "ib_test"):
        assert (out_dir / sub / "results.csv").exists(), f"missing {sub}/results.csv"
        assert (out_dir / sub / "summary.json").exists(), f"missing {sub}/summary.json"

    # 3 root artifacts
    assert (out_dir / "wf_results.csv").exists()
    assert (out_dir / "wf_summary.json").exists()
    assert (out_dir / "wf_report.md").exists()
```

- [ ] **Step 1.2: Run the test, confirm it fails (script does not exist)**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/test_sltp_wf.py::test_orchestrator_smoke_produces_expected_files -xvs
```

Expected: FAIL with `FileNotFoundError` or `CalledProcessError` because the orchestrator script doesn't exist yet.

- [ ] **Step 1.3: Create the orchestrator skeleton**

Create `scripts/v5_sltp_wf_orchestrator.py`:

```python
#!/usr/bin/env python
"""V5 MIX TP/SL walk-forward parameter split orchestrator.

Runs the §29 (close-only) and §30 (intrabar) 378-cell sweeps on a TRAIN
window and a TEST window, joins cells across IS/OOS, computes per-engine
verdict, and writes WF artifacts.

Outputs to data/v5_sltp_wf/:
  co_train/, co_test/, ib_train/, ib_test/ — per-sweep outputs
  wf_results.csv  — joined per-cell IS-SR + OOS-SR per engine
  wf_summary.json — train-best per engine + OOS scores + verdicts
  wf_report.md    — human-readable summary
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.baseline_v5_mix import COSTS, EARLY_EXIT_DEFAULT  # noqa: E402
from scripts.v5_mix_sltp_sweep import run_sweep as run_sweep_co  # noqa: E402
from scripts.v5_mix_sltp_sweep import (  # noqa: E402
    SL_GRID, EE_GRID, TP_GRID, SMOKE_SL, SMOKE_EE, SMOKE_TP,
)
from scripts.v5_mix_sltp_sweep_intrabar import run_sweep as run_sweep_ib  # noqa: E402

_BASELINE_SL = COSTS["stop_loss"]      # 0.03
_BASELINE_EE = EARLY_EXIT_DEFAULT      # 0.015
_BASELINE_TP = COSTS["take_profit"]    # 0.0


def _git_sha() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=PROJECT_ROOT
        ).decode().strip()
    except Exception:
        return "unknown"


def _join_is_oos(train_csv: Path, test_csv: Path, engine: str) -> pd.DataFrame:
    """Join train (IS) and test (OOS) per-cell portfolio metrics."""
    tr = pd.read_csv(train_csv)
    te = pd.read_csv(test_csv)
    tr = tr[tr["scope"] == "portfolio"].copy()
    te = te[te["scope"] == "portfolio"].copy()
    keys = ["sl", "ee", "tp"]
    cols = ["sharpe", "max_drawdown", "calmar", "total_return"]
    joined = tr[keys + cols].merge(
        te[keys + cols], on=keys, suffixes=("_is", "_oos"),
    )
    joined["engine"] = engine
    joined = joined.rename(columns={
        "sharpe_is": "is_sr", "sharpe_oos": "oos_sr",
        "max_drawdown_is": "is_dd", "max_drawdown_oos": "oos_dd",
        "calmar_is": "is_calmar", "calmar_oos": "oos_calmar",
        "total_return_is": "is_ret", "total_return_oos": "oos_ret",
    })
    return joined[
        ["engine"] + keys
        + ["is_sr", "oos_sr", "is_dd", "oos_dd", "is_calmar", "oos_calmar",
           "is_ret", "oos_ret"]
    ]


def _per_engine_verdict(joined: pd.DataFrame, engine: str) -> dict:
    """Compute train-best, OOS of train-best, baseline OOS, verdict."""
    sub = joined[joined["engine"] == engine].copy()
    train_best = sub.sort_values("is_sr", ascending=False).iloc[0]
    baseline_rows = sub[
        (sub["sl"] == _BASELINE_SL)
        & (sub["ee"] == _BASELINE_EE)
        & (sub["tp"] == _BASELINE_TP)
    ]
    baseline_oos_sr = (
        float(baseline_rows["oos_sr"].iloc[0]) if len(baseline_rows) else None
    )
    train_best_oos_sr = float(train_best["oos_sr"])
    verdict = (
        "pass" if baseline_oos_sr is not None
        and train_best_oos_sr > baseline_oos_sr
        else "fail"
    )
    return dict(
        engine=engine,
        train_best=dict(
            sl=float(train_best["sl"]), ee=float(train_best["ee"]),
            tp=float(train_best["tp"]),
            is_sr=float(train_best["is_sr"]),
            oos_sr=train_best_oos_sr,
            is_dd=float(train_best["is_dd"]),
            oos_dd=float(train_best["oos_dd"]),
            oos_calmar=float(train_best["oos_calmar"]),
        ),
        baseline_oos_sr=baseline_oos_sr,
        verdict=verdict,
    )


def _write_report(summary: dict, out_path: Path) -> None:
    co = summary["close_only"]
    ib = summary["intrabar"]
    lines = [
        "# V5 MIX TP/SL Walk-Forward Parameter Split Report",
        "",
        f"Train window: {summary['windows']['train']['start']} → {summary['windows']['train']['end']}",
        f"Test window:  {summary['windows']['test']['start']} → {summary['windows']['test']['end']}",
        "",
        f"Baseline cell: SL={_BASELINE_SL}, EE={_BASELINE_EE}, TP={_BASELINE_TP}",
        "",
        "## Close-only engine",
        "",
        f"- Train-best: SL={co['train_best']['sl']:g}, "
        f"EE={co['train_best']['ee']:g}, TP={co['train_best']['tp']:g}",
        f"  - IS SR  = {co['train_best']['is_sr']:+.3f}",
        f"  - OOS SR = {co['train_best']['oos_sr']:+.3f}",
        f"  - OOS DD = {co['train_best']['oos_dd']:.1%}",
        f"  - OOS Calmar = {co['train_best']['oos_calmar']:+.2f}",
        f"- Baseline OOS SR = "
        f"{co['baseline_oos_sr']:+.3f}" if co['baseline_oos_sr'] is not None else "n/a",
        f"- **Verdict: {co['verdict'].upper()}** "
        f"(train-best OOS > baseline OOS? "
        f"{co['train_best']['oos_sr']:+.3f} vs {co['baseline_oos_sr']:+.3f})",
        "",
        "## Intrabar engine",
        "",
        f"- Train-best: SL={ib['train_best']['sl']:g}, "
        f"EE={ib['train_best']['ee']:g}, TP={ib['train_best']['tp']:g}",
        f"  - IS SR  = {ib['train_best']['is_sr']:+.3f}",
        f"  - OOS SR = {ib['train_best']['oos_sr']:+.3f}",
        f"  - OOS DD = {ib['train_best']['oos_dd']:.1%}",
        f"  - OOS Calmar = {ib['train_best']['oos_calmar']:+.2f}",
        f"- Baseline OOS SR = "
        f"{ib['baseline_oos_sr']:+.3f}" if ib['baseline_oos_sr'] is not None else "n/a",
        f"- **Verdict: {ib['verdict'].upper()}** "
        f"(train-best OOS > baseline OOS? "
        f"{ib['train_best']['oos_sr']:+.3f} vs {ib['baseline_oos_sr']:+.3f})",
        "",
        "## Joint outcome",
        "",
        f"- Close-only: {co['verdict']}",
        f"- Intrabar:   {ib['verdict']}",
        "",
        f"git SHA: {summary['git_sha']}",
        f"wall clock: {summary['wall_clock_sec']:.1f} s",
        "",
    ]
    out_path.write_text("\n".join(lines) + "\n")


def run_wf(
    sl_grid: list[float], ee_grid: list[float], tp_grid: list[float],
    train_start: str, train_end: str,
    test_start: str, test_end: str,
    kelly_fraction: float, out_dir: Path,
) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    sweeps = [
        ("co_train", run_sweep_co, train_start, train_end),
        ("co_test",  run_sweep_co, test_start,  test_end),
        ("ib_train", run_sweep_ib, train_start, train_end),
        ("ib_test",  run_sweep_ib, test_start,  test_end),
    ]
    for name, runner, start, end in sweeps:
        print(f"\n  === {name}: {start} → {end} ===")
        sub_dir = out_dir / name
        runner(sl_grid, ee_grid, tp_grid, start, end, kelly_fraction, sub_dir)

    joined_co = _join_is_oos(
        out_dir / "co_train" / "results.csv",
        out_dir / "co_test" / "results.csv",
        engine="close_only",
    )
    joined_ib = _join_is_oos(
        out_dir / "ib_train" / "results.csv",
        out_dir / "ib_test" / "results.csv",
        engine="intrabar",
    )
    joined = pd.concat([joined_co, joined_ib], ignore_index=True)
    joined.to_csv(out_dir / "wf_results.csv", index=False)

    co_verdict = _per_engine_verdict(joined, "close_only")
    ib_verdict = _per_engine_verdict(joined, "intrabar")

    summary = dict(
        grid=dict(sl=sl_grid, ee=ee_grid, tp=tp_grid),
        windows=dict(
            train=dict(start=train_start, end=train_end),
            test=dict(start=test_start, end=test_end),
        ),
        kelly_fraction=kelly_fraction,
        baseline_cell=dict(sl=_BASELINE_SL, ee=_BASELINE_EE, tp=_BASELINE_TP),
        close_only=co_verdict,
        intrabar=ib_verdict,
        wall_clock_sec=time.time() - t0,
        git_sha=_git_sha(),
    )
    with open(out_dir / "wf_summary.json", "w") as f:
        json.dump(summary, f, indent=2, default=str)
    _write_report(summary, out_dir / "wf_report.md")

    print(f"\n  Wrote: {out_dir / 'wf_results.csv'}  ({len(joined)} rows)")
    print(f"  Wrote: {out_dir / 'wf_summary.json'}")
    print(f"  Wrote: {out_dir / 'wf_report.md'}")
    print(f"\n  CO verdict: {co_verdict['verdict'].upper()}  "
          f"(train-best OOS SR={co_verdict['train_best']['oos_sr']:+.3f} vs "
          f"baseline OOS SR={co_verdict['baseline_oos_sr']:+.3f})")
    print(f"  IB verdict: {ib_verdict['verdict'].upper()}  "
          f"(train-best OOS SR={ib_verdict['train_best']['oos_sr']:+.3f} vs "
          f"baseline OOS SR={ib_verdict['baseline_oos_sr']:+.3f})")

    return summary


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--train-start", default="2021-11-07")
    p.add_argument("--train-end",   default="2024-12-31")
    p.add_argument("--test-start",  default="2025-01-01")
    p.add_argument("--test-end",    default="2026-04-15")
    p.add_argument("--output-dir",  default="data/v5_sltp_wf")
    p.add_argument("--kelly",       type=float, default=0.5)
    p.add_argument("--smoke", action="store_true",
                   help="Smoke run on tiny grid (2x1x2=4 cells)")
    p.add_argument("--data-root", default=None)
    args = p.parse_args()

    if args.data_root:
        os.environ["TRADINGAGENTS_DATA_ROOT"] = args.data_root

    if args.smoke:
        sl, ee, tp = SMOKE_SL, SMOKE_EE, SMOKE_TP
        print("  SMOKE MODE — small grid")
    else:
        sl, ee, tp = SL_GRID, EE_GRID, TP_GRID

    out_dir = PROJECT_ROOT / args.output_dir
    print(f"\n  V5 MIX TP/SL walk-forward")
    print(f"  train  : {args.train_start} → {args.train_end}")
    print(f"  test   : {args.test_start} → {args.test_end}")
    print(f"  grid   : SL={len(sl)} EE={len(ee)} TP={len(tp)} = "
          f"{len(sl) * len(ee) * len(tp)} cells × 4 sweeps")
    print(f"  output : {out_dir}\n")

    run_wf(sl, ee, tp,
           args.train_start, args.train_end,
           args.test_start, args.test_end,
           args.kelly, out_dir)


if __name__ == "__main__":
    main()
```

- [ ] **Step 1.4: Run the schema test, confirm PASS**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/test_sltp_wf.py::test_orchestrator_smoke_produces_expected_files -xvs
```

Expected: PASSED. (Smoke takes ~10-20 s — 4 small sweeps on smoke grids).

- [ ] **Step 1.5: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add scripts/v5_sltp_wf_orchestrator.py tests/strategies/test_sltp_wf.py
git commit -m "feat(wf): V5 MIX TP/SL walk-forward orchestrator skeleton

Runs CO + IB sweeps on TRAIN + TEST windows, joins cells, computes
per-engine verdict (train-best OOS SR > baseline OOS SR). Schema test
green."
```

---

## Task 2: Window non-overlap test

**Files:**
- Modify: `tests/strategies/test_sltp_wf.py` (append)

- [ ] **Step 2.1: Append the non-overlap test (reuses `smoke_dir` fixture)**

```python
def test_orchestrator_train_test_windows_do_not_overlap(smoke_dir):
    """wf_summary.json train and test windows must be disjoint (test starts
    strictly after train ends)."""
    out_dir = smoke_dir
    s = json.loads((out_dir / "wf_summary.json").read_text())
    train_end = pd.Timestamp(s["windows"]["train"]["end"])
    test_start = pd.Timestamp(s["windows"]["test"]["start"])
    assert test_start > train_end, (
        f"train_end={train_end} must be < test_start={test_start}"
    )
```

- [ ] **Step 2.2: Run + confirm**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/test_sltp_wf.py -xvs
```

Expected: 2 PASS.

- [ ] **Step 2.3: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add tests/strategies/test_sltp_wf.py
git commit -m "test(wf): assert train/test windows disjoint in wf_summary.json"
```

---

## Task 3: Per-engine verdict schema test

**Files:**
- Modify: `tests/strategies/test_sltp_wf.py` (append)

- [ ] **Step 3.1: Append the verdict schema test (reuses `smoke_dir` fixture)**

```python
def test_orchestrator_per_engine_verdict_present(smoke_dir):
    """wf_summary.json must contain close_only.verdict and intrabar.verdict,
    each in {pass, fail}."""
    out_dir = smoke_dir
    s = json.loads((out_dir / "wf_summary.json").read_text())

    for engine in ("close_only", "intrabar"):
        assert engine in s, f"missing engine block: {engine}"
        block = s[engine]
        assert block["engine"] == engine
        assert "verdict" in block
        assert block["verdict"] in ("pass", "fail"), (
            f"{engine}.verdict must be pass|fail, got {block['verdict']}"
        )
        assert "train_best" in block
        for k in ("sl", "ee", "tp", "is_sr", "oos_sr", "oos_dd", "oos_calmar"):
            assert k in block["train_best"], f"missing train_best.{k}"
        assert "baseline_oos_sr" in block
```

- [ ] **Step 3.2: Run + confirm**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/test_sltp_wf.py -xvs
```

Expected: 3 PASS.

- [ ] **Step 3.3: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add tests/strategies/test_sltp_wf.py
git commit -m "test(wf): assert per-engine verdict schema in wf_summary.json"
```

---

## Task 4: Cell-join correctness test

**Files:**
- Modify: `tests/strategies/test_sltp_wf.py` (append)

- [ ] **Step 4.1: Append the cell-join test (reuses `smoke_dir` fixture)**

```python
def test_orchestrator_cell_join_matches_source_csvs(smoke_dir):
    """A sampled cell in wf_results.csv must match the same cell looked up
    in the per-window per-engine source CSVs."""
    out_dir = smoke_dir

    wf = pd.read_csv(out_dir / "wf_results.csv")
    # Pick the close-only baseline cell (always in smoke grid).
    co_rows = wf[
        (wf["engine"] == "close_only")
        & (wf["sl"] == 0.03) & (wf["ee"] == 0.015) & (wf["tp"] == 0.0)
    ]
    assert len(co_rows) == 1, "expected exactly one CO baseline cell row"
    co = co_rows.iloc[0]

    co_train = pd.read_csv(out_dir / "co_train" / "results.csv")
    co_train_port = co_train[
        (co_train["scope"] == "portfolio")
        & (co_train["sl"] == 0.03) & (co_train["ee"] == 0.015) & (co_train["tp"] == 0.0)
    ].iloc[0]
    co_test = pd.read_csv(out_dir / "co_test" / "results.csv")
    co_test_port = co_test[
        (co_test["scope"] == "portfolio")
        & (co_test["sl"] == 0.03) & (co_test["ee"] == 0.015) & (co_test["tp"] == 0.0)
    ].iloc[0]

    assert abs(co["is_sr"] - co_train_port["sharpe"]) < 1e-9, (
        f"is_sr mismatch: wf_results={co['is_sr']} vs co_train={co_train_port['sharpe']}"
    )
    assert abs(co["oos_sr"] - co_test_port["sharpe"]) < 1e-9, (
        f"oos_sr mismatch: wf_results={co['oos_sr']} vs co_test={co_test_port['sharpe']}"
    )
```

- [ ] **Step 4.2: Run + confirm**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/test_sltp_wf.py -xvs
```

Expected: 4 PASS.

- [ ] **Step 4.3: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add tests/strategies/test_sltp_wf.py
git commit -m "test(wf): assert per-cell IS/OOS join matches source CSVs"
```

---

## Task 5: Slow end-to-end test (full WF)

**Files:**
- Modify: `tests/strategies/test_sltp_wf.py` (append slow test)

- [ ] **Step 5.1: Append the slow end-to-end test**

```python
@pytest.mark.slow
def test_orchestrator_full_wf_completes_and_populates_verdicts(tmp_path):
    """Full WF (378 cells × 4 sweeps) must complete in <300s and produce a
    valid wf_summary.json with both engine verdicts populated."""
    out_dir = tmp_path / "wf_full"
    if out_dir.exists():
        shutil.rmtree(out_dir)
    import time as _time
    t0 = _time.time()
    subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "v5_sltp_wf_orchestrator.py"),
            "--output-dir", str(out_dir),
        ],
        cwd=str(PROJECT_ROOT),
        check=True,
        timeout=300,
    )
    elapsed = _time.time() - t0
    assert elapsed < 300, f"WF took {elapsed:.1f}s, expected <300s"

    s = json.loads((out_dir / "wf_summary.json").read_text())
    for engine in ("close_only", "intrabar"):
        assert s[engine]["verdict"] in ("pass", "fail")
        assert s[engine]["baseline_oos_sr"] is not None
        assert s[engine]["train_best"]["is_sr"] > 0  # full sweep has a positive winner
```

- [ ] **Step 5.2: Run the slow test (~60s wall)**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/test_sltp_wf.py -m slow -xvs
```

Expected: 1 PASS in <300 s.

- [ ] **Step 5.3: Confirm default exclusion**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/test_sltp_wf.py -v 2>&1 | tail -5
```

Expected: 4 PASS + 1 deselected.

- [ ] **Step 5.4: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add tests/strategies/test_sltp_wf.py
git commit -m "test(wf): slow end-to-end full WF reproduction guard"
```

---

## Task 6: Full WF run

**Files:** runtime only

- [ ] **Step 6.1: Launch the full WF**

```bash
cd /home/malecada/master_thesis/TradingAgents
mkdir -p data/v5_sltp_wf
python scripts/v5_sltp_wf_orchestrator.py --output-dir data/v5_sltp_wf 2>&1 | tee data/v5_sltp_wf/wf_sweep.log
```

Expected wall clock: ~60 s (4 × 15 s).

- [ ] **Step 6.2: Inspect the verdicts**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -c "
import json
s = json.load(open('data/v5_sltp_wf/wf_summary.json'))
for engine in ('close_only', 'intrabar'):
    b = s[engine]
    print(f'=== {engine} ===')
    print(f'  train_best : SL={b[\"train_best\"][\"sl\"]} EE={b[\"train_best\"][\"ee\"]} TP={b[\"train_best\"][\"tp\"]}')
    print(f'  IS SR      : {b[\"train_best\"][\"is_sr\"]:+.3f}')
    print(f'  OOS SR     : {b[\"train_best\"][\"oos_sr\"]:+.3f}')
    print(f'  OOS DD     : {b[\"train_best\"][\"oos_dd\"]:.1%}')
    print(f'  baseline OOS SR: {b[\"baseline_oos_sr\"]:+.3f}')
    print(f'  VERDICT    : {b[\"verdict\"].upper()}')
print()
print('wall_clock_sec:', s['wall_clock_sec'])
"
```

Record both verdicts. Possible combinations:
- pass/pass → both finds stand
- pass/fail or fail/pass → only one finding generalises
- fail/fail → both finds rejected

- [ ] **Step 6.3: Sanity-check the joined results**

```bash
python -c "
import pandas as pd
df = pd.read_csv('data/v5_sltp_wf/wf_results.csv')
print('shape:', df.shape)
print('engines:', df['engine'].unique().tolist())
print('cells per engine:', df.groupby('engine').size().to_dict())
# Each engine: 378 cells joined IS/OOS
"
```

Expected: `shape: (756, 10)` (378 × 2 engines × 1 row per cell post-join); engines = `['close_only', 'intrabar']`.

- [ ] **Step 6.4: Commit the results**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add -f data/v5_sltp_wf/wf_results.csv data/v5_sltp_wf/wf_summary.json data/v5_sltp_wf/wf_report.md data/v5_sltp_wf/wf_sweep.log
git add -f data/v5_sltp_wf/co_train/ data/v5_sltp_wf/co_test/ data/v5_sltp_wf/ib_train/ data/v5_sltp_wf/ib_test/
git commit -m "results(wf): V5 MIX TP/SL walk-forward 4-sweep output

Train 2021-11-07 → 2024-12-31; Test 2025-01-01 → 2026-04-15.
See wf_summary.json for per-engine train-best + OOS scores + verdict."
```

---

## Task 7: THESIS_FINDINGS.md §31 + §30 cross-reference

**Files:**
- Modify: `THESIS_FINDINGS.md`

- [ ] **Step 7.1: Find next section anchor**

```bash
grep -n "^## 3[0-9]" /home/malecada/master_thesis/TradingAgents/THESIS_FINDINGS.md | tail -5
```

Expected: latest is `## 30.`. Use `## 31.`. If higher exists, use next available.

- [ ] **Step 7.2: Extract live numbers from wf_summary.json**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -c "
import json
s = json.load(open('data/v5_sltp_wf/wf_summary.json'))
for eng in ('close_only', 'intrabar'):
    b = s[eng]
    tb = b['train_best']
    print(f'{eng.upper()}')
    print(f'  TB_SL={tb[\"sl\"]:g}  TB_EE={tb[\"ee\"]:g}  TB_TP={tb[\"tp\"]:g}')
    print(f'  TB_IS_SR={tb[\"is_sr\"]:.3f}')
    print(f'  TB_OOS_SR={tb[\"oos_sr\"]:.3f}')
    print(f'  TB_OOS_DD={tb[\"oos_dd\"]*100:.1f}%')
    print(f'  BASELINE_OOS_SR={b[\"baseline_oos_sr\"]:.3f}')
    print(f'  VERDICT={b[\"verdict\"].upper()}')
"
```

Record these values. They MUST substitute every `<<...>>` placeholder.

- [ ] **Step 7.3: Append §31 to THESIS_FINDINGS.md**

Append (two leading blank lines). Substitute the values from Step 7.2 into every `<<...>>`:

```markdown


## 31. V5 MIX TP/SL Walk-Forward Parameter Split — §29 + §30 OOS Validation (2026-05-19)

**Goal.** §29 (close-only sweep) and §30 (intrabar sweep) both produced
single-window in-sample best cells. §30 partial-confirmed §29 only with a
**different** parameter regime — wicks flipped the optimum. This study tests
both engines' train-best cells out-of-sample on a held-out 2025-01 → 2026-04
window.

**Method.** Train window 2021-11-07 → 2024-12-31 (~3.15 yr); test window
2025-01-01 → 2026-04-15 (~1.3 yr). For each engine (close-only, intrabar),
the same 378-cell SL × EE × TP grid is swept on TRAIN and TEST. The
train-best cell (highest IS Sharpe) is identified and its OOS Sharpe is
compared to the OOS Sharpe of the V5 baseline cell (SL=0.03, EE=0.015,
TP=off). Verdict per engine: **pass** if train-best OOS SR > baseline OOS SR,
else **fail**.

**Results — close-only engine.**

| | Value |
|---|---|
| Train-best cell | SL = <<CO_TB_SL>>, EE = <<CO_TB_EE>>, TP = <<CO_TB_TP>> |
| IS SR (TRAIN) | <<CO_TB_IS_SR>> |
| OOS SR (TEST) | <<CO_TB_OOS_SR>> |
| OOS DD | <<CO_TB_OOS_DD>>% |
| Baseline OOS SR | <<CO_BASELINE_OOS_SR>> |
| **Verdict** | **<<CO_VERDICT>>** |

**Results — intrabar engine.**

| | Value |
|---|---|
| Train-best cell | SL = <<IB_TB_SL>>, EE = <<IB_TB_EE>>, TP = <<IB_TB_TP>> |
| IS SR (TRAIN) | <<IB_TB_IS_SR>> |
| OOS SR (TEST) | <<IB_TB_OOS_SR>> |
| OOS DD | <<IB_TB_OOS_DD>>% |
| Baseline OOS SR | <<IB_BASELINE_OOS_SR>> |
| **Verdict** | **<<IB_VERDICT>>** |

**Joint outcome.** [Insert one paragraph following this verdict matrix.]

| CO | IB | Action taken |
|---|---|---|
| pass | pass | Both stand. Recommend bootstrap CI follow-up before any live consideration. |
| pass | fail | Close-only generalises; intrabar finding window-specific. |
| fail | pass | Close-only does not generalise; intrabar finding is the survivor. |
| fail | fail | Both rejected. §29-§30-§31 sweep family produces no WF-confirmed alpha — controlled negative result. |

**Limitations.**
1. Single train/test split. Test window only 1.3 yr. Bootstrap CI on the OOS delta is the natural follow-up to test whether any observed OOS improvement is statistically distinguishable from sampling noise.
2. No embargo between train and test. PIT prediction CSVs + per-call position reset means no leakage path, but the immediacy of the boundary inherits any momentum from late-2024 into early-2025.
3. Global tuple — same SL/EE/TP across 4 coins. Per-coin OOS may behave differently.
4. Both engines and both windows share the same 4 coins and the same V5 sizing layer. The §21 attribution caveat (sizing dominates LGB signal) means a "pass" here primarily validates the parameter family, not the LGB predictions.

**Live deployment.** Regardless of verdict, no recommendation. Any change to `src_live/config.py` requires (at minimum) bootstrap CI on the OOS delta plus a live A/B spec — neither in scope here.

**Artifacts.**
- Joined per-cell IS/OOS results: `data/v5_sltp_wf/wf_results.csv`
- Per-engine train-best + verdicts: `data/v5_sltp_wf/wf_summary.json`
- Human-readable report: `data/v5_sltp_wf/wf_report.md`
- Per-window per-engine raw sweeps: `data/v5_sltp_wf/{co,ib}_{train,test}/`
- Run log: `data/v5_sltp_wf/wf_sweep.log`

**Spec + plan.**
- Spec: `docs/superpowers/specs/2026-05-19-v5-sltp-wf-split-design.md`
- Plan: `docs/superpowers/plans/2026-05-19-v5-sltp-wf-split.md`
- Branch: `feature/v5-sltp-wf-split`
```

- [ ] **Step 7.4: Add cross-reference line to §30**

Find the final line of §30 (the "Spec + plan" block). Use Edit to append immediately after:

```markdown

**Follow-up:** §31 walk-forward validates this OOS; see verdict there.
```

- [ ] **Step 7.5: Verify no `<<...>>` remain + section anchor**

```bash
grep -n "<<.*>>" /home/malecada/master_thesis/TradingAgents/THESIS_FINDINGS.md
grep -n "^## 31\." /home/malecada/master_thesis/TradingAgents/THESIS_FINDINGS.md
grep -n "Follow-up.*walk-forward" /home/malecada/master_thesis/TradingAgents/THESIS_FINDINGS.md
```

Expected: zero `<<...>>` matches; one `## 31.` match; one cross-reference line inside §30.

- [ ] **Step 7.6: Commit**

```bash
cd /home/malecada/master_thesis/TradingAgents
git add THESIS_FINDINGS.md
git commit -m "docs(thesis): §31 walk-forward parameter split — joint OOS verdicts

Train 2021-11→2024-12 / Test 2025-01→2026-04 on 378-cell × 2-engine grid.
Per-engine verdict: train-best OOS SR > baseline OOS SR? Joint outcome
table interprets pass/pass, pass/fail, fail/pass, fail/fail. Bootstrap
CI deferred; no live change recommended regardless of verdict."
```

---

## Task 8: Final verification

**Files:** none modified

- [ ] **Step 8.1: Run the WF test suite**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/test_sltp_wf.py -v
```

Expected: 4 PASS + 1 deselected.

- [ ] **Step 8.2: Run the full strategies suite (no regression)**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/ -v 2>&1 | tail -3
```

Expected: 126 + 1 skip + 4 deselected (122 prior + 4 new = 126 PASS).

- [ ] **Step 8.3: Run all slow regression guards**

```bash
cd /home/malecada/master_thesis/TradingAgents
python -m pytest tests/strategies/ -m slow -xvs 2>&1 | tail -15
```

Expected: 4 PASS — §29 baseline reproduction, §30 close-only reproduction, §30 intrabar baseline sane, §31 full WF completes.

- [ ] **Step 8.4: Confirm branch state**

```bash
cd /home/malecada/master_thesis/TradingAgents
git log --oneline feature/v5-sltp-wf-split ^main
git status --short
```

Expected: 9 commits (spec + plan + Tasks 1-7). Working tree clean (or only pre-existing untracked).

- [ ] **Step 8.5: Report final state**

Report the WF verdicts (from `data/v5_sltp_wf/wf_summary.json`) to the user with a recommendation:
- If both `pass` → recommend bootstrap CI follow-up spec
- If exactly one `pass` → name which engine generalises; recommend bootstrap CI on that engine
- If both `fail` → recommend `superpowers:finishing-a-development-branch`; the parameter family is exhausted as a controlled negative result

---

## Done

The branch `feature/v5-sltp-wf-split` contains:
- Orchestrator that runs 4 sweeps (CO/IB × train/test) without engine changes
- 5 tests (4 fast + 1 slow end-to-end)
- WF artifacts (joined CSV, summary JSON, human report, raw per-sweep dirs)
- THESIS_FINDINGS.md §31 with per-engine + joint verdict + §30 cross-reference

If at least one engine = pass → next spec: bootstrap CI on OOS delta (statistical significance test). If both = fail → finish branch; the §29-§30-§31 parameter-sweep family is closed as a controlled negative result.
