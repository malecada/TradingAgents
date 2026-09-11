"""Pure conditional WBETH market-value hedge book; no input reads or execution."""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR
import importlib.util
import math
from pathlib import Path

_spec = importlib.util.spec_from_file_location('wbeth_saved_carry_primitives', Path(__file__).with_name('carry_book.py'))
_saved = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_saved)
COSTS = _saved.COSTS
START_MS, END_MS, DAY_MS = _saved.START_MS, _saved.END_MS, _saved.DAY_MS
WBETH_LOT, ETH_PERP_LOT = 0.0001, 0.001


def _bars(rows, traded=False):
    bars = _saved._bars(rows)
    for row in rows:
        for column in (5, 7, 9, 10):
            if _saved._finite(row[column]) < 0:
                raise ValueError('negative activity field')
        count = _saved._finite(row[8])
        if count < 0 or not count.is_integer():
            raise ValueError('nonnegative integer trade count required')
    if traded and any(_saved._finite(row[5]) <= 0 or _saved._finite(row[8]) <= 0 for row in (rows[0], rows[-1])):
        raise ValueError('entry and exit traded bars require positive volume and trade count')
    return bars


def _close(qw, qe, w_entry, f_entry, w_exit, f_exit, capital, idle, reserve, funding, costs):
    spot_fee, future_fee = qw * w_exit * costs['spot_fee'], qe * f_exit * costs['perp_fee']
    proceeds, future_pnl = qw * w_exit, qe * (f_entry - f_exit)
    future_cash = reserve + funding + future_pnl - future_fee
    final_cash = math.fsum((idle, future_cash, proceeds, -spot_fee))
    return {'wbeth_exit_price': w_exit, 'eth_perp_exit_price': f_exit,
            'wbeth_sale_proceeds': proceeds, 'wbeth_exit_fee': spot_fee, 'eth_perp_exit_fee': future_fee,
            'wbeth_price_pnl': qw * (w_exit - w_entry), 'eth_perp_price_pnl': future_pnl,
            'cumulative_funding_cash': funding, 'futures_cash_after_close': future_cash,
            'idle_cash_before_exit': idle, 'final_cash': final_cash, 'cash_profit': final_cash - capital,
            'terminal_wbeth_quantity': 0.0, 'terminal_eth_perp_quantity': 0.0}


