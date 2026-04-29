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
        data_refresh.refresh_ohlcv(coin="BTC", cache_root=tmp_path)
        mock_f.assert_called_once()
        mock_app.assert_called_once()
