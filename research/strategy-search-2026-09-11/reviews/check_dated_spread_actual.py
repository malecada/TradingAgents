"""Independent actual eight-book source/Fraction/HAC reconstruction; no engine imports."""
from pathlib import Path
from fractions import Fraction as F
from decimal import Decimal
from datetime import datetime,timezone
from urllib.parse import urlencode
from scipy.stats import t as student_t
import numpy as np
import base64,csv,hashlib,io,json,math,re,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[3];P=ROOT/'research/strategy-search-2026-09-11';RUN=ROOT/'research_runs/dated-spread-book-20260911';OUT=RUN/'outputs'
# This checker cannot inspect empirical financial inputs before completed execution.
assert (RUN/'failed.json').exists() and not (RUN/'complete.json').exists(),'Wait for reviewed failed-receipt closure'
START=1777593600000;DAY=86400000;END=START+56*DAY;Q2=1775001600000;QEND=1782864000000
checks=0;max_error=0.
def check(actual,expected):
 global checks,max_error
 error=abs(float(actual)-float(expected));assert math.isfinite(float(actual)) and error<=1e-8,(actual,str(expected),error)
 checks+=1;max_error=max(max_error,error)
def pairs(items):
 result={}
 for k,v in items:
  if k in result:raise ValueError('duplicate JSON field')
  result[k]=v
 return result
def bad(x):raise ValueError('nonfinite JSON token')
def decode(raw):return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)
def read(path):return decode(path.read_bytes())
def sha(raw):return hashlib.sha256(raw).hexdigest()
def clock(value):
 result=datetime.fromisoformat(value);assert result.utcoffset().total_seconds()==0;return result

def expected_book(inputs,asset,C,cost,out):
 d,p,dm,pm,funding,spot=inputs;C=F(str(C));f=F(5 if cost=='base' else 10,10000);s=F(2 if cost=='base' else 4,10000);lot=F(1,1000 if asset=='BTC' else 100)
 de=F(d[0][1])*(1+s);pe=F(p[0][1])*(1-s);unit=max(de,pe)+f*(de+pe);q=((C*F(2,5))/(unit*lot)).numerator//((C*F(2,5))/(unit*lot)).denominator*lot
 df=q*de*f;pf=q*pe*f
 def close(ds,ps,paid):
  dx=ds*(1-s);px=ps*(1+s);dfee=q*dx*f;pfee=q*px*f
  dw=C*F(2,5)-df+q*(dx-de)-dfee;pw=C/2-pf+paid+q*(pe-px)-pfee
  return dw,pw,dw+pw+C/10,dfee,pfee
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
 return {'out':out,'nav':navs,'q':q,'profit':profit,'funding':cumulative,'raw':raw,'fees':df+pf+dfee+pfee,'dated_fee':df,'perp_fee':pf,'dated_entry':de,'perp_entry':pe}

claim=read(RUN/'claim.json');terminal=read(RUN/'failed.json');actual=read(OUT/'books.json')['cases'];summary=read(OUT/'summary.json');audit=read(OUT/'source-audit.json')
exp=claim['experiment'];source=claim['source'];gate=decode(subprocess.check_output(['git','show',source+':'+claim['registration']],cwd=ROOT))
assert gate['experiments'][claim['experiment_id']]==exp and terminal.get('source',source)==source and terminal['claim_sha256']==sha((RUN/'claim.json').read_bytes())
assert terminal.get('registration_sha256',claim['registration_sha256'])==claim['registration_sha256']==sha((ROOT/claim['registration']).read_bytes())
assert set(p.name for p in OUT.iterdir())==set(exp['outputs'])==set(terminal['output_sha256'])
for name,digest in terminal['output_sha256'].items():assert sha((OUT/name).read_bytes())==digest
for path,digest in exp['source_files'].items():assert sha((ROOT/path).read_bytes())==digest==sha(subprocess.check_output(['git','show',source+':'+path],cwd=ROOT))
inputs={}
for name,item in exp['inputs'].items():
 raw=(ROOT/item['path']).read_bytes();assert sha(raw)==item['sha256'];inputs[name]=decode(raw)
 assert audit['source_files'][name]=={'sha256':sha(raw),'bytes':len(raw)}
