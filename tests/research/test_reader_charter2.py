"""Reader configuration (Charter 2), evaluation side: fitted forecasters, panel, gates, verdict, registered run.

Synthetic fixtures only; no market data, no network. The fixtures of the extraction side are shared with
``test_reader_extract.py``.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import reader_charter2_run as run_script  # noqa: E402
import reader_extract as rx  # noqa: E402
from test_reader_extract import FakeClient, commit, extract, script_root, sha, store_frames  # noqa: E402
from tradingagents.agents_v2 import evaluate  # noqa: E402
from tradingagents.agents_v2.charter1b import CacheError  # noqa: E402
from tradingagents.dossier.quant_forecast import RIDGE_ALPHA  # noqa: E402
from tradingagents.reader import charter2 as c2, consensus, model, schema  # noqa: E402
from tradingagents.reader.extract import CallCache, Reader  # noqa: E402

WEEK = pd.Timedelta(days=7)
COLS = ["f1", "f2"]


# ---------------------------------------------------------------- fixtures
def _grid(weeks: int = 12, n: int = 8, seed: int = 0, start: str = "2022-01-07") -> pd.DataFrame:
    """Weekly rows of ``n`` symbols with two noise features and a noise return."""
    rng = np.random.default_rng(seed)
    days = pd.date_range(start, periods=weeks, freq="7D", tz="UTC")
    frame = pd.DataFrame([(d, f"S{i:02d}USDT") for d in days for i in range(n)], columns=["date", "symbol"])
    for col in COLS:
        frame[col] = rng.normal(size=len(frame))
    frame["fwd_ret"] = 0.05 * rng.normal(size=len(frame))
    return frame


def _redrawn(panel: pd.DataFrame, days, seed: int = 99) -> pd.DataFrame:
    """The panel with new return values on the given days."""
    out, mask = panel.copy(), panel["date"].isin(list(days)).to_numpy()
    out.loc[mask, "fwd_ret"] = np.random.default_rng(seed).normal(size=int(mask.sum()))
    return out


def _manual(panel: pd.DataFrame, day, train_days) -> tuple[np.ndarray, np.ndarray]:
    """Ridge score of one day from the given training days, written out directly."""
    X = (panel.groupby("date")[COLS].rank(pct=True) - 0.5).fillna(0.0).to_numpy()
    y = (panel.groupby("date")["fwd_ret"].rank(pct=True) - 0.5).to_numpy()
    train = panel["date"].isin(list(train_days)).to_numpy() & np.isfinite(y)
    beta = np.linalg.solve(X[train].T @ X[train] + RIDGE_ALPHA * np.eye(len(COLS)), X[train].T @ y[train])
    return X[(panel["date"] == day).to_numpy()] @ beta, beta


def synth(signal: float = 0.0, weeks: int = 156, n: int = 50, seed: int = 0):
    """(universe rows, text features, record table, forward returns, funding, quant forecast, flags) of the
    registered shape. ``signal`` plants an effect of ``tone_7d`` on the forward return."""
    rng = np.random.default_rng(seed)
    days = pd.date_range(c2.PANEL_START, periods=weeks, freq="7D", tz="UTC")
    syms = [f"S{i:02d}USDT" for i in range(n)]
    top = pd.DataFrame([(d, s) for d in days for s in syms], columns=["date", "symbol"])
    top["base"] = top["symbol"].str[:-4]
    for col in dict.fromkeys([*c2.QUANT, *c2.CONTROLS]):
        top[col] = rng.normal(size=len(top))
    top["vol_ewma20"] = rng.uniform(0.3, 1.5, len(top))
    top.loc[rng.uniform(size=len(top)) < 0.4, "size_rank"] = np.nan
    feats = top[["date", "symbol", "base"]].copy()
    for col in c2.TEXT_COLUMNS:
        feats[col] = np.where(rng.uniform(size=len(top)) < 0.5, 0.0, rng.normal(size=len(top)).round(1))
    feats.loc[feats["date"] < days[min(5, weeks - 1)], "attn_abn"] = np.nan
    fwd = top[["date", "symbol"]].copy()
    fwd["fwd_ret"] = 0.08 * (rng.normal(size=len(top)) + signal * feats["tone_7d"].to_numpy() + 0.1 * top["ret_4w"].to_numpy())
    fwd["delisted"] = False
    fwd = fwd[rng.uniform(size=len(fwd)) > 0.01].reset_index(drop=True)
    funding = top[["date", "symbol"]].assign(funding_week=1e-4, n_settlements=21)
    quant = top[["date", "symbol"]].assign(pred_rank_pct=rng.uniform(size=len(top)))
    flags = top[["date", "symbol"]].iloc[::3].rename(columns={"date": "friday"})
    flags = flags.assign(friday=flags["friday"].dt.strftime("%Y-%m-%d"), identified=rng.uniform(size=len(flags)) > 0.5,
                         month_within_6=False)
    fields = schema.FIELDS[:-1]
    first = ("subject", "other", "occurred", "neutral", 1)
    rows = [{"doc_id": f"d{i}", "base": "S00", "alias": "Asset_A", "focus_only": False, "resolution": "agreed",
             **dict(zip(fields, first)), "evidence": "x", **{f"a_{f}": v for f, v in zip(fields, first)},
             **{f"b_{f}": v for f, v in zip(fields, ("subject", "other", "occurred", "neutral", 2))}} for i in range(20)]
    rows.append({**rows[0], "doc_id": "u", "resolution": "unresolved", **dict.fromkeys(schema.FIELDS),
                 **{f"a_{f}": None for f in fields}, **{f"b_{f}": None for f in fields}})
    return top, feats, consensus.record_frame(rows), fwd, funding, quant, flags


def _scored(weeks: int = 30, n: int = 20, seed: int = 1) -> pd.DataFrame:
    """A joined panel with a noise column in the place of the gate score."""
    top, feats, _, fwd, _, quant, flags = synth(0.0, weeks=weeks, n=n, seed=seed)
    panel = c2.assemble_panel(top, feats, fwd, quant, flags)
    panel[c2.GATE_SCORE] = np.random.default_rng(seed).normal(size=len(panel))
    return panel


def _gate_verdict(signal: float, seed: int = 0) -> dict:
    """Verdict of the two gates on a synthetic panel of the registered shape (gate score only)."""
    top, feats, _, fwd, _, quant, flags = synth(signal, seed=seed)
    panel = c2.assemble_panel(top, feats, fwd, quant, flags)
    panel[c2.GATE_SCORE], _ = model.walk_forward(panel, c2.TEXT)
    test = panel[panel[c2.GATE_SCORE].notna()]
    gates, _ = c2.gate_statistics(test)
    return c2.build_verdict({"gates": gates, "weeks": {"test": int(test["date"].nunique())}}, {}, {}, {})


def _evaluation(t=2.5, beta=0.01, y2023=0.01, y2024=0.02, **extra) -> dict:
    return {"gates": {"encompassing_text_vs_quant": {"weeks": 104, "beta_quant": 0.0, "t_quant": 0.0, "beta_llm": beta, "t_llm": t},
                      "text_coefficient_by_year": {"2023": {"weeks": 52, "mean": y2023}, "2024": {"weeks": 52, "mean": y2024}}},
            "weeks": {"test": 104}, **extra}


def _verdict(**kwargs) -> dict:
    return c2.build_verdict(_evaluation(**kwargs), {}, {}, {})


# ---------------------------------------------------------------- ranks, target, ridge
def test_cross_sectional_rank_is_within_the_week_and_neutral_for_missing_values():
    days = pd.to_datetime(["2022-01-07"] * 4 + ["2022-01-14"] * 2, utc=True)
    panel = pd.DataFrame({"date": days, "f1": [3.0, 1.0, np.nan, 2.0, 5.0, 5.0], "fwd_ret": [0.1, np.nan, -0.2, 0.0, 0.3, 0.1]})
    assert np.allclose(model.xs_rank(panel, ["f1"])["f1"].to_numpy(), [0.5, -1 / 6, 0.0, 1 / 6, 0.25, 0.25])
    want = [0.5, np.nan, -1 / 6, 1 / 6, 0.5, 0.0]
    assert np.allclose(model.target(panel).to_numpy(), want, equal_nan=True)       # a missing return stays missing


def test_ridge_is_the_penalised_normal_equation_without_intercept():
    rng = np.random.default_rng(0)
    X, y = rng.normal(size=(200, 3)), rng.normal(size=200)
    predict, beta = model.fit_ridge(X, y)
    assert np.allclose(beta, np.linalg.solve(X.T @ X + 10.0 * np.eye(3), X.T @ y)) and RIDGE_ALPHA == 10.0
    assert np.allclose(predict(X[:5]), X[:5] @ beta) and np.allclose(predict(np.zeros((1, 3))), 0.0)
    _, plain = model.fit_ridge(X, y, alpha=0.0)
    assert np.allclose(plain, np.linalg.lstsq(X, y, rcond=None)[0])
    assert np.linalg.norm(beta) < np.linalg.norm(plain)


# ---------------------------------------------------------------- walk-forward
def test_walk_forward_equals_a_fit_on_the_earlier_weeks():
    panel = _grid(weeks=12)
    days = sorted(panel["date"].unique())
    score, info = model.walk_forward(panel, COLS, burn_in=5)
    assert score[panel["date"].isin(days[:5])].isna().all() and score[panel["date"].isin(days[5:])].notna().all()
    assert list(info.index) == days[5:] and list(info.columns) == COLS
    for k in (5, 8, 11):
        want, beta = _manual(panel, days[k], days[:k])
        assert np.allclose(score[panel["date"] == days[k]].to_numpy(), want)
        assert np.allclose(info.loc[days[k]].to_numpy(), beta)
    assert model.walk_forward(panel, COLS)[0].isna().all()                       # registered burn-in: 52 weeks
    assert model.walk_forward(panel, COLS)[1].empty


def test_later_returns_do_not_change_a_score():
    panel = _grid(weeks=12)
    days = sorted(panel["date"].unique())
    base, _ = model.walk_forward(panel, COLS, burn_in=5)
    upto = panel["date"].isin(days[:9]).to_numpy()
    later, _ = model.walk_forward(_redrawn(panel, days[8:]), COLS, burn_in=5)      # week 8 itself and everything after
    assert np.array_equal(later[upto].to_numpy(), base[upto].to_numpy(), equal_nan=True)
    assert not np.allclose(later[~upto].to_numpy(), base[~upto].to_numpy())
    previous, _ = model.walk_forward(_redrawn(panel, days[7:8]), COLS, burn_in=5)   # the week before is training data
    week8, before = (panel["date"] == days[8]).to_numpy(), panel["date"].isin(days[:8]).to_numpy()
    assert not np.allclose(previous[week8].to_numpy(), base[week8].to_numpy())
    assert np.array_equal(previous[before].to_numpy(), base[before].to_numpy(), equal_nan=True)


def test_a_week_trains_only_once_its_outcome_is_realised():
    grid = _grid(weeks=4)                                                        # days 0, 7, 14, 21
    days = sorted(grid["date"].unique())
    monday = _grid(weeks=1, seed=5, start="2022-01-24")                          # day 17: outcome realised on day 24
    panel = pd.concat([grid, monday], ignore_index=True)
    score, info = model.walk_forward(panel, COLS, burn_in=3)
    scored = sorted(panel.loc[score.notna(), "date"].unique())
    assert scored == [days[3]] and list(info.index) == [days[3]]                # day 14 and day 17 have two realised weeks
    want, _ = _manual(panel, days[3], days[:3])                                 # day 17 is not in the training set
    assert np.allclose(score[panel["date"] == days[3]].to_numpy(), want)


def test_rows_without_a_return_are_scored_and_left_out_of_the_training():
    panel = _grid(weeks=10)
    days = sorted(panel["date"].unique())
    holes = panel.copy()
    holes.loc[[3, 17, 30], "fwd_ret"] = np.nan                                   # three training rows
    holes.loc[holes["date"] == days[9], "fwd_ret"] = np.nan                      # the newest week has no outcome yet
    score, _ = model.walk_forward(holes, COLS, burn_in=5)
    assert score[holes["date"].isin(days[5:])].notna().all()
    want, _ = _manual(holes, days[9], days[:9])
    assert np.allclose(score[holes["date"] == days[9]].to_numpy(), want)
    full, _ = model.walk_forward(panel, COLS, burn_in=5)
    assert not np.allclose(full[panel["date"] == days[9]].to_numpy(), want)


def test_boosted_tree_is_deterministic_and_finds_a_planted_feature(monkeypatch):
    monkeypatch.setattr(model, "GBM_ROUNDS", 10)
    panel = _grid(weeks=44, n=10, seed=2)
    panel["fwd_ret"] += 0.2 * panel["f1"]
    first, info = model.walk_forward(panel, COLS, fit=model.fit_gbm, burn_in=40)
    again, _ = model.walk_forward(panel, COLS, fit=model.fit_gbm, burn_in=40)
    assert np.array_equal(first.to_numpy(), again.to_numpy(), equal_nan=True)
    test = first.notna()
    assert int(test.sum()) == 40 and list(info.columns) == COLS and len(info) == 4
    assert (info["f1"] > info["f2"]).all()                                       # gain importance per test week
    assert np.corrcoef(first[test], model.xs_rank(panel, COLS).loc[test, "f1"])[0, 1] > 0.5
    assert model.GBM_PARAMS["seed"] == 20261112 and model.GBM_PARAMS["deterministic"] and model.GBM_PARAMS["num_threads"] == 1


def test_cross_fit_leaves_the_own_block_and_the_embargo_out():
    panel = _grid(weeks=24)
    days = sorted(panel["date"].unique())
    base = model.cross_fit(panel, COLS)                                          # six blocks of four weeks, embargo one week
    assert base.notna().all() and (model.CROSS_FIT_BLOCKS, model.CROSS_FIT_EMBARGO_WEEKS) == (6, 1)
    block = panel["date"].isin(days[8:12]).to_numpy()
    inside = model.cross_fit(_redrawn(panel, days[7:13]), COLS)                  # the block and one week on each side
    assert np.array_equal(inside[block].to_numpy(), base[block].to_numpy())
    outside = model.cross_fit(_redrawn(panel, days[:1]), COLS)
    assert not np.allclose(outside[block].to_numpy(), base[block].to_numpy())
    want, _ = _manual(panel, days[9], [*days[:7], *days[13:]])
    assert np.allclose(base[panel["date"] == days[9]].to_numpy(), want)
    edge, _ = _manual(panel, days[0], days[5:])                                  # first block: weeks 0-3, embargo week 4
    assert np.allclose(base[panel["date"] == days[0]].to_numpy(), edge)


# ---------------------------------------------------------------- feature sets
def test_registered_feature_sets():
    assert c2.TEXT == ["attn_7d", "attn_abn", "tone_7d", "tone_30d", "unfav_7d", "sched_fwd", "stance_7d", "supply_30d"]
    assert c2.FULL == c2.QUANT + c2.TEXT and len(set(c2.FULL)) == len(c2.FULL)
    assert c2.GATE_SCORE == "s_text" and c2.RIDGE_SCORES["s_text"] == c2.TEXT and c2.RIDGE_SCORES["s_full"] == c2.FULL
    assert c2.GBM_SCORES == {"g_text": c2.TEXT, "g_full": c2.FULL, "g_quant": c2.QUANT}
    assert (c2.GATE_TEXT_T, c2.GATE_YEARS, c2.MIN_WEEK_ROWS, c2.UNIVERSE_N) == (2.0, (2023, 2024), 15, 50)
    assert (c2.PANEL_START, c2.PANEL_END) == ("2022-01-07", "2024-12-27")
    assert set(c2.SCORES) <= set(c2.OUTPUT_COLUMNS) and set(c2.TEXT) <= set(c2.TEXT_COLUMNS)
    for a, b in [*c2.PAIRED, *c2.ENCOMPASSING]:
        assert {a, b} <= {*c2.SCORES, "p_quant"}
    assert set(c2.BOOK_SCORES) <= {*c2.SCORES, "p_quant"}


# ---------------------------------------------------------------- panel
def test_panel_joins_one_row_per_universe_row():
    top, feats, _, fwd, _, quant, flags = synth(0.0, weeks=8, n=6)
    shuffled = top.sample(frac=1.0, random_state=1)
    panel = c2.assemble_panel(shuffled, feats, fwd, quant, flags)
    assert list(panel.columns) == c2.PANEL_COLUMNS and len(panel) == len(top) == 48
    assert panel[["date", "symbol"]].equals(panel[["date", "symbol"]].sort_values(["date", "symbol"]).reset_index(drop=True))
    assert str(panel["date"].dt.tz) == "UTC"
    key = ["date", "symbol"]
    want = top[key].merge(fwd, on=key, how="left").merge(quant, on=key, how="left").sort_values(key)
    assert np.allclose(panel["fwd_ret"].to_numpy(), want["fwd_ret"].to_numpy(), equal_nan=True)
    assert int(panel["fwd_ret"].isna().sum()) == len(top) - len(fwd)             # a missing outcome stays missing
    assert np.allclose(panel["p_quant"].to_numpy(), want["pred_rank_pct"].to_numpy())
    assert int(panel["identified"].notna().sum()) == len(flags) == 16
    assert panel["attn_abn"].isna().any()                                        # allowed: short own history
    bare = c2.assemble_panel(top, feats, fwd, quant, None)
    assert bare["identified"].isna().all() and list(bare.columns) == c2.PANEL_COLUMNS


def test_panel_refuses_incomplete_or_duplicated_inputs():
    top, feats, _, fwd, _, quant, flags = synth(0.0, weeks=8, n=6)
    with pytest.raises(ValueError, match="not unique"):
        c2.assemble_panel(pd.concat([top, top.iloc[:1]]), feats, fwd, quant, flags)
    with pytest.raises(ValueError, match="without text features"):
        c2.assemble_panel(top, feats.iloc[1:], fwd, quant, flags)
    broken = feats.copy()
    broken.loc[broken.index[3], "tone_7d"] = np.nan
    with pytest.raises(ValueError, match="missing values"):
        c2.assemble_panel(top, broken, fwd, quant, flags)
    for name, frames in (("features", (pd.concat([feats, feats.iloc[:1]]), fwd, quant, flags)),
                         ("returns", (feats, pd.concat([fwd, fwd.iloc[:1]]), quant, flags)),
                         ("quant", (feats, fwd, pd.concat([quant, quant.iloc[:1]]), flags)),
                         ("flags", (feats, fwd, quant, pd.concat([flags, flags.iloc[:1]])))):
        with pytest.raises(pd.errors.MergeError):
            c2.assemble_panel(top, *frames)
        assert name


def test_text_features_need_exactly_the_work_list(tmp_path):
    items, docs, cards = store_frames(weeks=8, n_syms=8, docs_per_week=12)
    top = c2.universe(cards)
    sets, work = c2.reading(items, docs, top)
    _, unit_list = rx.build_units(items, docs, cards)
    reader = Reader(FakeClient(), CallCache(tmp_path / "calls.jsonl"))
    records = consensus.record_frame([row for unit in unit_list for row in consensus.resolve(reader, unit)])
    assert len(records) == len(work) == 80
    feats = c2.text_features(items, sets, records, top)
    assert len(feats) == len(top) == 64 and set(c2.TEXT_COLUMNS) <= set(feats.columns)
    assert not feats[["date", "symbol"]].duplicated().any()
    shuffled = c2.text_features(items, sets, records.sample(frac=1.0, random_state=2), top)
    pd.testing.assert_frame_equal(shuffled, feats)                               # the order of the records does not matter
    with pytest.raises(ValueError, match="differ"):
        c2.text_features(items, sets, records.iloc[1:], top)
    with pytest.raises(ValueError, match="duplicate"):
        c2.text_features(items, sets, pd.concat([records, records.iloc[:1]]), top)
    with pytest.raises(ValueError, match="differ"):
        c2.text_features(items, sets, pd.concat([records, records.iloc[:1].assign(doc_id="other")]), top)
    panel = c2.assemble_panel(top, feats, top[["date", "symbol"]].assign(fwd_ret=0.0, delisted=False),
                              top[["date", "symbol"]].assign(pred_rank_pct=0.5), None)
    assert len(panel) == 64                                                      # the features of a real build join the panel


# ---------------------------------------------------------------- gate statistics
def test_encompassing_series_is_the_charter_1b_regression_with_its_weekly_path():
    panel = _scored(weeks=30)
    summary, weekly = c2.encompassing_series(panel, c2.GATE_SCORE)
    assert summary == pytest.approx(evaluate.encompassing(panel, c2.GATE_SCORE, "p_quant"))
    assert summary["weeks"] == len(weekly) == 30 and list(weekly.columns) == ["beta_quant", "beta_llm"]
    assert weekly["beta_llm"].mean() == pytest.approx(summary["beta_llm"])
    assert summary["t_llm"] == pytest.approx(evaluate.newey_west_t(weekly["beta_llm"]))
    days = sorted(panel["date"].unique())
    short, path = c2.encompassing_series(panel[panel["date"].isin(days[:2])], c2.GATE_SCORE)
    assert short == {"weeks": 2, "beta_quant": None, "t_quant": None, "beta_llm": None, "t_llm": None} and len(path) == 2
    assert short == evaluate.encompassing(panel[panel["date"].isin(days[:2])], c2.GATE_SCORE, "p_quant")
    thin, path = c2.encompassing_series(panel.groupby("date").head(c2.MIN_WEEK_ROWS - 1), c2.GATE_SCORE)
    assert thin["weeks"] == 0 and thin["t_llm"] is None and path.empty           # a week needs 15 complete rows
    exact, _ = c2.encompassing_series(panel.dropna(subset=["fwd_ret"]).groupby("date").head(c2.MIN_WEEK_ROWS), c2.GATE_SCORE)
    assert exact["weeks"] == 30


def test_gate_statistics_split_the_weekly_coefficient_by_calendar_year():
    panel = _scored(weeks=156)                                                   # 2022-01-07 to 2024-12-27
    gates, weekly = c2.gate_statistics(panel)
    assert gates["encompassing_text_vs_quant"] == pytest.approx(c2.encompassing_series(panel, "s_text")[0])
    years = pd.DatetimeIndex(weekly.index).year
    for year in (2023, 2024):
        got = gates["text_coefficient_by_year"][str(year)]
        assert got["weeks"] == 52 and got["mean"] == pytest.approx(weekly["beta_llm"][years == year].mean())
    assert set(gates["text_coefficient_by_year"]) == {"2023", "2024"} and len(weekly) == 156
    early, _ = c2.gate_statistics(panel[panel["date"] < pd.Timestamp("2024-01-01", tz="UTC")])
    assert early["text_coefficient_by_year"]["2024"] == {"weeks": 0, "mean": None}
    assert early["text_coefficient_by_year"]["2023"]["weeks"] == 52


# ---------------------------------------------------------------- verdict
def test_verdict_passes_only_with_both_gates():
    passed = _verdict()
    assert passed["verdict"] == "PASS" and passed["failed_gates"] == [] and passed["descriptive_errors"] == []
    assert passed["test_weeks"] == 104 and set(passed["gates"]) == {"text_encompassing", "text_coefficient_sign_by_year"}
    assert passed["gates"]["text_encompassing"]["value"] == {"nw_t": 2.5, "mean_coefficient": 0.01, "weeks": 104}
    assert passed["gates"]["text_coefficient_sign_by_year"]["value"] == {"2023": 0.01, "2024": 0.02}
    assert _verdict(t=2.0)["verdict"] == "PASS" and _verdict(t=np.float64(2.0))["verdict"] == "PASS"
    both = _verdict(t=1.0, y2023=-0.01)
    assert both["verdict"] == "FAIL" and both["failed_gates"] == ["text_encompassing", "text_coefficient_sign_by_year"]


@pytest.mark.parametrize("kwargs", [{"t": 1.999}, {"t": None}, {"t": float("nan")}, {"t": float("inf")}, {"t": "3.0"},
                                    {"beta": 0.0}, {"beta": -0.01}, {"beta": None}, {"beta": float("nan")}])
def test_encompassing_gate_fails(kwargs):
    verdict = _verdict(**kwargs)
    assert verdict["verdict"] == "FAIL" and verdict["failed_gates"] == ["text_encompassing"]
    assert verdict["gates"]["text_coefficient_sign_by_year"]["pass"] is True


@pytest.mark.parametrize("kwargs", [{"y2023": 0.0}, {"y2024": 0.0}, {"y2023": -0.001}, {"y2024": -0.5}, {"y2023": None},
                                    {"y2024": float("nan")}])
def test_year_sign_gate_fails(kwargs):
    verdict = _verdict(**kwargs)
    assert verdict["verdict"] == "FAIL" and verdict["failed_gates"] == ["text_coefficient_sign_by_year"]
    assert verdict["gates"]["text_encompassing"]["pass"] is True


def test_year_sign_gate_fails_without_a_year():
    evaluation = _evaluation()
    del evaluation["gates"]["text_coefficient_by_year"]["2024"]
    verdict = c2.build_verdict(evaluation, {}, {}, {})
    assert verdict["verdict"] == "FAIL" and verdict["failed_gates"] == ["text_coefficient_sign_by_year"]
    assert verdict["gates"]["text_coefficient_sign_by_year"]["value"] == {"2023": 0.01, "2024": None}


def test_descriptive_errors_are_listed_and_cannot_change_the_verdict():
    evaluation = _evaluation(paired_ic={"s_full_minus_s_quant": {"error": "ValueError: boom"}, "other": {"weeks": 3}},
                             fit_errors={"g_text": {"error": "RuntimeError: no booster"}})
    verdict = c2.build_verdict(evaluation, {"s_full": {"error": "KeyError: x"}, "cost_per_side": 0.0005},
                               {"s_full": {"error": "KeyError: x"}}, {"quality": {"error": "TypeError: y"}, "extraction": None})
    assert verdict["verdict"] == "PASS" and verdict["failed_gates"] == []
    assert verdict["descriptive_errors"] == ["evaluation/paired_ic/s_full_minus_s_quant", "evaluation/fit_errors/g_text",
                                             "portfolio/s_full", "books/s_full", "reader/quality"]
    failed = c2.build_verdict(_evaluation(t=0.5, coefficients={"error": "ValueError: boom"}), {}, {}, {})
    assert failed["verdict"] == "FAIL" and failed["descriptive_errors"] == ["evaluation/coefficients"]


def test_planted_signal_passes_and_a_noise_draw_fails():
    planted = _gate_verdict(0.3)
    assert planted["verdict"] == "PASS" and planted["test_weeks"] == 104
    assert planted["gates"]["text_encompassing"]["value"]["nw_t"] > 4.0
    # One noise draw. A gate of t >= 2 passes a few noise draws in a hundred by construction (charter §5; the
    # draw of seed 0 is one of them), so this shows the failing branch on real statistics, not a rejection rate.
    noise = _gate_verdict(0.0, seed=1)
    assert noise["verdict"] == "FAIL" and "text_encompassing" in noise["failed_gates"]
    assert abs(noise["gates"]["text_encompassing"]["value"]["nw_t"]) < 2.0


# ---------------------------------------------------------------- evaluation tail
def test_finalize_returns_the_registered_outputs_in_json_form(monkeypatch):
    monkeypatch.setattr(model, "GBM_ROUNDS", 5)
    data = synth(0.3, weeks=110, n=20, seed=4)
    out = c2.finalize(*data, extraction={"note": "synthetic"}, n_placebo=5, n_boot=20)
    assert set(out) == set(run_script.OUTPUTS)
    assert json.loads(json.dumps(out, allow_nan=False)) == out                   # plain JSON types, no NaN
    verdict, evaluation = out["verdict.json"], out["evaluation.json"]
    assert verdict["descriptive_errors"] == [] and evaluation["fit_errors"] == {}
    assert verdict["verdict"] == "PASS" and verdict["test_weeks"] == 58
    assert evaluation["weeks"]["panel"] == 110 and evaluation["weeks"]["first_test"].startswith("2023-01-06")
    assert evaluation["weeks"]["last_test"].startswith("2024-02-09")
    assert evaluation["gates"]["text_coefficient_by_year"]["2023"]["weeks"] == 52
    assert evaluation["gates"]["text_coefficient_by_year"]["2024"]["weeks"] == 6
    assert len(evaluation["gate_weekly_coefficients"]) == 58
    forecasts = out["forecasts.json"]
    assert forecasts["columns"] == c2.OUTPUT_COLUMNS and len(forecasts["rows"]) == 110 * 20
    table = pd.DataFrame(forecasts["rows"], columns=forecasts["columns"])
    burn_in = table["date"] < "2023-01-06"
    assert table.loc[burn_in, [*c2.RIDGE_SCORES, *c2.GBM_SCORES]].isna().all().all()     # no forecast inside the burn-in
    assert table.loc[~burn_in, [*c2.RIDGE_SCORES, *c2.GBM_SCORES]].notna().all().all()
    assert table[list(c2.CROSS_FIT_SCORES)].notna().all().all()
    assert set(evaluation["ic_test_weeks"]) == {*c2.RIDGE_SCORES, *c2.GBM_SCORES, "p_quant"}
    assert set(evaluation["encompassing"]) == {f"{a}_vs_{b}" for a, b in c2.ENCOMPASSING}
    assert set(evaluation["paired_ic"]) == {f"{a}_minus_{b}" for a, b in c2.PAIRED}
    assert set(out["portfolio.json"]) == {*c2.BOOK_SCORES, "funding_coverage", "cost_per_side"}
    assert out["portfolio.json"]["funding_coverage"] == 1.0 and set(out["books.json"]) == set(c2.BOOK_SCORES)
    assert out["reader.json"]["extraction"] == {"note": "synthetic"}
    assert out["reader.json"]["quality"]["records"] == 21
    top, feats, _, fwd, _, quant, flags = data                                  # the gate values are those of the gate score alone
    panel = c2.assemble_panel(top, feats, fwd, quant, flags)
    panel[c2.GATE_SCORE], _ = model.walk_forward(panel, c2.TEXT)
    gates, _ = c2.gate_statistics(panel[panel[c2.GATE_SCORE].notna()])
    assert evaluation["gates"]["encompassing_text_vs_quant"] == pytest.approx(gates["encompassing_text_vs_quant"])


def test_a_failing_descriptive_fit_is_recorded_and_the_gates_stand(monkeypatch):
    def no_booster(X, y):
        raise RuntimeError("no booster")

    monkeypatch.setattr(model, "fit_gbm", no_booster)
    top, feats, records, fwd, funding, quant, flags = synth(0.3, weeks=110, n=20, seed=4)
    out = c2.finalize(top, feats, records, fwd, funding, quant, flags, n_placebo=5, n_boot=20)
    evaluation, verdict = out["evaluation.json"], out["verdict.json"]
    assert evaluation["fit_errors"] == dict.fromkeys(c2.GBM_SCORES, {"error": "RuntimeError: no booster"})
    assert {f"evaluation/fit_errors/{name}" for name in c2.GBM_SCORES} <= set(verdict["descriptive_errors"])
    panel = c2.assemble_panel(top, feats, fwd, quant, flags)
    panel[c2.GATE_SCORE], _ = model.walk_forward(panel, c2.TEXT)
    gates, _ = c2.gate_statistics(panel[panel[c2.GATE_SCORE].notna()])
    assert evaluation["gates"]["encompassing_text_vs_quant"] == pytest.approx(gates["encompassing_text_vs_quant"])
    assert verdict["verdict"] == "PASS" and verdict["failed_gates"] == []
    json.dumps(out, allow_nan=False)


# ---------------------------------------------------------------- extraction manifest
def _digest(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _manifest_and_experiment() -> tuple[dict, dict]:
    manifest = {"charter": {"path": "charter.md", "sha256": _digest("charter")}, "prompt_sha256": schema.prompt_sha256(),
                "inputs": {name: {"path": name, "sha256": _digest(name)} for name in ("items", "docs", "cards")},
                "records_file": {"path": "records", "sha256": _digest("records")},
                "cache": {"path": "calls", "sha256": _digest("calls")},
                "source_files": {"a.py": _digest("a"), "b.py": _digest("b")}}
    experiment = {"charter": {"path": "charter.md", "sha256": _digest("charter")},
                  "inputs": {name: {"path": name, "sha256": _digest(name)} for name in ("items", "docs", "cards", "records", "calls")},
                  "source_files": {"a.py": _digest("a"), "b.py": _digest("b"), "c.py": _digest("c")}}
    return manifest, experiment


def test_manifest_of_the_registered_extraction_is_accepted():
    run_script.check_manifest(*_manifest_and_experiment())


@pytest.mark.parametrize("where, key, message", [
    ("manifest", ("charter", "sha256"), "different charter text"),
    ("manifest", ("prompt_sha256",), "agent instructions differ"),
    ("experiment", ("inputs", "items", "sha256"), "items differs from the registered input"),
    ("experiment", ("inputs", "docs", "sha256"), "docs differs from the registered input"),
    ("experiment", ("inputs", "cards", "sha256"), "cards differs from the registered input"),
    ("manifest", ("records_file", "sha256"), "records differs from the registered input"),
    ("experiment", ("inputs", "calls", "sha256"), "calls differs from the registered input"),
    ("experiment", ("source_files", "a.py"), "a.py changed since the extraction"),
])
def test_manifest_of_another_extraction_is_refused(where, key, message):
    manifest, experiment = _manifest_and_experiment()
    node = manifest if where == "manifest" else experiment
    for part in key[:-1]:
        node = node[part]
    node[key[-1]] = _digest("something else")
    with pytest.raises(SystemExit, match=message):
        run_script.check_manifest(manifest, experiment)


def test_manifest_source_file_must_be_registered():
    manifest, experiment = _manifest_and_experiment()
    del experiment["source_files"]["b.py"]
    with pytest.raises(SystemExit, match="b.py changed since the extraction"):
        run_script.check_manifest(manifest, experiment)


def test_rehearsal_outcomes_are_seeded_noise_of_the_registered_shape():
    top, *_ = synth(0.0, weeks=20, n=10)
    fwd, funding = run_script.synthetic_outcomes(top)
    again, _ = run_script.synthetic_outcomes(top)
    pd.testing.assert_frame_equal(fwd, again)
    other, _ = run_script.synthetic_outcomes(top, seed=1)
    assert not np.allclose(other["fwd_ret"].to_numpy()[:50], fwd["fwd_ret"].to_numpy()[:50])
    assert list(fwd.columns) == ["date", "symbol", "fwd_ret", "delisted"] and not fwd["delisted"].any()
    assert 0 < len(top) - len(fwd) < 0.05 * len(top) and not fwd[["date", "symbol"]].duplicated().any()
    assert len(funding) == len(top) and (funding["funding_week"] == 1e-4).all() and (funding["n_settlements"] == 21).all()
    assert abs(fwd["fwd_ret"].mean()) < 0.02 and 0.06 < fwd["fwd_ret"].std() < 0.10


# ---------------------------------------------------------------- registered run on a synthetic checkout
RUN_SHAPE = {"weeks": 110, "n_syms": 20, "docs_per_week": 12}                    # 52 burn-in weeks, 52 weeks of 2023, 6 of 2024
RUN_INPUTS = {"items": rx.INPUTS["items"], "docs": rx.INPUTS["docs"], "cards": rx.INPUTS["cards"], "calls": rx.CACHE,
              "records": rx.RECORDS, "extraction_manifest": rx.MANIFEST, "quant_forecasts": "quant.parquet",
              "reid_flags": "flags.parquet", "klines_digest": "klines_digest.json", "funding_digest": "funding_digest.json"}


def _run_root(root: Path) -> dict:
    """A synthetic checkout in the state before the registered run: sources and charter committed, the
    extraction complete (stub client), kline and funding stores with an effect of the text features planted in
    the weekly returns, and a committed registration."""
    from tradingagents.research import runtime_hashes
    items, docs, cards = script_root(root, frozen=True, **RUN_SHAPE)
    manifest = extract(root, "--cost-cap", "5", client=FakeClient())
    records = pd.read_parquet(root / rx.RECORDS)
    top = c2.universe(cards)
    sets, _ = c2.reading(items, docs, top)
    feats = c2.text_features(items, sets, records, top)
    rng = np.random.default_rng(11)
    log_ret = 0.02 * rng.normal(size=len(feats)) + 0.05 * np.tanh(feats["tone_7d"]) + 0.03 * np.tanh(feats["tone_30d"])
    weekly = feats[["date", "symbol"]].assign(log_ret=log_ret.to_numpy())
    fridays = sorted(top["date"].unique())
    days = pd.date_range(fridays[0], fridays[-1] + WEEK, freq="D", tz="UTC")
    stamps = pd.date_range(fridays[0], fridays[-1] + 9 * pd.Timedelta(days=1), freq="8h", tz="UTC")
    for store in ("klines", "funding"):
        (root / store).mkdir()
    for sym, rows in weekly.groupby("symbol"):
        steps = rows.set_index("date")["log_ret"].reindex(fridays).to_numpy()
        level = 100.0 * np.exp(np.concatenate([[0.0], np.cumsum(steps)]))        # one level per week, flat inside the week
        pd.DataFrame({"close": np.repeat(level, 7)[:len(days)]}, index=days).to_parquet(root / "klines" / f"{sym}.parquet")
        pd.DataFrame({"fundingTime": stamps, "fundingRate": 1e-4}).to_parquet(root / "funding" / f"{sym}.parquet")
    for store in ("klines", "funding"):
        digest = {f"{store}/{p.name}": sha(p) for p in sorted((root / store).glob("*.parquet"))}
        (root / f"{store}_digest.json").write_text(json.dumps(digest))
    keys = top[["date", "symbol"]].reset_index(drop=True)
    keys.assign(pred_rank_pct=rng.uniform(size=len(keys))).to_parquet(root / "quant.parquet", index=False)
    flags = keys.iloc[::3].rename(columns={"date": "friday"})
    flags.assign(friday=flags["friday"].dt.strftime("%Y-%m-%d"), identified=rng.uniform(size=len(flags)) > 0.5,
                 month_within_6=False).to_parquet(root / "flags.parquet", index=False)
    spec = {"schema_version": 1, "program_id": "synthetic-c2",
            "families": {"fam": {"mechanism_id": "synthetic-mechanism", "attempt_budget": 3, "prior_attempts": 0,
                                 "history_reference": "synthetic"}},
            "datasets": {"sample": {"identity": "synthetic-sample", "history_reference": "synthetic", "exposures": []}},
            "experiments": {"c2": {
                "family": "fam", "parent": None, "question": "synthetic",
                "charter": {"path": "charter.md", "sha256": sha(root / "charter.md")},
                "stage": "development", "reuse": "exploratory", "selection": None,
                "source_files": manifest["source_files"], "runtime_hashes": runtime_hashes(),
                "windows": [{"dataset": "sample", "start": "2022-01-01T00:00:00Z", "end": "2024-03-01T00:00:00Z",
                             "availability": "existing"}],
                "inputs": {name: {"path": path, "sha256": sha(root / path), "dataset": "sample"} for name, path in RUN_INPUTS.items()},
                "cells": list(run_script.CELLS), "outputs": list(run_script.OUTPUTS)}}}
    (root / "registration.json").write_text(json.dumps(spec))
    commit(root, "synthetic registration", "registration.json")
    return {"manifest": manifest, "feats": feats, "weekly": weekly, "fridays": fridays}


def _run(root: Path, *extra: str) -> int:
    return run_script.main(["--registration", "registration.json", "--experiment", "c2", *extra], root=root)


def _output(root: Path, name: str):
    return json.loads((root / "research_runs" / "c2" / "outputs" / name).read_text())


def test_registered_run_checks_everything_before_the_claim_and_joins_outcomes_once(tmp_path, monkeypatch, capsys):
    from tradingagents.research.verify import verify_run
    ctx = _run_root(tmp_path)
    joins, real_join, real_finalize = [], run_script.forward_returns, c2.finalize

    def counted_join(symbols, fridays, **kwargs):
        joins.append(len(symbols) * len(fridays))
        return real_join(symbols, fridays, **kwargs)

    def quick_finalize(*args, **kwargs):
        kwargs.setdefault("n_placebo", 5)
        kwargs.setdefault("n_boot", 20)
        return real_finalize(*args, **kwargs)

    rehearsals, real_rehearse = [], run_script.rehearse

    def counted_rehearse(ctx):
        rehearsals.append(len(ctx["top"]))
        return real_rehearse(ctx)

    monkeypatch.setattr(run_script, "rehearse", counted_rehearse)
    monkeypatch.setattr(run_script, "forward_returns", counted_join)
    monkeypatch.setattr(c2, "finalize", quick_finalize)
    monkeypatch.setattr(run_script, "REHEARSAL_PLACEBO", 5)
    monkeypatch.setattr(run_script, "REHEARSAL_BOOT", 20)
    monkeypatch.setattr(model, "GBM_ROUNDS", 5)
    claimed = tmp_path / "research_runs"

    # a record edited after the extraction: found before the claim, no outcome read
    records_path = tmp_path / rx.RECORDS
    original = records_path.read_bytes()
    edited = pd.read_parquet(records_path)
    row = edited.index[edited["direction"].notna()][0]
    edited.loc[row, "direction"] = "favourable" if edited.loc[row, "direction"] != "favourable" else "unfavourable"
    edited.to_parquet(records_path, index=False)
    with pytest.raises(SystemExit, match="record table differs from the rebuild"):
        _run(tmp_path)
    records_path.write_bytes(original)
    assert not claimed.exists() and joins == [] and rehearsals == []

    # a kline file changed after the digest was taken: found before the claim
    kline = tmp_path / "klines" / "S03USDT.parquet"
    stored = kline.read_bytes()
    frame = pd.read_parquet(kline)
    frame.iloc[5, 0] *= 1.01
    frame.to_parquet(kline)
    with pytest.raises(CacheError, match="kline store: changed since freeze"):
        _run(tmp_path)
    kline.write_bytes(stored)
    assert not claimed.exists() and joins == [] and rehearsals == []

    # pre-flight alone: inputs verified, records rebuilt, rehearsal on synthetic outcomes, no claim
    assert _run(tmp_path, "--preflight-only") == 0
    assert "pre-flight passed" in capsys.readouterr().out
    assert not claimed.exists() and joins == [] and rehearsals == [2200]

    # the registered run
    assert _run(tmp_path) == 0
    directory = claimed / "c2"
    assert (directory / "claim.json").is_file() and (directory / "complete.json").is_file()
    assert not (directory / "failed.json").exists() and verify_run(directory)["status"] == "complete"
    assert sorted(p.name for p in (directory / "outputs").iterdir()) == sorted(run_script.OUTPUTS)
    assert joins == [20 * 110]                                                   # the single outcome join
    assert rehearsals == [2200, 2200]                                            # one rehearsal per process, before the claim
    verdict, evaluation = _output(tmp_path, "verdict.json"), _output(tmp_path, "evaluation.json")
    assert verdict["verdict"] == "PASS" and verdict["failed_gates"] == [] and verdict["descriptive_errors"] == []
    assert verdict["test_weeks"] == 58 and verdict["gates"]["text_encompassing"]["value"]["nw_t"] > 4.0
    assert evaluation["fit_errors"] == {} and evaluation["weeks"]["first_test"].startswith("2023-01-06")
    assert evaluation["panel"]["rows"] == 2200 and evaluation["panel"]["missing_fwd_ret"] == 0
    reader = _output(tmp_path, "reader.json")
    assert set(reader["extraction"]) == set(run_script.EXTRACTION_KEYS)
    assert reader["extraction"]["model"]["id"] == "fake/model" and reader["extraction"]["units"] == ctx["manifest"]["units"] == 880
    assert reader["quality"]["records"] == ctx["manifest"]["records"] == 1100
    assert _output(tmp_path, "portfolio.json")["funding_coverage"] == 1.0
    forecasts = _output(tmp_path, "forecasts.json")
    table = pd.DataFrame(forecasts["rows"], columns=forecasts["columns"])
    want = ctx["weekly"].assign(date=ctx["weekly"]["date"].dt.strftime("%Y-%m-%d")).set_index(["date", "symbol"])["log_ret"]
    got = table.assign(date=table["date"].str[:10]).set_index(["date", "symbol"])["fwd_ret"]
    assert np.allclose(np.log1p(got.to_numpy(dtype=float)), want.reindex(got.index).to_numpy())    # the planted weekly returns
    feats = ctx["feats"].assign(date=ctx["feats"]["date"].dt.strftime("%Y-%m-%d")).set_index(["date", "symbol"])
    assert np.allclose(table.assign(date=table["date"].str[:10]).set_index(["date", "symbol"])["tone_7d"].to_numpy(dtype=float),
                       feats["tone_7d"].reindex(got.index).to_numpy())

    # one registered run per registration
    monkeypatch.setattr(run_script, "rehearse", lambda ctx: rehearsals.append(0))    # the rehearsal is not the subject here
    with pytest.raises(ValueError, match="repeat run prohibited"):
        _run(tmp_path)
    assert joins == [20 * 110] and rehearsals == [2200, 2200, 0]
    assert verify_run(directory)["status"] == "complete"


# ---------------------------------------------------------------- registration
CLOSURE = """
import json, sys
from pathlib import Path
root = Path.cwd().resolve()
import reader_charter2_register, reader_charter2_run, reader_extract, llm_v2c0_client  # noqa: F401,E401
import tradingagents.reader.items  # noqa: F401
out = set()
for module in list(sys.modules.values()):
    name = getattr(module, "__file__", None)
    path = Path(name).resolve() if name else None
    if path and path.is_relative_to(root) and ".venv" not in path.parts:
        out.add(path.relative_to(root).as_posix())
