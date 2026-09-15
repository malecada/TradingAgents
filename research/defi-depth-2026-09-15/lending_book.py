"""Pure conditional F1 cash book; no acquisition or empirical entry point.

Scaled aToken atoms are a distinct claim. Index growth changes its entitlement;
no APR or index increment is also paid as a cash distribution. Observed cash is
only a snapshot withdrawal constraint, not solvency or execution assurance.
"""
from fractions import Fraction as F
from decimal import Decimal
from datetime import date, timedelta
import importlib.util
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent

def module(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE / file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

W = module('lending_wallet_helpers', 'wrapper_book.py')
L = module('lending_integer_model', 'lending_math.py')
R = module('lending_literal_receipts', 'literal_receipts.py')
ASSETS = {a: W.ASSETS[a] for a in ('USDC', 'ETH')}
ASSETS['AUSDC_SCALED'] = ('base', '0x4e65fe4dba92790696d040ac24aa414708f5c0ab:scaled')
CAPITAL, RESERVE = W.CAPITAL, W.RESERVE
FinancialUnavailable = W.FinancialUnavailable


def amounts(book):
    out = {}
    for asset, key in ASSETS.items():
        q = book.balances.get(key, Decimal(0))
        if q != int(q):
            raise ValueError('noninteger ledger atoms')
        out[asset] = int(q)
    return out


def entitlement(q, row):
    return L.ray_mul(q['AUSDC_SCALED'], row['income']) if q['AUSDC_SCALED'] else 0


def mark(q, row):
    p = row['prices']
    return F(q['USDC'] + entitlement(q, row), 10**6) * p['USDC'] + F(q['ETH'], 10**18) * p['ETH']


def validate_panel(panel, *, operational=True):
    if len(panel) != 366:
        raise ValueError('complete fixed annual source panel required')
    previous = None
    for i, row in enumerate(panel):
        if row['date'] != (date(2025, 9, 1) + timedelta(days=i)).isoformat():
            raise ValueError('fixed calendar mismatch')
        if set(row['prices']) != {'USDC', 'ETH'} or any(
            not isinstance(v, (F, int)) or isinstance(v, bool) or v <= 0 for v in row['prices'].values()
        ):
            raise ValueError('positive exact ETH and USDC USD marks required')
        L.index(row['income'])
        if operational:
            L.configuration(row['config'])
            L.m.uint(row['contract_cash'])
        if row.get('source_model_qualified') is not True:
            raise FinancialUnavailable('source-model units and same-block bindings unqualified')
        if previous is not None and row['income'] < previous:
            raise FinancialUnavailable('decreasing normalized income outside admitted source model')
        previous = row['income']


def liquidation(q, row, cost, *, claim_factor=F(1), check_withdrawal=True):
    """Fund withdrawal and native sale entirely from held ETH; keep exact dust.

    A stress haircut changes credited claim atoms, not its scaled storage balance.
    Lock scenarios describe post-delay marked exit, never guaranteed horizon cash.
    """
    q = dict(q)
    ops = []
    if q['AUSDC_SCALED']:
        if check_withdrawal:
            try:
                gross = L.withdrawal_preview(q['AUSDC_SCALED'], row['income'], row['config'], row['contract_cash'])['underlying_credit_atoms']
            except L.SourceModelUnavailable as exc:
                raise FinancialUnavailable(str(exc)) from exc
        else:
            gross = entitlement(q, row)
        if not isinstance(claim_factor, (F, int)) or isinstance(claim_factor, bool) or not 0 <= claim_factor <= 1:
            raise ValueError('explicit claim retention between zero and one required')
        if q['ETH'] < cost['gas']:
            raise FinancialUnavailable('unfunded lending withdrawal gas')
        received = W.floor(gross * claim_factor)
        ops.append({'id': 'withdraw', 'debits': {'AUSDC_SCALED': q['AUSDC_SCALED']},
                    'credits': {'USDC': received}, 'gas': cost['gas']})
        q['AUSDC_SCALED'] = 0
        q['USDC'] += received
        q['ETH'] -= cost['gas']
    if q['ETH']:
        if q['ETH'] <= cost['gas']:
            raise FinancialUnavailable('unfunded native gas-reserve exit')
        sold = q['ETH'] - cost['gas']
        received = W.sell_value(sold, 'ETH', row['prices'], cost)
        ops.append({'id': 'native-exit', 'debits': {'ETH': sold}, 'credits': {'USDC': received}, 'gas': cost['gas']})
        q['ETH'] = 0
        q['USDC'] += received
    value = F(q['USDC'], 10**6) * row['prices']['USDC'] - cost['route']
    return value, q, ops


def stress(q, row, cost):
    origin = liquidation(q, row, cost)[0]
    if origin <= 0:
        raise ValueError('nonpositive stress origin')
    # Factors: ETH USD mark, USDC USD mark, underlying credit retention, impact, delay.
    shocks = {
        'eth-minus50': (F(1, 2), F(1), F(1), 1, 0),
        'eth-minus80': (F(1, 5), F(1), F(1), 1, 0),
        'eth-minus90': (F(1, 10), F(1), F(1), 1, 0),
        'credit-minus50': (F(1), F(1), F(1, 2), 1, 0),
        'stable-depeg-lock30': (F(1), F(4, 5), F(1), 1, 30),
        'seven-day-withdrawal-outage': (F(1, 2), F(1), F(1), 5, 7),
        'combined-credit-depeg-outage': (F(1, 10), F(4, 5), F(1, 2), 5, 30),
    }
    out = {}
    for name, (eth, usd, credit, impact, delay) in shocks.items():
        shocked = {**row, 'prices': {'ETH': row['prices']['ETH'] * eth, 'USDC': row['prices']['USDC'] * usd}}
        c = {**cost, 'adverse': cost['adverse'] * impact}
        value = liquidation(q, shocked, c, claim_factor=credit, check_withdrawal=False)[0]
        out[name] = {'loss_fraction': (origin-value)/origin, 'loss_usd': origin-value,
                     'delayed_days': delay, 'horizon_cash_unavailable_during_lock': bool(delay)}
    up = {**row, 'prices': {**row['prices'], 'ETH': row['prices']['ETH']*2}}
    down = {**row, 'prices': {**row['prices'], 'ETH': row['prices']['ETH']*F(4, 5)}}
    peak = liquidation(q, up, cost)[0]
    end = liquidation(q, down, cost)[0]
    out['double-then-minus60'] = {'loss_fraction': (origin-end)/origin, 'loss_usd': origin-end,
                                'peak_drawdown': (peak-end)/peak, 'delayed_days': 0}
    out['total-wallet-loss'] = {'loss_fraction': F(1), 'loss_usd': origin, 'separate_tail': True}
    lost = {**q, 'AUSDC_SCALED': 0}
    loss = origin - liquidation(lost, row, cost)[0]
    out['total-contract-position-loss'] = {'loss_fraction': loss/origin, 'loss_usd': loss,
        'gross_affected_mark_usd': F(entitlement(q, row), 10**6)*row['prices']['USDC'], 'separate_tail': True}
    return out


def entry_preview(amount, row, *, cap_assumption='require-proof'):
    if cap_assumption not in ('require-proof', 'assume-cap-for-diagnostic'):
        raise ValueError('explicit registered cap-assumption role required')
    cfg = L.configuration(row['config'])
    if not cfg['active'] or cfg['paused'] or cfg['frozen'] or cfg['decimals'] != 6:
        raise FinancialUnavailable('source-model deposit reserve flags unavailable')
    try:
        if cap_assumption == 'assume-cap-for-diagnostic' and cfg['supply_cap_whole_tokens']:
            result = {'sufficient_cap_pass': None, 'cap_disabled': False,
                      'cap_atoms': cfg['supply_cap_whole_tokens']*10**6,
                      'cap_unproved': True, 'scope': 'Explicit diagnostic assumption only; no cap proof'}
        else:
            result = L.supply_cap_sufficient_bound(amount, row['income'], row['config'],
                row.get('scaled_supply'), row.get('stored_treasury'), row.get('current_debt_upper_bound'),
                debt_bound_qualified=row.get('debt_bound_qualified'))
            if not result['sufficient_cap_pass']:
                raise FinancialUnavailable('sufficient cap bound inconclusive; actual cap failure not established')
        scaled = L.m.uint(L.ray_div(amount, row['income']), 128)
        if not scaled:
            raise FinancialUnavailable('deposit mints zero scaled units')
    except L.SourceModelUnavailable as exc:
        raise FinancialUnavailable(str(exc)) from exc
    return scaled, result


def run_book(panel, scenario, progress=None, *, cap_assumption='require-proof'):
    validate_panel(panel)
    if scenario not in W.SCENARIOS:
        raise ValueError('unregistered cost scenario')
    cost = W.SCENARIOS[scenario]
    p0 = panel[0]['prices']
    usdc = W.floor((CAPITAL-F(RESERVE, 10**18)*p0['ETH'])/p0['USDC']*10**6)
    if usdc <= 0:
        raise FinancialUnavailable('gas reserve exhausts capital')
    initial = {'USDC': usdc, 'ETH': RESERVE, 'AUSDC_SCALED': 0}
    book = W.M.ProtocolBook({ASSETS[a]: q for a, q in initial.items()})
    formation = CAPITAL-mark(initial, panel[0])
    states, events, maxima = [], [], {}
    market = accrual = event_loss = log_adjust = F(0)
    previous = log_error = None
    cap_check = None
    if progress is not None:
        progress.update(book=book, initial_atoms=initial, formation_loss=formation, states=states, events=events, stress_maxima=maxima)

    def checkpoint():
        if progress is not None:
            progress.update(market=market, accrual=accrual, event_loss=event_loss)

    def observe(row, phase):
        nonlocal market, accrual, previous, log_adjust, log_error
        if progress is not None:
            progress.update(current_date=row['date'], current_phase=phase, current_source_row=R.json_safe(row))
        q, p = amounts(book), row['prices']
        if previous is not None:
            oldq, oldrow = previous
            oldp = oldrow['prices']
            oldclaim = entitlement(oldq, oldrow)
            newclaim = entitlement(oldq, row)
            market += F(oldq['USDC']+oldclaim, 10**6)*(p['USDC']-oldp['USDC'])
            market += F(oldq['ETH'], 10**18)*(p['ETH']-oldp['ETH'])
            accrual += F(newclaim-oldclaim, 10**6)*p['USDC']
            components = [(F(oldq['USDC'], 10**6)*oldp['USDC'], p['USDC']/oldp['USDC']),
                          (F(oldq['ETH'], 10**18)*oldp['ETH'], p['ETH']/oldp['ETH'])]
            if oldclaim:
                components.append((F(oldclaim, 10**6)*oldp['USDC'], F(newclaim, oldclaim)*p['USDC']/oldp['USDC']))
            for value, ratio in components:
                if value and ratio != 1 and log_error is None:
                    try:
                        log_adjust += value*(F(str(math.log(float(ratio))))-(ratio-1))
                    except (ValueError, OverflowError, ZeroDivisionError) as exc:
                        log_error = type(exc).__name__+': '+str(exc)
        checkpoint()
        if progress is not None:
            progress.update(current_date=row['date'], current_phase=phase)
        value = liquidation(q, row, cost)[0]
        states.append({'date': row['date'], 'phase': phase, 'atoms': q,
            'income': row['income'], 'underlying_claim_atoms': entitlement(q, row),
            'prices': {a: W.fraction_record(p[a]) for a in p}, 'liquidation_usd': W.fraction_record(value)})
        for name, r in stress(q, row, cost).items():
            old = maxima.get(name)
            if old is None or r['loss_fraction'] > old['loss_fraction']:
                maxima[name] = {**r, 'date': row['date'], 'phase': phase}
            maxima[name]['maximum_peak_drawdown'] = max(r.get('peak_drawdown', F(0)), (old or {}).get('maximum_peak_drawdown', F(0)))
        previous = (q, row)

    def post(row, event, debits, credits, gas):
        nonlocal event_loss, previous
        before = amounts(book)
        if before['ETH'] < gas + debits.get('ETH', 0):
            raise FinancialUnavailable('prefunded gas inadequate')
        if any(v <= 0 for v in credits.values()):
            raise FinancialUnavailable('positive protocol receipt rounds to zero')
        book.convert(event, {ASSETS[a]: v for a, v in debits.items()}, {ASSETS[a]: v for a, v in credits.items()},
                     fee_key=ASSETS['ETH'], fee=gas, evidence='F1 conditional source-model conversion, not witnessed execution')
        after = amounts(book)
        loss = mark(before, row)-mark(after, row)
        event_loss += loss
        events.append({'id': event, 'date': row['date'], 'debits_atoms': debits, 'credits_atoms': credits,
                       'gas_atoms': gas, 'before_atoms': before, 'after_atoms': after, 'marked_loss_usd': W.fraction_record(loss)})
        checkpoint()
        previous = (after, row)
        observe(row, 'after-'+event)

    for i, row in enumerate(panel):
        observe(row, 'daily')
        if i == 1:
            budget = usdc*7//10
            scaled, cap_check = entry_preview(budget, row, cap_assumption=cap_assumption)
            post(row, 'supply', {'USDC': budget}, {'AUSDC_SCALED': scaled}, 2*cost['gas'])
        if i == 365:
            expected, terminal, operations = liquidation(amounts(book), row, cost)
            for op in operations:
                post(row, op['id'], op['debits'], op['credits'], op['gas'])
            if terminal != amounts(book):
                raise ValueError('terminal atom plan differs from signed book')
            ending = mark(terminal, row)-cost['route']
            if ending != expected:
                raise ValueError('terminal liquidation plan differs')
    profit = ending-CAPITAL
    reconstruction = market+accrual-event_loss-formation-cost['route']
    if reconstruction != profit:
        raise ValueError('lending cash conservation failure')
    peak, dd = CAPITAL, F(0)
    for state in states:
        value = F(state['liquidation_usd']['numerator'], state['liquidation_usd']['denominator'])
        peak = max(peak, value)
        dd = max(dd, (peak-value)/peak)
    daily = [F(s['liquidation_usd']['numerator'], s['liquidation_usd']['denominator']) for s in states if s['phase'] == 'daily']
    daily[0], daily[-1] = CAPITAL, ending
    rolling = max([F(0)]+[(daily[i-30]-daily[i])/daily[i-30] for i in range(30, len(daily))])
    numerical = max(F(0), *(r['loss_fraction'] for r in maxima.values() if not r.get('separate_tail')))
    return {'policy': 'F1', 'scenario': scenario, 'net_cash_profit_usd': W.render(profit),
        'exact_net_cash_profit': W.fraction_record(profit), 'simple_net_return': W.render(profit/CAPITAL),
        'terminal_liquidation_usd': W.render(ending), 'initial_atoms': initial, 'terminal_atoms': amounts(book),
        'entry_cap_check': cap_check, 'cap_assumption_role': cap_assumption,
        'strict_entry_cap_proved': cap_check.get('sufficient_cap_pass') is True, 'cash_attribution': {'market_usd': W.render(market),
            'interest_entitlement_change_usd': W.render(accrual), 'conversion_gas_rounding_loss_usd': W.render(event_loss),
            'formation_loss_usd': W.render(formation), 'route_usd': W.render(cost['route']),
            'reconstructed_profit': W.fraction_record(reconstruction)},
        'observed_discrete_max_drawdown': W.render(dd), 'worst_rolling_30day_loss': W.render(rolling),
        'numerical_stress_max_loss': W.render(numerical), 'absolute_floor_pass_conditional': profit >= 1000,
        'numerical_risk_pass_conditional': dd <= F(3, 10) and numerical <= F(1, 2), 'states': states, 'events': events,
        'stress': {name: {k: W.render(v) if isinstance(v, F) else v for k, v in r.items()} for name, r in maxima.items()},
        'log_convention_diagnostic': {'status': 'unavailable' if log_error else 'complete', 'reason': log_error,
            'never_booked_as_cash': True, 'difference_usd': None if log_error else W.render(log_adjust),
            'erroneous_profit_usd': None if log_error else W.render(profit+log_adjust)},
        'implementation_admitted': False, 'promotion_admitted': False, 'actual_horizon_cash_under_locks': 'unavailable',
        'scope': 'Conditional source-model interest entitlement, oracle marks and hypothetical prefunded wallet execution'}


def partial_snapshot(progress):
    out = {k: v for k, v in progress.items() if k not in ('book', 'formation_loss', 'market', 'accrual', 'event_loss')}
    for key in ('formation_loss', 'market', 'accrual', 'event_loss'):
        if key in progress:
            out[key] = W.fraction_record(progress[key])
    if 'book' in progress:
        out.update(R.snapshot(progress['book'], progress['initial_atoms'], ASSETS))
        out['valued_events_cover_literal_events'] = len(progress['events']) == len(progress['book'].events)
    return R.json_safe(out)


def opportunity_ceiling(panel):
    """Generous endpoint ceiling for this same allocation and source model only.

    Omits all fees, gas consumption, cap/withdrawal restrictions and route costs.
    Uses ceiling mint and ceiling redemption to dominate both half-up operations.
    This is a separate diagnostic; it cannot pass primary feasibility or rescue it.
    """
    if len(panel) not in (3,366):
        raise ValueError('three fixed ceiling endpoints or full annual panel required')
    start, entry, terminal = panel[0], panel[1], panel[-1]
    for row, day in zip((start,entry,terminal),('2025-09-01','2025-09-02','2026-09-01')):
        if row['date']!=day or row.get('source_model_qualified') is not True:
            raise FinancialUnavailable('fixed ceiling endpoint identity/model unavailable')
    for row in (start,terminal):
        if any(not isinstance(row['prices'][a],(F,int)) or isinstance(row['prices'][a],bool) or row['prices'][a]<=0 for a in ('USDC','ETH')):
            raise ValueError('positive exact endpoint USD marks required')
    L.index(entry['income']);L.index(terminal['income'])
    if terminal['income']<entry['income']:
        raise FinancialUnavailable('endpoint index declines outside admitted model')
    usdc = W.floor((CAPITAL-F(RESERVE,10**18)*start['prices']['ETH'])/start['prices']['USDC']*10**6)
    if usdc<=0:
        raise FinancialUnavailable('gas reserve exhausts initial capital')
    deposit=usdc*7//10
    ceiling_scaled=(deposit*L.RAY+entry['income']-1)//entry['income']
    ceiling_claim=(ceiling_scaled*terminal['income']+L.RAY-1)//L.RAY
    cash=usdc-deposit+ceiling_claim
    wealth=F(cash,10**6)*terminal['prices']['USDC']+F(RESERVE,10**18)*terminal['prices']['ETH']
    profit=wealth-CAPITAL
    return {'policy':'F1-opportunity-ceiling','exact_net_cash_profit_upper_bound':W.fraction_record(profit),
            'upper_bound_below_absolute_floor':profit<1000,'initial_usdc_atoms':usdc,
            'deposit_atoms':deposit,'ceiling_scaled_atoms':ceiling_scaled,'ceiling_terminal_claim_atoms':ceiling_claim,
            'costs_route_cap_and_withdrawal_restrictions_omitted':True,'primary_pass':False,
            'scope':'Conditional ray-index opportunity ceiling for the fixed70% allocation only; above floor is inconclusive'}
