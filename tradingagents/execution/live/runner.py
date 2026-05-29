"""Daily cycle orchestrator.

Wires the live pipeline:
    data_refresh → retrain → predict → size → risk_check → execute →
    shadow_replay → snapshot → notify.

CLI entry: ``python -m tradingagents.execution.live.runner --once``
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from tradingagents.execution.exchange import (
    BinanceIPBan,
    BinanceOrderTimeoutUnknown,
    ExchangeClient,
)
from tradingagents.execution.live import (
    config,
    data_refresh,
    halt,
    journal,
    notify,
    predict,
    retrain,
    risk,
    shadow,
    sizer,
    stops,
    structured_log,
)
from tradingagents.execution.live.config import to_binance_symbol

logger = logging.getLogger(__name__)


@dataclass
class CycleResult:
    cycle_id: str
    status: str
    n_executed: int
    error_msg: str = ""
    trades_executed: list[dict] = field(default_factory=list)


def _reconcile_fills(ex, journal, *, symbol: str, order_id: str,
                      trade_id: int) -> None:
    """Backfill `trades.fees` + `trades.pnl` from Binance fills.

    `place_market_order` returns only the order envelope; the per-fill
    `commission` and `realizedPnl` are exposed via
    `/fapi/v1/userTrades?orderId=...`. We sum across fills (negative
    commission rebates are taken as magnitude — the operator metric is
    "fees paid") and call `journal.update_trade_fills`.

    Failures are swallowed: the trade row already exists and the worst
    outcome is a NULL fees/pnl pair the operator can see in the journal.
    """
    if not order_id or order_id == "dry-run":
        return
    try:
        fills = ex.get_user_trades(symbol, order_id)
    except Exception as e:  # noqa: BLE001
        logger.warning(
            "fill reconciliation: get_user_trades(%s, %s) failed: %s",
            symbol, order_id, e,
        )
        return
    if not fills:
        return
    total_fees = sum(abs(float(f.get("commission", 0) or 0)) for f in fills)
    total_pnl = sum(float(f.get("realizedPnl", 0) or 0) for f in fills)
    try:
        journal.update_trade_fills(
            trade_id, fees=total_fees, realized_pnl=total_pnl,
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(
            "fill reconciliation: update_trade_fills(%s) failed: %s",
            trade_id, e,
        )


_shutdown_requested = False


def _handle_sigterm(signum, frame):
    global _shutdown_requested
    _shutdown_requested = True


def _git_sha(repo_dir: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=repo_dir,
        ).decode().strip()
    except Exception:
        return "unknown"


def _today_id() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_cycle(cycle_id: str | None = None, dry_run: bool = False) -> CycleResult:
    """Execute one full cycle. Returns a CycleResult — never raises."""
    cycle_id = cycle_id or _today_id()

    cfg = config.load_config()
    data_dir = Path(os.environ.get("DATA_DIR", "data"))
    log_dir = Path(os.environ.get("LOG_DIR", "logs"))
    data_dir.mkdir(parents=True, exist_ok=True)

    # R4: refuse to trade while a persistent halt sentinel is set (written by a
    # KILL_SWITCH trip or --kill-all). The operator clears it with --resume
    # after investigating, so a tripped halt never silently auto-resumes on the
    # next systemd timer fire. Checked before data refresh / exchange access.
    if halt.is_halted(data_dir=data_dir):
        reason = halt.halt_reason(data_dir=data_dir)
        logger.error("Cycle %s skipped — trading halted: %s", cycle_id, reason)
        jh = journal.Journal(str(data_dir / "trade_journal.db"))
        try:
            jh.log_cycle_start(cycle_id, git_sha=_git_sha(Path(__file__).resolve().parents[3]))
            jh.log_cycle_end(cycle_id, status="halted", error_msg=reason)
        finally:
            jh.close()
        try:
            notify.send_alert(
                bot_token=cfg.telegram_bot_token,
                chat_id=cfg.telegram_chat_id,
                severity="HALTED",
                message=(f"Cycle {cycle_id} skipped — trading halted: {reason}. "
                         f"Investigate, then clear with --resume."),
            )
        except Exception:
            pass
        return CycleResult(
            cycle_id=cycle_id, status="halted", n_executed=0, error_msg=reason,
        )

    log_path = log_dir / f"cycle_{cycle_id}.jsonl"
    structured = structured_log.StructuredLogger(log_path, cycle_id)

    j = journal.Journal(str(data_dir / "trade_journal.db"))
    repo_dir = Path(__file__).resolve().parents[3]
    j.log_cycle_start(cycle_id, git_sha=_git_sha(repo_dir))

    n_executed = 0
    trades_executed: list[dict] = []
    portfolio_before = 0.0
    portfolio_after = 0.0
    start_ts = _utc_now_iso()
    # Track supplementary-data freshness so we can stamp it on the terminal
    # cycle row at the end of the success path.
    stale_sources: str | None = None

    try:
        # 1. data_refresh — tiered (critical hard-fail, supplementary degrade)
        with structured.step("data_refresh"):
            try:
                refresh_result = data_refresh.refresh_all(cfg, structured)
            except data_refresh.CriticalDataRefreshError as exc:
                end_ts = _utc_now_iso()
                j.record_cycle(
                    cycle_id=cycle_id, start_ts=start_ts, end_ts=end_ts,
                    status="critical_data_fail", n_trades=0,
                    notes=str(exc),
                    critical_data_fail_sources=json.dumps(
                        [s for s, _e in exc.failures]
                    ),
                )
                try:
                    notify.send_alert(
                        bot_token=cfg.telegram_bot_token,
                        chat_id=cfg.telegram_chat_id,
                        severity="CRITICAL_DATA_FAIL",
                        message=f"V5 cycle {cycle_id}: CRITICAL DATA FAIL — {exc}",
                    )
                except Exception:
                    pass
                return CycleResult(
                    cycle_id=cycle_id, status="critical_data_fail",
                    n_executed=0, trades_executed=[],
                )

        supp_failures = (refresh_result or {}).get("supplementary_failures", [])
        if supp_failures:
            stale_sources = json.dumps([s for s, _ in supp_failures])

        # 2. retrain — V5 composite (routing-aware)
        asof_date = (
            datetime.now(timezone.utc).date() - timedelta(days=1)
        ).isoformat()
        with structured.step("retrain"):
            artifact = retrain.run_retrain_with_fallback(
                routing=cfg.routing,
                horizons=cfg.horizons,
                asof=asof_date,
                checkpoint_dir=Path(cfg.data_root) / "checkpoints",
                retrain_id=cycle_id,
                lookback_days=getattr(cfg, "lookback_days", 730),
            )
            j.record_retrain(
                retrain_id=cycle_id, cycle_id=cycle_id,
                checkpoint_path=str(artifact.path),
                checkpoint_sha=artifact.sha,
                n_train_rows=artifact.n_train_rows,
                train_window_start=artifact.train_window_start,
                train_dir_acc=artifact.train_dir_acc,
                status="success",
                routes=json.dumps(artifact.routes),
            )

        # 3. predict — V5 composite (routing-aware, majority-fail abort)
        with structured.step("predict"):
            try:
                preds_df = predict.run_predict(
                    coin_universe=cfg.coin_universe,
                    routing=cfg.routing,
                    ckpt_path=artifact.path,
                    asof=asof_date,
                    store_root=Path(cfg.data_root) / "onchain",
                    ohlcv_cache=Path(cfg.data_root) / "cache",
                    horizons=cfg.horizons,
                )
            except predict.PredictMajorityFail as exc:
                end_ts = _utc_now_iso()
                j.record_cycle(
                    cycle_id=cycle_id, start_ts=start_ts, end_ts=end_ts,
                    status="predict_majority_fail",
                    n_trades=0, notes=str(exc),
                    supplementary_stale_sources=stale_sources,
                )
                try:
                    notify.send_alert(
                        bot_token=cfg.telegram_bot_token,
                        chat_id=cfg.telegram_chat_id,
                        severity="PREDICT_MAJORITY_FAIL",
                        message=f"V5 cycle {cycle_id}: PREDICT MAJORITY FAIL — {exc}",
                    )
                except Exception:
                    pass
                return CycleResult(
                    cycle_id=cycle_id, status="predict_majority_fail",
                    n_executed=0, trades_executed=[],
                )
            j.record_predictions(cycle_id=cycle_id, preds_df=preds_df)

        # Reshape the V5 long-format preds DataFrame into the per-coin dict the
        # downstream sizing/shadow loop expects: {coin: {ref_price, pred_h{h}}}.
        preds: dict[str, dict] = {}
        if preds_df is not None and len(preds_df) > 0:
            for coin, group in preds_df.groupby("coin"):
                row: dict[str, float] = {
                    "ref_price": float(group["ref_price"].iloc[0]),
                }
                for _, r in group.iterrows():
                    row[f"pred_h{int(r['horizon'])}"] = float(r["prediction"])
                preds[str(coin)] = row

        # Persist feature snapshots so any cycle's decision is reconstructible
        # from the journal alone (spec guarantee). One row per (coin, feature).
        for coin, p in preds.items():
            j.log_feature_snapshot(cycle_id, coin, "ref_price", p["ref_price"], "OHLCV")
            for h in cfg.horizons:
                if f"pred_h{h}" in p:
                    j.log_feature_snapshot(cycle_id, coin, f"pred_h{h}", p[f"pred_h{h}"], "LGB")

        ex = ExchangeClient(
            api_key=cfg.binance_api_key,
            api_secret=cfg.binance_api_secret,
            testnet=not cfg.live_mode,
        )
        # Pin Binance per-symbol leverage to MAX_LEVERAGE so margin
        # consumption matches V2 sizing's leverage assumption. Default
        # testnet leverage is 1x → 3x more margin than expected,
        # exhausting account on multi-coin cycles.
        for c in cfg.coin_universe:
            try:
                ex.set_leverage(to_binance_symbol(c), int(cfg.max_leverage))
            except Exception as e:
                logger.warning("set_leverage failed for %s: %s", c, e)
        portfolio_before = ex.get_total_portfolio_value()

        # Daily PnL + drawdown for the kill-switch gate (L1 fix). The old gate
        # fed compute_live_metrics(today, today) — only today's single snapshot
        # (<2 rows) -> return_pct=0.0, so the daily-loss check never fired.
        # Compare the live current equity against the prior-day close, and
        # track drawdown from the running peak. _today_id() is the UTC date,
        # aligning with the UTC-stamped portfolio_snapshots (local date() would
        # misalign the window near midnight).
        today_str = _today_id()
        try:
            from tradingagents.execution.live.rebacktest import (
                compute_daily_pnl_pct, compute_drawdown_from_peak,
            )
            pnl_today_pct = compute_daily_pnl_pct(portfolio_before, today_str)
            dd_from_peak = compute_drawdown_from_peak(portfolio_before, today_str)
        except Exception:
            pnl_today_pct = 0.0  # safe fallback if journal unavailable
            dd_from_peak = 0.0

        for coin in cfg.coin_universe:
            if _shutdown_requested:
                break
            if coin not in preds:
                continue
            symbol = to_binance_symbol(coin)

            cache = data_dir / "ohlcv_cache" / f"{symbol}_1d.parquet"
            history = pd.read_parquet(cache) if cache.exists() else pd.DataFrame()
            if len(history) < cfg.vol_lookback:
                structured.event("skip_coin", "insufficient_history", {"coin": coin})
                continue

            # 4-5. size + log
            with structured.step("size", {"coin": coin}):
                sz = sizer.compute_size(
                    coin=coin,
                    prediction=preds[coin],
                    price_history=history,
                    horizons=cfg.horizons,
                    symmetric=cfg.symmetric,
                    target_vol=cfg.target_vol,
                    kelly_fraction=cfg.kelly_fraction,
                    max_leverage=cfg.max_leverage,
                    vol_lookback=cfg.vol_lookback,
                    vol_cap_pct=cfg.vol_cap_pct,
                    confidence_ref=cfg.confidence_ref_return,
                    trend_sma=cfg.trend_sma,
                    trend_multiplier=cfg.trend_multiplier,
                )
                # Log per-prediction (one row per horizon).
                # signal_h7 / signal_h14 carry the per-horizon direction from
                # the model (+1/-1/0); consensus_signal carries the V2
                # term-structure consensus output. Both columns get the same
                # values across horizon rows — they describe global state at
                # decision time, not per-horizon.
                dirs = sz.dirs_per_horizon or {}
                sig_h7 = dirs.get(7)
                sig_h14 = dirs.get(14)
                for h in cfg.horizons:
                    j.log_prediction(
                        cycle_id=cycle_id, coin=coin, horizon=h,
                        model_path_sha=artifact.sha,
                        pred_value=preds[coin][f"pred_h{h}"],
                        ref_price=preds[coin]["ref_price"],
                        signal_h7=sig_h7,
                        signal_h14=sig_h14,
                        consensus_signal=sz.signal,
                    )
                j.log_sizing(
                    cycle_id=cycle_id, coin=coin,
                    realized_vol=sz.realized_vol,
                    target_vol=cfg.target_vol,
                    kelly=cfg.kelly_fraction,
                    confidence=sz.confidence,
                    base_size=sz.base_size,
                    leverage=sz.leverage,
                    sma30_multiplier=sz.sma_multiplier,
                    final_size_notional=sz.final_size_notional,
                )

            # 6. risk_check
            with structured.step("risk_check", {"coin": coin}):
                ok_lev, why = risk.check_leverage(
                    sz.final_size_notional, cfg.max_leverage,
                )
                j.log_risk_check(
                    cycle_id, coin, "leverage_cap", ok_lev,
                    abs(sz.final_size_notional), cfg.max_leverage, why,
                )
                if not ok_lev:
                    continue

                # pnl_today_pct / dd_from_peak were pre-computed once per cycle
                # (above the per-coin loop) from the live equity vs the journal.
                ok_loss, why = risk.check_daily_loss(
                    pnl_today_pct, cfg.max_daily_loss_pct,
                )
                j.log_risk_check(
                    cycle_id, coin, "daily_loss", ok_loss,
                    pnl_today_pct, -cfg.max_daily_loss_pct, why,
                )
                ok_dd, why_dd = risk.check_drawdown(
                    dd_from_peak, cfg.max_portfolio_dd,
                )
                j.log_risk_check(
                    cycle_id, coin, "portfolio_drawdown", ok_dd,
                    dd_from_peak, cfg.max_portfolio_dd, why_dd,
                )
                if not ok_loss or not ok_dd:
                    kill_reason = why if not ok_loss else why_dd
                    # R4: persist the halt so the next cycle stays down until an
                    # operator clears it with --resume.
                    halt.write_halt(
                        f"cycle {cycle_id}: {kill_reason}", data_dir=data_dir,
                    )
                    notify.send_alert(
                        bot_token=cfg.telegram_bot_token,
                        chat_id=cfg.telegram_chat_id,
                        severity="KILL_SWITCH", message=kill_reason,
                    )
                    break

            # 7. execute (or shadow-only when no trade)
            if sz.final_size_notional == 0:
                with structured.step("shadow_replay", {"coin": coin}):
                    shadow_dec = shadow.compute_shadow_decision(
                        coin=coin, prediction=preds[coin],
                        price_history=history,
                        horizons=cfg.horizons, symmetric=cfg.symmetric,
                        target_vol=cfg.target_vol,
                        kelly_fraction=cfg.kelly_fraction,
                        max_leverage=cfg.max_leverage,
                        vol_lookback=cfg.vol_lookback,
                        vol_cap_pct=cfg.vol_cap_pct,
                        confidence_ref=cfg.confidence_ref_return,
                        trend_sma=cfg.trend_sma,
                        trend_multiplier=cfg.trend_multiplier,
                    )
                    j.log_shadow_decision(
                        cycle_id=cycle_id, coin=coin,
                        live_signal=sz.signal,
                        backtest_signal=shadow_dec.signal,
                        live_size=sz.final_size_notional,
                        backtest_size=shadow_dec.size,
                    )
                continue

            # Frequency guard: skip if this coin already executed today.
            import sqlite3
            conn = sqlite3.connect(str(data_dir / "trade_journal.db"))
            today_count = conn.execute(
                "SELECT COUNT(*) FROM trades WHERE cycle_id = ? AND coin = ? "
                "AND status IN ('EXECUTED', 'UNPROTECTED', 'DRY_RUN')",
                (cycle_id, coin),
            ).fetchone()[0]
            conn.close()
            ok_freq, why = risk.check_frequency_guard(coin, today_count)
            j.log_risk_check(
                cycle_id, coin, "frequency_guard", ok_freq, today_count, 0, why,
            )
            if not ok_freq:
                continue

            # Target position is what V2 sizing says the book SHOULD look
            # like after this cycle. Trade only the delta vs the current
            # exchange position so we don't stack notional across days.
            # Scale by the coin's renormalized portfolio weight (C1 fix):
            # final_size_notional is a full-equity sleeve fraction, so without
            # the weight an N-coin book runs ~N x the validated gross exposure.
            target_signed_qty = sizer.target_position_qty(
                size_fraction=sz.final_size_notional,
                portfolio_value=portfolio_before,
                weight=cfg.portfolio_weights[coin],
                ref_price=preds[coin]["ref_price"],
            )
            try:
                current_signed_qty = float(ex.get_current_position(symbol))
            except Exception:
                current_signed_qty = 0.0
            delta_qty = target_signed_qty - current_signed_qty
            if abs(delta_qty) < 1e-8:
                structured.event(
                    "execute", "no_change",
                    {"coin": coin, "current": current_signed_qty,
                     "target": target_signed_qty},
                )
                continue
            side = "BUY" if delta_qty > 0 else "SELL"
            qty = abs(delta_qty)

            # Max positions check: only blocks NEW entries (current was flat
            # and target is non-flat). Modifying or closing existing
            # positions is always allowed regardless of open count.
            opening_new = (
                abs(current_signed_qty) < 1e-9
                and abs(target_signed_qty) > 1e-9
            )
            open_count = sum(
                1 for c in cfg.coin_universe
                if abs(ex.get_current_position(to_binance_symbol(c))) > 1e-9
            )
            ok_pos, why = risk.check_max_positions(
                open_count, cfg.max_open_positions,
                opening_new=opening_new,
            )
            j.log_risk_check(
                cycle_id, coin, "max_positions", ok_pos, open_count,
                cfg.max_open_positions, why,
            )
            if not ok_pos:
                continue

            # Skip cleanly when delta is below the symbol's LOT_SIZE — rounded
            # qty would be 0 and Binance rejects with -1013/-2010. This isn't
            # a failure, just nothing to do.
            try:
                rounded_qty = float(ex.round_quantity(symbol, qty))
            except (TypeError, Exception):
                rounded_qty = qty
            if rounded_qty <= 0:
                structured.event(
                    "execute", "below_lot_size",
                    {"coin": coin, "delta": delta_qty,
                     "rounded_qty": rounded_qty},
                )
                continue

            with structured.step("execute", {"coin": coin}):
                if dry_run:
                    j.log_trade(
                        cycle_id=cycle_id, coin=coin, side=side, qty=qty,
                        entry_price=preds[coin]["ref_price"],
                        exit_price=None, pnl=None, fees=None, slippage=None,
                        order_id="dry-run", stop_loss_id=None, status="DRY_RUN",
                    )
                    structured.event(
                        "execute", "dry_run",
                        {"coin": coin, "side": side, "qty": qty},
                    )
                else:
                    try:
                        # If the trade is reducing or closing a same-direction
                        # position (delta opposite-sign to current, magnitude
                        # ≤ |current|) it can run as reduceOnly. This bypasses
                        # the Binance MIN_NOTIONAL ($20) filter and prevents
                        # accidental over-shoot if margin is tight.
                        is_reduce_only = (
                            abs(current_signed_qty) > 1e-9
                            and current_signed_qty * delta_qty < 0
                            and abs(delta_qty) <= abs(current_signed_qty) + 1e-9
                        )
                        order = ex.place_market_order(
                            symbol, side, qty, reduce_only=is_reduce_only,
                        )
                        order_id = str(order.get("orderId", ""))
                        # Binance Futures MARKET orders return avgPrice="0.00"
                        # in the placement response — fill price is only known
                        # afterward. Try the response field; if it's zero or
                        # missing, fall back to the live ticker price (close
                        # enough for slippage telemetry on testnet).
                        avg_price = float(order.get("avgPrice") or 0.0)
                        if avg_price <= 0:
                            try:
                                avg_price = ex.get_ticker_price(symbol)
                            except Exception:
                                avg_price = preds[coin]["ref_price"]
                        exec_price = avg_price
                        ref_px = preds[coin]["ref_price"]
                        slippage = (
                            (exec_price - ref_px) / ref_px if ref_px else 0.0
                        )
                        # Stop direction must follow NET position, not the
                        # delta order side. With delta-trade a SELL can be a
                        # partial close that leaves a residual LONG — placing
                        # a BUY stop above entry on a long would ADD to the
                        # long instead of protecting it. Compute net position
                        # explicitly and skip the stop if position is flat.
                        net_position = current_signed_qty + delta_qty
                        if abs(net_position) < 1e-8:
                            # Flat after the trade — clear any resting stop.
                            try:
                                if hasattr(ex, "cancel_all_orders"):
                                    ex.cancel_all_orders(symbol)
                            except Exception:
                                pass
                            stop_id = None
                            status = "EXECUTED"
                        else:
                            stop_side = "SELL" if net_position > 0 else "BUY"
                            stop_price = (
                                exec_price * (1 - cfg.stop_loss_pct)
                                if net_position > 0
                                else exec_price * (1 + cfg.stop_loss_pct)
                            )
                            # R1/R5: place-then-cancel + monotonic stop. Never
                            # leaves the position naked on a failed swap, and
                            # won't ratchet the stop looser cycle-over-cycle.
                            stop_id, status = stops.arm_stop_loss(
                                ex, symbol=symbol, net_position=net_position,
                                stop_price=stop_price, stop_side=stop_side,
                            )
                            if status == "UNPROTECTED":
                                notify.send_alert(
                                    bot_token=cfg.telegram_bot_token,
                                    chat_id=cfg.telegram_chat_id,
                                    severity="UNPROTECTED",
                                    message=f"{coin} stop-loss failed — position UNPROTECTED",
                                )
                        trade_id = j.log_trade(
                            cycle_id=cycle_id, coin=coin, side=side, qty=qty,
                            entry_price=exec_price, exit_price=None,
                            pnl=None, fees=None, slippage=slippage,
                            order_id=order_id, stop_loss_id=stop_id,
                            status=status,
                        )
                        # Backfill realized PnL + fees from Binance fills —
                        # the placement response above does not include them.
                        _reconcile_fills(
                            ex, j, symbol=symbol, order_id=order_id,
                            trade_id=trade_id,
                        )
                        n_executed += 1
                        trades_executed.append({
                            "coin": coin, "side": side,
                            "qty": qty, "price": exec_price,
                        })
                    except BinanceOrderTimeoutUnknown as e:
                        # -1007 + reconciliation could not confirm fill or
                        # cancel cleanly. Log a distinct status so the next
                        # cycle's position-reconcile path can detect the
                        # ambiguous state, and emit RECONCILE_NEEDED so a
                        # human checks before more orders fire for this coin.
                        j.log_trade(
                            cycle_id=cycle_id, coin=coin, side=side, qty=qty,
                            entry_price=preds[coin]["ref_price"],
                            exit_price=None, pnl=None, fees=None, slippage=None,
                            order_id=None, stop_loss_id=None,
                            status=f"TIMEOUT_{e.state.upper()}",
                        )
                        notify.send_alert(
                            bot_token=cfg.telegram_bot_token,
                            chat_id=cfg.telegram_chat_id,
                            severity="RECONCILE_NEEDED",
                            message=(
                                f"{coin} order -1007 timeout, state={e.state}: "
                                f"{e.side} qty={e.qty}. "
                                f"Verify positions before next cycle."
                            ),
                        )
                    except Exception as e:
                        j.log_trade(
                            cycle_id=cycle_id, coin=coin, side=side, qty=qty,
                            entry_price=preds[coin]["ref_price"],
                            exit_price=None, pnl=None, fees=None, slippage=None,
                            order_id=None, stop_loss_id=None, status="FAILED",
                        )
                        notify.send_alert(
                            bot_token=cfg.telegram_bot_token,
                            chat_id=cfg.telegram_chat_id,
                            severity="FAILED",
                            message=f"{coin} order failed: {e}",
                        )

            # 8. shadow_replay (after execute)
            with structured.step("shadow_replay", {"coin": coin}):
                shadow_dec = shadow.compute_shadow_decision(
                    coin=coin, prediction=preds[coin],
                    price_history=history,
                    horizons=cfg.horizons, symmetric=cfg.symmetric,
                    target_vol=cfg.target_vol,
                    kelly_fraction=cfg.kelly_fraction,
                    max_leverage=cfg.max_leverage,
                    vol_lookback=cfg.vol_lookback,
                    vol_cap_pct=cfg.vol_cap_pct,
                    confidence_ref=cfg.confidence_ref_return,
                    trend_sma=cfg.trend_sma,
                    trend_multiplier=cfg.trend_multiplier,
                )
                j.log_shadow_decision(
                    cycle_id=cycle_id, coin=coin,
                    live_signal=sz.signal,
                    backtest_signal=shadow_dec.signal,
                    live_size=sz.final_size_notional,
                    backtest_size=shadow_dec.size,
                )

        # 9. snapshot
        portfolio_after = ex.get_total_portfolio_value()
        j.log_portfolio_snapshot(
            cycle_id=cycle_id, total_value=portfolio_after,
            usdt_balance=ex.get_usdt_balance(),
            position_qty_per_coin={
                c: ex.get_current_position(to_binance_symbol(c))
                for c in cfg.coin_universe
            },
            unrealized_pnl=portfolio_after - portfolio_before,
        )

        # 10. notify
        with structured.step("notify"):
            agreement = (
                sum(1 for _ in trades_executed) / max(len(trades_executed), 1)
                if trades_executed else 1.0
            )
            # All-time peak across portfolio_snapshots (includes the snapshot
            # just written above, so peak is at worst equal to portfolio_after).
            peak_value = j.peak_total_value()
            notify.send_daily_summary(
                bot_token=cfg.telegram_bot_token,
                chat_id=cfg.telegram_chat_id,
                cycle_id=cycle_id,
                portfolio_before=portfolio_before,
                portfolio_after=portfolio_after,
                trades=trades_executed,
                agreement_rate=agreement,
                peak_value=peak_value,
                initial_capital=cfg.initial_capital,
            )
            # Drawdown-from-peak alert: silent erosion was the bug that hid the
            # V1 -52% loss for months — a single threshold catches it.
            if peak_value > 0:
                dd_from_peak = (portfolio_after - peak_value) / peak_value
                if dd_from_peak <= -0.10:
                    notify.send_alert(
                        bot_token=cfg.telegram_bot_token,
                        chat_id=cfg.telegram_chat_id,
                        severity="DRAWDOWN",
                        message=(
                            f"Cycle {cycle_id}: portfolio {portfolio_after:.2f} "
                            f"is {dd_from_peak:+.2%} from all-time peak "
                            f"{peak_value:.2f}."
                        ),
                    )

        end_ts = _utc_now_iso()
        j.record_cycle(
            cycle_id=cycle_id, start_ts=start_ts, end_ts=end_ts,
            status="ok", n_trades=n_executed,
            supplementary_stale_sources=stale_sources,
        )
        return CycleResult(
            cycle_id=cycle_id, status="ok", n_executed=n_executed,
            trades_executed=trades_executed,
        )

    except BinanceIPBan as e:
        # Binance -1003: don't retry, don't crash the service. Alert + exit clean
        # so systemd timer fires the next cycle on schedule (after ban expires).
        from datetime import datetime as _dt, timezone as _tz
        until_iso = (
            _dt.fromtimestamp(e.until_ms / 1000.0, tz=_tz.utc).isoformat()
            if e.until_ms else "unknown"
        )
        msg = (
            f"Binance IP banned until {until_iso} "
            f"(~{e.seconds_remaining / 60:.1f} min remaining). "
            f"Cycle skipped; next attempt at scheduled timer fire."
        )
        logger.error(msg)
        j.log_cycle_end(cycle_id, status="banned", error_msg=msg)
        try:
            notify.send_alert(
                bot_token=cfg.telegram_bot_token,
                chat_id=cfg.telegram_chat_id,
                severity="BAN", message=msg,
            )
        except Exception:
            pass
        return CycleResult(
            cycle_id=cycle_id, status="banned",
            n_executed=n_executed, error_msg=msg,
        )

    except Exception as e:
        logger.exception("Cycle failed")
        j.log_cycle_end(cycle_id, status="error", error_msg=str(e))
        try:
            notify.send_alert(
                bot_token=cfg.telegram_bot_token,
                chat_id=cfg.telegram_chat_id,
                severity="CYCLE_ERROR", message=str(e),
            )
        except Exception:
            pass
        return CycleResult(
            cycle_id=cycle_id, status="error",
            n_executed=n_executed, error_msg=str(e),
        )
    finally:
        j.close()


def replay_cycle(cycle_id: str) -> CycleResult:
    """Reconstruct decision for a past cycle from journal — read-only.

    Reads predictions, sizing, risk_checks rows for cycle_id and re-runs
    sizer.compute_size + shadow.compute_shadow_decision to verify they still
    produce the recorded values. Implementation deferred to a future phase.
    """
    logger.error(
        "--replay is not implemented in live-v1.0; use the journal SQLite "
        "DB to inspect cycle %s manually.", cycle_id,
    )
    return CycleResult(
        cycle_id=cycle_id, status="error", n_executed=0,
        error_msg="replay_cycle not implemented",
    )


def kill_all() -> None:
    """Cancel all open orders, close all open positions, halt cycle execution."""
    cfg = config.load_config()
    # R4: persist the halt first, so even if the close-out below partially
    # fails the next cycle still refuses to trade until an operator --resumes.
    data_dir = Path(os.environ.get("DATA_DIR", "data"))
    halt.write_halt("operator --kill-all", data_dir=data_dir)
    ex = ExchangeClient(
        api_key=cfg.binance_api_key, api_secret=cfg.binance_api_secret,
        testnet=not cfg.live_mode,
    )
    for coin in cfg.coin_universe:
        symbol = to_binance_symbol(coin)
        try:
            if hasattr(ex, "cancel_all_orders"):
                ex.cancel_all_orders(symbol)
        except Exception as e:
            logger.warning("cancel_all_orders failed for %s: %s", symbol, e)
        try:
            pos = ex.get_current_position(symbol)
        except Exception as e:
            logger.warning("get_current_position failed for %s: %s", symbol, e)
            continue
        if pos != 0:
            close_side = "SELL" if pos > 0 else "BUY"
            try:
                ex.place_market_order(symbol, close_side, abs(pos))
                logger.info("Closed %s position of %s", coin, pos)
            except Exception as e:
                logger.error("Failed to close %s: %s", coin, e)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    parser = argparse.ArgumentParser(description="TradingAgents live cycle")
    parser.add_argument("--once", action="store_true",
                        help="run one cycle then exit")
    parser.add_argument("--dry-run", action="store_true",
                        help="execute pipeline without placing real orders")
    parser.add_argument("--cycle-id", default=None,
                        help="override cycle id (default: today UTC)")
    parser.add_argument("--replay", default=None, metavar="DATE",
                        help="reconstruct decision for past cycle from journal")
    parser.add_argument("--kill-all", action="store_true",
                        help="cancel all orders + close all positions, halt")
    parser.add_argument("--resume", action="store_true",
                        help="clear a persistent trading halt, then exit")
    args = parser.parse_args()

    signal.signal(signal.SIGTERM, _handle_sigterm)

    if args.resume:
        data_dir = Path(os.environ.get("DATA_DIR", "data"))
        cleared = halt.clear_halt(data_dir=data_dir)
        logger.info("Halt %s", "cleared" if cleared else "was not set")
        sys.exit(0)
    if args.kill_all:
        kill_all()
        sys.exit(0)
    if args.replay:
        replay_cycle(args.replay)
        sys.exit(2)  # 2 = not-implemented; distinct from cycle failure (1)
    result = run_cycle(cycle_id=args.cycle_id, dry_run=args.dry_run)
    sys.exit(0 if result.status == "ok" else 1)


if __name__ == "__main__":
    main()
