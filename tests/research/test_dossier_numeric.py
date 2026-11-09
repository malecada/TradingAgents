from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from tradingagents.dossier.numeric_card import numeric_block, render_numeric, weekly_path  # noqa: E402


def test_numeric_block_is_relative_and_renders(tmp_path):
    friday = pd.Timestamp("2024-01-05", tz="UTC")
    cards = pd.DataFrame({"date": [friday] * 3, "symbol": ["AUSDT", "BUSDT", "CUSDT"],
                          "ret_4w": [0.1, -0.2, 0.05], "ret_12w": [0.5, 0.1, np.nan], "dist_26w_high": [0, -0.3, -0.1],
                          "vol_ewma20": [0.5, 0.9, 0.7], "volvol_20": [0.1, 0.2, 0.3], "dvol_30d": [3e9, 1e8, 5e8],
                          "mcap_cm": [1e11, np.nan, 1e9], "funding_3d": [0.0001, -0.0002, 0.0], "funding_30d": [0.0001] * 3,
                          "d_adract_30d": [0.05, np.nan, -0.1], "d_txcnt_30d": [0.0, 0.1, 0.2],
                          "unlock_next30_pct": [np.nan, 0.031, 0.0], "unlock_prev30_pct": [np.nan] * 3,
                          "age_weeks": [400, 20, 80], "category": ["Layer 1", None, "Dexs"], "size_rank": [0.95, np.nan, 0.4]})
    idx = pd.date_range("2023-06-01", "2024-01-05", freq="D", tz="UTC")
    k = pd.DataFrame({"open": 1, "high": 1, "low": 1, "close": np.linspace(50, 100, len(idx)), "quote_volume": 1}, index=idx)
    k.index.name = "ts"
    k.to_parquet(tmp_path / "AUSDT.parquet")
    path = weekly_path("AUSDT", friday, klines_dir=tmp_path)
    assert path["indexed_path"][-1] == 100.0 and path["weeks"] == 12 and path["drawdown_90d_pct"] == 0.0
    block = numeric_block(cards, "AUSDT", friday, path)
    assert block["size_bucket"] == "top decile by market cap" and block["volume_rank_pct"] > 0.8 and block["category"] == "network or infrastructure"
    assert block["ret_4w_pct"] == 10.5 and block["funding_3d_ann_pct"] == 3.7        # log 0.1 -> 10.5%; daily 0.0001 x 365 = 3.65
    assert "universe_size" not in block and "Universe:" not in render_numeric(block)
    sub = numeric_block(cards, "AUSDT", friday, path, universe_symbols=["AUSDT", "CUSDT"])
    assert sub["volume_rank_pct"] != block["volume_rank_pct"]                          # percentiles within the given universe
    text = render_numeric(block)
    assert "pct" in text and "2024" not in text and "$" not in text and "AUSDT" not in text
    b = numeric_block(cards, "BUSDT", friday, None)
    assert b["category"] == "unknown" and b["unlock_next30_pct_supply"] == 3.1 and b["listing_age"] == "listed under a year"
