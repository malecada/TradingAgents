import pandas as pd
from tradingagents.dataflows import sentiment_index_store as sis


def _rows():
    return pd.DataFrame({
        "event_ts": pd.to_datetime(["2024-01-01", "2024-01-02"], utc=True),
        "as_of_ts": pd.to_datetime(["2024-01-01 01:00", "2024-01-02 01:00"], utc=True),
        "coin": ["btc", "btc"],
        "metric": ["snt_idx_mean", "snt_idx_mean"],
        "value": [0.25, -0.5],
        "source": ["sentiment_index", "sentiment_index"],
        "status": ["final", "final"],
    })


def test_upsert_and_load_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(sis, "BASE_ROOT", tmp_path)
    sis.upsert_index_rows(_rows(), engine="llm")
    out = sis.load_index("llm", coins=["btc"], start="2024-01-01", end="2024-01-31")
    assert len(out) == 2 and set(out.metric) == {"snt_idx_mean"}


def test_engines_are_isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(sis, "BASE_ROOT", tmp_path)
    sis.upsert_index_rows(_rows(), engine="llm")
    assert sis.load_index("bert", coins=["btc"], start="2024-01-01", end="2024-01-31").empty
