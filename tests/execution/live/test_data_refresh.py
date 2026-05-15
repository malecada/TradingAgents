from unittest.mock import patch, MagicMock

import pandas as pd
import pytest


@pytest.fixture
def fake_cm_df():
    return pd.DataFrame({
        "coin": ["BTC"], "metric": ["MVRV"], "valid_from": ["2026-05-12"],
        "value": [1.5],
    })


@pytest.fixture
def fake_defillama_df():
    return pd.DataFrame({
        "coin": ["BTC"], "metric": ["TVL"], "valid_from": ["2026-05-12"],
        "value": [50e9],
    })


def test_refresh_coinmetrics_calls_fetch_and_upsert(tmp_path, fake_cm_df):
    from tradingagents.execution.live import data_refresh

    with patch.object(data_refresh, "fetch_coinmetrics_incremental",
                      return_value=fake_cm_df) as mock_fetch, \
         patch.object(data_refresh, "upsert_onchain_rows") as mock_upsert:
        data_refresh.refresh_coinmetrics(coins=["BTC"], store_root=tmp_path)
        mock_fetch.assert_called_once()
        mock_upsert.assert_called_once()
        df_arg, root_arg = mock_upsert.call_args.args
        assert root_arg == tmp_path
        assert "MVRV" in df_arg["metric"].values


def test_refresh_handles_empty_response(tmp_path):
    from tradingagents.execution.live import data_refresh

    empty = pd.DataFrame(columns=["coin", "metric", "valid_from", "value"])
    with patch.object(data_refresh, "fetch_coinmetrics_incremental",
                      return_value=empty), \
         patch.object(data_refresh, "upsert_onchain_rows") as mock_upsert:
        data_refresh.refresh_coinmetrics(coins=["BTC"], store_root=tmp_path)
        mock_upsert.assert_not_called()


def test_refresh_defillama_uses_correct_args(tmp_path, fake_defillama_df):
    from tradingagents.execution.live import data_refresh

    with patch.object(data_refresh, "fetch_defillama_incremental",
                      return_value=fake_defillama_df), \
         patch.object(data_refresh, "upsert_onchain_rows") as mock_upsert:
        data_refresh.refresh_defillama(coins=["BTC", "ETH"], store_root=tmp_path)
        mock_upsert.assert_called_once()


def test_refresh_binance_ohlcv_appends_yesterday(tmp_path):
    from tradingagents.execution.live import data_refresh

    fake_bar = pd.DataFrame({
        "date": ["2026-05-11"], "open": [60000], "high": [61000],
        "low": [59000], "close": [60500], "volume": [1000],
    })
    with patch.object(data_refresh, "fetch_binance_daily",
                      return_value=fake_bar) as mock_f, \
         patch.object(data_refresh, "append_ohlcv") as mock_app:
        data_refresh.refresh_ohlcv(coin="bitcoin", cache_root=tmp_path)
        mock_f.assert_called_once()
        mock_app.assert_called_once()
        # Cold-start: no cache file → fetches the full min_history window.
        kwargs = mock_f.call_args.kwargs
        assert kwargs.get("symbol") == "BTCUSDT"


def test_refresh_binance_ohlcv_incremental_when_cache_warm(tmp_path):
    """When cache has >= min_history rows, refresh fetches only 2 days."""
    from tradingagents.execution.live import data_refresh

    # Seed a warm cache with 100 rows (>= default min_history=60).
    cache_file = tmp_path / "BTCUSDT_1d.parquet"
    seed = pd.DataFrame({
        "date": pd.date_range("2026-01-01", periods=100, freq="D"),
        "open": [60000] * 100, "high": [61000] * 100,
        "low": [59000] * 100, "close": [60500] * 100, "volume": [1000] * 100,
    })
    seed.to_parquet(cache_file, index=False)

    fake_bar = pd.DataFrame({
        "date": ["2026-05-11"], "open": [60000], "high": [61000],
        "low": [59000], "close": [60500], "volume": [1000],
    })
    with patch.object(data_refresh, "fetch_binance_daily",
                      return_value=fake_bar) as mock_f, \
         patch.object(data_refresh, "append_ohlcv") as mock_app:
        data_refresh.refresh_ohlcv(coin="bitcoin", cache_root=tmp_path)
        mock_f.assert_called_once()
        mock_app.assert_called_once()
        kwargs = mock_f.call_args.kwargs
        assert kwargs.get("days") == 2
        assert kwargs.get("symbol") == "BTCUSDT"


def test_refresh_coinglass_idempotent(monkeypatch, tmp_path):
    """Two calls in one cycle produce identical parquet (no row duplication)."""
    import pandas as pd
    from tradingagents.execution.live import data_refresh

    # Stub the underlying Coinglass fetch helpers — return a small known frame.
    calls = []

    def fake_fetch_oi_agg(symbol, key):
        calls.append(("oi", symbol))
        idx = pd.to_datetime(["2026-05-13", "2026-05-14"], utc=True)
        return pd.DataFrame({
            "oi_open": [1.0, 2.0], "oi_high": [1.0, 2.0],
            "oi_low": [1.0, 2.0], "oi_close": [1.0, 2.0],
        }, index=idx)

    monkeypatch.setattr(
        "scripts.fetch_coinglass_history.fetch_oi_agg", fake_fetch_oi_agg
    )
    # Stub other endpoints similarly (return empty DataFrames so the test stays focused)
    for fn in ("fetch_liq_agg", "fetch_ls_ratio", "fetch_taker_vol", "fetch_funding_weighted"):
        monkeypatch.setattr(f"scripts.fetch_coinglass_history.{fn}",
                             lambda *a, **k: pd.DataFrame())

    deriv_dir = tmp_path / "derivatives"
    deriv_dir.mkdir()
    raw_dir = tmp_path / "derivatives_raw"
    raw_dir.mkdir()

    data_refresh.refresh_coinglass(
        coins=["bitcoin"], derivatives_dir=deriv_dir, raw_dir=raw_dir,
        api_key="test", structured_log=None,
    )
    out1 = pd.read_parquet(deriv_dir / "bitcoin.parquet").copy()
    data_refresh.refresh_coinglass(
        coins=["bitcoin"], derivatives_dir=deriv_dir, raw_dir=raw_dir,
        api_key="test", structured_log=None,
    )
    out2 = pd.read_parquet(deriv_dir / "bitcoin.parquet")
    pd.testing.assert_frame_equal(out1, out2)


def test_refresh_coinglass_raises_on_missing_key(tmp_path):
    from tradingagents.execution.live import data_refresh
    with pytest.raises(RuntimeError, match="COINGLASS_API_KEY"):
        data_refresh.refresh_coinglass(
            coins=["bitcoin"], derivatives_dir=tmp_path / "d", raw_dir=tmp_path / "r",
            api_key="", structured_log=None,
        )
