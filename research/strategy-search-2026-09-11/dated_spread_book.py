"""One fixed long-dated/short-perpetual episode; pure signed-wallet arithmetic."""
from datetime import datetime, timezone
from decimal import Decimal, ROUND_FLOOR, localcontext
import math

START=1777593600000
DAY=86400000
DAYS=56
END=START+DAYS*DAY
LOTS={'BTC':'0.001','ETH':'0.01'}
COSTS={'base':('0.0005','0.0002'),'stress':('0.001','0.0004')}


def number(value,positive=False):
    if isinstance(value,bool):raise ValueError('boolean financial value')
    result=float(value)
    if not math.isfinite(result) or (positive and result<=0):raise ValueError('invalid financial number')
    return result


def stamp(value):
    if type(value) is int:return value
    if isinstance(value,str) and len(value)==13 and value.isascii() and value.isdigit():return int(value)
    raise ValueError('integer millisecond clock required')


def bars(rows,interval,count,trade):
    if len(rows)!=count:raise ValueError('exact complete registered bar count required')
    out=[]
    for i,row in enumerate(rows):
        t=START+i*interval
        if len(row)!=12 or stamp(row[0])!=t or stamp(row[6])!=t+interval-1:raise ValueError('bar chronology differs')
        o,h,l,c=[number(x,True) for x in row[1:5]]
        if not l<=min(o,c)<=max(o,c)<=h:raise ValueError('invalid OHLC')
        item={'open':o,'high':h,'low':l,'close':c}
        if trade:
            for k in (5,7,8,9,10):
                if number(row[k])<0:raise ValueError('negative activity')
            if not number(row[8]).is_integer():raise ValueError('noninteger trade count')
            item.update(volume=number(row[5]),trades=number(row[8]))
        out.append(item)
    return out


