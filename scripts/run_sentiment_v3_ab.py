"""Sentiment v3 A/B validation harness.

Runs 4 variants over BTC + ETH, 2026-01-16 -> 2026-04-15 (90 bars),
all-gpt-4o-mini, sequential. Variants:
    A -- pure V5 quant (no sentiment analyst)
    B -- legacy sentiment analyst (current production)
    C -- v3 structured-only (modulator features only, no narrow LLM)
    D -- v3 full (modulator features + narrow LLM)

Each variant runs TWO scripts per coin:
  1. generate_hybrid_signals.py  -- drives the analyst chain, writes
     data/sentiment_v3_ab/{variant}/{coin}_{start}_{end}.csv
  2. backtest_hybrid.py          -- consumes those signals, writes
     data/sentiment_v3_ab/{variant}/backtest/

After all 4 variants complete, computes paired bootstrap 10k CI for
Sharpe ratio per (coin, variant) vs (coin, A) and (coin, B), and writes
data/sentiment_v3_ab/summary.json.

Variant A note: the --analysts list excludes crypto_sentiment so the
sentiment analyst is fully absent from the chain. The generate step
still runs with legacy mode (default) so no v3 path is triggered.

Variants B/C/D all include crypto_sentiment in --analysts.
C distinguishes from D via --sentiment-skip-llm (structured snapshot
only, no narrow LLM call inside the analyst).

Signal file naming convention (set by generate_hybrid_signals.py):
  {output_dir}/{coin}_{start}_{end}.csv
This is what backtest_hybrid.py reads from --signals-dir.
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

# ---------------------------------------------------------------------------
# Variant definitions
# ---------------------------------------------------------------------------
# analysts: passed to generate_hybrid_signals.py --analysts
# sentiment_mode: passed to generate_hybrid_signals.py --sentiment-mode
# sentiment_skip_llm: if True, add --sentiment-skip-llm to generate step
# ---------------------------------------------------------------------------
VARIANTS: dict[str, dict] = {
    "A_pure_quant": {
        # No crypto_sentiment analyst in chain — pure quant baseline.
        "analysts": ["market", "onchain", "prediction"],
        "sentiment_mode": "legacy",
        "sentiment_skip_llm": False,
    },
    "B_legacy_sentiment": {
        # Current production: legacy free-text sentiment analyst.
        "analysts": ["market", "onchain", "crypto_sentiment", "prediction"],
        "sentiment_mode": "legacy",
        "sentiment_skip_llm": False,
    },
    "C_v3_features_only": {
        # v3 structured snapshot populates sentiment_features for the
        # modulator, but the narrow LLM event analyst is skipped.
        "analysts": ["market", "onchain", "crypto_sentiment", "prediction"],
        "sentiment_mode": "v3",
        "sentiment_skip_llm": True,
    },
    "D_v3_full": {
        # v3 structured snapshot + narrow LLM event analyst.
        "analysts": ["market", "onchain", "crypto_sentiment", "prediction"],
        "sentiment_mode": "v3",
        "sentiment_skip_llm": False,
    },
}


# ---------------------------------------------------------------------------
# Signal generation + backtest per variant
# ---------------------------------------------------------------------------

def run_variant(
    variant: str,
    coin: str,
    start: str,
    end: str,
    out_root: Path,
    force: bool = False,
) -> Path:
    """Run generate_hybrid_signals then backtest_hybrid for one variant+coin.

    Returns the path of the signals CSV written by generate_hybrid_signals.
    """
    cfg = VARIANTS[variant]
    signals_dir = out_root / variant
    signals_dir.mkdir(parents=True, exist_ok=True)
    backtest_dir = signals_dir / "backtest"
    backtest_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: generate signals
    gen_cmd: list[str] = [
        "python", "scripts/generate_hybrid_signals.py",
        "--coins", coin,
        "--start", start,
        "--end", end,
        "--analysts", *cfg["analysts"],
        "--sentiment-mode", cfg["sentiment_mode"],
        "--quant-version", "v5",
        "--quant-pool-preset", "v5_2coin",
        "--output-dir", str(signals_dir),
    ]
    if cfg["sentiment_skip_llm"]:
        gen_cmd.append("--sentiment-skip-llm")
    if force:
        gen_cmd.append("--force")

    logger.info("GENERATE %s / %s: %s", variant, coin, " ".join(gen_cmd))
    subprocess.run(gen_cmd, check=True)

    # Step 2: backtest
    bt_cmd: list[str] = [
        "python", "scripts/backtest_hybrid.py",
        "--signals-dir", str(signals_dir),
        "--coins", coin,
        "--start", start,
        "--end", end,
        "--quant-version", "v2",
        "--baseline-preset", "v5_2coin",
        "--output-dir", str(backtest_dir),
        "--sentiment-mode", cfg["sentiment_mode"],
    ]
    if cfg["sentiment_skip_llm"]:
        bt_cmd.append("--sentiment-skip-llm")

    logger.info("BACKTEST %s / %s: %s", variant, coin, " ".join(bt_cmd))
    subprocess.run(bt_cmd, check=True)

    # Signals CSV written by generate_hybrid_signals: {coin}_{start}_{end}.csv
    return signals_dir / f"{coin}_{start}_{end}.csv"


# ---------------------------------------------------------------------------
# Statistics
# ---------------------------------------------------------------------------

def sharpe(returns: np.ndarray, ann: int = 365) -> float:
    """Annualised Sharpe ratio from a daily return series."""
    if returns.size == 0 or returns.std(ddof=0) == 0:
        return 0.0
    return float(returns.mean() / returns.std(ddof=0) * np.sqrt(ann))


def paired_bootstrap_ci(
    a: np.ndarray,
    b: np.ndarray,
    n_boot: int = 10_000,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    """Bootstrap 10k paired CI for delta Sharpe (a - b).

    Returns (mean_delta, ci_lo, ci_hi).
    """
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
    """Extract a daily return series from a signals/backtest CSV.

    Tries columns in order: ret, return, then equity-diff.
    """
    if "ret" in df.columns:
        return df["ret"].dropna().values
    if "return" in df.columns:
        return df["return"].dropna().values
    if "equity" in df.columns:
        eq = df["equity"].dropna().values
        if len(eq) > 1:
            return np.diff(eq) / np.where(eq[:-1] != 0, eq[:-1], 1.0)
    return np.array([], dtype=float)


# ---------------------------------------------------------------------------
# Summary aggregation
# ---------------------------------------------------------------------------

def _load_signals(
    out_root: Path,
    variant: str,
    coin: str,
    start: str,
    end: str,
) -> pd.DataFrame | None:
    """Load signals CSV. Falls back to backtest returns CSV if needed."""
    # Primary: generate_hybrid_signals output
    primary = out_root / variant / f"{coin}_{start}_{end}.csv"
    if primary.exists():
        return pd.read_csv(primary, parse_dates=["date"])
    # Fallback: backtest output directory (contains daily returns)
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
    """Load all variant CSVs and compute Sharpe + paired bootstrap CIs."""
    # Load
    signals: dict[str, dict[str, pd.DataFrame]] = {}
    for v in VARIANTS:
        signals[v] = {}
        for c in coins:
            df = _load_signals(out_root, v, c, start, end)
            if df is not None:
                signals[v][c] = df

    summary: dict = {"runs": {}, "comparisons": {}}

    # Per-variant per-coin Sharpe
    for v in VARIANTS:
        summary["runs"][v] = {}
        for c, df in signals[v].items():
            rets = _extract_returns(df)
            summary["runs"][v][c] = {
                "sharpe": round(sharpe(rets), 4),
                "n_bars": int(len(rets)),
            }

    # Paired bootstrap CI: C and D vs A and B
    for v in ["C_v3_features_only", "D_v3_full"]:
        summary["comparisons"][v] = {}
        for c in coins:
            if c not in signals.get(v, {}):
                continue
            rets_v = _extract_returns(signals[v][c])
            for baseline in ["A_pure_quant", "B_legacy_sentiment"]:
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "4-variant sentiment v3 A/B validation harness.\n\n"
            "Variants:\n"
            "  A_pure_quant        -- no sentiment analyst (quant only)\n"
            "  B_legacy_sentiment  -- legacy free-text sentiment analyst\n"
            "  C_v3_features_only  -- v3 structured snapshot (no narrow LLM)\n"
            "  D_v3_full           -- v3 full (structured + narrow LLM)\n\n"
            "Per variant, runs generate_hybrid_signals.py then backtest_hybrid.py.\n"
            "After all runs, writes data/sentiment_v3_ab/summary.json with\n"
            "bootstrap-10k paired CI per (coin, variant) vs baselines A and B.\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--coins",
        nargs="+",
        default=["bitcoin", "ethereum"],
        help="Coin(s) to run (default: bitcoin ethereum)",
    )
    ap.add_argument(
        "--start",
        default="2026-01-16",
        help="Backtest start date YYYY-MM-DD (default: 2026-01-16)",
    )
    ap.add_argument(
        "--end",
        default="2026-04-15",
        help="Backtest end date YYYY-MM-DD (default: 2026-04-15)",
    )
    ap.add_argument(
        "--out",
        default="data/sentiment_v3_ab",
        help="Root output directory (default: data/sentiment_v3_ab)",
    )
    ap.add_argument(
        "--variants",
        nargs="+",
        default=list(VARIANTS.keys()),
        choices=list(VARIANTS.keys()),
        help="Subset of variants to run (default: all four)",
    )
    ap.add_argument(
        "--skip-runs",
        action="store_true",
        help=(
            "Skip generate+backtest runs; only recompute summary.json "
            "from existing signal CSVs in --out"
        ),
    )
    ap.add_argument(
        "--force",
        action="store_true",
        help="Pass --force to generate_hybrid_signals.py (overwrite cached signals)",
    )
    ap.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO)",
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
