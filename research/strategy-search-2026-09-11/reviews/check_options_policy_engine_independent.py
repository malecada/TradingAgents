"""Independent invented cash-flow reconstruction; no empirical inputs."""
import importlib.util
import json
from fractions import Fraction as F
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('reviewed_engine',ROOT/'options_policy_engine.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
checks=0
def eq(a,b):
    global checks
    assert F(a)==b,(a,str(b))
    checks+=1

def fixture():
    rows=[]
    for i,(px,d,cp,pp) in enumerate(zip(['100','110','90','120','105'],['.6','.2','-.4','.8','0'],['10','9','8','7','6'],['8','7','10','8','9'])):
        rows.append({'time_ms':i*3600000,'action_time_ms':i*3600000+5000,'decision_available':True,'index':px,
          'call':{'unit':1,'bid':cp,'ask':cp,'bid_qty':'100','ask_qty':'100','mark':cp,'delta':d},
          'put':{'unit':1,'bid':pp,'ask':pp,'bid_qty':'100','ask_qty':'100','mark':pp,'delta':'0'},
          'perp':{'bid':px,'ask':px,'bid_qty':'100','ask_qty':'100','mark':px}})
    return rows

cases=[]
for cap in (1000,10000):
 for q in (F(1),F(2)):
  for stress in (False,True):
    rows=fixture();of=F(3,10000);pf=F(1,2000)*(2 if stress else 1);sl=F(1,5000)*(2 if stress else 1);tick=F(1,10) if stress else F(0)
    # Literal decimals satisfy the reviewed parser; the reconstruction uses fractions.
    costs={'option_fee_rate':'.0003','perp_fee_rate':'.001' if stress else '.0005','perp_slippage':'.0004' if stress else '.0002','option_tick_worsening':'.1' if stress else '0'}
    ev=[{'time_ms':i*3600000+3000,'rate':'.001' if i%2 else '-.001','mark':rows[i]['index']} for i in range(1,5)]
    out=m.ledger(rows,capital=str(cap),option_quantity=str(q),costs=costs,hedge_lot='.1',hedge_min_quantity='0',hedge_min_notional='0',expected_funding_times=[e['time_ms'] for e in ev],funding_events=ev)
    o=F(2,5)*cap; b=F(cap,2); h=F(0); fs=F(0); os=F(0); ps=F(0)
    for i,r in enumerate(rows):
        px=F(r['index'])
        if i:
            fund=-h*px*F(ev[i-1]['rate']);b+=fund;fs+=fund
            eq(out['funding_events'][i-1]['inventory'],h);eq(out['funding_events'][i-1]['cash'],fund)
        if i in (0,4):
            for side in ('call','put'):
                p=F(r[side]['ask' if i else 'bid'])+(tick if i else -tick)
                fee=q*min(of*px,p/10);os+=fee
                o+=(-q*p-fee) if i else (q*p-fee)
        target=F(0) if i==4 else q*F(r['call']['delta'])
        # Fixture target is already an exact tenth; no implementation rounding reused.
        assert (target*10).denominator==1
        dq=target-h;fill=px*(1+sl if dq>0 else 1-sl);fee=abs(dq)*fill*pf
        # Linear derivative signed cash-flow representation, independent of weighted basis.
        b-=dq*fill+fee;ps+=fee;h=target
        liability=F(0) if i==4 else q*(F(r['call']['mark'])+F(r['put']['mark']))
        equity=b+h*px;nav=o-liability+equity+F(cap,10)
        trace=out['trace'][i]
        eq(trace['hedge_quantity'],h);eq(trace['option_cash'],o);eq(trace['option_liability'],liability)
        eq(trace['perp_wallet_equity'],equity);eq(trace['nav'],nav)
    eq(out['final']['cash'],o+b+F(cap,10));eq(out['cash_components']['known_funding'],fs)
    eq(out['cash_components']['option_fees'],os);eq(out['cash_components']['perp_fees'],ps)
    cases.append({'capital':cap,'q':str(q),'stress':stress,'checks_passed':True})

# Unknown intermediate mark cannot certify absence of a wallet deficit.
rows=fixture();rows[2]['call']['mark']=None
unknown=m.ledger(rows,capital='1000',option_quantity='1',costs={'option_fee_rate':'0','perp_fee_rate':'0','perp_slippage':'0','option_tick_worsening':'0'},hedge_lot='.1',hedge_min_quantity='0',hedge_min_notional='0',expected_funding_times=[],funding_events=[])
assert unknown['risk']['option_wallet_deficit'] is None
# A valid option liability remains observable when only the hedge mark is absent.
rows=fixture();rows[2].update(valuation_available=False,option_valuation_available=True,perp_valuation_available=False)
rows[2]['call']['mark']='1000';rows[2]['perp']['mark']=None
separate=m.ledger(rows,capital='1000',option_quantity='1',costs={'option_fee_rate':'0','perp_fee_rate':'0','perp_slippage':'0','option_tick_worsening':'0'},hedge_lot='.1',hedge_min_quantity='0',hedge_min_notional='0',expected_funding_times=[],funding_events=[])
assert separate['trace'][2]['nav'] is None
assert F(separate['trace'][2]['option_wallet_equity'])<0
assert separate['risk']['option_wallet_deficit'] is True
assert separate['risk']['perp_wallet_deficit'] is None
report={'passed':True,'cases':cases,'exact_cash_checks':checks,'unknown_mark_risk':unknown['risk'],
        'scope':'Invented direct signed cash-flow reconstruction only. No implementation basis or expected output reused; no actual market inputs or empirical run.'}
Path(__file__).with_name('options-policy-engine-independent-review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':True,'cases':len(cases),'exact_cash_checks':checks,'unknown_mark_deficit_flag':unknown['risk']['option_wallet_deficit']}))
