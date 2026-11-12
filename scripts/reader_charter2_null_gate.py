"""Pass rate of the Charter 2 gates on pure noise (zero cost, synthetic panels only, no market data).

Each draw is a synthetic panel of the registered shape (156 weeks of 50 assets, 104 test weeks) in which the text
features and the forward returns are independent noise. The registered gate score and gate statistics are computed
exactly as in the registered run. One JSON line per draw; ``--summary`` reads such lines and prints the pass rate.
With a third argument the text features are redrawn as AR(1) series per asset with that persistence, still
independent of the returns (real text features are persistent within an asset).

    python scripts/reader_charter2_null_gate.py 0 900 > draws_a.jsonl
    python scripts/reader_charter2_null_gate.py 5000 5900 0.9 > draws_persistent.jsonl
    python scripts/reader_charter2_null_gate.py --summary research/multiagent-v2/charter2_null_gate.jsonl
"""
from __future__ import annotations

import json
import math
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tests" / "research"))

from tradingagents.reader import charter2 as c2, model  # noqa: E402


def persistent(feats, rho: float, seed: int):
    """The text columns redrawn as stationary AR(1) series per asset (unit variance), independent of the returns."""
    rng = np.random.default_rng([seed, 1])
    out = feats.sort_values(["symbol", "date"]).reset_index(drop=True)
    n_syms, n_weeks = out["symbol"].nunique(), out["date"].nunique()
    if len(out) != n_syms * n_weeks:
        raise SystemExit("persistent features need a balanced panel")
    for col in c2.TEXT_COLUMNS:
        eps = rng.normal(size=(n_syms, n_weeks))
        z = eps.copy()
        for week in range(1, n_weeks):
            z[:, week] = rho * z[:, week - 1] + math.sqrt(1 - rho * rho) * eps[:, week]
        out[col] = z.reshape(-1)
    return out


def draw(seed: int, rho: float | None = None) -> dict:
    from test_reader_charter2 import synth          # the synthetic panel of the tests, one definition

    top, feats, _, fwd, _, quant, flags = synth(0.0, seed=seed)
    if rho is not None:
        feats = persistent(feats, rho, seed)
    panel = c2.assemble_panel(top, feats, fwd, quant, flags)
    panel[c2.GATE_SCORE], _ = model.walk_forward(panel, c2.TEXT)
    test = panel[panel[c2.GATE_SCORE].notna()]
    gates, _ = c2.gate_statistics(test)
    verdict = c2.build_verdict({"gates": gates, "weeks": {"test": int(test["date"].nunique())}}, {}, {}, {})
    enc, years = gates["encompassing_text_vs_quant"], gates["text_coefficient_by_year"]
    return {"seed": seed, "t": enc["t_llm"], "beta": enc["beta_llm"], "y2023": years["2023"]["mean"],
            "y2024": years["2024"]["mean"], "verdict": verdict["verdict"]}


def summary(path: Path) -> dict:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    seeds = [row["seed"] for row in rows]
    if len(set(seeds)) != len(seeds):
        raise SystemExit("a seed occurs twice")
    t = np.array([row["t"] for row in rows])
    n, passes = len(rows), sum(row["verdict"] == "PASS" for row in rows)
    rate = passes / n
    half = 1.96 * math.sqrt(rate * (1 - rate) / n)
    return {"draws": n, "pass": passes, "pass_rate": rate, "pass_rate_95": [rate - half, rate + half],
            "first_gate_alone": int(sum(row["t"] >= c2.GATE_TEXT_T and row["beta"] > 0 for row in rows)),
            "t_mean": float(t.mean()), "t_sd": float(t.std(ddof=1)), "t_q95": float(np.quantile(t, 0.95)),
            "t_q975": float(np.quantile(t, 0.975)), "t_q99": float(np.quantile(t, 0.99)),
            "share_abs_t_ge_2": float((np.abs(t) >= 2.0).mean())}


def main(argv: list[str]) -> int:
    if argv and argv[0] == "--summary":
        print(json.dumps(summary(Path(argv[1])), indent=1))
        return 0
    rho = float(argv[2]) if len(argv) > 2 else None
    for seed in range(int(argv[0]), int(argv[1])):
        print(json.dumps(draw(seed, rho)), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
