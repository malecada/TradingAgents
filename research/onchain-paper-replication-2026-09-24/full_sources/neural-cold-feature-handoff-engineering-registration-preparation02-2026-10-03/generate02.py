"""Unregistered cold-proof templates. No admission, numerical import or job API.

Materialization needs a genuine installed committed capsule and real input bytes.
Comparison uses accepted outer03 historical authentication before producing drafts.
"""
import argparse,hashlib,importlib.util,json,os,re,stat,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
PROGRAM='compact-cold-engineering-20261003'
FAMILY='compact-cold-genuine-authority'
IDS={'materialize':'compact-cold-inputs-20261003-01','compare':'compact-cold-comparison-20261003-01'}
CELL={'materialize':'cold-input-materialization','compare':'cold-genuine-comparison'}
MAX=4194304;GIB=1073741824
PINNED_INVENTORY='8576e2baba60576818ee4def16fcfad32cc69bd197c4ff1b727808d9695786d2'
RELEASE_SHA='53c2294b7b38f340e9160e4484a6b7506942ce36e2dff12694a47f9b72206812'
CONFIG_PINS={'recipe':'35a10c4b1e342afe2bff01e6d655b4d93312e07302b2061a237dcea861f56570','configs':'1ceae44792c7ff3ff76ce15a7cf79b0267e4a919f56917473862ddf432935a1f','model':'29af65736dddfbd22b5ce94c6ff3e507041b00dc81dfcc94c6919a615a68dcb7','training':'99fb74a84b85ddff9589e5a8706f8b5ef3807a3f065dfb7091a220a28af63bb3'}
MATERIAL_INPUTS=frozenset(['graph-'+str(i).zfill(2) for i in range(19)]+['population','model','training','calendar','coverage','pair_checkpoint','compact_policy','compact_training','compact_sampler','compact_samples','compact_dictionary','compact_mcm','compact_mcm_output','compact_feature','compact_graph_output','compact_denominator','compact_closure','compact_publication','compact_terminal','compact_native_features','compact_cold_handoff','cold_proof','plan','future_execution_job'])

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
def validate(root,request):
 require(type(request) is dict and request.get('phase') in IDS,'fixed phase required')
 require(request['phase']=='materialize','use authenticated comparison generator')
 keys={'schema_version','phase','root','source','inventory','runtime','environment','resources','anchor','inputs','cpus'}
 require(set(request)==keys and type(request['schema_version']) is int and request['schema_version']==1,'request fields differ')
 require(type(request['root']) is str and request['root']==str(root) and root.resolve()==root and Path.cwd()==root,'genuine capsule cwd required')
 source=request['source'];require(type(source) is str and re.fullmatch('[0-9a-f]{40}',source) and len(set(source))>1,'real source commit required')
 require((root/'.git').is_dir() and not (root/'.git').is_symlink() and not (root/'.git/objects/info/alternates').exists(),'independent capsule Git required')
 require(git(root,'rev-parse','HEAD').decode().strip()==source,'current source differs')
 inventory_raw=reference(root,request['inventory']);require(digest(inventory_raw)==PINNED_INVENTORY,'accepted outer03 inventory differs')
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
 for ref,name in [(charter_ref,'CHARTER_MATERIALIZE02.md'),(history_ref,'HISTORY02.md')]:require(reference(root,ref)==(HERE/name).read_bytes(),'frozen charter/history differs')
 family={'mechanism_id':'compact-cold-genuine-authority','attempt_budget':2,'prior_attempts':0,'history_reference':history_ref['path']}
 experiment={'family':FAMILY,'parent':None,'question':'Can the frozen fresh synthetic cold-proof population be materialized under genuine guarded ResearchRun authority?','stage':'development','reuse':'exploratory','charter':charter_ref,'source_files':sources,'runtime_hashes':{Path(k).name:v for k,v in sources.items() if str(Path(k).parent)=='tradingagents/research'},'cells':[CELL['materialize']],'outputs':['proof-materialize.json'],'inputs':request['inputs'],'windows':[{'dataset':'synthetic-cold','start':'2023-12-04T00:00:00Z','end':'2024-05-13T00:00:00Z','availability':'existing'}]}
 return {'source_document':{'schema_version':1,'files':sources},'phase_contract':{'schema_version':1,'identity':IDS['materialize'],'experiment':experiment,'family':family,'expected_outputs':experiment['outputs']},'gate_template':{'schema_version':1,'kind':'unregistered-materialization-release-template','status':'draft','phase':'materialize','root':str(root),'source':None,'registration':None,'sources':None,'runtime':request['runtime'],'native_environment':request['environment'],'phase_contract':None,'prior_materialization':None,'cpus':request['cpus'],'execution_authorized':False,'remaining':['commit root reviewed exact registration/charter and select actual A','use accepted build_release_draft01 helper with exact document refs to assemble reviewed release']},'schema_version':1,'kind':'unregistered-cold-engineering-draft','execution_authorized':False,'registration':{'schema_version':1,'program_id':PROGRAM,'families':{FAMILY:family},'datasets':{'synthetic-cold':{'identity':'compact-cold-synthetic-20261003','history_reference':history_ref['path'],'exposures':[]}},'experiments':{IDS['materialize']:experiment}},'root_required':['independent exact registration/budget/native release','commit actual registration and charter before any claim','fresh source/Git/native/input check at final execution','genuine materialization then authenticated comparison draft and sole-child release'],'runtime_readback':readback,'comparison_status':'requires-actual-materialization-and-reviewed-sole-child-registration-release'}

