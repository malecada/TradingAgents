"""Full-length invented direct-PnL audit; no market observations."""
from fractions import Fraction as F
from decimal import Decimal, localcontext
import hashlib
import importlib.util
import json
import math
from pathlib import Path

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('reviewed_engine',root/'options_policy_engine.py')
engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
checks=0;cases=[]
def eq(a,b):
    global checks
    assert F(a)==b,(a,str(b));checks+=1

for asset in ('BTC','ETH'):
 for capital in (1000,10000):
  for stress in (False,True):
    rows=[];q=F(1,100);pf=F(1,1000) if stress else F(1,2000);sl=F(1,2500) if stress else F(1,5000)
    of=F(3,10000) if stress else F(24,100000);tick=F(1,100) if stress else F(0)
    for hour in range(1057):
        opt={'unit':1,'bid':'10','ask':'10.01','bid_qty':'100','ask_qty':'100','mark':'10'}
        price=str(100+hour%7)
        rows.append({'time_ms':hour*3600000,'action_time_ms':hour*3600000+5000,'decision_available':True,'index':price,
            'call':dict(opt,delta=('1','.2','.7','.4')[hour%4]),'put':dict(opt,delta='-.5'),
            'perp':{'bid':price,'ask':price,'bid_qty':'100','ask_qty':'100','mark':price}})
    expected=[h*3600000+3000 for h in range(0,1057,8)]
    events=[{'time_ms':t,'rate':'.0001','mark':'100'} for t in expected[1:]]
    out=engine.ledger(rows,capital=str(capital),option_quantity='.01',costs={'option_fee_rate':'.00030' if stress else '.00024','perp_fee_rate':'.001' if stress else '.0005','perp_slippage':'.0004' if stress else '.0002','option_tick_worsening':'.01' if stress else '0'},hedge_lot='.0001',hedge_min_quantity='0',hedge_min_notional='0',expected_funding_times=expected,funding_events=events)
    assert out['status']=='conditional_cash_complete' and len(out['trace'])==1057
    h=F(0);lastmark=None;trading=F(0);fees=F(0);fund=F(0);ocash=F(2,5)*capital;fund_i=0;navs=[F(capital)]
    for i,r in enumerate(rows):
        mark=F(r['index'])
        # Independent incremental marked PnL, avoiding the engine's execution accumulator.
        if lastmark is not None:trading+=h*(mark-lastmark)
        if i and i%8==0:
            payment=-h*100*F(1,10000);fund+=payment
            eq(out['funding_events'][fund_i]['inventory'],h);eq(out['funding_events'][fund_i]['cash'],payment);fund_i+=1
        target=F(0) if i==1056 else q*(F(r['call']['delta'])+F(r['put']['delta']))
        assert (target/F(1,10000)).denominator==1
        dq=target-h;fill=mark*(1+sl if dq>0 else 1-sl)
        trading+=dq*(mark-fill);fees+=abs(dq)*fill*pf;h=target
        if i in (0,1056):
            px=(F('10.01')+tick) if i else (F(10)-tick)
            ofees=2*q*min(of*mark,px/10)
            ocash+=(-2*q*px-ofees) if i else (2*q*px-ofees)
        liability=F(0) if i==1056 else 2*q*10
        equity=F(capital,2)+trading+fund-fees
        nav=ocash-liability+equity+F(capital,10)
        trace=out['trace'][i]
        eq(trace['hedge_quantity'],h);eq(trace['perp_wallet_equity'],equity)
        eq(trace['option_cash'],ocash);eq(trace['nav'],nav)
        navs.append(nav)
        lastmark=mark
    eq(out['final']['cash'],ocash+equity+F(capital,10))
    eq(out['cash_components']['known_funding'],fund)
    assert fund_i==len(events)
    with localcontext() as ctx:
        ctx.prec=100
        shadow=Decimal(0)
        for left,right in zip(navs,navs[1:]):
            change=right/left-1
            shadow+=Decimal(change.numerator)/Decimal(change.denominator)
        assert abs(Decimal(out['convention_diagnostic']['arithmetic_return_sum'])-shadow)<Decimal('1e-55')
    assert '60' in out['convention_diagnostic']['arithmetic_precision']
    assert abs(out['convention_diagnostic']['log_return_sum']-math.log(float(navs[-1]/capital)))<1e-11
    cases.append({'asset_label':asset,'capital':capital,'stress':stress,'hourly_points':1057,'funding_events':fund_i,'passed':True})
report={'passed':True,'source_sha256':hashlib.sha256((root/'options_policy_engine.py').read_bytes()).hexdigest(),'cases':cases,'exact_checks':checks,'scope':'Invented full-length8case reconstruction by incremental held-mark PnL plus execution slippage; no actual data or model-expected values.'}
Path(__file__).with_name('options-policy-direct-independent-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='cases'}))
