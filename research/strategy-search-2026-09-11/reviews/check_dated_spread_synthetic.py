"""Invented-input independent Fraction book reconstruction; no observations."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal,localcontext
import copy,hashlib,importlib.util,json,math
P=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('spread_engine_review',P/'dated_spread_book.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
START=1777593600000;DAY=86400000;checks=0;cases=[]
def check(actual,expected):
 global checks
 checks+=1
 assert math.isfinite(float(actual)) and abs(float(actual)-float(expected))<=1e-8,(actual,str(expected))
def bar(t,interval,o='100',c='112',hi='113',lo='90'):
 return [t,o,hi,lo,c,'1',t+interval-1,'1',1,'1','1','0']
def fixture(asset='BTC'):
 d=[bar(START+i*DAY//24,DAY//24)for i in range(1344)]
 p=[bar(START+i*DAY,DAY,'99','110')for i in range(56)]
 dm=[bar(START+i*DAY,DAY,'104','105','108','102')for i in range(56)]
 pm=[bar(START+i*DAY,DAY,'102','103','106','100')for i in range(56)]
 spot=[bar(START+i*DAY,DAY,'100','101')for i in range(56)]
 funding=[{'fundingTime':START+i*DAY//3,'symbol':asset+'USDT','fundingRate':['-.0002','.0001','.0003'][i%3],'markPrice':'103'}for i in range(168)]
 return [d,p,dm,pm,funding,spot]
def expected_book(inputs,asset,C,cost):
 d,p,dm,pm,funding,spot=inputs;C=F(str(C));f=F(5 if cost=='base' else 10,10000);s=F(2 if cost=='base' else 4,10000);lot=F(1,1000 if asset=='BTC' else 100)
 de=F(d[0][1])*(1+s);pe=F(p[0][1])*(1-s);unit=max(de,pe)+f*(de+pe);q=((C*F(2,5))/(unit*lot)).numerator//((C*F(2,5))/(unit*lot)).denominator*lot
 df=q*de*f;pf=q*pe*f
 def close(ds,ps,paid):
  dx=ds*(1-s);px=ps*(1+s);dfee=q*dx*f;pfee=q*px*f
  dw=C*F(2,5)-df+q*(dx-de)-dfee;pw=C/2-pf+paid+q*(pe-px)-pfee
  return dw,pw,dw+pw+C/10,dfee,pfee
 out=m.book(*inputs,asset=asset,capital=str(C),cost_scenario=cost)
 assert out['status']=='conditional';check(out['initial']['quantity'],q)
 assert F(out['initial']['sizing']['used_ceiling_decimal'])<=C*F(2,5)<F(out['initial']['sizing']['next_lot_ceiling_decimal'])
 cumulative=F(0);priornav=C;navs=[]
 for i,row in enumerate(out['daily_trace']):
  events=[ev for j,ev in enumerate(funding)if j!=0 and (ev['fundingTime']-START)//DAY==i]
  amounts=[q*F(ev['markPrice'])*F(ev['fundingRate'])for ev in events];paid=sum(amounts,F(0));negative=sum((v for v in amounts if v<0),F(0));prior=cumulative;cumulative+=paid
  dw=C*F(2,5)-df+q*(F(dm[i][4])-de);pw=C/2-pf+cumulative+q*(pe-F(pm[i][4]));nav=dw+pw+C/10
  check(row['pre_exit_nav'],nav);check(row['funding_cash'],paid);check(row['cumulative_funding_cash'],cumulative)
  check(row['dated_low_buffer'],C*F(2,5)-df+q*(F(dm[i][3])-de)-q*F(dm[i][3])/100)
  check(row['perp_high_buffer'],C/2-pf+prior+negative+q*(pe-F(pm[i][2]))-q*F(pm[i][2])/100)
  if i==55:dw,pw,nav,dfee,pfee=close(F(d[-1][4]),F(p[-1][4]),cumulative)
  check(row['dated_wallet'],dw);check(row['perp_wallet'],pw);check(row['nav'],nav);check(row['cash_increment'],nav-priornav)
  if nav>0 and priornav>0:check(row['full_capital_daily_return'],nav/priornav-1)
  else:assert row['full_capital_daily_return']is None
  priornav=nav;navs.append(nav)
 final=out['final_ledger'];raw=q*(F(d[-1][4])-F(d[0][1])+F(p[0][1])-F(p[-1][4]));profit=nav-C
 for key,value in [('cash_profit',profit),('signed_component_profit',profit),('funding_cash',cumulative),('raw_two_leg_price_change',raw),('all_fees',df+pf+dfee+pfee),('zero_funding_same_quantity_profit',profit-cumulative),('frictionless_same_quantity_profit',raw+cumulative)]:check(final[key],value)
 check(final['slippage_cost'],q*s*(F(d[0][1])+F(p[0][1])+F(d[-1][4])+F(p[-1][4])))
 assert len(out['funding_events'])==168 and sum(x['included']for x in out['funding_events'])==167
 assert len(out['stress_states'])==9 and len(out['scalar_diagnostics'])==2
 for row in out['stress_states']:
  ref=F(spot[0][1])*F(str(row['price_multiple']));b=F(row['adverse_basis_bps'],20000);ds=ref*(1-b);ps=ref*(1+b)
  dw=C*F(2,5)-df+q*(ds-de);pw=C/2-pf+q*(pe-ps)
  for key,value in [('dated_pre_exit_wallet',dw),('perp_pre_exit_wallet',pw),('pre_exit_nav',dw+pw+C/10),('dated_buffer',dw-q*ds/100),('perp_buffer',pw-q*ps/100)]:check(row[key],value)
  closed=close(ds,ps,F(0));check(row['closed_cash']['final_cash'],closed[2]);assert row['future_funding_cash']==0
  assert row['separate_wallet_deficit']==(dw-q*ds/100<0 or pw-q*ps/100<0)
 assert out['daily_trace'][-1]['dated_quantity']==out['daily_trace'][-1]['perp_quantity']==0
 if all(v>0 for v in navs):check(out['convention_diagnostic']['log1p_sum'],math.log(float(navs[-1]/C)))
 return out
for asset in ['BTC','ETH']:
 for C in [1000,10000]:
  for cost in ['base','stress']:
   out=expected_book(fixture(asset),asset,C,cost);cases.append({'name':f'{asset}-{C}-{cost}','passed':True})
# Shared price changes cancel raw linear price cash at identical base quantities.
inputs=fixture();inputs[0][-1][4]='107';inputs[1][-1][4]='106'
out=expected_book(inputs,'BTC',1000,'base');check(out['final_ledger']['raw_two_leg_price_change'],0)
cases.append({'name':'shared-price-cancellation','passed':True})
# Both legs mark to the same high level: total NAV remains positive but short wallet fails.
inputs=fixture()
for bars in inputs[2:4]:
 for row in bars:row[1:5]=['1000','1001','999','1000']
out=expected_book(inputs,'BTC',1000,'base');assert out['daily_trace'][0]['nav']>0 and out['daily_trace'][0]['perp_wallet']<0 and out['metrics']['path_wallet_deficit']
cases.append({'name':'separate-wallet-deficit-with-positive-total','passed':True})
inputs=fixture()
for row in inputs[3]:row[1:5]=['1000','1001','999','1000']
out=expected_book(inputs,'BTC',1000,'base');assert out['convention_diagnostic']['status']=='unavailable' and out['metrics']['modeled_net_base_fraction_nav']is None
cases.append({'name':'negative-intermediate-NAV-retained','passed':True})
for offset in [-5000,-1,0,1,5000]:
 inputs=fixture();inputs[4][0]['fundingTime']=START+offset
 try:
  out=m.book(*inputs,asset='BTC',capital=1000,cost_scenario='base');assert out['excluded_entry_funding_timestamps']==[START+offset] and out['metrics']['applied_funding_events']==167
 except (ValueError,AssertionError)as error:cases.append({'name':f'first-canonical-offset-{offset}','passed':False,'error':str(error)})
 else:cases.append({'name':f'first-canonical-offset-{offset}','passed':True})
for kind in ['first-after-tolerance','extra-early-June26','missing-event','included-before-ownership']:
 inputs=fixture()
 if kind=='first-after-tolerance':inputs[4][0]['fundingTime']=START+5001
 elif kind=='extra-early-June26':inputs[4].append({**inputs[4][-1],'fundingTime':START+56*DAY-1})
 elif kind=='missing-event':inputs[4].pop(30)
 else:inputs[4][1]['fundingTime']=START+5000
 try:m.book(*inputs,asset='BTC',capital=1000,cost_scenario='base')
 except ValueError:cases.append({'name':kind,'passed':True})
 else:cases.append({'name':kind,'passed':False,'error':'ambiguous/missing funding admitted'})
inputs=fixture();inputs[4][3]['fundingTime']-=5000
out=expected_book(inputs,'BTC',1000,'base');assert out['daily_trace'][0]['funding_event_count']==3 and out['daily_trace'][1]['funding_event_count']==2
cases.append({'name':'canonical-midnight-arrives-previous-day','passed':True})
with localcontext()as context:
 context.prec=80
 unit=Decimal('100.02')+Decimal('.0005')*(Decimal('100.02')+Decimal('98.9802'))
 for count in [1,3995]:
  threshold=Decimal(count)*Decimal('.001')*unit/Decimal('.4')
  for epsilon in [Decimal('-1e-20'),Decimal(0),Decimal('1e-20')]:
   out=m.book(*fixture(),asset='BTC',capital=str(threshold+epsilon),cost_scenario='base')
   wanted=count-1 if epsilon<0 else count
   if wanted==0:assert out['status']=='unavailable'
   else:assert out['initial']['sizing']['lot_count']==wanted
   cases.append({'name':f'exact-lot-boundary-{count}-{epsilon}','passed':True})
inputs=fixture()
for event in inputs[4]:event['fundingRate']='0'
inputs[3][0][1:5]=['354.1735910138923','355.1735910138923','1','354.1735910138923']
try:
 out=m.book(*inputs,asset='BTC',capital=1000,cost_scenario='base')
 log=out['convention_diagnostic']['log1p_sum'];expected_log=math.log(out['final_ledger']['final_cash']/1000)
 ok=out['convention_diagnostic']['status']=='unavailable' or abs(log-expected_log)<=1e-10
 cases.append({'name':'tiny-positive-NAV-log-telescoping','passed':ok,'observed_log_sum':log,'expected_endpoint_log':expected_log,'first_NAV':out['daily_trace'][0]['nav']})
except ValueError as error:cases.append({'name':'tiny-positive-NAV-log-telescoping','passed':False,'error':str(error)})
report={'passed':all(x['passed']for x in cases),'cases':cases,'independent_fraction_assertions':checks,'source_sha256':hashlib.sha256((P/'dated_spread_book.py').read_bytes()).hexdigest(),'scope':'Invented raw bars/events only; independent Fraction cash, quantity, daily wallets, fees, funding, final release and all nine stress states. No actual data, financial experiment, network or ledger write.'}
(Path(__file__).parent/'dated-spread-synthetic-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));raise SystemExit(0 if report['passed']else 1)