assert len(inputs)==8
source_report={};values={}
def receipt(record,request,maxbytes,check_url=True):
 for k,v in request.items():assert record[k]==v,(request['id'],k)
 assert record['attempted']is True and record['body_complete']is True and type(record['http_status'])is int and record['http_status']==200 and record['error']is None
 raw=base64.b64decode(record['body_base64'],validate=True);assert type(record['body_bytes'])is int and len(raw)==record['body_bytes']<=maxbytes and sha(raw)==record['body_sha256']
 assert clock(record['request_utc'])<=clock(record['retrieval_utc'])
 if check_url:assert record['request_url']==request['url']+('?' +urlencode(request['parameters'])if request['parameters']else '')
 source_report[request['id']]={'raw_bytes':len(raw),'body_sha256':sha(raw),'status':'complete'}
 return raw

def bars(rows,start,interval,count=None,trade=True,clock_strings=False):
 assert type(rows)is list and (count is None or len(rows)==count)
 for i,row in enumerate(rows):
  assert len(row)==12
  for k in [0,6]:assert type(row[k])is int or(clock_strings and type(row[k])is str and re.fullmatch(r'[0-9]{13}',row[k]))
  assert int(row[0])==start+i*interval and int(row[6])==start+(i+1)*interval-1
  o,h,l,c=map(lambda x:F(str(x)),row[1:5]);assert min(o,h,l,c)>0 and l<=o<=h and l<=c<=h
  if trade:
   for k in [5,7,8,9,10]:assert F(str(row[k]))>=0
   assert F(str(row[8])).denominator==1
 return rows

# Independently reconstruct all ten historical carry responses.
requests=[]
for kind,host,route in [('funding','fapi.binance.com','/fapi/v1/fundingRate'),('spot','api.binance.com','/api/v3/klines'),('perp','fapi.binance.com','/fapi/v1/klines'),('mark','fapi.binance.com','/fapi/v1/markPriceKlines')]:
 for asset in ['btc','eth']:
  params={'symbol':asset.upper()+'USDT','startTime':Q2,'endTime':QEND-1,'limit':1000}
  if kind!='funding':params['interval']='1d'
  requests.append({'id':asset+'-'+kind,'kind':kind,'url':'https://'+host+route,'parameters':params})
