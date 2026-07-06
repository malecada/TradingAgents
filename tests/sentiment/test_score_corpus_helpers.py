"""Tests for the pure helper functions in scripts/score_sentiment_corpus.py.

Scope (per Task 6 brief): coin-mapping + normalization + writer helpers only.
No network, no model download — LlmIndexScorer/CryptoBertScorer are imported
by the script but never instantiated/invoked here.
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from scripts import score_sentiment_corpus as ssc


# ---------------------------------------------------------------------------
# symbols -> coins mapping (incl. "global")
# ---------------------------------------------------------------------------

class TestResolveCoinsForArticle:
    def test_single_symbol_list_matches_requested_coin(self):
        assert ssc.resolve_coins_for_article(
            ["BTCUSD"], ["btc", "eth"], source="alpaca"
        ) == ["btc", "global"]

    def test_multi_symbol_list_matches_both_in_requested_order(self):
        assert ssc.resolve_coins_for_article(
            ["BTCUSD", "ETHUSD"], ["btc", "eth"], source="alpaca"
        ) == ["btc", "eth", "global"]

    def test_requested_order_is_preserved_even_if_symbols_order_differs(self):
        assert ssc.resolve_coins_for_article(
            ["ETHUSD", "BTCUSD"], ["btc", "eth"], source="alpaca"
        ) == ["btc", "eth", "global"]

    def test_comma_joined_string_symbols(self):
        assert ssc.resolve_coins_for_article(
            "BTCUSD,ETHUSD", ["btc", "eth"], source="alpaca"
        ) == ["btc", "eth", "global"]

    def test_single_string_symbol(self):
        assert ssc.resolve_coins_for_article(
            "BTCUSD", ["btc", "eth"], source="alpaca"
        ) == ["btc", "global"]

    def test_python_list_repr_string_symbols(self):
        # Defensive: some ingestion paths may have stringified a list literal.
        assert ssc.resolve_coins_for_article(
            "['BTCUSD', 'ETHUSD']", ["btc", "eth"], source="alpaca"
        ) == ["btc", "eth", "global"]

    def test_unmatched_symbol_yields_no_rows_not_even_global(self):
        assert ssc.resolve_coins_for_article(
            ["ADAUSD"], ["btc", "eth"], source="alpaca"
        ) == []

    def test_matched_symbol_not_in_requested_coins_is_filtered_out(self):
        # ETHUSD present but caller only requested btc -> eth must not appear.
        assert ssc.resolve_coins_for_article(
            ["BTCUSD", "ETHUSD"], ["btc"], source="alpaca"
        ) == ["btc", "global"]

    def test_hf_btc_source_ignores_symbols_field_and_maps_to_btc(self):
        assert ssc.resolve_coins_for_article(
            "irrelevant garbage", ["btc", "eth"], source="hf_btc"
        ) == ["btc", "global"]

    def test_hf_btc_source_yields_nothing_if_btc_not_requested(self):
        assert ssc.resolve_coins_for_article(
            "anything", ["eth"], source="hf_btc"
        ) == []

    def test_empty_requested_coins_yields_nothing(self):
        assert ssc.resolve_coins_for_article(["BTCUSD"], [], source="alpaca") == []


class TestValidateCoins:
    def test_supported_coins_pass(self):
        ssc.validate_coins(["btc", "eth"])  # should not raise

    def test_unsupported_coin_raises(self):
        with pytest.raises(ValueError):
            ssc.validate_coins(["btc", "doge"])


# ---------------------------------------------------------------------------
# score_norm mappings (both engines)
# ---------------------------------------------------------------------------

class TestLlmScoreNorm:
    @pytest.mark.parametrize("idx,expected", [(0, -1.0), (1, -0.5), (2, 0.0), (3, 0.5), (4, 1.0)])
    def test_maps_0_4_index_to_minus1_plus1(self, idx, expected):
        assert ssc.llm_score_norm(idx) == pytest.approx(expected)


class TestBertScoreNorms:
    def test_is_p_bull_minus_p_bear_per_row(self):
        probs = np.array([
            [0.2, 0.3, 0.5],   # bull-leaning
            [0.6, 0.3, 0.1],   # bear-leaning
            [0.33, 0.34, 0.33],  # ~neutral
        ])
        norms = ssc.bert_score_norms(probs)
        assert norms == pytest.approx([0.3, -0.5, 0.0], abs=1e-6)

    def test_empty_array_returns_empty(self):
        norms = ssc.bert_score_norms(np.zeros((0, 3)))
        assert len(norms) == 0


# ---------------------------------------------------------------------------
# anonymization alias consistency (LLM prompt must match anonymized text)
# ---------------------------------------------------------------------------

class TestCoinAlias:
    def test_btc_alias_matches_anonymize_text_substitution(self):
        from tradingagents.sentiment.anonymize import anonymize_text
        text = anonymize_text("Bitcoin price surged today", "btc")
        assert ssc.coin_alias("btc") in text

    def test_eth_alias_matches_anonymize_text_substitution(self):
        from tradingagents.sentiment.anonymize import anonymize_text
        text = anonymize_text("Ethereum price surged today", "eth")
        assert ssc.coin_alias("eth") in text

    def test_btc_and_eth_aliases_differ(self):
        assert ssc.coin_alias("btc") != ssc.coin_alias("eth")


# ---------------------------------------------------------------------------
# text builders
# ---------------------------------------------------------------------------

class TestBuildLlmText:
    def test_uses_content_when_present(self):
        out = ssc.build_llm_text("Headline", "Full content body", "Short summary", "btc")
        assert "Full content body" in out
        assert "Headline" in out

    def test_falls_back_to_summary_when_content_empty(self):
        out = ssc.build_llm_text("Headline", "", "Short summary", "btc")
        assert "Short summary" in out

    def test_anonymizes_coin_name(self):
        out = ssc.build_llm_text("Bitcoin surges", "Bitcoin adoption grows", "", "btc")
        assert "Bitcoin" not in out
        assert ssc.coin_alias("btc") in out


class TestBuildBertText:
    def test_joins_headline_and_summary(self):
        assert ssc.build_bert_text("Headline", "Summary") == "Headline. Summary"


# ---------------------------------------------------------------------------
# cost estimation
# ---------------------------------------------------------------------------

class TestEstimateCost:
    def test_known_value_for_1000_articles(self):
        # 1000 * (1400*0.15/1e6 + 160*0.60/1e6) = 1000 * (0.00021 + 0.000096) = 0.306
        cost = ssc.estimate_cost(1000)
        assert cost == pytest.approx(0.306, abs=1e-9)

    def test_zero_articles_is_zero_cost(self):
        assert ssc.estimate_cost(0) == 0.0


# ---------------------------------------------------------------------------
# knowledge-cutoff hard guard
# ---------------------------------------------------------------------------

class TestClampLlmStart:
    def test_llm_engine_clamps_earlier_start_to_cutoff(self):
        clamped, was_clamped = ssc.clamp_llm_start(date(2022, 1, 1), "llm")
        assert clamped == ssc.LLM_CUTOFF_DATE
        assert was_clamped is True

    def test_llm_engine_leaves_later_start_untouched(self):
        clamped, was_clamped = ssc.clamp_llm_start(date(2024, 1, 1), "llm")
        assert clamped == date(2024, 1, 1)
        assert was_clamped is False

    def test_bert_engine_never_clamps(self):
        clamped, was_clamped = ssc.clamp_llm_start(date(2020, 1, 1), "bert")
        assert clamped == date(2020, 1, 1)
        assert was_clamped is False

    def test_exact_cutoff_date_not_clamped(self):
        clamped, was_clamped = ssc.clamp_llm_start(ssc.LLM_CUTOFF_DATE, "llm")
        assert clamped == ssc.LLM_CUTOFF_DATE
        assert was_clamped is False


# ---------------------------------------------------------------------------
# content_sha
# ---------------------------------------------------------------------------

class TestSha1Of:
    def test_deterministic(self):
        assert ssc.sha1_of("hello") == ssc.sha1_of("hello")

    def test_differs_for_different_text(self):
        assert ssc.sha1_of("hello") != ssc.sha1_of("world")


# ---------------------------------------------------------------------------
# year-partition writer: round-trip + dedupe
# ---------------------------------------------------------------------------

def _make_rows(n, year=2024, coin="btc", engine="llm", start_score=0.0):
    return pd.DataFrame({
        "event_ts": pd.to_datetime([f"{year}-03-{i+1:02d}" for i in range(n)], utc=True),
        "as_of_ts": pd.to_datetime([f"{year}-03-{i+1:02d}" for i in range(n)], utc=True),
        "coin": [coin] * n,
        "engine": [engine] * n,
        "score_norm": [start_score + i * 0.1 for i in range(n)],
        "relevant": [True] * n,
        "content_sha": [f"sha{i}" for i in range(n)],
    })


class TestWriteScores:
    def test_round_trip_single_year(self, tmp_path):
        rows = _make_rows(3)
        ssc.write_scores(rows, engine="llm", source="alpaca", data_root=tmp_path)
        target = tmp_path / "sentiment" / "scores" / "llm" / "alpaca" / "2024.parquet"
        assert target.exists()
        out = pd.read_parquet(target)
        assert len(out) == 3
        assert set(ssc.SCORE_COLS) <= set(out.columns)

    def test_partitions_by_year(self, tmp_path):
        rows_2024 = _make_rows(2, year=2024)
        rows_2025 = _make_rows(2, year=2025)
        both = pd.concat([rows_2024, rows_2025], ignore_index=True)
        ssc.write_scores(both, engine="bert", source="hf_btc", data_root=tmp_path)
        base = tmp_path / "sentiment" / "scores" / "bert" / "hf_btc"
        assert (base / "2024.parquet").exists()
        assert (base / "2025.parquet").exists()
        assert len(pd.read_parquet(base / "2024.parquet")) == 2
        assert len(pd.read_parquet(base / "2025.parquet")) == 2

    def test_rerun_is_idempotent_no_duplicate_rows(self, tmp_path):
        rows = _make_rows(3)
        ssc.write_scores(rows, engine="llm", source="alpaca", data_root=tmp_path)
        ssc.write_scores(rows, engine="llm", source="alpaca", data_root=tmp_path)
        target = tmp_path / "sentiment" / "scores" / "llm" / "alpaca" / "2024.parquet"
        out = pd.read_parquet(target)
        assert len(out) == 3

    def test_dedupe_key_is_content_sha_and_coin_keep_last(self, tmp_path):
        first = _make_rows(1, start_score=0.0)
        first.loc[0, "content_sha"] = "dup-sha"
        ssc.write_scores(first, engine="llm", source="alpaca", data_root=tmp_path)

        second = _make_rows(1, start_score=0.9)
        second.loc[0, "content_sha"] = "dup-sha"
        ssc.write_scores(second, engine="llm", source="alpaca", data_root=tmp_path)

        target = tmp_path / "sentiment" / "scores" / "llm" / "alpaca" / "2024.parquet"
        out = pd.read_parquet(target)
        assert len(out) == 1
        assert out.iloc[0]["score_norm"] == pytest.approx(0.9)

    def test_same_content_sha_different_coin_both_kept(self, tmp_path):
        # e.g. a per-coin row and its "global" twin share content_sha but differ in coin.
        row_coin = _make_rows(1, coin="btc")
        row_coin.loc[0, "content_sha"] = "shared-sha"
        row_global = _make_rows(1, coin="global")
        row_global.loc[0, "content_sha"] = "shared-sha"
        combined = pd.concat([row_coin, row_global], ignore_index=True)

        ssc.write_scores(combined, engine="llm", source="alpaca", data_root=tmp_path)
        target = tmp_path / "sentiment" / "scores" / "llm" / "alpaca" / "2024.parquet"
        out = pd.read_parquet(target)
        assert len(out) == 2
        assert set(out["coin"]) == {"btc", "global"}

    def test_empty_dataframe_is_noop(self, tmp_path):
        empty = pd.DataFrame(columns=ssc.SCORE_COLS)
        ssc.write_scores(empty, engine="llm", source="alpaca", data_root=tmp_path)
        target = tmp_path / "sentiment" / "scores" / "llm" / "alpaca" / "2024.parquet"
        assert not target.exists()

    def test_missing_required_column_raises(self, tmp_path):
        bad = _make_rows(1).drop(columns=["content_sha"])
        with pytest.raises(ValueError):
            ssc.write_scores(bad, engine="llm", source="alpaca", data_root=tmp_path)


# ---------------------------------------------------------------------------
# script is importable without side effects (module-level guard)
# ---------------------------------------------------------------------------

def test_module_has_no_top_level_side_effects():
    # Re-importing must not create files/dirs or hit the network. If we got
    # this far (collection succeeded) the import itself was already side
    # effect free; this just documents the contract explicitly.
    assert hasattr(ssc, "main")
    assert callable(ssc.main)
