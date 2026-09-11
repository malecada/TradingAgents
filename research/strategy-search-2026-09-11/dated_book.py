"""Conditional dated-futures quantity book; pure arithmetic, no data I/O or gates."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR
import importlib.util
import math
from pathlib import Path

_spec = importlib.util.spec_from_file_location("dated_book_cash_primitives", Path(__file__).with_name("carry_book.py"))
_cash = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_cash)
COSTS, LOTS = _cash.COSTS, _cash.LOTS
START_MS = int(datetime(2026, 5, 1, tzinfo=timezone.utc).timestamp() * 1000)
DAY_MS, HOUR_MS, DAYS = 86_400_000, 3_600_000, 56
END_MS = START_MS + DAYS * DAY_MS


def _number(value, positive=False):
    if isinstance(value, bool):
        raise ValueError("boolean is not a financial number")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        raise ValueError("finite values and positive prices/capital required")
    return result


def _stamp(value):
    if type(value) is int:
        return value
    if isinstance(value, str) and len(value) == 13 and value.isascii() and value.isdigit():
        return int(value)
    raise ValueError("integer millisecond clock required")


def _bars(rows, interval, count):
    if len(rows) != count:
        raise ValueError("complete exact registered bar count required")
    values = []
    for index, row in enumerate(rows):
        expected = START_MS + index * interval
        if len(row) != 12 or _stamp(row[0]) != expected or _stamp(row[6]) != expected + interval - 1:
            raise ValueError("complete ordered unique UTC bar clocks required")
        opn, high, low, close = [_number(value, True) for value in row[1:5]]
        if not low <= min(opn, close) <= max(opn, close) <= high:
            raise ValueError("invalid OHLC ordering")
        for field in (5, 7, 8, 9, 10):
            if _number(row[field]) < 0:
                raise ValueError("negative volume/trade count")
        trades = _number(row[8])
        if not trades.is_integer():
            raise ValueError("trade count must be integer")
        values.append({"open": opn, "high": high, "low": low, "close": close,
                       "volume": _number(row[5]), "trades": trades})
    return values


def book(spot_daily, dated_hourly, *, asset, capital, cost_scenario="base"):
    if asset not in LOTS or cost_scenario not in COSTS:
        raise ValueError("unsupported asset/cost scenario")
    capital = _number(capital, True)
    spot = _bars(spot_daily, DAY_MS, DAYS)
    future = _bars(dated_hourly, HOUR_MS, DAYS * 24)
    zero_volume = [index for index, row in enumerate(future) if row["volume"] == 0]
    zero_trades = [index for index, row in enumerate(future) if row["trades"] == 0]
    held_activity = {"all_hour_count": len(future), "zero_volume_hour_count": len(zero_volume),
                     "zero_volume_hour_ids_ms": [START_MS + index * HOUR_MS for index in zero_volume],
                     "zero_trade_hour_count": len(zero_trades),
                     "zero_trade_hour_ids_ms": [START_MS + index * HOUR_MS for index in zero_trades]}
    if any(row["volume"] <= 0 or row["trades"] <= 0 for row in (spot[0], spot[-1], future[0], future[-1])):
        return {"status": "unavailable", "reason": "entry/exit spot daily and dated hourly volume and trades must be positive",
                "held_activity": held_activity}
    costs = COSTS[cost_scenario]
    slip, sf, ff = costs["slippage"], costs["spot_fee"], costs["perp_fee"]
    spot_open, future_open = spot[0]["open"], future[0]["open"]
    spot_entry, future_entry = spot_open * (1 + slip), future_open * (1 - slip)
    unit_cost = spot_entry * (1 + sf) + future_entry * ff
    lot = LOTS[asset]
    lots = (Decimal(str(capital)) * Decimal("0.4") /
            (Decimal(str(unit_cost)) * Decimal(str(lot)))).to_integral_value(rounding=ROUND_FLOOR)
    quantity = float(lots * Decimal(str(lot)))
    if quantity <= 0:
        return {"status": "unavailable", "reason": "capital cannot fund one assumed common lot",
                "held_activity": held_activity}
    spot_entry_fee, future_entry_fee = quantity * spot_entry * sf, quantity * future_entry * ff
    reserve = capital * 0.5
    idle = capital - reserve - quantity * spot_entry - spot_entry_fee - future_entry_fee
    if idle < capital * 0.1 - 1e-10:
        return {"status": "unavailable", "reason": "initial idle cash below 10% capital"}
    initial = {"quantity": quantity, "spot_quantity": quantity, "future_quantity": -quantity,
               "assumed_common_lot": lot, "spot_entry_price": spot_entry, "future_entry_price": future_entry,
               "spot_purchase_principal": quantity * spot_entry, "spot_entry_fee": spot_entry_fee,
               "future_entry_fee": future_entry_fee, "futures_reserve": reserve, "idle_cash": idle}
    trace = []
    for day in range(DAYS):
        hours = future[day * 24:(day + 1) * 24]
        future_close, trade_high = hours[-1]["close"], max(row["high"] for row in hours)
        short_mtm = quantity * (future_entry - future_close)
        spot_value = quantity * spot[day]["close"]
        nav = idle + reserve + short_mtm + spot_value
        trace.append({"date": datetime.fromtimestamp((START_MS + day * DAY_MS) / 1000, timezone.utc).date().isoformat(),
                      "spot_close": spot[day]["close"], "future_close": future_close,
                      "future_trade_high": trade_high, "futures_wallet": reserve,
                      "funding_cash": 0.0, "cumulative_funding_cash": 0.0,
                      "short_mtm": short_mtm, "spot_value": spot_value, "idle_cash": idle,
                      "spot_quantity": quantity, "future_quantity": -quantity,
                      "net_base_quantity": 0.0,
                      "net_market_notional": quantity * (spot[day]["close"] - future_close),
                      "gross_market_notional": quantity * (spot[day]["close"] + future_close),
                      "trade_high_reserve_buffer_proxy": reserve + quantity * (future_entry - trade_high) - 0.01 * quantity * trade_high,
                      "pre_exit_nav": nav, "nav": nav})
    final = _cash._liquidate(quantity, spot_entry, future_entry, spot[-1]["close"] * (1 - slip),
                             future[-1]["close"] * (1 + slip), capital, idle, reserve, 0.0, costs)
    # Rename the primitive's perpetual terminology for this linear dated contract.
    for old, new in (("perp_exit_price", "future_exit_price"), ("perp_realized_price_pnl", "future_realized_price_pnl"),
                     ("perp_exit_fee", "future_exit_fee"), ("terminal_perp_quantity", "terminal_future_quantity")):
        final[new] = final.pop(old)
    raw_basis = quantity * ((spot[-1]["close"] - spot_open) + (future_open - future[-1]["close"]))
    price_pnl = quantity * (final["spot_exit_price"] - spot_entry) + final["future_realized_price_pnl"]
    all_fees = spot_entry_fee + future_entry_fee + final["spot_exit_fee"] + final["future_exit_fee"]
    final.update(raw_basis_convergence=raw_basis, zero_friction_same_quantity_profit=raw_basis,
                 executed_price_pnl=price_pnl, slippage_cost=raw_basis - price_pnl, all_fees=all_fees,
                 cash_profit_from_signed_components=price_pnl - all_fees,
                 cash_reconciliation_difference=final["cash_profit"] - (price_pnl - all_fees))
    last = trace[-1]
    last["pre_exit_components"] = {name: last[name] for name in ("nav", "futures_wallet", "short_mtm", "spot_value", "idle_cash",
                "spot_quantity", "future_quantity", "net_base_quantity", "gross_market_notional", "net_market_notional")}
    last.update(nav=final["final_cash"], futures_wallet=final["futures_cash_after_close"], short_mtm=0.0,
                spot_value=0.0, spot_quantity=0.0, future_quantity=0.0, net_base_quantity=0.0,
                gross_market_notional=0.0, net_market_notional=0.0,
                idle_cash=idle + final["spot_sale_proceeds"] - final["spot_exit_fee"])
    peak, maximum_drawdown, previous, returns = capital, 0.0, capital, []
    for row in trace:
        nav = row["nav"]
        peak = max(peak, nav)
        maximum_drawdown = max(maximum_drawdown, (peak - nav) / peak)
        value = nav / previous - 1 if previous > 0 else None
        row["full_capital_daily_return"] = value
        returns.append(value)
        previous = nav
    valid = all(value is not None and value > -1 for value in returns)
    log_sum = math.fsum(math.log1p(value) for value in returns) if valid else None
    arithmetic_sum = math.fsum(returns) if valid else None
    total_return = final["cash_profit"] / capital
    stresses = {}
    for name, multiple in (("half", 0.5), ("double", 2.0)):
        stress = _cash._liquidate(quantity, spot_entry, future_entry, spot_open * multiple * (1 - slip),
                                future_open * multiple * (1 + slip), capital, idle, reserve, 0.0, costs)
        for old, new in (("perp_exit_price", "future_exit_price"), ("perp_realized_price_pnl", "future_realized_price_pnl"),
                         ("perp_exit_fee", "future_exit_fee"), ("terminal_perp_quantity", "terminal_future_quantity")):
            stress[new] = stress.pop(old)
        high = max(future_open, future_open * multiple)
        stress.update(quantity=quantity, price_multiple=multiple,
                      trade_high_reserve_buffer_proxy=reserve + quantity * (future_entry - high) - 0.01 * quantity * high,
                      interpretation="Same quantity and initial costs; both initial raw prices scale equally, funding zero, exit costs retained. Trade-price margin scenario only.")
        stresses[name] = stress
    return {"status": "conditional", "asset": asset, "capital": capital, "days": DAYS,
            "cost_scenario": cost_scenario, "costs": dict(costs), "initial": initial,
            "daily_trace": trace, "final_ledger": final, "held_activity": held_activity,
            "metrics": {"cash_profit": final["cash_profit"], "full_capital_return": total_return,
                        "annualized_simple_return_365": total_return * 365 / DAYS,
                        "max_drawdown": maximum_drawdown,
                        "minimum_trade_high_reserve_buffer_proxy": min(row["trade_high_reserve_buffer_proxy"] for row in trace),
                        "trade_high_proxy_breach": any(row["trade_high_reserve_buffer_proxy"] < 0 for row in trace)},
            "actual_margin_risk": {"status": "unavailable", "reason": "Actual mark, maintenance tiers and liquidation path are unverified; trade highs are not conservative mark bounds."},
            "quantity_price_stresses": stresses,
            "convention_diagnostic": {"label": "Invalid log-return arithmetic booking diagnostic only; not cash PnL",
                "status": "complete" if valid else "unavailable", "all_days": DAYS,
                "valid_simple_index_days": sum(value is not None and value > -1 for value in returns),
                "log1p_sum": log_sum, "arithmetic_daily_simple_return_sum": arithmetic_sum,
                "terminal_simple_return": total_return,
                "log_sum_minus_arithmetic_daily_sum": None if log_sum is None else log_sum - arithmetic_sum,
                "arithmetic_daily_sum_minus_terminal_simple_return": None if arithmetic_sum is None else arithmetic_sum - total_return},
            "assumptions": ["Linear USDT June26 dated future; no periodic funding or borrowing leg, conditional instrument treatment.",
                "Fixed assumed common lots and USDT-paid fees; historical/current trading rules and account access unverified.",
                "May1 open entry and June25 final-hour close exit precede unverified expiry-day terminal prices.",
                "Public hourly executions and daily trade-price valuations are conditional, not actual fills or mark prices.",
                "50% capital future reserve, at least 10% initial idle; 1% maintenance is a trade-price proxy scenario only.",
                "Cash profit excludes opportunity cost, stablecoin conversion, transfer and settlement charges; no adoption or beta inference."]}
