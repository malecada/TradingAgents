"""Exact future actual file-read inventory; does not execute public preflight.
Refuses until fixed final request and genuine release/proofs exist. No output
unless all actual byte/source/proof joins and original8MiB Reader.finish pass.
"""
from pathlib import Path
import hashlib,importlib.util,json,os
H=Path(__file__).resolve().parent
P=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-complete100-compatibility-root-launch-20261004-01')
CAP=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source')
raw=(P/'preclaim01.py').read_bytes();assert hashlib.sha256(raw).hexdigest()=='557b7bcb38b48e3bf1e9e5b5b1eae25ab4908b8567820e17700dc08774b48d16'
spec=importlib.util.spec_from_file_location('_actual_final_budget_reader',P/'preclaim01.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert not (H/'FINAL_READ_INVENTORY01.json').exists(),'one immutable observed output'
r=m.Reader();qraw=r.read(P/'REQUEST_FINAL01.json');q=json.loads(qraw)
m.require(q['status']=='RELEASED_ONE_USE_FINANCIAL_PARENT' and q['source']==q['design_source']=='32d57eac5ea14435cd9d4aeb3e3b04d98bf16c41','genuine final source contract required')
m.require(q['parent_root']==str(P) and q['capsule_root']==str(CAP) and q['identity']=='financial-wrapper-classification-eager-complete100-compatibility-20261004-01','fixed unused actual Parent identity')
regraw=r.read(CAP/q['registration']);m.require(m.sha(regraw)==q['registration_sha256'],'actual gate');g=json.loads(regraw);e=g['experiments'][q['identity']];i=m.Inputs(CAP,e['inputs'],r);policy=i.json('operational_source_compatibility')
m.require(e['source_files']==q['source_files'] and len(q['source_files'])==354,'complete354 source map');m.require(q['runtime_mapping']==i.json('runtime_mapping') and q['input_hashes']=={k:v['sha256'] for k,v in e['inputs'].items()},'all actual inputs/runtime')
for n,h in policy['target']['installed'].items():m.require(m.sha(r.read(CAP/n))==h,'current target source')
m.require(set(q['proofs'])=={'cumulative','full_recovery','independent_source_input_runtime'},'all three genuine proof roles');proofs={k:r.reference(v) for k,v in q['proofs'].items()}
external=json.loads(proofs['independent_source_input_runtime'])['compatibility_preclaim_external_refs'];m.require(set(external)==m.EXTERNAL-{'final_parent_contract','final_parent_review'},'exact eight actual refs')
for kind in ('review','recovery'):m._proof_bundle(kind,external,i,policy,r)
m.require(m.sha(r.read(P/'parent01.py'))==q['caller_sha256'],'caller pin')
for n,h in q['helper_hashes'].items():m.require(Path(n).name==n and m.sha(r.read(P/n))==h,'seven actual helpers')
review=json.loads(r.reference(q['final_review']));expected={'schema_version':1,'decision':'accepted-exact-one-use-financial-parent','contract_sha256':m.sha(m.encoded({k:v for k,v in q.items() if k!='final_review'})),'proof_sha256':{k:m.sha(v) for k,v in proofs.items()},'identity':q['identity'],'source':q['source'],'caller_sha256':q['caller_sha256']};m.require(review==expected,'genuine exact final release joins')
m.require(not os.path.lexists(P/'attempt') and not os.path.lexists(CAP/'research_runs'/q['identity']),'fresh actual attempt/claim absent')
first=r.total;r.finish();m.require(r.total==2*first,'full actual cache includingfinish')
result={'schema_version':1,'decision':'ACTUAL_BYTE_READ_INVENTORY_ONLY_NOT_PUBLIC_PREFLIGHT','first_read_bytes':first,'complete_reader_bytes':r.total,'remaining_bytes':m.TOTAL-r.total,'paths':len(r.cache),'final_request_sha256':m.sha(qraw),'final_review_sha256':q['final_review']['sha256'],'inventory':[{'path':str(p),'bytes':len(b),'sha256':m.sha(b)} for p,b in r.cache.items()],'public_preclaim_executed':False,'Admission_Run_Owner_created':False,'native_numerical_release':False,'exclusions':['Parent outer source/Git/runtime/resource eligibility checks','genuine Admission verification','scientific execution']}
with (H/'FINAL_READ_INVENTORY01.json').open('x') as f:f.write(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='inventory'}))
