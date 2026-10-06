"""Pure changed-source review; synthetic records are not recovery/authority receipts."""
import ast,copy,hashlib,importlib.util,json,sys
from pathlib import Path
R=Path.cwd().resolve();D=Path(__file__).resolve().parent;F=D.parents[1];A=F/'real-data-pilot-may30-ledger-cross-volume-continuation01-2026-10-06'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert h(A/'MANIFEST01.json')=='f43ed46f79fb90cd3c9576ca46dba374712176f30d5f407e229382a4b4bf6005'
manifest=json.loads((A/'MANIFEST01.json').read_bytes())
for name,row in manifest.get('files',manifest.get('members')).items():assert h(A/name)==(row['sha256'] if isinstance(row,dict) else row)
inverse=json.loads((A/'INVERSE01.json').read_bytes());edits={}
for name,v in inverse.items():
 old=Path(v['baseline']).read_text();assert hashlib.sha256(old.encode()).hexdigest()==v['before_sha256'];new=old
 for e in v['edits']:
  assert new.count(e['before'])==1;new=new.replace(e['before'],e['after'])
 assert new==(A/name).read_text() and h(A/name)==v['after_sha256'];ast.parse(new);edits[name]=len(v['edits'])
assert h(A/'launch01.py')=='a8d2f41d2c9c3f3289b465990c5cab3126ada975eaea673ec74bbee751b778b6'
def load(path,name):
 sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
m=load(A/'graph_ledger_continuation.py','candidate_metadata');old=load(Path(inverse['graph_ledger_continuation.py']['baseline']),'legacy_metadata')
p=json.loads((A/'PLAN_DRAFT01.json').read_bytes());refusals=[]
def refuse(call,label):
 try:call()
 except (ValueError,TypeError) as e:refusals.append({'case':label,'reason':str(e)})
 else:raise AssertionError(label+' passed')
refuse(lambda:m.plan_check(p),'unbound plan')
p['recovery_review_input']='original_recovery';p['ledger']['sha256']='a'*64
legacy={k:v for k,v in p.items() if k not in ('relocation_receipt_input','relocation_review_input')};legacy['schema_version']=1
assert m.plan_check(legacy)==old.plan_check(legacy)
assert m.relocated_path(Path('/not-accessed'),legacy,lambda _: (_ for _ in ()).throw(AssertionError('legacy relocation read')))==Path('/not-accessed')/m.LEDGER
assert m.plan_check(p)==p
record={'schema_version':1,'kind':'closed-ledger-cross-volume-relocation','identity':p['new_experiment_id'],'predecessor':m.OLD,'original_claim_sha256':m.FIXED['old_claim']['sha256'],'original_source':'14414c1637256dd286eafbe92391129dee3d29bf','original':p['ledger'],'target':{'path':str(m.EXTERNAL),'device':66307,'bytes':3189231616,'sha256':'a'*64,'stat_identity':[66307,123,1,3189231616,1,1,384]},'copy_readback_verified':True,'external_byte_recovery_verified':True,'original_retired':True,'retirement_evidence':{'path':'research/onchain-paper-replication-2026-09-24/synthetic-only/retired.json','sha256':'b'*64}}
def join(r,mutate_review=False):
 raw=json.dumps(r).encode();review={'decision':'accepted','identity':p['new_experiment_id'],'predecessor':m.OLD,'relocation_receipt_sha256':hashlib.sha256(raw).hexdigest(),'complete_copy_recovery_and_retirement':True,'evidence':{r['retirement_evidence']['path']:r['retirement_evidence']['sha256']}}
 if mutate_review:review['relocation_receipt_sha256']='0'*64
 return m.relocation_metadata(p,raw,json.dumps(review).encode())
assert join(record)==record
for kind in ('wrong-path','wrong-device','wrong-source','not-retired','unverified-copy','no-external-recovery','outside-retirement','multilink','wrong-review'):
 r=copy.deepcopy(record)
 if kind=='wrong-path':r['target']['path']='/tmp/ledger.sqlite'
 elif kind=='wrong-device':r['target']['device']=66310
 elif kind=='wrong-source':r['original_source']='0'*40
 elif kind=='not-retired':r['original_retired']=False
 elif kind=='unverified-copy':r['copy_readback_verified']=False
 elif kind=='no-external-recovery':r['external_byte_recovery_verified']=False
 elif kind=='outside-retirement':r['retirement_evidence']['path']='other-study/retired.json'
 elif kind=='multilink':r['target']['stat_identity'][2]=2
 refuse(lambda r=r,kind=kind:join(r,kind=='wrong-review'),kind)
prep=load(A/'prepare01.py','candidate_preparer');refuse(lambda:prep.validate_binding(json.loads((A/'BINDINGS_DRAFT01.json').read_bytes())),'unbound preparation')
assert m.data_budget(p)['limits']=={'max_logical_bytes':3256340480,'max_allocated_bytes':3256340480,'max_entries':2,'max_depth':1,'max_scan_seconds':5}
assert 'expected_resources[\'disk_paths\']=[str(ROOT),str(control.DATA_ROOT)]' in (A/'preflight01.py').read_text()
assert "required_paths=[root]+([DATA_ROOT] if p['schema_version']==2 else [])" in (A/'graph_ledger_continuation.py').read_text()
assert not any(n in sys.modules for n in ('sqlite3','numpy','torch','pyarrow'))
result={'decision':'pass-source-only','source_manifest':h(A/'MANIFEST01.json'),'inverse_edits':edits,'legacy_plan_and_original_path_parity':True,'unchanged_launcher':True,'negative_controls':refusals,'synthetic_positive_scope':'In-memory pure schema only; no actual receipt stored or genuine authority constructed','Data_SQLite_NPY_payload_access':False,'native_network_Git_calls':False}
(D/'CHECK01.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n');print(json.dumps({'decision':result['decision'],'inverses':edits,'refusals':len(refusals),'check_sha256':h(D/'CHECK01.json')}))
