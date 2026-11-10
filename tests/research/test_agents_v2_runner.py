"""Weekly runner v2.4: uniform judge panel, seeded random debate subset with paired judges, symbol-keyed book
that survives alias collisions, staged resumable cache."""
from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tradingagents.agents_v2.runner import random_debate_candidates, run_week  # noqa: E402
from test_agents_v2 import DOSSIER, StubClient  # noqa: E402


def _dossiers(n=8):
    out = {}
    for i in range(n):
        alias = "Asset_" + "AB"[i % 2]                    # deliberate alias collisions across the week
        out[f"S{i}USDT"] = {"alias": alias, "sha256": f"sha{i}", "text": DOSSIER.replace("Asset_A", alias),
                            "numeric": {"vol_ewma20_ann_pct": 50.0 + i}, "quant_forecast": {"pred_rank_pct": i / n}}
    return out


def test_random_selection_is_seeded_and_week_specific():
    syms = [f"S{i}" for i in range(50)]
    a = random_debate_candidates(syms, pd.Timestamp("2024-03-01", tz="UTC"), 12)
    b = random_debate_candidates(syms, pd.Timestamp("2024-03-01", tz="UTC"), 12)
    c = random_debate_candidates(syms, pd.Timestamp("2024-03-08", tz="UTC"), 12)
    assert a == b and len(a) == 12 and a != c


def test_run_week_uniform_panel_paired_debate_and_symbol_book(tmp_path):
    d = _dossiers()
    client = StubClient(0.7, 0.6, p_nd=0.45, weight=0.2)
    out = run_week(pd.Timestamp("2024-03-01", tz="UTC"), d, client, n_debate=3, runs_dir=tmp_path)
    res = out["results"]
    assert len(res) == 8 and all(r["p_judge_nd"] is not None and r["p_hybrid"] is not None for r in res.values())
    debated = [s for s, r in res.items() if r["debated"]]
    assert len(debated) == 3 and all(abs(res[s]["p_judge_debate"] - 0.65) < 1e-9 for s in debated)
    assert all(res[s]["p_judge_nd"] == 0.45 for s in res)                          # paired contrast available for all
    for s, r in res.items():
        assert r["p_outperform"] == (r["p_hybrid_debate"] if r["debated"] else r["p_hybrid_nd"])
    names = [n for n, _ in client.prompts]
    assert names.count("judge_no_debate") == 8 and names.count("judge_bull_first") == 3 and names.count("bear_reply") == 3
    assert "portfolio" not in names                                                # PM is not part of the main run
    w = out["portfolio"]["rule_weights"]
    assert set(w) == set(d) and abs(sum(w.values())) < 1e-9                        # keyed by symbol despite 2 aliases
    assert len(out["candidates"]) == 8
    # resume: nothing is re-run
    client2 = StubClient(0.7, 0.6, p_nd=0.45)
    out2 = run_week(pd.Timestamp("2024-03-01", tz="UTC"), d, client2, n_debate=3, runs_dir=tmp_path)
    assert client2.prompts == [] and out2["portfolio"]["rule_weights"] == w
