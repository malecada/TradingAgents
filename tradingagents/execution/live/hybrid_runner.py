# tradingagents/execution/live/hybrid_runner.py
"""Hybrid (quant base × LLM modulator) live cycle.

Runs AFTER ta-cycle, reads the quant cycle's predictions, re-derives the V5
base, runs the modulator graph per coin, recomposes, and executes on a SECOND
testnet account with its own journal. Zero writes to the quant book.

CLI entry: ``python -m tradingagents.execution.live.hybrid_runner --once``
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from tradingagents.execution.live import config, halt, journal
from tradingagents.execution.live import risk as live_risk
from tradingagents.execution.live import sizer, stops
from tradingagents.execution.live.config import to_binance_symbol
from tradingagents.execution.live.hold_sizer import HoldState
from tradingagents.execution.live.hybrid_base import derive_base
from tradingagents.execution.live.hybrid_compose import (
    HYBRID_ANALYSTS,
    build_hybrid_config,
    compose_final,
    extract_modulator_outputs,
    stage_quant_preds,
)
from tradingagents.execution.live.hybrid_config import load_hybrid_account
from tradingagents.execution.live.hybrid_io import read_cycle_predictions
from tradingagents.execution.live.runner import CycleResult, _today_id, _write_heartbeat

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Private builders (injectable for tests)
# ---------------------------------------------------------------------------

def _build_exchange(acct):
    from tradingagents.execution.exchange import ExchangeClient
    return ExchangeClient(api_key=acct.api_key, api_secret=acct.api_secret, testnet=True)


def _build_graph(quant_pred_dir: str):
    from tradingagents.graph.trading_graph import TradingAgentsGraph
    return TradingAgentsGraph(
        selected_analysts=HYBRID_ANALYSTS,
        config=build_hybrid_config(quant_pred_dir=quant_pred_dir),
    )


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_hybrid_cycle(
    cycle_id: str | None = None,
    dry_run: bool = False,
    *,
    _exchange=None,
    _graph=None,
) -> CycleResult:
    """Execute one hybrid cycle. Returns a CycleResult — never raises."""
    cycle_id = cycle_id or _today_id()
    acct = load_hybrid_account()
    data_dir = Path(acct.data_dir)
    n_executed = 0

    try:
        # R4: halt sentinel check (mirrors quant runner contract)
        if halt.is_halted(data_dir=data_dir):
            return CycleResult(
                cycle_id=cycle_id, status="halted", n_executed=0,
                error_msg=halt.halt_reason(data_dir=data_dir),
            )

        # ── load quant predictions ─────────────────────────────────────────
        rows, preds = read_cycle_predictions(acct.quant_db_path, cycle_id)
        if not preds:
            return CycleResult(
                cycle_id=cycle_id, status="no_quant_cycle", n_executed=0,
                error_msg=f"no predictions for {cycle_id} in quant journal",
            )

        # ── stage preds CSV for the modulator graph ────────────────────────
        staged = stage_quant_preds(
            rows, date=cycle_id,
            out_dir=data_dir / "cycle_preds" / cycle_id,
        )

        # ── build live objects (or accept injected test stubs) ─────────────
        cfg = config.load_config()
        cfg_dict = dict(
            horizons=cfg.horizons, symmetric=cfg.symmetric, target_vol=cfg.target_vol,
            kelly_fraction=cfg.kelly_fraction, max_leverage=cfg.max_leverage,
            vol_lookback=cfg.vol_lookback, vol_cap_pct=cfg.vol_cap_pct,
            confidence_ref_return=cfg.confidence_ref_return, trend_sma=cfg.trend_sma,
            trend_multiplier=cfg.trend_multiplier, min_hold=cfg.min_hold,
            early_exit_loss=cfg.early_exit_loss,
        )

        ex = _exchange or _build_exchange(acct)
        graph = _graph or _build_graph(str(staged))
        j = journal.Journal(str(data_dir / "trade_journal.db"))

        try:
            j.log_cycle_start(cycle_id, git_sha="hybrid")
            portfolio_before = float(ex.get_total_portfolio_value())
            asof = datetime.now(timezone.utc).date().isoformat()
            weights = config.compute_portfolio_weights(list(preds.keys()))

            # Count already-open positions for max-positions gate
            open_count = 0
            for coin in preds:
                sym = to_binance_symbol(coin)
                try:
                    pos = float(ex.get_current_position(sym))
                    if abs(pos) > 1e-9:
                        open_count += 1
                except Exception:
                    pass

            for coin in preds:
                symbol = to_binance_symbol(coin)

                # ── load OHLCV cache ───────────────────────────────────────
                cache = data_dir / "ohlcv_cache" / f"{symbol}_1d.parquet"
                history = pd.read_parquet(cache) if cache.exists() else pd.DataFrame()

                # ── re-derive V5 base using hybrid journal's hold state ────
                prev = j.get_hold_state(coin)
                prev_state = HoldState(
                    current_dir=prev["current_dir"] if prev else 0,
                    bars_held=prev["bars_held"] if prev else 0,
                    entry_price=prev["entry_price"] if prev else 0.0,
                    entry_base=prev["entry_base"] if prev else 0.0,
                )
                base, new_state, sz = derive_base(
                    coin=coin, prediction=preds[coin], price_history=history,
                    prev_state=prev_state, cfg=cfg_dict, asof=asof,
                )
                if sz is None:
                    continue

                # ── run modulator (degrade to pure quant on failure) ───────
                try:
                    _state, mp, _qs, _narr = graph.propagate_with_modulator(coin, cycle_id)
                except Exception as e:
                    logger.warning("modulator failed for %s: %s; pure quant", coin, e)
                    mp = None

                mult, eff_w = extract_modulator_outputs(mp)
                final_fraction = compose_final(base=base, multiplier=mult, effective_weight=eff_w)

                # ── persist hybrid hold state ──────────────────────────────
                j.upsert_hold_state(
                    coin=coin, current_dir=new_state.current_dir,
                    bars_held=new_state.bars_held, entry_price=new_state.entry_price,
                    entry_base=new_state.entry_base, entry_cycle=cycle_id,
                )

                # ── risk gates ─────────────────────────────────────────────
                lev_ok, lev_why = live_risk.check_leverage(final_fraction, cfg.max_leverage)
                j.log_risk_check(cycle_id, coin, "leverage", lev_ok,
                                 abs(final_fraction), cfg.max_leverage, lev_why)
                if not lev_ok:
                    continue

                try:
                    current = float(ex.get_current_position(symbol))
                except Exception:
                    current = 0.0

                opening_new = abs(current) < 1e-9 and abs(final_fraction) > 1e-9
                pos_ok, pos_why = live_risk.check_max_positions(
                    open_count, cfg.max_open_positions, opening_new=opening_new,
                )
                j.log_risk_check(cycle_id, coin, "max_positions", pos_ok,
                                 open_count, cfg.max_open_positions, pos_why)
                if not pos_ok:
                    continue

                # ── log sizing ─────────────────────────────────────────────
                j.log_sizing(
                    cycle_id=cycle_id, coin=coin, realized_vol=sz.realized_vol,
                    target_vol=cfg.target_vol, kelly=cfg.kelly_fraction,
                    confidence=sz.confidence, base_size=sz.base_size,
                    leverage=sz.leverage, sma30_multiplier=sz.sma_multiplier,
                    final_size_notional=final_fraction,
                )

                # ── convert to qty and execute ─────────────────────────────
                target_qty = sizer.target_position_qty(
                    size_fraction=final_fraction, portfolio_value=portfolio_before,
                    weight=weights[coin], ref_price=preds[coin]["ref_price"],
                )
                delta = target_qty - current
                if abs(delta) < 1e-8:
                    continue

                side = "BUY" if delta > 0 else "SELL"
                qty = ex.round_quantity(symbol, abs(delta))
                price = preds[coin]["ref_price"]
                if qty * price < ex.min_notional(symbol) and abs(current) < 1e-9:
                    continue  # below MIN_NOTIONAL for an opening order

                if dry_run:
                    continue

                order = ex.place_market_order(symbol, side, qty)
                n_executed += 1
                if opening_new:
                    open_count += 1

                # ── arm protective stop ────────────────────────────────────
                net = current + (qty if side == "BUY" else -qty)
                if abs(net) > 1e-9:
                    stop_side = "SELL" if net > 0 else "BUY"
                    stop_price = (
                        price * (1 - cfg.stop_loss_pct)
                        if net > 0
                        else price * (1 + cfg.stop_loss_pct)
                    )
                    stop_id, _status = stops.arm_stop_loss(
                        ex, symbol=symbol, net_position=net,
                        stop_price=stop_price, stop_side=stop_side,
                    )
                else:
                    stop_id = None

                j.log_trade(
                    cycle_id=cycle_id, coin=coin, side=side, qty=qty,
                    entry_price=price, exit_price=0.0, pnl=0.0, fees=0.0,
                    slippage=0.0, order_id=str(order.get("orderId", "")),
                    stop_loss_id=str(stop_id or ""), status="executed",
                )

            j.log_cycle_end(cycle_id, status="ok")
            return CycleResult(cycle_id=cycle_id, status="ok", n_executed=n_executed)
        finally:
            j.close()

    except Exception as e:
        logger.exception("hybrid cycle failed")
        return CycleResult(
            cycle_id=cycle_id, status="error", n_executed=n_executed,
            error_msg=str(e),
        )
    finally:
        _write_heartbeat(data_dir)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def kill_all() -> None:
    """Halt + flatten all hybrid positions (operator use only)."""
    acct = load_hybrid_account()
    data_dir = Path(acct.data_dir)
    halt.write_halt("operator --kill-all (hybrid)", data_dir=data_dir)
    ex = _build_exchange(acct)
    for coin in config.load_config().coin_universe:
        symbol = to_binance_symbol(coin)
        try:
            ex.cancel_all_orders(symbol)
        except Exception:
            pass
        try:
            pos = ex.get_current_position(symbol)
            if pos:
                ex.place_market_order(symbol, "SELL" if pos > 0 else "BUY", abs(pos))
        except Exception:
            pass


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    p = argparse.ArgumentParser(description="TradingAgents hybrid live cycle")
    p.add_argument("--once", action="store_true", help="Run one cycle and exit")
    p.add_argument("--dry-run", action="store_true", help="Size but do not place orders")
    p.add_argument("--cycle-id", default=None, help="Override cycle date (YYYY-MM-DD)")
    p.add_argument("--kill-all", action="store_true",
                   help="Halt + flatten all hybrid positions")
    p.add_argument("--resume", action="store_true",
                   help="Clear the halt sentinel (after investigation)")
    args = p.parse_args()

    if args.resume:
        acct = load_hybrid_account()
        halt.clear_halt(data_dir=Path(acct.data_dir))
        sys.exit(0)

    if args.kill_all:
        kill_all()
        sys.exit(0)

    res = run_hybrid_cycle(cycle_id=args.cycle_id, dry_run=args.dry_run)
    sys.exit(0 if res.status == "ok" else 1)


if __name__ == "__main__":
    main()
