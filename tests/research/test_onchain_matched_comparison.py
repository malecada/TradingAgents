"""Invented daily panels only; no external files, network, or empirical outcomes."""
import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


PATH = Path(__file__).resolve().parents[2] / "research/onchain-graph-2026-09-16/comparison/model.py"
SPEC = importlib.util.spec_from_file_location("matched_comparison_model", PATH)
model = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(model)
FEATURES = {"M0": ["market"], "M1": ["market", "count"], "M2": ["market", "count", "motif"]}


def panel(n=100):
    days = pd.date_range("2001-01-01", periods=n, tz="UTC")
    frame = pd.DataFrame(dict(decision_at=days, label_start=days,
                              label_end=days+pd.Timedelta(days=1), y=np.arange(n) % 2))
    for i, name in enumerate(FEATURES["M2"]):
        frame[name] = np.sin(np.arange(n)+i)
        frame[name+"__available_at"] = days
    return frame


def test_future_feature_rejected_even_if_other_feature_missing():
    frame = panel()
    frame.loc[4, "market"] = np.nan
    frame.loc[4, "motif__available_at"] += pd.Timedelta(seconds=1)
    _, admission = model.validate_panel(frame, FEATURES)
    assert not admission.loc[4, "included"]
    assert "late:motif" in admission.loc[4, "exclusion_reasons"]


def test_common_mask_retains_reasons_and_does_not_mutate():
    frame = panel()
    frame.loc[2, "count"] = np.nan
    frame.loc[3, "motif"] = np.inf
    frame.loc[4, "market__available_at"] = pd.NaT
    _, admission = model.validate_panel(frame, FEATURES)
    assert admission.included.sum() == 97
    assert admission.loc[2, "exclusion_reasons"] == ("missing:count",)
    assert admission.loc[3, "exclusion_reasons"] == ("missing:motif",)
    assert np.isnan(frame.loc[2, "count"])


def test_known_metrics_clipping_and_absent_class():
    metrics = model.binary_metrics([0, 1], [.25, .75])
    assert metrics["accuracy"] == metrics["balanced_accuracy"] == 1
    assert metrics["brier"] == .0625
    assert metrics["log_loss"] == pytest.approx(-np.log(.75))
    assert np.isfinite(model.binary_metrics([1, 0], [0, 1])["log_loss"])
    assert model.binary_metrics([0], [.5])["balanced_accuracy"] is None
    with pytest.raises(ValueError):
        model.binary_metrics([0], [1.1])


def test_training_cutoff_shared_rows_and_fixed_parameters(monkeypatch):
    frame = panel()
    frame.loc[9, "label_end"] = frame.decision_at.iloc[85]
    frame.loc[82, "motif"] = np.nan
    calls = []

    class Spy:
        def __init__(self, **params):
            self.params = params
            self.classes_ = [0, 1]

        def fit(self, x, y):
            calls.append((self.params, x.index.tolist(), None))

        def predict_proba(self, x):
            calls[-1] = (*calls[-1][:2], x.index.tolist())
            return np.tile([.4, .6], (len(x), 1))

    monkeypatch.setattr(model, "LGBMClassifier", Spy)
    folds = [{"id": "a", "start": frame.decision_at.iloc[80], "end": frame.decision_at.iloc[90]},
             {"id": "b", "start": frame.decision_at.iloc[90], "end": frame.label_end.iloc[-1]}]
    result = model.run_comparison(frame, FEATURES, folds, purge_gap="2D")
    assert len(calls) == 6
    assert all(c[0] == model.MODEL_PARAMS for c in calls)
    assert calls[0] == calls[1] == calls[2]
    assert calls[3] == calls[4] == calls[5]
    assert 9 not in calls[0][1] and max(calls[0][1]) == 77
    assert 9 in calls[3][1] and max(calls[3][1]) == 87
    assert 82 not in calls[0][2] and len(result["predictions"]) == 19
    assert result["folds"].test_candidates.tolist() == [10, 10]
    assert result["folds"].test_included.tolist() == [9, 10]


def test_real_fixed_learner_synthetic_smoke():
    frame = panel()
    result = model.run_comparison(frame, FEATURES, [dict(id="a", start=frame.decision_at.iloc[80], end=frame.label_end.iloc[-1])])
    assert len(result["predictions"]) == 20
    for name in FEATURES:
        assert result["predictions"][name+"_probability"].between(0, 1).all()


def test_identity_bootstrap_and_determinism():
    predictions = panel(20).assign(fold="a", M0_probability=.4, M1_probability=.4, M2_probability=.4)
    result = model.paired_loss_summary(predictions, resamples=30)
    assert all(s == {"mean": 0, "ci95": [0, 0]} for s in result["summaries"].values())
    predictions["M2_probability"] = .7
    first = model.paired_loss_summary(predictions, resamples=40)
    second = model.paired_loss_summary(predictions, resamples=40)
    assert first["summaries"] == second["summaries"]
    assert first["summaries"]["M2-M1:brier"]["mean"] == pytest.approx(.03)


def test_bootstrap_rejects_missing_days_and_short_samples():
    predictions = panel(20).assign(fold="a", M0_probability=.4, M1_probability=.4, M2_probability=.7)
    with pytest.raises(ValueError, match="uninterrupted"):
        model.paired_loss_summary(predictions.drop(index=5), resamples=10)
    with pytest.raises(ValueError, match="full block"):
        model.paired_loss_summary(predictions.iloc[:10], resamples=10)


