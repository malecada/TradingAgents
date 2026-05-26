"""Market analyst v2 A/B validation harness (asset-agnostic refactor).

Runs 4 variants over BTC + ETH + BNB + SOL (V5 4-coin universe),
2026-01-16 -> 2026-04-15 (~90 bars), all-gpt-4o-mini, sequential.

Variants:
    A_pure_quant       -- pure V5 quant (no market analyst at all)
    B_legacy_market    -- legacy 150-indicator free-text market analyst
    C_v2_struct_only   -- v2 structured snapshot only (no narrow LLM)
    D_v2_full          -- v2 structured snapshot + narrow LLM (Andrew persona)

Per variant per coin, runs:
  1. generate_hybrid_signals.py  -- drives the analyst chain, writes
     data/market_v2_ab/{variant}/{coin}_{start}_{end}.csv
  2. backtest_hybrid.py          -- consumes those signals, writes
     data/market_v2_ab/{variant}/backtest/

After all variants complete, computes paired bootstrap 10k CI for the
Sharpe ratio of each (variant, coin) vs A_pure_quant (and vs
B_legacy_market) and writes data/market_v2_ab/summary.json.

Acceptance gates for "do no harm":
  * Per coin, ΔSharpe(D_v2_full vs A_pure_quant) ≥ 0.
  * Worst-coin paired-bootstrap 95% CI lower bound ≥ -0.15.
  * At least one coin with ΔSharpe > 0.3 and p_positive ≥ 0.9.
"""
from __future__ import annotations

import argparse
import json
import logging
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


VARIANTS: dict[str, dict] = {
    "A_pure_quant": {
        # No market analyst in chain — pure V5 quant baseline.
        "analysts": ["onchain", "prediction"],
        "market_mode": "legacy",
        "market_skip_llm": False,
    },
    "B_legacy_market": {
        # Current production: legacy 150-indicator free-text market analyst.
        "analysts": ["market", "onchain", "prediction"],
        "market_mode": "legacy",
        "market_skip_llm": False,
    },
    "C_v2_struct_only": {
        # v2 deterministic snapshot, no narrow LLM call inside the analyst.
        "analysts": ["market", "onchain", "prediction"],
        "market_mode": "v2",
        "market_skip_llm": True,
    },
    "D_v2_full": {
        # v2 deterministic snapshot + Andrew narrow LLM.
        "analysts": ["market", "onchain", "prediction"],
        "market_mode": "v2",
        "market_skip_llm": False,
    },
}


def run_variant(
    variant: str,
    coin: str,
    start: str,
    end: str,
    out_root: Path,
    force: bool = False,
) -> Path:
    """Run generate_hybrid_signals then backtest_hybrid for one variant+coin.

    Returns the path of the signals CSV.
    """
    cfg = VARIANTS[variant]
    signals_dir = out_root / variant
    signals_dir.mkdir(parents=True, exist_ok=True)
    backtest_dir = signals_dir / "backtest"
    backtest_dir.mkdir(parents=True, exist_ok=True)

    gen_cmd: list[str] = [
        "python", "scripts/generate_hybrid_signals.py",
        "--coins", coin,
        "--start", start,
        "--end", end,
        "--analysts", *cfg["analysts"],
        "--market-mode", cfg["market_mode"],
        "--quant-version", "v5",
        "--quant-pool-preset", "v5_4coin",
        "--output-dir", str(signals_dir),
    ]
    if cfg["market_skip_llm"]:
        gen_cmd.append("--market-skip-llm")
    if force:
        gen_cmd.append("--force")

    logger.info("GENERATE %s / %s: %s", variant, coin, " ".join(gen_cmd))
    subprocess.run(gen_cmd, check=True)

    bt_cmd: list[str] = [
        "python", "scripts/backtest_hybrid.py",
        "--signals-dir", str(signals_dir),
        "--coins", coin,
        "--start", start,
        "--end", end,
        "--quant-version", "v2",
        "--baseline-preset", "v5_4coin",
        "--output-dir", str(backtest_dir),
    ]

    logger.info("BACKTEST %s / %s: %s", variant, coin, " ".join(bt_cmd))
    subprocess.run(bt_cmd, check=True)

    return signals_dir / f"{coin}_{start}_{end}.csv"


def sharpe(returns: np.ndarray, ann: int = 365) -> float:
    if returns.size == 0 or returns.std(ddof=0) == 0:
        return 0.0
    return float(returns.mean() / returns.std(ddof=0) * np.sqrt(ann))


