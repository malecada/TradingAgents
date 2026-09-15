"""Pure conditional spot/cash policy books and deterministic diagnostics.

No files/network are read by this module. Caller must admit the exact panel and
freeze scenarios. USD bar marks, fees/filters and access remain conditional.
"""
from datetime import datetime, timezone, timedelta
from decimal import Decimal as D
import importlib.util
import math
from pathlib import Path
import statistics

s=importlib.util.spec_from_file_location('conditional_inventory',Path(__file__).with_name('spot_book.py'))
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
C=D('10000');DAY=86400;START=1756684800;END=1788220800
STEPS={'BTC':D('0.000001'),'ETH':D('0.00001')}
SCENARIOS={'primary':(D('.001'),D('.001'),D('10')),
           'doubled':(D('.002'),D('.002'),D('20')),
           'frictionless':(D('0'),D('0'),D('10'))}
STATIC={'B0':(0,0),'B2':(1,0),'B3':(0,1),'B4':('.5','.5'),'B5':('.25',0),
        'B6':('.5',0),'B7':('.125','.125'),'B8':('.25','.25'),'B9':('.25',0)}


def prices(row,field='open'):
    u=D(row['usd_bars'][field])
    return {'USDC':u,'BTC':D(row['btc_bars'][field])*u,'ETH':D(row['eth_bars'][field])*u}


def balances(book):return {a:book.balances.get(('cex',a),D(0)) for a in ('USDC','BTC','ETH')}


def nav(book,p,scenario,impact_multiple=D(1),dust_zero=True):
    fee,adverse,route=SCENARIOS[scenario];v=balances(book)
    total=v['USDC']*p['USDC']-route
    for a in ('BTC','ETH'):
        value=v[a]*p[a]*(1-adverse*impact_multiple)
        if dust_zero and value/p['USDC']<5:continue
        total+=value*(1-fee)
    return total


def trade(book,event,asset,side,q,p,scenario):
    fee,adverse,_=SCENARIOS[scenario]
    q=m.floor_quantity(q,STEPS[asset])
    price=p[asset]/p['USDC']*(1+adverse if side=='buy' else 1-adverse)
    if q==0 or q*price<5:return {'id':event,'asset':asset,'side':side,'skipped':True,'quantity':str(q),'reason':'modeled lot/minimum'}
    before=balances(book)
    book.trade(event,'cex',asset,'USDC',side,q,price,fee_asset='USDC',fee=q*price*fee)
    return {'id':event,'asset':asset,'side':side,'skipped':False,'quantity':str(q),'fill_usdc':str(price),
            'commission_usdc':str(q*price*fee),'commission_usd':str(q*price*fee*p['USDC']),'spread_impact_usd':str(q*p[asset]*adverse),'notional_usd':str(q*price*p['USDC']),
            'before':{k:str(v) for k,v in before.items()},'after':{k:str(v) for k,v in balances(book).items()}}


def rebalance(book,weights,p,scenario,prefix,installment=None):
    fee,adverse,_=SCENARIOS[scenario];events=[]
    if installment is not None:
        available=min(D(installment)/p['USDC'],balances(book)['USDC'])
        q=available/(p['BTC']/p['USDC']*(1+adverse)*(1+fee))
        return [trade(book,prefix+'-BTC-buy','BTC','buy',q,p,scenario)]
    n=nav(book,p,scenario)
    if n<=0:raise ValueError('nonpositive pretrade liquidation NAV')
    target={a:D(str(w))*n/p[a] for a,w in zip(('BTC','ETH'),weights)}
    for a in ('BTC','ETH'):
        excess=balances(book)[a]-target[a]
        if excess>0:events.append(trade(book,prefix+'-'+a+'-sell',a,'sell',excess,p,scenario))
    desired={a:max(D(0),target[a]-balances(book)[a]) for a in ('BTC','ETH')}
    needed=sum(q*p[a]/p['USDC']*(1+adverse)*(1+fee) for a,q in desired.items())
    scale=min(D(1),balances(book)['USDC']/needed) if needed>0 else D(0)
    for a,q in desired.items():
        if q>0:events.append(trade(book,prefix+'-'+a+'-buy',a,'buy',q*scale,p,scenario))
    return events


