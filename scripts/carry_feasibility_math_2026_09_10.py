"""Pure, conditional linear-USDT dated-carry arithmetic; no I/O or market access.

Quotes/identity/clocks are admitted by the collector. This module neither admits
actual fees nor models liquidation. Books contain price and order-unit quantity
strings; futures quantities are contracts, converted by the explicit multiplier.
All numeric outputs are JSON-safe Decimal strings. Fee rounding is deliberately
unmodeled (registered fee assumptions), not presented as exchange commissions.
The reserve fraction is rational; lot/budget admission uses cross-multiplication,
so exactly 1/3 is not replaced by a rounded-down capital requirement.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_CEILING, ROUND_FLOOR, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from functools import wraps

PRECISION = 80
ZERO = Decimal(0)
ONE = Decimal(1)
YEAR_SECONDS = Decimal(365 * 24 * 60 * 60)
MODEL = 'conditional_linear_USDT_cash_settled_dated_carry_v1'


def _precise(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        with localcontext() as context:
            context.prec = PRECISION
            context.rounding = ROUND_HALF_EVEN
            return function(*args, **kwargs)
    return wrapped


def _d(value, name, *, positive=False, nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError(f'{name} requires a decimal string, Decimal or integer')
    try:
        number = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f'invalid {name}') from exc
    if not number.is_finite() or (positive and number <= 0) or (nonnegative and number < 0):
        raise ValueError(f'invalid {name}')
    # Fixed, generous precision bound prevents unbounded/exotic numeric payloads.
    if len(number.as_tuple().digits) > 40 or not -30 <= number.adjusted() <= 30:
        raise ValueError(f'unsupported precision/range for {name}')
    return number


def _s(number):
    if number == 0:
        return '0'
    value = format(number, 'f')
    return value.rstrip('0').rstrip('.') if '.' in value else value


def _fraction(value):
    if value == '1/3':
        return 1, 3, '1/3'
    d = _d(value, 'reserve fraction', positive=True)
    if d > 1:
        raise ValueError('reserve fraction exceeds supported full reserve')
    f = Fraction(d)
    return f.numerator, f.denominator, _s(d)


def _rules(value, name):
    if not isinstance(value, dict):
        raise ValueError(f'{name} rules must be a mapping')
    result = {k: _d(value[k], name+' '+k, positive=(k in {'step_size', 'max_qty'}),
                    nonnegative=True)
              for k in ['step_size', 'min_qty', 'max_qty', 'min_notional']}
    result['max_notional'] = (None if value.get('max_notional') is None else
                              _d(value['max_notional'], name+' max_notional', positive=True))
    if result['max_qty'] < result['min_qty']:
        raise ValueError(f'{name} inconsistent quantity bounds')
    if result['max_notional'] is not None and result['max_notional'] < result['min_notional']:
        raise ValueError(f'{name} inconsistent notional bounds')
    return result


def _book(value, name):
    if not isinstance(value, dict):
        raise ValueError(f'{name} book must be a mapping')
    result = {}
    for side in ['asks', 'bids']:
        rows = value.get(side)
        if not isinstance(rows, (list, tuple)) or not rows:
            raise ValueError(f'{name} missing {side}')
        clean = []
        for row in rows:
            if not isinstance(row, (list, tuple)) or len(row) != 2:
                raise ValueError(f'{name} invalid depth level')
            price, quantity = (_d(row[0], name+' price', positive=True),
                               _d(row[1], name+' quantity', positive=True))
            if clean and not (price > clean[-1][0] if side == 'asks' else price < clean[-1][0]):
                raise ValueError(f'{name} duplicate or unordered {side}')
            clean.append((price, quantity))
        result[side] = clean
    if result['bids'][0][0] >= result['asks'][0][0]:
        raise ValueError(f'{name} crossed or locked book')
    return result


def _take(levels, quantity, multiplier=ONE):
    remaining, notional, used = quantity, ZERO, 0
    for price, available in levels:
        take = min(available, remaining)
        if take > 0:
            notional += take * multiplier * price
            remaining -= take
            used += 1
        if remaining == 0:
            return notional, used
    raise ValueError('insufficient displayed depth; extrapolation is forbidden')


def _ceil_step(value, step):
    return (value / step).to_integral_value(rounding=ROUND_CEILING) * step


@_precise
def size_hedge(*, spot_book, future_book, spot_rules, future_rules, capital,
               reserve_fraction, fee_multiplier, future_multiplier='1',
               spot_fee='0.001', future_entry_fee='0.0005', future_expiry_fee='0.0005'):
    """Largest futures-lot hedge fitting budget, depth and order upper bounds.

    Minimum filters are checked AFTER monotone upper-bound/budget search. They
    must not turn low-size failures into a false 'nothing feasible' search. Spot
    purchase is grossed up for BASE commission and rounded upward to its step;
    the nonnegative excess spot is retained and valued in terminal_case.
    """
    c = _d(capital, 'capital', positive=True)
    m = _d(future_multiplier, 'future multiplier', positive=True)
    scale = _d(fee_multiplier, 'fee multiplier', positive=True)
    sf = _d(spot_fee, 'spot fee', nonnegative=True) * scale
    ef = _d(future_entry_fee, 'future entry fee', nonnegative=True) * scale
    xf = _d(future_expiry_fee, 'future expiry fee', nonnegative=True) * scale
    if any(rate >= 1 for rate in (sf, ef, xf)):
        raise ValueError('fee rates must be below one')
    numerator, denominator, reserve_label = _fraction(reserve_fraction)
    rn, rd = Decimal(numerator), Decimal(denominator)
    spot, future = _book(spot_book, 'spot'), _book(future_book, 'future')
    sr, fr = _rules(spot_rules, 'spot'), _rules(future_rules, 'future')
    spot_depth = sum((x[1] for x in spot['asks']), ZERO)
    future_depth = sum((x[1] for x in future['bids']), ZERO)
    step = fr['step_size']
    upper = int((min(future_depth, fr['max_qty']) / step).to_integral_value(rounding=ROUND_FLOOR))
    base = dict(status='unavailable', model=MODEL, capital=_s(c),
                reserve_fraction=reserve_label, reserve_numerator=numerator,
                reserve_denominator=denominator, fee_multiplier=_s(scale),
                spot_entry_fee_rate=_s(sf), spot_exit_fee_rate=_s(sf),
                future_entry_fee_rate=_s(ef), future_expiry_fee_rate=_s(xf),
                future_multiplier=_s(m), initial_top_spot_ask=_s(spot['asks'][0][0]),
                fee_status='registered_assumptions_not_verified_account_rates',
                fee_rounding='unrounded_scenario_no_exchange_rounding_claim',
                decimal_precision=PRECISION, executable_admission=False,
                future_entry_principal_cashflow='0')

    def candidate(lots):
        contracts = Decimal(lots) * step
        q = contracts * m
        gross = _ceil_step(q / (ONE - sf), sr['step_size'])
        reasons = []
        if contracts > future_depth:
            reasons.append('future_depth')
        if contracts > fr['max_qty']:
            reasons.append('future_max_qty')
        if gross > spot_depth:
            reasons.append('spot_depth')
        if gross > sr['max_qty']:
            reasons.append('spot_max_qty')
        if reasons:
            return None, reasons
        a, spot_levels = _take(spot['asks'], gross)
        b, future_levels = _take(future['bids'], contracts, m)
        if sr['max_notional'] is not None and a > sr['max_notional']:
            reasons.append('spot_max_notional')
        if fr['max_notional'] is not None and b > fr['max_notional']:
            reasons.append('future_max_notional')
        entry_fee = b * ef
        required_numerator = (a + entry_fee) * rd + b * rn
        if required_numerator > c * rd:
            reasons.append('capital_budget')
        values = (contracts, q, gross, a, b, entry_fee, required_numerator, spot_levels, future_levels)
        return values, reasons

    lo, hi = 0, upper
    while lo < hi:
        mid = (lo + hi + 1) // 2
        _, reasons = candidate(mid)
        if reasons:
            hi = mid - 1
        else:
            lo = mid
    if lo == 0:
        _, constraints = candidate(1)
        return dict(base, reason='no positive supported lot fits budget/depth/order limits',
                    binding_constraints=constraints, depth_limited=any(x.endswith('_depth') for x in constraints))
    values, reasons = candidate(lo)
    assert values is not None and not reasons
    contracts, q, gross, a, b, entry_fee, required_numerator, spot_levels, future_levels = values
    minimum_failures = []
    for label, qty, notional, rules in [('spot', gross, a, sr), ('future', contracts, b, fr)]:
        if qty < rules['min_qty']:
            minimum_failures.append(label+'_min_qty')
        if notional < rules['min_notional']:
            minimum_failures.append(label+'_min_notional')
    if minimum_failures:
        return dict(base, reason='maximum affordable hedge fails minimum order filters',
                    binding_constraints=minimum_failures, depth_limited=False)
    _, constraints = candidate(lo + 1)
    h = gross * (ONE - sf)
    reserve = b * rn / rd
    unused = (c * rd - required_numerator) / rd
    return dict(base, status='complete', reason=None,
                future_lots=lo, future_contracts=_s(contracts), future_base_quantity=_s(q),
                spot_gross_quantity=_s(gross), spot_entry_base_fee=_s(gross * sf),
                spot_net_quantity=_s(h), residual_base_quantity=_s(h - q),
                spot_entry_cost=_s(a), spot_entry_base_fee_quote_equivalent=_s(a * sf),
                future_entry_notional=_s(b), future_entry_cash_fee=_s(entry_fee),
                reserve_committed=_s(reserve), reserve_cash_numerator=_s(b * rn),
                entry_cash_required=_s(required_numerator / rd), uncommitted_cash=_s(unused),
                spot_entry_vwap=_s(a / gross), future_entry_vwap=_s(b / q),
                spot_ask_levels_used=spot_levels, future_bid_levels_used=future_levels,
                binding_constraints=constraints,
                depth_limited=any(x.endswith('_depth') for x in constraints),
                budget_limited='capital_budget' in constraints,
                exact_matched_base_units=(h == q))


@_precise
def terminal_case(entry, *, terminal_index_ratio, adverse_exit_bps, seconds_to_expiry,
                  cash_benchmark_annual=('0', '0.03', '0.05')):
    """Conditional terminal cash; no path, rolling NAV or futures sale proceeds.

    Future loss/gain is entry notional minus fixed units times terminal index.
    Spot residual and BASE entry commission are valued via the actual net spot
    holding; the entry base fee is never charged a second time in cash.
    """
    ratio = _d(terminal_index_ratio, 'terminal index ratio', positive=True)
    bps = _d(adverse_exit_bps, 'adverse exit basis points', nonnegative=True)
    seconds = _d(seconds_to_expiry, 'seconds to expiry', positive=True)
    if bps >= 10000:
        raise ValueError('adverse exit basis points must be below 10000')
    benchmarks = [_d(v, 'cash benchmark', nonnegative=True) for v in cash_benchmark_annual]
    if len(set(benchmarks)) != len(benchmarks):
        raise ValueError('duplicate cash benchmark')
    if entry.get('status') != 'complete':
        if entry.get('status') != 'unavailable' or not entry.get('reason'):
            raise ValueError('invalid entry status')
        return dict(entry, terminal_index_ratio=_s(ratio), adverse_exit_bps=_s(bps),
                    seconds_to_expiry=_s(seconds))
    # Entries are produced here at precision 80, so do not apply the external
    # forty-significant-digit input bound to the module's own repeating ratios.
    def number(key):
        value = Decimal(entry[key])
        if not value.is_finite():
            raise ValueError('invalid entry '+key)
        return value
    c, q, h = number('capital'), number('future_base_quantity'), number('spot_net_quantity')
    a, b, ef = number('spot_entry_cost'), number('future_entry_notional'), number('future_entry_cash_fee')
    x = number('initial_top_spot_ask') * ratio
    s = x * (ONE - bps / Decimal(10000))
    future_pnl = b - q * x
    spot_gross = h * s
    spot_exit_fee = spot_gross * number('spot_exit_fee_rate')
    expiry_fee = q * x * number('future_expiry_fee_rate')
    spot_net = spot_gross - spot_exit_fee
    profit = spot_net + future_pnl - a - ef - expiry_fee
    terminal_nav = c + profit
    rd = Decimal(entry['reserve_denominator'])
    terminal_reserve_numerator = number('reserve_cash_numerator') + (future_pnl - expiry_fee) * rd
    reserve_after = terminal_reserve_numerator / rd
    return_on_capital = profit / c
    cash_components = dict(spot_entry_principal=-a, future_entry_principal=ZERO,
                           future_entry_cash_fee=ef, spot_sale_gross=spot_gross,
                           spot_exit_fee=spot_exit_fee, spot_sale_net=spot_net,
                           future_settlement_pnl=future_pnl, future_expiry_fee=expiry_fee,
                           reserve_released=number('reserve_committed'),
                           uncommitted_cash=number('uncommitted_cash'),
                           paid_financing=ZERO, credited_interest=ZERO)
    benchmark_outputs = {}
    for rate in benchmarks:
        benchmark_profit = c * rate * seconds / YEAR_SECONDS
        benchmark_outputs[_s(rate)] = dict(cash_profit=_s(benchmark_profit),
                                          excess_cash_profit=_s(profit - benchmark_profit),
                                          excess_return_on_capital=_s(return_on_capital - rate * seconds / YEAR_SECONDS))
    return dict(entry, terminal_index_ratio=_s(ratio), adverse_exit_bps=_s(bps),
                seconds_to_expiry=_s(seconds), terminal_index=_s(x), terminal_spot_sale_price=_s(s),
                cash_components={key: _s(value) for key, value in cash_components.items()},
                net_cash_profit=_s(profit), terminal_nav=_s(terminal_nav),
                net_return_on_capital=_s(return_on_capital),
                annualized_simple_return=_s(return_on_capital * (YEAR_SECONDS / seconds)),
                benchmarks=benchmark_outputs,
                terminal_futures_reserve=_s(reserve_after),
                terminal_reserve_insufficient=(terminal_reserve_numerator < 0),
                pathwise_margin_survival_verified=False,
                terminal_residual_spot_value=_s((h - q) * s),
                cashflow_qualification='conditional_survival_unrounded_assumed_fees_no_fiat_transfer_costs')


def evaluate_case(*, terminal_index_ratio, adverse_exit_bps, seconds_to_expiry,
                  cash_benchmark_annual=('0', '0.03', '0.05'), **entry_kwargs):
    """Convenience composition; quantity selection never sees terminal scenarios."""
    entry = size_hedge(**entry_kwargs)
    return terminal_case(entry, terminal_index_ratio=terminal_index_ratio,
                         adverse_exit_bps=adverse_exit_bps, seconds_to_expiry=seconds_to_expiry,
                         cash_benchmark_annual=cash_benchmark_annual)
