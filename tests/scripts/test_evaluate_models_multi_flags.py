"""Wiring tests for --add-sentiment / --sentiment-engine in evaluate_models_multi.py.

These do NOT run a real evaluation: build_pooled_dataset is monkeypatched to
capture the kwargs it receives, and data_transform is monkeypatched to a
pass-through so build_pooled_transformed can complete without needing real
market data.
"""
from __future__ import annotations

import sys

import pandas as pd
import pytest

from scripts import evaluate_models_multi as em


def _fake_pooled_raw():
    idx = pd.date_range("2024-01-01", periods=5, freq="D")
    return pd.DataFrame(
        {"prices": [1.0, 2.0, 3.0, 4.0, 5.0], "coin_id": ["bitcoin"] * 5},
        index=idx,
    )


def _fake_data_transform(sub, first_future, include_future_row=False, horizons=None):
    reframed = sub.reset_index().rename(columns={"index": "date"})
    return reframed, None


class TestParseArgsDefaults:
    def test_sentiment_flags_default_off(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["evaluate_models_multi.py"])
        args = em.parse_args()
        assert args.add_sentiment is False
        assert args.sentiment_engine == "llm"

    def test_sentiment_flags_can_be_set(self, monkeypatch):
        monkeypatch.setattr(
            sys, "argv",
            ["evaluate_models_multi.py", "--add-sentiment", "--sentiment-engine", "bert"],
        )
        args = em.parse_args()
        assert args.add_sentiment is True
        assert args.sentiment_engine == "bert"

    def test_sentiment_engine_rejects_invalid_choice(self, monkeypatch):
        monkeypatch.setattr(
            sys, "argv",
            ["evaluate_models_multi.py", "--sentiment-engine", "not-a-real-engine"],
        )
        with pytest.raises(SystemExit):
            em.parse_args()


class TestBuildPooledTransformedThreading:
    def test_default_off_matches_head_call(self, monkeypatch):
        """Absent flags -> build_pooled_dataset receives add_sentiment=False,
        sentiment_engine='llm' (the pre-existing defaults), i.e. byte-identical
        to calls made before this feature was wired in."""
        captured = {}

        def fake_build_pooled_dataset(**kwargs):
            captured.update(kwargs)
            return _fake_pooled_raw()

        monkeypatch.setattr(
            "tradingagents.models.model_utils.build_pooled_dataset",
            fake_build_pooled_dataset,
        )
        monkeypatch.setattr(
            "tradingagents.models.model_utils.data_transform",
            _fake_data_transform,
        )

        em.build_pooled_transformed(
            coins=["bitcoin"], horizons=[1], days=30, trade_date=None,
            add_technical=True, add_cross_asset=True, add_onchain=True,
        )

        assert captured["add_onchain_pit"] is False
        assert captured["add_sentiment"] is False
        assert captured["sentiment_engine"] == "llm"

    def test_sentiment_kwargs_are_threaded_through(self, monkeypatch):
        captured = {}

        def fake_build_pooled_dataset(**kwargs):
            captured.update(kwargs)
            return _fake_pooled_raw()

        monkeypatch.setattr(
            "tradingagents.models.model_utils.build_pooled_dataset",
            fake_build_pooled_dataset,
        )
        monkeypatch.setattr(
            "tradingagents.models.model_utils.data_transform",
            _fake_data_transform,
        )

        em.build_pooled_transformed(
            coins=["bitcoin"], horizons=[1], days=30, trade_date=None,
            add_technical=True, add_cross_asset=True, add_onchain=True,
            add_onchain_pit=False,
            add_sentiment=True, sentiment_engine="bert",
        )

        assert captured["add_sentiment"] is True
        assert captured["sentiment_engine"] == "bert"

    def test_main_passes_parsed_sentiment_args_through(self, monkeypatch, tmp_path):
        """End-to-end: CLI flags -> args -> build_pooled_transformed kwargs,
        mirroring the existing --onchain-pit wiring in main()."""
        captured = {}

        def fake_build_pooled_dataset(**kwargs):
            captured.update(kwargs)
            return _fake_pooled_raw()

        monkeypatch.setattr(
            "tradingagents.models.model_utils.build_pooled_dataset",
            fake_build_pooled_dataset,
        )
        monkeypatch.setattr(
            "tradingagents.models.model_utils.data_transform",
            _fake_data_transform,
        )
        monkeypatch.setattr(
            sys, "argv",
            [
                "evaluate_models_multi.py",
                "--coins", "bitcoin",
                "--horizons", "1",
                "--models", "lgb",
                "--add-sentiment", "--sentiment-engine", "bert",
                "--output-dir", str(tmp_path / "em_flags_test"),
            ],
        )

        def fake_model_run_pooled(pooled, horizon, min_train):
            return pd.DataFrame({"actual": [1.0], "prediction": [1.0]}), {
                "r2": 0.0, "mae": 0.0, "rmse": 0.0, "mape": 0.0,
                "directional_accuracy": 0.5,
            }

        import tradingagents.models.lgb_model as lgb_model
        monkeypatch.setattr(lgb_model, "model_run_pooled", fake_model_run_pooled)

        em.main()

        assert captured["add_sentiment"] is True
        assert captured["sentiment_engine"] == "bert"
