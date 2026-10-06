"""Pure schema/inverse controls; synthetic records never become receipts."""
from pathlib import Path
import ast,copy,hashlib,importlib.util,json,sys
H=Path(__file__).resolve().parent;R=H.parents[3]
for name,v in json.loads((H/'INVERSE01.json').read_text()).items():
 s=(R/v['baseline']).read_text();assert hashlib.sha256(s.encode()).hexdigest()==v['before_sha256']
 for e in v['edits']:assert s.count(e['before'])==1;s=s.replace(e['before'],e['after'])
 assert s==(H/name).read_text();ast.parse(s)
def load(name,path):
 sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=load('metadata_only',H/'graph_ledger_continuation.py');p=json.loads((H/'PLAN_DRAFT01.json').read_text())
try:m.plan_check(p)
except ValueError as e:assert 'distinct registered relocation roles' in str(e)
else:raise AssertionError('null actual recovery accepted')
p['ledger']['sha256']='a'*64;p['recovery_review_input']='original_recovery';m.plan_check(p)
legacy={k:v for k,v in p.items() if k not in ('relocation_receipt_input','relocation_review_input')};legacy['schema_version']=1
base=load('legacy',R/json.loads((H/'INVERSE01.json').read_text())['graph_ledger_continuation.py']['baseline']);assert m.plan_check(legacy)==base.plan_check(legacy)
r={'schema_version':1,'kind':'closed-ledger-cross-volume-relocation','identity':p['new_experiment_id'],'predecessor':m.OLD,'original_claim_sha256':m.FIXED['old_claim']['sha256'],'original_source':'14414c1637256dd286eafbe92391129dee3d29bf','original':p['ledger'],'target':{'path':str(m.EXTERNAL),'device':66307,'bytes':3189231616,'sha256':'a'*64,'stat_identity':[66307,1,1,3189231616,1,1,384]},'copy_readback_verified':True,'external_byte_recovery_verified':True,'original_retired':True,'retirement_evidence':{'path':'research/onchain-paper-replication-2026-09-24/storage/synthetic/retired.json','sha256':'b'*64}}
def review(raw):return json.dumps({'decision':'accepted','identity':p['new_experiment_id'],'predecessor':m.OLD,'relocation_receipt_sha256':m.sha(raw),'complete_copy_recovery_and_retirement':True,'evidence':{r['retirement_evidence']['path']:'b'*64}}).encode()
raw=json.dumps(r).encode();assert m.relocation_metadata(p,raw,review(raw))==r
for change in ('path','device','retirement','ancestry'):
 x=copy.deepcopy(r)
 if change=='path':x['target']['path']='/tmp/other.sqlite'
 if change=='device':x['target']['device']=66310
 if change=='retirement':x['original_retired']=False
 if change=='ancestry':x['original_source']='0'*40
 raw=json.dumps(x).encode()
 try:m.relocation_metadata(p,raw,review(raw))
 except ValueError:pass
 else:raise AssertionError(change)
raw=json.dumps(r).encode();bad=json.loads(review(raw));bad['relocation_receipt_sha256']='0'*64
try:m.relocation_metadata(p,raw,json.dumps(bad).encode())
except ValueError:pass
else:raise AssertionError('wrong review join')
prep=load('prep',H/'prepare01.py')
try:prep.validate_binding(json.loads((H/'BINDINGS_DRAFT01.json').read_text()))
except ValueError as e:assert 'unavailable' in str(e)
else:raise AssertionError('null binding accepted')
assert m.data_budget(p)['limits']['max_allocated_bytes']==3189231616+64*1024**2
assert 6226836069-3189231616+5403824128==8441428581
assert 6281887744-3189231616+5403824128==8496480256
assert all(n not in sys.modules for n in ('sqlite3','numpy','torch'))
print('PASS three exact inverses; legacy parity; null proof; fixed path/device/retirement/ancestry/review refusals; scalar domain arithmetic; no Data/SQLite/payload reads')