def new_path(root,name):
 require(type(name) is str and name and not Path(name).is_absolute() and '..' not in Path(name).parts,'new local path required')
 p=root/name;require(p.resolve()==p and p.is_relative_to(root) and not p.exists() and not p.is_symlink(),'new output path already exists or redirected')
 require(not any(x in {'keys','apis','.env','hf_token.txt'} or x.startswith('.env.') for x in Path(name).parts),'secret location forbidden');return p

def source_closure(root,source,inventory_ref):
 require(root.resolve()==root and Path.cwd()==root and type(source) is str and re.fullmatch('[0-9a-f]{40}',source),'exact current capsule source required')
 require((root/'.git').is_dir() and not (root/'.git').is_symlink() and not (root/'.git/objects/info/alternates').exists(),'independent capsule Git required')
 require(git(root,'rev-parse','HEAD').decode().strip()==source,'source HEAD differs')
 raw=reference(root,inventory_ref);require(digest(raw)==PINNED_INVENTORY,'accepted outer03 inventory differs')
 rows=json.loads(raw)['source_inventory'];require(len(rows)==195 and len({r['target'] for r in rows})==195,'source denominator differs')
 sources={}
 for r in rows:
  data=body(root,r['target']);require(len(data)==r['bytes'] and digest(data)==r['sha256'] and git(root,'show',source+':'+r['target'])==data,'source Git/body drift');sources[r['target']]=r['sha256']
 require(sources['proof_tools/proof_release01.py']==RELEASE_SHA,'accepted release API differs');return sources

def load_release(root,sources):
 require(not any(n.split('.')[0] in {'numpy','torch','scipy'} for n in sys.modules),'numerical imports forbidden')
 for name in ('proof_raw01','proof_release01'):
  target=root/'proof_tools'/(name+'.py');require(digest(body(root,str(target.relative_to(root))))==sources[str(target.relative_to(root))],'release dependency differs')
  if name in sys.modules:require(Path(sys.modules[name].__file__).resolve()==target,'foreign release module already imported')
 sys.path.insert(0,str(root/'proof_tools'))
 import importlib
 release=importlib.import_module('proof_release01');require(Path(release.__file__).resolve()==root/'proof_tools/proof_release01.py','release origin differs');return release

