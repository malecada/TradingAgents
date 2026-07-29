"""P3 is the discriminating control liq_fade_i1 never ran: is the return from
crash TIMING, or from generic long exposure on high-volatility days?"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))


def _panel(n_bars=3000, seed=11):
    idx = pd.date_range("2021-01-01", periods=n_bars, freq="1h", tz="UTC")
    rng = np.random.default_rng(seed)
    close = pd.DataFrame({"AAAUSDT": 100.0 * np.exp(
        np.cumsum(rng.normal(0, 0.003, n_bars)))}, index=idx)
    qvol = pd.DataFrame({"AAAUSDT": rng.lognormal(10.0, 0.3, n_bars)}, index=idx)
    return close, qvol


def test_vol_only_ignores_the_return_condition():
    """A bar with a huge volume spike and a POSITIVE return must trigger the
    control but not the primary."""
    from liq_fade_repl import vol_only_triggers
    from tradingagents.xsect.liq_fade import cascade_triggers
    close, qvol = _panel()
    spike = 2500
    qvol.iloc[spike, 0] *= 500.0          # enormous volume
    close.iloc[spike, 0] *= 1.05          # POSITIVE return, not a crash
    ctrl = vol_only_triggers(qvol, thr=3.5)
    prim = cascade_triggers(close, qvol, thr=3.5)
    assert bool(ctrl.iloc[spike, 0]), "control must fire on the volume spike"
    assert not bool(prim.iloc[spike, 0]), "primary must NOT fire on a positive return"


def test_vol_only_is_a_superset_of_primary():
    """Every primary trigger requires z_vol >= thr, so it must also be a
    control trigger. Non-vacuous only if the primary fires at all."""
    from liq_fade_repl import vol_only_triggers
    from tradingagents.xsect.liq_fade import cascade_triggers
    close, qvol = _panel()
    for bar in (1800, 2200, 2600):
        qvol.iloc[bar, 0] *= 200.0
        close.iloc[bar, 0] *= 0.93
    prim = cascade_triggers(close, qvol, thr=3.0)
    ctrl = vol_only_triggers(qvol, thr=3.0)
    assert prim.to_numpy().sum() > 0, "fixture produced no primary triggers"
    assert (prim.to_numpy() & ~ctrl.to_numpy()).sum() == 0, (
        "primary trigger outside the control set -- z_vol condition not shared")


@pytest.mark.parametrize("primary,control,expected_pass,expected_verdict", [
    (1.30, 0.10, True,  "PASS"),                 # control 0.10 < 0.5, sep 1.20 >= 0.75
    (1.30, 0.49, True,  "PASS"),                 # control 0.49 < 0.5, sep 0.81 >= 0.75
    (1.30, 0.60, False, "NEGATIVE-confounded"),  # control 0.60 >= 0.5
    (1.30, 0.56, False, "NEGATIVE-confounded"),  # control ok but sep 0.74 < 0.75
    (0.80, 0.10, False, "NEGATIVE"),             # weak primary -> plain NEGATIVE
    (0.80, 0.70, False, "NEGATIVE"),             # weak primary, label still not confounded
])
def test_p3_verdict_matrix(primary, control, expected_pass, expected_verdict):
    from liq_fade_repl import p3_verdict
    v = p3_verdict(primary, control)
    assert v["pass"] is expected_pass
    assert v["verdict"] == expected_verdict


def test_confounded_label_reserved_for_strong_primary():
    """A weak primary can never be labelled confounded -- a signal that does
    not clear the floor cannot be said to be explained away by vol drift."""
    from liq_fade_repl import p3_verdict
    for control in (0.0, 0.4, 0.9, 2.0):
        v = p3_verdict(0.5, control)
        assert v["verdict"] == "NEGATIVE"
        assert "confounded" not in v["verdict"].lower()
