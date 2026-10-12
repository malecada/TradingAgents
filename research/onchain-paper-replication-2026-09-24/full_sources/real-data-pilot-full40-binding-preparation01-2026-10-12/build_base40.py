"""Finite Root40 public metadata preparation; no binding, admission or claim."""
import argparse,ast,copy,difflib,hashlib,json,subprocess
from pathlib import Path
R=Path.cwd().resolve();D=Path(__file__).resolve().parent;F=D.parent
OLD=F/'real-data-pilot-full39-binding-preparation01-2026-10-12'
PREFIX=F/'pilot40-prefix-inputs-2026-10-12'
NAME='eth-paper-real-data-end-to-end-resource-20261012-40'
def raw(v):return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def ref(p):
 b=p.read_bytes();return {'path':str(p.relative_to(R)),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)}
def load(p):return json.loads(p.read_bytes())
def save(p,v):
 with p.open('xb') as h:h.write(raw(v))
def build(anchor):
 assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==anchor
 assert not (D/'public01').exists() and not (R/'research_runs'/NAME).exists()
 p=R/'tradingagents/research/onchain_replication/job.py'
 f=next(n for n in ast.parse(p.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='required_sources')
 env={'Path':Path,'__file__':str(p)};exec(compile(ast.Module(body=[f],type_ignores=[]),str(p),'exec'),env)
 files={n:ref(R/n)['sha256'] for n in sorted(env['required_sources']())};assert len(files)==206
 queries='\n'.join(anchor+':'+n for n in files)+'\n'
 returned=subprocess.check_output(['git','cat-file','--batch'],input=queries.encode());offset=0
 for n,digest in files.items():
  end=returned.index(b'\n',offset);fields=returned[offset:end].split();assert fields[1]==b'blob'
  size=int(fields[2]);offset=end+1;b=returned[offset:offset+size];offset+=size
  assert returned[offset:offset+1]==b'\n';offset+=1
  assert b==(R/n).read_bytes() and hashlib.sha256(b).hexdigest()==digest
 assert offset==len(returned)
 docs={p.stem:load(p) for p in (OLD/'public01').glob('*.json')};assert len(docs)==12
 baseline=copy.deepcopy(docs)
 assert docs['archive_transport']['connection'] is None and docs['archive_policy']['transport_identity'] is None
 docs['pair_policy']['numerical_source']={'commit':anchor,'files':files}
 docs['mcm_policy']['batched']['continuation']['graph_manifest_inputs']={'0114d61904938208c75497bdabe82c5dae32b7d2110a4e460d1942f84dc473ba':'cont39_manifest'}
 assert docs['mcm_policy']['batched']['continuation']['manifest_input'] is None
 docs['archive_policy']['remote_namespace']='ethpilot-20261012-40';docs['archive_transport']['namespace']='ethpilot-20261012-40'
 for resources in (docs['execution_job']['resources'],docs['pilot']['resource_policy']):
  assert resources['storage_budget']['experiment']=='eth-paper-real-data-end-to-end-resource-20261012-39'
  resources['storage_budget']['experiment']=NAME
  resources['storage_budget']['roots'][1]=str(R/'research_runs'/NAME)
 assert docs['execution_job']['resources']==docs['pilot']['resource_policy']
 docs['pilot']['cell_id']='real-eth-whole-seven-graph-joint-pilot-resource40'
 docs['pilot']['weekly_graph_digest_pin']=True
 docs['pilot']['partial_progress']={'schema_version':1,'interval_seconds':60,'max_records':1024}
 for value in (docs['execution_job']['payload']['representation_jobs']['original32'],docs['producer_plan']['producers']['original32']):
  for role,key in [('pair_policy','pair_execution'),('archive_policy','compact_archive_execution')]:value['descriptor'][key]['policy_sha256']=hashlib.sha256(raw(docs[role])).hexdigest()
 for role in ('compact_policy','original_import','resource_population_plan','mcm_output_policy','typed_payload'):assert docs[role]==baseline[role]
 for k in ('decisions','graph_inputs','graph_sequences','batch_size','seed','lookback_days','model_execution','model_input','training_input','indices'):assert docs['pilot'][k]==baseline['pilot'][k]
 (D/'public01').mkdir()
 for role,v in docs.items():save(D/'public01'/(role+'.json'),v)
 prepared=load(OLD/'PREPARED01.json');prepared['builder03_result']['inputs']={k:v for k,v in docs.items() if k!='archive_policy'}
 prepared['builder03_spec']['references']['archive_policy']=ref(D/'public01/archive_policy.json');save(D/'PREPARED01.json',prepared)
 request=load(OLD/'REQUEST01.json');request.update(prepared=ref(D/'PREPARED01.json'),archive_policy=ref(D/'public01/archive_policy.json'),private_parent='research_artifacts/real_pilot_runtime/pilot-transport-20261012-40-01');save(D/'REQUEST01.json',request)
 refs=load(OLD/'PUBLIC_INPUT_REFS_DRAFT01.json');assert len(refs)==72 and 'archive_transport' not in refs
 for role in docs:
  if role!='archive_transport':
   p=ref(D/'public01'/(role+'.json'));refs[role].update(path=p['path'],sha256=p['sha256'])
 for role,p in load(PREFIX/'REGISTERED_ROLE_MAP.json').items():
  assert role not in refs;refs[role]={'dataset':'eth','path':p['path'],'sha256':p['sha256']}
 assert len(refs)==199
 for role,name in (('cont39_recovery_score','RECOVERED_SCORE_SCOPE01.json'),('cont39_recovery_numeric','RECOVERED_NUMERIC_SCOPE01.json')):
  p=ref(PREFIX/name);refs[role]={'dataset':'eth','path':p['path'],'sha256':p['sha256']}
 assert len(refs)==201;save(D/'BASE_PUBLIC_INPUT_REFS01.json',refs)
 before=(OLD/'bind_actual01.py').read_text();after=before.replace('20261012-39','20261012-40').replace('len(refs)==73','len(refs)==204');ast.parse(after)
 (D/'bind_actual01.py').write_text(after)
 (D/'BINDER_ADAPTATION01.diff').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=str(OLD/'bind_actual01.py'),tofile=str(D/'bind_actual01.py'))))
 save(D/'BASE_PREPARATION01.json',{'status':'DRAFT_NOT_RELEASED','source_anchor':anchor,'source_bodies':206,'base_roles':201,'missing_roles':['cont39_manifest','cont39_review'],'complete_public_roles':203,'bound_roles':204,'actual_git_batch_exit':0,'actual_git_batch_sha256':hashlib.sha256(returned).hexdigest(),'fixed_identity':NAME,'claim':False,'binder_executed':False})
 print(json.dumps({'status':'DRAFT_NOT_RELEASED','source_bodies':206,'base_roles':201,'missing_roles':2,'claim':False}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--anchor',required=True);build(p.parse_args().anchor)
