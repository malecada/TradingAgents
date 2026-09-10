"""Validate saved v2 journal measurements without reconstructing portfolios."""
from __future__ import annotations

import math
from datetime import date, datetime, timedelta

from tradingagents.monitor import metrics

# Deliberately pinned: future accounting conventions need explicit monitor support.
SUPPORTED_ACCOUNTING_VERSION = 'pretrade-nav-v1'
WARMUP_RETURNS = 20


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def finite_tree(value):
    if isinstance(value, dict):
        return all(finite_tree(v) for v in value.values())
    if isinstance(value, list):
        return all(finite_tree(v) for v in value)
    return not isinstance(value, float) or math.isfinite(value)


def quantities(value):
    return isinstance(value, dict) and all(isinstance(k, str) and number(v) for k, v in value.items())


def calendar(rows):
    """Daily reporting clock; a missing record remains an explicit None."""
    if not rows:
        return []
    days = [date.fromisoformat(row['asof']) for row in rows]
    by_day = {row['asof']: row for row in rows}
    start, end = min(days), max(days)
    return [((start + timedelta(days=i)).isoformat(), by_day.get((start + timedelta(days=i)).isoformat()))
            for i in range((end-start).days + 1)]


def record_error(rows, *, duplicates=True, paper=False):
    if any(type(r.get('journal_version')) is not int or r['journal_version'] != 2 for r in rows):
        return 'mixed or unsupported journal versions'
    if paper and any(r.get('accounting_version') != SUPPORTED_ACCOUNTING_VERSION for r in rows):
        return 'mixed, missing or unsupported paper accounting versions'
    if any(not finite_tree(r) for r in rows):
        return 'nonfinite journal value'
    if duplicates and len({r['asof'] for r in rows}) != len(rows):
        return 'duplicate journal dates'
    if paper and any(r.get('measurement_status') not in ('complete', 'incomplete') or
                     ('measurement_reason' in r and r['measurement_reason'] is not None and
                      not isinstance(r['measurement_reason'], str)) for r in rows):
        return 'invalid paper measurement metadata'
    if any((paper or 'weights' in r) and not quantities(r.get('weights')) for r in rows):
        return 'invalid target-weight mapping'
    return None


def state(value):
    return (isinstance(value, dict) and number(value.get('nav')) and value['nav'] > 0
            and quantities(value.get('notionals')))


def close(a, b):
    return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-12)


def flow_matches(value, ret):
    return (isinstance(value, dict) and all(number(value.get(k)) for k in ('net', 'gross', 'carry', 'cost', 'turnover'))
            and value['cost'] >= 0 and value['turnover'] >= 0
            and close(value['net'], ret) and close(value['gross'] + value['carry'] - value['cost'], ret))


