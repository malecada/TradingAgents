"""Observational diagnostics of saved factor traces; no strategy execution.

The target at Date[i] and its volatility use Close[i-1], and align to the
trace dated Date[i]. Date[0] is the initial valuation anchor, not a return.
Risk proxies describe requested/marked exposure times historical volatility;
they are neither realized account risk nor counterfactual trading outcomes.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


DEFAULT_POLICY = dict(volatility_lookback=20, volatility_annualization=252,
    entry_percentile=.95, entry_percentile_min_prior=20, target_vol=.10,
    kelly_fraction=.5, confidence=1., leverage_cap=3., initial_nav=10000.,
    permanent_drawdown_halt=.15, price_stop_fraction=.03,
    risk_quantiles=[.5, .9, .99], reconciliation_dollar_atol=1e-9,
    reconciliation_weight_atol=1e-12, reconciliation_rtol=1e-10)
ROW_CLASSES = ('no_trade', 'opening_from_flat', 'closing_to_flat', 'sign_flip',
               'same_sign_target_change', 'unchanged_target_maintenance')
COMPONENTS = ('gross_dollars', 'funding_dollars', 'fee_dollars', 'impact_dollars')
BOOL_COLUMNS = ('exit_executed', 'halted_before', 'price_stop_hit',
                'stop_outside_envelope', 'portfolio_stop_hit', 'halted_after')
NUM_COLUMNS = ('nav_before', 'pre_nav', 'nav_after', 'post_nav', 'target_position',
    'exposure', 'mark_return', 'mark_price', 'gross_dollars', 'funding_dollars',
    'entry_fee_dollars', 'entry_impact_dollars', 'entry_turnover_dollars',
    'exit_fee_dollars', 'exit_impact_dollars', 'exit_turnover_dollars',
    'exit_notional', 'fee_dollars', 'impact_dollars', 'turnover_dollars',
    'closing_notional', 'net_return')
QUALIFICATION = ('Saved primary sleeve only; nominal volatility proxies and dollar '
    'identities are descriptive. Proxy prices, assumed daily funding and threshold '
    'stop fills remain qualified. No alternative policy, causal effect, pooled '
    'account, new Sharpe or strategy validation is measured.')


def volatility_features(close, policy=None):
    p = DEFAULT_POLICY | (policy or {})
    close = np.asarray(close, dtype=float)
    if close.ndim != 1 or not len(close) or not np.isfinite(close).all() or (close <= 0).any():
        raise ValueError('volatility requires complete positive close observations')
    visible = np.r_[close[0], close[:-1]]
    log_ret = np.r_[np.nan, np.log(visible[1:]/visible[:-1])]
    sigma = np.full(len(close), np.nan)
    threshold = sigma.copy()
    gate = np.zeros(len(close), dtype=bool)
    for i in range(p['volatility_lookback'], len(close)):
        window = log_ret[i-p['volatility_lookback']+1:i+1]
        sigma[i] = np.std(window, ddof=1)*np.sqrt(p['volatility_annualization'])
        history = sigma[:i][np.isfinite(sigma[:i])]
        gate[i] = True
        if len(history) >= p['entry_percentile_min_prior']:
            threshold[i] = np.quantile(history, p['entry_percentile'])
            gate[i] = sigma[i] <= threshold[i]
    return pd.DataFrame(dict(sigma_252=sigma, entry_gate_threshold=threshold,
                             vol_entry_gate_open=gate))


def turnover_components(nav, held, weight, previous_weight, *, dollar_atol=1e-9,
                        weight_atol=1e-12):
    if not np.isfinite([nav, held, weight, previous_weight]).all() or nav <= 0:
        raise ValueError('invalid turnover inputs')
    # A stop has flattened the carrying account even if its latent target persists.
    reference = previous_weight if held != 0. else 0.
    a, b = nav*(weight-reference), nav*reference-held
    actual = nav*weight-held
    if abs(actual) <= dollar_atol:
        kind = 'no_trade'
    elif abs(held) <= dollar_atol:
        kind = 'opening_from_flat'
    elif abs(weight) <= weight_atol:
        kind = 'closing_to_flat'
    elif np.sign(held) != np.sign(weight):
        kind = 'sign_flip'
    elif abs(weight-reference) > weight_atol:
        kind = 'same_sign_target_change'
    else:
        kind = 'unchanged_target_maintenance'
    return dict(reference_weight=float(reference), target_change_dollars=float(a),
        maintenance_dollars=float(b), absolute_target_change_dollars=float(abs(a)),
        absolute_maintenance_dollars=float(abs(b)), opening_trade_dollars=float(actual),
        opening_turnover_dollars=float(abs(actual)),
        component_netting_dollars=float(max(0., abs(a)+abs(b)-abs(actual))), row_class=kind)


def _components(values):
    result = dict(zip(COMPONENTS, map(float, values)))
    result['net_dollars'] = float(values[0]+values[1]-values[2]-values[3])
    return result


def staged_accounting(trace, *, initial_nav=10000., policy=None):
    """Reconcile staged peaks and assign observed dollars, not causal effects."""
    p = DEFAULT_POLICY | (policy or {})
    atol, rtol = p['reconciliation_dollar_atol'], p['reconciliation_rtol']
    peak, peak_date, peak_stage = initial_nav, None, 'initial'
    cumulative, peak_components = np.zeros(4), np.zeros(4)
    last_nav, halted, first_halt = initial_nav, False, None
    staged = []
    for row in trace.to_dict('records'):
        nav, after = row['nav_before'], row['nav_after']
        if not np.isclose(nav, last_nav, atol=atol, rtol=0):
            raise ValueError('NAV continuity mismatch')
        if bool(row['halted_before']) != halted:
            raise ValueError('halt latch continuity mismatch')
        opening = np.array([row['gross_dollars'], row['funding_dollars'],
                            row['entry_fee_dollars'], row['entry_impact_dollars']])
        exit_cost = np.array([0., 0., row['exit_fee_dollars'], row['exit_impact_dollars']])
        pre_exit = nav + _components(opening)['net_dollars']
        if not np.isclose(after, pre_exit-_components(exit_cost)['fee_dollars']-
                          _components(exit_cost)['impact_dollars'], atol=atol, rtol=0):
            raise ValueError('NAV component identity mismatch')
        cumulative += opening
        if pre_exit > peak:
            peak, peak_date, peak_stage = pre_exit, pd.Timestamp(row['date']).isoformat(), 'pre_exit'
            peak_components = cumulative.copy()
        pre_dd = (peak-pre_exit)/peak
        pre_hit = pre_dd >= p['permanent_drawdown_halt']
        if bool(row['portfolio_stop_hit']) != pre_hit:
            raise ValueError('pre-exit portfolio halt flag mismatch')
        cumulative += exit_cost
        if after > peak:
            peak, peak_date, peak_stage = after, pd.Timestamp(row['date']).isoformat(), 'post_exit'
            peak_components = cumulative.copy()
        post_dd = (peak-after)/peak
        should_halt = halted or post_dd >= p['permanent_drawdown_halt']
        if bool(row['halted_after']) != should_halt:
            raise ValueError('post-exit halt flag mismatch')
        staged.append(dict(pre_exit_nav=float(pre_exit), running_peak_nav=float(peak),
            pre_exit_drawdown=float(pre_dd), post_exit_drawdown=float(post_dd)))
        if not halted and should_halt:
            attribution = _components(cumulative-peak_components)
            if not np.isclose(attribution['net_dollars'], after-peak, atol=atol, rtol=rtol):
                raise ValueError('cumulative peak-to-halt identity mismatch')
            first_halt = dict(date=pd.Timestamp(row['date']).isoformat(),
                crossing_stage='pre_exit' if pre_hit else 'post_exit',
                peak_nav=float(peak), peak_date=peak_date, peak_stage=peak_stage,
                pre_exit_drawdown=float(pre_dd), post_exit_drawdown=float(post_dd),
                nav_after=float(after), peak_to_halt_components=attribution)
        halted, last_nav = should_halt, after
    totals = _components(cumulative)
    if not np.isclose(totals['net_dollars'], last_nav-initial_nav, atol=atol, rtol=rtol):
        raise ValueError('cumulative NAV identity mismatch')
    return dict(first_halt=first_halt, components=totals, stages=pd.DataFrame(staged))


def stop_events(daily):
    columns = ['date', 'successor', 'next_date', 'raw_target_changed',
        'reused_sizing_reference', 'repeated_stop_chain', 'next_price_stop',
        'sizing_date', 'bars_since_sizing', 'next_sizing_date', 'next_bars_since_sizing',
        'next_entry_fee_dollars', 'next_entry_impact_dollars', 'applied_weight',
        'entry_price', 'mark_price', 'gross_dollars', 'funding_dollars',
        'entry_fee_dollars', 'entry_impact_dollars', 'exit_fee_dollars',
        'exit_impact_dollars', 'portfolio_stop_hit', 'stop_outside_envelope']
    events = []
    for i in np.flatnonzero(daily.price_stop_hit.to_numpy()):
        row = daily.iloc[i]
        event = {k: row[k] for k in columns if k in daily.columns}
        event.update(successor='end_of_window_censored', next_date=None,
            raw_target_changed=None, reused_sizing_reference=None,
            repeated_stop_chain=bool(i > 0 and daily.iloc[i-1].price_stop_hit),
            next_price_stop=None, next_sizing_date=None, next_bars_since_sizing=None,
            next_entry_fee_dollars=0., next_entry_impact_dollars=0.)
        if i+1 < len(daily):
            nxt = daily.iloc[i+1]
            kind = ('permanently_halted' if nxt.halted_before else
                    'flat' if nxt.applied_weight == 0 else
                    'same_sign_reentry' if np.sign(nxt.applied_weight) == np.sign(row.applied_weight)
                    else 'opposite_sign_entry')
            event.update(successor=kind, next_date=nxt.date,
                raw_target_changed=bool(nxt.latent_target != row.latent_target),
                next_price_stop=bool(nxt.price_stop_hit))
            if kind in ('same_sign_reentry', 'opposite_sign_entry'):
                event.update(next_entry_fee_dollars=float(nxt.entry_fee_dollars),
                    next_entry_impact_dollars=float(nxt.entry_impact_dollars),
                    next_sizing_date=nxt.sizing_date, next_bars_since_sizing=nxt.bars_since_sizing,
                    reused_sizing_reference=bool(nxt.sizing_date == row.sizing_date))
        events.append(event)
    return pd.DataFrame(events, columns=columns)


def _clock(values):
    clock = pd.DatetimeIndex(pd.to_datetime(values, utc=True)).tz_localize(None)
    if (not len(clock) or clock.hasnans or not clock.is_unique or
        not clock.is_monotonic_increasing or not clock.equals(clock.normalize()) or
        not clock.equals(pd.date_range(clock[0], clock[-1], freq='D'))):
        raise ValueError('incomplete, duplicate or malformed daily clock')
    return clock


def _distribution(values, active, quantiles):
    values = np.asarray(values, dtype=float)
    active = np.asarray(active, dtype=bool)
    finite = np.isfinite(values)
    observed = values[active & finite]
    result = dict(total_rows=len(values), finite_rows=int(finite.sum()),
        unavailable_rows=int((~finite).sum()), active_rows=int(active.sum()),
        active_finite_rows=len(observed), active_unavailable_rows=int((active & ~finite).sum()),
        median=None, p90=None, p99=None, maximum=None)
    if len(observed):
        result.update(dict(zip(('median', 'p90', 'p99'), map(float, np.quantile(observed, quantiles)))))
        result['maximum'] = float(observed.max())
    return result


def analyze_sleeve(targets, trace, *, policy=None, expected_clock=None):
    """Return an explicit unavailable sleeve on any unsupported input/identity.

    Per-row dollar equalities use atol1e-9, rtol0; cumulative sums use the
    registered rtol1e-10 as well. Weight equalities use atol1e-12, rtol0.
    No row is dropped from a valid input, including warmup and halted cash.
    """
    p = DEFAULT_POLICY | (policy or {})
    base = dict(target_rows=len(targets), trace_rows=len(trace), qualification=QUALIFICATION)
    try:
        return _analyze(targets, trace, p, expected_clock, base)
    except (ValueError, TypeError, KeyError, IndexError) as exc:
        return dict(summary={**base, 'status': 'unavailable', 'reason': str(exc)},
                    daily=pd.DataFrame(), events=pd.DataFrame())


def _analyze(targets, trace, p, expected_clock, base):
    t, r = targets.copy(deep=True), trace.copy(deep=True)
    tc, rc = _clock(t['Date']), _clock(r['date'])
    if expected_clock is not None and not tc.equals(pd.DatetimeIndex(expected_clock)):
        raise ValueError('target clock differs from registration')
    if not rc.equals(tc[1:]):
        raise ValueError('trace clock must equal target clock excluding initial anchor')
    t.index = range(len(t)); r.index = range(len(r)); r['date'] = rc
    for col in NUM_COLUMNS:
        if not pd.api.types.is_numeric_dtype(r[col]) or pd.api.types.is_bool_dtype(r[col]):
            raise ValueError(f'non-numeric trace field {col}')
        if not np.isfinite(r[col].to_numpy(dtype=float)).all():
            raise ValueError(f'nonfinite trace field {col}')
    for col in BOOL_COLUMNS:
        if not r[col].map(lambda x: isinstance(x, (bool, np.bool_))).all():
            raise ValueError(f'invalid boolean trace field {col}')
    for col in ('nav_before', 'nav_after', 'mark_price'):
        if (r[col] <= 0).any():
            raise ValueError(f'nonpositive {col}')
    for col in [x for x in NUM_COLUMNS if 'fee' in x or 'impact' in x or 'turnover' in x]:
        if (r[col] < 0).any():
            raise ValueError(f'negative charge/turnover {col}')
    weights = t['target'].to_numpy(dtype=float)
    if not np.isfinite(weights).all() or weights[0] != 0:
        raise ValueError('target series must be finite with flat initial anchor')
    atol, watol = p['reconciliation_dollar_atol'], p['reconciliation_weight_atol']

    def equal(a, b, label, tolerance=atol):
        if not np.allclose(a, b, atol=tolerance, rtol=0):
            raise ValueError(label + ' mismatch')

    vol = volatility_features(t['Close'], p)
    sizing = []
    last_i, last_sigma, last_risk = None, None, None
    for i, weight in enumerate(weights):
        prior = weights[i-1] if i else 0.
        kind = 'none'
        if abs(weight-prior) > watol and weight != 0:
            if prior != 0 and np.sign(prior) == np.sign(weight):
                raise ValueError('unsupported same-sign raw-target change')
            kind = 'entry' if prior == 0 else 'flip'
            sigma = vol.sigma_252.iloc[i]
            if not np.isfinite(sigma) or sigma <= 0 or not vol.vol_entry_gate_open.iloc[i]:
                raise ValueError('sizing event has unavailable volatility or closed entry gate')
            confidence = p['confidence']
            theoretical = min(p['leverage_cap'], p['target_vol']*p['kelly_fraction']*
                confidence*(1+(p['leverage_cap']-1)*confidence)/sigma)
            equal(abs(weight), theoretical, 'entry sizing algebra', watol)
            last_i, last_sigma, last_risk = i, float(sigma), float(abs(weight)*sigma)
        elif weight == 0:
            if prior != 0: kind = 'flat'
            last_i = last_sigma = last_risk = None
        sizing.append(dict(builder_sizing_event=kind,
            sizing_date=tc[last_i].isoformat() if last_i is not None else None,
            sizing_sigma_252=last_sigma, reference_entry_risk=last_risk,
            bars_since_sizing=i-last_i if last_i is not None else None))
    daily = pd.concat([r, vol.iloc[1:].reset_index(drop=True),
                       pd.DataFrame(sizing).iloc[1:].reset_index(drop=True)], axis=1)
    daily['latent_target'] = weights[1:]
    equal(r.pre_nav, r.nav_before, 'pre NAV alias')
    equal(r.post_nav, r.nav_after, 'post NAV alias')
    expected = np.where(r.halted_before, 0., weights[1:])
    equal(r.target_position, expected, 'target/halt alignment', watol)
    equal(r.exposure, expected, 'applied target', watol)
    daily['applied_weight'] = r.exposure
    held = np.r_[0., r.closing_notional.iloc[:-1]]
    daily['incoming_weight'] = held/r.nav_before
    daily['closing_weight'] = r.closing_notional/r.nav_after
    trade = pd.DataFrame([turnover_components(n, h, w, old, dollar_atol=atol,
        weight_atol=watol) for n,h,w,old in zip(r.nav_before, held, r.exposure,
                                                np.r_[0., r.exposure.iloc[:-1]])])
    daily = pd.concat([daily, trade], axis=1)
    equal(r.entry_turnover_dollars, trade.opening_turnover_dollars, 'opening turnover')
    equal(r.gross_dollars, r.nav_before*r.exposure*r.mark_return, 'gross dollars')
    equal(r.fee_dollars, r.entry_fee_dollars+r.exit_fee_dollars, 'fee subdivisions')
    equal(r.impact_dollars, r.entry_impact_dollars+r.exit_impact_dollars, 'impact subdivisions')
    equal(r.turnover_dollars, r.entry_turnover_dollars+r.exit_turnover_dollars, 'turnover subdivisions')
    equal(r.net_return, r.nav_after/r.nav_before-1, 'recorded return', watol)
    marked = r.nav_before*r.exposure*(1+r.mark_return)
    equal(r.exit_notional, np.where(r.exit_executed, marked, 0.), 'exit notional')
    equal(r.exit_turnover_dollars, abs(r.exit_notional), 'exit turnover')
    equal(r.closing_notional, np.where(r.exit_executed, 0., marked), 'closing notional')
    if (r.loc[~r.exit_executed, ['exit_fee_dollars','exit_impact_dollars']].to_numpy() != 0).any():
        raise ValueError('exit charges without recorded exit')
    if (r.price_stop_hit & ~r.exit_executed).any():
        raise ValueError('price stop without recorded exit')
    halted = r.halted_before
    cashcols = [x for x in NUM_COLUMNS if x.endswith('_dollars')] + ['exposure', 'closing_notional', 'net_return']
    if (r.loc[halted, cashcols].to_numpy() != 0).any():
        raise ValueError('nonzero halted cash tail')
    staged = staged_accounting(r, initial_nav=p['initial_nav'], policy=p)
    daily = pd.concat([daily, staged['stages']], axis=1)
    distributions, counts = {}, {}
    budget = p['target_vol']*p['kelly_fraction']*p['confidence']*(1+(p['leverage_cap']-1)*p['confidence'])
    for label in ('latent', 'incoming', 'applied', 'closing'):
        weight = daily.latent_target if label == 'latent' else daily[label+'_weight']
        value = abs(weight)*daily.sigma_252
        daily[label+'_risk_proxy'] = value
        active = weight != 0.
        distributions[label] = _distribution(value, active, p['risk_quantiles'])
        counts[label+'_above_leverage_cap'] = int((abs(weight) > p['leverage_cap']+watol).sum())
        reference = pd.to_numeric(daily.reference_entry_risk, errors='raise')
        ratio = value/reference.where(reference > 0)
        daily[label+'_reference_risk_ratio'] = ratio
        distributions[label+'_reference_ratio'] = _distribution(ratio, active, p['risk_quantiles'])
        ref_known = np.isfinite(value) & np.isfinite(reference)
        budget_known = np.isfinite(value)
        above_ref = pd.Series(pd.array(np.where(ref_known, value > reference+watol, None),dtype='boolean'))
        above_budget = pd.Series(pd.array(np.where(budget_known,value > budget+watol,None),dtype='boolean'))
        daily[label+'_above_reference_risk'] = above_ref
        daily[label+'_above_nominal_entry_budget'] = above_budget
        counts[label+'_risk_thresholds'] = dict(active_rows=int(active.sum()),
            reference_available_active_rows=int((active & ref_known).sum()),
            reference_unavailable_active_rows=int((active & ~ref_known).sum()),
            nominal_budget_available_active_rows=int((active & budget_known).sum()),
            nominal_budget_unavailable_active_rows=int((active & ~budget_known).sum()),
            above_reference_risk=int((above_ref.fillna(False) & active).sum()),
            above_nominal_entry_budget=int((above_budget.fillna(False) & active).sum()))
    daily['above_reference_risk'] = daily.applied_above_reference_risk
    daily['above_nominal_entry_budget'] = daily.applied_above_nominal_entry_budget
    counts.update(above_reference_risk=int(daily.above_reference_risk.sum()),
        above_nominal_entry_budget=int(daily.above_nominal_entry_budget.sum()),
        applied_while_entry_gate_closed=int(((daily.applied_weight != 0)&~daily.vol_entry_gate_open).sum()),
        builder_entries=int((daily.builder_sizing_event == 'entry').sum()),
        builder_flips=int((daily.builder_sizing_event == 'flip').sum()),
        latent_nonzero_halted_rows=int(((daily.latent_target != 0)&daily.halted_before).sum()))
    events = stop_events(daily)
    classes = {kind: dict(rows=int((daily.row_class == kind).sum()), **{
        field: float(daily.loc[daily.row_class == kind, field].sum()) for field in
        ('entry_turnover_dollars','entry_fee_dollars','entry_impact_dollars',
         'absolute_target_change_dollars','absolute_maintenance_dollars','component_netting_dollars')})
         for kind in ROW_CLASSES}
    summary = dict(**base, status='complete_qualified', reason=None, initial_nav=p['initial_nav'],
        final_nav=float(r.nav_after.iloc[-1]), first_halt=staged['first_halt'],
        components=staged['components'], risk_distributions=distributions, counts=counts,
        row_classes=classes, halted_cash_rows=int(halted.sum()),
        price_stops=len(events), stop_fills_outside_envelope=int(r.stop_outside_envelope.sum()),
        stop_successors={k:int(v) for k,v in events.successor.value_counts().items()},
        stop_sizing_age_distributions={
            'at_stop':_distribution(events.bars_since_sizing, np.ones(len(events),dtype=bool), p['risk_quantiles']),
            'at_reentry':_distribution(events.next_bars_since_sizing,
                events.successor.isin(['same_sign_reentry','opposite_sign_entry']),p['risk_quantiles']),
            'reused_reference_reentry':_distribution(events.next_bars_since_sizing,
                events.reused_sizing_reference.eq(True),p['risk_quantiles'])},
        unique_stop_successor_entry_fees=float(events.next_entry_fee_dollars.sum()),
        unique_stop_successor_entry_impact=float(events.next_entry_impact_dollars.sum()),
        exit_charges={k:float(r[k].sum()) for k in
            ('exit_turnover_dollars','exit_fee_dollars','exit_impact_dollars')},
        turnover_dollars=float(r.turnover_dollars.sum()),
        tolerance=dict(per_row_dollars_atol=atol, weights_atol=watol,
                       cumulative_rtol=p['reconciliation_rtol']))
    return dict(summary=summary, daily=daily, events=events)