def paired_bootstrap_ci(
    a: np.ndarray,
    b: np.ndarray,
    n_boot: int = 10_000,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    rng = np.random.default_rng(2026)
    diffs: list[float] = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        diffs.append(sharpe(a[idx]) - sharpe(b[idx]))
    arr = np.asarray(diffs)
    return (
        float(arr.mean()),
        float(np.quantile(arr, alpha / 2)),
        float(np.quantile(arr, 1 - alpha / 2)),
    )


def _extract_returns(df: pd.DataFrame) -> np.ndarray:
    if "ret" in df.columns:
        return df["ret"].dropna().values
    if "return" in df.columns:
        return df["return"].dropna().values
    if "equity" in df.columns:
        eq = df["equity"].dropna().values
        if len(eq) > 1:
            return np.diff(eq) / np.where(eq[:-1] != 0, eq[:-1], 1.0)
    return np.array([], dtype=float)


def _load_signals(
    out_root: Path,
    variant: str,
    coin: str,
    start: str,
    end: str,
) -> pd.DataFrame | None:
    primary = out_root / variant / f"{coin}_{start}_{end}.csv"
    if primary.exists():
        return pd.read_csv(primary, parse_dates=["date"])
    bt_dir = out_root / variant / "backtest"
    for stem in [f"{coin}_returns", f"returns_{coin}", coin]:
        p = bt_dir / f"{stem}.csv"
        if p.exists():
            return pd.read_csv(p)
    logger.warning("No signals file found for %s / %s", variant, coin)
    return None


def build_summary(
    out_root: Path,
    coins: list[str],
    start: str,
    end: str,
) -> dict:
    signals: dict[str, dict[str, pd.DataFrame]] = {}
    for v in VARIANTS:
        signals[v] = {}
        for c in coins:
            df = _load_signals(out_root, v, c, start, end)
            if df is not None:
                signals[v][c] = df

    summary: dict = {"runs": {}, "comparisons": {}}

    for v in VARIANTS:
        summary["runs"][v] = {}
        for c, df in signals[v].items():
            rets = _extract_returns(df)
            summary["runs"][v][c] = {
                "sharpe": round(sharpe(rets), 4),
                "n_bars": int(len(rets)),
            }

    for v in ["C_v2_struct_only", "D_v2_full"]:
        summary["comparisons"][v] = {}
        for c in coins:
            if c not in signals.get(v, {}):
                continue
            rets_v = _extract_returns(signals[v][c])
            for baseline in ["A_pure_quant", "B_legacy_market"]:
                if c not in signals.get(baseline, {}):
                    continue
                rets_b = _extract_returns(signals[baseline][c])
                if rets_v.size == 0 or rets_b.size == 0:
                    continue
                mean, lo, hi = paired_bootstrap_ci(rets_v, rets_b)
                n = min(len(rets_v), len(rets_b))
                p_positive = float(np.mean(
                    np.asarray([
                        sharpe(rets_v[np.random.default_rng(2026 + i).integers(0, n, n)])
                        - sharpe(rets_b[np.random.default_rng(2026 + i).integers(0, n, n)])
                        > 0
                        for i in range(10_000)
                    ])
                ))
                summary["comparisons"][v][f"{c}_vs_{baseline}"] = {
                    "delta_sharpe_mean": round(mean, 4),
                    "ci_lo": round(lo, 4),
                    "ci_hi": round(hi, 4),
                    "p_positive": round(p_positive, 4),
                }

    return summary


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "4-variant market analyst v2 A/B validation harness.\n\n"
            "Variants:\n"
            "  A_pure_quant      -- no market analyst (quant only)\n"
            "  B_legacy_market   -- legacy 150-indicator free-text market analyst\n"
            "  C_v2_struct_only  -- v2 structured snapshot only (no narrow LLM)\n"
            "  D_v2_full         -- v2 structured snapshot + narrow LLM (Andrew)\n\n"
            "Per variant, runs generate_hybrid_signals.py then backtest_hybrid.py.\n"
            "After all runs, writes data/market_v2_ab/summary.json with\n"
            "bootstrap-10k paired CI per (coin, variant) vs A_pure_quant and B_legacy_market.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--coins",
        nargs="+",
        default=["bitcoin", "ethereum", "binancecoin", "solana"],
        help="Coin(s) to run (default: V5 4-coin universe)",
    )
    ap.add_argument("--start", default="2026-01-16")
    ap.add_argument("--end", default="2026-04-15")
    ap.add_argument("--out", default="data/market_v2_ab")
    ap.add_argument(
        "--variants",
        nargs="+",
        default=list(VARIANTS.keys()),
        choices=list(VARIANTS.keys()),
    )
    ap.add_argument(
        "--skip-runs",
        action="store_true",
        help="Recompute summary.json from existing CSVs only",
    )
    ap.add_argument("--force", action="store_true")
    ap.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    args = ap.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)s %(message)s",
    )

    out_root = Path(args.out)
    out_root.mkdir(parents=True, exist_ok=True)

    if not args.skip_runs:
        for v in args.variants:
            for c in args.coins:
                logger.info("=" * 60)
                logger.info("VARIANT %s  COIN %s", v, c)
                logger.info("=" * 60)
                try:
                    csv = run_variant(v, c, args.start, args.end, out_root, force=args.force)
                    logger.info("Done -> %s", csv)
                except subprocess.CalledProcessError as exc:
                    logger.error("FAILED variant=%s coin=%s: %s", v, c, exc)
                    raise

    logger.info("Computing summary statistics ...")
    summary = build_summary(out_root, args.coins, args.start, args.end)

    summary_path = out_root / "summary.json"
    with open(summary_path, "w") as fh:
        json.dump(summary, fh, indent=2, default=str)
    logger.info("Summary written to %s", summary_path)
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