def paper_stream(rows, *, overlay=False, invalid_reason=None):
    """Observe contiguous net/state pairs; unknown intervals never reconnect."""
    fatal = invalid_reason or record_error(rows, paper=True)
    status, reason = ('invalid', fatal) if fatal else ('warmup', 'initial measurement')
    ret_key = 'realized_net_ret' if overlay else 'realized_base_net_ret'
    prefix = 'overlay' if overlay else 'base'
    points, observed = [], []
    anchor = previous_nav = previous = None
    started = False
    broken = bool(fatal)
    for i, (day, row) in enumerate(calendar(rows)):
        value = None
        if not broken:
            issue = None
            current = row.get(prefix + '_state') if row else None
            if row is None:
                issue = 'missing daily journal record'
            elif not state(current):
                issue = f'{prefix} state unavailable or invalid'
            elif row.get('measurement_status') not in {'complete', 'incomplete'}:
                issue = 'measurement status unavailable'
            elif 'executed_scale' not in row or (row['executed_scale'] is not None and
                                                (not number(row['executed_scale']) or row['executed_scale'] < 0)):
                issue = 'executed scale unavailable or invalid'
            elif row.get('mark_coverage') != 'complete':
                issue = row.get('measurement_reason') or 'current quote coverage incomplete'
            else:
                ret = row.get(ret_key)
                measure = row.get(prefix + '_measurement')
                if ret_key not in row or prefix + '_measurement' not in row:
                    issue = f'{prefix} measurement fields unavailable'
                elif i == 0:
                    if ret is not None or measure is not None or any(current['notionals'].values()):
                        issue = 'first record is not a flat initial measurement'
                    else:
                        anchor = previous_nav = current['nav']
                        value = 100.
                else:
                    had_scale = previous.get('executed_scale') is not None
                    warmup = not started and not had_scale
                    started = started or had_scale
                    if overlay and warmup:
                        if (ret is not None or measure is not None or not close(current['nav'], previous_nav)
                                or any(current['notionals'].values())):
                            issue = 'overlay warmup state is not an observed flat account'
                        else:
                            value = (current['nav'] / anchor) * 100.
                            reason = 'overlay scale warmup; no measured overlay returns'
                    elif overlay and not had_scale:
                        issue = 'overlay scale unavailable after measurement started'
                    elif not number(ret) or ret <= -1:
                        issue = f'{prefix} net return unavailable or invalid'
                    elif not flow_matches(measure, ret) or not close(current['nav']/previous_nav - 1., ret):
                        issue = f'{prefix} return/state accounting mismatch'
                    elif row['measurement_status'] != 'complete' and not warmup:
                        issue = row.get('measurement_reason') or 'journal measurement incomplete'
                    else:
                        value = (current['nav'] / anchor) * 100.
                        observed.append(measure)
                        status, reason = 'corrected_v2', None
                    previous_nav = current['nav']
                previous = row
            if issue:
                status, reason, broken = 'incomplete', f'{day}: {issue}', True
                value = None
        points.append({'ts': day, 'value': value})
    return dict(points=points, status=status, reason=reason, observed=observed)