def _book(wbeth_daily, eth_spot_daily, eth_perp_daily, eth_mark_daily, funding_events, *, capital, cost_scenario, zero_funding):
    capital = _saved._finite(capital, True)
    if capital not in (1000, 10000) or cost_scenario not in COSTS or type(zero_funding) is not bool:
        raise ValueError('only fixed capital/cost/funding scenarios are admitted')
    wb = _bars(wbeth_daily, True)
    eth, future, mark = _bars(eth_spot_daily), _bars(eth_perp_daily, True), _bars(eth_mark_daily)
    costs = dict(COSTS[cost_scenario])
    slip, sf, ff = costs['slippage'], costs['spot_fee'], costs['perp_fee']
    w_entry = _saved._finite(wb[0]['open'] * (1 + slip), True)
    f_entry = _saved._finite(future[0]['open'] * (1 - slip), True)
    # Fixed conservative formula; no search for a larger staircase-feasible lot.
    d = lambda value: Decimal(str(value))
    ratio = d(wb[0]['open']) / d(eth[0]['open'])
    denominator = d(w_entry) * (1 + d(sf)) + ratio * d(f_entry) * d(ff)
    qw = float((d(capital) * d(.4) / denominator / d(WBETH_LOT)).to_integral_value(rounding=ROUND_FLOOR) * d(WBETH_LOT))
    qe = float((d(qw) * ratio / d(ETH_PERP_LOT)).to_integral_value(rounding=ROUND_FLOOR) * d(ETH_PERP_LOT))
    _saved._finite(qw, True); _saved._finite(qe, True)
    spot_principal, spot_entry_fee, future_entry_fee = qw * w_entry, qw * w_entry * sf, qe * f_entry * ff
    reserve = .5 * capital
    spent = math.fsum((spot_principal, spot_entry_fee, future_entry_fee))
    idle = math.fsum((capital, -reserve, -spent))
    if spent > .4 * capital + 1e-10 or idle < .1 * capital - 1e-10:
        raise ValueError('joint entry spend or idle reserve fails fixed allocation')
    observed_funding, excluded = _saved._funding(funding_events, 'ETH', qe)
    funding = [[0.0 for _ in day] for day in observed_funding] if zero_funding else observed_funding
    initial = {'wbeth_quantity': qw, 'eth_perp_quantity': -qe, 'raw_wbeth_to_eth_spot_price_ratio': float(ratio),
               'assumed_wbeth_lot': WBETH_LOT, 'assumed_eth_perp_lot': ETH_PERP_LOT,
               'sizing': 'Conservative analytical joint 40% entry-budget formula, then two downward lot floors; not maximum feasible quantity.',
               'wbeth_entry_price': w_entry, 'eth_perp_entry_price': f_entry,
               'wbeth_purchase_principal': spot_principal, 'wbeth_entry_fee': spot_entry_fee,
               'eth_perp_entry_fee': future_entry_fee, 'joint_entry_spend': spent,
               'futures_reserve': reserve, 'idle_cash': idle,
               'raw_entry_net_market_value': qw * wb[0]['open'] - qe * eth[0]['open']}
    trace, cumulative = [], 0.0
    for index in range(91):
        prior = cumulative
        daily = math.fsum(funding[index])
        negative = math.fsum(cash for cash in funding[index] if cash < 0)
        cumulative = math.fsum((cumulative, daily))
        wallet = reserve + cumulative
        mtm = qe * (f_entry - mark[index]['close'])
        spot_value = qw * wb[index]['close']
        nav = math.fsum((idle, wallet, mtm, spot_value))
        margin_equity = reserve + prior + negative + qe * (f_entry - mark[index]['high'])
        maintenance = .01 * qe * mark[index]['high']
        trace.append({'date': datetime.fromtimestamp((START_MS + index * DAY_MS) / 1000, timezone.utc).date().isoformat(),
                      'wbeth_close': wb[index]['close'], 'eth_spot_close': eth[index]['close'],
                      'eth_perp_close': future[index]['close'], 'eth_mark_close': mark[index]['close'], 'eth_mark_high': mark[index]['high'],
                      'wbeth_quantity': qw, 'eth_perp_quantity': -qe,
                      'funding_event_count': len(funding[index]), 'funding_cash': daily,
                      'observed_same_quantity_funding_cash': math.fsum(observed_funding[index]),
                      'negative_funding_cash': negative, 'cumulative_funding_cash': cumulative,
                      'idle_cash': idle, 'futures_wallet': wallet, 'short_mtm': mtm, 'wbeth_value': spot_value,
                      'pre_exit_nav': nav, 'nav': nav, 'margin_equity_lower_bound': margin_equity,
                      'assumed_maintenance_requirement': maintenance, 'margin_buffer_lower_bound': margin_equity - maintenance,
                      'net_market_value': spot_value - qe * mark[index]['close'],
                      'gross_market_value': spot_value + qe * mark[index]['close']})
    final = _close(qw, qe, w_entry, f_entry, wb[-1]['close'] * (1 - slip), future[-1]['close'] * (1 + slip), capital, idle, reserve, cumulative, costs)
    final['all_fees'] = math.fsum((spot_entry_fee, future_entry_fee, final['wbeth_exit_fee'], final['eth_perp_exit_fee']))
    final['same_quantity_frictionless_price_pnl'] = math.fsum((qw * (wb[-1]['close'] - wb[0]['open']), qe * (future[0]['open'] - future[-1]['close'])))
    final['slippage_cost'] = math.fsum((qw * (w_entry - wb[0]['open']), qw * (wb[-1]['close'] - final['wbeth_exit_price']),
                                      qe * (future[0]['open'] - f_entry), qe * (final['eth_perp_exit_price'] - future[-1]['close'])))
    final['cash_profit_from_signed_components'] = math.fsum((final['wbeth_price_pnl'], final['eth_perp_price_pnl'], cumulative, -final['all_fees']))
    final['cash_reconciliation_difference'] = final['cash_profit'] - final['cash_profit_from_signed_components']
    if abs(final['cash_reconciliation_difference']) > 1e-8:
        raise ValueError('signed cash reconciliation exceeds 1e-8 USDT')
    last = trace[-1]
    last['pre_exit_components'] = {name: last[name] for name in ('nav','idle_cash','futures_wallet','short_mtm','wbeth_value','wbeth_quantity','eth_perp_quantity','net_market_value','gross_market_value')}
    last.update(nav=final['final_cash'], idle_cash=idle + final['wbeth_sale_proceeds'] - final['wbeth_exit_fee'],
                futures_wallet=final['futures_cash_after_close'], short_mtm=0.0, wbeth_value=0.0,
                wbeth_quantity=0.0, eth_perp_quantity=0.0, net_market_value=0.0, gross_market_value=0.0)
    peak, drawdown, previous = capital, 0.0, capital
    daily_returns = []
    for row in trace:
        peak = max(peak, row['nav'])
        drawdown = max(drawdown, (peak - row['nav']) / peak)
        value = row['nav'] / previous - 1 if previous > 0 else None
        row['full_capital_daily_return'] = value
        daily_returns.append(value)
        previous = row['nav']
    valid = all(value is not None and value > -1 for value in daily_returns)
    log_sum = math.fsum(math.log1p(value) for value in daily_returns) if valid else None
    arithmetic = math.fsum(daily_returns) if valid else None
    stresses = {}
    for label, w_multiple, eth_multiple in (('common_half',.5,.5),('common_double',2.,2.),('wbeth_depeg_10pct',.9,1.),('wbeth_depeg_50pct',.5,1.)):
        stress = _close(qw, qe, w_entry, f_entry, wb[0]['open'] * w_multiple * (1-slip), future[0]['open'] * eth_multiple * (1+slip), capital, idle, reserve, 0.0, costs)
        high = max(mark[0]['open'], mark[0]['open'] * eth_multiple)
        stress.update(wbeth_quantity=qw, eth_perp_quantity=-qe, wbeth_price_multiple=w_multiple, eth_price_multiple=eth_multiple,
                      margin_buffer_scenario=reserve + qe * (f_entry - high) - .01 * qe * high,
                      scope='Invented fixed-quantity, zero-funding terminal-price scenario from initial raw prices; not a guaranteed loss or liquidation bound.')
        stresses[label] = stress
    profit = final['cash_profit']
    return {'status':'conditional','asset':'WBETH-long/ETH-perp-short','capital':capital,'cost_scenario':cost_scenario,'zero_funding':zero_funding,
            'days':91,'costs':costs,'initial':initial,'daily_trace':trace,'final_ledger':final,
            'metrics':{'cash_profit':profit,'full_capital_return':profit/capital,'annualized_simple_return_365':profit/capital*365/91,
                       'max_drawdown':drawdown,'minimum_margin_buffer_lower_bound':min(row['margin_buffer_lower_bound'] for row in trace),
                       'margin_buffer_breach':any(row['margin_buffer_lower_bound']<0 for row in trace),'nonpositive_nav':any(row['nav']<=0 for row in trace),
                       'funding_cash':cumulative,'applied_funding_events':sum(len(day) for day in funding)},
            'cash_benchmarks':{str(rate):capital*rate*91/365 for rate in (0,.03,.05)},
            'excluded_first_funding_timestamps':excluded,'quantity_price_stresses':stresses,
            'true_eth_delta':{'status':'unavailable','reason':'Market-value matching does not establish contractual WBETH redemption delta or stable ETH sensitivity.'},
            'convention_diagnostic':{'status':'complete' if valid else 'unavailable','all_days':91,
                'valid_simple_index_days':sum(value is not None and value>-1 for value in daily_returns),
                'log1p_sum':log_sum,'arithmetic_daily_simple_return_sum':arithmetic,'terminal_simple_return':profit/capital,
                'invalid_log_cash_shadow':None if log_sum is None else capital*log_sum,
                'log_sum_minus_arithmetic_daily_sum':None if log_sum is None else log_sum-arithmetic,
                'label':'Log-return arithmetic booking is invalid cash PnL; actual cash is the signed final ledger.'},
            'assumptions':['WBETH quantity and short ETH quantity differ; raw entry market-value ratio is fixed with no rebalance or redemption.',
                'WBETH market appreciation combines staking, basis and depeg effects without attribution; zero funding is not pure staking.',
                'Assumed WBETH lot0.0001/ETH perpetual lot0.001, quote-currency fees and public OHLC execution; actual lots, fills and account access unverified.',
                '50% separate futures reserve, at least10% initial idle; conditional1% maintenance, daily mark high and all negative daily funding lower bound.',
                'Non-breach does not establish actual maintenance/liquidation safety; stablecoin conversion, transfers and borrowing are unmodeled.'],
            'held_zero_activity_bars':{'wbeth':sum(float(row[5])==0 or float(row[8])==0 for row in wbeth_daily),
                                       'eth_perp':sum(float(row[5])==0 or float(row[8])==0 for row in eth_perp_daily)}}


def book(wbeth_daily, eth_spot_daily, eth_perp_daily, eth_mark_daily, funding_events, *, capital, cost_scenario='base', zero_funding=False):
    """Fixed Q2 91-row Binance-style arrays and 273 ETH funding records.

    Zero funding still validates every observed event and keeps exactly the same
    entry quantities; it is a scalar-cashflow counterfactual, not another hedge.
    Invalid inputs return an explicit unavailable book for the runner denominator.
    """
    try:
        result = _book(wbeth_daily,eth_spot_daily,eth_perp_daily,eth_mark_daily,funding_events,
                       capital=capital,cost_scenario=cost_scenario,zero_funding=zero_funding)
        # Reject overflow anywhere in the output instead of emitting JSON NaN/Inf.
        def finite_tree(value):
            if isinstance(value,float) and not math.isfinite(value):
                raise ValueError('nonfinite book arithmetic')
            if isinstance(value,dict):
                for item in value.values():finite_tree(item)
            elif isinstance(value,list):
                for item in value:finite_tree(item)
        finite_tree(result)
        return result
    except (ValueError,TypeError,KeyError,IndexError,OverflowError,ArithmeticError) as exc:
        return {'status':'unavailable','reason':type(exc).__name__+': '+str(exc)}