def test_bootstrap_matches_independent_small_block_enumeration():
    predictions = panel(4).assign(fold="a", M0_probability=.5, M1_probability=[.1, .3, .6, .9], M2_probability=.5)
    # Enumerate all possible contiguous two-day blocks independently; replay
    # the declared seed solely to verify the resampling distribution arithmetic.
    differences = np.array([.01-.25, .49-.25, .36-.25, .01-.25])
    blocks = [[0, 1], [1, 2], [2, 3]]
    rng = np.random.default_rng(11)
    means = []
    for _ in range(30):
        sample = blocks[int(rng.integers(3))] + blocks[int(rng.integers(3))]
        means.append(sum(differences[i] for i in sample)/4)
    result = model.paired_loss_summary(predictions, block_days=2, resamples=30, seed=11)
    assert result["summaries"]["M1-M0:brier"]["ci95"] == pytest.approx(np.quantile(means, [.025, .975]))


def test_learner_failure_propagates(monkeypatch):
    class Broken:
        def __init__(self, **params):
            pass

        def fit(self, x, y):
            raise RuntimeError("synthetic fitting failure")

    monkeypatch.setattr(model, "LGBMClassifier", Broken)
    with pytest.raises(RuntimeError, match="synthetic fitting failure"):
        model.run_comparison(panel(), FEATURES, [dict(id="a", start="2001-03-01", end="2001-04-01")])


@pytest.mark.parametrize("mutation", ["duplicate", "label", "order", "target"])
def test_malformed_panel_fails(mutation):
    frame = panel()
    if mutation == "duplicate":
        frame.loc[1, "decision_at"] = frame.loc[0, "decision_at"]
    elif mutation == "label":
        frame.loc[0, "label_start"] -= pd.Timedelta(seconds=1)
    elif mutation == "order":
        frame = frame.iloc[::-1]
    else:
        frame.loc[0, "y"] = 2
    with pytest.raises(ValueError):
        model.validate_panel(frame, FEATURES)


def test_failed_fold_is_not_silently_skipped():
    frame = panel()
    frame["y"] = 1
    with pytest.raises(ValueError, match="both training classes"):
        model.run_comparison(frame, FEATURES, [dict(id="a", start="2001-03-01", end="2001-04-01")])


def protocol_panel():
    config = json.loads(PATH.with_name("config.json").read_text())
    days = pd.date_range("2022-01-01", "2024-12-31", tz="UTC")
    frame = pd.DataFrame(dict(decision_at=days, label_start=days, label_end=days+pd.Timedelta(days=1), y=np.arange(len(days)) % 2))
    for feature in config["feature_sets"]["M2"]:
        frame[feature] = .2
        frame[feature+"__available_at"] = days
    return frame


def test_protocol_wrapper_freezes_sample_purge_and_complete_inference(monkeypatch):
    fitted = []

    class Fixed:
        def __init__(self, **params):
            self.classes_ = [0, 1]

        def fit(self, x, y):
            fitted.append(x.index.tolist())

        def predict_proba(self, x):
            return np.tile([.5, .5], (len(x), 1))

    monkeypatch.setattr(model, "LGBMClassifier", Fixed)
    result = model.evaluate(protocol_panel())
    assert len(result["predictions"]) == 366
    assert len(result["attempts"]) == 12
    assert len(fitted) == 36
    assert result["admission"].decision_at.min() == pd.Timestamp("2022-01-09T00:00Z")
    assert result["counts"].train_label_cutoff.iloc[0] == pd.Timestamp("2023-12-31T00:00Z")
    assert result["inference"]["status"] == "available"
    assert result["screening"] == dict(status="available", supported=False, negative_months=0)
    assert result["pooled_metrics"]["M0"]["n"] == 366
    # A missing test observation preserves descriptive results and denies the
    # entire registered primary inference, even though generic bootstrap could
    # otherwise run on smaller uninterrupted pieces.
    frame = protocol_panel()
    frame.loc[frame.decision_at == "2024-06-15", "return_1"] = np.nan
    result = model.evaluate(frame)
    assert len(result["predictions"]) == 365
    assert result["inference"]["status"] == "unavailable"
    assert result["inference"]["missing_dates"] == [pd.Timestamp("2024-06-15T00:00Z")]
    assert result["screening"]["supported"] is None


def test_protocol_wrapper_retains_failed_attempts(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("synthetic fold failure")

    monkeypatch.setattr(model, "run_comparison", fail)
    result = model.evaluate(protocol_panel())
    assert len(result["attempts"]) == 12
    assert (result["attempts"].status == "failed").all()
    assert result["predictions"].empty
    assert result["inference"]["status"] == "unavailable"
    assert len(result["inference"]["missing_dates"]) == 366


def test_protocol_rejects_target_interval_mutation_and_retains_absent_training_days(monkeypatch):
    frame = protocol_panel()
    frame.loc[20, "label_end"] += pd.Timedelta(days=1)
    with pytest.raises(ValueError, match="exact one-day"):
        model.evaluate(frame)

    def fail(*args, **kwargs):
        raise RuntimeError("fixture avoids fitting")

    monkeypatch.setattr(model, "run_comparison", fail)
    frame = protocol_panel().drop(index=20)
    result = model.evaluate(frame)
    missing = result["admission"].loc[result["admission"].decision_at == "2022-01-21"].iloc[0]
    assert not missing.included
    assert "missing:y" in missing.exclusion_reasons
