"""Pinned prior execution expectation, never a current Torch/CUDA observation."""
import argparse,ast,importlib.metadata,json,os,platform,shutil
from pathlib import Path
import recovery04 as R
from bounded_git01 import git
H=Path(__file__).resolve().parent
BASE=H.parent
CURRENT=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-native-20261003-01/source')
CURRENT_SOURCE='44bf99d199acae5a043cf5b472a53e2fcf4caf1b'
OLD=Path('/home/malecada/master_thesis/onchain-fixture-isolation/held-score-consumer-native-20261003-07/source')
OLD_SOURCE='d443208795f59292c156c5b81b687594efacea4d'
FLAT=BASE/'held-consumer-post-outcome-root-flat-recovery01-2026-10-03/flat01'
META_SHA='d8b81554205b9eeb5523fbed41ba616ffc79a0b7fb78c6779b2bcee7f4844fdb'
EXPECTED_PATH='fixture_inputs/held/success01/environment.json'
EXPECTED_SHA='1ff7418a2b7c77300aea731cea5bba78277d323241ac0ec59f41f43207c66d87'
CLAIM_PATH='research_runs/original-import-held-success-20261003-01/claim.json'
CLAIM_SHA='d998a80d0178a4e46bf97ac863611ad3b1794d2b2e74e3048c4704f397f8b4ba'
REG='held-fixture-registration01.json'
JOB='tradingagents/research/onchain_replication/job.py'
ENV='tradingagents/research/onchain_replication/environment.py'
BASIC={'python','cpu_count','lock_sha256','packages'}
ALL=BASIC|{'torch_version','cuda_build','cuda_available'}

def expected_check(raw,basic):
 value=json.loads(raw)
 R.require(type(value) is dict and set(value)==ALL and set(basic)==BASIC,'exact environment schema')
 R.require(type(value['cuda_available']) is bool and type(value['torch_version']) is str and (value['cuda_build'] is None or type(value['cuda_build']) is str),'prior API expectation types')
 R.require(type(value['cpu_count']) is int and value['cpu_count']>0 and type(value['python']) is str,'prior basic types')
 R.require({k:value[k] for k in BASIC}==basic,'current directly observed basic fields differ from prior expectation')
 return value

def read_flat(meta,name):
 row=next(r for r in meta['manifest']['members'] if r['path']==name)
 raw=R.read(FLAT,meta['flat_members'][name]);R.require(row['kind']=='file' and len(raw)==row['bytes'] and R.digest(raw)==row['sha256'],'actual recovered member differs')
 return raw

def ordering(raw):
 tree=ast.parse(raw);fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='worker')
 contexts=[n for n in ast.walk(fn) if isinstance(n,ast.With) and any('ResearchRun.start' in ast.unparse(i.context_expr) for i in n.items)]
 R.require(len(contexts)==1,'one genuine lifecycle context');body=contexts[0].body
 R.require(isinstance(body[0],ast.ImportFrom) and body[0].module=='environment','inventory import directly inside claim')
 condition=body[1];R.require(isinstance(condition,ast.If) and isinstance(condition.body[0],ast.Raise),'immediate environment mismatch refusal')
 text=ast.unparse(condition)
 R.require('inventory(root, include_torch=' in text and "json.loads(run.read_input(job['environment_input']))" in text and 'registered execution environment differs' in text,'exact actual-vs-registered check')
 R.require("'financial_wrapper'" in text or "'compact_resource'" in text,'Torch enabled selected job kinds')
 return {'claim_context_line':contexts[0].lineno,'comparison_line':condition.lineno,'actual_inventory_after_claim':True,'mismatch_spends_attempt':True,'comparison_source':text}

