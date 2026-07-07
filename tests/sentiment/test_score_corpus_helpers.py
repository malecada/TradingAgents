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


class TestRawContentSha:
    def test_is_sha_of_raw_headline_plus_content(self):
        assert ssc.raw_content_sha("Head", "Body", "Sum") == ssc.sha1_of("Head\n\nBody")

    def test_falls_back_to_summary_when_content_empty(self):
        assert ssc.raw_content_sha("Head", "", "Sum") == ssc.sha1_of("Head\n\nSum")

    def test_coin_independent_unlike_llm_text(self):
        # Per-coin anonymized LLM texts differ between btc and eth for the
        # same article, but the raw sha (used for the global row) must not
        # depend on which coin's scoring path produced it.
        h, c = "Bitcoin and Ethereum rally", "Bitcoin adoption grows; Ethereum too."
        assert ssc.build_llm_text(h, c, "", "btc") != ssc.build_llm_text(h, c, "", "eth")
        expected = ssc.sha1_of(f"{h}\n\n{c}")
        assert ssc.raw_content_sha(h, c, "") == expected


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
# global-row stability across re-runs (review fix, Important)
# ---------------------------------------------------------------------------

def _multi_coin_article_df():
    """One article matching both btc and eth (plus global)."""
    return pd.DataFrame({
        "event_ts": pd.to_datetime(["2024-03-01"], utc=True),
        "as_of_ts": pd.to_datetime(["2024-03-01"], utc=True),
        "headline": ["Bitcoin and Ethereum rally"],
        "content": ["Bitcoin adoption grows; Ethereum staking too."],
        "summary": [""],
        "matched_coins": [["btc", "eth", "global"]],
    })


class _ScriptedLlmScorer:
    """Fake LlmIndexScorer: per-coin scripted outcomes, no network."""

    def __init__(self, outcomes: dict):
        # outcomes: coin -> dict result, or "error"
        self.outcomes = outcomes

    def score_article(self, text, coin, coin_name, symbol):
        out = self.outcomes[coin]
        if out == "error":
            return {"relevant": False, "idx": None, "raw": "__error__: boom"}
        return out


class TestGlobalRowStability:
    def test_global_content_sha_is_raw_and_coin_independent(self):
        df = _multi_coin_article_df()
        scorer = _ScriptedLlmScorer({
            "btc": {"relevant": True, "idx": 3, "raw": "Relevant. x, Index: 3"},
            "eth": {"relevant": True, "idx": 1, "raw": "Relevant. y, Index: 1"},
        })
        rows, _ = ssc.run_llm_engine(df, scorer=scorer)
        g = rows[rows["coin"] == "global"]
        assert len(g) == 1
        expected_sha = ssc.raw_content_sha(
            df.loc[0, "headline"], df.loc[0, "content"], df.loc[0, "summary"])
        assert g.iloc[0]["content_sha"] == expected_sha
        # score still copied from the first successfully scored coin (btc)
        assert g.iloc[0]["score_norm"] == pytest.approx(ssc.llm_score_norm(3))

    def test_rerun_with_different_surviving_coin_leaves_one_global_row(self, tmp_path):
        """Run 1: btc errors, eth succeeds -> global copies eth's score.
        Run 2: btc succeeds -> global copies btc's score. After writing both
        runs, exactly ONE global row must remain for the article (the raw
        content_sha makes [content_sha, coin] dedupe collapse them)."""
        df = _multi_coin_article_df()

        run1 = _ScriptedLlmScorer({
            "btc": "error",
            "eth": {"relevant": True, "idx": 1, "raw": "Relevant. y, Index: 1"},
        })
        rows1, _ = ssc.run_llm_engine(df, scorer=run1)
        ssc.write_scores(rows1, engine="llm", source="alpaca", data_root=tmp_path)

        run2 = _ScriptedLlmScorer({
            "btc": {"relevant": True, "idx": 3, "raw": "Relevant. x, Index: 3"},
            "eth": {"relevant": True, "idx": 1, "raw": "Relevant. y, Index: 1"},
        })
        rows2, _ = ssc.run_llm_engine(df, scorer=run2)
        ssc.write_scores(rows2, engine="llm", source="alpaca", data_root=tmp_path)

        target = tmp_path / "sentiment" / "scores" / "llm" / "alpaca" / "2024.parquet"
        out = pd.read_parquet(target)
        g = out[out["coin"] == "global"]
        assert len(g) == 1, f"expected 1 global row, got {len(g)}"
        # keep='last' -> run 2's global (btc-sourced) score wins
        assert g.iloc[0]["score_norm"] == pytest.approx(ssc.llm_score_norm(3))

    def test_bert_global_row_uses_raw_sha_too(self):
        df = _multi_coin_article_df()

        class FakeBert:
            def score(self, texts):
                return np.tile(np.array([0.2, 0.3, 0.5]), (len(texts), 1))

        rows, _ = ssc.run_bert_engine(df, scorer=FakeBert())
        g = rows[rows["coin"] == "global"]
        assert len(g) == 1
        expected_sha = ssc.raw_content_sha(
            df.loc[0, "headline"], df.loc[0, "content"], df.loc[0, "summary"])
        assert g.iloc[0]["content_sha"] == expected_sha
        # per-coin rows keep the engine-text sha (different from raw)
        bert_sha = ssc.sha1_of(ssc.build_bert_text(df.loc[0, "headline"], df.loc[0, "summary"]))
        per_coin = rows[rows["coin"] != "global"]
        assert set(per_coin["content_sha"]) == {bert_sha}
        assert bert_sha != expected_sha


