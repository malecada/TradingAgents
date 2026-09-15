"""Pure frozen eight-case analysis; coordinator admission must precede calling.

No source request, filesystem publication, model fitting or parameter selection.
A single conditional episode cannot establish expected profit or true tail risk.
"""
from fractions import Fraction as F
import math
from . import adapter
from .schedule import ASSETS, HOUR, DAY

ENGINE = adapter._policy('options_policy_engine')
COSTS = {
    'base': {'option_fee_rate':'0.00024','perp_fee_rate':'0.0005','perp_slippage':'0.0002'},
    'stress': {'option_fee_rate':'0.00030','perp_fee_rate':'0.001','perp_slippage':'0.0004'},
}
CELLS = tuple(f'{asset.lower()}-{capital}-{cost}' for asset in ASSETS for capital in (1000,10000) for cost in COSTS)


def beta(y,x):
    """Marginal OLS with Bartlett Newey-West L=24 and fixed normal interval.

    Two market coefficients use Bonferroni 95% simultaneous nominal intervals.
    These descriptive asymptotics are not fresh independent-episode inference.
    """
    n=len(y)
    if n!=len(x) or n<72 or any(not math.isfinite(v) for v in y+x):return {'status':'unavailable','reason':'72 complete consecutive hourly returns required'}
    xm=sum(x)/n;ym=sum(y)/n;z=[v-xm for v in x];ss=sum(v*v for v in z)
    if ss<=1e-20:return {'status':'unavailable','reason':'benchmark variance unavailable'}
    b=sum(a*(v-ym) for a,v in zip(z,y))/ss
    score=[a*(v-ym-b*a) for a,v in zip(z,y)]
    meat=sum(v*v for v in score)
    for lag in range(1,25):meat+=2*(1-lag/25)*sum(score[i]*score[i-lag] for i in range(lag,n))
    se=math.sqrt(max(0,meat)*n/(n-2))/ss
    return {'status':'descriptive','coefficient':b,'hac_standard_error':se,'interval':[b-2.2414027276*se,b+2.2414027276*se],
            'observations':n,'lags':24,'qualification':'Marginal hourly OLS; nominal simultaneous95% normal/HAC intervals across BTC and ETH only, not expected-profit confidence or independent episode replication.'}


def exposure(book,records,benchmarks,capital):
    traces=book['trace'];result={'beta':{},'model_net_notional_initial_capital_fraction_max':None,'model_gross_notional_initial_capital_fraction_max':None,
                              'model_net_notional_NAV_fraction_max':None,'model_gross_notional_NAV_fraction_max':None,
                              'true_delta':'unavailable','intrahour_tail_loss':'unavailable'}
    net=[];gross=[];netnav=[];grossnav=[]
    for t,r in zip(traces,records):
        try:
            if not r.get('hedge_available') or not r.get('valuation_available') or r.get('rule_scope',{}).get('available') is not True or r.get('missing_sources') or r.get('stale_sources'):raise ValueError('complete admitted exposure inputs required')
            index=F(r['index']);h=F(t['hedge_quantity']);q=abs(F(t['option_quantity']));nav=F(t['nav'])
            if nav<=0:raise ValueError('positive NAV required')
            d=[F(r[s]['delta']) for s in ('call','put')]
            net.append(abs(h-q*sum(d))*index/capital)
            gross.append((abs(h)+q*sum(abs(v) for v in d))*index/capital)
            netnav.append(net[-1]*capital/nav);grossnav.append(gross[-1]*capital/nav)
        except (KeyError,ValueError,TypeError,ZeroDivisionError):break
    if len(net)==len(traces):
        result['model_net_notional_initial_capital_fraction_max']=str(max(net));result['model_gross_notional_initial_capital_fraction_max']=str(max(gross))
        result['model_net_notional_NAV_fraction_max']=str(max(netnav));result['model_gross_notional_NAV_fraction_max']=str(max(grossnav))
    try:
        nav=[F(t['nav']) for t in traces]
        if any(v<=0 for v in nav):raise ValueError('nonpositive NAV')
        y=[float(b/a-1) for a,b in zip(nav,nav[1:])]
    except (KeyError,ValueError,TypeError,ZeroDivisionError):y=None
    for asset in ASSETS:
        try:
            prices=benchmarks[asset]
            if len(prices)!=len(traces) or any(v is None or F(v)<=0 for v in prices):raise ValueError('complete fresh benchmark required')
            x=[float(F(b)/F(a)-1) for a,b in zip(prices,prices[1:])]
            result['beta'][asset]=beta(y,x) if y is not None else {'status':'unavailable','reason':'complete positive NAV required'}
        except (KeyError,ValueError,TypeError,ZeroDivisionError):result['beta'][asset]={'status':'unavailable','reason':'complete fresh benchmark required'}
    return result


