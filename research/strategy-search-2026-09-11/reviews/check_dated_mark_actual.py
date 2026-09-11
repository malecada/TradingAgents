"""Independent raw source and receipt audit; no collector or financial imports."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
from decimal import Decimal
import base64,hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
P=ROOT/'research/strategy-search-2026-09-11';RUN=ROOT/'research_runs/dated-mark-20260911';OUT=RUN/'outputs'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def pairs(items):
 result={}
 for k,v in items:
  if k in result:raise ValueError('duplicate JSON field')
  result[k]=v
 return result
def reject(x):raise ValueError('nonfinite JSON')
def decode(raw):return json.loads(raw,object_pairs_hook=pairs,parse_constant=reject)
def read(p):return decode(p.read_bytes())
def clock(value):
 result=datetime.fromisoformat(value);assert result.utcoffset()==timedelta(0);return result
claim=read(RUN/'claim.json');terminal=read(RUN/'complete.json');capture=read(OUT/'capture.json');admission=read(OUT/'admission.json')
source='5cf5dd843131da489a4695623b81009a244ab49f';assert claim['source']==terminal['source']==source
gate=decode(subprocess.check_output(['git','show',source+':'+claim['registration']],cwd=ROOT))
assert sha((ROOT/claim['registration']).read_bytes())==claim['registration_sha256']==terminal['registration_sha256']
exp=gate['experiments'][claim['experiment_id']];assert exp==claim['experiment']
for path,digest in exp['source_files'].items():
 raw=subprocess.check_output(['git','show',source+':'+path],cwd=ROOT);assert sha(raw)==digest==sha((ROOT/path).read_bytes())
assert sha((RUN/'claim.json').read_bytes())==terminal['claim_sha256']
assert set(p.name for p in OUT.iterdir())==set(exp['outputs'])==set(terminal['output_sha256'])
for path,digest in terminal['output_sha256'].items():assert sha((OUT/path).read_bytes())==digest
spec=read(ROOT/exp['inputs']['request_spec']['path']);assert capture['request_spec']==spec
assert sha((ROOT/exp['inputs']['request_spec']['path']).read_bytes())==exp['inputs']['request_spec']['sha256']
start=int(datetime(2026,5,1,tzinfo=timezone.utc).timestamp()*1000);expected=[start+i*86400000 for i in range(56)];end=expected[-1]+86400000-1
assert spec['expected_open_ms']==expected
assert len(capture['receipts'])==len(admission['cells'])==2
summaries=[];previous=clock(claim['started_at'])
for i,(asset,symbol) in enumerate([('btc','BTCUSDT_260626'),('eth','ETHUSDT_260626')]):
 name=asset+'-dated-mark';filename=name+'-receipt.json';r=read(OUT/filename);ref=capture['receipts'][i];cell=admission['cells'][i]
 assert r['id']==ref['id']==cell['id']==name and r['symbol']==symbol and ref['path']==filename
 params={'symbol':symbol,'interval':'1d','startTime':start,'endTime':end,'limit':100}
 assert r['parameters']==params==spec['requests'][i]['parameters']
 assert r['endpoint']=='https://fapi.binance.com/fapi/v1/markPriceKlines'
 assert r['request_url']==r['endpoint']+f'?symbol={symbol}&interval=1d&startTime={start}&endTime={end}&limit=100'
 assert r['attempted'] is True and r['body_complete'] is True and r['http_status']==200 and r['error'] is None
 raw=base64.b64decode(r['body_base64'],validate=True)
 assert len(raw)==r['body_bytes']==ref['body_bytes'] and len(raw)<=256*1024
 assert sha(raw)==r['body_sha256']==ref['body_sha256'] and sha((OUT/filename).read_bytes())==ref['receipt_sha256']
 requested=clock(r['request_utc']);retrieved=clock(r['retrieval_utc'])
 assert previous<=requested<=retrieved<=clock(capture['capture_closed_utc'])<=clock(terminal['ended_at'])
 assert r['request_utc']==ref['request_utc'] and r['retrieval_utc']==ref['retrieval_utc']
 assert 0<=r['elapsed_seconds']<20 and abs((retrieved-requested).total_seconds()-r['elapsed_seconds'])<.001
 previous=retrieved
 rows=decode(raw);assert type(rows)is list and len(rows)==56
 slots=[]
 for index,row in enumerate(rows):
  assert type(row)is list and len(row)==12
  assert type(row[0])is int and row[0]==expected[index] and type(row[6])is int and row[6]==expected[index]+86400000-1
  for value in row[1:5]:assert type(value)is str and len(value)<=64 and Decimal(value).is_finite() and Decimal(value)>0 and -32<=Decimal(value).adjusted()<=32
  o,h,l,c=map(Decimal,row[1:5]);assert l<=o<=h and l<=c<=h
  slots.append({'open_ms':row[0],'close_ms':row[6],'open':row[1],'high':row[2],'low':row[3],'close':row[4],'row_index':index,'status':'complete'})
 assert cell['slots']==slots and cell['observed_rows']==cell['expected_slots']==cell['complete_slots']==56 and cell['unavailable_slots']==0
 assert cell['status']=='complete' and cell['issues']=={} and cell['malformed_or_unexpected_rows']==[]
 summaries.append({'id':name,'raw_bytes':len(raw),'body_sha256':sha(raw),'rows':len(rows),'missing':0,'duplicate':0,'unexpected':0,'OHLC_valid':56,'first_open_utc':datetime.fromtimestamp(rows[0][0]/1000,timezone.utc).isoformat(),'last_close_utc':datetime.fromtimestamp(rows[-1][6]/1000,timezone.utc).isoformat(),'request_utc':r['request_utc'],'retrieval_utc':r['retrieval_utc'],'ignored_fields':{str(k):{'literal_zero_string_count':sum(row[k]=='0' for row in rows),'literal_integer_count':sum(type(row[k])is int for row in rows)}for k in [5,7,8,9,10,11]}})
assert terminal['cells']==[{'id':x['id'],'status':'complete'}for x in summaries] and terminal['cell_count']==2 and terminal['unavailable_count']==0
assert admission['planned_cells']==2 and admission['planned_subslots']==112 and admission['graduation']is False and admission['expected_profit']=='unavailable'
cert=read(ROOT/exp['budget_extension']['path']);assert sha((ROOT/exp['budget_extension']['path']).read_bytes())==exp['budget_extension']['sha256']
same=[]
for folder in (ROOT/'research_runs').iterdir():
 if folder.name.startswith('.'):continue
 old=read(folder/'claim.json')
 if old['family']['mechanism_id']==claim['family']['mechanism_id']:same.append(folder.name)
assert set(same)==set(cert['prior_claims'])|{claim['experiment_id']} and len(same)==5
assert claim['family']['attempt_budget']==4 and claim['family']['prior_attempts']==1
assert claim['budget_extension']['effective_budget']==6 and claim['budget_extension']['prior_effective_budget']==5 and claim['budget_extension']['prior_claim_count']==4
for name,item in cert['prior_claims'].items():
 folder=ROOT/'research_runs'/name;assert sha((folder/'claim.json').read_bytes())==item['claim_sha256'] and sha((folder/item['terminal']).read_bytes())==item['terminal_sha256']
from tradingagents.research_extended.verify import verify_run as extended_verify
structural=extended_verify(RUN);historical=extended_verify(ROOT/'research_runs/dated-book-amended-20260911')
from tradingagents.research_amended.verify import verify_run as frozen_v1_verify
try:frozen_v1_verify(ROOT/'research_runs/dated-book-amended-20260911')
except ValueError as error:v1_refusal=str(error)
else:raise AssertionError('Frozen live-ledger v1 must refuse the later descendant')
assert 'inventory' in v1_refusal or 'budget' in v1_refusal
guard=read(P/'reviews/dated-mark-resource-execution.json')
assert guard['child_exit_code']==0 and guard['limit_reason']is None and guard['elapsed_seconds']<120 and guard['peak_sampled_tree_rss_bytes']<=512*1024**2
size=sum(x.stat().st_size for x in OUT.iterdir());assert size<=4*1024**2
report={'passed':True,'scope':'Independent saved raw-source schema/chronology/hash reconstruction and receipt verification; no collector imports, financial calculations, network or ledger mutations.','source':source,'sources':summaries,'cells':2,'complete_subslots':112,'unavailable_subslots':0,'output_count':4,'output_bytes':size,'raw_bytes':sum(s['raw_bytes']for s in summaries),'capture_closed_utc':capture['capture_closed_utc'],'structural_verification':structural,'closed_v1_verification':historical,'frozen_v1_live_ledger_refusal':v1_refusal,'accounting':{'historical_units':1,'visible_program_claims':5,'consumed_effective_budget':6,'original_family_cap':4,'new_budget_remaining':0},'guard':guard,'limits':'HTTP receipts substantiate retained public responses, not historical account eligibility, execution, intraday liquidation or positive returns. Historical fields8 are ignored fields, not admitted trade activity.'}
(Path(__file__).parent/'dated-mark-actual-review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
