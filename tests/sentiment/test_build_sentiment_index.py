"""Tests for scripts/build_sentiment_index.py's pure/IO helper `load_scores`.

Scope: cross-source concat + dedupe on [content_sha, coin]. No network.
Writes go to tmp_path only (data_root passed explicitly, never the real
project `data/` dir).
"""
from __future__ import annotations

import pandas as pd

from scripts import build_sentiment_index as bsi

SCORE_COLS = bsi.SCORE_COLS


def _row(event_ts, coin, score_norm, content_sha, engine="llm"):
    return {
        "event_ts": pd.Timestamp(event_ts, tz="UTC"),
        "as_of_ts": pd.Timestamp(event_ts, tz="UTC") + pd.Timedelta(hours=1),
        "coin": coin,
        "engine": engine,
        "score_norm": score_norm,
        "relevant": True,
        "content_sha": content_sha,
    }


def _write_shard(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows, columns=SCORE_COLS).to_parquet(path, index=False)


class TestLoadScores:
    def test_concatenates_both_sources(self, tmp_path):
        _write_shard(
            tmp_path / "sentiment" / "scores" / "llm" / "alpaca" / "2024.parquet",
            [_row("2024-01-01", "btc", 0.5, "sha-a1")],
        )
        _write_shard(
            tmp_path / "sentiment" / "scores" / "llm" / "hf_btc" / "2024.parquet",
            [_row("2024-01-02", "btc", -0.2, "sha-h1")],
        )
        out = bsi.load_scores("llm", ["alpaca", "hf_btc"], tmp_path)
        assert len(out) == 2
        assert set(out["content_sha"]) == {"sha-a1", "sha-h1"}

    def test_dedupes_overlapping_article_across_sources_keep_first(self, tmp_path):
        # Same (content_sha, coin) pair appears in both source shards — this
        # models the rare case of an article present in both the Alpaca and
        # HF BTC corpora. Alpaca is listed first in --sources order, so its
        # row must survive.
        _write_shard(
            tmp_path / "sentiment" / "scores" / "llm" / "alpaca" / "2024.parquet",
            [_row("2024-01-01", "btc", 0.9, "dup-sha")],
        )
        _write_shard(
            tmp_path / "sentiment" / "scores" / "llm" / "hf_btc" / "2024.parquet",
            [_row("2024-01-01", "btc", -0.9, "dup-sha")],
        )
        out = bsi.load_scores("llm", ["alpaca", "hf_btc"], tmp_path)
        assert len(out) == 1
        assert out["score_norm"].iloc[0] == 0.9

    def test_same_sha_different_coin_both_kept(self, tmp_path):
        # [content_sha, coin] is the dedupe key — the same article can
        # legitimately emit rows for two different coins (e.g. btc + global)
        # and both must survive.
        _write_shard(
            tmp_path / "sentiment" / "scores" / "llm" / "alpaca" / "2024.parquet",
            [
                _row("2024-01-01", "btc", 0.5, "shared-sha"),
                _row("2024-01-01", "global", 0.5, "shared-sha"),
            ],
        )
        out = bsi.load_scores("llm", ["alpaca"], tmp_path)
        assert len(out) == 2
        assert set(out["coin"]) == {"btc", "global"}

    def test_missing_source_shard_is_skipped_not_an_error(self, tmp_path):
        _write_shard(
            tmp_path / "sentiment" / "scores" / "llm" / "alpaca" / "2024.parquet",
            [_row("2024-01-01", "btc", 0.5, "sha-only")],
        )
        out = bsi.load_scores("llm", ["alpaca", "hf_btc"], tmp_path)
        assert len(out) == 1

    def test_no_shards_at_all_returns_empty_frame_with_schema(self, tmp_path):
        out = bsi.load_scores("llm", ["alpaca", "hf_btc"], tmp_path)
        assert out.empty
        assert list(out.columns) == SCORE_COLS

    def test_engines_are_isolated(self, tmp_path):
        _write_shard(
            tmp_path / "sentiment" / "scores" / "llm" / "alpaca" / "2024.parquet",
            [_row("2024-01-01", "btc", 0.5, "sha-llm")],
        )
        _write_shard(
            tmp_path / "sentiment" / "scores" / "bert" / "alpaca" / "2024.parquet",
            [_row("2024-01-01", "btc", 0.1, "sha-bert")],
        )
        out = bsi.load_scores("llm", ["alpaca", "hf_btc"], tmp_path)
        assert len(out) == 1
        assert out["content_sha"].iloc[0] == "sha-llm"


class TestMainImportSafety:
    def test_module_importable_without_side_effects(self):
        # Import already happened at module load time above; just assert
        # main() exists and is callable without having triggered any I/O.
        assert callable(bsi.main)
        assert callable(bsi.parse_args)
