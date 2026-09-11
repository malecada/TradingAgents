"""Optimistic static unit-conversion and full-notional proxies; no orders or fills."""
from __future__ import annotations

import math

SYMBOLS = ("BTCUSDT", "ETHUSDT", "ETHBTC")
PATHS = {
    "btc-eth": (("BTCUSDT", "buy", "USDT", "BTC"), ("ETHBTC", "buy", "BTC", "ETH"), ("ETHUSDT", "sell", "ETH", "USDT")),
    "eth-btc": (("ETHUSDT", "buy", "USDT", "ETH"), ("ETHBTC", "sell", "ETH", "BTC"), ("BTCUSDT", "sell", "BTC", "USDT")),
}
CASES = [(direction, capital, fee) for direction in PATHS for capital in (1000, 10000) for fee in (0.0, 0.001)]


def case_id(direction, capital, fee):
    return f"{direction}-{capital}-{'zero-fee' if fee == 0 else '10bp'}"


def case_ids():
    return [case_id(*case) for case in CASES]


def _positive(value):
    if isinstance(value, bool):
        raise ValueError("boolean quote is invalid")
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError("quote prices/quantities and computed gross quantities must be finite and positive")
    return value


def _admit(quotes):
    if not isinstance(quotes, dict) or set(quotes) != set(SYMBOLS):
        raise ValueError("exact BTCUSDT/ETHUSDT/ETHBTC quote identity set required")
    admitted = {}
    for symbol in SYMBOLS:
        row = quotes[symbol]
        if "symbol" in row and row["symbol"] != symbol:
            raise ValueError("quote symbol identity conflicts with mapping key")
        values = {name: _positive(row[name]) for name in ("bidPrice", "askPrice", "bidQty", "askQty")}
        if values["bidPrice"] > values["askPrice"]:
            raise ValueError("crossed quote is unavailable")
        admitted[symbol] = values
    return admitted


