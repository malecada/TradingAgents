"""Unregistered cold-proof templates. No admission, numerical import or job API.

Materialization needs a genuine installed committed capsule and real input bytes.
Comparison deliberately refuses the unresolved outer02 equal-commit boundary.
"""
import argparse,hashlib,importlib.util,json,os,re,stat,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PROGRAM='compact-cold-engineering-20261003'
FAMILY='compact-cold-genuine-authority'
IDS={'materialize':'compact-cold-inputs-20261003-01','compare':'compact-cold-comparison-20261003-01'}
CELL={'materialize':'cold-input-materialization','compare':'cold-genuine-comparison'}
MAX=4194304;GIB=1073741824
PINNED_INVENTORY='e12b979c843f52eec39b0a0edd978dc50de9901d98b0446c716fc8d97ffc6a58'
CONFIG_PINS={'recipe':'35a10c4b1e342afe2bff01e6d655b4d93312e07302b2061a237dcea861f56570','configs':'1ceae44792c7ff3ff76ce15a7cf79b0267e4a919f56917473862ddf432935a1f','model':'29af65736dddfbd22b5ce94c6ff3e507041b00dc81dfcc94c6919a615a68dcb7','training':'99fb74a84b85ddff9589e5a8706f8b5ef3807a3f065dfb7091a220a28af63bb3'}
def require(v,m):
 if not v:raise ValueError(m)
def digest(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()
def sha(v):return type(v) is str and re.fullmatch('[0-9a-f]{64}',v) and len(set(v))>1
def body(root,name):
 require(type(name) is str,'path must be text');rel=Path(name);p=root/rel
 require(not rel.is_absolute() and '..' not in rel.parts and not any(x in {'keys','apis','.env','hf_token.txt'} or x.startswith('.env.') for x in rel.parts),'unsafe input path')
 require(p.resolve()==p and p.is_relative_to(root),'redirected input path');s=p.lstat()
 require(stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size<=MAX,'bounded regular body required')
 b=p.read_bytes();t=p.lstat();require((s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(t.st_dev,t.st_ino,t.st_size,t.st_mtime_ns,t.st_ctime_ns) and len(b)==s.st_size,'body changed');return b
def reference(root,r):
 require(type(r) is dict and set(r)=={'path','sha256'} and sha(r['sha256']),'exact reference required')
 b=body(root,r['path']);require(digest(b)==r['sha256'],'reference hash differs');return b
def document(root,r):return json.loads(reference(root,r))
def git(root,*args):return subprocess.check_output(['git',*args],cwd=root,stderr=subprocess.PIPE,timeout=15)
def resources(root,p):
 require(type(p) is dict,'resources required')
 exact={'memory_max_bytes':3*GIB,'memory_high_bytes':3*GIB,'reserve_bytes':3*GIB,'start_reserve_bytes':6*GIB,'wall_seconds':1800,'disk_floor_bytes':10*GIB}
 for k,v in exact.items():require(type(p.get(k)) is int and p[k]==v,'resource bound differs: '+k)
 require(p.get('disk_paths')==[str(root)] and p.get('native_unit_limits')=={'file_size_bytes':MAX} and 'physical_policy' not in p,'native file/disk route differs')
 require(type(p['native_unit_limits']['file_size_bytes']) is int,'file cap type differs')
 require(p.get('storage_budget')=={'root':str(root),'limits':{'max_allocated_bytes':GIB,'max_logical_bytes':GIB,'max_entries':32768,'max_depth':32,'max_scan_seconds':5}},'whole capsule watch differs')
 return p
def blocked_compare(request):
 # No status flag, accepted summary or forged receipt can bypass this boundary.
 raise ValueError('COMPARISON_UNREGISTRABLE: outer02 requires the materialization commit equal current HEAD, while exact emitted-input registration requires a later commit; separately reviewed historical-source descendant binding is required')
def validate(root,request):
 require(type(request) is dict and request.get('phase') in IDS,'fixed phase required')
 if request['phase']=='compare':blocked_compare(request)
 keys={'schema_version','phase','root','source','inventory','runtime','environment','resources','anchor','inputs','cpus'}
 require(set(request)==keys and type(request['schema_version']) is int and request['schema_version']==1,'request fields differ')
 require(type(request['root']) is str and request['root']==str(root) and root.resolve()==root and Path.cwd()==root,'genuine capsule cwd required')
 source=request['source'];require(type(source) is str and re.fullmatch('[0-9a-f]{40}',source) and len(set(source))>1,'real source commit required')
 require((root/'.git').is_dir() and not (root/'.git').is_symlink() and not (root/'.git/objects/info/alternates').exists(),'independent capsule Git required')
 require(git(root,'rev-parse','HEAD').decode().strip()==source,'current source differs')
 inventory_raw=reference(root,request['inventory']);require(digest(inventory_raw)==PINNED_INVENTORY,'accepted CSC2 inventory differs')
 inventory=json.loads(inventory_raw);rows=inventory['source_inventory'];require(len(rows)==195 and len({r['target'] for r in rows})==195,'full195 source denominator required')
 sources={}
 for row in rows:
  b=body(root,row['target']);require(len(b)==row['bytes'] and digest(b)==row['sha256'] and git(root,'show',source+':'+row['target'])==b,'installed source/Git differs: '+row['target']);sources[row['target']]=row['sha256']
 runtime=document(root,request['runtime']);environment=document(root,request['environment'])
 require(not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules),'numerical/research imports forbidden')
 # Exact accepted stdlib runtime checker; cannot mint a runtime from booleans.
 name='cold_registration_runtime';path=root/'proof_tools/runtime_gate01.py'
 spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);runtime_readback=module.check(root,runtime)
 p=resources(root,document(root,request['resources']))
 cpus=request['cpus'];require(type(cpus) is list and len(cpus)==2 and all(type(x) is int and x>=0 for x in cpus) and cpus==sorted(set(cpus)),'two CPU identities required')
 anchor=document(root,request['anchor']);require(set(anchor)=={'commit','files'} and type(anchor['commit']) is str and re.fullmatch('[0-9a-f]{40}',anchor['commit']) and anchor['files'],'real numerical anchor required')
 git(root,'merge-base','--is-ancestor',anchor['commit'],source)
 for name,h in anchor['files'].items():require(sha(h) and digest(git(root,'show',anchor['commit']+':'+name))==h,'numerical anchor Git body differs')
 inputs=request['inputs'];require(type(inputs) is dict and set(inputs)=={'recipe','configs','model','training','anchor','future_resources','environment','cold_proof','execution_job'},'materialization input denominator differs')
 docs={}
 for name,r in inputs.items():
  require(type(r) is dict and set(r)=={'path','sha256','dataset'} and r['dataset']=='synthetic-cold','input role differs');docs[name]=document(root,{k:r[k] for k in ('path','sha256')})
 for role,h in CONFIG_PINS.items():require(digest(canonical(docs[role]))==h,'frozen configuration changed: '+role)
 for name,ref in [('anchor','anchor'),('future_resources','resources'),('environment','environment')]:require({k:inputs[name][k] for k in ('path','sha256')}==request[ref],'original resource/runtime/anchor input route differs')
 job=docs['execution_job'];require(set(job)=={'schema_version','kind','environment_input','resources','payload'} and type(job['schema_version']) is int and job['schema_version']==1 and job['kind']=='fit' and job['environment_input']=='environment' and job['resources']==p and job['payload']=={'cold_proof_input':'cold_proof','representation_jobs':{}},'actual materialization worker job differs')
 policy={'schema_version':1,'kind':'genuine-compact-cold-engineering-proof-v1','phase':'materialize','experiment':IDS['materialize'],'output':'proof-materialize.json','inputs':{n:n for n in ('recipe','configs','model','training','anchor','future_resources')},'source_files':sources,'watch':p['storage_budget'],'max_file_bytes':MAX,'max_total_bytes':268435456}
 require(docs['cold_proof']==policy,'materialization source/policy differs')
 for identity in IDS.values():
  for base in ('research_runs','proof_outer','proof_supervise','research_artifacts/compact-cold-engineering-20261003','research_artifacts/onchain-paper-replication-2026-09-24/runs'):
   q=root/base/identity;require(not q.exists() and not q.is_symlink(),'one-use identity already reserved')
 return sources,runtime_readback