def prepare():
 out=H/'prepared01';R.require(not os.path.lexists(out),'one-use output reserved');R.require(shutil.disk_usage(H).free>=R.FLOOR,'10GiBfloor')
 R.require(git(CURRENT,['rev-parse','HEAD'],cap=128).decode().strip()==CURRENT_SOURCE,'fixed observed current source')
 meta_raw=R.read(FLAT,'capsule-metadata.json');R.require(R.digest(meta_raw)==META_SHA,'actual recovered metadata pin');meta=json.loads(meta_raw)
 raw=read_flat(meta,EXPECTED_PATH);R.require(R.digest(raw)==EXPECTED_SHA,'registered expectation pin')
 claim_raw=read_flat(meta,CLAIM_PATH);R.require(R.digest(claim_raw)==CLAIM_SHA,'actual original claim pin');claim=json.loads(claim_raw)
 desc={'dataset':'synthetic','path':EXPECTED_PATH,'sha256':EXPECTED_SHA}
 R.require(claim['source']==claim['design_source']==OLD_SOURCE and claim['experiment_id']=='original-import-held-success-20261003-01' and claim['inputs']['environment']==claim['experiment']['inputs']['environment']==desc,'genuine claim environment/source join')
 reg_raw=read_flat(meta,REG);R.require(R.digest(reg_raw)==claim['registration_sha256'],'original registration pin');reg=json.loads(reg_raw)
 R.require(reg['experiments'][claim['experiment_id']]==claim['experiment'],'original selected registration exact')
 R.require(git(OLD,['show',OLD_SOURCE+':'+REG])==reg_raw and git(OLD,['show',OLD_SOURCE+':'+EXPECTED_PATH])==raw,'actual original committed registration and expectation bodies')
 failed_raw=read_flat(meta,CLAIM_PATH.replace('claim.json','failed.json'));failed=json.loads(failed_raw)
 R.require(failed['claim_sha256']==CLAIM_SHA and failed['experiment_id']==claim['experiment_id'] and failed['status']=='failed','preserve actual original FAILED')
 oldjob=read_flat(meta,JOB);oldenv=read_flat(meta,ENV)
 for name,body in ((JOB,oldjob),(ENV,oldenv)):
  R.require(claim['experiment']['source_files'][name]==R.digest(body) and git(OLD,['show',OLD_SOURCE+':'+name])==body,'actual old admitted code join')
 currentjob=R.read(CURRENT,JOB);currentenv=R.read(CURRENT,ENV)
 for name,body in ((JOB,currentjob),(ENV,currentenv)):
  R.require(git(CURRENT,['show',CURRENT_SOURCE+':'+name])==body,'current exact committed code')
 R.require(currentenv==oldenv,'same original inventory implementation')
 oldorder=ordering(oldjob);neworder=ordering(currentjob)
 # These are actual current basic API observations; no Torch package import.
 basic={'python':platform.python_version(),'cpu_count':os.cpu_count(),'lock_sha256':R.digest(R.read(CURRENT,'uv.lock')),'packages':{p:importlib.metadata.version(p) for p in ('numpy','scipy','pyarrow','torch','scikit-learn')}}
 expected=expected_check(raw,basic)
 R.require(git(CURRENT,['rev-parse','HEAD'],cap=128).decode().strip()==CURRENT_SOURCE,'current source changed')
 out.mkdir(mode=0o700)
 for name,body in [('environment.EXPECTATION.json',raw),('historical-claim.json',claim_raw),('historical-failed.json',failed_raw),('historical-registration.json',reg_raw),('historical-job.py',oldjob),('inventory.py',currentenv),('current-job.py',currentjob)]:
  with R.new_file(out/name) as fd:sink=R.Sink(fd);sink.write(body);os.fsync(fd)
  R.require(R.read(out,name)==body,'preserved body readback')
 result={'status':'EXPECTATION_PREPARATION_ONLY_NOT_RELEASED','current_source_observed':CURRENT_SOURCE,'historical_source':OLD_SOURCE,'historical_environment_sha256':EXPECTED_SHA,'historical_claim_sha256':CLAIM_SHA,'historical_failed_sha256':R.digest(failed_raw),'recovered_metadata_sha256':META_SHA,'current_basic_observations':basic,'historical_expected_values':expected,'current_torch_api_observed':False,'driver_unchanged_claim':False,'current_environment_equality_proven':False,'old_order':oldorder,'current_order':neworder,'input_adoption':None,'registration':None,'cumulative_authority':None,'phase_slots_unreserved':18,'paper_fit_credit':0,'next_root_action':'Independently review and adopt exact expectation body SHA1ff7418a as separately hashed environment input; keep historical null draft unchanged. Freeze exact new source/input registration/cumulative/release. Actual worker compares full inventory inside genuine guard AFTER claim; mismatch closes spent FAILED, never replay same identity.'}
 R.put(out/'EVIDENCE01.json',result);R.require(shutil.disk_usage(out).free>=R.FLOOR,'final10GiBfloor');return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--prepare',action='store_true');p.add_argument('--release',action='store_true');a=p.parse_args()
 R.require(not a.release,'expectation preparation cannot release a job');R.require(a.prepare,'explicit prepare only');result=prepare();print(json.dumps({'status':result['status'],'expectation_sha256':EXPECTED_SHA,'current_torch_api_observed':False}))
