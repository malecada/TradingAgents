"""Pure conditional F2 wallet book. Exact atoms/Fractions, no data acquisition.

Oracle marks and authored costs are inputs to a scenario, never witnessed fills.
The existing funded ProtocolBook holds atoms with explicit asset identities.
"""
from decimal import Decimal, localcontext
from fractions import Fraction as F
import importlib.util
import math
from pathlib import Path
S=importlib.util.spec_from_file_location('wrapper_protocol_math',Path(__file__).with_name('protocol_math.py'))
M=importlib.util.module_from_spec(S);S.loader.exec_module(M)
ASSETS={'USDC':('base','0x833589fcd6edb6e08f4c7c32d4f71b54bda02913'),
        'ETH':('base','native-ETH'), 'WST':('base','0xc1cba3fcea344f92d9239c08c0568f6f2f0ee452')}
SCALE={'USDC':10**6,'ETH':10**18,'WST':10**18}
CAPITAL=F(10000);RESERVE=5*10**15
SCENARIOS={'primary':{'gas':10**14,'haircut':F(3,1000),'adverse':F(1,1000),'route':F(10)},
'doubled':{'gas':2*10**14,'haircut':F(6,1000),'adverse':F(2,1000),'route':F(20)},
'frictionless':{'gas':0,'haircut':F(0),'adverse':F(0),'route':F(10)}}
POLICIES=('F2','wallet-ETH25','wallet-cash')

class FinancialUnavailable(ValueError):
    """Authored capital/execution feasibility fails for this cell only."""

def floor(x): return x.numerator//x.denominator

def render(x):
    x=F(x)
    with localcontext() as ctx:
        ctx.prec=45
        return format(Decimal(x.numerator)/Decimal(x.denominator),'f')

def fraction_record(x):
    x=F(x);return {'numerator':x.numerator,'denominator':x.denominator,'decimal':render(x)}

def amounts(book):
    result={}
    for a,k in ASSETS.items():
        value=book.balances.get(k,Decimal(0))
        if value!=int(value): raise ValueError('noninteger atom balance')
        result[a]=int(value)
    return result

def mark(q,p): return sum((F(q[a],SCALE[a])*p[a] for a in ASSETS),F(0))

def validate_panel(panel):
    if len(panel)!=366: raise ValueError('complete fixed 366-mark annual panel required')
    from datetime import date,timedelta
    start=date(2025,9,1)
    for i,row in enumerate(panel):
        if row['date']!=(start+timedelta(days=i)).isoformat(): raise ValueError('calendar gap or clock mismatch')
        if set(row['prices'])!=set(ASSETS): raise ValueError('all USD marks required')
        if any(not isinstance(v,(F,int)) or isinstance(v,bool) or v<=0 for v in row['prices'].values()): raise ValueError('positive exact rational marks required')

def sell_value(q,a,p,cost):
    hops=2 if a=='WST' else 1
    factor=((1-cost['haircut'])*(1-cost['adverse']))**hops
    return floor(F(q,SCALE[a])*p[a]/p['USDC']*SCALE['USDC']*factor)

def liquidation(q,p,cost):
    """Hypothetical immediate exit. Return exact USD value and residual atoms.

    WST approval+multihop sale cost two transactions; native sale one. A sale
    consumes its own gas from prefunded ETH. All dust is retained and valued.
    """
    q=dict(q);gas=cost['gas'];operations=[]
    if q['WST']:
        if q['ETH']<2*gas: raise FinancialUnavailable('insufficient gas for wrapper exit')
        receive=sell_value(q['WST'],'WST',p,cost)
        operations.append({'asset':'WST','sold_atoms':q['WST'],'received_usdc_atoms':receive,'gas_atoms':2*gas})
        q['ETH']-=2*gas;q['USDC']+=receive;q['WST']=0
    if q['ETH']:
        if q['ETH']<=gas: raise FinancialUnavailable('insufficient gas for native terminal sale')
        sold=q['ETH']-gas;receive=sell_value(sold,'ETH',p,cost)
        operations.append({'asset':'ETH','sold_atoms':sold,'received_usdc_atoms':receive,'gas_atoms':gas})
        q['ETH']=0;q['USDC']+=receive
    value=F(q['USDC'],10**6)*p['USDC']-cost['route']
    return value,q,operations

