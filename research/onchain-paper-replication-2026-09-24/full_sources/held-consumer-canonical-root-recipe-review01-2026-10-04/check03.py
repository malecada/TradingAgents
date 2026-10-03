"""Additive committed metadata joins and safe owned-path mutation witness."""
import copy,hashlib,json,os,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;C=H.parent/'held-consumer-canonical-root-recipe01-2026-10-04';G=C/'generated01'
sys.path.insert(0,str(C))
import prepare01 as P
import rebind01 as R
checks=[]
def ok(n,v):
 if not v:raise AssertionError(n)
 checks.append(n)
def sha(raw):return hashlib.sha256(raw).hexdigest()
env=os.environ.copy();env.update(GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0',GIT_CONFIG_NOSYSTEM='1')
r=subprocess.run(['git','-c','protocol.allow=never','-C',str(P.CAP),'ls-tree','-rz',P.HEAD],stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,timeout=15);assert r.returncode==0 and len(r.stdout)<4*1024**2
tree={}
for row in r.stdout.split(b'\0'):
 if row:
  meta,name=row.split(b'\t');mode,kind,oid=meta.decode().split();tree[name.decode()]=(mode,kind,oid)
names=['held-fixture-registration01.json','held-auxiliary-success01.json','held-auxiliary-second_target_publication_failure01.json']
names+=['fixture_inputs/held/'+case+'01/case-contract.json' for case in P.CASES]
joins=[]
for name in names:
 raw=(P.CAP/name).read_bytes();mode,kind,oid=tree[name];ok('genuine committed metadata '+name,kind=='blob' and hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==oid)
 joins.append({'path':name,'git_mode':mode,'git_oid':oid,'sha256':sha(raw),'bytes':len(raw)})
config=Path('research/onchain-paper-replication-2026-09-24/config/model.json');configsha=sha(config.read_bytes());ok('model CONFIG20f451 observed',configsha=='20f451c08143dd81491b5c9fa0a90243ee6a9363df1fbbfcbd9c45b32f9b054d')
draft=json.loads((G/'DRAFT_CASES01.json').read_bytes());mut=copy.deepcopy(draft);original=mut['success']['experiment']['inputs']['execution_job']['path'];owned=H/'opaque-job.json'
with owned.open('xb') as f:f.write((G/'input-draft'/original).read_bytes())
mut['success']['experiment']['inputs']['execution_job']['path']=str(owned)
old=R.read
def reader(path):return P.encode(mut) if Path(path)==G/'DRAFT_CASES01.json' else old(path)
R.read=reader
try:out,bodies=R.rebind('success',str(H/'uncreated-source'))
finally:R.read=old
ok('RR5 absolute owned input path accepted',str(owned) in bodies and out['case_contract']['additional_inputs']['execution_job']['reference']['path']==str(owned))
ok('pure rebind does not mutate owned input',owned.read_bytes()==(G/'input-draft'/original).read_bytes())
ok('candidate draft remains byte unchanged',json.loads((G/'DRAFT_CASES01.json').read_bytes())==draft)
witness={'id':'RR5','candidate_rebind_sha256':sha((C/'rebind01.py').read_bytes()),'mutation':'only execution_job.path replaced by an owned absolute path in a copied in-memory draft','owned_path':str(owned),'accepted_by_pure_rebind':True,'returned_input_path':out['case_contract']['additional_inputs']['execution_job']['reference']['path'],'original_candidate_mutated':False,'external_paths_read':False,'future_capsule_written':False,'release_granted':False}
(H/'RR5_WITNESS01.json').write_text(json.dumps(witness,sort_keys=True,indent=2)+'\n')
(H/'CHECKS03.json').write_text(json.dumps({'schema_version':1,'checks':checks,'count':len(checks),'actual_committed_metadata':joins,'model_configuration':{'path':str(config),'sha256':configsha,'is_model_py':False,'included_in_this_recipe_as_new_body':False},'path_mutation_witness':witness,'actual_native_execution':False,'actual_claims':False,'payload_decoding':False},sort_keys=True,indent=2)+'\n');print(len(checks),'additive checks passed; absolute-input-path acceptance retained')
