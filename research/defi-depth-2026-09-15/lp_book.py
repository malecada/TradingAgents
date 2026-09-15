"""Pure F3 full usable-range historical-path attribution and matched inventory.

No acquisition. Attributed fees assume the historical path remains unchanged by
added liquidity. This is not a counterfactual execution/capacity model. Native
ETH and WETH remain distinct balances with an explicit parity-mark assumption.
"""
from fractions import Fraction as F
from decimal import Decimal
from datetime import date, timedelta
import importlib.util
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result

W=module('lp_wallet_helpers','wrapper_book.py')
M=W.M
T=module('lp_exact_ticks','v3_ticks.py')
S=module('lp_exact_stress','protocol_stress.py')
R=module('lp_literal_receipts','literal_receipts.py')
LOW,HIGH=T.position_bounds(-887220,887220,60)
MAX_TICK_LIQUIDITY=((1<<128)-1)//29575
ASSETS={a:W.ASSETS[a] for a in ('USDC','ETH')}
ASSETS['WETH']=('base','0x4200000000000000000000000000000000000006')
ASSETS['LP']=('base','0x6c561b446416e1a00e8e93e221854d6ea4171372:liquidity:-887220:887220')
SCALE={'ETH':10**18,'WETH':10**18,'USDC':10**6}
CAPITAL,RESERVE=W.CAPITAL,W.RESERVE
FinancialUnavailable=W.FinancialUnavailable
POLICIES=('F3','matched-entry-inventory')


def amounts(book):
    out={}
    for a,k in ASSETS.items():
        value=book.balances.get(k,Decimal(0))
        if value!=int(value):raise ValueError('noninteger protocol atoms')
        out[a]=int(value)
    return out


def validate_panel(panel):
    if len(panel)!=366:raise ValueError('complete fixed annual panel required')
    for i,row in enumerate(panel):
        if row['date']!=(date(2025,9,1)+timedelta(days=i)).isoformat():raise ValueError('fixed calendar mismatch')
        if set(row['prices'])!={'ETH','WETH','USDC'} or any(
            not isinstance(p,(F,int)) or isinstance(p,bool) or p<=0 for p in row['prices'].values()
        ):raise ValueError('positive exact marks with native/wrapped identities required')
        if row['prices']['ETH']!=row['prices']['WETH']:
            raise FinancialUnavailable('explicit parity-mark model not satisfied')
        for field in ('growth0','growth1'):M.uint(row[field])
        M.uint(row['liquidity'],128);M.uint(row['sqrt_price'],160)
        if not T.MIN_SQRT<=row['sqrt_price']<T.MAX_SQRT:raise ValueError('sqrt price outside protocol domain')
        if type(row['tick']) is not int or not -887272<=row['tick']<=887272:raise ValueError('invalid tick')
        # slot0 tick can be the left tick at an exact crossed boundary.
        implied_low=T.sqrt_at_tick(row['tick'])
        implied_high=T.sqrt_at_tick(row['tick']+1) if row['tick']<887272 else T.MAX_SQRT
        if not implied_low<=row['sqrt_price']<=implied_high:raise ValueError('tick and sqrt price disagree')
        if row.get('source_model_qualified') is not True:
            raise FinancialUnavailable('pool identity/version/fee/spacing model unqualified')
        if row.get('unlocked') is not True:raise FinancialUnavailable('observed pool locked')


def claims(q,row,entry):
    if not q['LP']:return (0,0),(0,0)
    if entry is None:raise ValueError('LP receipt without entry growth origin')
    principal=M.lp_amounts(q['LP'],row['sqrt_price'],LOW,HIGH,mint=False)
    fees=(M.lp_fees(q['LP'],entry['growth0'],row['growth0']),
          M.lp_fees(q['LP'],entry['growth1'],row['growth1']))
    # burn principal joins already-owed fees in uint128 before collect.
    M.uint(principal[0]+fees[0],128);M.uint(principal[1]+fees[1],128)
    return principal,fees


