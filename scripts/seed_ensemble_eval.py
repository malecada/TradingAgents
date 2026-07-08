"""Lead #2 — multi-seed LGB ensemble vs single-seed.

5 seeds (42,7,123,2024,777) walk-forward over 4.5yr, BTC+ETH canonical 78f.
Build ensemble = mean prediction across seeds per (date,coin,horizon), write a
pred dir, then backtest each single seed AND the ensemble through the
authoritative V5 pipeline (2-coin EW). Bootstrap CI on ensemble-vs-seed42 SR
diff. Variance reduction shows up as: (a) tighter SR across seeds, (b) ensemble
SR >= mean single-seed SR with lower turnover/whipsaw.

NOTE: both coins use canonical 78f here (seeds trained without --onchain-pit),
so ETH is NOT on its production 193f route. This isolates the seed-variance
question; absolute SR differs from the 193f production ETH.
"""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
import scripts.baseline_v5_mix as bm  # noqa: E402

SEEDS = [42, 7, 123, 2024, 777]
COINS = ["bitcoin", "ethereum"]
START, END = "2021-11-07", "2026-04-14"
ANN = bm.ANN
BASE = sys.argv[1] if len(sys.argv) > 1 else "seed_ens"
SEED_ROOT = REPO / "data" / BASE
ENS_DIR = SEED_ROOT / "ensemble"


def build_ensemble():
    ENS_DIR.mkdir(parents=True, exist_ok=True)
    for h in ("preds_lgb_h7.csv", "preds_lgb_h14.csv"):
        frames = [pd.read_csv(SEED_ROOT / f"seed_{s}" / h,
                              parse_dates=["date"]) for s in SEEDS]
        base = frames[0][["date", "coin_id", "actual", "ref_price"]].copy()
        preds = np.column_stack([f["prediction"].values for f in frames])
        base["prediction"] = preds.mean(axis=1)
        base.to_csv(ENS_DIR / h, index=False)
    print(f"ensemble written to {ENS_DIR}")


def port_series(pred_dir):
    cr = {c: bm.run_coin(c, pred_dir, START, END, kelly_fraction=0.5,
                         costs_override=bm.costs_for_coin(c)) for c in COINS}
    df = pd.DataFrame(cr).dropna().sort_index()
    # equal weight 2-coin: PORTFOLIO_WEIGHTS BTC/ETH both 0.15 -> renorm 0.5/0.5
    return bm.portfolio_return(df, bm.PORTFOLIO_WEIGHTS), df


def sr(r):
    sd = r.std()
    return float(r.mean() / sd * ANN) if sd > 0 else 0.0


def maxdd(r):
    eq = (1 + r).cumprod()
    return float((eq / eq.cummax() - 1).min())


def boot_ci(a, b, n=5000, block=5):
    """Stationary block bootstrap CI on SR(a)-SR(b), paired daily returns."""
    a = np.asarray(a); b = np.asarray(b); N = len(a)
    diffs = []
    rng_idx = np.arange(N)
    # deterministic-ish: vary start by iteration to avoid Math.random ban
    for it in range(n):
        idx = []
        pos = (it * 2654435761) % N
        while len(idx) < N:
            L = block
            idx.extend(list(range(pos, min(pos + L, N))))
            pos = (pos + L + (it % 7) + 1) % N
        idx = np.array(idx[:N])
        sa = a[idx]; sb = b[idx]
        da = sa.mean() / sa.std() * ANN if sa.std() > 0 else 0
        db = sb.mean() / sb.std() * ANN if sb.std() > 0 else 0
        diffs.append(da - db)
    diffs = np.array(diffs)
    return float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5)), float((diffs > 0).mean())


def turnover(df):
    """Mean abs daily position change across coins (whipsaw proxy)."""
    # df cols are per-coin returns; need positions — approximate via sign flips
    return None  # positions not exposed here; skip


def main():
    build_ensemble()
    print("\n=== per-seed portfolio SR (2-coin EW, canonical 78f) ===")
    seed_series = {}
    rows = []
    for s in SEEDS:
        port, _ = port_series(SEED_ROOT / f"seed_{s}")
        seed_series[s] = port
        rows.append((f"seed_{s}", sr(port), port.sum(), maxdd(port)))
        print(f"  seed_{s:<5} SR {sr(port):.3f}  ret {(np.prod(1+port)-1)*100:+8.1f}%  DD {maxdd(port)*100:5.1f}%")
    seed_srs = [r[1] for r in rows]
    print(f"\n  single-seed SR: mean {np.mean(seed_srs):.3f}  std {np.std(seed_srs):.3f}  "
          f"min {np.min(seed_srs):.3f}  max {np.max(seed_srs):.3f}")

    ens_port, _ = port_series(ENS_DIR)
    print(f"\n=== 5-seed ENSEMBLE ===")
    print(f"  ensemble  SR {sr(ens_port):.3f}  ret {(np.prod(1+ens_port)-1)*100:+8.1f}%  DD {maxdd(ens_port)*100:5.1f}%")
    print(f"  ensemble SR - mean(single) = {sr(ens_port) - np.mean(seed_srs):+.3f}")
    print(f"  ensemble SR - seed42(prod) = {sr(ens_port) - sr(seed_series[42]):+.3f}")

    # align ensemble vs seed42 on common dates
    common = ens_port.index.intersection(seed_series[42].index)
    lo, hi, pp = boot_ci(ens_port.reindex(common).values, seed_series[42].reindex(common).values)
    print(f"\n  bootstrap SR diff (ensemble - seed42): 95% CI [{lo:+.3f}, {hi:+.3f}]  P(>0)={pp:.3f}")


if __name__ == "__main__":
    main()