def render(root,request,charter_ref,history_ref):
 sources,readback=validate(root,request)
 # Documents must already be root-installed genuine copies; no supplied prose replaces frozen policy.
 for ref,name in [(charter_ref,'CHARTER_MATERIALIZE01.md'),(history_ref,'HISTORY01.md')]:require(reference(root,ref)==(HERE/name).read_bytes(),'frozen charter/history differs')
 family={'mechanism_id':'compact-cold-genuine-authority','attempt_budget':2,'prior_attempts':0,'history_reference':history_ref['path']}
 experiment={'family':FAMILY,'parent':None,'question':'Can the frozen fresh synthetic cold-proof population be materialized under genuine guarded ResearchRun authority?','stage':'development','reuse':'exploratory','charter':charter_ref,'source_files':sources,'runtime_hashes':{Path(k).name:v for k,v in sources.items() if str(Path(k).parent)=='tradingagents/research'},'cells':[CELL['materialize']],'outputs':['proof-materialize.json'],'inputs':request['inputs'],'windows':[{'dataset':'synthetic-cold','start':'2023-12-04T00:00:00Z','end':'2024-05-13T00:00:00Z','availability':'existing'}]}
 return {'schema_version':1,'kind':'unregistered-cold-engineering-draft','execution_authorized':False,'registration':{'schema_version':1,'program_id':PROGRAM,'families':{FAMILY:family},'datasets':{'synthetic-cold':{'identity':'compact-cold-synthetic-20261003','history_reference':history_ref['path'],'exposures':[]}},'experiments':{IDS['materialize']:experiment}},'root_required':['independent exact registration/budget/native release','commit actual registration and charter before any claim','fresh source/Git/native/input check at final execution','separate reviewed outer historical-source correction before comparison registration'],'runtime_readback':readback,'comparison_status':'unregistrable-until-authenticated-materialization-and-source-sequencing-correction'}

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--request',required=True);parser.add_argument('--charter',required=True);parser.add_argument('--history',required=True);parser.add_argument('--output',required=True);a=parser.parse_args();root=Path(a.root)
 request=json.loads(body(root,a.request));charter=json.loads(body(root,a.charter));history=json.loads(body(root,a.history));result=render(root,request,charter,history)
 output=root/a.output;require(not Path(a.output).is_absolute() and '..' not in Path(a.output).parts and output.resolve()==output and output.parent.is_dir(),'new local draft output required')
 raw=canonical(result)+b'\n';require(len(raw)<=MAX,'draft too large');fd=os.open(output,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);primary=None
 try:
  view=memoryview(raw)
  while view:
   n=os.write(fd,view);require(n>0,'short draft write');view=view[n:]
  os.fsync(fd)
 except BaseException as error:primary=error
 try:os.close(fd)
 except BaseException as error:
  if primary is None or (isinstance(primary,Exception) and not isinstance(primary,(MemoryError,RecursionError))):primary=error
 if primary is not None:raise primary
 # A draft is not a released or durable claim and never reserves an identity.
 print(json.dumps({'status':'unregistered-draft','path':a.output,'sha256':digest(raw),'execution_authorized':False}))
if __name__=='__main__':main()
