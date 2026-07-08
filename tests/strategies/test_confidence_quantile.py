"""Hand-computed tests for confidence_mode="quantile" in generate_term_structure_signals.

Confidence formula (longest-horizon predictive interval, e.g. h14 when
horizons=[7, 14]):
    confidence = clip(|q50 - ref| / max(q90 - q10, eps), 0, 1)
where q50 == pred_h{longest_horizon} (the point estimate emitted alongside
q10/q90 by lgb_model.walk_forward_pooled(quantiles=...)). Direction/signal
logic is unchanged from confidence_mode="ref" — only the confidence
magnitude formula differs.
"""
import math

import pandas as pd
import pytest


def _row(ref, pred_h7, pred_h14, q10_h14, q90_h14):
    return {
        "ref_price": ref,
        "pred_h7": pred_h7,
        "pred_h14": pred_h14,
        "q10_h14": q10_h14,
        "q90_h14": q90_h14,
    }


def test_quantile_confidence_wide_straddle_near_zero():
    """Small deviation from ref relative to a very wide interval -> conf ~0."""
    from tradingagents.strategies.v2_sizing import generate_term_structure_signals

    df = pd.DataFrame([_row(ref=100, pred_h7=102, pred_h14=101, q10_h14=50, q90_h14=150)])
    signals, conf = generate_term_structure_signals(
        df, horizons=[7, 14], confidence_ref=0.05, confidence_mode="quantile",
    )
    assert signals[0] == 1.0
    expected = abs(101 - 100) / (150 - 50)  # 0.01
    assert math.isclose(conf[0], expected, rel_tol=1e-9)
    assert conf[0] < 0.05


def test_quantile_confidence_tight_interval_saturates_to_one():
    """Large deviation from ref relative to a very tight interval -> conf ~1 (clipped)."""
    from tradingagents.strategies.v2_sizing import generate_term_structure_signals

    df = pd.DataFrame([_row(ref=100, pred_h7=105, pred_h14=110, q10_h14=108, q90_h14=109)])
    signals, conf = generate_term_structure_signals(
        df, horizons=[7, 14], confidence_ref=0.05, confidence_mode="quantile",
    )
    assert signals[0] == 1.0
    assert conf[0] == 1.0  # |110-100|/(109-108) = 10, clipped to 1.0


def test_quantile_confidence_degenerate_interval_is_zero():
    """q90 <= q10 (degenerate interval) -> confidence forced to 0 regardless of magnitude."""
    from tradingagents.strategies.v2_sizing import generate_term_structure_signals

    df = pd.DataFrame([_row(ref=100, pred_h7=102, pred_h14=105, q10_h14=110, q90_h14=100)])
    signals, conf = generate_term_structure_signals(
        df, horizons=[7, 14], confidence_ref=0.05, confidence_mode="quantile",
    )
    assert signals[0] == 1.0
    assert conf[0] == 0.0


def test_quantile_confidence_asymmetric_fallback_is_halved():
    """Horizons disagree (h7 DOWN, h14 UP): asymmetric fallback halves the base confidence,
    same discount structure as confidence_mode="ref"."""
    from tradingagents.strategies.v2_sizing import generate_term_structure_signals

    df = pd.DataFrame([_row(ref=100, pred_h7=95, pred_h14=110, q10_h14=108, q90_h14=109)])
    signals, conf = generate_term_structure_signals(
        df, horizons=[7, 14], confidence_ref=0.05, confidence_mode="quantile", asymmetric=True,
    )
    assert signals[0] == 1.0
    assert math.isclose(conf[0], 0.5, rel_tol=1e-9)  # min(1, 10/1)=1.0, halved by fallback


def test_quantile_mode_missing_columns_raises_clear_error():
    """CSVs generated without --quantiles lack q10_h14/q90_h14 -> clear error, not a silent
    KeyError, when a caller opts into confidence_mode="quantile"."""
    from tradingagents.strategies.v2_sizing import generate_term_structure_signals

    df = pd.DataFrame({
        "ref_price": [100],
        "pred_h7": [101],
        "pred_h14": [102],
    })
    with pytest.raises(ValueError, match="q10_h14"):
        generate_term_structure_signals(
            df, horizons=[7, 14], confidence_ref=0.05, confidence_mode="quantile",
        )


def test_ref_mode_still_works_without_quantile_columns():
    """Backward compat: confidence_mode="ref" (the default) never touches q-columns, so
    CSVs generated before this feature keep working unchanged."""
    from tradingagents.strategies.v2_sizing import generate_term_structure_signals

    df = pd.DataFrame({
        "ref_price": [100, 100, 100],
        "pred_h7":   [105, 95, 102],
        "pred_h14":  [110, 90, 99],
    })
    signals, conf = generate_term_structure_signals(
        df, horizons=[7, 14], confidence_ref=0.02, asymmetric=False,
    )
    assert signals.tolist() == [1.0, -1.0, 0.0]
    assert conf[0] == 1.0
    assert conf[1] == 1.0
    assert conf[2] == 0.0


def test_invalid_confidence_mode_raises():
    from tradingagents.strategies.v2_sizing import generate_term_structure_signals

    df = pd.DataFrame({"ref_price": [100], "pred_h7": [101], "pred_h14": [102]})
    with pytest.raises(ValueError, match="confidence_mode"):
        generate_term_structure_signals(
            df, horizons=[7, 14], confidence_ref=0.02, confidence_mode="bogus",
        )
