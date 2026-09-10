"""Complete-clock descriptive evaluation for the registered fixed risk-policy grid.

No fitting, selection, bootstrap or strategy signal construction occurs here.
All cash rows remain observations; undefined ratios are null metrics rather
than unavailable books. Dollar summaries always refer to one sleeve.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from tradingagents.strategies.factor_risk_diagnostics import (
    DEFAULT_POLICY, NUM_COLUMNS, BOOL_COLUMNS, ROW_CLASSES,
    volatility_features, turnover_components, staged_accounting, stop_events,
)

POLICY = DEFAULT_POLICY | dict(daily_risk_numerator=.15,
    block_release='saved_raw_target_zero_or_opposite', invalid_required_sigma='unavailable',
    daily_vol_gate_exit=False, stop_loss=1., take_profit=0.)
COSTS = dict(fee_rate=.0004, slippage=.0005, spread=.0001, price_impact=.00005,
             funding_rate=.0003, stop_loss=1., max_portfolio_dd=.15, take_profit=0.)
VARIANTS = ('primary','zero_execution','double_execution','zero_funding')
COINS = ('bitcoin','ethereum')
PERIODS = [['2021-11-08','2022-12-31'],['2023-01-01','2024-12-31'],['2025-01-01','2025-03-31']]
RETURN_FIELDS = ('mean_return','annual_mean','annual_volatility','sharpe','total_return','max_drawdown')


def clock(values):
    idx = pd.DatetimeIndex(pd.to_datetime(values, utc=True))
    if (not len(idx) or idx.hasnans or not idx.is_unique or not idx.is_monotonic_increasing
            or not idx.equals(idx.normalize())
            or not idx.equals(pd.date_range(idx[0],idx[-1],freq='D'))):
        raise ValueError('incomplete, duplicated or non-midnight UTC clock')
    return idx


def validate_targets(frame, expected_clock):
    f = frame.copy(deep=True)
    idx = clock(f['Date'])
    if not idx.equals(pd.DatetimeIndex(expected_clock)):
        raise ValueError('target clock differs from registered full clock')
    for field in ('Open','High','Low','Close','target'):
        if not pd.api.types.is_numeric_dtype(f[field]) or pd.api.types.is_bool_dtype(f[field]):
            raise ValueError(f'non-numeric target/price: {field}')
        if not np.isfinite(f[field].to_numpy(dtype=float)).all():
            raise ValueError(f'nonfinite target/price: {field}')
    ohlc=f[['Open','High','Low','Close']].to_numpy(dtype=float)
    if ((ohlc<=0).any() or (ohlc[:,1]<ohlc.max(axis=1)).any()
            or (ohlc[:,2]>ohlc.min(axis=1)).any()):
        raise ValueError('invalid OHLC envelope')
    if f.target.iloc[0] != 0 or (abs(f.target)>3+1e-12).any():
        raise ValueError('nonflat initial target or target leverage breach')
    f['Date']=idx
    return f.reset_index(drop=True)


def return_metrics(series, expected_clock):
    idx=clock(series.index)
    r=np.asarray(series,dtype=float)
    if not idx.equals(pd.DatetimeIndex(expected_clock)) or not np.isfinite(r).all() or (r<=-1).any():
        raise ValueError('incomplete/unavailable return clock')
    eq=np.r_[1.,np.cumprod(1+r)]
    if not np.isfinite(eq).all() or (eq<=0).any(): raise ValueError('invalid cumulative NAV')
    mean=float(r.mean()); sd=float(r.std(ddof=1)) if len(r)>1 else None
    return dict(status='complete',n_bars=len(r),first=idx[0].isoformat(),last=idx[-1].isoformat(),
        mean_return=mean,annual_mean=365*mean,annual_volatility=sd*np.sqrt(365) if sd is not None else None,
        sharpe=float(np.sqrt(365)*mean/sd) if sd is not None and sd>0 else None,
        sharpe_reason=None if sd is not None and sd>0 else 'zero_variance' if sd==0 else 'insufficient_observations',
        total_return=float(eq[-1]-1),max_drawdown=float((eq/np.maximum.accumulate(eq)-1).min()))


def period_metrics(series,periods=PERIODS):
    out=[]
    for start,end in periods:
        expected=pd.date_range(start,end,tz='UTC',freq='D')
        part=series.loc[(series.index>=expected[0])&(series.index<=expected[-1])]
        out.append(dict(start=start,end=end,metrics=return_metrics(part,expected)))
    return out


def cost_variant(costs,name):
    if name not in VARIANTS: raise ValueError('unregistered cost variant')
    c=dict(costs)
    if name in ('zero_execution','double_execution'):
        for k in ('fee_rate','slippage','spread','price_impact'):
            c[k]*=0 if name=='zero_execution' else 2
    if name=='zero_funding': c['funding_rate']=0.
    return c


def _equal(actual,expected,label,atol,rtol=0,equal_nan=False):
    if not np.allclose(actual,expected,atol=atol,rtol=rtol,equal_nan=equal_nan):
        raise ValueError(label+' mismatch')


def control_trace_parity(actual,reference,policy):
    if len(actual)!=len(reference): raise ValueError('control trace length mismatch')
    for field in reference:
        if field not in actual: raise ValueError('missing original trace column '+field)
        a,b=actual[field],reference[field]
        if field=='date':
            if not clock(a).equals(clock(b)): raise ValueError('control date mismatch')
        elif pd.api.types.is_bool_dtype(b):
            if not pd.api.types.is_bool_dtype(a) or not np.array_equal(a,b):
                raise ValueError('control flag mismatch '+field)
        elif pd.api.types.is_numeric_dtype(b) or b.isna().all():
            if not np.array_equal(a.isna(),b.isna()): raise ValueError('control null mismatch '+field)
            atol=policy['reconciliation_dollar_atol']
            if field in ('exposure','target_position','net_return','mark_return'): atol=policy['reconciliation_weight_atol']
            _equal(a.to_numpy(dtype=float),b.to_numpy(dtype=float),'control '+field,atol,
                   policy['reconciliation_rtol'],True)
        elif not a.equals(b): raise ValueError('control category mismatch '+field)
    return dict(matched=True,original_columns=list(reference),rows=len(reference))


def control_return_parity(actual,reference,policy):
    if list(actual.columns)!=list(COINS)+['index_return'] or list(reference.columns)!=list(actual.columns):
        raise ValueError('control return columns mismatch')
    if not clock(actual.index).equals(clock(reference.index)): raise ValueError('control return clock mismatch')
    if not np.isfinite(actual.to_numpy()).all() or not np.isfinite(reference.to_numpy()).all():
        raise ValueError('nonfinite control return')
    _equal(actual.to_numpy(),reference.to_numpy(),'control returns',policy['reconciliation_weight_atol'],policy['reconciliation_rtol'])
    return dict(matched=True,rows=len(reference),columns=list(reference.columns))


def frozen_log_shadow(trace):
    r=trace.mark_return.to_numpy(dtype=float); w=trace.exposure.to_numpy(dtype=float)
    if not np.isfinite(r).all() or (r<=-1).any(): raise ValueError('invalid frozen log mark')
    result=trace.post_nav.to_numpy()/trace.pre_nav.to_numpy()-1+w*(np.log1p(r)-r)
    if not np.isfinite(result).all() or (result<=-1).any(): raise ValueError('invalid frozen log NAV')
    return result


def scalar_contrasts(arms):
    keys=set.intersection(*(set(v) for v in arms.values()))
    def difference(terms):
        out={}
        for k in sorted(keys):
            vals=[arms[a][k] for a,_ in terms]
            out[k]=float(sum(arms[a][k]*c for a,c in terms)) if all(
                isinstance(v,(int,float,np.number)) and not isinstance(v,(bool,np.bool_)) and np.isfinite(v) for v in vals) else None
        return out
    return dict(direct={a:difference([(a,1),('A00',-1)]) for a in ('A10','A01','A11')},
        factorial=dict(sizing=difference([('A10',.5),('A00',-.5),('A11',.5),('A01',-.5)]),
            waiting=difference([('A01',.5),('A00',-.5),('A11',.5),('A10',-.5)]),
            interaction=difference([('A11',1),('A10',-1),('A01',-1),('A00',1)])))


def distribution(values,active,quantiles):
    values=np.asarray(values,dtype=float); active=np.asarray(active,dtype=bool)
    finite=np.isfinite(values); obs=values[active&finite]
    out=dict(total_rows=len(values),finite_rows=int(finite.sum()),unavailable_rows=int((~finite).sum()),
        active_rows=int(active.sum()),active_finite_rows=len(obs),active_unavailable_rows=int((active&~finite).sum()),
        median=None,p90=None,p99=None,maximum=None)
    if len(obs):
        out.update(dict(zip(('median','p90','p99'),map(float,np.quantile(obs,quantiles)))))
        out['maximum']=float(obs.max())
    return out


def evaluate_trace(targets,trace,cell,policy=POLICY):
    """Reconcile one policy-aware sleeve; raise instead of deleting bad rows."""
    r=trace.copy(deep=True).reset_index(drop=True)
    tc=clock(targets.Date); rc=clock(r.date)
    if not rc.equals(tc[1:]): raise ValueError('trace/target clock mismatch')
    r['date']=rc
    atol=policy['reconciliation_dollar_atol']; watol=policy['reconciliation_weight_atol']
    for field in NUM_COLUMNS:
        if not pd.api.types.is_numeric_dtype(r[field]) or pd.api.types.is_bool_dtype(r[field]) or not np.isfinite(r[field]).all():
            raise ValueError('invalid numeric trace '+field)
    for field in (*BOOL_COLUMNS,'decision_blocked'):
        if not pd.api.types.is_bool_dtype(r[field]): raise ValueError('invalid trace bool '+field)
    for field in ('nav_before','nav_after','mark_price'):
        if (r[field]<=0).any(): raise ValueError('nonpositive trace '+field)
    for field in [f for f in NUM_COLUMNS if any(x in f for x in ('fee','impact','turnover'))]:
        if (r[field]<0).any(): raise ValueError('negative trace charge '+field)
    raw=targets.target.to_numpy(dtype=float)
    vol=volatility_features(targets.Close,policy)
    sig=vol.sigma_252.to_numpy()
    reference=[]; last=None
    for i,w in enumerate(raw):
        prior=raw[i-1] if i else 0.
        if w==0: last=None
        elif prior==0 or np.sign(w)!=np.sign(prior): last=i
        elif abs(w-prior)>watol: raise ValueError('unsupported original same-sign target change')
        reference.append(dict(sizing_date=tc[last].isoformat() if last is not None else None,
            bars_since_sizing=i-last if last is not None else None,
            reference_entry_risk=float(abs(w)*sig[last]) if last is not None and np.isfinite(sig[last]) else None))
    _equal(r.raw_target,raw[1:],'raw target',watol)
    _equal(r.requested_target,r.exposure,'requested exposure',watol)
    _equal(r.target_position,r.exposure,'applied exposure',watol)
    _equal(r.pre_nav,r.nav_before,'pre NAV aliases',atol)
    _equal(r.post_nav,r.nav_after,'post NAV aliases',atol)
    _equal(pd.to_numeric(r.sizing_sigma).to_numpy(),sig[1:],'policy causal sigma',watol,equal_nan=True)
    if not (r.policy_sizing==cell['sizing']).all() or not (r.policy_reentry==cell['reentry']).all():
        raise ValueError('policy identity differs from cell')
    blocked=0
    for j,row in enumerate(r.to_dict('records')):
        w=raw[j+1]; before=blocked; after=blocked; halted=row['halted_before']
        release=None
        if not halted and blocked and (w==0 or np.sign(w)!=blocked):
            release='raw_flat' if w==0 else 'raw_opposite'; after=0
        waiting=bool(not halted and after and w!=0 and np.sign(w)==after)
        requested=0. if halted or waiting or w==0 else w
        if cell['sizing']=='daily' and requested!=0:
            sigma=sig[j+1]
            if not np.isfinite(sigma) or sigma<=0: raise ValueError('unavailable required sigma')
            requested=float(np.sign(w)*min(policy['leverage_cap'],policy['daily_risk_numerator']/sigma))
        _equal(row['exposure'],requested,'policy applied transition',watol)
        if row['decision_blocked']!=waiting or row['blocked_before']!=before or row['blocked_after_decision']!=after or row['block_release']!=release:
            raise ValueError('policy block transition metadata mismatch')
        stopped=int(np.sign(row['exposure'])) if row['price_stop_hit'] and row['exit_executed'] else 0
        blocked=stopped if stopped and cell['reentry']=='new_target_episode' else after
        if row['blocked_after']!=blocked or row['stopped_direction']!=stopped:
            raise ValueError('post-exit policy notification mismatch')
    held=np.r_[0.,r.closing_notional.iloc[:-1]]
    trade=pd.DataFrame([turnover_components(n,h,w,old,dollar_atol=atol,weight_atol=watol)
        for n,h,w,old in zip(r.nav_before,held,r.exposure,np.r_[0.,r.exposure.iloc[:-1]])])
    _equal(trade.opening_turnover_dollars,r.entry_turnover_dollars,'opening turnover',atol)
    _equal(r.gross_dollars,r.nav_before*r.exposure*r.mark_return,'gross dollars',atol)
    for total,a,b in [('fee_dollars','entry_fee_dollars','exit_fee_dollars'),('impact_dollars','entry_impact_dollars','exit_impact_dollars'),('turnover_dollars','entry_turnover_dollars','exit_turnover_dollars')]:
        _equal(r[total],r[a]+r[b],total+' subdivisions',atol)
    _equal(r.net_return,r.nav_after/r.nav_before-1,'net return',watol)
    marked=r.nav_before*r.exposure*(1+r.mark_return)
    _equal(r.exit_notional,np.where(r.exit_executed,marked,0),'exit notional',atol)
    _equal(r.exit_turnover_dollars,abs(r.exit_notional),'exit turnover',atol)
    _equal(r.closing_notional,np.where(r.exit_executed,0,marked),'closing notional',atol)
    if (r.price_stop_hit&~r.exit_executed).any(): raise ValueError('stop without exit')
    cashcols=[f for f in NUM_COLUMNS if f.endswith('_dollars')]+['exposure','closing_notional','net_return']
    if (r.loc[r.halted_before,cashcols].to_numpy()!=0).any(): raise ValueError('nonzero halted cash')
    stages=staged_accounting(r,initial_nav=policy['initial_nav'],policy=policy)
    daily=pd.concat([r,vol.iloc[1:].reset_index(drop=True),pd.DataFrame(reference).iloc[1:].reset_index(drop=True),trade,stages['stages']],axis=1)
    daily['latent_target']=raw[1:]; daily['applied_weight']=r.exposure
    daily['incoming_weight']=held/r.nav_before; daily['closing_weight']=r.closing_notional/r.nav_after
    risks={}; counts={}; exposures={}
    for label in ('latent','incoming','applied','closing'):
        weight=daily.latent_target if label=='latent' else daily[label+'_weight']
        active=weight!=0; value=abs(weight)*daily.sigma_252
        reference_risk=pd.to_numeric(daily.reference_entry_risk)
        daily[label+'_risk_proxy']=value
        risks[label]=distribution(value,active,policy['risk_quantiles'])
        ratio=value/reference_risk.where(reference_risk>0)
        daily[label+'_reference_risk_ratio']=ratio
        risks[label+'_reference_ratio']=distribution(ratio,active,policy['risk_quantiles'])
        known=np.isfinite(value)&np.isfinite(reference_risk)
        counts[label]=dict(active_rows=int(active.sum()),reference_available_active_rows=int((active&known).sum()),
            reference_unavailable_active_rows=int((active&~known).sum()),
            above_reference=int((active&known&(value>reference_risk+watol)).sum()),
            above_nominal_budget=int((active&np.isfinite(value)&(value>policy['daily_risk_numerator']+watol)).sum()),
            above_leverage_cap=int((abs(weight)>policy['leverage_cap']+watol).sum()))
        exposures[label]=dict(integrated_absolute=float(abs(weight).sum()),integrated_signed=float(weight.sum()))
    if cell['sizing']=='daily' and counts['applied']['above_nominal_budget']:
        raise ValueError('daily risk numerator conformance failure')
    events=stop_events(daily)
    # The helper's sizing dates describe the frozen builder, not daily resizing.
    events['sizing_reference_basis']='original_raw_target'
    if len(events):
        # Preserve a waiting successor distinctly from ordinary flat exposure.
        waiting_by_date=dict(zip(daily.date,daily.decision_blocked))
        for i,event in events.iterrows():
            if event.successor=='flat' and waiting_by_date.get(event.next_date,False): events.loc[i,'successor']='waiting'
    classes={kind:dict(rows=int((daily.row_class==kind).sum()),**{f:float(daily.loc[daily.row_class==kind,f].sum())
        for f in ('entry_turnover_dollars','entry_fee_dollars','entry_impact_dollars','absolute_target_change_dollars','absolute_maintenance_dollars','component_netting_dollars')}) for kind in ROW_CLASSES}
    active=r.exposure!=0; waiting=r.decision_blocked; halted=r.halted_before
    summary=dict(status='complete',target_rows=len(targets),trace_rows=len(r),initial_nav=policy['initial_nav'],
        final_nav=float(r.nav_after.iloc[-1]),first_halt=stages['first_halt'],components=stages['components'],
        risk_distributions=risks,risk_counts=counts,exposures=exposures,row_classes=classes,
        active_rows=int(active.sum()),waiting_rows=int(waiting.sum()),halted_cash_rows=int(halted.sum()),
        other_flat_rows=int((~active&~waiting&~halted).sum()),blocked_reentry_opportunities=int(waiting.sum()),
        price_stops=int(r.price_stop_hit.sum()),stop_fills_outside_envelope=int(r.stop_outside_envelope.sum()),
        stop_successors={k:int(v) for k,v in events.successor.value_counts().items()},
        raw_sizing_age=distribution(daily.bars_since_sizing,active,policy['risk_quantiles']),
        turnover_dollars=float(r.turnover_dollars.sum()),
        unique_stop_successor_entry_fees=float(events.next_entry_fee_dollars.sum()),
        unique_stop_successor_entry_impact=float(events.next_entry_impact_dollars.sum()),
        exit_charges={k:float(r[k].sum()) for k in ('exit_turnover_dollars','exit_fee_dollars','exit_impact_dollars')},
        engineering_conformance=True,validated=False)
    return dict(summary=summary,daily=daily,events=events)