def ref_bytes(path,data):return {'path':path,'sha256':digest(data),'bytes':len(data),'kind':'document'}

def compare_documents(retained,paths,accepted_ref,wait_ref,charter_bytes):
 """Pure deterministic assembly AFTER authentication; not a capability factory."""
 ctx=retained['context'];original=ctx['release'];old=retained['registration'];material=retained['material']
 require(old['program_id']==PROGRAM and set(old['experiments'])=={IDS['materialize']} and set(old['families'])=={FAMILY},'original program/family/experiment differs')
 family=old['families'][FAMILY];require(family['mechanism_id']==FAMILY and type(family['attempt_budget']) is int and family['attempt_budget']==2 and type(family['prior_attempts']) is int and family['prior_attempts']==0,'finite engineering budget/history differs')
 require(set(paths)=={'registration','charter','evolution','phase_contract'} and len(set(paths.values()))==4,'exact disjoint output paths required')
 require(charter_bytes==(HERE/'CHARTER_COMPARE02.md').read_bytes(),'frozen comparison charter differs')
 require(set(material['inputs'])==MATERIAL_INPUTS,'actual materialized denominator required')
 first=old['experiments'][IDS['materialize']];new=json.loads(canonical(first));new.update(parent=IDS['materialize'],question='Does genuine scientific cold detachment preserve exact resident joint-model trajectories, lifetimes and checkpoint behavior?',cells=[CELL['compare']],outputs=['binding.json','journal.json','cold-handoff.json','proof-compare.json'],charter={'path':paths['charter'],'sha256':digest(charter_bytes)},inputs={('execution_job' if name=='future_execution_job' else name):info for name,info in material['inputs'].items()}|{'environment':first['inputs']['environment']})
 registration=json.loads(canonical(old));registration['experiments'][IDS['compare']]=new
 contract={'schema_version':1,'identity':IDS['compare'],'experiment':new,'family':family,'expected_outputs':new['outputs']}
 rawreg=canonical(registration)+b'\n';rawcontract=canonical(contract)+b'\n'
 regref=ref_bytes(paths['registration'],rawreg);contractref=ref_bytes(paths['phase_contract'],rawcontract)
 rows=sorted([{'path':paths['registration'],'sha256':digest(rawreg),'role':'comparison-registration'},{'path':paths['charter'],'sha256':digest(charter_bytes),'role':'comparison-charter'},{'path':paths['phase_contract'],'sha256':digest(rawcontract),'role':'comparison-phase-contract'}],key=lambda r:r['path'])
 evolution={'schema_version':1,'kind':'cold-proof-additive-registration-evolution-v1','parent_source':original['source'],'original_registration':original['registration'],'current_registration':regref,'accepted':accepted_ref,'wait':wait_ref,'additions':rows}
 rawevolution=canonical(evolution)+b'\n'
 files={paths['registration']:rawreg,paths['charter']:charter_bytes,paths['phase_contract']:rawcontract,paths['evolution']:rawevolution}
 require(all(len(b)<=MAX for b in files.values()),'bounded draft extent exceeded')
 # No B hash or self hash is included in the committed evolution body.
 gate={'schema_version':1,'kind':'unregistered-comparison-release-template','status':'draft','phase':'compare','root':original['root'],'source':None,'registration':regref,'sources':original['sources'],'runtime':original['runtime'],'native_environment':original['native_environment'],'phase_contract':contractref,'prior_materialization':{'accepted':accepted_ref,'wait':wait_ref,'evolution':ref_bytes(paths['evolution'],rawevolution)},'cpus':original['cpus'],'remaining':['commit exactly four generated bodies as sole direct child B of original A','do not commit this gate template in B','fill actual B source in a NEW reviewed release envelope of kind cold-proof-outer-release-v1','actual fresh admission/native readiness and independent release required'],'execution_authorized':False}
 return {'files':files,'registration':registration,'experiment':new,'gate_template':gate,'exact_commit_additions':sorted(files),'parent_source':original['source']}