def instruction(policy,book,p,closes,month_index,scenario):
    if policy in STATIC:
        if policy in ('B0','B2','B3','B4','B9') and month_index>0:return None
        return {'weights':STATIC[policy]}
    if policy=='H2':
        w=balances(book)['BTC']*p['BTC']/nav(book,p,scenario)
        return {'weights':('.25',0)} if w<D('.20') or w>D('.30') else None
    if policy=='H3':
        if len(closes)<200:raise ValueError('insufficient trend warmup')
        return {'weights':('.25' if closes[-1]>sum(closes[-200:])/200 else 0,0)}
    if policy=='H4':return {'installment':'625','weights':(0,0)} if month_index<4 else None
    if policy=='H5':
        if len(closes)<61:raise ValueError('insufficient volatility warmup')
        r=[float(closes[i]/closes[i-1]-1) for i in range(len(closes)-60,len(closes))]
        vol=statistics.stdev(r)*math.sqrt(365)
        if not math.isfinite(vol) or vol<=0:raise ValueError('zero or unavailable realized volatility')
        return {'weights':(str(min(.25,.10/vol)),0),'signal_volatility':vol}
    raise ValueError('unregistered policy')


def monthly_index(stamp):
    d=datetime.fromtimestamp(stamp,timezone.utc)
    return (d.year-2025)*12+d.month-9


def next_month_decision(stamp):
    d=datetime.fromtimestamp(stamp,timezone.utc)
    candidate=d.replace(day=1,hour=0,minute=5,second=0,microsecond=0)
    if candidate.timestamp()<=stamp:
        candidate=(candidate.replace(day=28)+timedelta(days=4)).replace(day=1)
    return int(candidate.timestamp())


