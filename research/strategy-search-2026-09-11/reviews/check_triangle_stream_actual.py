"""Independent retained-frame/currency audit. No collector/helper import or request."""
from pathlib import Path
import base64,collections,hashlib,json,math,subprocess
from datetime import datetime
from decimal import Decimal
from fractions import Fraction

ROOT=Path(__file__).resolve().parents[3]
REV=Path(__file__).resolve().parent
RUN=ROOT/'research_runs/triangle-stream-20260911'
OUT=RUN/'outputs'
SYMS=('BTCUSDT','ETHUSDT','ETHBTC')
PATHS={'btc-eth':(('BTCUSDT',True),('ETHBTC',True),('ETHUSDT',False)), 'eth-btc':(('ETHUSDT',True),('ETHBTC',False),('BTCUSDT',False))}
COUNTS=collections.Counter();DIAG=collections.Counter();REASONS=collections.Counter();ASSETS=collections.Counter();ERROR=0.;CHECKS=0

def sha(b):return hashlib.sha256(b).hexdigest()
def pairs(values):
 d={}
 for k,v in values:
  assert k not in d,'duplicate JSON key';d[k]=v
 return d

def loads(b):return json.loads(b,object_pairs_hook=pairs,parse_constant=lambda s:(_ for _ in ()).throw(AssertionError('nonfinite JSON')))
def read(p):return loads(p.read_bytes())
def compare(a,b):
 global ERROR,CHECKS
 CHECKS+=1
 if isinstance(b,bool) or isinstance(b,int):assert type(a)==type(b) and a==b,(a,b)
 else:
  assert isinstance(a,(int,float)) and math.isfinite(a)
  error=abs(a-float(b));ERROR=max(ERROR,error)
  assert error<=max(1e-8,abs(float(b))*2e-12),(a,float(b),error)

claim=read(RUN/'claim.json');complete=read(RUN/'complete.json');capture=read(OUT/'capture.json');summary=read(OUT/'summary.json');bins=read(OUT/'bins.json')
assert claim['source']=='71234f87d4221e8849f130dfb3e62824d700f0df'
assert complete['claim_sha256']==sha((RUN/'claim.json').read_bytes())
assert claim['experiment']['cells']==[v['id'] for v in complete['cells']]
assert len(complete['cells'])==9 and complete['unavailable_count']==1
assert set(claim['experiment']['outputs'])==set(complete['output_sha256'])=={f.name for f in OUT.iterdir()}
outputbytes=0
for name,h in complete['output_sha256'].items():
 b=(OUT/name).read_bytes();assert sha(b)==h;outputbytes+=len(b)
assert outputbytes<64*1024**2
for name,binding in claim['inputs'].items():assert sha((ROOT/binding['path']).read_bytes())==binding['sha256']
for path,h in claim['experiment']['source_files'].items():
 raw=subprocess.check_output(['git','show',claim['source']+':'+path],cwd=ROOT);assert sha(raw)==h
assert sha(subprocess.check_output(['git','show',claim['source']+':'+claim['registration']],cwd=ROOT))==claim['registration_sha256']
meta_capture=read(ROOT/claim['inputs']['metadata_capture']['path']);meta_admit=read(ROOT/claim['inputs']['metadata_admission']['path'])
meta=[r for r in meta_capture['requests'] if r['id']=='triangle-exchange-info'];assert len(meta)==1
mr=meta[0];mb=base64.b64decode(mr['body_base64'],validate=True);assert len(mb)==mr['body_bytes'] and sha(mb)==mr['body_sha256'];assert mr['attempted'] and mr['body_complete'] and mr['http_status']==200 and mr['error'] is None
expected=next(r for r in meta_capture['request_spec']['requests'] if r['id']==mr['id']);assert all(mr[k]==v for k,v in expected.items())
ma=next(r for r in meta_admit['cells'] if r['id']==mr['id']);md=loads(mb)
assert ma['symbols']=={r['symbol']:r for r in md['symbols']} and set(ma['symbols'])==set(SYMS)
for s,(base,quote) in {'BTCUSDT':('BTC','USDT'),'ETHUSDT':('ETH','USDT'),'ETHBTC':('ETH','BTC')}.items():
 r=ma['symbols'][s];assert r['baseAsset']==base and r['quoteAsset']==quote and r['status']=='TRADING' and r['isSpotTradingAllowed'] is True
