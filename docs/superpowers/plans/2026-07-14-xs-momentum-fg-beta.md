# Wide-Universe Cross-Sectional Momentum (P1) + F&G Sentiment-Beta Sort (D1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Evaluate, under pre-registered gates and the locked holdout, whether (P1) cross-sectional momentum on a wide PIT-safe Binance USDT-perp universe survives realistic retail costs, and whether (D1) a Fear&Greed sentiment-beta sort adds value — each yielding a thesis-defensible positive or negative.

**Architecture:** New `tradingagents/xsect/` package (universe, signals, portfolio, fgbeta) + a bulk kline store `data/xsect/klines/{SYMBOL}.parquet` downloaded from Binance (survivorship-safe: must include delisted symbols like LUNAUSDT/FTTUSDT). Weekly-rebalance long-only EW portfolios with per-side costs, benchmark = EW basket of the full eligible universe. Reuses `tradingagents/rebuild/ledger.py` (trial ledger + dev-window guard) and the frozen conventions from the stress-ews program (SR √365 with 0-on-zero-variance, maxDD positive magnitude, placebo p = (1+ge)/(n+1)).

**Tech Stack:** Python 3.13 (`.venv/bin/python`), pandas, numpy, requests, pytest.

## Global Constraints

- Branch: `feature/xs-momentum` off `feature/stress-index-ews` @ 23016d7 (keeps unified gates.json + trial ledger).
- Causality: momentum scores and F&G betas computed only from data ≤ rebalance decision time (Monday close uses data through that Monday close; positions earn returns from Tuesday onward — decision bar never earns its own return). Universe eligibility for a rebalance at Monday D uses volume data ≤ D.
- Dev window: **2021-01-01 → 2025-03-31**. Holdout: **2025-04-01 → 2026-07-01**, locked, one-shot, `allow_holdout=True` only in the holdout script. Ledger guard (`assert_dev_window`) governs mechanically.
- PIT universe MUST include delisted symbols. Hard verification: LUNAUSDT and FTTUSDT present in the kline store with data ending near their delistings. If unobtainable, the program is BLOCKED (survivorship bias would void everything).
- Costs: 10 bps per side (5 taker + 5 slippage) applied to turnover, including initial entry and weekly reconstitution of the benchmark.
- Pre-registered grids, closed: P1 = 12 configs (L ∈ {7,14,28} × skip ∈ {0,1} × K ∈ {10,20}); D1 = 2 configs. Every evaluated config → `log_trial`. No config added after the respective dev run starts.
- SR = mean/std·√365 on daily log-returns, SR := 0.0 if std == 0. MaxDD reported as positive magnitude. Paired comparisons: stationary block bootstrap, block 21, n = 2000, on aligned daily return pairs.
- Tests: `.venv/bin/python -m pytest tests/<file> -v` from repo root. Working tree carries unrelated modified files — every commit adds ONLY the files its task names.

---

### Task 0: Pre-registration — gates for P1 and D1

**Files:**
- Modify: `data/rebuild/gates.json` (add `xs_mom_p1` and `fg_beta_d1` keys)
- Create: `docs/superpowers/specs/2026-07-14-xs-mom-fg-beta-prereg.md`

**Interfaces:**
- Produces: frozen constants all later tasks copy verbatim.

- [ ] **Step 1: Create branch**

```bash
cd /home/malecada/master_thesis/TradingAgents
git checkout feature/stress-index-ews
git checkout -b feature/xs-momentum
```

- [ ] **Step 2: Add two keys to `data/rebuild/gates.json`** (preserve all existing keys byte-for-byte; validate JSON after edit):

```json
"xs_mom_p1": {
  "registered": "2026-07-14",
  "dev_window": ["2021-01-01", "2025-03-31"],
  "holdout_window": ["2025-04-01", "2026-07-01"],
  "universe_rule": "PIT daily eligibility: USDT-M perp with kline on day D, first kline <= D-30, 30d median quote-volume >= 5000000 USD; rank by 30d median quote-volume, keep top 100; snapshot at each weekly rebalance (Monday close) using data <= that close",
  "portfolio_rule": "EW long-only top-K by momentum at Monday close, held to next Monday close; returns accrue from the bar AFTER the decision bar; momentum = sum of daily log-returns over L days ending S days before the decision close; costs 10bps per side on turnover; benchmark = EW full eligible universe, same mechanics",
  "grid": { "L": [7, 14, 28], "skip": [0, 1], "K": [10, 20] },
  "bootstrap": { "block": 21, "n": 2000 },
  "placebo": "N=500 within-rebalance random rank permutations of the momentum scores, identical mechanics; p=(1+#{placebo SR >= real SR})/(N+1)",
  "dev_select": {
    "net_sr_min": 0.8,
    "delta_sr_vs_benchmark_min": 0.0,
    "p_pos_min": 0.85,
    "placebo_p_max": 0.05,
    "dsr_min": 0.9,
    "tiebreak": "highest DSR, then lowest placebo p"
  },
  "holdout_deploy": { "net_sr_min": 0.5, "delta_sr_vs_benchmark_min": 0.0, "p_pos_min": 0.85, "placebo_p_max": 0.05, "one_shot": true }
},
"fg_beta_d1": {
  "registered": "2026-07-14",
  "dev_window": ["2021-01-01", "2025-03-31"],
  "holdout_window": ["2025-04-01", "2026-07-01"],
  "beta_rule": "rolling 90d OLS beta of coin daily log-return on delta F&G (value diff), min 60 overlapping obs, inputs shift(1)-causal at the decision close",
  "grid_desc": "exactly 2 configs: (a) standalone = EW long the MIDDLE F&G-beta quintile of the eligible universe, weekly, same mechanics/costs as P1; (b) overlay = P1 dev-selected portfolio excluding coins in the extreme (top+bottom) beta quintiles; if P1 selects NONE, only (a) runs",
  "dev_select_standalone": { "net_sr_min": 0.8, "delta_sr_vs_benchmark_min": 0.0, "p_pos_min": 0.85, "placebo_p_max": 0.05, "dsr_min": 0.9 },
  "dev_select_overlay": { "delta_sr_vs_p1_min": 0.0, "p_pos_min": 0.85 },
  "holdout_deploy": { "same_as_dev": true, "net_sr_min_holdout": 0.5, "one_shot": true }
}
```

