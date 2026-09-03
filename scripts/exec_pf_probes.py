"""exec_pf blocking probes (gates.json["exec_pf"]["probes"]).

  python scripts/exec_pf_probes.py sample   # seeded P0 sample -> p0_sample.json (pre-fetch)
  python scripts/exec_pf_probes.py agg      # 1m -> hourly execution aggregates (all symbols)
  python scripts/exec_pf_probes.py p3       # data integrity (STOP)
  python scripts/exec_pf_probes.py p2       # taker parity vs parents (STOP)
  python scripts/exec_pf_probes.py p0       # tick-vs-1m calibration + spread model freeze (STOP)
  python scripts/exec_pf_probes.py p1       # unconditional adverse selection (STOP)
  python scripts/exec_pf_probes.py r0       # xfam_llg arithmetic pre-check
  python scripts/exec_pf_probes.py verdict  # assemble probes.json, STOP flag

Order of execution: sample -> (fetch) -> agg -> p3 -> p2 -> p0 -> p1 -> r0 -> verdict.
Every probe writes its own JSON under data/rebuild/exec_pf/; `verdict` refuses
to declare PASS unless every file exists and passes.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import exec_pf_common as X  # noqa: E402
from tradingagents.xsect.fills import (  # noqa: E402
    estimate_spread_rel, first_cross_minute, limit_price, passive_overlay, tick_level_fill,
)

SEED = 20260903
N_ALT_DAYS, N_BTC_DAYS, N_ETH_DAYS = 40, 10, 10
P0_TOL_PP = 0.05
P1_N = 2000
P3_MIN_AGREE = 0.995
P3_MIN_MINUTES = 55
PIN_TOL_SR = 1e-6
PIN_TOL_SERIES = 1e-9
LLG = Path("/home/malecada/master_thesis/TradingAgents-predlab/data/predlab/xfam/llg_result.json")


def _dump(name: str, obj: dict) -> None:
    X.OUT.mkdir(parents=True, exist_ok=True)
    (X.OUT / name).write_text(json.dumps(obj, indent=1, default=str))
    print(f"wrote {X.OUT / name}")


# ── sample ───────────────────────────────────────────────────────────────────

def main_sample() -> None:
    ev = json.loads(X.EVENTS_FILE.read_text())
    days = [tuple(d) for d in ev["event_symbol_days"]]
    rng = np.random.default_rng(SEED)
    pick = [days[i] for i in rng.choice(len(days), size=N_ALT_DAYS, replace=False)]
    cal = pd.date_range(X.DEV[0], X.DEV[1], freq="D")
    btc = [("BTCUSDT", str(cal[i].date())) for i in rng.choice(len(cal), size=N_BTC_DAYS, replace=False)]
    eth_cal = cal[cal >= "2021-12-01"]
    eth = [("ETHUSDT", str(eth_cal[i].date())) for i in rng.choice(len(eth_cal), size=N_ETH_DAYS, replace=False)]
    out = {"seed": SEED, "n_event_symbol_days": len(days), "days": [list(d) for d in pick + btc + eth],
           "roles": {"liq_fade_event_days": N_ALT_DAYS, "btc_days": N_BTC_DAYS, "eth_days": N_ETH_DAYS}}
    _dump("p0_sample.json", out)


# ── aggregates ───────────────────────────────────────────────────────────────

def main_agg() -> None:
    t0 = time.time()
    man = {}
    force = "--force" in sys.argv
    for i, s in enumerate(X.symbols()):
        a = X.build_agg(s, force=force)
        if a is None:
            man[s] = None
            print(f"[{i+1}] {s}: no 1m data")
            continue
        man[s] = {"first": str(a.index.min()), "last": str(a.index.max()), "rows": int(len(a)),
                  "ticks": {str(k): float(v) for k, v in
                            a["tick"].groupby(a.index.tz_convert("UTC").tz_localize(None).to_period("M")).first().items()}}
        print(f"[{i+1}] {s}: {len(a)} hours t={time.time()-t0:.0f}s", flush=True)
    _dump("agg_manifest.json", man)


# ── P3 data integrity ────────────────────────────────────────────────────────

def _r2_orders_bars() -> pd.DataFrame:
    """(ts_bar, symbol) of every parent R2 order (LTM path == parent path)."""
    r2 = X.r2_parent()
    W = r2["W"]
    dW = W.diff().fillna(W.iloc[0])
    rows = [(W.index[i], W.columns[j]) for i, j in zip(*np.nonzero(dW.to_numpy() != 0))]
    return pd.DataFrame(rows, columns=["ts_bar", "symbol"])


def main_p3() -> None:
    syms = X.symbols()
    idx = pd.date_range(X.DEV_LO, X.DEV_HI, freq="h")
    agg = X.load_agg_panel(syms, idx)
    per = {}
    worst = 1.0
    for s in syms:
        p = X.KL1H / f"{s}.parquet"
        if not p.exists() or s not in agg["close_1m"].columns:
            per[s] = {"agree": None}
            continue
        c1h = pd.read_parquet(p)["close"].reindex(idx)
        c1m = agg["close_1m"][s]
        both = c1h.notna() & c1m.notna()
        if both.sum() == 0:
            per[s] = {"agree": None, "n_both": 0}
            continue
        rel = ((c1m - c1h).abs() / c1h)[both]
        agree = float((rel <= 1e-6).mean())
        ticks = agg["tick"][s].dropna()
        tick_months = ticks.groupby(ticks.index.tz_convert("UTC").tz_localize(None).to_period("M")).first()
        ratio = (tick_months / tick_months.shift()).dropna()
        tick_flags = [str(m) for m, r in ratio.items() if r > 10 or r < 0.1]
        per[s] = {"agree": agree, "n_both": int(both.sum()), "n_mismatch": int((rel > 1e-6).sum()),
                  "n_1h_only": int((c1h.notna() & c1m.isna()).sum()),
                  "n_1m_only": int((c1m.notna() & c1h.isna()).sum()),
                  "tick_flags": tick_flags, "tick_first": float(ticks.iloc[0]), "tick_last": float(ticks.iloc[-1])}
        worst = min(worst, agree)
    # ordered bars minute coverage (R2 + R1)
    ob = _r2_orders_bars()
    for s in ("BTCUSDT", "ETHUSDT"):
        r1 = X.r1_parent(s)
        W = r1["W"]
        d = W.diff().fillna(W.iloc[0])
        ob = pd.concat([ob, pd.DataFrame({"ts_bar": W.index[d[s].to_numpy() != 0], "symbol": s})])
    nmin = agg["n_min"]
    c1h_all = {s: pd.read_parquet(X.KL1H / f"{s}.parquet")["close"] for s in ob["symbol"].unique()}
    cov, has_close = [], []
    for t, s in zip(ob["ts_bar"], ob["symbol"]):
        cov.append(float(nmin.at[t, s]) if (t in nmin.index and s in nmin.columns) else np.nan)
        has_close.append(bool(np.isfinite(c1h_all[s].get(t, np.nan))))
    cov, has_close = np.array(cov), np.array(has_close)
    # amendment A1 (2026-09-03): the >=55-minute requirement applies to ordered bars where
    # the 1h store carries a close; bars absent from BOTH stores (exchange halt/delisting)
    # are fill-model item 8 (no fill, zero return, cost charged) and are listed, not gated.
    n_bad = int(np.sum(has_close & ~(cov >= P3_MIN_MINUTES)))
    both_absent = [(str(t), s) for t, s, h in zip(ob["ts_bar"], ob["symbol"], has_close) if not h]
    # exchangeInfo cross-check (online, best effort)
    xinfo = {}
    try:
        import requests
        d = requests.get("https://fapi.binance.com/fapi/v1/exchangeInfo", timeout=30).json()
        for si in d["symbols"]:
            if si["symbol"] in syms:
                f = {x["filterType"]: x for x in si["filters"]}
                xinfo[si["symbol"]] = float(f["PRICE_FILTER"]["tickSize"])
    except Exception as exc:
        xinfo = {"error": str(exc)}
    tick_vs_xinfo = {s: {"inferred_last": per[s].get("tick_last"), "exchangeInfo": xinfo.get(s),
                         "match": (abs(per[s]["tick_last"] - xinfo[s]) < 1e-12) if (s in xinfo and per[s].get("tick_last")) else None}
                     for s in syms if isinstance(xinfo, dict) and s in xinfo and per[s].get("agree") is not None}
    n_flag = sum(len(v.get("tick_flags", [])) for v in per.values())
    # amendment A2: tick consistency across months is REPORTED (genuine Binance tick changes fire it)
    passed = bool(worst >= P3_MIN_AGREE and n_bad == 0)
    out = {"pass": passed, "min_agree": worst, "required_agree": P3_MIN_AGREE,
           "amendments": ["A1 coverage gated only where the 1h store has a close", "A2 modal tick; consistency reported"],
           "ordered_bars": {"n": int(len(ob)), "n_with_1h_close": int(has_close.sum()), "n_below_55_min_gated": n_bad,
                            "min_minutes_gated": float(np.nanmin(cov[has_close])) if has_close.any() else None,
                            "absent_from_both_stores": both_absent},
           "tick_flags_total": n_flag, "tick_vs_exchangeInfo_mismatch": [s for s, v in tick_vs_xinfo.items() if v["match"] is False],
           "per_symbol": per, "tick_vs_exchangeInfo": tick_vs_xinfo}
    _dump("p3_integrity.json", out)
    print(f"P3 pass={passed} min_agree={worst:.5f} ordered_bars_below_55min={n_bad} tick_flags={n_flag}")


# ── P2 parity ────────────────────────────────────────────────────────────────

def main_p2() -> None:
    r2 = X.r2_parent()
    W, C = r2["W"], r2["close"]
    nan = pd.DataFrame(np.nan, index=W.index, columns=W.columns)
    tick = pd.DataFrame(1e-8, index=W.index, columns=W.columns)
    out = passive_overlay(W, C, nan, nan, tick, {c: 0.0 for c in W.columns}, policy="taker",
                          parent_cost_bp=X.R2["cost_bps"], rf_annual=X.R2["rf_annual"])
    got = out["daily_net"].reindex(r2["parent_daily_net"].index)
    series_diff = float((got - r2["parent_daily_net"]).abs().max())
    sr_got = X.sharpe(got)
    r2_ok = series_diff <= PIN_TOL_SERIES and abs(sr_got - r2["pin_sr"]) <= PIN_TOL_SR \
        and abs(r2["parent_sr"] - r2["pin_sr"]) <= PIN_TOL_SR
    # R1-BTC: parent log-series hourly SR pin from copied pp_dev_results (harness check)
    pp = json.loads((X.INPUTS / "pp_dev_results.json").read_text())
    pin_s3 = pp["S3"]["s3_t0.5_h24"]["sr_net"]
    r1 = X.r1_parent("BTCUSDT")
    pos = r1["W"]["BTCUSDT"].to_numpy()
    par = X.s3_parent_hourly(pos, r1["logret_parent"].to_numpy(), cost_bp=X.R1["cost_bps"])
    # overlay in taker mode with log booking on a synthetic close = exp(cumsum logret)
    syn = pd.DataFrame({"BTCUSDT": np.exp(np.concatenate([[0.0], np.cumsum(r1["logret_parent"].to_numpy()[1:])]))},
                       index=r1["W"].index)
    # bar i return = log(syn_i/syn_{i-1}) = logret_i for i>=1; parent multiplies pos_i * ret_i
    ov = passive_overlay(r1["W"], syn, nan.reindex(columns=["BTCUSDT"]).reindex(r1["W"].index),
                         nan.reindex(columns=["BTCUSDT"]).reindex(r1["W"].index),
                         tick.reindex(columns=["BTCUSDT"]).reindex(r1["W"].index), {"BTCUSDT": 0.0},
                         policy="taker", parent_cost_bp=X.R1["cost_bps"], log_booking=True)
    ov_net = ov["hourly_net"].to_numpy()
    par_net = par["net"].copy()
    # first bar: parent books pos_0 * ret_0 (ret_0 is the first stored return); overlay has no prior close -> 0
    first_bar_diff = float(abs(par_net[0] - ov_net[0]))
    hourly_diff = float(np.abs(par_net[1:] - ov_net[1:]).max())
    y_vs_ret = float((r1["y_true"] - r1["logret_parent"]).abs().max())
    r1_ok = abs(par["sr_hourly"] - pin_s3) <= PIN_TOL_SR and hourly_diff <= PIN_TOL_SERIES
    out_j = {"pass": bool(r2_ok and r1_ok),
             "R2": {"pin_sr": r2["pin_sr"], "parent_engine_sr": r2["parent_sr"], "overlay_taker_sr": sr_got,
                    "max_abs_series_diff": series_diff, "n_days": int(len(got)), "ok": bool(r2_ok)},
             "R1_BTC": {"pin_sr_hourly_log": pin_s3, "restated_sr_hourly_log": par["sr_hourly"],
                        "overlay_taker_log_hourly_max_diff_from_bar1": hourly_diff, "first_bar_diff": first_bar_diff,
                        "y_true_minus_rv_ret_maxabs": y_vs_ret, "n_hours": int(len(pos)), "ok": bool(r1_ok)}}
    _dump("p2_parity.json", out_j)
    print(f"P2 pass={out_j['pass']} R2 sr {sr_got:.6f} vs pin {r2['pin_sr']:.6f} (series diff {series_diff:.2e}); "
          f"R1 hourly {par['sr_hourly']:.6f} vs pin {pin_s3:.6f}, overlay diff {hourly_diff:.2e}")


# ── P0 calibration ───────────────────────────────────────────────────────────

def _orders_on_days(sample_days: set[tuple[str, str]]) -> pd.DataFrame:
    """Parent-path orders (R2 + R1 BTC/ETH) whose execution bar falls on a sampled (symbol, day)."""
    rows = []
    r2 = X.r2_parent()
    W = r2["W"]
    dW = W.diff().fillna(W.iloc[0])
    for i, j in zip(*np.nonzero(dW.to_numpy() != 0)):
        s, t = W.columns[j], W.index[i]
        if (s, str(t.date())) in sample_days:
            rows.append({"symbol": s, "ts_bar": t, "dw": float(dW.iloc[i, j]), "close_b": float(r2["close"].iloc[i - 1, j]) if i > 0 else np.nan, "signal": "R2"})
    for s in ("BTCUSDT", "ETHUSDT"):
        r1 = X.r1_parent(s)
        W1 = r1["W"]
        d = W1.diff().fillna(W1.iloc[0])
        for i in np.nonzero(d[s].to_numpy() != 0)[0]:
            t = W1.index[i]
            if (s, str(t.date())) in sample_days:
                rows.append({"symbol": s, "ts_bar": t, "dw": float(d[s].iloc[i]),
                             "close_b": float(r1["close"][s].iloc[i - 1]) if i > 0 else np.nan, "signal": "R1"})
    return pd.DataFrame(rows)


def main_p0() -> None:
    sample = json.loads((X.OUT / "p0_sample.json").read_text())
    days = [tuple(d) for d in sample["days"]]
    # 1) spread model from the sample (frozen procedure)
    per_day, per_sym = {}, {}
    for s, d in days:
        p = X.AGGTR / f"{s}-{d}.parquet"
        if not p.exists():
            per_day[f"{s}-{d}"] = None
            continue
        tr = pd.read_parquet(p)
        v = estimate_spread_rel(tr)
        per_day[f"{s}-{d}"] = v
        per_sym.setdefault(s, []).append(v)
    sym_rel = {s: float(np.median(v)) for s, v in per_sym.items() if len(v)}
    alt_days = [v for k, v in per_day.items() if v is not None and not (k.startswith("BTCUSDT") or k.startswith("ETHUSDT"))]
    pooled = float(np.median(alt_days)) if alt_days else float("nan")
    if X.SPREAD_FILE.exists():
        print(f"spread model already frozen at {X.SPREAD_FILE} -- not rewritten")
        spread = X.spread_model()
    else:
        spread = {"frozen_utc": pd.Timestamp.utcnow().isoformat(), "seed": SEED, "per_symbol_s_rel": sym_rel,
                  "pooled_alt_s_rel": pooled, "per_day": per_day,
                  "rule": "s_rel(sym) if sampled else pooled_alt_s_rel; spread = max(tick, s_rel*close)"}
        X.SPREAD_FILE.write_text(json.dumps(spread, indent=1))
        print(f"spread model frozen -> {X.SPREAD_FILE}")
    srel_of = lambda s: spread["per_symbol_s_rel"].get(s, spread["pooled_alt_s_rel"])  # noqa: E731

    # 2) orders on sampled days
    orders = _orders_on_days(set(days))
    agg_syms = sorted(orders["symbol"].unique())
    idx = pd.date_range(X.DEV_LO - pd.Timedelta(hours=1), X.DEV_HI, freq="h")
    agg = X.load_agg_panel(agg_syms, idx)

    def evaluate(through: int) -> dict:
        recs = []
        for _, o in orders.iterrows():
            s, t = o["symbol"], o["ts_bar"]
            side = "buy" if o["dw"] > 0 else "sell"
            tick = float(agg["tick"].at[t, s]) if t in agg["tick"].index else np.nan
            if not np.isfinite(tick) or not np.isfinite(o["close_b"]):
                continue
            L = limit_price(o["close_b"], srel_of(s), tick, side)
            ml, mh = agg["minlow_ex0"].at[t, s], agg["maxhigh_ex0"].at[t, s]
            f1m = bool(ml <= L - through * tick + 1e-6 * tick) if side == "buy" else bool(mh >= L + through * tick - 1e-6 * tick)
            p = X.AGGTR / f"{s}-{str(t.date())}.parquet"
            if not p.exists():
                continue
            tr = pd.read_parquet(p)
            tk = tick_level_fill(tr, t, side, tick, latency_s=60, through_ticks=through)
            tk0 = tick_level_fill(tr, t, side, tick, latency_s=0, through_ticks=through)
            recs.append({"symbol": s, "ts_bar": t, "side": side, "signal": o["signal"], "tick": tick, "close_b": o["close_b"],
                         "L_1m": L, "quote_tick": tk["quote"], "fill_1m": f1m, "fill_tick": bool(tk["filled"]),
                         "fill_tick_lat0": bool(tk0["filled"]),
                         "quote_err_rel": abs(L - tk["quote"]) / o["close_b"] if np.isfinite(tk["quote"]) else np.nan})
        df = pd.DataFrame(recs)
        if df.empty:
            return {"n": 0}
        r = {"n": int(len(df)), "through_ticks": through,
             "fill_rate_1m": float(df["fill_1m"].mean()), "fill_rate_tick": float(df["fill_tick"].mean()),
             "fill_rate_tick_latency0": float(df["fill_tick_lat0"].mean()),
             "mean_quote_err_rel": float(df["quote_err_rel"].mean()),
             "by_side": {sd: {"n": int(g.shape[0]), "fill_1m": float(g["fill_1m"].mean()), "fill_tick": float(g["fill_tick"].mean())}
                         for sd, g in df.groupby("side")},
             "by_signal": {sg: {"n": int(g.shape[0]), "fill_1m": float(g["fill_1m"].mean()), "fill_tick": float(g["fill_tick"].mean())}
                           for sg, g in df.groupby("signal")},
             "agreement": float((df["fill_1m"] == df["fill_tick"]).mean()),
             "n_1m_fill_tick_nofill": int((df["fill_1m"] & ~df["fill_tick"]).sum()),
             "n_tick_fill_1m_nofill": int((~df["fill_1m"] & df["fill_tick"]).sum())}
        r["conservative"] = bool(r["fill_rate_1m"] <= r["fill_rate_tick"] + P0_TOL_PP)
        r["records"] = df.assign(ts_bar=df["ts_bar"].astype(str)).to_dict(orient="records")
        return r

    e1 = evaluate(1)
    out = {"n_sample_days": len(days), "n_days_on_disk": sum(v is not None for v in per_day.values()),
           "n_orders": int(len(orders)), "spread_model_summary": {"n_symbols": len(sym_rel), "pooled_alt_s_rel": pooled,
                                                                    "btc": sym_rel.get("BTCUSDT"), "eth": sym_rel.get("ETHUSDT"),
                                                                    "alt_median": float(np.median(list(v for k, v in sym_rel.items() if k not in ("BTCUSDT", "ETHUSDT")))) if len(sym_rel) > 2 else None},
           "through_1": e1}
    if e1.get("n", 0) and not e1["conservative"]:
        e2 = evaluate(2)
        out["through_2"] = e2
        out["through_ticks_selected"] = 2 if e2["conservative"] else None
        out["pass"] = bool(e2["conservative"])
    else:
        out["through_ticks_selected"] = 1 if e1.get("n", 0) else None
        out["pass"] = bool(e1.get("conservative", False))
    _dump("p0_calibration.json", out)
    print(f"P0 pass={out['pass']} n_orders={e1.get('n')} fill_1m={e1.get('fill_rate_1m')} fill_tick={e1.get('fill_rate_tick')} "
          f"selected_through={out['through_ticks_selected']}")


# ── P1 unconditional adverse selection ───────────────────────────────────────

def main_p1() -> None:
    spread = X.spread_model()
    cal = json.loads((X.OUT / "p0_calibration.json").read_text())
    through = cal["through_ticks_selected"] or 1
    srel_of = lambda s: spread["per_symbol_s_rel"].get(s, spread["pooled_alt_s_rel"])  # noqa: E731
    syms = [s for s in X.symbols() if (X.AGG_DIR / f"{s}.parquet").exists()]
    rng = np.random.default_rng(SEED + 1)
    recs = []
    per_sym_quota = int(np.ceil(P1_N / len(syms)))
    for s in syms:
        df = X.load_1m(s, X.DEV_LO, X.DEV_HI)
        if df is None or df.empty:
            continue
        agg = pd.read_parquet(X.AGG_DIR / f"{s}.parquet")
        hours = agg.index[(agg.index >= X.DEV_LO) & (agg.index <= X.DEV_HI) & (agg["n_min"] >= 60)]
        hours = hours[1:]  # need the previous bar close
        if len(hours) == 0:
            continue
        pick = rng.choice(len(hours), size=min(per_sym_quota, len(hours)), replace=False)
        c1h = df["close"].resample("1h").last()
        for i in pick:
            t = hours[i]
            cb = c1h.get(t - pd.Timedelta(hours=1), np.nan)
            tick = float(agg.at[t, "tick"])
            if not np.isfinite(cb) or not np.isfinite(tick):
                continue
            side = "buy" if rng.integers(2) == 0 else "sell"
            L = limit_price(cb, srel_of(s), tick, side)
            thr = L - through * tick + 1e-6 * tick if side == "buy" else L + through * tick - 1e-6 * tick
            m = first_cross_minute(df, t, side, thr)
            rec = {"symbol": s, "ts_bar": str(t), "side": side, "L": L, "filled": m is not None}
            if m is not None:
                t5 = t + pd.Timedelta(minutes=m + 5)
                c5 = df["close"].get(t5, np.nan)
                cn = c1h.get(t, np.nan)
                sgn = 1.0 if side == "buy" else -1.0
                rec["drift_5m"] = sgn * (c5 / L - 1) if np.isfinite(c5) else np.nan
                rec["drift_bar_end"] = sgn * (cn / L - 1) if np.isfinite(cn) else np.nan
                rec["fill_minute"] = m
            recs.append(rec)
    df = pd.DataFrame(recs)
    f = df[df["filled"]]
    d5 = f["drift_5m"].dropna()
    t5 = float(d5.mean() / d5.std(ddof=1) * np.sqrt(len(d5))) if len(d5) > 1 else float("nan")
    out = {"n_placements": int(len(df)), "n_filled": int(len(f)), "fill_rate_unconditional": float(df["filled"].mean()),
           "drift_5m_mean": float(d5.mean()), "drift_5m_t": t5, "drift_5m_median": float(d5.median()),
           "drift_bar_end_mean": float(f["drift_bar_end"].mean()),
           "by_side": {sd: {"n": int(g["filled"].sum()), "drift_5m_mean": float(g.loc[g["filled"], "drift_5m"].mean())}
                       for sd, g in df.groupby("side")},
           "through_ticks": through, "pass": bool(d5.mean() <= 0.0)}
    _dump("p1_adverse_selection.json", out)
    print(f"P1 pass={out['pass']} n={len(df)} filled={len(f)} drift5m={out['drift_5m_mean']*1e4:+.2f} bp t={t5:+.2f} "
          f"bar-end {out['drift_bar_end_mean']*1e4:+.2f} bp")


# ── R0 arithmetic pre-check ──────────────────────────────────────────────────

def main_r0() -> None:
    llg = json.loads(LLG.read_text())
    slope = llg["P0"]["hourly_BTC"]["slope"]
    c = pd.read_parquet(X.KL1H / "BTCUSDT.parquet")["close"]
    c = c.loc[(c.index >= X.DEV_LO) & (c.index <= X.DEV_HI)]
    r = np.log(c).diff().dropna().abs()
    out = {"llg_sha256": hashlib.sha256(LLG.read_bytes()).hexdigest(), "slope": slope, "n_hours": int(len(r)),
           "maker_round_trip_bp": 2 * X.FEES["maker_bp"], "bar_bp": 2 * 2 * X.FEES["maker_bp"], "cells": {}}
    for q in (0.90, 0.95, 0.99):
        thr = float(r.quantile(q))
        m = float(r[r >= thr].mean())
        out["cells"][f"q{int(q*100)}"] = {"threshold_abs_r": thr, "mean_abs_r_above": m,
                                          "expected_gross_bp": abs(slope) * m * 1e4,
                                          "n_triggers": int((r >= thr).sum()),
                                          "clears_bar": bool(abs(slope) * m * 1e4 >= out["bar_bp"])}
    out["registered_cell"] = "q90"
    out["run_R0"] = out["cells"]["q90"]["clears_bar"]
    _dump("r0_arithmetic.json", out)
    print(f"R0 q90 expected gross {out['cells']['q90']['expected_gross_bp']:.2f} bp vs bar {out['bar_bp']:.1f} bp -> run={out['run_R0']}")


def main_verdict() -> None:
    files = {"p3": "p3_integrity.json", "p2": "p2_parity.json", "p0": "p0_calibration.json", "p1": "p1_adverse_selection.json"}
    res = {}
    for k, f in files.items():
        p = X.OUT / f
        res[k] = json.loads(p.read_text())["pass"] if p.exists() else None
    r0 = X.OUT / "r0_arithmetic.json"
    res["r0_run"] = json.loads(r0.read_text())["run_R0"] if r0.exists() else None
    stop = any(v is not True for k, v in res.items() if k != "r0_run")
    _dump("probes.json", {"generated_utc": pd.Timestamp.utcnow().isoformat(), "results": res, "stop": stop})
    print(json.dumps(res), "STOP" if stop else "ALL PROBES PASS")
    if stop:
        sys.exit(1)


if __name__ == "__main__":
    {"sample": main_sample, "agg": main_agg, "p3": main_p3, "p2": main_p2, "p0": main_p0,
     "p1": main_p1, "r0": main_r0, "verdict": main_verdict}[sys.argv[1]]()