def stress(q,p,cost):
    origin=liquidation(q,p,cost)[0]
    if origin<=0: raise ValueError('nonpositive stress origin')
    shocks={'crypto-minus50':(F(1,2),F(1,2),F(1),1,0),
      'crypto-minus80':(F(1,5),F(1,5),F(1),1,0),
      'eth-minus90':(F(1,10),F(1,10),F(1),1,0),
      'wrapper-discount30':(F(1),F(7,10),F(1),1,0),
      'eth50-wrapper-discount30':(F(1,2),F(7,20),F(1),1,0),
      'stable-depeg-lock30':(F(1),F(1),F(4,5),1,30),
      'seven-day-outage':(F(1,2),F(7,20),F(1),5,7),
      'combined-depeg-outage':(F(1,2),F(7,20),F(4,5),5,30)}
    result={}
    for name,(eth,wst,usd,impact,delay) in shocks.items():
        marks={'ETH':p['ETH']*eth,'WST':p['WST']*wst,'USDC':p['USDC']*usd}
        stressed={**cost,'adverse':cost['adverse']*impact}
        value=liquidation(q,marks,stressed)[0]
        result[name]={'loss_fraction':(origin-value)/origin,'loss_usd':origin-value,'delayed_days':delay,
                      'horizon_cash_unavailable_during_lock':bool(delay)}
    up={**p,'ETH':p['ETH']*2,'WST':p['WST']*2}
    down={**p,'ETH':p['ETH']*F(4,5),'WST':p['WST']*F(4,5)}
    peak=liquidation(q,up,cost)[0];end=liquidation(q,down,cost)[0]
    result['double-then-minus60']={'loss_fraction':(origin-end)/origin,'loss_usd':origin-end,'peak_drawdown':(peak-end)/peak,'delayed_days':0}
    # Total affected position failures are separate tails; actual losses always enter NAV.
    result['total-wallet-loss']={'loss_fraction':F(1),'loss_usd':origin,'separate_tail':True}
    lost=dict(q);lost['WST']=0
    loss=origin-liquidation(lost,p,cost)[0]
    result['total-wrapper-position-loss']={'loss_fraction':loss/origin,
       'loss_usd':loss,'gross_affected_mark_usd':F(q['WST'],10**18)*p['WST'],'separate_tail':True}
    return result