for kind,route in [('exchange-info','exchangeInfo'),('server-time','time')]:requests.append({'id':kind,'kind':kind,'url':'https://fapi.binance.com/fapi/v1/'+route,'parameters':{}})
cc=inputs['carry_capture'];assert cc['request_spec']['requests']==requests
records={r['id']:r for r in cc['requests']};assert len(cc['requests'])==len(records)==10 and set(records)=={r['id']for r in requests}
for req in requests:
 rec=records[req['id']];value=decode(receipt(rec,req,5*1024**2));values[req['id']]=value
 if req['kind'] in ['spot','perp','mark']:bars(value,Q2,DAY,91,req['kind']!='mark')
 elif req['kind']=='funding':
  assert len(value)==273;previous=None
  for i,event in enumerate(value):
   ts=event['fundingTime'];assert type(ts)is int and Q2<=ts<QEND and abs(ts-(Q2+i*DAY//3))<=5000 and(previous is None or ts>previous)
   assert event['symbol']==req['parameters']['symbol'] and F(event['markPrice'])>0;F(event['fundingRate']);previous=ts
 elif req['kind']=='server-time':
  assert type(value['serverTime'])is int and int(clock(rec['request_utc']).timestamp()*1000)-5000<=value['serverTime']<=int(clock(rec['retrieval_utc']).timestamp()*1000)+5000
 else:
  rows=[r for r in value['symbols']if r['symbol']in ['BTCUSDT','ETHUSDT']];assert len(rows)==2
  for row in rows:assert row['contractType']=='PERPETUAL' and row['marginAsset']==row['quoteAsset']=='USDT' and row['status']=='TRADING'
# Event marks must also be consistent with each source day's observed mark range.
for asset in ['btc','eth']:
 for event in values[asset+'-funding']:
  day=(event['fundingTime']-Q2)//DAY;markrow=values[asset+'-mark'][day]
  assert F(str(markrow[3]))<=F(event['markPrice'])<=F(str(markrow[2]))

# Paired ZIP/checksum provenance, full monthly rows, and declared observed June tail.
ac=inputs['archive_capture'];ar={r['id']:r for r in ac['requests']};assert len(ar)==len(ac['requests'])==8
archive_requests=[];archive_rows={}
for asset in ['btc','eth']:
 for month,count in [('2026-05',744),('2026-06',None)]:
  symbol=asset.upper()+'USDT_260626';filename=symbol+'-1h-'+month+'.zip';url='https://data.binance.vision/data/futures/um/monthly/klines/'+symbol+'/1h/'+filename;raws={}
  for kind in ['zip','checksum']:
   req={'id':asset+'-'+month+'-'+kind,'asset':asset,'symbol':symbol,'month':month,'kind':kind,'filename':filename,'url':url+('.CHECKSUM'if kind=='checksum'else '')};archive_requests.append(req);raws[kind]=receipt(ar[req['id']],req,5*1024**2,False)
  assert re.fullmatch(r'([0-9a-fA-F]{64})  '+re.escape(filename)+r'\r?\n?',raws['checksum'].decode('ascii')).group(1).lower()==sha(raws['zip'])
  with zipfile.ZipFile(io.BytesIO(raws['zip']))as z:
   assert len(z.infolist())==1;info=z.infolist()[0];assert info.filename==filename[:-4]+'.csv' and 0<info.file_size<=2*1024**2 and info.file_size/max(info.compress_size,1)<=100
   body=z.read(info);rows=list(csv.reader(io.StringIO(body.decode('utf-8'))))
  header=['open_time','open','high','low','close','volume','close_time','quote_volume','count','taker_buy_volume','taker_buy_quote_volume','ignore']
  if rows[0]==header:rows=rows[1:]
  begin=int(datetime(2026,int(month[-2:]),1,tzinfo=timezone.utc).timestamp()*1000);bars(rows,begin,DAY//24,count,True,True)
  if count is None:assert 600<=len(rows)<=720
  archive_rows[asset+'-'+month]=rows;source_report[asset+'-'+month+'-zip'].update(member_sha256=sha(body),rows=len(rows))
assert ac['request_spec']['requests']==archive_requests
# Exact two receipt files and normalized rows were independently reviewed at capture;
# this check reconstructs their literal values again without the collector.
mc=inputs['mark_capture'];assert len(mc['receipts'])==2
for asset in ['btc','eth']:
 name=asset+'-dated-mark';r=inputs[asset+'_dated_mark_receipt'];req={'id':name,'symbol':asset.upper()+'USDT_260626','endpoint':'https://fapi.binance.com/fapi/v1/markPriceKlines','parameters':{'symbol':asset.upper()+'USDT_260626','interval':'1d','startTime':START,'endTime':END-1,'limit':100}}
 raw=receipt(r,req,256*1024,False);assert r['request_url']==req['endpoint']+'?'+urlencode(req['parameters'])
 ref=next(x for x in mc['receipts']if x['id']==name);assert ref['receipt_sha256']==exp['inputs'][asset+'_dated_mark_receipt']['sha256'] and ref['body_sha256']==sha(raw)
 assert clock(mc['capture_closed_utc'])>=clock(r['retrieval_utc'])
 values[name]=bars(decode(raw),START,DAY,56,False)
assert len(source_report)==20 and len(audit['source_states'])==20 and set(source_report)==set(audit['source_states'])
for name,value in source_report.items():
 assert audit['source_states'][name]['status']=='complete' and audit['source_states'][name]['body_sha256']==value['body_sha256'] and audit['source_states'][name]['body_bytes']==value['raw_bytes']
for group in ['carry','archive','mark']:
 rows=inputs[group+'_admission']['cells'];assert len(rows)=={'carry':10,'archive':8,'mark':2}[group] and all(r['status']=='complete'for r in rows)

reference={};verdicts=[]
for asset in ['BTC','ETH']:
 a=asset.lower();d=[row for month in ['2026-05','2026-06']for row in archive_rows[a+'-'+month]if START<=int(row[0])<END];assert len(d)==1344
 clip=lambda kind:[r for r in values[a+'-'+kind]if START<=int(r[0])<END]
 funding=values[a+'-funding'][90:258];assert len(funding)==168 and abs(funding[0]['fundingTime']-START)<=5000
 assert all(START+5000<r['fundingTime']<END for r in funding[1:])
 data=[d,clip('perp'),values[a+'-dated-mark'],clip('mark'),funding,clip('spot')]
 assert audit['clipping'][asset]['funding']['canonical_before']==90 and audit['clipping'][asset]['funding']['canonical_after']==15
 for C in [1000,10000]:
  for cost in ['base','stress']:
   key=f'{a}-{C}-{cost}';out=actual[key];ref=expected_book(data,asset,C,cost,out);reference[key]=ref;q=ref['q'];initial=out['initial']
   for name,want in [('dated_quantity',q),('perp_quantity',-q),('net_base_quantity',0),('dated_entry_fill',ref['dated_entry']),('perp_entry_fill',ref['perp_entry']),('dated_entry_fee',ref['dated_fee']),('perp_entry_fee',ref['perp_fee']),('dated_entry_notional',q*ref['dated_entry']),('perp_entry_notional',q*ref['perp_entry']),('dated_reserve',F(2,5)*C),('perp_reserve',F(1,2)*C),('idle_cash',F(1,10)*C)]:check(initial[name],want)
   assert len(out['daily_trace'])==56 and out['excluded_entry_funding_timestamps']==[funding[0]['fundingTime']]
   for j,event in enumerate(out['funding_events']):
    original=funding[j];assert event['funding_time_ms']==original['fundingTime'] and event['included']==(j>0);check(event['rate'],F(original['fundingRate']));check(event['event_mark'],F(original['markPrice']))
    if j:check(event['signed_short_cash'],q*F(original['markPrice'])*F(original['fundingRate']))
    else:assert event['signed_short_cash']is None
   peak=F(C);dd=F(0)
   for nav in ref['nav']:peak=max(peak,nav);dd=max(dd,(peak-nav)/peak)
   check(out['metrics']['cash_profit'],ref['profit']);check(out['metrics']['full_capital_return'],ref['profit']/C);check(out['metrics']['annualized_simple_return_365'],ref['profit']/C*F(365,56));check(out['metrics']['max_drawdown'],dd)
   check(out['scalar_diagnostics']['zero_funding']['profit'],ref['profit']-ref['funding']);check(out['scalar_diagnostics']['frictionless']['profit'],ref['raw']+ref['funding'])
   ref['max_drawdown']=dd
   verdicts.append({'id':key,'quantity':float(q),'cash_profit':float(ref['profit']),'annualized_simple_return':float(ref['profit']/C*F(365,56)),'raw_two_leg_price_change':float(ref['raw']),'funding_cash':float(ref['funding']),'fees':float(ref['fees']),'slippage_cost':out['final_ledger']['slippage_cost'],'frictionless_same_q_profit':float(ref['raw']+ref['funding']),'zero_funding_same_q_profit':float(ref['profit']-ref['funding'])})

# Direct HAC reconstruction from independent NAVs and raw spot benchmarks.
spot={a:[r for r in values[a+'-spot']if START<=r[0]<END]for a in ['btc','eth']}
def benchmark(rows):return np.asarray([float(F(str(row[4]))/F(str(rows[i-1][4]if i else row[1]))-1)for i,row in enumerate(rows)])
X=np.column_stack([np.ones(56),benchmark(spot['btc']),benchmark(spot['eth'])]);inverse=np.linalg.inv(X.T@X);assert np.linalg.matrix_rank(X)==3
for case in summary['cases']:
 key=case['id'];ref=reference[key];C=case['capital'];nav=np.asarray([float(v)for v in ref['nav']]);previous=np.r_[C,nav[:-1]];stat=case['statistics']['market_exposure']
 if np.all(nav>0)and np.all(previous>0):
  Y=nav/previous-1;beta=inverse@X.T@Y;resid=Y-X@beta;score=X*resid[:,None];S=score.T@score
  for lag in range(1,8):term=score[lag:].T@score[:-lag];S+=(1-lag/8)*(term+term.T)
  cov=inverse@S@inverse;se=np.sqrt(np.diag(cov));critical=student_t.ppf(.9875,53);intervals=np.c_[beta-critical*se,beta+critical*se]
  assert stat['status']=='complete'
  for got,want in zip([stat['intercept'],stat['btc_beta'],stat['eth_beta']],beta):check(got,want)
  for got,want in zip(np.asarray(stat['covariance']).ravel(),cov.ravel()):check(got,want)
  for i,a in enumerate(['btc','eth'],1):
   check(stat[a+'_standard_error'],se[i])
   for got,want in zip(stat[a+'_interval'],intervals[i]):check(got,want)
  beta_pass=all(abs(beta[i])<=.1 and intervals[i,0]>=-.2 and intervals[i,1]<=.2 for i in [1,2])
 else:assert stat['status']=='unavailable';beta_pass=None
 pair=[reference[f"{case['asset'].lower()}-{C}-{cost}"]for cost in ['base','stress']];relevant=all(r['profit']>0 and r['profit']/C*F(365,56)>=F(3,100)for r in pair)
 screens=case['conditional_screens'];assert screens['positive_cash_and_3pct_annual_base_and_stress']==relevant and screens['beta_point_and_interval']==beta_pass
 assert screens['drawdown_at_most_10pct']==(ref['max_drawdown']<=F(1,10))
 assert screens['no_separate_path_wallet_deficit']==(not any(row['dated_low_buffer']<0 or row['perp_high_buffer']<0 for row in ref['out']['daily_trace']))
 assert screens['no_separate_stress_wallet_deficit']==(not any(row['separate_wallet_deficit']for row in ref['out']['stress_states']))
 assert screens['modeled_net_base_at_most_1pct_nav']==(True if all(v>0 for v in ref['nav'])else None)
 check(ref['out']['metrics']['minimum_dated_low_buffer'],min(row['dated_low_buffer']for row in ref['out']['daily_trace']))
 check(ref['out']['metrics']['minimum_perp_high_buffer'],min(row['perp_high_buffer']for row in ref['out']['daily_trace']))
 for rate in [0,.03,.05]:check(case['cash_benchmarks'][str(rate)],F(str(rate))*C*F(56,365))
 assert case['statistics']['expected_profit_confidence']['status']==case['statistics']['power']['status']=='unavailable'
 assert case['actual_margin']['status']==case['execution']['status']=='unavailable' and case['graduation']is False and case['validated_strategy']is False
 verdict=next(v for v in verdicts if v['id']==key);verdict.update(conditional_screens=screens,btc_beta=stat.get('btc_beta'),eth_beta=stat.get('eth_beta'))
assert set(actual)==set(exp['cells']) and len(actual)==8 and len(summary['cases'])==8
assert (summary['complete_primary'],summary['unavailable_primary'],summary['complete_scalars'],summary['unavailable_scalars'],summary['complete_stresses'],summary['unavailable_stresses'])==(8,0,16,0,72,0)
assert terminal['status']=='failed' and 'cells' not in terminal and 'cell_count' not in terminal
sys.path.insert(0,str(ROOT))
from tradingagents.research_spread.verify import verify_run
structural=verify_run(RUN)
# Explicitly preserve older live-verifier limitations and independently admitted snapshots.
older=[]
for package,parent in [('tradingagents.research_amended.verify','dated-book-amended-20260911'),('tradingagents.research_extended.verify','dated-mark-20260911')]:
 module=__import__(package,fromlist=['verify_run'])
 try:module.verify_run(ROOT/'research_runs'/parent)
 except ValueError as error:older.append({'parent':parent,'frozen_live_refusal':str(error),'new_closed_snapshot':verify_run(ROOT/'research_runs'/parent)})
 else:raise AssertionError('frozen live verifier unexpectedly accepted descendant')
guard=read(P/'reviews/dated-spread-actual-guard.json');assert guard['child_exit_code']==-15 and guard['limit_reason']=='wall-clock limit exceeded' and guard['elapsed_seconds']>=120
size=sum(x.stat().st_size for x in OUT.iterdir());assert size<=8*1024**2
report={'passed':True,'operational_status':'failed','forensic_only':True,'registered_resource_requirement_passed':False,'scope':'Independent raw source and Fraction cash/wallet/scalar/stress reconstruction; direct HAC covariance and Student-t intervals. No engine, adapter, runner or statistics module imports; no network, new experiment or ledger write. Structural verifier used only for failed-receipt provenance. Reconstructed cases are failed-run retained-output forensics, not completed lifecycle cells.','source':source,'numeric_assertions':checks,'maximum_absolute_error':max_error,'source_cells':source_report,'retained_primary_cases':8,'completed_lifecycle_cells':0,'daily_NAVs':448,'scalar_diagnostics':16,'stress_states':72,'credited_events_per_case':167,'excluded_events_per_case':1,'verdicts':verdicts,'structural':structural,'historical_verifiers':older,'guard':guard,'output_bytes':size,'accounting':{'prior_program_claims':5,'current_program_claims':6,'historical_prior':1,'consumed_effective_budget':7,'original_cap':4,'remaining_named_grant':0},'limits':'One exposed episode, no expected-profit CI/power, actual margin, fills or strategy graduation; all screens conditional.'}
(Path(__file__).parent/'dated-spread-actual-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k not in ['source_cells','historical_verifiers']},indent=2))