def stress_at(book,p,scenario,stamp,policy,history,pending=None,last_completed_prices=None,remaining_orders=None):
    origin=nav(book,p,scenario)
    if origin<=0:raise ValueError('nonpositive stress origin NAV')
    def shocked(btc,eth,usd,impact=1):
        marks={'BTC':p['BTC']*D(str(btc)),'ETH':p['ETH']*D(str(eth)),'USDC':p['USDC']*D(str(usd))}
        return nav(book,marks,scenario,D(impact))
    cases={
        'crypto-minus50':(shocked('.5','.5',1),0),
        'crypto-minus80':(shocked('.2','.2',1),0),
        'btc50-eth90':(shocked('.5','.1',1),0),
        'seven-day-outage':(shocked('.5','.5',1,5),7),
        'stable-depeg-redemption-lock':(shocked(1,1,'.8'),30),
        'combined-crypto-depeg-outage':(shocked('.5','.5','.8',5),30)}
    up={'BTC':p['BTC']*2,'ETH':p['ETH']*2,'USDC':p['USDC']}
    down={'BTC':p['BTC']*D('.8'),'ETH':p['ETH']*D('.8'),'USDC':p['USDC']}
    clone=m.SpotBook({('cex',a):q for a,q in balances(book).items()})
    peak=nav(clone,up,scenario);decision=next_month_decision(stamp);fill=decision+86100
    intervening=[]
    if remaining_orders:
        # Orders already sized at the interrupted execution retain quantities;
        # reject an unfunded remaining buy rather than invent borrowed cash.
        for j,order in enumerate(remaining_orders):
            try:intervening.append(trade(clone,'stress-remaining-'+str(j),order['asset'],order['side'],D(order['quantity']),up,scenario))
            except ValueError as exc:
                if 'insufficient funded inventory' not in str(exc):raise
                intervening.append({'skipped':True,'reason':'unfunded remaining order after shock'})
    elif pending is not None and pending[0]+86100>=stamp and pending[0]+86100<END:
        decision,act=pending
        intervening=rebalance(clone,act['weights'],up,scenario,'stress-pending',act.get('installment'))
    elif fill<END:
        # Retain only completed native closes at origin, then authored flat doubled prices.
        next_close=(stamp//DAY+1)*DAY
        extra=max(0,(decision//DAY*DAY-next_close)//DAY+1)
        synthetic_closes=history+[up['BTC']/up['USDC']]*extra
        signal_marks=up if extra>0 else (last_completed_prices or p)
        act=instruction(policy,clone,signal_marks,synthetic_closes,monthly_index(decision),scenario)
        if act is not None:intervening=rebalance(clone,act['weights'],up,scenario,'stress-month',act.get('installment'))
    terminal=nav(clone,down,scenario)
    cases['double-then-minus60']=(terminal,0)
    return {name:{'loss_fraction':str((origin-value)/origin),'loss_usd':str(origin-value),'origin_nav':str(origin),'nav':str(value),'lock_days':days} for name,(value,days) in cases.items()} | {
        'double-then-minus60':{'loss_fraction':str((origin-terminal)/origin),'loss_usd':str(origin-terminal),'origin_nav':str(origin),'nav':str(terminal),'lock_days':0,'stress_peak_drawdown':str((peak-terminal)/peak),'intervening_actions':len([r for r in intervening if not r['skipped']])},
        'total-binance-loss':{'loss_fraction':'1','loss_usd':str(origin),'origin_nav':str(origin),'nav':'0','lock_days':None,'separate_tail':True}}


def run_book(panel,policy,scenario,lagged_instructions=None,with_stress=True,progress=None,deadline=None):
    rows=panel['joined'];indexes={r['open_epoch']:i for i,r in enumerate(rows)}
    if START not in indexes or END not in indexes or len(rows)!=566:raise ValueError('fixed cohort unavailable')
    start,end=indexes[START],indexes[END]
    book=m.SpotBook({('cex','USDC'):C/prices(rows[start])['USDC']})
    states=[];events=[];decisions=[];pending=None;remaining_orders=[];max_stress={};previous=None;log_adjust=D(0);market_pnl={a:D(0) for a in ('USDC','BTC','ETH')}
    if progress is not None:progress.update(states=states,events=events,decisions=decisions,book=book,initial_balances={a:str(v) for a,v in balances(book).items()})
    def observe(stamp,phase,p,history):
        nonlocal previous,log_adjust
        if deadline is not None:
            import time
            if time.monotonic()>deadline:raise TimeoutError('cooperative financial deadline')
        if previous is not None:
            oldp,oldq=previous
            for a,q in oldq.items():
                market_pnl[a]+=q*(p[a]-oldp[a])
                ratio=p[a]/oldp[a]
                log_adjust+=q*oldp[a]*(D(str(math.log(float(ratio))))-(ratio-1))
        n=nav(book,p,scenario);q=balances(book)
        states.append({'timestamp':stamp,'phase':phase,'nav':str(n),'balances':{a:str(v) for a,v in q.items()},'prices_usd':{a:str(v) for a,v in p.items()},'crypto_fraction':str((q['BTC']*p['BTC']+q['ETH']*p['ETH'])/n)})
        previous=(p,q.copy())
        if with_stress:
            closed_p=p if phase=='close' else prices(rows[max(0,i-1)],'close')
            for name,v in stress_at(book,p,scenario,stamp,policy,history,pending,closed_p,remaining_orders).items():
                old=max_stress.get(name,{})
                max_usd=max(D(v['loss_usd']),D(old.get('maximum_loss_usd',v['loss_usd'])))
                max_peak=max(D(v.get('stress_peak_drawdown','0')),D(old.get('maximum_stress_peak_drawdown','0')))
                if not old or D(v['loss_fraction'])>D(old['loss_fraction']):max_stress[name]={**v,'origin_timestamp':stamp,'origin_phase':phase}
                max_stress[name]['maximum_loss_usd']=str(max_usd)
                max_stress[name]['maximum_stress_peak_drawdown']=str(max_peak)
    for i in range(start,end+1):
        row=rows[i];stamp=row['open_epoch'];p=prices(row);history=[D(r['btc_bars']['close']) for r in rows[:i]]
        observe(stamp,'open',p,history)
        if stamp==END:
            for j,a in enumerate(('BTC','ETH')):
                event=trade(book,'terminal-'+a,a,'sell',balances(book)[a],p,scenario);events.append(event)
                remaining_orders=[{'asset':other,'side':'sell','quantity':str(balances(book)[other])} for other in ('BTC','ETH')[j+1:] if balances(book)[other]>0]
                observe(stamp,'after-terminal-'+a,p,history)
            remaining_orders=[]
            break
        if pending is not None:
            decision,act=pending;pending=None
            m.check_action_clock(datetime.fromtimestamp(decision-300,timezone.utc).isoformat(),datetime.fromtimestamp(decision-300,timezone.utc).isoformat(),datetime.fromtimestamp(decision,timezone.utc).isoformat(),datetime.fromtimestamp(stamp,timezone.utc).isoformat(),'86100')
            # Observe after every actual asset action as required by the stress contract.
            prior_count=len(book.events)
            new=rebalance(book,act['weights'],p,scenario,'month-'+str(stamp),act.get('installment'))
            events.extend(new)
            # Reconstruct intermediate balances from signed event deltas for state checks.
            final=dict(book.balances);intermediate=dict(final)
            for e in reversed(book.events[prior_count:]):
                for k,d in e['deltas'].items():intermediate[k]-=d
            actual_orders=[order for order in new if not order['skipped']]
            try:
                for j,e in enumerate(book.events[prior_count:]):
                    for k,d in e['deltas'].items():intermediate[k]+=d
                    remaining_orders=actual_orders[j+1:]
                    book.balances=dict(intermediate);observe(stamp,'after-'+e['id'],p,history)
            finally:
                book.balances=final
                remaining_orders=[]
            previous=(p,balances(book).copy());pending=None
        date=datetime.fromtimestamp(stamp,timezone.utc)
        if date.day==1:
            decision=stamp+300;signal_p=prices(rows[i-1],'close');month=monthly_index(stamp)
            act=instruction(policy,book,signal_p,history,month,scenario) if lagged_instructions is None else (lagged_instructions[month-1]['instruction'] if month>0 else None)
            decisions.append({'decision':decision,'signal_close':stamp,'instruction':act})
            if act is not None:pending=(decision,act)
        closep=prices(row,'close');observe(stamp+DAY,'close',closep,history+[D(row['btc_bars']['close'])])
    terminal=nav(book,prices(rows[end]),scenario,dust_zero=True)
    observed=[C]+[D(s['nav']) for s in states]+[terminal];peak=observed[0];maxdd=D(0)
    for value in observed:peak=max(peak,value);maxdd=max(maxdd,(peak-value)/peak)
    daily=[D(s['nav']) for s in states if s['phase']=='open'];daily[0]=C;daily[-1]=terminal
    rolling=max([D(0)]+[(daily[i-30]-daily[i])/daily[i-30] for i in range(30,len(daily))])
    profit=terminal-C;trades=[e for e in events if not e['skipped']]
    after_actions={}
    for state in states:
        if state['phase']!='close' and state['timestamp']<END:after_actions[state['timestamp']]=state
    cashdays=sum(D(state['balances']['BTC'])==0 and D(state['balances']['ETH'])==0 for state in after_actions.values())
    exposures=[D(state['crypto_fraction']) for state in after_actions.values()]
    port_returns=[float(daily[i]/daily[i-1]-1) for i in range(1,len(daily))]
    betas={}
    for asset in ('BTC','ETH'):
        marks=[prices(r)[asset] for r in rows[start:end+1]]
        x=[float(marks[i]/marks[i-1]-1) for i in range(1,len(marks))]
        xbar=sum(x)/len(x);ybar=sum(port_returns)/len(port_returns)
        variance=sum((v-xbar)**2 for v in x)
        betas[asset]=sum((a-xbar)*(b-ybar) for a,b in zip(x,port_returns))/variance if variance>0 else None
    fee_total=sum((D(e['commission_usd']) for e in trades),D(0));impact_total=sum((D(e['spread_impact_usd']) for e in trades),D(0))
    terminal_dust=sum((q*prices(rows[end])[a] for a,q in balances(book).items() if a!='USDC'),D(0))
    cash_reconstruction=sum(market_pnl.values())-fee_total-impact_total-SCENARIOS[scenario][2]-terminal_dust
    if abs(cash_reconstruction-profit)>D('0.00000001'):raise ValueError('signed cash attribution does not reconcile')
    return {'policy':policy,'scenario':scenario,'scope':'Conditional authored costs and historical bar/USD proxies only','net_cash_profit_usd':str(profit),'simple_net_return':str(profit/C),'terminal_liquidation_usd':str(terminal),
        'observed_discrete_max_drawdown':str(maxdd),'worst_rolling_30day_loss':str(rolling),'terminal_loss_fraction':str(max(D(0),-profit/C)),
        'absolute_floor_pass_conditional':profit>=C*D('.10'),'mean_crypto_fraction':str(sum(exposures)/len(exposures)),'max_crypto_fraction':str(max(D(state['crypto_fraction']) for state in states)),'mean_exposure_and_cash_days_sampling':'daily open after scheduled actions; maximum uses all retained states',
        'cash_days':cashdays,'active_days':365-cashdays,'turnover_usd':str(sum(D(e['notional_usd']) for e in trades)),'trade_count':len(trades),
        'cash_attribution':{'market_pnl_usd':{a:str(v) for a,v in market_pnl.items()},'commission_usd':str(fee_total),'spread_impact_usd':str(impact_total),'terminal_route_usd':str(SCENARIOS[scenario][2]),'terminal_dust_markdown_usd':str(terminal_dust),'reconstructed_profit_usd':str(cash_reconstruction)},
        'states':states,'events':events,'decisions':decisions,'stress':max_stress,
        'log_convention_diagnostic':{'never_booked_as_cash':True,'difference_usd':str(log_adjust),'erroneous_log_path_profit_usd':str(profit+log_adjust),'absolute_floor_classification_changed':(profit>=C*D('.10'))!=((profit+log_adjust)>=C*D('.10'))},
        'implementation_admitted':False,'promotion_admitted':False,'actual_B1_comparison':'unavailable','actual_continuous_drawdown':'unavailable','descriptive_univariate_daily_proxy_beta':betas,'complete_tail_loss_fraction':'1'}