assert ma['status']=='complete' and summary['metadata']['status']=='complete'

transport=capture['transport'];cutoff=transport['unretained_event']['elapsed_ns'];end=transport['end_elapsed_ns']
assert transport['end_reason']=='raw_chunk_capacity' and transport['attempts']==1 and transport['http_status']==101 and transport['opened'] is True
state={};pending_pings=[];pong_delays=[];chunk_sizes=[];chunk_counts=[];rawbytes=0;clocklags=[];last_receipt=-1;last_utc=None;firsttext=None;lasttext=None
startutc=datetime.fromisoformat(transport['start_utc']).timestamp()

def records():
 global rawbytes,last_receipt,last_utc,firsttext,lasttext
 n=0
 for i in range(32):
  path=OUT/f'raw-{i:02d}.json';raw=path.read_bytes();chunk_sizes.append(len(raw));assert len(raw)<=1048576
  chunk=loads(raw);assert chunk['index']==i;chunk_counts.append(len(chunk['receipts']))
  for row in chunk['receipts']:
   assert row['sequence']==n;n+=1
   stamp=row['elapsed_ns'];assert type(stamp) is int and stamp>=0 and stamp>=last_receipt;last_receipt=stamp
   utc=datetime.fromisoformat(row['observation_utc']).timestamp();assert last_utc is None or utc>=last_utc;last_utc=utc
   clocklags.append(utc-startutc-stamp/1e9)
   b=base64.b64decode(row['body_base64'],validate=True);assert len(b)==row['body_bytes'] and sha(b)==row['body_sha256'];rawbytes+=len(b);COUNTS[row['kind']]+=1
   yield row,b
 assert n==capture['receipt_count']==transport['receipt_count'] and rawbytes==capture['raw_payload_bytes']==transport['raw_bytes']

def process(row,raw):
 global firsttext,lasttext
 t=row['elapsed_ns'];kind=row['kind']
 if kind=='outbound-control-wire':
  assert raw[0]==0x8a and raw[1]&128
  size=raw[1]&127;assert size<=125 and len(raw)==6+size
  payload=bytes(v^raw[2+j%4] for j,v in enumerate(raw[6:]))
  assert pending_pings and pending_pings[0][1]==payload
  arrival,_=pending_pings.pop(0);assert t>=arrival;pong_delays.append((t-arrival)/1e9);return
 if kind!='inbound-frame':return
 assert row['fin'] is True,'Actual capture has unsupported fragment requiring separate audit'
 if row['opcode']==9:
  assert len(raw)<=125;DIAG['control_frames']+=1;pending_pings.append((t,raw));return
 assert row['opcode']==1
 d=loads(raw);assert isinstance(d,dict) and isinstance(d['data'],dict)
 r=d['data'];s=r['s'];assert s in SYMS and d['stream']==s.lower()+'@bookTicker'
 u=r['u'];assert type(u) is int and 0<=u<=2**63-1
 q={}
 for k in ('b','a','B','A'):
  v=r[k];assert isinstance(v,str) and len(v)<=64
  x=Decimal(v);assert x.is_finite() and -32<=x.adjusted()<=32 and x>=0 and (k not in ('a','b') or x>0);q[k]=Fraction(x)
 assert q['b']<=q['a']
 if s in state:
  previous=state[s]
  assert u>previous['id'],'Actual duplicate/regression needs separately mapped invalidation'
  DIAG['id_jumps']+=u>previous['id']+1
 state[s]={'q':q,'id':u,'arrival':t};ASSETS[s]+=1
 firsttext=t if firsttext is None else firsttext;lasttext=t

