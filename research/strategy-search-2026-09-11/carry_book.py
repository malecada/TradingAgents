"""Conditional signed-quantity USDT spot/linear-perpetual book; no I/O or gates."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR
import math

START_MS, END_MS, DAY_MS = 1775001600000, 1782864000000, 86_400_000
LOTS = {"BTC": 0.001, "ETH": 0.01}
COSTS = {"base": {"spot_fee": 0.001, "perp_fee": 0.0005, "slippage": 0.0002},
         "stress": {"spot_fee": 0.002, "perp_fee": 0.001, "slippage": 0.0004}}


def _finite(value, positive=False):
    if isinstance(value, bool):
        raise ValueError("boolean is not a price or cashflow")
    result = float(value)
    if not math.isfinite(result) or (positive and result <= 0):
        raise ValueError("finite positive prices/capital or finite cashflows required")
    return result


def _bars(rows):
    if len(rows) != 91:
        raise ValueError("exact 91 daily bars required")
    result = []
    for index, row in enumerate(rows):
        expected = START_MS + DAY_MS * index
        if len(row) != 12 or type(row[0]) is not int or row[0] != expected or type(row[6]) is not int or row[6] != expected + DAY_MS - 1:
            raise ValueError("complete ordered daily bar chronology required")
        opn, high, low, close = [_finite(value, True) for value in row[1:5]]
        if not low <= min(opn, close) <= max(opn, close) <= high:
            raise ValueError("invalid OHLC")
        result.append({"open": opn, "high": high, "low": low, "close": close})
    return result


def _funding(rows, asset, quantity):
    if len(rows) != 273:
        raise ValueError("all 273 conditional funding events required; no missing-event fill")
    cash = [[] for _ in range(91)]
    previous, excluded = None, []
    for index, row in enumerate(rows):
        stamp = row["fundingTime"]
        if type(stamp) is not int or not START_MS <= stamp < END_MS or (previous is not None and stamp <= previous):
            raise ValueError("funding event chronology invalid")
        if abs(stamp - (START_MS + index * DAY_MS // 3)) > 5000:
            raise ValueError("funding event missing/unexpected under conditional schedule")
        if row["symbol"] != asset + "USDT":
            raise ValueError("funding symbol differs")
        rate, mark = _finite(row["fundingRate"]), _finite(row["markPrice"], True)
        if stamp <= START_MS + 5000:
            excluded.append(stamp)
        else:
            cash[(stamp - START_MS) // DAY_MS].append(quantity * mark * rate)
        previous = stamp
    if len(excluded) != 1:
        raise ValueError("first funding event exclusion ambiguous")
    return cash, excluded


def _liquidate(quantity, spot_entry, perp_entry, spot_exit, perp_exit, capital,
               idle, reserve, funding, costs):
    spot_exit_fee = quantity * spot_exit * costs["spot_fee"]
    perp_exit_fee = quantity * perp_exit * costs["perp_fee"]
    spot_proceeds = quantity * spot_exit
    perp_realized = quantity * (perp_entry - perp_exit)
    future_cash = reserve + funding + perp_realized - perp_exit_fee
    final_cash = idle + future_cash + spot_proceeds - spot_exit_fee
    return {"spot_exit_price": spot_exit, "perp_exit_price": perp_exit,
            "spot_sale_proceeds": spot_proceeds, "spot_exit_fee": spot_exit_fee,
            "perp_realized_price_pnl": perp_realized, "perp_exit_fee": perp_exit_fee,
            "cumulative_funding_cash": funding, "futures_cash_after_close": future_cash,
            "idle_cash": idle, "final_cash": final_cash, "cash_profit": final_cash - capital,
            "terminal_spot_quantity": 0.0, "terminal_perp_quantity": 0.0}


def book(spot_bars, perp_bars, mark_bars, funding_events, *, asset, capital, cost_scenario="base"):
    """No selection/inference: fixed quantities, explicit wallets and assumptions.

    Rates are cash-paid at the recorded event mark. The first 00:00 funding
    event is excluded because the position opens at that boundary. Public OHLC
    executions, lot sizes, USDT fee payment and 1% maintenance are conditional.
    """
    if asset not in LOTS or cost_scenario not in COSTS:
        raise ValueError("unsupported asset/cost scenario")
    capital = _finite(capital, True)
    spot, perp, mark = _bars(spot_bars), _bars(perp_bars), _bars(mark_bars)
    costs = COSTS[cost_scenario]
    slip, spot_fee, perp_fee = costs["slippage"], costs["spot_fee"], costs["perp_fee"]
    spot_entry, perp_entry = spot[0]["open"] * (1 + slip), perp[0]["open"] * (1 - slip)
    entry_cash_per_unit = spot_entry * (1 + spot_fee) + perp_entry * perp_fee
    lot = LOTS[asset]
    lots = (Decimal(str(capital)) * Decimal("0.4") /
            (Decimal(str(entry_cash_per_unit)) * Decimal(str(lot)))).to_integral_value(rounding=ROUND_FLOOR)
    quantity = float(lots * Decimal(str(lot)))
    if quantity <= 0:
        return {"status": "unavailable", "reason": "capital cannot fund one assumed common lot",
                "asset": asset, "capital": capital, "assumed_lot": lot}
    initial_spot_fee, initial_perp_fee = quantity * spot_entry * spot_fee, quantity * perp_entry * perp_fee
    reserve = 0.5 * capital
    idle = capital - reserve - quantity * spot_entry - initial_spot_fee - initial_perp_fee
    if idle < 0.1 * capital - 1e-10:
        return {"status": "unavailable", "reason": "initial idle reserve below 10% capital"}
    funding, excluded = _funding(funding_events, asset, quantity)
    initial = {"quantity": quantity, "spot_quantity": quantity, "perp_quantity": -quantity,
               "assumed_common_lot": lot, "spot_entry_price": spot_entry, "perp_entry_price": perp_entry,
               "spot_purchase_principal": quantity * spot_entry, "spot_entry_fee": initial_spot_fee,
               "perp_entry_fee": initial_perp_fee, "futures_reserve": reserve, "idle_cash": idle}
    trace, cumulative = [], 0.0
    for index in range(91):
        prior_funding = cumulative
        day_cash = math.fsum(funding[index])
        negative_cash = math.fsum(value for value in funding[index] if value < 0)
        cumulative = math.fsum((cumulative, day_cash))
        wallet = reserve + cumulative
        short_mtm = quantity * (perp_entry - mark[index]["close"])
        spot_value = quantity * spot[index]["close"]
        nav = idle + wallet + short_mtm + spot_value
        maintenance = 0.01 * quantity * mark[index]["high"]
        lower_wallet = reserve + prior_funding + negative_cash
        margin_equity_lower = lower_wallet + quantity * (perp_entry - mark[index]["high"])
        trace.append({"date": datetime.fromtimestamp((START_MS + index * DAY_MS) / 1000, timezone.utc).date().isoformat(),
                      "spot_close": spot[index]["close"], "perp_close": perp[index]["close"],
                      "mark_close": mark[index]["close"], "mark_high": mark[index]["high"],
                      "funding_event_count": len(funding[index]), "funding_cash": day_cash,
                      "negative_funding_cash": negative_cash, "cumulative_funding_cash": cumulative,
                      "futures_wallet": wallet, "short_mtm": short_mtm, "spot_value": spot_value,
                      "idle_cash": idle, "pre_exit_nav": nav, "nav": nav,
                      "margin_wallet_lower_bound": lower_wallet,
                      "margin_equity_lower_bound": margin_equity_lower,
                      "assumed_maintenance_requirement": maintenance,
                      "margin_buffer_lower_bound": margin_equity_lower - maintenance,
                      "spot_quantity": quantity, "perp_quantity": -quantity,
                      "net_base_quantity": 0.0,
                      "net_market_notional": quantity * (spot[index]["close"] - mark[index]["close"]),
                      "gross_market_notional": quantity * (spot[index]["close"] + mark[index]["close"])})
    final = _liquidate(quantity, spot_entry, perp_entry, spot[-1]["close"] * (1 - slip),
                       perp[-1]["close"] * (1 + slip), capital, idle, reserve, cumulative, costs)
    final["spot_price_pnl"] = final["spot_sale_proceeds"] - initial["spot_purchase_principal"]
    final["all_fees"] = initial_spot_fee + initial_perp_fee + final["spot_exit_fee"] + final["perp_exit_fee"]
    final["cash_profit_from_signed_components"] = math.fsum((final["spot_price_pnl"],
        final["perp_realized_price_pnl"], cumulative, -final["all_fees"]))
    final["cash_reconciliation_difference"] = final["cash_profit"] - final["cash_profit_from_signed_components"]
    final_row = trace[-1]
    final_row["pre_exit_components"] = {name: final_row[name] for name in (
        "futures_wallet", "short_mtm", "spot_value", "idle_cash", "spot_quantity",
        "perp_quantity", "net_base_quantity", "net_market_notional", "gross_market_notional", "nav")}
    final_row.update(nav=final["final_cash"], futures_wallet=final["futures_cash_after_close"],
                     short_mtm=0.0, spot_value=0.0, spot_quantity=0.0, perp_quantity=0.0,
                     net_base_quantity=0.0, net_market_notional=0.0, gross_market_notional=0.0,
                     idle_cash=idle + final["spot_sale_proceeds"] - final["spot_exit_fee"])
    peak, max_dd, previous_nav, simple_returns = capital, 0.0, capital, []
    for row in trace:
        nav = row["nav"]
        peak = max(peak, nav)
        max_dd = max(max_dd, (peak - nav) / peak)
        simple = nav / previous_nav - 1 if previous_nav > 0 else None
        row["full_capital_daily_return"] = simple
        simple_returns.append(simple)
        previous_nav = nav
    valid_logs = all(value is not None and value > -1 for value in simple_returns)
    log_sum = math.fsum(math.log1p(value) for value in simple_returns) if valid_logs else None
    arithmetic_sum = math.fsum(simple_returns) if valid_logs else None
    stresses = {}
    for name, multiple in (("half", 0.5), ("double", 2.0)):
        stressed = _liquidate(quantity, spot_entry, perp_entry, spot[0]["open"] * multiple * (1 - slip),
                              perp[0]["open"] * multiple * (1 + slip), capital, idle, reserve, 0.0, costs)
        high = max(mark[0]["open"], mark[0]["open"] * multiple)
        stressed["margin_buffer_lower_bound"] = reserve + quantity * (perp_entry - high) - 0.01 * quantity * high
        stressed["quantity"] = quantity
        stressed["price_multiple"] = multiple
        stressed["description"] = "Both spot/perp initial raw prices scale equally; quantity fixed, funding zero, original entry costs and stressed exit costs retained."
        stresses[name] = stressed
    profit = final["cash_profit"]
    return {"status": "conditional", "asset": asset, "capital": capital, "cost_scenario": cost_scenario,
            "costs": dict(costs), "days": 91, "initial": initial, "daily_trace": trace,
            "final_ledger": final, "excluded_first_funding_timestamps": excluded,
            "metrics": {"cash_profit": profit, "full_capital_return": profit / capital,
                        "annualized_simple_return_365": profit / capital * 365 / 91,
                        "max_drawdown": max_dd, "minimum_margin_buffer_lower_bound": min(row["margin_buffer_lower_bound"] for row in trace),
                        "margin_buffer_breach": any(row["margin_buffer_lower_bound"] < 0 for row in trace),
                        "funding_cash": cumulative, "applied_funding_events": sum(len(day) for day in funding)},
            "quantity_price_stresses": stresses,
            "convention_diagnostic": {"label": "Invalid log-return arithmetic booking diagnostic only; not cash PnL",
                                      "status": "complete" if valid_logs else "unavailable",
                                      "all_days": 91, "valid_simple_index_days": sum(value is not None and value > -1 for value in simple_returns),
                                      "log1p_sum": log_sum,
                                      "arithmetic_daily_simple_return_sum": arithmetic_sum,
                                      "terminal_simple_return": profit / capital,
                                      "log_sum_minus_arithmetic_daily_sum": None if log_sum is None else log_sum - arithmetic_sum,
                                      "arithmetic_daily_sum_minus_terminal_simple_return": None if arithmetic_sum is None else arithmetic_sum - profit / capital,
                                      "log_sum_minus_actual_simple_total_return": None if log_sum is None else log_sum - profit / capital},
            "assumptions": ["Fixed assumed common BTC 0.001 / ETH 0.01 lots; historical/current rules unverified.",
                            "Linear USDT perpetual, fees paid in USDT, public OHLC executions conditional.",
                            "No borrow leg, stablecoin conversion, transfer or settlement modeled; no account eligibility claim.",
                            "50% capital futures reserve, at least 10% initial idle, conditional 1% maintenance.",
                            "Daily high/all-negative-funding margin lower bound; non-breach does not establish actual intraday maintenance or liquidation safety.",
                            "Spent historical window; no beta inference or adoption claim."]}
