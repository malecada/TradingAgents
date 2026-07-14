import numpy as np
import pandas as pd
import pytest
from tradingagents.stress.index import (
    zscore_365,
    composite_warn,
    _coin_components,
    _fng_component,
    build_components,
)


def _series(vals):
    idx = pd.date_range("2020-01-01", periods=len(vals), freq="D", tz="UTC")
    return pd.Series(vals, index=idx, dtype=float)


def test_zscore_needs_180_obs():
    s = _series(np.random.default_rng(0).normal(size=400))
    z = zscore_365(s)
    assert z.iloc[:179].isna().all()
    assert z.iloc[200:].notna().all()


def test_zscore_detects_shift():
    vals = [0.0] * 300 + [5.0] * 5
    z = zscore_365(_series(vals))
    assert z.iloc[-1] > 3  # 5-sigma-ish jump vs flat history


def test_composite_warn_hysteresis():
    idx = pd.date_range("2021-01-01", periods=6, freq="D", tz="UTC")
    comp = pd.DataFrame(
        {"z_fund": [0.0, 1.6, 1.4, 1.3, 1.1, 0.5],
         "z_oi":   [0.0, 1.6, 1.4, 1.3, 1.1, 0.5]},
        index=idx,
    )
    out = composite_warn(comp, ["z_fund", "z_oi"], k=1.5)
    # on at 1.6, stays on at 1.4 and 1.3 (>= k-0.25=1.25), off at 1.1
    assert out["warn"].tolist() == [False, True, True, True, False, False]


def test_composite_nan_when_component_missing():
    idx = pd.date_range("2021-01-01", periods=2, freq="D", tz="UTC")
    comp = pd.DataFrame({"z_fund": [1.0, np.nan], "z_oi": [1.0, 2.0]}, index=idx)
    out = composite_warn(comp, ["z_fund", "z_oi"], k=0.5)
    assert np.isnan(out["composite"].iloc[1])
    assert not out["warn"].iloc[1]


def test_zscore_zero_variance_is_nan():
    # Constant series -> rolling std is exactly 0 wherever min_periods is met.
    # Must guard against 0/0 -> inf; result must be NaN everywhere.
    s = _series([5.0] * 400)
    z = zscore_365(s)
    assert z.isna().all()


def _synthetic_deriv_df(rng, idx):
    return pd.DataFrame(
        {
            "funding_rate_ma7": rng.normal(0.0, 0.0005, len(idx)),
            "oi_close": rng.uniform(1e9, 2e9, len(idx)),
            "liq_total_usd": rng.uniform(1e6, 1e7, len(idx)),
        },
        index=idx,
    )


def test_coin_components_causal(tmp_path):
    # Regression guardrail: this project once shipped a same-bar look-ahead
    # that manufactured Sharpe 4 from Sharpe 0.3. _coin_components lags all
    # inputs by 1 day (`df.shift(1)`); day-D output must never depend on
    # day-D input.
    rng = np.random.default_rng(42)
    n = 400
    idx = pd.date_range("2022-01-01", periods=n, freq="D", tz="UTC", name="ts")
    df = _synthetic_deriv_df(rng, idx)

    path = tmp_path / "coin.parquet"
    df.to_parquet(path)
    out1 = _coin_components(path)

    # Perturb ONLY the last row's inputs by a large factor.
    df_mod = df.copy()
    last = df_mod.index[-1]
    df_mod.loc[last, ["funding_rate_ma7", "oi_close", "liq_total_usd"]] *= 1000.0
    path_mod = tmp_path / "coin_mod.parquet"
    df_mod.to_parquet(path_mod)
    out2 = _coin_components(path_mod)

    # The entire output frame -- including the last date's own row -- must
    # be unchanged: day-D output must not depend on day-D input.
    pd.testing.assert_frame_equal(out1, out2)

    # Sanity check that the perturbation isn't simply inert: extend both
    # series by one more day so the perturbed last row becomes "yesterday"
    # relative to the new day. Now it SHOULD show up in the output, proving
    # the lag mechanism (and this test) actually exercises the data.
    next_day = last + pd.Timedelta(days=1)
    extra = df.iloc[[-1]].copy()
    extra.index = pd.DatetimeIndex([next_day], tz="UTC", name="ts")
    df_ext1 = pd.concat([df, extra])
    df_ext2 = pd.concat([df_mod, extra])
    path_ext1 = tmp_path / "coin_ext1.parquet"
    path_ext2 = tmp_path / "coin_ext2.parquet"
    df_ext1.to_parquet(path_ext1)
    df_ext2.to_parquet(path_ext2)
    out_ext1 = _coin_components(path_ext1)
    out_ext2 = _coin_components(path_ext2)
    assert not out_ext1.loc[next_day].equals(out_ext2.loc[next_day])


def test_fng_component_causal(tmp_path):
    # Same causality guardrail as test_coin_components_causal, applied to
    # _fng_component (also lagged via `.shift(1)`).
    rng = np.random.default_rng(7)
    n = 400
    dates = pd.date_range("2022-01-01", periods=n, freq="D", tz="UTC")
    values = rng.uniform(10.0, 90.0, n)
    df = pd.DataFrame({"event_ts": dates, "value": values})

    path = tmp_path / "fng.parquet"
    df.to_parquet(path)
    out1 = _fng_component(path)

    df_mod = df.copy()
    last_idx = df_mod.index[-1]
    df_mod.loc[last_idx, "value"] = 999.0
    path_mod = tmp_path / "fng_mod.parquet"
    df_mod.to_parquet(path_mod)
    out2 = _fng_component(path_mod)

    # Changing the last day's F&G value must not change that day's z_fg.
    pd.testing.assert_series_equal(out1, out2)


def test_build_components_nan_propagation(tmp_path):
    # Two-coin equal-weight aggregate: if one coin is missing a data point
    # on a given date, z_fund on that date must be NaN, not a silent
    # 1-coin fallback average.
    rng = np.random.default_rng(11)
    n = 400
    idx = pd.date_range("2022-01-01", periods=n, freq="D", tz="UTC", name="ts")
    base = _synthetic_deriv_df(rng, idx)

    coin_a = base.copy()
    coin_b = base.copy()
    # Coin B is missing funding data on one date; Coin A stays fully valid.
    nan_date = idx[250]
    coin_b.loc[nan_date, "funding_rate_ma7"] = np.nan

    deriv_dir = tmp_path / "deriv"
    deriv_dir.mkdir()
    coin_a.to_parquet(deriv_dir / "coinA.parquet")
    coin_b.to_parquet(deriv_dir / "coinB.parquet")

    fng = pd.DataFrame({"event_ts": idx, "value": rng.uniform(10.0, 90.0, n)})
    fng_path = tmp_path / "fng.parquet"
    fng.to_parquet(fng_path)

    ew = build_components(["coinA", "coinB"], deriv_dir, fng_path)

    # _coin_components lags by 1 day, so the NaN input on `nan_date` shows
    # up in the output the following day.
    affected_date = nan_date + pd.Timedelta(days=1)

    # CHOSEN pre-registered behavior (see spec): the cross-coin EW mean is a
    # strict "all coins must have data" aggregate, not a silent per-row
    # fallback to whichever coins happen to be present. If any single coin
    # is missing an input, z_fund for that date is NaN, which in turn makes
    # composite_warn force warn OFF that day -- conservative by design: no
    # data means no warning, rather than a warning built on partial data.
    assert np.isnan(ew.loc[affected_date, "z_fund"])
