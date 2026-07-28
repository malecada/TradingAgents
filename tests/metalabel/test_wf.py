import numpy as np
import pandas as pd
import warnings

from tradingagents.metalabel.wf import EMBARGO_CAL_DAYS, purged_walk_forward


def _meta(n=400, start="2021-07-01"):
    ev = pd.date_range(start, periods=n, freq="3D")
    return pd.DataFrame({
        "event_date": ev,
        "touch_date": ev + pd.Timedelta(days=10),
        "coin": "bitcoin",
    })


def test_no_train_event_touches_into_test():
    meta = _meta()
    folds = purged_walk_forward(meta, "2021-07-01", "2025-03-31")
    assert len(folds) > 3
    for tr, te in folds:
        test_start = meta.iloc[te]["event_date"].min()
        assert (meta.iloc[tr]["touch_date"]
                < test_start - pd.Timedelta(days=EMBARGO_CAL_DAYS)).all()
        # no index overlap, train strictly before test
        assert set(tr).isdisjoint(set(te))


def test_expanding_and_contiguous_test_blocks():
    meta = _meta()
    folds = purged_walk_forward(meta, "2021-07-01", "2025-03-31")
    sizes = [len(tr) for tr, _ in folds]
    assert sizes == sorted(sizes)  # expanding
    covered = np.concatenate([te for _, te in folds])
    assert len(covered) == len(set(covered))  # each test event exactly once


def test_min_train_events_skips_early_folds():
    meta = _meta(n=60)  # tiny -> early folds under 150 train events
    with warnings.catch_warnings(record=True) as rec:
        warnings.simplefilter("always")
        folds = purged_walk_forward(meta, "2021-07-01", "2022-06-30")
    assert all(len(tr) >= 150 for tr, _ in folds) or len(folds) == 0


def test_embargo_bars_widens_admissible_train_set():
    meta = _meta()
    folds_tight = purged_walk_forward(
        meta, "2021-07-01", "2025-03-31", embargo_bars=1, min_train_events=0
    )
    folds_wide = purged_walk_forward(
        meta, "2021-07-01", "2025-03-31", embargo_bars=15, min_train_events=0
    )
    assert len(folds_tight) == len(folds_wide)
    sizes_tight = [len(tr) for tr, _ in folds_tight]
    sizes_wide = [len(tr) for tr, _ in folds_wide]
    # smaller embargo_bars -> shorter embargo -> more admissible train events
    assert any(t > w for t, w in zip(sizes_tight, sizes_wide))
    assert all(t >= w for t, w in zip(sizes_tight, sizes_wide))
