"""llm_p5_hybrid harness tests — slot alignment + fallback + composition.

Spec: docs/superpowers/specs/2026-07-28-llm-p5-hybrid-prereg.md.
"""
import numpy as np
import pandas as pd
import pytest

from scripts.llm_p5_ab import modulation_factors


def _merged(dates):
    return pd.DataFrame({"date": pd.to_datetime(dates)})


def _csv(tmp_path, rows):
    df = pd.DataFrame(rows)
    p = tmp_path / "sig.csv"
    df.to_csv(p, index=False)
    return p


def test_factor_uses_previous_day_csv_row(tmp_path):
    """Position slot D takes the factor from the CSV row dated D-1."""
    csv = _csv(tmp_path, [
        {"date": "2026-02-01", "llm_multiplier": 0.5, "effective_weight": 1.0},
        {"date": "2026-02-02", "llm_multiplier": 1.5, "effective_weight": 1.0},
    ])
    merged = _merged(["2026-02-01", "2026-02-02", "2026-02-03"])
    f, diag = modulation_factors(merged, csv)
    assert f[0] == 1.0                      # slot 02-01 <- row 01-31 missing -> fallback
    assert f[1] == pytest.approx(0.5)       # slot 02-02 <- row 02-01
    assert f[2] == pytest.approx(1.5)       # slot 02-03 <- row 02-02
    assert diag["n_slot_factor_missing"] == 1


def test_extraction_failure_falls_back_to_neutral(tmp_path):
    csv = _csv(tmp_path, [
        {"date": "2026-02-01", "llm_multiplier": np.nan, "effective_weight": 0.8},
    ])
    merged = _merged(["2026-02-02"])
    f, diag = modulation_factors(merged, csv)
    assert f[0] == 1.0                      # mult NaN -> factor exactly neutral
    assert diag["n_extract_fail"] == 1


def test_composition_formula(tmp_path):
    csv = _csv(tmp_path, [
        {"date": "2026-02-01", "llm_multiplier": 0.0, "effective_weight": 0.4},
    ])
    merged = _merged(["2026-02-02"])
    f, _ = modulation_factors(merged, csv)
    # 1 + 0.4 * (0.0 - 1.0) = 0.6
    assert f[0] == pytest.approx(0.6)


def test_duplicate_csv_dates_keep_last(tmp_path):
    csv = _csv(tmp_path, [
        {"date": "2026-02-01", "llm_multiplier": 0.2, "effective_weight": 1.0},
        {"date": "2026-02-01", "llm_multiplier": 1.2, "effective_weight": 1.0},
    ])
    merged = _merged(["2026-02-02"])
    f, _ = modulation_factors(merged, csv)
    assert f[0] == pytest.approx(1.2)