def prepare_compare(root,request):
 keys={'schema_version','phase','root','source','inventory','accepted','wait','paths','charter_template'}
 require(type(request) is dict and set(request)==keys and type(request['schema_version']) is int and request['schema_version']==1 and request['phase']=='compare' and request['root']==str(root),'comparison request differs')
 sources=source_closure(root,request['source'],request['inventory'])
 for path in request['paths'].values():new_path(root,path)
 release=load_release(root,sources)
 retained=release.authenticated_materialization(root,request['accepted'],request['wait'])
 original=retained['context']['release'];require(original['source']==request['source'],'draft comparison only at original A before B')
 require(retained['context']['sources']==sources,'authenticated original sources differ')
 family=retained['registration']['families'][FAMILY]
 require(body(root,family['history_reference'])==(HERE/'HISTORY02.md').read_bytes(),'original family history template differs')
 require(git(root,'show',original['source']+':'+family['history_reference'])==body(root,family['history_reference']),'original history not committed at A')
 charter=reference(root,request['charter_template']);require(git(root,'show',original['source']+':'+request['charter_template']['path'])==charter,'comparison charter template not committed at A')
 for base in ('research_runs','proof_outer','proof_supervise','research_artifacts/compact-cold-engineering-20261003','research_artifacts/onchain-paper-replication-2026-09-24/runs'):
  p=root/base/IDS['compare'];require(not p.exists() and not p.is_symlink(),'comparison identity already reserved')
 result=compare_documents(retained,request['paths'],request['accepted'],request['wait'],charter)
 release._registration_evolution(retained['registration'],result['registration'],result['experiment'],retained['material'])
 return result

def write_exclusive(path,raw):
 """Draft writer: retain first actual fatal and close every acquired FD once."""
 require(len(raw)<=MAX,'draft too large');fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600);primary=None
 def choose(a,b):
  fatal=lambda e:e is not None and (not isinstance(e,Exception) or isinstance(e,(MemoryError,RecursionError)))
  return a if fatal(a) else b if fatal(b) or a is None else a
 try:
  view=memoryview(raw)
  while view:
   n=os.write(fd,view);require(n>0,'short draft write');view=view[n:]
  os.fsync(fd)
 except BaseException as error:primary=choose(primary,error)
 try:os.close(fd)
 except BaseException as error:primary=choose(primary,error)
 if primary is not None:raise primary
 parent=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW);primary=None
 try:os.fsync(parent)
 except BaseException as error:primary=choose(primary,error)
 try:os.close(parent)
 except BaseException as error:primary=choose(primary,error)
 if primary is not None:raise primary

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--request',required=True);parser.add_argument('--charter');parser.add_argument('--history');parser.add_argument('--output',required=True);a=parser.parse_args();root=Path(a.root)
 request=json.loads(body(root,a.request));output=new_path(root,a.output)
 if request.get('phase')=='materialize':
  require(a.charter is not None and a.history is not None,'materialization charter/history references required')
  value=render(root,request,json.loads(body(root,a.charter)),json.loads(body(root,a.history)));write_exclusive(output,canonical(value)+b'\n')
 else:
  require(a.charter is None and a.history is None,'comparison uses authenticated original history and frozen charter template')
  result=prepare_compare(root,request);require(a.output not in result['files'],'gate template cannot overlap B files')
  require(all((root/name).parent.is_dir() for name in result['files']) and output.parent.is_dir(),'root must prepare real output directories')
  # Retain any partial writing failure. Never retry or label an incomplete draft complete.
  for name,raw in result['files'].items():write_exclusive(root/name,raw)
  write_exclusive(output,canonical(result['gate_template'])+b'\n')
 print(json.dumps({'status':'unregistered-draft','phase':request['phase'],'output':a.output,'execution_authorized':False}))
if __name__=='__main__':main()
