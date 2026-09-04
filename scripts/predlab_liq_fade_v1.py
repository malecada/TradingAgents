"""predlab_liq_fade_v1 — liq_fade_i1 frozen config on Bybit 1h (charter 2026-09-04).

  python scripts/predlab_liq_fade_v1.py register
  python scripts/predlab_liq_fade_v1.py probes    # P0, P3 (first), P1, P2 -> liq_fade_v1_probes.json
  python scripts/predlab_liq_fade_v1.py run       # refuses without passing probes; one-shot

Engine: the main worktree's tradingagents/xsect/liq_fade.py (simple returns),
loaded by file path (the predlab package has no xsect module). Placebo
families and the hourly membership mask are transcribed from the parent
scripts/liq_fade_dev.py (feature/llm-event-xs) verbatim.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT.parent / "TradingAgents"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from predlab_xfam_lib import ledger_append  # noqa: E402
from tradingagents.predlab import registry  # noqa: E402

_spec = importlib.util.spec_from_file_location("liq_fade_engine", MAIN / "tradingagents" / "xsect" / "liq_fade.py")
LF = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(LF)

KEY = "predlab_liq_fade_v1"
BYBIT = ROOT / "data" / "predlab" / "bybit"
OUT = ROOT / "data" / "predlab"
CFG = {"thr": 3.5, "H": 48, "w_per": 0.1, "cap": 1.0, "cost_bps": 10.0, "rf_annual": 0.045}
DEV = ("2021-01-01", "2025-03-31")
WARMUP = "2020-10-01"
DEV_LO = pd.Timestamp(DEV[0], tz="UTC")
DEV_HI = pd.Timestamp(DEV[1], tz="UTC") + pd.Timedelta(hours=23)
BENCH = ["2021-05-19", "2022-06-13", "2022-11-09", "2024-08-05", "2025-02-03"]
MAJORS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT", "DOGEUSDT", "XRPUSDT", "TRXUSDT"]
N_PLACEBO = 500
GATE = {"net_sr_min": 1.0, "placebo_p_max": 0.05, "top_share_max": 0.25, "ctrl_sr_max": 0.5, "separation_min": 0.75, "p2_min_ret": 0.0025, "p2_min_events": 300}

ENTRY = {
    "registered_utc": "2026-09-04", "charter": "docs/superpowers/specs/2026-09-04-liq-fade-v1-charter.md",
    "purpose": "frozen liq_fade_i1 (thr 3.5, H 48, w 0.1, cap 1.0, long-fade, 10 bp, rf 4.5%) on Bybit linear USDT perps, monthly top-50 PIT by trailing-30d median turnover, 1h; venue/universe robustness evidence (not an independent sample)",
    "parents": "liq_fade_i1 (49), liq_fade_r1 (50), combo_c1 sleeve (76), exec_pf (77)",
    "decisions_afk_grant": "Bybit; cost 10 bp for comparability (5.5 bp venue-actual reported)",
    "data": "Bybit v5 kline interval 60, 735 symbols of the daily store, dev cap 2025-03-31 (predlab_bybit_fetch_1h.py); quote volume = turnover; universe from the Bybit daily store as-is (delisting-truncation caveat applies)",
    "windows": {"dev": list(DEV), "warmup": WARMUP, "holdout": "none (H3); Binance sealed window spent (76); Bybit claims only on the F window >= 2027-01"},
    "probes": {"P0": "Bybit vs Binance 1h BTC/ETH simple returns corr > 0.99 on overlap; else STOP",
               "P3_FIRST": "vol-drift control: long 1/10 for 48 bars after hours with z_vol >= 3.5 and z_ret > -3.5 (no crash), same engine/costs; control net SR < 0.5 AND primary - control >= 0.75; else NEGATIVE-confounded (primary >= 1.0) or NEGATIVE",
               "P1": "thr 2.5 detector on the 8 majors flags >= 4/5 benchmark cascade dates",
               "P2": "mean gross forward return t+1..t+48 over dev triggers >= +0.25% with >= 300 events; else STOP"},
    "gates": {**GATE, "placebo": "dual family A per-symbol circular trigger shift >= 24 bars, B count-matched uniform redraw within membership; 500 draws each; worse p", "cost_stress": "20 bp keeps sign", "convention_swap": "log booking keeps sign", "dsr": "n=1 confirmatory (frozen config, new venue) + cumulative reported"},
    "reported": ["5.5 bp venue-actual cost", "per-year SR", "events per year", "DSR cumulative"],
    "stop_rule": "any probe/gate FAIL => does not replicate on Bybit (or NEGATIVE-confounded per P3); no re-tuning; one-shot", "thesis_section": "87",
}


# ── transcribed from the parent scripts/liq_fade_dev.py ──────────────────────

def membership_mask_hourly(universe: dict, columns: list[str], index: pd.DatetimeIndex) -> pd.DataFrame:
    keys = sorted(universe.keys())
    starts = [pd.Timestamp(k, tz="UTC") for k in keys]
    mask = pd.DataFrame(False, index=index, columns=columns)
    for i, (k, start) in enumerate(zip(keys, starts)):
        end = starts[i + 1] if i + 1 < len(starts) else (index[-1] + pd.Timedelta(hours=1) if len(index) else start)
        members = [s for s in universe[k] if s in columns]
        if not members:
            continue
        sel = (index >= start) & (index < end)
        if sel.any():
            mask.loc[sel, members] = True
    return mask


def _shift_triggers(trig: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    n = len(trig)
    out = {}
    for col in trig.columns:
        k = int(rng.integers(24, n - 24 + 1))
        out[col] = np.roll(trig[col].to_numpy(), k)
    return pd.DataFrame(out, index=trig.index, columns=trig.columns)


def _redraw_random_triggers(trig: pd.DataFrame, mask: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    T, M = trig.to_numpy(), mask.to_numpy()
    out = np.zeros_like(T)
    for j in range(T.shape[1]):
        n_ev = int(T[:, j].sum())
        if n_ev == 0:
            continue
        eligible = np.nonzero(M[:, j])[0]
        pick = rng.choice(eligible, size=n_ev, replace=False)
        out[pick, j] = True
    return pd.DataFrame(out, index=trig.index, columns=trig.columns)


# ── data ─────────────────────────────────────────────────────────────────────

def load_daily() -> dict:
    out = {}
    for p in sorted((BYBIT / "klines").glob("*.parquet")):
        d = pd.read_parquet(p)
        if len(d) == 0:
            continue
        out[p.stem] = d.rename(columns={"turnover": "quote_volume"})
    return out


def load_hourly(symbols: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    lo, hi = pd.Timestamp(WARMUP, tz="UTC"), DEV_HI
    idx = pd.date_range(lo, hi, freq="h")
    close, qvol = {}, {}
    for s in symbols:
        p = BYBIT / "klines_1h" / f"{s}.parquet"
        if not p.exists():
            continue
        d = pd.read_parquet(p)
        d = d.loc[(d.index >= lo) & (d.index <= hi)]
        if d.empty:
            continue
        close[s] = d["close"].reindex(idx)
        qvol[s] = d["turnover"].reindex(idx)
    cols = sorted(close)
    return pd.DataFrame(close, index=idx)[cols], pd.DataFrame(qvol, index=idx)[cols]


def build() -> dict:
    daily = load_daily()
    universe = LF.monthly_top_n(daily, DEV[0], DEV[1], n=50, lookback=30, min_age_days=60)
    universe = {str(k.date()): v for k, v in universe.items()}
    syms = sorted({s for v in universe.values() for s in v})
    close, qvol = load_hourly(syms)
    mask = membership_mask_hourly(universe, close.columns.tolist(), close.index)
    R = close.pct_change(fill_method=None)
    row = (close.index >= DEV_LO) & (close.index <= DEV_HI)
    r_log = np.log(close).diff()
    z_ret = LF._roll_z(r_log, 2160, 1440)
    z_vol = LF._roll_z(np.log1p(qvol), 2160, 1440)
    trig = ((z_ret <= -CFG["thr"]) & (z_vol >= CFG["thr"]) & mask).loc[row]
    ctrl = ((z_vol >= CFG["thr"]) & (z_ret > -CFG["thr"]) & mask).loc[row]
    active = trig.columns[(trig | ctrl).to_numpy().any(axis=0)].tolist()
    return {"universe": universe, "close": close.loc[row, active], "R": R.loc[row, active], "mask": mask.loc[row, active],
            "trig": trig[active], "ctrl": ctrl[active], "z_close_all": close, "z_qvol_all": qvol, "n_universe_syms": len(syms),
            "breadth": {k: len(v) for k, v in universe.items()}}


def net_of(trig: pd.DataFrame, R: pd.DataFrame, cost_bps: float = CFG["cost_bps"], log_booking: bool = False) -> pd.Series:
    W = LF.event_weights_hourly(trig, CFG["H"], w_per=CFG["w_per"], cap=CFG["cap"])
    Rb = np.log1p(R) if log_booking else R
    return LF.run_hourly_portfolio(W, Rb, cost_bps=cost_bps, rf_annual=CFG["rf_annual"])


def main_register() -> None:
    gates = registry.load_gates()
    if KEY in gates:
        raise SystemExit("already registered")
    gates[KEY] = ENTRY
    registry.gates_path().write_text(json.dumps(gates, indent=1))
    print(f"gates.json['{KEY}'] written")


def main_probes() -> None:
    t0 = time.time()
    b = build()
    print(f"universe {b['n_universe_syms']} syms, active {b['trig'].shape[1]}, breadth median {np.median(list(b['breadth'].values()))} ({time.time()-t0:.0f}s)", flush=True)
    # P0 stamp reconciliation vs Binance 1h
    p0 = {}
    for s in ("BTCUSDT", "ETHUSDT"):
        bin_c = pd.read_parquet(MAIN / "data" / "xsect" / "klines_1h" / f"{s}.parquet")["close"]
        byb_c = b["z_close_all"][s] if s in b["z_close_all"].columns else pd.read_parquet(BYBIT / "klines_1h" / f"{s}.parquet")["close"]
        j = pd.concat([bin_c.pct_change(fill_method=None).rename("bin"), byb_c.pct_change(fill_method=None).rename("byb")], axis=1).dropna()
        j = j[(j.index >= DEV_LO) & (j.index <= DEV_HI)]
        p0[s] = {"corr": float(j.corr().iloc[0, 1]), "n": int(len(j))}
    p0["pass"] = bool(all(v["corr"] > 0.99 for k, v in p0.items() if k != "pass"))
    print(f"P0 {p0}", flush=True)
    # P3 FIRST: vol-drift control
    net_primary = net_of(b["trig"], b["R"])
    net_ctrl = net_of(b["ctrl"], b["R"])
    sr_p, sr_c = LF.sharpe_daily(net_primary), LF.sharpe_daily(net_ctrl)
    p3 = {"primary_net_sr": sr_p, "control_net_sr": sr_c, "separation": sr_p - sr_c,
          "n_events_primary": int(b["trig"].to_numpy().sum()), "n_events_control": int(b["ctrl"].to_numpy().sum()),
          "pass": bool(sr_c < GATE["ctrl_sr_max"] and (sr_p - sr_c) >= GATE["separation_min"]),
          "label_if_fail": ("NEGATIVE-confounded" if sr_p >= GATE["net_sr_min"] else "NEGATIVE")}
    print(f"P3 primary {sr_p:+.3f} control {sr_c:+.3f} sep {sr_p-sr_c:+.3f} pass={p3['pass']}", flush=True)
    # P1 detector concordance (thr 2.5) on the majors
    flagged = {d: [] for d in BENCH}
    used = []
    for s in MAJORS:
        if s not in b["z_close_all"].columns:
            continue
        c, q = b["z_close_all"][[s]], b["z_qvol_all"][[s]]
        tr = LF.cascade_triggers(c, q, thr=2.5)[s]
        tr = tr[(tr.index >= DEV_LO) & (tr.index <= DEV_HI)]
        day = tr.groupby(tr.index.normalize()).any()
        used.append(s)
        for d in BENCH:
            ts = pd.Timestamp(d, tz="UTC")
            if ts in day.index and bool(day.loc[ts]):
                flagged[d].append(s)
    p1 = {"coins_used": used, "matched": {d: v for d, v in flagged.items()}, "n_matched": sum(1 for v in flagged.values() if v),
          "pass": bool(sum(1 for v in flagged.values() if v) >= 4)}
    print(f"P1 matched {p1['n_matched']}/5", flush=True)
    # P2 gross event floor
    fwd = b["R"].rolling(CFG["H"], min_periods=CFG["H"]).sum().shift(-CFG["H"])
    vals = fwd.to_numpy()[b["trig"].to_numpy()]
    vals = vals[~np.isnan(vals)]
    p2 = {"n_events": int(b["trig"].to_numpy().sum()), "n_with_full_window": int(len(vals)), "mean_fwd_ret": float(vals.mean()) if len(vals) else None,
          "pass": bool(len(vals) >= GATE["p2_min_events"] and vals.mean() >= GATE["p2_min_ret"])}
    print(f"P2 events {p2['n_events']} mean fwd {p2['mean_fwd_ret']} pass={p2['pass']}", flush=True)
    payload = {"ts_utc": pd.Timestamp.utcnow().isoformat(), "p0": p0, "p3": p3, "p1": p1, "p2": p2,
               "breadth": b["breadth"], "stop": not (p0["pass"] and p3["pass"] and p1["pass"] and p2["pass"]),
               "runtime_sec": time.time() - t0}
    (OUT / "liq_fade_v1_probes.json").write_text(json.dumps(payload, indent=1, default=str))
    print("STOP" if payload["stop"] else "PROBES PASS", flush=True)


def main_run() -> None:
    gates = registry.load_gates()
    if gates[KEY].get("verdicts"):
        raise SystemExit("REFUSED: verdicts already recorded (one-shot)")
    probes = json.loads((OUT / "liq_fade_v1_probes.json").read_text())
    if probes["stop"]:
        raise SystemExit("probes STOP -- refusing the run")
    t0 = time.time()
    b = build()
    trig, R, mask = b["trig"], b["R"], b["mask"]
    net = net_of(trig, R)
    sr = LF.sharpe_daily(net)
    sr_stress = LF.sharpe_daily(net_of(trig, R, cost_bps=20.0))
    sr_venue = LF.sharpe_daily(net_of(trig, R, cost_bps=5.5))
    sr_log = LF.sharpe_daily(net_of(trig, R, log_booking=True))
    W = LF.event_weights_hourly(trig, CFG["H"], w_per=CFG["w_per"], cap=CFG["cap"])
    gp = (W * R.fillna(0.0)).sum(axis=0)
    top_share = float(gp.abs().max() / gp.abs().sum()) if gp.abs().sum() > 0 else float("nan")
    print(f"real SR {sr:+.3f} stress20 {sr_stress:+.3f} venue5.5 {sr_venue:+.3f} log {sr_log:+.3f} top {top_share:.3f} ({time.time()-t0:.0f}s)", flush=True)
    rng = np.random.default_rng(48)
    srA = [LF.sharpe_daily(net_of(_shift_triggers(trig, rng), R)) for _ in range(N_PLACEBO)]
    srB = [LF.sharpe_daily(net_of(_redraw_random_triggers(trig, mask, rng), R)) for _ in range(N_PLACEBO)]
    pA = (1 + sum(1 for x in srA if x >= sr)) / (N_PLACEBO + 1)
    pB = (1 + sum(1 for x in srB if x >= sr)) / (N_PLACEBO + 1)
    p_worse = max(pA, pB)
    yearly = {str(y): LF.sharpe_daily(g) for y, g in net.groupby(net.index.year)}
    ev_year = trig.groupby(trig.index.year).sum().sum(axis=1).to_dict()
    from tradingagents.strategies.v3.backtest.dsr import deflated_sharpe_ratio, expected_max_sharpe, variance_of_sr
    def dsr(n):
        x = net.to_numpy()
        if x.std(ddof=1) <= 0:
            return float("nan")
        v = variance_of_sr(x)
        try:
            return float(deflated_sharpe_ratio(float(x.mean() / x.std(ddof=1)), expected_max_sharpe(n, v), float(np.sqrt(v))))
        except ValueError:
            return float("nan")
    n_cum = registry.trial_count() + 1
    g = {"net_sr": bool(sr >= GATE["net_sr_min"]), "placebo": bool(p_worse <= GATE["placebo_p_max"]),
         "cost_stress_sign": bool(np.sign(sr_stress) == np.sign(sr) and sr != 0), "top_share": bool(top_share <= GATE["top_share_max"]),
         "convention_swap_sign": bool(np.sign(sr_log) == np.sign(sr) and sr != 0)}
    verdict = "PASS" if all(g.values()) else "FAIL"
    metrics = {"net_sr": sr, "sr_stress_20bp": sr_stress, "sr_venue_5p5bp": sr_venue, "sr_logbooking": sr_log, "top_share": top_share,
               "placebo_pA": pA, "placebo_pB": pB, "placebo_p_worse": p_worse, "dsr_n1": dsr(1), "dsr_cumulative": dsr(n_cum), "n_trials_cumulative": n_cum,
               "n_events": int(trig.to_numpy().sum()), "n_days": int(len(net)), "maxdd": float((1 - (1 + net).cumprod() / (1 + net).cumprod().cummax()).max())}
    ledger_append(KEY, "dev_frozen", "liq_fade_i1_bybit", CFG, metrics)
    payload = {"ts_utc": pd.Timestamp.utcnow().isoformat(), "config": CFG, "metrics": metrics, "gates": g, "verdict": verdict,
               "yearly_sr": yearly, "events_per_year": {str(k): int(v) for k, v in ev_year.items()},
               "placebo_null": {"A_mean": float(np.mean(srA)), "A_sd": float(np.std(srA, ddof=1)), "B_mean": float(np.mean(srB)), "B_sd": float(np.std(srB, ddof=1))},
               "probes": probes, "runtime_sec": time.time() - t0}
    (OUT / "liq_fade_v1_result.json").write_text(json.dumps(payload, indent=1, default=str))
    gates = registry.load_gates()
    gates[KEY]["verdicts"] = {"dev": f"{verdict}: net SR {sr:+.3f}, placebo worse p {p_worse:.3f}, stress20 {sr_stress:+.3f}, log {sr_log:+.3f}, top share {top_share:.2f}; P3 control {probes['p3']['control_net_sr']:+.3f} sep {probes['p3']['separation']:+.3f}"}
    registry.gates_path().write_text(json.dumps(gates, indent=1))
    print(f"VERDICT {verdict} gates {g} pA {pA:.3f} pB {pB:.3f} yearly {yearly} ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    {"register": main_register, "probes": main_probes, "run": main_run}[sys.argv[1]]()
