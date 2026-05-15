"""Runner orchestrator tests — end-to-end dry-run with mocked boundaries."""
from pathlib import Path
from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def env_setup(monkeypatch, tmp_path):
    monkeypatch.setenv("LIVE_MODE", "false")
    monkeypatch.setenv("BINANCE_API_KEY", "k")
    monkeypatch.setenv("BINANCE_API_SECRET", "s")
    monkeypatch.setenv("BINANCE_BASE_URL", "https://testnet.binancefuture.com")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "t")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    monkeypatch.setenv("DATA_DIR", str(tmp_path / "data"))
    monkeypatch.setenv("LOG_DIR", str(tmp_path / "logs"))
    return tmp_path


def _seed_ohlcv_cache(data_dir: Path, seed: int) -> None:
    cache_dir = data_dir / "ohlcv_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2026-03-01", periods=60, freq="D")
    for coin, base_price in [("BTC", 60000.0), ("ETH", 3000.0), ("BNB", 400.0)]:
        prices = base_price * np.exp(np.cumsum(rng.normal(0, 0.02, 60)))
        df = pd.DataFrame({"date": dates, "close": prices})
        df.to_parquet(cache_dir / f"{coin}USDT_1d.parquet", index=False)


def test_dry_run_completes_full_pipeline(env_setup):
    """End-to-end dry run: no real orders, all steps execute, summary sent."""
    from tradingagents.execution.live import runner

    data_dir = env_setup / "data"
    _seed_ohlcv_cache(data_dir, seed=42)

    with patch("tradingagents.execution.live.data_refresh.refresh_coinmetrics"), \
         patch("tradingagents.execution.live.data_refresh.refresh_defillama"), \
         patch("tradingagents.execution.live.data_refresh.refresh_ohlcv"), \
         patch("tradingagents.execution.live.retrain.run_retrain_with_fallback") as mock_retrain, \
         patch("tradingagents.execution.live.predict.run_predict") as mock_pred, \
         patch("tradingagents.execution.live.runner.ExchangeClient") as mock_ex_cls, \
         patch("tradingagents.execution.live.notify.send_daily_summary") as mock_notify:
        mock_retrain.return_value = MagicMock(
            path=Path("/tmp/m.pkl"),
            sha="a" * 64,
            retrain_id="2026-05-12",
            routes=["bitcoin_78f", "ethereum_193f", "binancecoin_78f"],
            n_train_rows=100,
            train_window_start="2024-01-01",
            train_dir_acc=0.0,
        )
        mock_pred.return_value = {
            "bitcoin": {"ref_price": 60000.0, "pred_h7": 63000.0, "pred_h14": 66000.0},
            "ethereum": {"ref_price": 3000.0, "pred_h7": 2950.0, "pred_h14": 2900.0},
            "binancecoin": {"ref_price": 400.0, "pred_h7": 410.0, "pred_h14": 405.0},
        }
        mock_ex_cls.return_value.get_total_portfolio_value.return_value = 10000.0
        mock_ex_cls.return_value.get_usdt_balance.return_value = 10000.0
        mock_ex_cls.return_value.get_current_position.return_value = 0.0
        mock_ex_cls.return_value.get_ticker_price.return_value = 60000.0

        result = runner.run_cycle(cycle_id="2026-05-12", dry_run=True)

    assert result.status == "ok"
    assert result.n_executed == 0  # dry-run skips real orders
    mock_notify.assert_called_once()


def test_run_cycle_logs_to_journal(env_setup):
    """After a cycle, the journal DB has rows in cycles/sizing/shadow/snapshots."""
    from tradingagents.execution.live import runner
    import sqlite3

    data_dir = env_setup / "data"
    _seed_ohlcv_cache(data_dir, seed=7)

    with patch("tradingagents.execution.live.data_refresh.refresh_coinmetrics"), \
         patch("tradingagents.execution.live.data_refresh.refresh_defillama"), \
         patch("tradingagents.execution.live.data_refresh.refresh_ohlcv"), \
         patch("tradingagents.execution.live.retrain.run_retrain_with_fallback") as mock_retrain, \
         patch("tradingagents.execution.live.predict.run_predict") as mock_pred, \
         patch("tradingagents.execution.live.runner.ExchangeClient") as mock_ex_cls, \
         patch("tradingagents.execution.live.notify.send_daily_summary"):
        mock_retrain.return_value = MagicMock(
            path=Path("/tmp/m.pkl"),
            sha="b" * 64,
            retrain_id="2026-05-12",
            routes=["bitcoin_78f", "ethereum_193f", "binancecoin_78f"],
            n_train_rows=100,
            train_window_start="2024-01-01",
            train_dir_acc=0.0,
        )
        mock_pred.return_value = {
            "bitcoin": {"ref_price": 60000.0, "pred_h7": 63000.0, "pred_h14": 66000.0},
            "ethereum": {"ref_price": 3000.0, "pred_h7": 3050.0, "pred_h14": 3100.0},
            "binancecoin": {"ref_price": 400.0, "pred_h7": 410.0, "pred_h14": 420.0},
        }
        mock_ex_cls.return_value.get_total_portfolio_value.return_value = 10000.0
        mock_ex_cls.return_value.get_usdt_balance.return_value = 10000.0
        mock_ex_cls.return_value.get_current_position.return_value = 0.0
        mock_ex_cls.return_value.get_ticker_price.return_value = 60000.0

        runner.run_cycle(cycle_id="2026-05-12", dry_run=True)

    db = data_dir / "trade_journal.db"
    assert db.exists()
    conn = sqlite3.connect(db)
    cycles = conn.execute("SELECT cycle_id, status FROM cycles").fetchall()
    assert cycles == [("2026-05-12", "ok")]
    sizing_rows = conn.execute("SELECT COUNT(*) FROM sizing").fetchone()[0]
    assert sizing_rows == 3  # BTC, ETH, BNB
    shadow_rows = conn.execute("SELECT COUNT(*) FROM shadow_decisions").fetchone()[0]
    assert shadow_rows == 3
    snapshot_rows = conn.execute(
        "SELECT COUNT(*) FROM portfolio_snapshots"
    ).fetchone()[0]
    assert snapshot_rows >= 1
    conn.close()