def underlying(q,row,entry):
    principal,fees=claims(q,row,entry)
    return {'USDC':q['USDC']+principal[1]+fees[1], 'WETH':q['WETH']+principal[0]+fees[0], 'ETH':q['ETH']}


def value_underlying(q,p):
    return sum((F(q[a],SCALE[a])*p[a] for a in SCALE),F(0))


def mark(q,row,entry):return value_underlying(underlying(q,row,entry),row['prices'])


def buy_debit(weth,p,cost):
    """USDC atoms required to fund exact WETH mint atoms in the authored model."""
    factor=(1-cost['haircut'])/(1+cost['adverse'])
    exact=F(weth,10**18)*p['WETH']/p['USDC']*10**6/factor
    return (exact.numerator+exact.denominator-1)//exact.denominator


def entry_plan(budget,row,cost):
    M.uint(budget)
    if not budget:raise FinancialUnavailable('zero LP sleeve budget')
    # Monotonic funded constraint; no outcomes or tunable range/weight selection.
    def debit(liquidity):
        a,b=M.lp_amounts(liquidity,row['sqrt_price'],LOW,HIGH,mint=True)
        return b+buy_debit(a,row['prices'],cost)
    low,high=0,(1<<127)-1
    while low<high:
        middle=(low+high+1)//2
        if debit(middle)<=budget:low=middle
        else:high=middle-1
    if not low:raise FinancialUnavailable('funded sleeve mints no liquidity')
    a,b=M.lp_amounts(low,row['sqrt_price'],LOW,HIGH,mint=True)
    if not a or not b:raise FinancialUnavailable('registered two-sided entry inventory unavailable')
    return {'liquidity':low,'weth_atoms':a,'usdc_atoms':b,
            'weth_purchase_usdc_atoms':buy_debit(a,row['prices'],cost),'sleeve_budget_atoms':budget,
            'unused_sleeve_usdc_atoms':budget-b-buy_debit(a,row['prices'],cost)}


def qualify_mint(plan,row):
    for field in ('lower_gross','upper_gross'):M.uint(row[field],128)
    if row.get('max_tick_liquidity')!=MAX_TICK_LIQUIDITY:
        raise FinancialUnavailable('spacing60 mint-limit identity unavailable')
    if any(row[field]+plan['liquidity']>MAX_TICK_LIQUIDITY for field in ('lower_gross','upper_gross')):
        raise FinancialUnavailable('observed full-range boundary mint headroom inadequate')
    if row['liquidity']+plan['liquidity']>=(1<<128):
        raise FinancialUnavailable('observed active-liquidity headroom inadequate')


def liquidation(q,row,entry,cost):
    q=dict(q);ops=[]
    if q['LP']:
        principal,fees=claims(q,row,entry)
        if q['ETH']<2*cost['gas']:raise FinancialUnavailable('unfunded LP burn/collect gas')
        credits={'WETH':principal[0]+fees[0],'USDC':principal[1]+fees[1]}
        # The two tx debit represents burn then collect with no in-between yield.
        ops.append({'id':'burn-collect','debits':{'LP':q['LP']},'credits':credits,'gas':2*cost['gas']})
        q['ETH']-=2*cost['gas'];q['LP']=0
        for a,v in credits.items():q[a]+=v
    if q['WETH']:
        if q['ETH']<2*cost['gas']:raise FinancialUnavailable('unfunded WETH approval/sale gas')
        receive=W.floor(F(q['WETH'],10**18)*row['prices']['WETH']/row['prices']['USDC']*10**6*(1-cost['haircut'])*(1-cost['adverse']))
        ops.append({'id':'weth-exit','debits':{'WETH':q['WETH']},'credits':{'USDC':receive},'gas':2*cost['gas']})
        q['ETH']-=2*cost['gas'];q['USDC']+=receive;q['WETH']=0
    if q['ETH']:
        if q['ETH']<=cost['gas']:raise FinancialUnavailable('unfunded native gas-reserve sale')
        sold=q['ETH']-cost['gas'];receive=W.sell_value(sold,'ETH',row['prices'],cost)
        ops.append({'id':'native-exit','debits':{'ETH':sold},'credits':{'USDC':receive},'gas':cost['gas']})
        q['USDC']+=receive;q['ETH']=0
    return F(q['USDC'],10**6)*row['prices']['USDC']-cost['route'],q,ops


