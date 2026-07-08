"""Causal convention must cover the whole validation stack, not just
baseline_v5_mix (audit 2026-07-07 C1: walkforward_v2 / cpcv_v2 /
validate_v5_mix each carried their own same-bar builder + ref_price
overwrite).

PnL prices must stay unshifted — only sizing inputs are lagged.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from tests.strategies.test_causal_convention import _merged


def _bump_last_close(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.loc[out.index[-1], "Close"] *= 0.65
    return out


def test_walkforward_v2_positions_causal():
    from scripts.walkforward_v2 import _v2_positions

    base = _merged()
    pos_a, px_a = _v2_positions(base, convention="causal")
    pos_b, px_b = _v2_positions(_bump_last_close(base), convention="causal")

    assert pos_a[-1] != 0.0
    assert pos_b[-1] == pytest.approx(pos_a[-1])
    # PnL price series must remain the true (unshifted) closes
    assert px_a[-1] == pytest.approx(base["Close"].iloc[-1])
    assert px_b[-1] == pytest.approx(base["Close"].iloc[-1] * 0.65)


def test_cpcv_v2_path_causal():
    from scripts.cpcv_v2 import _build_v2_path

    base = _merged()
    _, px_a, pos_a = _build_v2_path(base, convention="causal")
    _, px_b, pos_b = _build_v2_path(_bump_last_close(base), convention="causal")

    assert pos_a[-1] != 0.0
    assert pos_b[-1] == pytest.approx(pos_a[-1])
    assert px_b[-1] == pytest.approx(base["Close"].iloc[-1] * 0.65)


def test_validate_v5_mix_pipeline_causal():
    from scripts.validate_v5_mix import _v2_pipeline

    base = _merged()
    n = len(base)
    sig = np.ones(n)
    conf = np.full(n, 0.8)

    pos_a = _v2_pipeline(base, sig, conf, convention="causal")
    pos_b = _v2_pipeline(_bump_last_close(base), sig, conf, convention="causal")

    assert pos_a[-1] != 0.0
    assert pos_b[-1] == pytest.approx(pos_a[-1])
