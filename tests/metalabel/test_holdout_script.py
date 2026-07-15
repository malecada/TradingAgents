import json
import pandas as pd
import pytest

import scripts.metalabel_holdout as h
from tradingagents.metalabel.wf import EMBARGO_CAL_DAYS


def test_refuses_without_chosen_tau(tmp_path, monkeypatch):
    res = tmp_path / "dev_results.json"
    res.write_text(json.dumps({"chosen_tau": None}))
    monkeypatch.setattr(h, "DEV_RESULTS", res)
    with pytest.raises(RuntimeError, match="G2 did not pass"):
        h.main()


def test_refuses_when_already_spent(tmp_path, monkeypatch):
    res = tmp_path / "dev_results.json"
    res.write_text(json.dumps({"chosen_tau": 0.5}))
    flag = tmp_path / "holdout_spent.flag"
    flag.write_text("spent")
    monkeypatch.setattr(h, "DEV_RESULTS", res)
    monkeypatch.setattr(h, "SPENT_FLAG", flag)
    with pytest.raises(RuntimeError, match="already spent"):
        h.main()


def test_g3_train_mask_purges_dev_tail_events_touching_holdout():
    # Regression for I1: an event_date <= DEV_END alone is not sufficient —
    # a dev-tail event whose label resolves (touch_date) inside the
    # embargo window right before HOLDOUT_START had its label computed
    # using holdout-window prices. g3_train_mask must exclude it.
    purge_cutoff = pd.Timestamp(h.HOLDOUT_START) - pd.Timedelta(days=EMBARGO_CAL_DAYS)
    meta = pd.DataFrame({
        "event_date": [
            pd.Timestamp(h.DEV_START) + pd.Timedelta(days=10),  # clean, early dev event
            pd.Timestamp(h.DEV_END) - pd.Timedelta(days=5),      # dev-tail, clean touch
            pd.Timestamp(h.DEV_END) - pd.Timedelta(days=2),      # dev-tail, leaking touch
        ],
        "touch_date": [
            purge_cutoff - pd.Timedelta(days=30),
            purge_cutoff - pd.Timedelta(days=1),   # resolves just before cutoff -> keep
            purge_cutoff + pd.Timedelta(days=1),   # resolves after cutoff -> purge
        ],
    })

    mask = h.g3_train_mask(meta)

    assert list(mask) == [True, True, False]


def test_g3_train_mask_excludes_events_past_dev_end():
    meta = pd.DataFrame({
        "event_date": [pd.Timestamp(h.DEV_END) + pd.Timedelta(days=1)],
        "touch_date": [pd.Timestamp(h.DEV_END) + pd.Timedelta(days=2)],
    })
    mask = h.g3_train_mask(meta)
    assert list(mask) == [False]