def run_book(panel,policy,scenario,progress=None):
    validate_panel(panel)
    if policy not in POLICIES or scenario not in SCENARIOS: raise ValueError('unregistered book')
    c=SCENARIOS[scenario];p0=panel[0]['prices']
    usdc=floor((CAPITAL-F(RESERVE,10**18)*p0['ETH'])/p0['USDC']*10**6)
    if usdc<=0: raise FinancialUnavailable('gas reserve exhausts capital')
    initial={'USDC':usdc,'ETH':RESERVE,'WST':0}
    book=M.ProtocolBook({ASSETS[a]:q for a,q in initial.items()})
    formation=CAPITAL-mark(initial,p0)
    if formation<0: raise ValueError('formation creates capital')
    states=[];market=F(0);event_loss=F(0);log_adjust=F(0);previous=None;max_stress={}
    economic_events=[];log_error=None
    if progress is not None:progress.update(book=book,states=states,events=economic_events,initial_atoms=initial,formation_loss=formation)
    def checkpoint():
        if progress is not None:progress.update(market=market,event_loss=event_loss)
    def observe(date,phase,p):
        nonlocal market,previous,log_adjust,log_error
        q=amounts(book)
        if previous is not None:
            oldq,oldp=previous
            for a in ASSETS:
                market+=F(oldq[a],SCALE[a])*(p[a]-oldp[a])
                ratio=p[a]/oldp[a]
                if oldq[a] and ratio!=1 and log_error is None:
                    try:log_adjust+=F(oldq[a],SCALE[a])*oldp[a]*(F(str(math.log(float(ratio))))-(ratio-1))
                    except (ValueError,OverflowError,ZeroDivisionError) as exc:log_error=type(exc).__name__+': '+str(exc)
        checkpoint()
        if progress is not None:progress.update(current_date=date,current_phase=phase,current_prices={a:fraction_record(v) for a,v in p.items()})
        value=liquidation(q,p,c)[0]
        states.append({'date':date,'phase':phase,'atoms':dict(q),'prices':{a:fraction_record(p[a]) for a in ASSETS},'liquidation_usd':fraction_record(value)})
        for name,row in stress(q,p,c).items():
            old=max_stress.get(name)
            if old is None or row['loss_fraction']>old['loss_fraction']:
                max_stress[name]={**row,'date':date,'phase':phase}
            max_stress[name]['maximum_peak_drawdown']=max(row.get('peak_drawdown',F(0)),(old or {}).get('maximum_peak_drawdown',F(0)))
        checkpoint()
        previous=(q,dict(p))
    def post(date,p,event,debits,credits,gas):
        nonlocal event_loss,previous
        before=amounts(book);value=mark(before,p)
        book.convert(event,{ASSETS[a]:v for a,v in debits.items()},
                     {ASSETS[a]:v for a,v in credits.items()},fee_key=ASSETS['ETH'],fee=gas,
                     evidence='F2 frozen hypothetical swap; oracle marks are not witnessed fills')
        after=amounts(book);loss=value-mark(after,p)
        event_loss+=loss
        economic_events.append({'id':event,'date':date,'debits_atoms':debits,'credits_atoms':credits,'gas_atoms':gas,'before_atoms':before,'after_atoms':after,'marked_loss_usd':fraction_record(loss)})
        checkpoint()
        previous=(after,dict(p))
        observe(date,'after-'+event,p)
    for i,row in enumerate(panel):
        date,p=row['date'],row['prices'];observe(date,'daily',p)
        if i==1 and policy!='wallet-cash':
            a='WST' if policy=='F2' else 'ETH';hops=2 if a=='WST' else 1
            budget=usdc//4
            factor=((1-c['haircut'])/(1+c['adverse']))**hops
            bought=floor(F(budget,10**6)*p['USDC']/p[a]*SCALE[a]*factor)
            if not bought: raise FinancialUnavailable('entry amount rounds to zero')
            post(date,p,'entry',{'USDC':budget},{a:bought},2*c['gas'])
        if i==365:
            expected,terminal,operations=liquidation(amounts(book),p,c)
            for index,op in enumerate(operations):
                if not op['received_usdc_atoms']: raise FinancialUnavailable('terminal positive sale rounds to zero')
                post(date,p,'exit-'+str(index),{op['asset']:op['sold_atoms']},{'USDC':op['received_usdc_atoms']},op['gas_atoms'])
            if amounts(book)!=terminal: raise ValueError('terminal atoms differ from liquidation plan')
            ending=mark(terminal,p)-c['route']
            if ending!=expected: raise ValueError('terminal wealth differs')
    profit=ending-CAPITAL
    reconstruction=market-event_loss-formation-c['route']
    if reconstruction!=profit: raise ValueError('cash conservation failure')
    values=[CAPITAL]+[F(r['liquidation_usd']['numerator'],r['liquidation_usd']['denominator']) for r in states]
    peak=CAPITAL;dd=F(0)
    for v in values:
        peak=max(peak,v);dd=max(dd,(peak-v)/peak)
    daily=[F(r['liquidation_usd']['numerator'],r['liquidation_usd']['denominator']) for r in states if r['phase']=='daily']
    daily[0]=CAPITAL;daily[-1]=ending
    rolling=max([F(0)]+[(daily[i-30]-daily[i])/daily[i-30] for i in range(30,len(daily))])
    # Delayed-exit stresses are marks after an authored lock, not guaranteed day365 cash.
    numerical_stress=max(F(0),*(row['loss_fraction'] for row in max_stress.values() if not row.get('separate_tail')))
    risk=dd<=F(3,10) and numerical_stress<=F(1,2)
    def printable(row): return {k:render(v) if isinstance(v,F) else v for k,v in row.items()}
    return {'policy':policy,'scenario':scenario,'net_cash_profit_usd':render(profit),'simple_net_return':render(profit/CAPITAL),
      'exact_net_cash_profit':fraction_record(profit),'terminal_liquidation_usd':render(ending),'initial_atoms':initial,'terminal_atoms':amounts(book),
      'formation_rounding_loss_usd':render(formation),'cash_attribution':{'market_usd':render(market),'swap_gas_rounding_loss_usd':render(event_loss),'formation_loss_usd':render(formation),'route_usd':render(c['route']),'reconstructed_profit':fraction_record(reconstruction)},
      'observed_discrete_max_drawdown':render(dd),'worst_rolling_30day_loss':render(rolling),'numerical_stress_max_loss':render(numerical_stress),
      'absolute_floor_pass_conditional':profit>=1000,'numerical_risk_pass_conditional':risk,'events':economic_events,'states':states,
      'stress':{k:printable(v) for k,v in max_stress.items()},'log_convention_diagnostic':{'status':'unavailable' if log_error else 'complete','reason':log_error,'never_booked_as_cash':True,'difference_usd':None if log_error else render(log_adjust),'erroneous_profit_usd':None if log_error else render(profit+log_adjust)},
      'implementation_admitted':False,'promotion_admitted':False,'actual_horizon_cash_under_locks':'unavailable',
      'scope':'Conditional oracle-price/hypothetical wallet execution; no native staking, queue, execution or confirmation claim'}


def partial_snapshot(progress):
    result={k:v for k,v in progress.items() if k not in ('book','formation_loss','market','event_loss')}
    for key in ('formation_loss','market','event_loss'):
        if key in progress:result[key]=fraction_record(progress[key])
    if 'book' in progress:
        result['current_atoms']=amounts(progress['book'])
        replay=dict(progress['initial_atoms'])
        for event in progress['events']:
            for a,q in event['debits_atoms'].items():replay[a]-=q
            for a,q in event['credits_atoms'].items():replay[a]+=q
            replay['ETH']-=event['gas_atoms']
        result['literal_balances_reconciled']=replay==result['current_atoms']
        if not result['literal_balances_reconciled']:raise ValueError('partial atom replay differs')
    return result