- [ ] **Step 3: Spec doc** `docs/superpowers/specs/2026-07-14-xs-mom-fg-beta-prereg.md`: verbatim gate JSON; grid-closure sentences ("P1 grid is closed at 12 configs; D1 at 2; any config evaluated outside these grids voids the respective experiment"); evidence basis — mechanism-level only, NO invented quantitative expectations: PIVOT_RESEARCH_2026-07-12.md (CMOM post-2020 t=3.70, Borri et al. arXiv 2510.14435, verified 3-0; JFQA CTREND; central caveat: published Sharpes are GROSS) and SENTIMENT_EARLY_WARNING_RESEARCH_2026-07-14.md D1 (F&G-beta priced nonlinearly on 1,100 coins, S2214635025000243, 3-0/2-1; intermediate-beta premium); statement that survivorship safety (delisted symbols present) is a validity precondition.

- [ ] **Step 4: Commit**

```bash
git add data/rebuild/gates.json docs/superpowers/specs/2026-07-14-xs-mom-fg-beta-prereg.md
git commit -m "prereg(xs-mom+fg-beta): gates, closed grids (12+2), universe/portfolio rules frozen"
```

---

### Task 1: Bulk kline store — every USDT perp EVER listed (survivorship-safe)

**Files:**
- Create: `scripts/fetch_xsect_klines.py`
- Output: `data/xsect/klines/{SYMBOL}.parquet`, `data/xsect/klines_manifest.json`

**Interfaces:**
- Produces: per-symbol parquet with tz-aware UTC daily DatetimeIndex `ts`, columns `open, high, low, close, quote_volume` (floats); manifest JSON `{symbol: {"first": iso, "last": iso, "rows": int}}`.

- [ ] **Step 1: Write the fetcher**

```python
# scripts/fetch_xsect_klines.py
"""Bulk daily klines for ALL Binance USDT-M perps ever listed (incl. delisted).

Symbol enumeration: S3 listing of data.binance.vision (includes delisted symbols).
Kline source: fapi /fapi/v1/klines (works for most delisted symbols); fallback to
data.binance.vision monthly zips when fapi returns nothing.
"""
import io
import json
import time
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests

S3 = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
PREFIX = "data/futures/um/daily/klines/"
FAPI = "https://fapi.binance.com/fapi/v1/klines"
OUT = Path("data/xsect/klines")
START_MS = int(pd.Timestamp("2019-09-01", tz="UTC").timestamp() * 1000)
END_MS = int(pd.Timestamp("2026-07-02", tz="UTC").timestamp() * 1000)


def list_all_symbols() -> list[str]:
    symbols, marker = [], None
    while True:
        params = {"delimiter": "/", "prefix": PREFIX}
        if marker:
            params["marker"] = marker
        r = requests.get(S3, params=params, timeout=30)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        ns = {"s3": root.tag.split("}")[0].strip("{")}
        prefixes = [p.find("s3:Prefix", ns).text for p in root.findall("s3:CommonPrefixes", ns)]
        symbols += [p[len(PREFIX):].strip("/") for p in prefixes]
        if root.find("s3:IsTruncated", ns) is not None and root.find("s3:IsTruncated", ns).text == "true":
            marker = prefixes[-1]
        else:
            break
    return sorted(s for s in symbols if s.endswith("USDT"))


def fetch_fapi(symbol: str) -> pd.DataFrame:
    rows, start = [], START_MS
    while True:
        r = requests.get(FAPI, params={"symbol": symbol, "interval": "1d",
                                        "startTime": start, "endTime": END_MS, "limit": 1500},
                         timeout=30)
        if r.status_code != 200:
            break
        batch = r.json()
        if not batch:
            break
        rows += batch
        if len(batch) < 1500:
            break
        start = batch[-1][0] + 86_400_000
        time.sleep(0.15)
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows, columns=["open_time", "open", "high", "low", "close", "volume",
                                     "close_time", "quote_volume", "n", "tbv", "tbqv", "x"])
    df["ts"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    out = df.set_index("ts")[["open", "high", "low", "close", "quote_volume"]].astype(float)
    return out[~out.index.duplicated(keep="first")].sort_index()


def fetch_vision_monthly(symbol: str) -> pd.DataFrame:
    """Fallback: iterate monthly zips 2019-09..2026-06 for delisted symbols fapi refuses."""
    frames = []
    for month in pd.period_range("2019-09", "2026-06", freq="M"):
        url = (f"https://data.binance.vision/data/futures/um/monthly/klines/"
               f"{symbol}/1d/{symbol}-1d-{month}.zip")
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            continue
        with zipfile.ZipFile(io.BytesIO(r.content)) as z:
            raw = pd.read_csv(z.open(z.namelist()[0]), header=None)
        if isinstance(raw.iloc[0, 0], str) and not str(raw.iloc[0, 0]).isdigit():
            raw = raw.iloc[1:].reset_index(drop=True)  # some months ship with header row
        raw.columns = ["open_time", "open", "high", "low", "close", "volume", "close_time",
                       "quote_volume", "n", "tbv", "tbqv", "x"][: raw.shape[1]]
        frames.append(raw)
        time.sleep(0.1)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames)
    ts = pd.to_numeric(df["open_time"])
    # vision switched to microseconds in 2025 — normalize to ms
    ts = ts.where(ts < 10**14, ts // 1000)
    df["ts"] = pd.to_datetime(ts, unit="ms", utc=True)
    out = df.set_index("ts")[["open", "high", "low", "close", "quote_volume"]].astype(float)
    return out[~out.index.duplicated(keep="first")].sort_index()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    symbols = list_all_symbols()
    print(f"{len(symbols)} USDT symbols enumerated (incl. delisted)")
    for i, sym in enumerate(symbols):
        path = OUT / f"{sym}.parquet"
        if path.exists():
            df = pd.read_parquet(path)
        else:
            df = fetch_fapi(sym)
            if df.empty:
                df = fetch_vision_monthly(sym)
            if df.empty:
                print(f"  {sym}: NO DATA (skipped)")
                continue
            df.to_parquet(path)
        manifest[sym] = {"first": str(df.index.min()), "last": str(df.index.max()), "rows": len(df)}
        if i % 25 == 0:
            print(f"  [{i}/{len(symbols)}] {sym}: {len(df)} rows")
    json.dump(manifest, open("data/xsect/klines_manifest.json", "w"), indent=1)
    print(f"done: {len(manifest)} symbols stored")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it** (`.venv/bin/python scripts/fetch_xsect_klines.py`, ~20-60 min). Expected: 300+ symbols stored.

- [ ] **Step 3: SURVIVORSHIP VERIFICATION (hard gate)**

```bash
.venv/bin/python - <<'EOF'
import json
m = json.load(open("data/xsect/klines_manifest.json"))
for s in ["LUNAUSDT", "FTTUSDT", "BTCUSDT", "ETHUSDT"]:
    print(s, m.get(s, "MISSING"))