def observation_timestamp(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        return parsed.tzinfo is not None and parsed.utcoffset() is not None
    except ValueError:
        return False


def account_stream(rows, *, invalid_reason=None):
    """Reconciliation updates share a cycle timestamp; dates alone prove nothing."""
    fatal = invalid_reason or record_error(rows, duplicates=False)
    latest = {}
    seen = set()
    for row in rows:
        if not isinstance(row.get('executed_utc'), str) or not isinstance(row.get('status'), str):
            fatal = fatal or 'malformed execution observation metadata'
            latest[row['asof']] = row
            continue
        key = (row['asof'], row.get('executed_utc'), row.get('status'))
        if key in seen:
            fatal = fatal or 'duplicate execution reconciliation record'
        seen.add(key)
        latest[row['asof']] = row
    final = list(latest.values())
    points, verified = [], []
    anchor = None
    broken = bool(fatal)
    status, reason = ('invalid', fatal) if fatal else ('incomplete', 'no reconciled execution measurements')
    for day, row in calendar(final):
        value = None
        if not broken:
            issue = None
            if row is None:
                issue = 'missing daily execution measurement'
            elif row.get('status') in {'intent', 'pending'}:
                status, issue = 'pending', 'execution has not reconciled'
            elif row.get('status') != 'reconciled' or row.get('dry_run') is not False:
                issue = 'execution is incomplete or was only a dry run'
            elif not observation_timestamp(row.get('executed_utc')):
                issue = 'execution observation timestamp unavailable'
            elif not quantities(row.get('actual_positions')) or not quantities(row.get('target_qty')) or row.get('residual_qty') != {}:
                issue = 'reconciled positions or zero residual confirmation unavailable'
            elif any(not math.isclose(row['actual_positions'].get(k, 0), row['target_qty'].get(k, 0), abs_tol=1e-9)
                     for k in set(row['actual_positions']) | set(row['target_qty'])):
                issue = 'actual positions do not reconcile to intended quantities'
            elif not number(row.get('equity_before')) or row['equity_before'] <= 0:
                issue = 'account equity unavailable or invalid'
            else:
                anchor = anchor or row['equity_before']
                value = (row['equity_before'] / anchor) * 100.
                verified.append(row)
                status, reason = 'reconciled', None
            if issue:
                status = 'pending' if status == 'pending' else 'incomplete'
                reason, broken = f'{day}: {issue}', True
        points.append({'ts': day, 'value': value})
    return dict(points=points, status=status, reason=reason, verified=verified, cycles=final)


def status_fields(stream):
    return {'measurement_status': stream['status'], 'measurement_reason': stream['reason']}


def derive_book(rows, scale_key, *, invalid_reason=None):
    if not rows or (all(r.get('journal_version') is None for r in rows) and not invalid_reason):
        return None
    stream = paper_stream(rows, invalid_reason=invalid_reason)
    equity, measured = stream['points'], stream['observed']
    complete = stream['status'] == 'corrected_v2'
    values = [p['value'] for p in equity]
    good_prefix = []
    for point in equity:
        if point['value'] is None:
            break
        good_prefix.append(point)
    drawdown = metrics.drawdown_series(good_prefix)
    drawdown.extend({'ts': p['ts'], 'value': None} for p in equity[len(good_prefix):])
    returns = [m['net'] for m in measured]
    sharpe = None
    if complete and len(returns) >= 2 and max(returns) != min(returns):
        sharpe = round(metrics.sharpe(values), 2)
    return dict(equity=equity, drawdown=drawdown,
        rolling_sharpe=metrics.rolling_sharpe(good_prefix, 30), slippage=None,
        **status_fields(stream), cards={
            **status_fields(stream), 'cum_return': values[-1]/100.-1. if complete else None,
            'sharpe': sharpe, 'max_drawdown': round(metrics.max_drawdown(values), 4) if complete else None,
            'scale': rows[-1].get('executed_scale') if number(rows[-1].get('executed_scale')) else None,
            'warmup': {'n': len(measured), 'required': WARMUP_RETURNS},
            'avg_turnover': sum(m['turnover'] for m in measured)/len(measured) if complete else None,
            'cum_cost': sum(m['cost'] for m in measured) if complete else None,
            'last_asof': rows[-1]['asof'], 'n_days': len(equity)})


def derive_nav(rows, scale_key, *, invalid_reason=None):
    if not rows or (all(r.get('journal_version') is None for r in rows) and not invalid_reason):
        return None
    stream = paper_stream(rows, overlay=True, invalid_reason=invalid_reason)
    complete = stream['status'] == 'corrected_v2'
    base = paper_stream(rows, invalid_reason=invalid_reason)
    return dict(series=stream['points'], **status_fields(stream), cards={
        **status_fields(stream), 'nav_cum_return': stream['points'][-1]['value']/100.-1. if complete else None,
        'active_days': len(stream['observed']),
        'warmup': {'n': len(base['observed']), 'required': WARMUP_RETURNS},
        'last_scale': rows[-1].get('executed_scale') if number(rows[-1].get('executed_scale')) else None,
        'last_applied_scale': rows[-1].get('measurement_scale') if number(rows[-1].get('measurement_scale')) else None})


def derive_account(rows, halted, *, invalid_reason=None, empty_status=None):
    if not rows and not empty_status and not invalid_reason:
        return None
    if rows and all(r.get('journal_version') is None for r in rows) and not invalid_reason:
        stream = dict(points=[], verified=[], cycles=rows, status='legacy_only',
                      reason='legacy account dates do not establish reconciled execution')
    else:
        stream = account_stream(rows, invalid_reason=invalid_reason)
    if not rows:
        stream.update(status='invalid' if invalid_reason else empty_status,
                      reason=invalid_reason or 'v2 account journal has no reconciled observations')
    complete = stream['status'] == 'reconciled'
    verified, cycles = stream['verified'], stream['cycles']
    reconciliation = dict(reconciliation_status=stream['status'], reconciliation_reason=stream['reason'])
    return dict(series=stream['points'], **status_fields(stream), **reconciliation, cards={
        **reconciliation,
        **status_fields(stream), 'cum_return': stream['points'][-1]['value']/100.-1. if complete and len(verified) > 1 else None,
        'equity': verified[-1]['equity_before'] if complete else None,
        'n_cycles': len(cycles),
        'orders_total': sum(r['orders_filled'] for r in verified) if complete and all(number(r.get('orders_filled')) for r in verified) else None,
        'last_asof': cycles[-1]['asof'] if cycles else None,
        'dry_run_last': bool(cycles[-1].get('dry_run')) if cycles else None, 'halted': halted})
