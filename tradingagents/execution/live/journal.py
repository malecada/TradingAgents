"""SQLite forensic journal — one writer per pipeline step.

All schema in schema.sql. Designed for post-hoc reconstruction of any cycle.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class Journal:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.execute("PRAGMA foreign_keys = ON;")
        with open(_SCHEMA_PATH) as f:
            self._conn.executescript(f.read())
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def log_cycle_start(self, cycle_id: str, *, git_sha: str) -> None:
        self._conn.execute(
            "INSERT OR IGNORE INTO cycles (cycle_id, start_ts, git_commit_sha) "
            "VALUES (?, ?, ?)",
            (cycle_id, _utcnow_iso(), git_sha),
        )
        self._conn.commit()

    def log_cycle_end(self, cycle_id: str, *, status: str, error_msg: str = "") -> None:
        self._conn.execute(
            "UPDATE cycles SET end_ts = ?, status = ?, error_msg = ? WHERE cycle_id = ?",
            (_utcnow_iso(), status, error_msg, cycle_id),
        )
        self._conn.commit()

    def log_prediction(self, *, cycle_id, coin, horizon, model_path_sha,
                        pred_value, ref_price, signal_h7, signal_h14, consensus_signal,
                        pred_quantile_low=None, pred_quantile_high=None) -> None:
        self._conn.execute(
            "INSERT INTO predictions (cycle_id, coin, horizon, model_path_sha, "
            "pred_value, pred_quantile_low, pred_quantile_high, ref_price, "
            "signal_h7, signal_h14, consensus_signal) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (cycle_id, coin, horizon, model_path_sha, pred_value,
             pred_quantile_low, pred_quantile_high, ref_price,
             signal_h7, signal_h14, consensus_signal),
        )
        self._conn.commit()

    def log_sizing(self, *, cycle_id, coin, realized_vol, target_vol, kelly,
                    confidence, base_size, leverage, sma30_multiplier,
                    final_size_notional) -> None:
        self._conn.execute(
            "INSERT INTO sizing (cycle_id, coin, realized_vol, target_vol, kelly, "
            "confidence, base_size, leverage, sma30_multiplier, final_size_notional) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (cycle_id, coin, realized_vol, target_vol, kelly, confidence,
             base_size, leverage, sma30_multiplier, final_size_notional),
        )
        self._conn.commit()

    def log_risk_check(self, cycle_id, coin, check_name, passed: bool,
                        value, threshold, reason: str) -> None:
        self._conn.execute(
            "INSERT INTO risk_checks (cycle_id, coin, check_name, passed, value, threshold, reason) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (cycle_id, coin, check_name, 1 if passed else 0, value, threshold, reason),
        )
        self._conn.commit()

    def log_trade(self, *, cycle_id, coin, side, qty, entry_price, exit_price,
                   pnl, fees, slippage, order_id, stop_loss_id, status) -> None:
        self._conn.execute(
            "INSERT INTO trades (cycle_id, coin, side, qty, entry_price, exit_price, "
            "pnl, fees, slippage, order_id, stop_loss_id, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (cycle_id, coin, side, qty, entry_price, exit_price, pnl, fees,
             slippage, order_id, stop_loss_id, status),
        )
        self._conn.commit()

    def log_portfolio_snapshot(self, cycle_id, total_value, usdt_balance,
                                position_qty_per_coin: dict, unrealized_pnl) -> None:
        self._conn.execute(
            "INSERT INTO portfolio_snapshots (cycle_id, ts, total_value, usdt_balance, "
            "position_qty_per_coin, unrealized_pnl) VALUES (?, ?, ?, ?, ?, ?)",
            (cycle_id, _utcnow_iso(), total_value, usdt_balance,
             json.dumps(position_qty_per_coin), unrealized_pnl),
        )
        self._conn.commit()

    def log_feature_snapshot(self, cycle_id, coin, feature_name, value, source) -> None:
        self._conn.execute(
            "INSERT INTO feature_snapshots (cycle_id, coin, feature_name, value, source) "
            "VALUES (?, ?, ?, ?, ?)",
            (cycle_id, coin, feature_name, value, source),
        )
        self._conn.commit()

    def log_model_artifact(self, *, retrain_id, model_path, train_window_start,
                            train_window_end, train_rows, train_dir_acc_h7,
                            train_dir_acc_h14, sha256) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO model_artifacts (retrain_id, ts, model_path, "
            "train_window_start, train_window_end, train_rows, "
            "train_dir_acc_h7, train_dir_acc_h14, sha256) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (retrain_id, _utcnow_iso(), model_path, train_window_start,
             train_window_end, train_rows, train_dir_acc_h7,
             train_dir_acc_h14, sha256),
        )
        self._conn.commit()

    def log_shadow_decision(self, *, cycle_id, coin, live_signal, backtest_signal,
                             live_size, backtest_size) -> None:
        agree = 1 if live_signal == backtest_signal else 0
        if abs(backtest_size) > 1e-9:
            size_delta_pct = abs(live_size - backtest_size) / abs(backtest_size)
        else:
            size_delta_pct = 0.0 if abs(live_size) < 1e-9 else float("inf")
        self._conn.execute(
            "INSERT INTO shadow_decisions (cycle_id, coin, live_signal, backtest_signal, "
            "agree, live_size, backtest_size, size_delta_pct) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (cycle_id, coin, live_signal, backtest_signal, agree,
             live_size, backtest_size, size_delta_pct),
        )
        self._conn.commit()