assert "LUNAUSDT" in m and "FTTUSDT" in m, "SURVIVORSHIP GATE FAILED"
assert m["LUNAUSDT"]["last"] < "2022-06", "LUNA data should end near May-2022 delisting"
print("survivorship gate PASS,", len(m), "symbols")
EOF
```

If LUNA/FTT missing after both sources: STOP, report BLOCKED (do not proceed with a survivors-only universe).

- [ ] **Step 4: Commit** (parquets are data assets — commit manifest + script; store parquets with `git add -f data/xsect/klines` ONLY if repo policy allows large data (check .gitignore for data/); if data/ is committed elsewhere in repo (it is — data/derivatives/*.parquet are tracked), commit them):

```bash
git add scripts/fetch_xsect_klines.py data/xsect/klines_manifest.json
git add data/xsect/klines/*.parquet
git commit -m "data(xsect): bulk daily klines, all USDT perps ever listed (survivorship-safe)"
```

---

### Task 2: PIT universe builder (`tradingagents/xsect/universe.py`)

**Files:**
- Create: `tradingagents/xsect/__init__.py` (empty), `tradingagents/xsect/universe.py`
- Test: `tests/test_xsect_universe.py`

**Interfaces:**
- Consumes: `data/xsect/klines/*.parquet`.
- Produces:
  - `load_klines(kline_dir: Path) -> dict[str, pd.DataFrame]` (all symbols).
  - `eligibility(klines: dict, date: pd.Timestamp, min_age_days: int = 30, min_mvol: float = 5e6, top_n: int = 100) -> list[str]` — symbols with a kline ON `date`, first kline ≤ date−30d, 30d median quote_volume (window ending at `date`, inclusive) ≥ min_mvol; ranked by that median, top_n kept.
  - `weekly_rebalance_dates(start: str, end: str) -> pd.DatetimeIndex` — all Mondays in [start, end], tz UTC.

- [ ] **Step 1: Failing tests**

```python
# tests/test_xsect_universe.py
import numpy as np
import pandas as pd
from tradingagents.xsect.universe import eligibility, weekly_rebalance_dates


def _kl(first, last, qv=1e7):
    idx = pd.date_range(first, last, freq="D", tz="UTC")
    return pd.DataFrame({"open": 1.0, "high": 1.0, "low": 1.0, "close": 1.0,
                         "quote_volume": qv}, index=idx)


def test_age_filter():
    kl = {"OLD": _kl("2021-01-01", "2021-12-31"), "NEW": _kl("2021-11-20", "2021-12-31")}
    d = pd.Timestamp("2021-12-06", tz="UTC")
    assert eligibility(kl, d) == ["OLD"]  # NEW is 16 days old


def test_volume_filter_and_ranking():
    kl = {"BIG": _kl("2021-01-01", "2021-12-31", qv=2e7),
          "MID": _kl("2021-01-01", "2021-12-31", qv=1e7),
          "DUST": _kl("2021-01-01", "2021-12-31", qv=1e5)}
    d = pd.Timestamp("2021-06-07", tz="UTC")
    got = eligibility(kl, d, top_n=2)
    assert got == ["BIG", "MID"]  # DUST fails $5M floor; ranked by volume


def test_delisted_symbol_leaves_universe():
    kl = {"DEAD": _kl("2021-01-01", "2021-06-01"), "LIVE": _kl("2021-01-01", "2021-12-31")}
    assert "DEAD" in eligibility(kl, pd.Timestamp("2021-05-03", tz="UTC"))
    assert "DEAD" not in eligibility(kl, pd.Timestamp("2021-06-07", tz="UTC"))


def test_weekly_mondays():
    dates = weekly_rebalance_dates("2021-01-01", "2021-01-31")
    assert all(d.dayofweek == 0 for d in dates)
    assert str(dates[0].date()) == "2021-01-04"
```

- [ ] **Step 2: Run, expect import failure** (`pytest tests/test_xsect_universe.py -v`).

- [ ] **Step 3: Implement**

```python
# tradingagents/xsect/universe.py
"""PIT universe: eligibility from raw kline availability (incl. delisted symbols)."""
from pathlib import Path

import pandas as pd


def load_klines(kline_dir: Path) -> dict[str, pd.DataFrame]:
    return {p.stem: pd.read_parquet(p) for p in sorted(Path(kline_dir).glob("*.parquet"))}


def eligibility(klines: dict, date: pd.Timestamp, min_age_days: int = 30,
                min_mvol: float = 5e6, top_n: int = 100) -> list[str]:
    scored = []
    for sym, df in klines.items():
        if date not in df.index:
            continue
        if df.index[0] > date - pd.Timedelta(days=min_age_days):
            continue
        window = df.loc[:date].tail(30)["quote_volume"]
        mvol = float(window.median())
        if mvol >= min_mvol:
            scored.append((sym, mvol))
    scored.sort(key=lambda x: (-x[1], x[0]))
    return [s for s, _ in scored[:top_n]]


def weekly_rebalance_dates(start: str, end: str) -> pd.DatetimeIndex:
    days = pd.date_range(start, end, freq="D", tz="UTC")
    return days[days.dayofweek == 0]
```

- [ ] **Step 4: Run, expect 4 passed.**

- [ ] **Step 5: Commit** (`git add tradingagents/xsect/ tests/test_xsect_universe.py`, message `feat(xsect): PIT universe eligibility from kline availability`).

---

### Task 3: Weekly portfolio engine + bootstrap + placebo (`tradingagents/xsect/portfolio.py`)

**Files:**
- Create: `tradingagents/xsect/portfolio.py`
- Test: `tests/test_xsect_portfolio.py`

**Interfaces:**
- Consumes: klines dict, eligibility(), weekly_rebalance_dates().
- Produces:
  - `momentum_scores(klines, symbols, date, L, skip) -> dict[str, float]` — sum of daily log-returns over the L days ending `skip` days before `date` (window (date−skip−L, date−skip]); NaN-score symbols dropped.
  - `run_weekly_portfolio(klines, rebalance_dates, select_fn, cost_bps=10.0) -> pd.Series` — daily log-return series. Mechanics: at each rebalance date t (Monday, using close t), target = EW over `select_fn(t)` (list of symbols); positions apply from bar t+1; daily portfolio log-return = mean of members' close-to-close log-returns; costs: `cost_bps/1e4 * turnover` deducted on the first accrual day after each rebalance, turnover = 0.5 * Σ|w_new − w_old| ∈ [0,1] scaled ×2 legs (i.e. total one-side turnover; document formula in docstring: cost = cost_bps/1e4 * 2 * turnover_oneside... SIMPLIFY: cost = cost_bps/1e4 * Σ|w_new − w_old| — per-side rate times per-side turnover summed over both sides of each trade); a member delisted mid-week contributes its last available return then weight redistributes at next rebalance (no look-ahead).
  - `sr(returns) -> float` (√365, 0.0 on zero variance); `maxdd(returns) -> float` (positive magnitude) — import from `tradingagents.stress.overlay` (`_sr`, `_maxdd`) instead of re-implementing: re-export as `sr = _sr`, `maxdd = _maxdd`.
  - `paired_bootstrap(a: pd.Series, b: pd.Series, block=21, n=2000, seed=0) -> dict` — aligned inner-join; ΔSR = sr(a)−sr(b); p_pos = fraction of resamples with Δ>0; stationary block bootstrap resampling the same index positions for both series.
  - `rank_placebo_pvalue(real_sr: float, placebo_srs: list[float]) -> float` — (1+#{placebo ≥ real})/(N+1).

- [ ] **Step 1: Failing tests**

```python
# tests/test_xsect_portfolio.py
import numpy as np
import pandas as pd
import pytest
from tradingagents.xsect.portfolio import (momentum_scores, paired_bootstrap,
                                           rank_placebo_pvalue, run_weekly_portfolio, sr)


def _kl(prices, first="2021-01-01"):
    idx = pd.date_range(first, periods=len(prices), freq="D", tz="UTC")
    p = pd.Series(prices, index=idx, dtype=float)
    return pd.DataFrame({"open": p, "high": p, "low": p, "close": p, "quote_volume": 1e7})


def test_momentum_score_window():
    # 10 flat days then +1%/day for 5 days; L=5, skip=0 at the last day => 5*log(1.01)
    prices = [100.0] * 10 + [100 * 1.01 ** i for i in range(1, 6)]
    kl = {"A": _kl(prices)}
    d = kl["A"].index[-1]
    s = momentum_scores(kl, ["A"], d, L=5, skip=0)
    assert s["A"] == pytest.approx(5 * np.log(1.01), rel=1e-9)


def test_momentum_skip_shifts_window():
    prices = [100.0] * 10 + [100 * 1.01 ** i for i in range(1, 6)]
    kl = {"A": _kl(prices)}
    d = kl["A"].index[-1]
    s1 = momentum_scores(kl, ["A"], d, L=4, skip=1)  # excludes last day
    assert s1["A"] == pytest.approx(4 * np.log(1.01), rel=1e-9)


def test_portfolio_no_lookahead():
    # coin B jumps +50% ON the rebalance Monday; selecting B at that close must NOT earn the jump
    up = [100.0] * 32 + [150.0] + [150.0] * 13
    flat = [100.0] * 46
    kl = {"B": _kl(up), "F": _kl(flat)}
    reb = pd.DatetimeIndex([kl["B"].index[32]])  # the jump day
    series = run_weekly_portfolio(kl, reb, lambda t: ["B"], cost_bps=0.0)
    assert series.loc[kl["B"].index[33]:].abs().sum() == pytest.approx(0.0)  # flat after jump
    assert kl["B"].index[32] not in series.index or series.loc[kl["B"].index[32]] == 0.0


def test_costs_deducted_once_per_rebalance():
    flat = [100.0] * 46
    kl = {"A": _kl(flat)}
    reb = pd.DatetimeIndex([kl["A"].index[10]])
    gross = run_weekly_portfolio(kl, reb, lambda t: ["A"], cost_bps=0.0)
    net = run_weekly_portfolio(kl, reb, lambda t: ["A"], cost_bps=10.0)
    diff = (gross - net).sum()
    assert diff == pytest.approx(10 / 1e4, rel=1e-6)  # one full entry, one side


def test_paired_bootstrap_direction():
    idx = pd.date_range("2021-01-01", periods=400, freq="D", tz="UTC")
    rng = np.random.default_rng(0)
    base = pd.Series(rng.normal(0, 0.01, 400), index=idx)
    better = base + 0.002
    r = paired_bootstrap(better, base, n=200, seed=1)
    assert r["delta_sr"] > 0 and r["p_pos"] > 0.95


def test_rank_placebo():
    assert rank_placebo_pvalue(2.0, [1.0] * 99) == pytest.approx(1 / 100)
    assert rank_placebo_pvalue(0.0, [1.0] * 99) == pytest.approx(1.0)
```

- [ ] **Step 2: Run, expect import failure.**

- [ ] **Step 3: Implement**

```python
# tradingagents/xsect/portfolio.py
"""Weekly EW long-only cross-sectional portfolio engine — frozen mechanics per gates.json xs_mom_p1."""
import numpy as np
import pandas as pd

from tradingagents.stress.overlay import _maxdd as maxdd  # positive magnitude
from tradingagents.stress.overlay import _sr as sr  # sqrt(365), 0.0 on zero variance


def momentum_scores(klines: dict, symbols: list, date: pd.Timestamp,
                    L: int, skip: int) -> dict:
    out = {}
    for s in symbols:
        close = klines[s]["close"].loc[:date]
        if skip:
            close = close.iloc[:-skip] if len(close) > skip else close.iloc[:0]
        if len(close) < L + 1:
            continue
        window = np.log(close.iloc[-(L + 1):]).diff().dropna()
        if len(window) == L:
            out[s] = float(window.sum())
    return out


def run_weekly_portfolio(klines: dict, rebalance_dates: pd.DatetimeIndex,
                         select_fn, cost_bps: float = 10.0) -> pd.Series:
    logret = {s: np.log(df["close"]).diff() for s, df in klines.items()}
    all_days = sorted(set().union(*[df.index for df in klines.values()]))
    all_days = pd.DatetimeIndex(all_days)
    port = pd.Series(0.0, index=all_days)
    weights: dict = {}
    pending_cost = 0.0
    reb = set(rebalance_dates)
    for day in all_days:
        if weights:
            rets = [logret[s].get(day) for s in weights]
            rets = [r for r in rets if r is not None and not np.isnan(r)]
            port.loc[day] = float(np.mean(rets)) if rets else 0.0
        if pending_cost and weights:
            port.loc[day] -= pending_cost
            pending_cost = 0.0
        if day in reb:
            members = select_fn(day)
            new_w = {s: 1.0 / len(members) for s in members} if members else {}
            keys = set(new_w) | set(weights)
            turnover = sum(abs(new_w.get(k, 0.0) - weights.get(k, 0.0)) for k in keys)
            pending_cost = cost_bps / 1e4 * turnover
            weights = new_w
    start = rebalance_dates[0] if len(rebalance_dates) else all_days[0]
    return port.loc[port.index > start]


def _stationary_indices(n: int, block: int, rng) -> np.ndarray:
    idx = np.empty(n, dtype=int)
    i = 0
    while i < n:
        length = min(rng.geometric(1.0 / block), n - i)
        start = rng.integers(0, n)
        idx[i:i + length] = (start + np.arange(length)) % n
        i += length
    return idx


def paired_bootstrap(a: pd.Series, b: pd.Series, block: int = 21,
                     n: int = 2000, seed: int = 0) -> dict:
    j = pd.concat([a, b], axis=1, join="inner").dropna()
    av, bv = j.iloc[:, 0].to_numpy(), j.iloc[:, 1].to_numpy()
    rng = np.random.default_rng(seed)
    deltas = np.empty(n)
    for k in range(n):
        ix = _stationary_indices(len(av), block, rng)
        deltas[k] = _np_sr(av[ix]) - _np_sr(bv[ix])
    return {"delta_sr": sr(j.iloc[:, 0]) - sr(j.iloc[:, 1]),
            "p_pos": float((deltas > 0).mean())}


def _np_sr(x: np.ndarray) -> float:
    sd = x.std()
    return 0.0 if sd == 0 or np.isnan(sd) else float(x.mean() / sd * np.sqrt(365))


def rank_placebo_pvalue(real_sr: float, placebo_srs: list) -> float:
    ge = sum(1 for p in placebo_srs if p >= real_sr)
    return (1 + ge) / (len(placebo_srs) + 1)
```

- [ ] **Step 4: Run, expect 6 passed.** Then full stress+xsect suites for regressions.

- [ ] **Step 5: Commit** (`feat(xsect): weekly EW portfolio engine + paired bootstrap + rank placebo`).

---

### Task 4: P1 dev grid runner (`scripts/xs_mom_dev.py`)

**Files:**
- Create: `scripts/xs_mom_dev.py`
- Output: `data/rebuild/xs_mom/dev_results.json`

**Interfaces:**
- Consumes: Tasks 1-3 + `log_trial` + DSR (`tradingagents/strategies/v3/backtest/dsr.py` — same implementation the rebuild used; check exact function signature before use: `grep -n "def " tradingagents/strategies/v3/backtest/dsr.py`).
- Produces: per-config record {config, net metrics, delta vs benchmark, p_pos, placebo_p, dsr}, benchmark record, `selected` per frozen gate.

- [ ] **Step 1: Write runner.** Structure (complete the DSR import per the grep; everything else verbatim):

```python
# scripts/xs_mom_dev.py
"""P1 dev grid: 12 pre-registered configs vs EW-universe benchmark. Ledger: xs_mom_p1."""
import json
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tradingagents.rebuild.ledger import log_trial, trial_count
from tradingagents.xsect.portfolio import (momentum_scores, paired_bootstrap, maxdd,
                                           rank_placebo_pvalue, run_weekly_portfolio, sr)
from tradingagents.xsect.universe import eligibility, load_klines, weekly_rebalance_dates

DEV = ("2021-01-01", "2025-03-31")
GRID = list(product([7, 14, 28], [0, 1], [10, 20]))  # L, skip, K — frozen, 12 configs
GATE = {"net_sr_min": 0.8, "delta_sr_vs_benchmark_min": 0.0, "p_pos_min": 0.85,
        "placebo_p_max": 0.05, "dsr_min": 0.9}
OUT = Path("data/rebuild/xs_mom")
N_PLACEBO = 500

klines = load_klines(Path("data/xsect/klines"))
reb = weekly_rebalance_dates(*DEV)
lo, hi = pd.Timestamp(DEV[0], tz="UTC"), pd.Timestamp(DEV[1], tz="UTC")

# benchmark: EW full eligible universe
bench = run_weekly_portfolio(klines, reb, lambda t: eligibility(klines, t)).loc[:hi]

results = []
for L, skip, K in GRID:
    def select(t, L=L, skip=skip, K=K):
        elig = eligibility(klines, t)
        scores = momentum_scores(klines, elig, t, L, skip)
        return [s for s, _ in sorted(scores.items(), key=lambda kv: -kv[1])[:K]]
    series = run_weekly_portfolio(klines, reb, select).loc[:hi]
    real_sr = sr(series)
    pb = paired_bootstrap(series, bench)
    rng = np.random.default_rng(0)
    placebo_srs = []
    for p in range(N_PLACEBO):
        def pselect(t, L=L, skip=skip, K=K, rng=rng):
            elig = eligibility(klines, t)
            scores = momentum_scores(klines, elig, t, L, skip)
            syms = list(scores)
            rng.shuffle(syms)
            return syms[:K]
        placebo_srs.append(sr(run_weekly_portfolio(klines, reb, pselect).loc[:hi]))
    placebo_p = rank_placebo_pvalue(real_sr, placebo_srs)
    cfg = {"L": L, "skip": skip, "K": K, "cost_bps": 10.0, "top_n": 100, "min_mvol": 5e6}
    metrics = {"net_sr": real_sr, "maxdd": maxdd(series), "total_logret": float(series.sum()),
               "bench_sr": sr(bench), "delta_sr": pb["delta_sr"], "p_pos": pb["p_pos"],
               "placebo_p": placebo_p, "n_days": len(series)}
    log_trial("xs_mom_p1", cfg, DEV, metrics)
    results.append({"config": cfg, "metrics": metrics})
    print(f"L={L} skip={skip} K={K}: SR={real_sr:.2f} dSR={pb['delta_sr']:+.2f} "
          f"p_pos={pb['p_pos']:.2f} placebo_p={placebo_p:.3f}")

# DSR with n_trials = unique config hashes in ledger (compute after all runs)
# <implementer: import the same DSR used by scripts/validate_v5_mix.py; grep first>
from tradingagents.strategies.v3.backtest.dsr import deflated_sharpe_ratio  # verify name!
n_trials = trial_count(unique=True) if "unique" in trial_count.__code__.co_varnames else trial_count()
for r in results:
    s = r["metrics"]["net_sr"]
    r["metrics"]["dsr"] = float(deflated_sharpe_ratio(  # adapt args to actual signature
        observed_sr=s / np.sqrt(365), n_obs=r["metrics"]["n_days"], n_trials=n_trials))
    r["gate_pass"] = bool(
        r["metrics"]["net_sr"] >= GATE["net_sr_min"]
        and r["metrics"]["delta_sr"] > GATE["delta_sr_vs_benchmark_min"]
        and r["metrics"]["p_pos"] >= GATE["p_pos_min"]
        and r["metrics"]["placebo_p"] <= GATE["placebo_p_max"]
        and r["metrics"]["dsr"] >= GATE["dsr_min"])

passing = [r for r in results if r["gate_pass"]]
selected = max(passing, key=lambda r: (r["metrics"]["dsr"], -r["metrics"]["placebo_p"])) if passing else None
OUT.mkdir(parents=True, exist_ok=True)
json.dump({"benchmark": {"sr": sr(bench), "maxdd": maxdd(bench), "n_days": len(bench)},
           "results": results, "selected": selected, "n_trials_at_eval": n_trials},
          open(OUT / "dev_results.json", "w"), indent=1, default=str)
print("selected:", json.dumps(selected["config"]) if selected else "NONE")
```

NOTE for implementer: the 500-placebo × 12-config loop = 6000 portfolio runs; if a smoke timing of ONE run × universe-100 exceeds ~5s, memoize `eligibility` and `momentum_scores` per (t, L, skip) across placebos (scores don't change — only the ranking shuffle does), which collapses placebo cost to the portfolio accounting loop. Correctness first, then speed; do NOT reduce N_PLACEBO or the grid.

- [ ] **Step 2: Smoke-run** (`.venv/bin/python scripts/xs_mom_dev.py`, may take a while). Sanity gates: benchmark n_days ≈ 1500; benchmark SR plausible (crypto EW basket 2021-2025 likely between −0.5 and +1.5); each config n_days within 5 of benchmark. If eligibility returns < 20 symbols on 2021 Mondays or > 100 always, investigate before interpreting.

- [ ] **Step 3: Commit** code + dev_results.json + ledger (`exp(xs-mom): P1 dev grid 12 configs vs EW benchmark, ledgered`).

---

### Task 5: D1 F&G-beta module + dev run (`tradingagents/xsect/fgbeta.py`, `scripts/fg_beta_dev.py`)

**Files:**
- Create: `tradingagents/xsect/fgbeta.py`, `scripts/fg_beta_dev.py`
- Test: `tests/test_xsect_fgbeta.py`
- Output: `data/rebuild/fg_beta/dev_results.json`

**Interfaces:**
- Consumes: F&G store `data/sentiment/fng/fng.parquet` (cols event_ts, value — same as stress index), klines, portfolio engine, P1 `dev_results.json` selected config (may be None).
- Produces: `fg_beta(klines, fng_daily: pd.Series, symbols, date, window=90, min_obs=60) -> dict[str, float]` — rolling OLS beta of coin daily log-returns on ΔF&G, both shifted so only data ≤ date−1 used (shift(1) then window ending at date); `middle_quintile(betas: dict) -> list[str]`; `exclude_extreme_quintiles(betas: dict, members: list[str]) -> list[str]`.

- [ ] **Step 1: Failing tests**

```python
# tests/test_xsect_fgbeta.py
import numpy as np
import pandas as pd
import pytest
from tradingagents.xsect.fgbeta import exclude_extreme_quintiles, fg_beta, middle_quintile


def _mk(n=200, seed=0, beta=0.0):
    idx = pd.date_range("2021-01-01", periods=n, freq="D", tz="UTC")
    rng = np.random.default_rng(seed)
    dfg = pd.Series(rng.normal(0, 5, n), index=idx)
    noise = rng.normal(0, 0.001, n)
    ret = beta * dfg / 100.0 + noise
    price = 100 * np.exp(np.cumsum(ret))
    kl = pd.DataFrame({"open": price, "high": price, "low": price, "close": price,
                       "quote_volume": 1e7}, index=idx)
    fng = 50 + dfg.cumsum().clip(-45, 45)
    return kl, fng


def test_beta_recovers_sign_and_causality():
    kl, fng = _mk(beta=2.0)
    d = kl.index[-1]
    b = fg_beta({"A": kl}, fng, ["A"], d)
    assert b["A"] > 0.5  # strongly positive beta recovered
    # causality: changing the last day's fng/price must not change beta at d... 
    kl2 = kl.copy(); kl2.iloc[-1, kl2.columns.get_loc("close")] *= 2.0
    fng2 = fng.copy(); fng2.iloc[-1] = 90.0
    b2 = fg_beta({"A": kl2}, fng2, ["A"], d)
    assert b2["A"] == pytest.approx(b["A"], rel=1e-9)


def test_min_obs_gate():
    kl, fng = _mk(n=50)
    assert fg_beta({"A": kl}, fng, ["A"], kl.index[-1]) == {}


def test_quintile_helpers():
    betas = {f"S{i}": float(i) for i in range(10)}  # 0..9
    mid = middle_quintile(betas)
    assert mid == ["S4", "S5"]
    kept = exclude_extreme_quintiles(betas, [f"S{i}" for i in range(10)])
    assert "S0" not in kept and "S9" not in kept and "S4" in kept
```

- [ ] **Step 2: Run, expect import failure.**

- [ ] **Step 3: Implement**

```python
# tradingagents/xsect/fgbeta.py
"""F&G sentiment-beta cross-sectional sort — frozen rule gates.json fg_beta_d1."""
import numpy as np
import pandas as pd


def fng_daily_series(fng_path) -> pd.Series:
    fng = pd.read_parquet(fng_path)
    s = (fng.assign(d=pd.to_datetime(fng["event_ts"], utc=True).dt.normalize())
         .set_index("d")["value"].astype(float).sort_index())
    return s[~s.index.duplicated(keep="last")]


def fg_beta(klines: dict, fng: pd.Series, symbols: list, date: pd.Timestamp,
            window: int = 90, min_obs: int = 60) -> dict:
    dfg = fng.diff().shift(1).loc[:date].tail(window)  # causal: uses fng <= date-1
    out = {}
    for s in symbols:
        ret = np.log(klines[s]["close"]).diff().shift(1).loc[:date].tail(window)
        j = pd.concat([ret, dfg], axis=1, join="inner").dropna()
        if len(j) < min_obs:
            continue
        x, y = j.iloc[:, 1].to_numpy(), j.iloc[:, 0].to_numpy()
        vx = x.var()
        if vx == 0:
            continue
        out[s] = float(((x - x.mean()) * (y - y.mean())).mean() / vx)
    return out


def _quintile_bounds(betas: dict):
    vals = np.array(sorted(betas.values()))
    return np.quantile(vals, 0.4), np.quantile(vals, 0.6), np.quantile(vals, 0.2), np.quantile(vals, 0.8)


def middle_quintile(betas: dict) -> list:
    if not betas:
        return []
    q40, q60, _, _ = _quintile_bounds(betas)
    return sorted([s for s, b in betas.items() if q40 <= b <= q60])


def exclude_extreme_quintiles(betas: dict, members: list) -> list:
    if not betas:
        return list(members)
    _, _, q20, q80 = _quintile_bounds(betas)
    return [s for s in members if s in betas and q20 < betas[s] < q80]
```

- [ ] **Step 4: Run tests → pass. Commit module+tests** (`feat(xsect): F&G sentiment-beta sort (causal rolling OLS)`).

- [ ] **Step 5: Write + run `scripts/fg_beta_dev.py`** — same runner pattern as Task 4: config (a) standalone middle-quintile portfolio (select_fn: eligibility → fg_beta → middle_quintile), judged vs the SAME benchmark with the standalone gate incl. DSR and 500 rank placebos (shuffle beta ranks); config (b) ONLY if P1 selected a config: P1-winner select_fn wrapped with exclude_extreme_quintiles, judged paired vs P1 winner series (delta_sr > 0, p_pos ≥ 0.85, no placebo/DSR per frozen gate). Ledger experiment="fg_beta_d1" (2 rows max). Output `data/rebuild/fg_beta/dev_results.json` with per-config gate verdicts + `selected`. Commit (`exp(fg-beta): D1 dev run (standalone + overlay), ledgered`).

---

### Task 6: Holdout one-shot(s) (`scripts/xsect_holdout.py`) — ONLY for dev-gate survivors

- [ ] **Step 1:** If BOTH P1 and D1 selected NONE → skip to Task 7 (negative path; holdout unspent).
- [ ] **Step 2:** For each survivor: single execution on 2025-04-01 → 2026-07-01 with frozen config read from the respective dev_results.json (never CLI), fresh benchmark on holdout window, same metrics + 500 placebos, `log_trial(..., allow_holdout=True)`, assert-once file guard (script refuses if `data/rebuild/xs_mom/holdout_result.json` / `data/rebuild/fg_beta/holdout_result.json` exists). Gates: holdout_deploy from gates.json. Output + commit (`exp(xsect): holdout one-shot — verdict as it fell`).

---

### Task 7: THESIS section + wrap-up

- [ ] **Step 1:** Append `## Section 43: Wide-Universe Cross-Sectional Momentum (P1) + F&G Sentiment-Beta (D1)` to THESIS_FINDINGS.md: pre-registration provenance, universe construction (PIT, delisted included — name LUNA/FTT presence), benchmark, 12-config P1 table, D1 table, gate math, holdout verdicts (or unspent), interpretation limits (long-only tilt vs literature long-short; liquid-100 vs 16k-coin universe; gross-vs-net central caveat resolved empirically here), no first person. All numbers from dev_results/holdout_result JSONs.
- [ ] **Step 2:** Commit (`docs(xsect): THESIS section 43 — P1+D1 verdicts`).

---

## Self-Review

- Coverage: prereg (T0) ✓, survivorship-safe data (T1, hard gate) ✓, PIT universe (T2) ✓, engine+stats (T3) ✓, P1 grid (T4) ✓, D1 both variants (T5) ✓, one-shot holdout (T6) ✓, thesis (T7) ✓.
- Deliberate implementation-time lookups: DSR function name/signature (grep given); vision kline column drift (normalization included); these reference existing verified code/data, not invention.
- Type consistency: select_fn(t)->list[str] used by engine, Task 4/5 closures conform; sr/maxdd re-exported from stress overlay keep conventions identical across programs.
- Known risks accepted: fapi may refuse some delisted symbols (fallback provided; LUNA/FTT gate enforces); 6000 placebo portfolio runs may need memoization (note included); benchmark includes 100 names weekly → its own turnover costs (rule frozen; symmetric treatment).
