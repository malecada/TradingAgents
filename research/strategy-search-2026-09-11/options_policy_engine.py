"""Invented hourly unit-one short-straddle ledger. No data acquisition or admission."""
from fractions import Fraction as F
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
import math


MAX_RATIONAL_BITS = 4096


class ArithmeticScopeError(RuntimeError):
    """Exact rational grew beyond the declared synthetic-engine scope."""


def _rational_scope(value):
    if isinstance(value, F):
        if value.numerator.bit_length() > MAX_RATIONAL_BITS or value.denominator.bit_length() > MAX_RATIONAL_BITS:
            raise ArithmeticScopeError('exact rational exceeds 4096-bit numerator/denominator scope; retain case unavailable')
    elif isinstance(value, dict):
        for item in value.values(): _rational_scope(item)
    elif isinstance(value, list):
        for item in value: _rational_scope(item)


def number(value, *, positive=False, nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise ValueError('explicit finite decimal string/integer required')
    text = str(value)
    if len(text) > 64:
        raise ValueError('numeric scope exceeds 64 characters')
    d = Decimal(text)
    if not d.is_finite() or (d and not -32 <= d.adjusted() <= 32):
        raise ValueError('finite bounded decimal required')
    n = F(d)
    if positive and n <= 0 or nonnegative and n < 0:
        raise ValueError('numeric sign invalid')
    return n


def nearest_lot(value, lot):
    """Exact nearest lot; a half lot rounds toward zero."""
    sign = -1 if value < 0 else 1
    units = abs(value) / lot
    whole = units.numerator // units.denominator
    return sign * lot * (whole + (units - whole > F(1, 2)))


def _encoded(value):
    if isinstance(value, F):
        _rational_scope(value)
        return str(value)
    if isinstance(value, dict):
        return {k: _encoded(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_encoded(v) for v in value]
    return value


def deficit(values):
    if any(value is not None and value < 0 for value in values):
        return True
    return None if any(value is None for value in values) else False


def log_fraction(value):
    # math.log accepts arbitrary-size positive integers without float conversion.
    # Taking logs separately avoids ratio underflow after exact cancellation.
    return math.log(value.numerator) - math.log(value.denominator)


def ledger(records, *, capital, option_quantity, costs, hedge_lot,
           hedge_min_quantity, hedge_min_notional, expected_funding_times, funding_events):
    """Explicit hourly records; missing decisions never generate a substitute trade.

    Every record: integer time_ms and typed entry_available/hedge_available/
    exit_available for its phase, or decision_available fallback; index and
    call/put/perp dictionaries as proposed API. Missing marks may be None.
    Funding events: time_ms, rate, mark. The expected calendar is caller supplied,
    not inferred from observed events. Outputs use exact rational strings.
    """
    C = number(capital, positive=True); q = number(option_quantity, positive=True)
    lot = number(hedge_lot, positive=True)
    minq = number(hedge_min_quantity, nonnegative=True)
    minn = number(hedge_min_notional, nonnegative=True)
    if set(costs) != {'option_fee_rate', 'perp_fee_rate', 'perp_slippage', 'option_tick_worsening'}:
        raise ValueError('all four explicit cost parameters required')
    ofee, pfee, slip, tick = [number(costs[k], nonnegative=True) for k in
        ('option_fee_rate', 'perp_fee_rate', 'perp_slippage', 'option_tick_worsening')]
    if slip >= 1 or ofee >= 1 or pfee >= 1:
        raise ValueError('cost fraction outside scope')
    times = [r['time_ms'] for r in records]
    if not 2 <= len(times) <= 1057 or any(type(t) is not int or t < 0 for t in times) or any(b-a != 3600000 for a,b in zip(times,times[1:])):
        raise ValueError('complete hourly record denominator required, including missing placeholders')
    for i, r in enumerate(records):
        phase = 'entry_available' if i == 0 else 'exit_available' if i == len(records)-1 else 'hedge_available'
        if type(r.get(phase, r.get('decision_available'))) is not bool:
            raise ValueError('typed phase availability or decision fallback required')
        for key in ('valuation_available', 'option_valuation_available', 'perp_valuation_available'):
            if key in r and type(r[key]) is not bool:
                raise ValueError('typed valuation availability required')
    actions = [r.get('action_time_ms', r['time_ms']) for r in records]
    if any(type(a) is not int or not t <= a <= t+5000 for t,a in zip(times,actions)):
        raise ValueError('action time must be an integer within nominal slot plus 5000ms')
    start, end = actions[0], actions[-1]
    expected = list(expected_funding_times)
    if any(type(t) is not int or not times[0] <= t <= end for t in expected) or expected != sorted(set(expected)):
        raise ValueError('explicit unique ordered in-window funding calendar required')
    events = {}
    for e in funding_events:
        t = e['time_ms']
        if type(t) is not int or t not in expected or t in events:
            raise ValueError('unexpected or duplicate funding event')
        events[t] = (number(e['rate']), number(e['mark'], positive=True))
    missing = [t for t in expected if t > start and t not in events]
    ocash, pcash, idle = C*F(2,5), C/2, C/10
    h, execution_offset = F(0), F(0)
    fees, funding, premium, buyback = F(0), F(0), F(0), F(0)
    ofees, pfees, turnover = F(0), F(0), F(0)
    trace, trades, funding_trace = [], [], []
    active = False; closed = False; lasttime = start
    unknown_funding = False

    def quote(row, side):
        obj = row[side]
        if side in ('call', 'put') and (type(obj.get('unit')) is not int or obj['unit'] != 1):
            raise ValueError('explicit option unit one required')
        bid, ask = number(obj['bid'], positive=True), number(obj['ask'], positive=True)
        if bid > ask: raise ValueError('crossed quote')
        return bid, ask, number(obj['bid_qty'], nonnegative=True), number(obj['ask_qty'], nonnegative=True)

    def option_prices(row, closing):
        index = number(row['index'], positive=True)
        prices = []
        for side in ('call', 'put'):
            bid, ask, bq, aq = quote(row, side)
            price, size = (ask+tick, aq) if closing else (bid-tick, bq)
            if price <= 0 or size < q: raise ValueError('option execution unavailable')
            prices.append((price, min(ofee*index, price/10)*q))
        return prices

    def execute(row, target, terminal=False):
        nonlocal h, execution_offset, pcash, fees, pfees, turnover
        change = target-h
        if not change: return 'unchanged'
        bid, ask, bq, aq = quote(row, 'perp')
        price = ask*(1+slip) if change > 0 else bid*(1-slip)
        if abs(change) < minq or abs(change)*price < minn:
            return 'minimum_order_unavailable' if terminal else 'minimum_order_no_trade'
        if abs(change) > (aq if change > 0 else bq): return 'hedge_size_unavailable'
        # Offset is a valuation identity, never credited as notional wallet cash.
        offset_change = -change*price
        execution_offset += offset_change
        h += change
        fee = abs(change)*price*pfee
        pcash -= fee; fees += fee; pfees += fee
        turnover += abs(change)*price
        trades.append({'time_ms':row['time_ms'],'action_time_ms':row.get('action_time_ms',row['time_ms']),
                       'quantity':change,'price':price,'execution_offset_change':offset_change,
                       'fee':fee,'terminal':terminal})
        return 'traded'

    for i,row in enumerate(records):
        nominal = row['time_ms']; t = actions[i]; terminal = i == len(records)-1
        for ft in expected:
            if not lasttime < ft <= t: continue
            if ft not in events:
                funding_trace.append({'time_ms':ft,'inventory':h,'status':'missing','cash':None})
                if h: unknown_funding = True
            else:
                rate, mark = events[ft]; cash = -h*mark*rate
                pcash += cash; funding += cash
                funding_trace.append({'time_ms':ft,'inventory':h,'status':'known','cash':cash})
        reason = None; decision = 'no_trade'; desired = None
        try:
            phase = 'entry_available' if i == 0 else 'exit_available' if terminal else 'hedge_available'
            if not row.get(phase, row.get('decision_available')): raise ValueError('missing_or_stale_' + phase)
            if i == 0:
                prices = option_prices(row, False)
                # Validate hedge signal/executable schema before opening either option.
                desired = q*(number(row['call']['delta'])+number(row['put']['delta']))
                target = nearest_lot(desired, lot)
                quote(row,'perp')
                for price,fee in prices:
                    ocash += q*price-fee; premium += q*price; fees += fee; ofees += fee
                active = True
                decision = execute(row,target)
            elif terminal and active:
                prices = option_prices(row, True)
                # All terminal sides are checked before changing either wallet.
                if h:
                    bid,ask,bq,aq = quote(row,'perp')
                    px = bid*(1-slip) if h>0 else ask*(1+slip)
                    if abs(h)<minq or abs(h)*px<minn or abs(h)>(bq if h>0 else aq):
                        raise ValueError('terminal hedge execution unavailable')
                decision = execute(row,F(0),True)
                for price,fee in prices:
                    ocash -= q*price+fee; buyback += q*price; fees += fee; ofees += fee
                active = False; closed = True
            elif active:
                desired = q*(number(row['call']['delta'])+number(row['put']['delta']))
                target = nearest_lot(desired, lot)
                decision = execute(row,target)
        except (KeyError, TypeError, ValueError, ArithmeticError) as exc:
            reason = str(exc) or type(exc).__name__; decision = 'unavailable_no_trade'
        liability = F(0) if not active else None
        total_pnl = execution_offset if not h else None
        try:
            if active and row.get('option_valuation_available', row.get('valuation_available', True)): liability = q*(number(row['call']['mark'],nonnegative=True)+number(row['put']['mark'],nonnegative=True))
        except (KeyError,TypeError,ValueError,ArithmeticError): pass
        try:
            if h and row.get('perp_valuation_available', row.get('valuation_available', True)): total_pnl = execution_offset+h*number(row['perp']['mark'],positive=True)
        except (KeyError,TypeError,ValueError,ArithmeticError): pass
        nav = idle+ocash+pcash-liability+total_pnl if liability is not None and total_pnl is not None and not unknown_funding else None
        trace.append({'time_ms':nominal,'action_time_ms':t,'decision':decision,'reason':reason,'option_quantity':-q if active else F(0),
                      'desired_model_hedge':desired,'model_hedge_residual':None if desired is None else h-desired,
                      'hedge_quantity':h,'perp_execution_offset_uncredited':execution_offset,
                      'perp_realized_cash_while_open':'unavailable' if h else 'flat_total_pnl_known','option_cash':ocash,'perp_cash_known_component':pcash,
                      'idle_cash':idle,'option_liability':liability,'perp_total_pnl_known':total_pnl,'nav':nav,
                      'funding_cash_complete':not unknown_funding,'option_wallet_equity':None if liability is None else ocash-liability,
                      'perp_wallet_equity':None if total_pnl is None or unknown_funding else pcash+total_pnl})
        _rational_scope(trace[-1])
        if trades: _rational_scope(trades[-1])
        _rational_scope([fees, funding, execution_offset, premium, buyback, ofees, pfees, turnover])
        lasttime = t
    # Missing scheduled funding is never replaced by zero, even if inventory was zero.
    valid = closed and not missing
    final = idle+ocash+pcash+execution_offset if valid else None
    navs = [C]+[r['nav'] for r in trace]
    returns = None
    if all(n is not None and n>0 for n in navs):
        returns = [b/a-1 for a,b in zip(navs,navs[1:])]
    dd = None
    if all(n is not None for n in navs):
        peak = C; dd = F(0)
        for n in navs: peak=max(peak,n); dd=max(dd,(peak-n)/peak)
    arithmetic_shadow = None
    if returns is not None:
        with localcontext() as context:
            context.prec = 60
            context.rounding = ROUND_HALF_EVEN
            arithmetic_shadow = str(sum((Decimal(r.numerator)/Decimal(r.denominator) for r in returns), Decimal(0)))
    result = {'status':'conditional_cash_complete' if valid else 'financial_result_unavailable',
              'initial':{'capital':C,'option_wallet':C*F(2,5),'perp_wallet':C/2,'idle':C/10,'option_quantity_each':q,'unit':1,'account':'empty'},
              'trace':trace,'trades':trades,'funding_events':funding_trace,'missing_funding_times':missing,
              'initial_zero_inventory_funding_times':[t for t in expected if t<=start],
              'final':{'closed':closed,'cash':final,'profit':None if final is None else final-C,'full_capital_return':None if final is None else final/C-1},
              'cash_components':{'premium':premium,'option_buyback':buyback,'option_fees':ofees,'perp_fees':pfees,'all_fees':fees,'perp_realized':execution_offset if not h else None,
                                 'perp_execution_offset_uncredited':execution_offset,
                                 'perp_cash_component_scope':'initial reserve plus known funding minus fees; execution offset is not cash proceeds or withdrawable cash while open','known_funding':funding,'perp_turnover':turnover},
              'metrics':{'duration_ms':end-start,'duration_scope':'actual declared entry-to-exit action clocks; invented execution boundary',
                         'annualized_simple_return':None if final is None else (final/C-1)*F(365*86400000,end-start),
                         'cash_benchmarks':{str(rate):C*(1+rate*F(end-start,365*86400000)) for rate in (F(0),F(3,100),F(5,100))},
                         'missed_decisions':sum(r['decision']=='unavailable_no_trade' for r in trace)},
              'risk':{'minimum_option_cash':min(r['option_cash'] for r in trace),
                      'minimum_known_perp_cash_component':min(r['perp_cash_known_component'] for r in trace),
                      'minimum_option_wallet_equity':None if any(r['option_wallet_equity'] is None for r in trace) else min(r['option_wallet_equity'] for r in trace),
                      'minimum_perp_wallet_equity':None if any(r['perp_wallet_equity'] is None for r in trace) else min(r['perp_wallet_equity'] for r in trace),
                      'max_drawdown':dd,'option_wallet_deficit':deficit([r['option_wallet_equity'] for r in trace]),
                      'perp_wallet_deficit':deficit([r['perp_wallet_equity'] for r in trace]),
                      'actual_margin_and_access':'unavailable','intrahour_risk':'unavailable'},
              'convention_diagnostic':{'arithmetic_return_sum':arithmetic_shadow,
                 'arithmetic_precision':'60 significant decimal digits, ROUND_HALF_EVEN approximate noncash diagnostic only',
                 'log_return_sum':None if returns is None else sum(log_fraction(b)-log_fraction(a) for a,b in zip(navs,navs[1:])),
                 'scope':'NAV convention diagnostic only; logs are never booked as cash PnL'},
              'scope':'Invented unit-one quote-side fills and model deltas; fixed reserves are not actual margin admission. No beta, expected-return inference or graduation.'}
    return _encoded(result)