def stress(q,row,entry,cost):
    origin=liquidation(q,row,entry,cost)[0]
    if origin<=0:raise ValueError('nonpositive stress origin')
    out={}
    scenarios={'eth-minus50':(F(1,2),F(1),1,0),'eth-minus80':(F(1,5),F(1),1,0),
       'eth-minus90':(F(1,10),F(1),1,0),'stable-depeg-lock30':(F(1),F(4,5),1,30),
       'seven-day-outage':(F(1,2),F(1),5,7),'combined-depeg-outage':(F(1,10),F(4,5),5,30)}
    def shocked_value(eth,usd,impact=1):
        r={**row,'prices':{'ETH':row['prices']['ETH']*eth,'WETH':row['prices']['WETH']*eth,'USDC':row['prices']['USDC']*usd},
           'sqrt_price':S.shocked_sqrt_price(row['sqrt_price'],eth,usd,operating_arbitrage_path=True)}
        return liquidation(q,r,entry,{**cost,'adverse':cost['adverse']*impact})[0]
    for name,(eth,usd,impact,delay) in scenarios.items():
        end=shocked_value(eth,usd,impact)
        out[name]={'loss_fraction':(origin-end)/origin,'loss_usd':origin-end,'delayed_days':delay,
                  'horizon_cash_unavailable_during_lock':bool(delay),'incremental_shock_fees':0}
    peak=shocked_value(F(2),F(1));end=shocked_value(F(4,5),F(1))
    out['double-then-minus60']={'loss_fraction':(origin-end)/origin,'loss_usd':origin-end,'peak_drawdown':(peak-end)/peak,'delayed_days':0}
    out['total-wallet-loss']={'loss_fraction':F(1),'loss_usd':origin,'separate_tail':True}
    lost={**q,'LP':0}
    loss=origin-liquidation(lost,row,entry,cost)[0]
    principal,fees=claims(q,row,entry)
    affected=F(principal[0]+fees[0],10**18)*row['prices']['WETH']+F(principal[1]+fees[1],10**6)*row['prices']['USDC']
    out['total-pool-position-loss']={'loss_fraction':loss/origin,'loss_usd':loss,'gross_affected_mark_usd':affected,'separate_tail':True}
    return out