def evaluate(*,entry_ms,selection,records,initial_rules,initial_rules_ms,rule_vintages,funding,benchmarks):
    """Already independently admitted source products; retain all eight outcomes.

    records/benchmarks keyed by BTC/ETH; no missing hourly slots may be dropped.
    funding[asset] must expose engine_inputs only after complete source admission.
    """
    outputs={}
    for asset in ASSETS:
        for capital in (1000,10000):
            for cost in COSTS:
                key=f'{asset.lower()}-{capital}-{cost}'
                row={'id':key,'asset':asset,'capital':capital,'cost':cost,'status':'unavailable'}
                outputs[key]=row
                try:
                    chosen=selection[asset]
                    exit_ms=chosen['expiry_ms']-DAY
                    expected=list(range(entry_ms,exit_ms+1,HOUR))
                    if exit_ms%HOUR or not 6*DAY<=exit_ms-entry_ms<=44*DAY or [r['time_ms'] for r in records[asset]]!=expected:raise ValueError('exact selected hourly denominator required')
                    if any(r.get('action_time_ms')!=r['time_ms']+5000 for r in records[asset]):raise ValueError('fixed5second action clocks required')
                    if funding[asset].get('coverage_known') is not True or funding[asset].get('engine_inputs') is None:raise ValueError('funding coverage unknown; no zero-filled financial book')
                    adjusted,rules=adapter.apply_rule_vintages(records[asset],asset=asset,selection=chosen,initial=initial_rules,initial_ms=initial_rules_ms,vintages=rule_vintages,stress=cost=='stress')
                    costs={**COSTS[cost],'option_tick_worsening':chosen['option_tick'] if cost=='stress' else '0'}
                    f=funding[asset]['engine_inputs']
                    book=ENGINE.ledger(adjusted,capital=capital,option_quantity=chosen['quantity'],costs=costs,
                        hedge_lot=rules['perp']['lot']['stepSize'],hedge_min_quantity=rules['perp']['lot']['minQty'],hedge_min_notional=rules['perp']['min_notional'],
                        expected_funding_times=f['expected_funding_times'],funding_events=f['funding_events'])
                    book['scope']='Conditional unit-one quote-side fills and arrived model deltas; last-observed rules, assumed fees and effective slippage costs. Actual margin, account access, fills, tail probabilities and expected profit unvalidated.'
                    book['metrics']['duration_scope']='Fixed declared entry-to-exit actions; hypothetical execution at nominal time plus5seconds.'
                    row['book']=book
                    row['exposure']=exposure(book,adjusted,{a:benchmarks[a][:len(expected)] for a in ASSETS},capital)
                    profit=book['final']['profit']
                    row['screens']={'cash_positive':None if profit is None else F(profit)>0,
                        'annual3percent_relevance':None if profit is None else F(profit)>=F(capital*3*(exit_ms-entry_ms),100*365*DAY),
                        'expected_profit_confidence':'unavailable: one development episode',
                        'actual_margin_and_tradability':'unavailable','strategy_validated':False}
                    row['screens']['modeled_drawdown_at_most_10percent']=None if book['risk']['max_drawdown'] is None else F(book['risk']['max_drawdown'])<=F(1,10)
                    residual=row['exposure']['model_net_notional_NAV_fraction_max']
                    row['screens']['conditional_model_residual_at_most_1percent_NAV']=None if residual is None else F(residual)<=F(1,100)
                    row['screens']['realized_true_delta_at_most_1percent_NAV']='unavailable: model deltas do not establish true delta'
                    row['screens']['beta']={}
                    for market,metric in row['exposure']['beta'].items():
                        row['screens']['beta'][market]=None if metric['status']!='descriptive' else abs(metric['coefficient'])<=.10 and metric['interval'][0]>=-.20 and metric['interval'][1]<=.20
                    row['screens']['down50_up100_basis_liquidity_margin_stress']='unavailable: no admitted option repricing, liquidation or margin model'
                    row['status']='complete' if book['status']=='conditional_cash_complete' else 'unavailable'
                    if row['status']=='unavailable':row['reason']='Frozen cash ledger could not close with complete funding and permitted fills.'
                except (KeyError,ValueError,TypeError,ArithmeticError) as exc:row['reason']=str(exc)
    return {'cells':outputs,'count':8,'strategy_validated':False,'inference':'One prospectively frozen development episode; eight correlated cases, not eight independent hypotheses. No interim look or graduation.'}
