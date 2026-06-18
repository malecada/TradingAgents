"""Backtest truncated hybrid signal streams vs pure-quant V5 baseline, on the
quota-limited valid window (~144-151 bars, 2025-04-18..2025-09). Reuses the
authoritative run_coin / run_coin_backtest machinery. Bootstrap CI on dSR.

Leads #4 (BNB/SOL hybrid) and #5 (ETH market-drop A/B).
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
import scripts.baseline_v5_mix as bm  # noqa: E402
from scripts.baseline_strategy_v2 import run_coin_backtest  # noqa: E402

ANN = bm.ANN

# variant -> (signal_dir, coin, baseline_pred_dir). Full-year signal dirs.
VARIANTS = {
    "bnb":         ("data/hybrid_signals_v5_bnbsol_1y", "binancecoin", "data/multi_3coins_bnb"),
    "sol":         ("data/hybrid_signals_v5_bnbsol_1y", "solana", "data/multi_3coins_sol_pit_wf"),
    "eth_prod3":   ("data/hybrid_signals_v5_eth_prod3_1y", "ethereum", "data/multi_2coins_pit_wf"),
    "eth_dropmkt": ("data/hybrid_signals_v5_eth_dropmkt_1y", "ethereum", "data/multi_2coins_pit_wf"),
}


def _ohlcv(coin, end):
    oh = bm._load_crypto_ohlcv(coin, end)
    oh["Date"] = pd.to_datetime(oh["Date"]).dt.tz_localize(None).dt.normalize()
    return oh[["Date", "Close"]]


def hybrid_returns(sig_dir, coin):
    f = next((REPO / sig_dir).glob(f"{coin}_*.csv"))
    sig = pd.read_csv(f, parse_dates=["date"]).sort_values("date")
    sig = sig[sig["position"].notna()]
    start = sig["date"].min().strftime("%Y-%m-%d")
    end = sig["date"].max().strftime("%Y-%m-%d")
    oh = _ohlcv(coin, end)
    m = sig.merge(oh, left_on="date", right_on="Date").dropna(subset=["Close"]).reset_index(drop=True)
    eq, _ = run_coin_backtest(dates=m["date"].values, prices=m["Close"].values,
                             positions=m["position"].astype(float).values,
                             initial_capital=10_000.0, **dict(bm.costs_for_coin(coin)))
    eq = np.asarray(eq, float)
    return pd.Series(eq[1:] / eq[:-1] - 1.0, index=pd.to_datetime(m["date"].values[1:])), start, end


def baseline_returns(coin, pred_dir, start, end):
    r = bm.run_coin(coin, REPO / pred_dir, start, end, kelly_fraction=0.5,
                    costs_override=bm.costs_for_coin(coin))
    r.index = pd.to_datetime(r.index)
    return r


def sr(r):
    sd = r.std()
    return float(r.mean() / sd * ANN) if sd > 0 else 0.0


def maxdd(r):
    eq = (1 + r).cumprod()
    return float((eq / eq.cummax() - 1).min())


def boot(a, b, n=5000, block=5):
    a = np.asarray(a); b = np.asarray(b); N = len(a); d = []
    for it in range(n):
        idx = []; pos = (it * 2654435761) % N
        while len(idx) < N:
            idx.extend(range(pos, min(pos + block, N)))
            pos = (pos + block + (it % 7) + 1) % N
        idx = np.array(idx[:N]); sa = a[idx]; sb = b[idx]
        da = sa.mean() / sa.std() * ANN if sa.std() > 0 else 0
        db = sb.mean() / sb.std() * ANN if sb.std() > 0 else 0
        d.append(da - db)
    d = np.array(d)
    return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5)), float((d > 0).mean())


def run(name):
    sig_dir, coin, base_dir = VARIANTS[name]
    h, start, end = hybrid_returns(sig_dir, coin)
    b = baseline_returns(coin, base_dir, start, end)
    common = h.index.intersection(b.index)
    h = h.reindex(common); b = b.reindex(common)
    lo, hi, pp = boot(h.values, b.values)
    print(f"\n[{name}] {coin}  window {start}..{end}  ({len(common)} bars)")
    print(f"  hybrid   SR {sr(h):+.3f}  ret {(np.prod(1+h)-1)*100:+7.1f}%  DD {maxdd(h)*100:5.1f}%")
    print(f"  baseline SR {sr(b):+.3f}  ret {(np.prod(1+b)-1)*100:+7.1f}%  DD {maxdd(b)*100:5.1f}%")
    print(f"  dSR (hybrid-baseline) {sr(h)-sr(b):+.3f}  95%CI [{lo:+.3f},{hi:+.3f}]  P(>0)={pp:.3f}")
    return dict(name=name, coin=coin, bars=len(common), hybrid_sr=sr(h),
                baseline_sr=sr(b), dsr=sr(h)-sr(b), ci=[lo, hi], p_pos=pp)


def main():
    print("=== Lead #4: BNB/SOL hybrid vs pure-quant V5 (quota-limited window) ===")
    for n in ["bnb", "sol"]:
        run(n)
    print("\n=== Lead #5: ETH market-analyst-drop A/B ===")
    rp = run("eth_prod3")
    rd = run("eth_dropmkt")
    print(f"\n  market-DROP effect (dropmkt dSR - prod3 dSR): "
          f"{rd['dsr'] - rp['dsr']:+.3f}  "
          f"(LOO predicted ETH +0.69 from dropping market)")


if __name__ == "__main__":
    main()
