"""The 1h panel is deliberately NaN at missing bars. pct_change must NOT
forward-fill across those gaps, or a pandas major-version bump silently
changes gap-bar return attribution. See spec 2026-07-29-liq-fade-r1 section 8."""
import ast
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
FILES = [
    ROOT / "scripts" / "liq_fade_dev.py",
    ROOT / "scripts" / "liq_fade_forensics.py",
    ROOT / "scripts" / "liq_fade_repl.py",
]
# Files that MUST contain at least one pct_change call. liq_fade_repl.py is
# deliberately absent: it is created in Task 5 with no pct_change and gains its
# calls in Task 6, so an anti-vacuity assertion over it would be red between
# those two tasks. The pin check below still covers it from the moment it
# exists -- a file with zero calls trivially satisfies "all calls are pinned".
MUST_HAVE_CALLS = [
    ROOT / "scripts" / "liq_fade_dev.py",
    ROOT / "scripts" / "liq_fade_forensics.py",
]


def _pct_change_calls(path):
    """Yield every ast.Call node that is a .pct_change(...) attribute call."""
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "pct_change"):
            yield node


@pytest.mark.parametrize("path", MUST_HAVE_CALLS, ids=lambda p: p.name)
def test_anti_vacuity_file_has_pct_change_calls(path):
    """Guards the pin test below from passing on a file where a refactor
    removed every pct_change call."""
    assert list(_pct_change_calls(path)), (
        f"no pct_change calls in {path.name} -- the pin test is vacuous there")


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_every_pct_change_pins_fill_method_none(path):
    if not path.exists():
        pytest.skip(f"{path.name} not yet created")
    for node in _pct_change_calls(path):
        kw = {k.arg: k.value for k in node.keywords}
        assert "fill_method" in kw, (
            f"{path.name}:{node.lineno} pct_change() without explicit "
            "fill_method -- pandas 2 pads, pandas 3 does not")
        assert isinstance(kw["fill_method"], ast.Constant) and kw["fill_method"].value is None, (
            f"{path.name}:{node.lineno} fill_method must be the literal None")


def test_padding_actually_changes_gap_bar_returns():
    """Non-vacuity: the two fill_method settings genuinely disagree on a
    panel shaped like the real 1h store (NaN at a missing bar)."""
    s = pd.Series([100.0, np.nan, 110.0, 121.0])
    padded = s.pct_change(fill_method="pad")
    unpadded = s.pct_change(fill_method=None)
    # index 2: padded compares 110 against the padded 100 -> +10%;
    # unpadded compares 110 against NaN -> NaN.
    assert padded.iloc[2] == pytest.approx(0.10)
    assert np.isnan(unpadded.iloc[2])
