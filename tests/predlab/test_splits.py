from __future__ import annotations

from tradingagents.predlab.splits import rolling_origin


def test_no_label_overlap_property():
    # last usable train origin s = train_end - 1; its label covers (s, s+h];
    # purge guarantees s + h <= origin - embargo for every split
    for h in (1, 7, 24):
        for emb in (0, 3):
            splits = rolling_origin(500, min_train=100, horizon=h, embargo=emb)
            assert splits, f"expected splits for h={h} emb={emb}"
            for sp in splits:
                assert (sp.train_end - 1) + h <= sp.origin - emb


def test_origin_range_and_step():
    sps = rolling_origin(200, min_train=150, horizon=1, step=10)
    assert [s.origin for s in sps] == [150, 160, 170, 180, 190]


def test_train_end_formula():
    (sp,) = rolling_origin(101, min_train=100, horizon=7, embargo=3)
    assert sp.origin == 100
    assert sp.train_end == 100 - 7 - 3 + 1


def test_short_series_yields_nothing():
    assert rolling_origin(50, min_train=100, horizon=1) == []


def test_tiny_train_end_skipped():
    # origin exists but purged train set would be < 30 origins -> skipped
    sps = rolling_origin(60, min_train=40, horizon=20, embargo=0)
    # train_end = origin - 20 + 1; needs >= 30 => origin >= 49
    assert all(s.origin >= 49 for s in sps)
    assert [s.origin for s in sps] == list(range(49, 60))