print(json.dumps(sorted(out)))
"""


def test_registration_pins_every_project_file_the_run_and_the_extraction_import():
    import os
    import subprocess

    import reader_charter2_register as reg

    env = {**os.environ, "PYTHONPATH": os.pathsep.join([str(ROOT), str(ROOT / "scripts")])}
    done = subprocess.run([sys.executable, "-c", CLOSURE], cwd=ROOT, env=env, capture_output=True, text=True, check=True)
    imported = set(json.loads(done.stdout.strip().splitlines()[-1]))
    helper = {p for p in imported if p.startswith("tradingagents/research/")}       # pinned by the runtime hashes, if loaded
    assert "scripts/reader_charter2_run.py" in imported and "tradingagents/reader/charter2.py" in imported
    assert imported - helper <= set(reg.SOURCE_FILES), sorted(imported - helper - set(reg.SOURCE_FILES))
    assert len(set(reg.SOURCE_FILES)) == len(reg.SOURCE_FILES) and all((ROOT / p).is_file() for p in reg.SOURCE_FILES)
    assert set(rx.SOURCES) <= set(reg.SOURCE_FILES)                                 # the manifest is checked against these
    assert {"scripts/reader_items_build.py", "uv.lock"} <= set(reg.SOURCE_FILES)


def test_registration_names_the_inputs_the_run_reads():
    import reader_charter2_register as reg

    shared = ("items", "docs", "cards", "calls", "records", "extraction_manifest")
    assert set(reg.INPUTS) == set(RUN_INPUTS) and set(reg.SAME_AS_PARENT) < set(reg.INPUTS)
    assert {name: reg.INPUTS[name] for name in shared} == {name: RUN_INPUTS[name] for name in shared}
    assert reg.CHARTER == rx.CHARTER and reg.DRAFT_MARK == rx.DRAFT_MARK
    assert reg.FAMILY_KEY == "llm-multiagent-v2" and reg.PARENT == "llm-v2c1b-dev-run-20261112"


# ---------------------------------------------------------------- charter text
def test_charter_quotes_the_instructions_and_the_registered_constants():
    text = (ROOT / rx.CHARTER).read_text(encoding="utf-8")
    for quoted in (schema.INSTRUCTION, schema.REVIEWER, schema.ADJUDICATOR, schema.RETRY_LINE, schema.prompt_sha256()):
        assert quoted in text
    assert text.count(rx.DRAFT_MARK) == int(text.splitlines()[0].endswith(rx.DRAFT_MARK))     # in the title or nowhere
    provider_list = " and ".join(rx.PINS[rx.PIN][1])
    for stated in (f"`{rx.PINS[rx.PIN][0]}`", f"providers {provider_list} only", f"t at least {c2.GATE_TEXT_T}",
                   f"seed {rx.PILOT_SEED}", f"below {rx.PILOT_GROUNDING}", f"below {rx.PILOT_DIRECTION:.2f}",
                   f"{model.GBM_ROUNDS} rounds", f"penalty {RIDGE_ALPHA:g}", *c2.SCORES, *c2.TEXT):
        assert stated in text, stated