def _case(quotes, direction, capital, fee):
    path = PATHS[direction]
    wallets = {"USDT": float(capital), "BTC": 0.0, "ETH": 0.0}
    trace, rates = [], []
    gross_terminal = float(capital)
    for index, (symbol, side, spent_asset, acquired_asset) in enumerate(path):
        quote = quotes[symbol]
        price = quote["askPrice"] if side == "buy" else quote["bidPrice"]
        rate = _positive(1 / price if side == "buy" else price)
        rates.append(rate)
        gross_terminal = _positive(gross_terminal * rate)
        before = dict(wallets)
        spent = wallets[spent_asset]
        acquired_gross = _positive(spent * rate)
        commission = acquired_gross * fee
        acquired_net = _positive(acquired_gross - commission)
        base_executed = acquired_gross if side == "buy" else spent
        displayed_size = quote["askQty"] if side == "buy" else quote["bidQty"]
        wallets[spent_asset] = 0.0
        wallets[acquired_asset] += acquired_net
        signed_flows = {asset: wallets[asset] - before[asset] for asset in wallets}
        trace.append({"leg": index + 1, "symbol": symbol, "side": side, "execution_side_price": price,
                      "spent_asset": spent_asset, "spent_quantity": spent, "acquired_asset": acquired_asset,
                      "acquired_gross_quantity": acquired_gross, "fee_asset": acquired_asset,
                      "fee_quantity": commission, "acquired_net_quantity": acquired_net,
                      "executed_base_quantity_before_fee": base_executed,
                      "displayed_best_base_quantity": displayed_size,
                      "displayed_best_size_sufficient": base_executed <= displayed_size,
                      "wallets_before": before, "signed_currency_flows": signed_flows, "wallets_after": dict(wallets),
                      "qualification": "Entire continuous quantity priced at displayed best quote, regardless of size; no depth or fills assumed."})
    fee_equivalents = []
    for index, row in enumerate(trace):
        equivalent = row["fee_quantity"]
        for rate in rates[index + 1:]:
            equivalent *= rate
        if not math.isfinite(equivalent):
            raise ValueError("nonfinite downstream fee conversion")
        row["fee_usdt_equivalent_at_downstream_gross_quotes"] = equivalent
        fee_equivalents.append(equivalent)
    net_terminal = wallets["USDT"]
    gross_factor, net_factor = gross_terminal / capital, net_terminal / capital
    cash_profit = capital * (net_factor - 1)
    fee_drag = math.fsum(fee_equivalents)
    reconciliation = gross_terminal - net_terminal - fee_drag
    if abs(reconciliation) > max(1e-8, abs(gross_terminal) * 1e-12):
        raise ValueError("three-fee USDT decomposition does not reconcile")
    initial_wallets = {"USDT": float(capital), "BTC": 0.0, "ETH": 0.0}
    currency_reconciliation = {asset: initial_wallets[asset] + math.fsum(row["signed_currency_flows"][asset] for row in trace) - wallets[asset]
                               for asset in wallets}
    shadow = capital * math.log(_positive(net_factor))
    return {"status": "conditional_full_notional_proxy", "direction": direction,
            "currency_path": [path[0][2], *[leg[3] for leg in path]], "initial_capital_usdt": capital,
            "received_asset_fee_rate_per_leg": fee, "initial_wallets": initial_wallets,
            "trace": trace, "terminal_wallets": wallets,
            "gross_roundtrip_factor": gross_factor, "after_fee_roundtrip_factor": net_factor,
            "gross_terminal_usdt": gross_terminal, "terminal_usdt": net_terminal,
            "gross_cash_profit_usdt": gross_terminal - capital, "cash_profit_usdt": cash_profit,
            "three_fees_terminal_usdt_equivalent": fee_drag,
            "fee_decomposition_difference_usdt": reconciliation,
            "currency_flow_reconciliation": currency_reconciliation,
            "all_displayed_best_sizes_sufficient": all(row["displayed_best_size_sufficient"] for row in trace),
            "necessary_after_10bp_screen": {"status": "evaluated" if fee == .001 else "not_applicable",
                "positive": cash_profit > 0 if fee == .001 else None,
                "scope": "A factor greater than one is necessary only for positive cycle profit in the frozen synchronous-price/assumed-fee model; asynchronous execution is unvalidated."},
            "convention_diagnostic": {"label": "Invalid arithmetic-PnL log-factor shadow only",
                "capital_times_log_factor_usdt": shadow, "actual_simple_cash_profit_usdt": cash_profit,
                "log_shadow_minus_actual_usdt": shadow - cash_profit},
            "temporary_inventory_risk": "Full capital becomes long BTC or ETH between idealized legs; partial/failed execution can strand that exposure.",
            "execution": {"status": "unavailable", "reason": "Asynchronously observed quotes; no filled orders, atomic cycle or depth execution established."},
            "unvalidated": ["deeper liquidity and impact", "lots, rounding, dust and minimum notional", "actual fee assets/account rates",
                            "account/product access", "latency and partial fills", "market beta, zero-risk exposure or annual returns"],
            "full_notional_scope": "Forced continuous full-capital cycle proxy, not an upper bound on wallet wealth with abstention, partial sizing, rounding or residual cash.",
            "unit_factor_scope": "Best-quote unit factor is optimistic for the frozen synchronous prices and fee assumptions; a factor at or below one excludes positive cycle profit only within that model.",
            "graduation": False}


def evaluate(quotes):
    """Both directions x two capitals x two fees, with every cell retained."""
    try:
        admitted, input_error = _admit(quotes), None
    except (ValueError, TypeError, KeyError, OverflowError) as exc:
        admitted, input_error = {}, type(exc).__name__ + ": " + str(exc)
    results, cells = {}, []
    for direction, capital, fee in CASES:
        identifier = case_id(direction, capital, fee)
        try:
            if input_error is not None:
                raise ValueError(input_error)
            result = _case(admitted, direction, capital, fee)
        except (ValueError, TypeError, KeyError, OverflowError, ZeroDivisionError) as exc:
            result = {"status": "unavailable", "reason": type(exc).__name__ + ": " + str(exc), "graduation": False}
        results[identifier] = result
        cells.append({"id": identifier, "status": "unavailable" if result["status"] == "unavailable" else "complete",
                      **({"reason": result["reason"]} if result["status"] == "unavailable" else {})})
    return {"cases": results, "cells": cells, "case_count": 8, "graduation": False,
            "interpretation": "Eight correlated static conversion proxies, not independent trials. Best-quote unit factors are optimistic within a synchronous-price model; forced full-capital cash values are not universal wallet-wealth upper bounds. Size insufficiency does not establish fills."}
