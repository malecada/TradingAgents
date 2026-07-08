# tests/strategies/test_load_preds_quantile_compat.py
"""CSV backward-compat tests for scripts.baseline_v5_mix._load_preds + confidence_mode wiring.

Covers the E3 requirement: prediction CSVs generated *before* quantile support
(no q10/q90 columns) must keep working unchanged in confidence_mode="ref", and
must fail with a clear, actionable error (not a bare KeyError) if a caller
opts into confidence_mode="quantile" without regenerating them.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _write_pred_csv(path: Path, coin: str, with_quantiles: bool) -> None:
    dates = pd.date_range("2024-01-01", periods=5, freq="D")
    data = {
        "date": dates,
        "coin_id": [coin] * 5,
        "prediction": [100.0 + i for i in range(5)],
        "actual": [101.0 + i for i in range(5)],
        "ref_price": [100.0] * 5,
    }
    if with_quantiles:
        data["q10"] = [95.0 + i for i in range(5)]
        data["q90"] = [105.0 + i for i in range(5)]
    pd.DataFrame(data).to_csv(path, index=False)


def test_load_preds_without_quantile_columns_has_no_q_columns(tmp_path):
    from scripts.baseline_v5_mix import _load_preds

    _write_pred_csv(tmp_path / "preds_lgb_h7.csv", "bitcoin", with_quantiles=False)
    _write_pred_csv(tmp_path / "preds_lgb_h14.csv", "bitcoin", with_quantiles=False)

    merged = _load_preds(tmp_path, "bitcoin")
    assert "q10_h14" not in merged.columns
    assert "q90_h14" not in merged.columns


def test_ref_mode_works_without_quantile_columns(tmp_path):
    from scripts.baseline_v5_mix import _load_preds, _v2_positions

    _write_pred_csv(tmp_path / "preds_lgb_h7.csv", "bitcoin", with_quantiles=False)
    _write_pred_csv(tmp_path / "preds_lgb_h14.csv", "bitcoin", with_quantiles=False)

    merged = _load_preds(tmp_path, "bitcoin")
    merged["Close"] = merged["ref_price"]
    pos = _v2_positions(merged, confidence_mode="ref")
    assert len(pos) == len(merged)


def test_quantile_mode_without_quantile_columns_raises_clear_error(tmp_path):
    from scripts.baseline_v5_mix import _load_preds, _v2_positions

    _write_pred_csv(tmp_path / "preds_lgb_h7.csv", "bitcoin", with_quantiles=False)
    _write_pred_csv(tmp_path / "preds_lgb_h14.csv", "bitcoin", with_quantiles=False)

    merged = _load_preds(tmp_path, "bitcoin")
    merged["Close"] = merged["ref_price"]
    with pytest.raises(ValueError, match="q10_h14"):
        _v2_positions(merged, confidence_mode="quantile")


def test_load_preds_with_quantile_columns_renamed_per_horizon(tmp_path):
    from scripts.baseline_v5_mix import _load_preds

    _write_pred_csv(tmp_path / "preds_lgb_h7.csv", "bitcoin", with_quantiles=True)
    _write_pred_csv(tmp_path / "preds_lgb_h14.csv", "bitcoin", with_quantiles=True)

    merged = _load_preds(tmp_path, "bitcoin")
    assert {"q10_h7", "q90_h7", "q10_h14", "q90_h14"}.issubset(merged.columns)


def test_quantile_mode_with_quantile_columns_runs_without_error(tmp_path):
    from scripts.baseline_v5_mix import _load_preds, _v2_positions

    _write_pred_csv(tmp_path / "preds_lgb_h7.csv", "bitcoin", with_quantiles=True)
    _write_pred_csv(tmp_path / "preds_lgb_h14.csv", "bitcoin", with_quantiles=True)

    merged = _load_preds(tmp_path, "bitcoin")
    merged["Close"] = merged["ref_price"]
    pos = _v2_positions(merged, confidence_mode="quantile")
    assert len(pos) == len(merged)