def funding(rows,asset,q):
    if len(rows)!=DAYS*3:raise ValueError('all 168 fixed-window funding events required')
    days=[[] for _ in range(DAYS)];excluded=[];events=[];previous=None
    for i,row in enumerate(rows):
        t=row['fundingTime']
        if type(t) is not int or not START-5000<=t<END or (previous is not None and t<=previous):raise ValueError('funding chronology')
        if abs(t-(START+i*DAY//3))>5000 or row['symbol']!=asset+'USDT':raise ValueError('conditional funding calendar or symbol differs')
        rate,mark=number(row['fundingRate']),number(row['markPrice'],True)
        included=i>0
        if included and t<=START+5000:raise ValueError('post-entry funding ownership ambiguous')
        cash=q*mark*rate if included else None
        if included:days[(t-START)//DAY].append(cash)
        else:excluded.append(t)
        events.append({'funding_time_ms':t,'rate':rate,'event_mark':mark,'included':included,'signed_short_cash':cash})
        previous=t
    if len(excluded)!=1:raise ValueError('entry funding exclusion ambiguous')
    return days,excluded,events


def close(q,de,pe,dx,px,C,f,entry_df,entry_pf,paid):
    dfee,pfee=q*dx*f,q*px*f
    dpnl,ppnl=q*(dx-de),q*(pe-px)
    dw=.4*C-entry_df+dpnl-dfee
    pw=.5*C-entry_pf+paid+ppnl-pfee
    cash=math.fsum((dw,pw,.1*C))
    fees=math.fsum((entry_df,entry_pf,dfee,pfee))
    signed=math.fsum((dpnl,ppnl,paid,-fees))
    return {'dated_exit_fill':dx,'perp_exit_fill':px,'dated_exit_fee':dfee,'perp_exit_fee':pfee,
            'dated_price_pnl':dpnl,'perp_price_pnl':ppnl,'funding_cash':paid,'all_fees':fees,
            'dated_wallet_after_close':dw,'perp_wallet_after_close':pw,'idle_cash':.1*C,
            'final_cash':cash,'cash_profit':cash-C,'signed_component_profit':signed,
            'cash_reconciliation_difference':cash-C-signed,'terminal_dated_quantity':0.,'terminal_perp_quantity':0.}


def book(dated_hourly,perp_daily,dated_marks,perp_marks,funding_events,spot_daily,*,asset,capital,cost_scenario):
    if asset not in LOTS or cost_scenario not in COSTS:raise ValueError('unregistered case')
    C=number(capital,True)
    d=bars(dated_hourly,DAY//24,DAYS*24,True);p=bars(perp_daily,DAY,DAYS,True)
    dm=bars(dated_marks,DAY,DAYS,False);pm=bars(perp_marks,DAY,DAYS,False)
    spot=bars(spot_daily,DAY,DAYS,True)
    activity={'dated_zero_volume_hours':[START+i*DAY//24 for i,x in enumerate(d) if x['volume']==0],
              'dated_zero_trade_hours':[START+i*DAY//24 for i,x in enumerate(d) if x['trades']==0],
              'perp_zero_volume_days':[START+i*DAY for i,x in enumerate(p) if x['volume']==0],
              'perp_zero_trade_days':[START+i*DAY for i,x in enumerate(p) if x['trades']==0]}
    if any(x['volume']<=0 or x['trades']<=0 for x in (d[0],d[-1],p[0],p[-1])):
        return {'status':'unavailable','reason':'entry/exit trade activity missing','held_activity':activity}
    # Exact decimal sizing from raw literals, before binary floating cash arithmetic.
    with localcontext() as context:
        context.prec=80
        fee,slip=map(Decimal,COSTS[cost_scenario]);lot=Decimal(LOTS[asset])
        de_dec=Decimal(str(dated_hourly[0][1]))*(1+slip)
        pe_dec=Decimal(str(perp_daily[0][1]))*(1-slip)
        unit=max(de_dec,pe_dec)+fee*de_dec+fee*pe_dec
        count=(Decimal(str(capital))*Decimal('.4')/(lot*unit)).to_integral_value(rounding=ROUND_FLOOR)
        q=float(count*lot);de,pe,f,s=float(de_dec),float(pe_dec),float(fee),float(slip)
        sizing={'lot_count':int(count),'unit_ceiling_cost_decimal':str(unit),'quantity_decimal':str(count*lot),
                'used_ceiling_decimal':str(count*lot*unit),'next_lot_ceiling_decimal':str((count+1)*lot*unit)}
    if q<=0:return {'status':'unavailable','reason':'capital cannot fund one assumed common lot','held_activity':activity}
    df,pf=q*de*f,q*pe*f
    days,excluded,events=funding(funding_events,asset,q)
    initial={'quantity':q,'dated_quantity':q,'perp_quantity':-q,'net_base_quantity':0.,
             'assumed_common_lot':float(lot),'dated_entry_raw':d[0]['open'],'perp_entry_raw':p[0]['open'],
             'dated_entry_fill':de,'perp_entry_fill':pe,'dated_entry_fee':df,'perp_entry_fee':pf,
             'dated_reserve':.4*C,'perp_reserve':.5*C,'idle_cash':.1*C,
             'dated_entry_notional':q*de,'perp_entry_notional':q*pe,'sizing':sizing}
    trace=[];cumulative=0.
    for i in range(DAYS):
        prior=cumulative;paid=math.fsum(days[i]);negative=math.fsum(v for v in days[i] if v<0)
        cumulative=math.fsum((prior,paid))
        dw=.4*C-df+q*(dm[i]['close']-de)
        pw=.5*C-pf+cumulative+q*(pe-pm[i]['close'])
        db=.4*C-df+q*(dm[i]['low']-de)-.01*q*dm[i]['low']
        pb=.5*C-pf+prior+negative+q*(pe-pm[i]['high'])-.01*q*pm[i]['high']
        nav=math.fsum((dw,pw,.1*C))
        trace.append({'date':datetime.fromtimestamp((START+i*DAY)/1000,timezone.utc).date().isoformat(),
            'dated_mark_close':dm[i]['close'],'perp_mark_close':pm[i]['close'],
            'dated_mark_low':dm[i]['low'],'perp_mark_high':pm[i]['high'],
            'dated_trade_close':d[(i+1)*24-1]['close'],'perp_trade_close':p[i]['close'],
            'funding_cash':paid,'negative_funding_cash':negative,'prior_cumulative_funding':prior,
            'cumulative_funding_cash':cumulative,'funding_event_count':len(days[i]),
            'dated_wallet':dw,'perp_wallet':pw,'idle_cash':.1*C,'pre_exit_nav':nav,'nav':nav,
            'dated_maintenance_assumed':.01*q*dm[i]['low'],'perp_maintenance_assumed':.01*q*pm[i]['high'],
            'dated_low_buffer':db,'perp_high_buffer':pb,
            'dated_quantity':q,'perp_quantity':-q,'net_base_quantity':0.,
            'net_market_notional':q*(dm[i]['close']-pm[i]['close']),
            'gross_market_notional':q*(dm[i]['close']+pm[i]['close'])})
    final=close(q,de,pe,d[-1]['close']*(1-s),p[-1]['close']*(1+s),C,f,df,pf,cumulative)
    if abs(final['cash_reconciliation_difference'])>1e-8:raise ValueError('cash reconciliation above1e-8USDT')
    raw=q*((d[-1]['close']-d[0]['open'])+(p[0]['open']-p[-1]['close']))
    executed=final['dated_price_pnl']+final['perp_price_pnl']
    final.update(raw_two_leg_price_change=raw,slippage_cost=raw-executed,
                 zero_funding_same_quantity_profit=final['cash_profit']-cumulative,
                 frictionless_same_quantity_profit=raw+cumulative)
    last=trace[-1]
    last['pre_exit_components']={k:last[k] for k in ('nav','dated_wallet','perp_wallet','dated_quantity','perp_quantity','net_base_quantity','net_market_notional','gross_market_notional')}
    last.update(nav=final['final_cash'],dated_wallet=final['dated_wallet_after_close'],perp_wallet=final['perp_wallet_after_close'],
                dated_quantity=0.,perp_quantity=0.,net_base_quantity=0.,net_market_notional=0.,gross_market_notional=0.)
    peak=C;dd=0.;previous=C;returns=[]
    for row in trace:
        nav=row['nav'];peak=max(peak,nav);dd=max(dd,(peak-nav)/peak)
        value=nav/previous-1 if previous>0 and nav>0 else None
        row['full_capital_daily_return']=value;row['cash_increment']=nav-previous
        returns.append(value);previous=nav
    valid=all(x is not None for x in returns)
    logsum=math.fsum(math.log(row['nav'])-math.log(C if i==0 else trace[i-1]['nav']) for i,row in enumerate(trace)) if valid else None
    simple=math.fsum(returns) if valid else None
    stresses=[]
    for multiple in (.5,1.,2.):
        for basis in (0,10,50):
            ref=spot[0]['open']*multiple;ds=ref*(1-basis/20000);ps=ref*(1+basis/20000)
            dw=.4*C-df+q*(ds-de);pw=.5*C-pf+q*(pe-ps)
            closed=close(q,de,pe,ds*(1-s),ps*(1+s),C,f,df,pf,0.)
            stresses.append({'id':f'{multiple:g}x-{basis}bp','status':'complete','common_reference':ref,
                'price_multiple':multiple,'adverse_basis_bps':basis,'dated_mark':ds,'perp_mark':ps,
                'dated_pre_exit_wallet':dw,'perp_pre_exit_wallet':pw,'pre_exit_nav':dw+pw+.1*C,
                'dated_assumed_maintenance':.01*q*ds,'perp_assumed_maintenance':.01*q*ps,
                'dated_buffer':dw-.01*q*ds,'perp_buffer':pw-.01*q*ps,
                'separate_wallet_deficit':dw-.01*q*ds<0 or pw-.01*q*ps<0,
                'closed_cash':closed,'future_funding_cash':0.})
    profit=final['cash_profit'];ret=profit/C
    return {'status':'conditional','asset':asset,'capital':C,'cost_scenario':cost_scenario,'days':DAYS,
        'costs':{'futures_fee_per_side':f,'adverse_slippage_per_side':s},'initial':initial,'daily_trace':trace,
        'funding_events':events,'excluded_entry_funding_timestamps':excluded,'final_ledger':final,'held_activity':activity,
        'scalar_diagnostics':{'zero_funding':{'status':'complete','profit':final['zero_funding_same_quantity_profit']},
                              'frictionless':{'status':'complete','profit':final['frictionless_same_quantity_profit']}},
        'stress_states':stresses,'metrics':{'cash_profit':profit,'full_capital_return':ret,
            'annualized_simple_return_365':ret*365/DAYS,'max_drawdown':dd,'funding_cash':cumulative,
            'applied_funding_events':sum(map(len,days)),
            'minimum_dated_low_buffer':min(x['dated_low_buffer'] for x in trace),
            'minimum_perp_high_buffer':min(x['perp_high_buffer'] for x in trace),
            'path_wallet_deficit':any(x['dated_low_buffer']<0 or x['perp_high_buffer']<0 for x in trace),
            'stress_wallet_deficit':any(x['separate_wallet_deficit'] for x in stresses),
            'modeled_net_base_quantity':0.,'modeled_net_base_fraction_nav':0. if valid else None},
        'convention_diagnostic':{'status':'complete' if valid else 'unavailable',
            'label':'Invalid log-return arithmetic PnL shadow only; neither return sum is cash profit.',
            'valid_days':sum(x is not None for x in returns),'log1p_sum':logsum,
            'log_method':'log(NAV)-log(previous NAV), stable equivalent of log1p(simple return) for positive wallets',
            'daily_simple_return_sum':simple,'terminal_simple_return':ret,
            'log_sum_minus_terminal_return':None if logsum is None else logsum-ret},
        'assumptions':['Two linear USDT derivatives; no spot principal or notional cash credit.',
            'Fixed assumed lots, OHLC fills, USDT fees, personal product access unverified.',
            '40/50/10 independent wallets; no margin transfers or portfolio offsets.',
            'Daily extrema and1% maintenance are conditional diagnostics, not actual liquidation evidence.',
            'Stress states are invented; no calibrated tail bound, settlement, depeg or counterparty model.',
            'One spent development episode; no expected-profit confidence, power or graduation.']}
