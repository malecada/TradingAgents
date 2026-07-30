from __future__ import annotations

import numpy as np
from dieboldmariano import dm_test as ref_dm

from tradingagents.predlab import dm, meanstats


def test_dm_matches_reference_package_h1():
    rng = np.random.default_rng(11)
    actual = rng.normal(0, 1, 300)
    p1 = actual + rng.normal(0, 1.0, 300)  # worse
    p2 = actual + rng.normal(0, 0.6, 300)  # better
    ours = dm.dm_test((actual - p1) ** 2, (actual - p2) ** 2, h=1, alternative="two-sided")
    ref_stat, ref_p = ref_dm(actual, p1, p2, one_sided=False)
    assert np.isclose(ours.stat, ref_stat, rtol=1e-4)
    assert np.isclose(ours.pvalue, ref_p, rtol=1e-3)


def test_dm_matches_reference_package_h7():
    rng = np.random.default_rng(13)
    actual = rng.normal(0, 1, 400)
    p1 = actual + rng.normal(0, 0.9, 400)
    p2 = actual + rng.normal(0, 0.7, 400)
    ours = dm.dm_test((actual - p1) ** 2, (actual - p2) ** 2, h=7, alternative="two-sided")
    ref_stat, ref_p = ref_dm(actual, p1, p2, h=7, one_sided=False)
    assert np.isclose(ours.stat, ref_stat, rtol=1e-4)
    assert np.isclose(ours.pvalue, ref_p, rtol=1e-3)


def test_dm_sign_convention_model_better_positive():
    rng = np.random.default_rng(1)
    base = 2.0 + rng.normal(0, 0.01, 200)
    model = np.full(200, 1.0)
    r = dm.dm_test(base, model, h=1)
    assert r.stat > 0 and r.pvalue < 0.01


def test_dm_one_sided_halves_two_sided_when_positive():
    rng = np.random.default_rng(8)
    base = 1.5 + rng.normal(0, 0.3, 250)
    model = 1.0 + rng.normal(0, 0.3, 250)
    two = dm.dm_test(base, model, h=1, alternative="two-sided")
    one = dm.dm_test(base, model, h=1, alternative="greater")
    assert np.isclose(one.pvalue, two.pvalue / 2, rtol=1e-9)


def test_dm_degenerate_identical_losses():
    loss = np.ones(100)
    r = dm.dm_test(loss, loss.copy(), h=1)
    assert r.degenerate and np.isnan(r.stat) and np.isnan(r.pvalue)


def test_dm_degenerate_too_short():
    r = dm.dm_test(np.array([1.0, 2.0]), np.array([0.5, 0.4]), h=1)
    assert r.degenerate


def test_clark_west_nested_null_not_rejected_and_alt_rejected():
    rng = np.random.default_rng(5)
    y = rng.normal(0, 1, 800)  # truly unpredictable
    yh_small = np.zeros(800)  # RW/zero forecast (true model)
    yh_big = yh_small + rng.normal(0, 0.3, 800)  # nested bigger model = noise added
    r_null = dm.clark_west(y - yh_small, y - yh_big, yh_small, yh_big, h=1)
    assert r_null.pvalue > 0.01  # must not strongly reject under null

    x = rng.normal(0, 1, 800)
    y2 = 0.6 * x + rng.normal(0, 1, 800)
    r_alt = dm.clark_west(y2 - 0.0, y2 - 0.6 * x, np.zeros(800), 0.6 * x, h=1)
    assert r_alt.pvalue < 0.01  # genuine nested improvement detected


def test_gw_equals_nw_on_loss_diff():
    rng = np.random.default_rng(9)
    a, b = rng.normal(1, 0.2, 300), rng.normal(0.8, 0.2, 300)
    assert np.isclose(dm.gw_test(a, b, h=3).stat, meanstats.nw_tstat(a - b, lag=2), rtol=1e-9)


def test_gw_two_sided_pvalue_range():
    rng = np.random.default_rng(10)
    a = rng.normal(1.0, 0.2, 300)
    r = dm.gw_test(a, a + 0.001 * rng.normal(size=300), h=1)
    assert 0.0 <= r.pvalue <= 1.0
