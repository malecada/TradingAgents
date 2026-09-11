"""Independent invented dated-mark schema/cell/prefix checks; no network."""
from pathlib import Path
from datetime import datetime,timezone
import base64,copy,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[3];DIRECTORY=ROOT/'research/strategy-search-2026-09-11';sys.path.insert(0,str(DIRECTORY))
import dated_mark as candidate
START=int(datetime(2026,5,1,tzinfo=timezone.utc).timestamp())*1000
END=int(datetime(2026,6,26,tzinfo=timezone.utc).timestamp())*1000-1
DAY=86400000
assert candidate.START==START and candidate.END==END and (END-START+1)//DAY==56
base=[[START+i*DAY,'10','12','9','11',0,START+(i+1)*DAY-1,0,0,0,0,0] for i in range(56)]
checks=[]

def run(raw,status=200,complete=True):
 outputs={};calls=[]
 def persist(name,value):outputs[name]=copy.deepcopy(value)
 def response(url):
  calls.append(url)
  return {'body':raw,'http_status':status,'body_complete':complete,'error':None if status==200 else 'HTTP'+str(status),'headers':{}}
 capture,admission,cells=candidate.run(candidate.default_spec(),persist,response)
 assert len(outputs)==4 and len(cells)==2 and len(admission['cells'])==2
 assert [len(c['slots']) for c in admission['cells']]==[56,56]
 assert all([s['open_ms'] for s in c['slots']]==list(range(START,END+1,DAY)) for c in admission['cells'])
 assert all(c['complete_slots']+c['unavailable_slots']==56 for c in admission['cells'])
 assert sum(len((json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n').encode()) for v in outputs.values())<4*1024**2
 for name,r in outputs.items():
  if not name.endswith('-receipt.json'):continue
  decoded=base64.b64decode(r['body_base64'],validate=True)
  expected=raw[:262144] if r['attempted'] else b''
  assert decoded==expected and r['body_bytes']==len(expected) and r['body_sha256']==hashlib.sha256(expected).hexdigest()
 return admission,cells,outputs,calls

def check(name,rows,complete_slots,source_complete):
 admission,cells,_,_=run(json.dumps(rows).encode())
 assert all(c['complete_slots']==complete_slots for c in admission['cells']),name
 assert all((c['status']=='complete')==source_complete for c in cells),name
 checks.append(name)

check('complete_zero_ignored_fields',base,56,True)
values=copy.deepcopy(base)
for row in values:
 for i in (5,7,8,9,10,11):row[i]={'ignored':['literal',0]}
check('ignored_fields_do_not_become_trade_activity',values,56,True)
check('one_missing_day',base[:-1],55,False)
check('duplicate_first_day',base+[base[0]],55,False)
check('all_reversed_order_not_global_admission',base[::-1],56,False)
values=copy.deepcopy(base);values.append([END+1,'10','12','9','11',0,END+DAY,0,0,0,0,0]);check('unexpected_next_day',values,56,False)
for field,value,name in [(0,START+.5,'fractional_clock'),(0,str(START),'string_clock'),(0,True,'boolean_clock'),(6,START+DAY,'close_one_ms_late'),(1,'0','zero_price'),(2,'10.9999999999999999999999','exact_high_below_close'),(3,'10.0000000000000000000001','exact_low_above_open'),(4,'NaN','nonfinite_price'),(1,'1e-33','exponent_outside'),(1,'1'*65,'coefficient_outside')]:
 values=copy.deepcopy(base);values[0][field]=value;check(name,values,55,False)
raw=json.dumps(base).encode();raw+=b' '*(262144-len(raw));a,c,_,_=run(raw);assert all(v['status']=='complete' for v in c);checks.append('exact256KiB_valid_body')
a,c,o,_=run(raw+b' ');assert all(v['status']=='unavailable' for v in c);assert all(not r['body_complete'] for n,r in o.items() if n.endswith('-receipt.json'));checks.append('overflow_bounded_prefix')
a,c,o,calls=run(b'denied',451);assert len(calls)==1 and all(v['status']=='unavailable' for v in c);checks.append('denial_suppresses_second_preserves112')
for raw,name in [(b'['*12000+b'0'+b']'*12000,'deeply_nested_json'),(b'[NaN]','nonfinite_ignored_json'),(b'['+b'0,'*120000+b'0]','large_malformed_projection')]:
 a,c,_,_=run(raw);assert all(v['status']=='unavailable' for v in c);checks.append(name)
result={'passed':True,'independent_scenarios':len(checks),'checks':checks,'source_sha256':hashlib.sha256((DIRECTORY/'dated_mark.py').read_bytes()).hexdigest(),'transport_sha256':hashlib.sha256((DIRECTORY/'dated_mark_transport.py').read_bytes()).hexdigest(),'scope':'Invented bytes only. Independently specified UTC day grid, OHLC boundary expectations and fixed output/slot/hash conservation; no historical market bodies, network or ResearchRun.'}
(Path(__file__).parent/'dated-mark-synthetic-review.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