def wallet(direction,capital,fee):
 amount=Fraction(capital);gross=amount;required=[];available=[];sizes=[];rates=[];commissions=[]
 for symbol,buy in PATHS[direction]:
  q=state[symbol]['q'];rate=1/q['a'] if buy else q['b'];rates.append(rate)
  base=amount*rate if buy else amount;size=q['A' if buy else 'B'];required.append(base);available.append(size);sizes.append(base<=size)
  acquired=amount*rate;commissions.append(acquired*fee);amount=acquired*(1-fee);gross*=rate
 charges=[]
 for i,c in enumerate(commissions):
  for rate in rates[i+1:]:c*=rate
  charges.append(c)
 assert sum(charges)==gross-amount
 return [gross/capital,amount/capital,amount-capital,capital*math.log(float(amount/capital)),sum(charges),0.,*required,*available,*sizes],amount>capital and all(sizes)

iterator=iter(records());pending=next(iterator,None);stats={};unsupported=[]
for direction in PATHS:
 for capital in (1000,10000):
  for fee in (Fraction(0),Fraction(1,1000)):
   name=f"{direction}-{capital}-{'zero-fee' if not fee else '10bp'}";stats[name]={'registered_statuses':[],'supported_statuses':[],'maximum_supported_factor':None,'minimum_supported_factor':None,'positive_factor_bins':0,'size_sufficient_bins':0}
assert set(stats)==set(bins['series']) and all(len(v)==5400 for v in bins['series'].values())
for i in range(5400):
 boundary=(i+1)*100000000
 while pending is not None and pending[0]['elapsed_ns']<=boundary:process(*pending);pending=next(iterator,None)
 reason=('capture_tail_raw_chunk_capacity' if boundary>=end else 'missing' if set(state)!=set(SYMS) else 'stale_local_observation' if any(boundary-v['arrival']>1000000000 for v in state.values()) else None)
 REASONS[reason or 'valid']+=1
 if reason:
  assert bins['bin_provenance'][i]==[int(next(k for k,v in bins['reason_codes'].items() if v==reason))]
 else:
  expected=[0,*[(boundary-state[s]['arrival'])/1e6 for s in SYMS],*[state[s]['id'] for s in SYMS]]
  for actual,want in zip(bins['bin_provenance'][i],expected):compare(actual,want)
 if reason is None and boundary>=cutoff:unsupported.append(i)
 for direction in PATHS:
  for capital in (1000,10000):
   for fee in (Fraction(0),Fraction(1,1000)):
    name=f"{direction}-{capital}-{'zero-fee' if not fee else '10bp'}";row=bins['series'][name][i];st=stats[name]
    if reason:
     expected_reason=int(next(k for k,v in bins['reason_codes'].items() if v==reason));assert row==[0,expected_reason];status=0
    else:
     values,qualified=wallet(direction,capital,fee);status=2 if qualified else 1
     assert row[:2]==[status,0] and len(row)==17
     for actual,want in zip(row[2:],values):compare(actual,want)
     if boundary<cutoff:
      factor=float(values[1]);st['maximum_supported_factor']=max(st['maximum_supported_factor'] or factor,factor);st['minimum_supported_factor']=min(st['minimum_supported_factor'] or factor,factor)
      st['positive_factor_bins']+=values[1]>1;st['size_sufficient_bins']+=all(values[-3:])
    st['registered_statuses'].append(status);st['supported_statuses'].append(status if boundary<cutoff else 0)
if pending:process(*pending)
for record in iterator:process(*record)
assert not pending_pings and len(pong_delays)==20 and max(pong_delays)<60
assert COUNTS['inbound-frame']==41514 and sum(ASSETS.values())==41494
for k,v in summary['diagnostics'].items():assert v==DIAG[k],(k,v,DIAG[k])