def run_book(panel,policy,scenario,progress=None):
    validate_panel(panel)
    if policy not in POLICIES or scenario not in W.SCENARIOS:raise ValueError('unregistered LP book')
    cost=W.SCENARIOS[scenario];p0=panel[0]['prices']
    usdc=W.floor((CAPITAL-F(RESERVE,10**18)*p0['ETH'])/p0['USDC']*10**6)
    if usdc<=0:raise FinancialUnavailable('gas reserve exhausts capital')
    initial={'USDC':usdc,'ETH':RESERVE,'WETH':0,'LP':0}
    book=M.ProtocolBook({ASSETS[a]:q for a,q in initial.items()})
    formation=CAPITAL-mark(initial,panel[0],None)
    states,events,maxima=[],[],{}
    market=inventory=fee_accrual=event_loss=log_adjust=F(0)
    previous=entry=plan=log_error=None
    max_daily_participation=F(0);zero_liquidity_dates=[]
    if progress is not None:progress.update(book=book,initial_atoms=initial,formation_loss=formation,states=states,events=events,stress_maxima=maxima,zero_liquidity_dates=zero_liquidity_dates)

    def checkpoint():
        if progress is not None:progress.update(market=market,inventory=inventory,fee_accrual=fee_accrual,event_loss=event_loss)

    def observe(row,phase):
        nonlocal market,inventory,fee_accrual,previous,log_adjust,log_error,max_daily_participation
        if progress is not None:progress.update(current_date=row['date'],current_phase=phase,current_source_row=R.json_safe(row))
        q=amounts(book);p=row['prices']
        if previous is not None:
            oldq,oldrow=previous
            oldunder=underlying(oldq,oldrow,entry)
            market+=sum((F(oldunder[a],SCALE[a])*(p[a]-oldrow['prices'][a]) for a in SCALE),F(0))
            oldprincipal,oldfees=claims(oldq,oldrow,entry)
            newprincipal,newfees=claims(oldq,row,entry)
            for j,a in enumerate(('WETH','USDC')):
                if newfees[j]<oldfees[j]:raise FinancialUnavailable('cumulative attributed fees decrease; counter path unqualified')
                inventory+=F(newprincipal[j]-oldprincipal[j],SCALE[a])*p[a]
                fee_accrual+=F(newfees[j]-oldfees[j],SCALE[a])*p[a]
            # Isolated convention swap on total pre-event held wealth. LP quantity
            # transformations remain part of the simple marked change, not extra IL.
            oldvalue=mark(oldq,oldrow,entry);newvalue=mark(oldq,row,entry)
            if oldvalue>0 and newvalue>0 and oldvalue!=newvalue and log_error is None:
                ratio=newvalue/oldvalue
                try:log_adjust+=oldvalue*(F(str(math.log(float(ratio))))-(ratio-1))
                except (ValueError,OverflowError,ZeroDivisionError) as exc:log_error=type(exc).__name__+': '+str(exc)
        checkpoint()
        if progress is not None:progress.update(current_date=row['date'],current_phase=phase)
        value=liquidation(q,row,entry,cost)[0]
        principal,fees=claims(q,row,entry)
        states.append({'date':row['date'],'phase':phase,'atoms':q,'principal_atoms':list(principal),'cumulative_fee_atoms':list(fees),
                       'sqrt_price':row['sqrt_price'],'prices':{a:W.fraction_record(p[a]) for a in p},
                       'liquidation_usd':W.fraction_record(value)})
        if q['LP']:
            if not row['liquidity']:
                if row['date'] not in zero_liquidity_dates:zero_liquidity_dates.append(row['date'])
            else:max_daily_participation=max(max_daily_participation,F(q['LP'],row['liquidity']))
        for name,r in stress(q,row,entry,cost).items():
            old=maxima.get(name)
            if old is None or r['loss_fraction']>old['loss_fraction']:maxima[name]={**r,'date':row['date'],'phase':phase}
            maxima[name]['maximum_peak_drawdown']=max(r.get('peak_drawdown',F(0)),(old or {}).get('maximum_peak_drawdown',F(0)))
        previous=(q,row)

    def post(row,event,debits,credits,gas):
        nonlocal event_loss,previous
        before=amounts(book)
        if before['ETH']<gas+debits.get('ETH',0):raise FinancialUnavailable('prefunded gas inadequate')
        # Zero inventory on one side is valid after leaving the range.
        credits={a:v for a,v in credits.items() if v}
        if not credits:raise FinancialUnavailable('conversion has no positive received atoms')
        book.convert(event,{ASSETS[a]:v for a,v in debits.items()},{ASSETS[a]:v for a,v in credits.items()},
                     fee_key=ASSETS['ETH'],fee=gas,evidence='F3 conditional historical-path inventory/fee attribution; authored execution costs')
        after=amounts(book);loss=mark(before,row,entry)-mark(after,row,entry)
        event_loss+=loss
        events.append({'id':event,'date':row['date'],'debits_atoms':debits,'credits_atoms':credits,'gas_atoms':gas,
                       'before_atoms':before,'after_atoms':after,'marked_loss_usd':W.fraction_record(loss)})
        checkpoint();previous=(after,row);observe(row,'after-'+event)

    for i,row in enumerate(panel):
        observe(row,'daily')
        if i==1:
            entry=row
            plan=entry_plan(usdc//2,row,cost)
            # The control holds precisely the funded candidate entry quantities.
            # Mint headroom qualifies the candidate only, not the control purchase.
            if policy=='F3':qualify_mint(plan,row)
            post(row,'weth-entry',{'USDC':plan['weth_purchase_usdc_atoms']},{'WETH':plan['weth_atoms']},2*cost['gas'])
            if policy=='F3':
                post(row,'lp-mint',{'WETH':plan['weth_atoms'],'USDC':plan['usdc_atoms']},{'LP':plan['liquidity']},3*cost['gas'])
        if i==365:
            expected,terminal,operations=liquidation(amounts(book),row,entry,cost)
            for op in operations:post(row,op['id'],op['debits'],op['credits'],op['gas'])
            if amounts(book)!=terminal:raise ValueError('terminal LP atom plan differs')
            ending=mark(terminal,row,entry)-cost['route']
            if ending!=expected:raise ValueError('terminal LP liquidation differs')
    profit=ending-CAPITAL
    reconstruction=market+inventory+fee_accrual-event_loss-formation-cost['route']
    if reconstruction!=profit:raise ValueError('LP cash conservation failure')
    peak,dd=CAPITAL,F(0)
    for state in states:
        value=F(state['liquidation_usd']['numerator'],state['liquidation_usd']['denominator'])
        peak=max(peak,value);dd=max(dd,(peak-value)/peak)
    daily=[F(r['liquidation_usd']['numerator'],r['liquidation_usd']['denominator']) for r in states if r['phase']=='daily']
    daily[0],daily[-1]=CAPITAL,ending
    rolling=max([F(0)]+[(daily[i-30]-daily[i])/daily[i-30] for i in range(30,len(daily))])
    numerical=max(F(0),*(r['loss_fraction'] for r in maxima.values() if not r.get('separate_tail')))
    return {'policy':policy,'scenario':scenario,'net_cash_profit_usd':W.render(profit),'exact_net_cash_profit':W.fraction_record(profit),
      'terminal_liquidation_usd':W.render(ending),'simple_net_return':W.render(profit/CAPITAL),
      'initial_atoms':initial,'terminal_atoms':amounts(book),'entry_plan':plan,
      'cash_attribution':{'market_usd':W.render(market),'inventory_transformation_usd':W.render(inventory),
        'fee_entitlement_change_usd':W.render(fee_accrual),'conversion_gas_rounding_loss_usd':W.render(event_loss),
        'formation_loss_usd':W.render(formation),'route_usd':W.render(cost['route']),'reconstructed_profit':W.fraction_record(reconstruction)},
      'observed_discrete_max_drawdown':W.render(dd),'worst_rolling_30day_loss':W.render(rolling),
      'numerical_stress_max_loss':W.render(numerical),'absolute_floor_pass_conditional':profit>=1000,
      'numerical_risk_pass_conditional':dd<=F(3,10) and numerical<=F(1,2),'states':states,'events':events,
      'stress':{name:{k:W.render(v) if isinstance(v,F) else v for k,v in r.items()} for name,r in maxima.items()},
      'log_convention_diagnostic':{'status':'unavailable' if log_error else 'complete','reason':log_error,'never_booked_as_cash':True,
          'difference_usd':None if log_error else W.render(log_adjust),'erroneous_profit_usd':None if log_error else W.render(profit+log_adjust)},
      'maximum_sampled_virtual_to_historical_liquidity':W.render(max_daily_participation),
      'sampled_zero_historical_liquidity_dates':zero_liquidity_dates,
      'sampled_liquidity_does_not_bound_intraday_capacity':True,'implementation_admitted':False,'promotion_admitted':False,
      'actual_horizon_cash_under_locks':'unavailable',
      'scope':'Historical-path full-range LP attribution; fee dilution/path impact/native-WETH parity/executable prices unproved'}


def partial_snapshot(progress):
    exact=('formation_loss','market','inventory','fee_accrual','event_loss')
    result={k:v for k,v in progress.items() if k not in ('book',)+exact}
    for k in exact:
        if k in progress:result[k]=W.fraction_record(progress[k])
    if 'book' in progress:
        result.update(R.snapshot(progress['book'],progress['initial_atoms'],ASSETS))
        result['valued_events_cover_literal_events']=len(progress['events'])==len(progress['book'].events)
    return R.json_safe(result)
