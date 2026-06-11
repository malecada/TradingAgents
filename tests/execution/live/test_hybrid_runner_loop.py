# tests/execution/live/test_hybrid_runner_loop.py
import sqlite3
import numpy as np
import pandas as pd
import pytest
from tradingagents.execution.live import hybrid_runner
from tradingagents.execution.live.journal import Journal


class FakeExchange:
    def __init__(self):
        self.orders = []
        self.stops = []

    def set_leverage(self, *a, **k):
        pass

    def get_total_portfolio_value(self):
        return 10000.0

    def get_usdt_balance(self):
        return 10000.0

    def get_current_position(self, symbol):
        return 0.0

    def round_quantity(self, symbol, q):
        return round(q, 3)

    def min_notional(self, symbol):
        return 5.0

    def get_ticker_price(self, symbol):
        return 65000.0

    def place_market_order(self, symbol, side, qty, reduce_only=False):
        self.orders.append((symbol, side, qty))
        return {"orderId": 1, "status": "FILLED"}

    def cancel_all_orders(self, symbol):
        return []

    def list_open_stops(self, symbol):
        return []

    def place_stop_loss(self, symbol, qty, stop_price, stop_side):
        stop_id = len(self.stops) + 100
        self.stops.append((symbol, qty, stop_price, stop_side))
        return {"orderId": stop_id}

    def cancel_order(self, symbol, order_id):
        pass


class StubGraph:
    """Returns a fixed modulator output: mult=1.4, eff_w=0.5.
    Importantly, position=-999.0 to assert it is DISCARDED."""

    def propagate_with_modulator(self, coin, date):
        mp = {
            "coin": coin,
            "llm_multiplier": 1.4,
            "effective_weight": 0.5,
            "position": -999.0,   # must be discarded; composition uses base×formula
            "regime": "bull",
            "llm_uncertainty": 0.1,
        }
        return ({}, mp, {"coin": coin, "direction": "long", "magnitude": 0.2}, "ok")


def _seed_quant_db(db_path: str, cycle_id: str) -> None:
    j = Journal(db_path)
    j.log_cycle_start(cycle_id, git_sha="x")
    preds_df = pd.DataFrame([
        {"coin": "bitcoin", "horizon": 7,  "prediction": 0.03,
         "ref_price": 65000.0, "bundle_route": "bitcoin_78f"},
        {"coin": "bitcoin", "horizon": 14, "prediction": 0.05,
         "ref_price": 65000.0, "bundle_route": "bitcoin_78f"},
    ])
    j.record_predictions(cycle_id=cycle_id, preds_df=preds_df)
    j.close()


def _seed_ohlcv_cache(hybrid_dir, symbol: str) -> None:
    """Write 60-bar parquet to <hybrid_dir>/ohlcv_cache/<symbol>_1d.parquet
    with lowercase columns: date, open, high, low, close, volume.
    60 bars ensures vol_lookback=20 + trend_sma=30 have sufficient history.
    """
    cache_dir = hybrid_dir / "ohlcv_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    idx = pd.date_range("2026-03-01", periods=60, freq="D")
    px = pd.Series(100.0 + np.arange(60) * 0.5)
    df = pd.DataFrame({
        "date": idx,
        "open": px,
        "high": px * 1.01,
        "low": px * 0.99,
        "close": px,
        "volume": 1000.0,
    })
    df.to_parquet(cache_dir / f"{symbol}_1d.parquet", index=False)


def test_loop_composes_and_executes_on_hybrid_only(tmp_path, monkeypatch):
    quant_dir = tmp_path / "data"
    quant_dir.mkdir()
    hybrid_dir = tmp_path / "data-hybrid"

    _seed_quant_db(str(quant_dir / "trade_journal.db"), "2026-06-11")

    monkeypatch.setenv("HYBRID_BINANCE_API_KEY", "k")
    monkeypatch.setenv("HYBRID_BINANCE_API_SECRET", "s")
    monkeypatch.setenv("HYBRID_DATA_DIR", str(hybrid_dir))
    monkeypatch.setenv("QUANT_DATA_DIR", str(quant_dir))
    monkeypatch.setenv("COIN_UNIVERSE", "bitcoin")
    # Provide required quant config vars so config.load_config() succeeds
    monkeypatch.setenv("BINANCE_API_KEY", "qk")
    monkeypatch.setenv("BINANCE_API_SECRET", "qs")
    monkeypatch.setenv("COINGLASS_API_KEY", "cgk")

    _seed_ohlcv_cache(hybrid_dir, "BTCUSDT")

    fake_ex = FakeExchange()
    res = hybrid_runner.run_hybrid_cycle(
        cycle_id="2026-06-11", dry_run=False,
        _exchange=fake_ex, _graph=StubGraph(),
    )
    assert res.status == "ok", f"cycle returned {res.status}: {res.error_msg}"

    # An order was placed on the hybrid (fake) exchange
    assert len(fake_ex.orders) >= 1, "expected at least one order on the hybrid exchange"

    # Hybrid journal got a trade row
    hybrid_db = str(hybrid_dir / "trade_journal.db")
    hyb_conn = sqlite3.connect(hybrid_db)
    h_trades = hyb_conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    hyb_conn.close()
    assert h_trades >= 1, f"hybrid journal has {h_trades} trades (expected ≥ 1)"

    # Quant journal is UNTOUCHED (0 trades written from this cycle)
    qn = sqlite3.connect(str(quant_dir / "trade_journal.db")).execute(
        "SELECT COUNT(*) FROM trades"
    ).fetchone()[0]
    assert qn == 0, f"quant journal has {qn} trades — isolation breached!"