def describe(statuses):
 valid=sum(x!=0 for x in statuses);positive=sum(x==2 for x in statuses);longest=streak=0
 for x in statuses:streak=streak+1 if x==2 else 0;longest=max(longest,streak)
 return {'valid_bins':valid,'unavailable_bins':5400-valid,'qualified_bins':positive,'unqualified_bins':valid-positive,'longest_consecutive_qualified_bins':longest,'sampled_span_seconds':max(0,longest-1)/10,'fraction_of_planned':positive/5400,'fraction_of_valid':positive/valid if valid else None}
for name,st in stats.items():
 st['registered']=describe(st.pop('registered_statuses'));st['supportable_audit']=describe(st.pop('supported_statuses'))
 for k,v in st['registered'].items():compare(summary['cases'][name][k],v)
 assert st['registered']['qualified_bins']==st['supportable_audit']['qualified_bins'] and st['registered']['longest_consecutive_qualified_bins']==st['supportable_audit']['longest_consecutive_qualified_bins']
assert unsupported==[4077,4078,4079,4080]
assert all(summary[k]=='unavailable' for k in ['annual_relevance','beta','power','expected_return_confidence']) and summary['graduation'] is False
resource=read(REV/'triangle-stream-resource-execution.json');assert resource['child_exit_code']==0 and resource['limit_reason'] is None and resource['peak_sampled_tree_rss_bytes']<536870912 and resource['elapsed_seconds']<600
# Structural verifier is used separately from the independent raw/math reconstruction.
from tradingagents.research.verify import verify_run
structural=verify_run(RUN)
result={'disposition':'MEASUREMENT DEFECT; registered arithmetic and bytes reconcile;32 subslots unsupported after first dropped frame','source':claim['source'],'gate_sha256':claim['registration_sha256'],'output_hashes':complete['output_sha256'],'numeric_checks':CHECKS,'max_absolute_numeric_difference':ERROR,'output_count':35,'output_bytes':outputbytes,'top_cells':9,'subslots':43200,'registered_reasons':dict(REASONS),'raw':{'receipt_count':capture['receipt_count'],'payload_bytes':rawbytes,'kind_counts':dict(COUNTS),'asset_updates':dict(ASSETS),'chunk_bytes':sum(chunk_sizes),'chunk_sizes':chunk_sizes,'chunk_counts':chunk_counts,'first_text_seconds':firsttext/1e9,'last_retained_text_seconds':lasttext/1e9,'ping_pong_pairs':len(pong_delays),'max_observed_pong_delay_seconds':max(pong_delays),'utc_minus_arrival_lag_seconds_range':[min(clocklags),max(clocklags)]},'defect':{'first_unretained_frame_seconds':cutoff/1e9,'recorded_transport_end_seconds':end/1e9,'gap_seconds':(end-cutoff)/1e9,'unsupported_zero_based_bins':unsupported,'unsupported_case_subslots':len(unsupported)*8,'supportable_valid_percase':2353,'supportable_unavailable_percase':3047,'all_affected_registered_statuses':'unqualified','qualified_counts_and_streaks_changed':False,'scope':'Conservative forensic source-support audit, not rewritten registered outcomes or a rerun.'},'cases':stats,'resource':resource,'structural_verification':structural,'limits':['No independently retained complete handshake header to recompute original_header_sha256; projection bytes/hash independently verified.','Dropped frame is digest-only; unknown symbol/payload invalidates support after earliest dropped arrival.','Exact screening confirms only synchronous-price-model necessary conditions for locally aged asynchronous observations, no fills/returns/frequency inference.']}
(REV/'triangle-stream-actual-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'checks':CHECKS,'max_error':ERROR,'cases':stats,'registered_reasons':dict(REASONS),'unsupported':unsupported,'raw':result['raw']},indent=2))