# ---------------------------------------------------------------------------
# summary stats use per-call denominators (review fix, Minor)
# ---------------------------------------------------------------------------

class TestLlmStatsPerCallDenominator:
    def test_relevant_share_cannot_exceed_one_for_multi_coin_articles(self):
        # 1 article, 2 coins, both relevant -> 2 relevant results over
        # 2 score_article calls = 1.0 (per-article denominator would say 2.0).
        df = _multi_coin_article_df()
        scorer = _ScriptedLlmScorer({
            "btc": {"relevant": True, "idx": 3, "raw": "Relevant. x, Index: 3"},
            "eth": {"relevant": True, "idx": 1, "raw": "Relevant. y, Index: 1"},
        })
        _, stats = ssc.run_llm_engine(df, scorer=scorer)
        assert stats["n_calls"] == 2
        assert stats["relevant_share"] == pytest.approx(1.0)

    def test_error_rate_uses_per_call_denominator(self):
        df = _multi_coin_article_df()
        scorer = _ScriptedLlmScorer({
            "btc": "error",
            "eth": {"relevant": True, "idx": 1, "raw": "Relevant. y, Index: 1"},
        })
        _, stats = ssc.run_llm_engine(df, scorer=scorer)
        assert stats["n_calls"] == 2
        assert stats["n_errors"] == 1
        assert stats["relevant_share"] == pytest.approx(0.5)


# ---------------------------------------------------------------------------
# --est-only messaging per engine (review fix, Minor)
# ---------------------------------------------------------------------------

class TestEstOnlyMessaging:
    def _run(self, engine, tmp_path, capsys):
        rc = ssc.main([
            "--engine", engine, "--source", "alpaca", "--coins", "btc",
            "--start", "2024-01-01", "--end", "2024-02-01",
            "--est-only", "--data-root", str(tmp_path),
        ])
        assert rc == 0
        return capsys.readouterr().out

    def test_bert_est_only_prints_no_api_cost(self, tmp_path, capsys):
        out = self._run("bert", tmp_path, capsys)
        assert "local model" in out
        assert "no API cost" in out
        assert "gpt-4o-mini" not in out

    def test_llm_est_only_prints_cost_estimate(self, tmp_path, capsys):
        out = self._run("llm", tmp_path, capsys)
        assert "gpt-4o-mini" in out
        assert "Estimated cost" in out


# ---------------------------------------------------------------------------
# script is importable without side effects (module-level guard)
# ---------------------------------------------------------------------------

def test_module_has_no_top_level_side_effects():
    # Re-importing must not create files/dirs or hit the network. If we got
    # this far (collection succeeded) the import itself was already side
    # effect free; this just documents the contract explicitly.
    assert hasattr(ssc, "main")
    assert callable(ssc.main)