def test_loop_compose_uses_mult_not_position(tmp_path, monkeypatch):
    """Verify compose uses (mult, eff_w) from StubGraph, not mp['position']=-999."""
    quant_dir = tmp_path / "data"
    quant_dir.mkdir()
    hybrid_dir = tmp_path / "data-hybrid"

    _seed_quant_db(str(quant_dir / "trade_journal.db"), "2026-06-11")

    monkeypatch.setenv("HYBRID_BINANCE_API_KEY", "k")
    monkeypatch.setenv("HYBRID_BINANCE_API_SECRET", "s")
    monkeypatch.setenv("HYBRID_DATA_DIR", str(hybrid_dir))
    monkeypatch.setenv("QUANT_DATA_DIR", str(quant_dir))
    monkeypatch.setenv("COIN_UNIVERSE", "bitcoin")
    monkeypatch.setenv("BINANCE_API_KEY", "qk")
    monkeypatch.setenv("BINANCE_API_SECRET", "qs")
    monkeypatch.setenv("COINGLASS_API_KEY", "cgk")

    _seed_ohlcv_cache(hybrid_dir, "BTCUSDT")

    # StubGraph returns position=-999 but the hybrid should use mult=1.4, eff_w=0.5
    fake_ex = FakeExchange()
    res = hybrid_runner.run_hybrid_cycle(
        cycle_id="2026-06-11", dry_run=False,
        _exchange=fake_ex, _graph=StubGraph(),
    )
    assert res.status == "ok"
    # If position=-999 were used, the order quantity would be enormous/negative;
    # it's bounded to exchange round_quantity (a small positive number).
    for sym, side, qty in fake_ex.orders:
        assert qty > 0, f"negative qty {qty} for {sym}/{side} — position=-999 leaked"
        assert qty < 10.0, f"huge qty {qty} for {sym}/{side} — position=-999 leaked"


def test_modulator_failure_degrades_to_pure_quant(tmp_path, monkeypatch):
    """A crashing modulator must not block the cycle — pure-quant fallback."""
    class CrashGraph:
        def propagate_with_modulator(self, coin, date):
            raise RuntimeError("intentional modulator crash")

    quant_dir = tmp_path / "data"
    quant_dir.mkdir()
    hybrid_dir = tmp_path / "data-hybrid"

    _seed_quant_db(str(quant_dir / "trade_journal.db"), "2026-06-11")

    monkeypatch.setenv("HYBRID_BINANCE_API_KEY", "k")
    monkeypatch.setenv("HYBRID_BINANCE_API_SECRET", "s")
    monkeypatch.setenv("HYBRID_DATA_DIR", str(hybrid_dir))
    monkeypatch.setenv("QUANT_DATA_DIR", str(quant_dir))
    monkeypatch.setenv("COIN_UNIVERSE", "bitcoin")
    monkeypatch.setenv("BINANCE_API_KEY", "qk")
    monkeypatch.setenv("BINANCE_API_SECRET", "qs")
    monkeypatch.setenv("COINGLASS_API_KEY", "cgk")

    _seed_ohlcv_cache(hybrid_dir, "BTCUSDT")

    fake_ex = FakeExchange()
    res = hybrid_runner.run_hybrid_cycle(
        cycle_id="2026-06-11", dry_run=False,
        _exchange=fake_ex, _graph=CrashGraph(),
    )
    # Cycle must succeed (pure quant fallback, not crash)
    assert res.status == "ok", f"cycle failed with modulator crash: {res.error_msg}"
    # Still executed (pure-quant base is non-zero for a long signal)
    assert len(fake_ex.orders) >= 1
