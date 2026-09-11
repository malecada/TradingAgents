"""Independent invented-data cash oracle; does not open empirical inputs."""
from decimal import Decimal, ROUND_FLOOR, getcontext
import importlib.util
import json
import math
from pathlib import Path

getcontext().prec=60
D=lambda x:Decimal(str(x))
HERE=Path(__file__).parent
source=HERE.parent/'wbeth_book.py'
loader=importlib.util.spec_from_file_location('review_synthetic_wbeth_engine',source)
engine=importlib.util.module_from_spec(loader);loader.loader.exec_module(engine)
START,DAY=1775001600000,86400000


def invented():
    datasets=[[] for _ in range(4)]
    events=[]
    for i in range(91):
        e=100*(1+.15*math.sin(i*.21))
        prices=[2.5*e*(1+.03*i/90),e,1.004*e,1.002*e]
        for dataset,p in zip(datasets,prices):
            dataset.append([START+i*DAY,p,p*1.03,p*.97,p,20,START+(i+1)*DAY-1,100,10,2,20,0])
        for j in range(3):
            events.append({'symbol':'ETHUSDT','fundingTime':START+i*DAY+j*DAY//3,
                           'markPrice':prices[3]*(1+(j-1)*.001),'fundingRate':.0002 if (i+j)%2 else -.0001})
    # A large opening-boundary cashflow must be excluded, including a +5s stamp.
    events[0]['fundingRate']=.5;events[0]['fundingTime']+=5000
    return [*datasets,events]


def verify():
    data=invented();wb,eth,future,mark,events=data
    checks=0;maximum=0.
    def eq(actual,expected,label):
        nonlocal checks,maximum
        error=abs(float(actual)-float(expected));assert error<1e-8,(label,actual,str(expected),error)
        checks+=1;maximum=max(maximum,error)
    rows=[]
    for cap in (1000,10000):
        for scenario in ('base','stress'):
            sf,ff,slip=(D('.001'),D('.0005'),D('.0002')) if scenario=='base' else (D('.002'),D('.001'),D('.0004'))
            capital=D(cap);w0,e0,f0=D(wb[0][1]),D(eth[0][1]),D(future[0][1]);ratio=w0/e0
            we,fe=w0*(1+slip),f0*(1-slip)
            qw=(capital*D('.4')/(we*(1+sf)+ratio*fe*ff)/D('.0001')).to_integral_value(rounding=ROUND_FLOOR)*D('.0001')
            qe=(qw*ratio/D('.001')).to_integral_value(rounding=ROUND_FLOOR)*D('.001')
            spent=qw*we*(1+sf)+qe*fe*ff;idle=capital-capital/2-spent
            assert spent<=capital*D('.4') and idle>=capital/10 and qw!=qe
            funding=[sum(qe*D(row['markPrice'])*D(row['fundingRate']) for row in events[1:] if (row['fundingTime']-START)//DAY==i) for i in range(91)]
            observed_total=sum(funding)
            primary=engine.book(*data,capital=cap,cost_scenario=scenario)
            zero=engine.book(*data,capital=cap,cost_scenario=scenario,zero_funding=True)
            assert primary['status']==zero['status']=='conditional'
            assert primary['initial']==zero['initial']
            for result,is_zero in ((primary,False),(zero,True)):
                applied=D(0) if is_zero else observed_total
                sx,fx=D(wb[-1][4])*(1-slip),D(future[-1][4])*(1+slip)
                fees=qw*(we+sx)*sf+qe*(fe+fx)*ff
                signed=qw*(sx-we)+qe*(fe-fx)+applied-fees
                cash=idle+capital/2+applied+qe*(fe-fx)-qe*fx*ff+qw*sx-qw*sx*sf
                assert cash-capital==signed
                eq(result['initial']['wbeth_quantity'],qw,'WBETH quantity')
                eq(result['initial']['eth_perp_quantity'],-qe,'signed ETH quantity')
                eq(result['initial']['joint_entry_spend'],spent,'joint spend')
                eq(result['initial']['idle_cash'],idle,'idle')
                eq(result['final_ledger']['all_fees'],fees,'four fees')
                eq(result['final_ledger']['cash_profit'],signed,'signed profit')
                eq(result['final_ledger']['final_cash'],cash,'wallet cash')
                assert result['excluded_first_funding_timestamps']==[START+5000]
                assert result['metrics']['applied_funding_events']==272
                cumulative=D(0)
                for i,row in enumerate(result['daily_trace']):
                    day_cash=D(0) if is_zero else funding[i];cumulative+=day_cash
                    nav=idle+capital/2+cumulative+qe*(fe-D(mark[i][4]))+qw*D(wb[i][4])
                    eq(row['observed_same_quantity_funding_cash'],funding[i],'observed event cash')
                    eq(row['funding_cash'],day_cash,'applied event cash')
                    eq(row['pre_exit_nav'],nav,'pre-exit daily NAV')
                    eq(row['nav'],cash if i==90 else nav,'published daily NAV')
                    eq(row['nav'],D(row['idle_cash'])+D(row['futures_wallet'])+D(row['short_mtm'])+D(row['wbeth_value']),'wallet components')
                eq(result['metrics']['funding_cash'],applied,'total funding')
                assert result['true_eth_delta']['status']=='unavailable'
                assert result['daily_trace'][-1]['wbeth_quantity']==result['daily_trace'][-1]['eth_perp_quantity']==0
            eq(primary['final_ledger']['cash_profit']-zero['final_ledger']['cash_profit'],observed_total,'paired funding difference')
            rows.append({'capital':cap,'scenario':scenario,'quantity_wbeth':float(qw),'quantity_eth':float(qe),'status':'PASS'})
    return {'status':'PASS','invented_data_only':True,'financial_engine_used_only_on_invented_data':True,'empirical_inputs_opened':0,
            'comparisons':checks,'maximum_absolute_error':maximum,'paired_cases':rows,
            'method':'Independent 60-digit Decimal two-quantity sizing, wallet/cash and actual-event funding oracle; no production observations or registered runner execution.'}


if __name__=='__main__':
    result=verify()
    with (HERE/'wbeth-engine-synthetic-review.json').open('x') as out:json.dump(result,out,indent=2);out.write('\n')
    print(json.dumps(result))
