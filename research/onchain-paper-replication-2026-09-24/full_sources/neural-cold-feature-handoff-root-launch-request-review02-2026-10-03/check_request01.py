"""Independent exact prospective request/capsule checks; no admission or jobs."""
import ast,datetime,hashlib,importlib.util,json,os,pathlib,shutil,stat,subprocess,sys,types
P=pathlib.Path(__file__).resolve().parent;BASE=P.parent;REPO=P.parents[3];Q=BASE/'neural-cold-feature-handoff-root-launch-request02-2026-10-03'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(pathlib.Path(p).read_bytes())
def ref(r):
 p=pathlib.Path(r['path']);b=p.read_bytes();assert sha(b)==r['sha256'];return b
assert sha((Q/'MATERIALIZE_REQUEST02.json').read_bytes())=='ef024344fba338a34208686ef55f64a784a68571d0194d0e5a14040daa067836'
q=read(Q/'MATERIALIZE_REQUEST02.json');cmd=read(Q/'EXACT_COMMAND02.json');assert sha((Q/'EXACT_COMMAND02.json').read_bytes())=='3f20df217e73eb249140687d755ed984c41a0029e868cfcc3ffc544ec16814ac'
assert cmd['request']['sha256']==sha((Q/'MATERIALIZE_REQUEST02.json').read_bytes())
for r in [q[k] for k in ('identity_baseline','inventory','recovery','release')]+list(q['reviews'].values())+[cmd['launcher'],cmd['launcher_review'],cmd['request']]:ref(r)
assert set(q['reviews'])=={'composition','recovery','registration','release','withdrawal'}
root=pathlib.Path(q['capsule']);output=pathlib.Path(q['output_parent']);identity='compact-cold-inputs-20261003-01';otherid='compact-cold-comparison-20261003-01'
assert q['phase']=='materialize' and q['source']=='9742c6ec817dd0917f9f35a52e4b83965ca1cd29'
assert str(output)=='/home/malecada/master_thesis/onchain-fixture-isolation/compact-cold-root-launches-20261003'==cmd['selected_once_global_output_parent']
assert output.is_dir() and not list(output.iterdir())
expected=[str(REPO/'.venv/bin/python'),'-B',cmd['launcher']['path'],'--request',str(Q/'MATERIALIZE_REQUEST02.json'),'--request-sha256',sha((Q/'MATERIALIZE_REQUEST02.json').read_bytes())]
assert cmd['argv']==expected and cmd['cwd']==str(root) and cmd['allowed_identity']==identity and cmd['automatic_retry'] is False
# Only safe helper calls, never validate/execute or check_release.
s=importlib.util.spec_from_file_location('actual_launcher02_request_checks',cmd['launcher']['path']);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.request_shape(q)
recovery=m.recovery(q,root);assert recovery['members']==733 and recovery['logical_bytes']==5107186
idx=read(q['recovery']['path']);restored=pathlib.Path(idx['recovered_root']);assert idx['source']==q['source']
ret=read(BASE/'neural-cold-feature-handoff-root-integration02-2026-10-03/FINAL_CAPSULE_RETENTION02.json')
expectedindex=[]
for r in ret['members']:
 if r['path']=='.':continue
 expectedindex.append({k:r[k] for k in (('path','kind') if r['kind']=='directory' else ('path','kind','sha256','bytes'))})
assert expectedindex==idx['members'] and ret['member_count']==734
for base in (root,restored):
 for r in ret['members']:
  p=base/r['path'];s=p.lstat();assert stat.S_IMODE(s.st_mode)==r['mode']
  if r['kind']=='directory':assert stat.S_ISDIR(s.st_mode)
  else:assert stat.S_ISREG(s.st_mode) and s.st_nlink==1 and s.st_size==r['bytes'] and sha(p.read_bytes())==r['sha256']
# Immutable actual Git chain/source joins; no network or mutation.
env=dict(os.environ,GIT_NO_LAZY_FETCH='1',GIT_TERMINAL_PROMPT='0',GIT_OPTIONAL_LOCKS='0',GIT_NO_REPLACE_OBJECTS='1')
def git(base,*args):return subprocess.check_output(['git','-c','protocol.allow=never',*args],cwd=base,env=env,stderr=subprocess.PIPE,timeout=10)
S='fb9fad1d93836b4f92f2be8111da4adf22b7e069';T='095fd51e4d65318f4ee92de9873edf98cbee6c9b'
for base in (root,restored):
 assert git(base,'rev-parse','HEAD').decode().strip()==q['source']
 for c,parents in ((q['source'],[T]),(T,[S]),(S,[])):assert git(base,'show','-s','--format=%P',c).decode().strip().split()==parents
 for name in ('.git/objects/info/alternates','.git/info/grafts','.git/shallow'):assert not os.path.lexists(base/name)
 assert not git(base,'for-each-ref','refs/replace').strip()
 assert not git(base,'ls-files','cold_release/materialize02/released-envelope02.json').strip()
inv=read(q['inventory']['path']);sources={}
for r in inv['source_inventory']:
 b=(root/r['target']).read_bytes();assert len(b)==r['bytes'] and sha(b)==r['sha256'] and git(root,'show',q['source']+':'+r['target'])==b;sources[r['target']]=r['sha256']
assert len(sources)==195 and sum(n.startswith('tradingagents/') for n in sources)==147
release=read(q['release']['path']);docs={}
for k in ('registration','sources','runtime','native_environment','phase_contract'):
 r=release[k];b=(root/r['path']).read_bytes();assert set(r)=={'path','sha256','bytes','kind'} and len(b)==r['bytes'] and sha(b)==r['sha256'];assert git(root,'show',q['source']+':'+r['path'])==b;docs[k]=json.loads(b)
assert release['status']=='released' and release['remaining']==[] and release['phase']=='materialize' and release['prior_materialization'] is None and release['cpus']==[0,1]
reg=docs['registration'];assert set(reg['experiments'])=={identity};experiment=reg['experiments'][identity];family=reg['families'][experiment['family']];assert family['attempt_budget']==2 and family['prior_attempts']==0
assert reg['datasets']['synthetic-cold']['exposures']==[] and experiment['parent'] is None and experiment['cells']==['cold-input-materialization'] and experiment['outputs']==['proof-materialize.json']
assert docs['sources']['files']==sources==experiment['source_files'];contract=docs['phase_contract'];assert contract['experiment']==experiment and contract['family']==family and contract['identity']==identity
assert len(experiment['inputs'])==9
inputs={}
for k,r in experiment['inputs'].items():
 b=(root/r['path']).read_bytes();assert sha(b)==r['sha256'] and git(root,'show',q['source']+':'+r['path'])==b;inputs[k]=json.loads(b)
anchor=inputs['anchor'];assert anchor['commit']==S and len(anchor['files'])==147
jobsrc=root/'tradingagents/research/onchain_replication/job.py';tree=ast.parse(jobsrc.read_bytes());names={'required_sources','_command'};nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
ns={'Path':pathlib.Path,'__file__':str(jobsrc),'sys':sys,'MODULE':'tradingagents.research.onchain_replication.job'};exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-pure-command-and-inventory','exec'),ns)
assert ns['required_sources']()==set(anchor['files'])
for path,h in anchor['files'].items():assert h==sha((root/path).read_bytes())==sha(git(root,'show',S+':'+path))
args=types.SimpleNamespace(root=root,registration=release['registration']['path'],experiment=identity,source=q['source']);commands={mode:ns['_command'](args,mode) for mode in ('launch','worker')}
job=inputs['execution_job'];assert job['resources']==inputs['future_resources'] and job['payload']=={'cold_proof_input':'cold_proof','representation_jobs':{}}
policy=job['resources'];GIB=1024**3
assert policy['memory_max_bytes']==policy['memory_high_bytes']==3*GIB and policy['reserve_bytes']==3*GIB and policy['start_reserve_bytes']==6*GIB and policy['wall_seconds']==1800 and policy['native_unit_limits']=={'file_size_bytes':4194304} and policy['disk_floor_bytes']==10*GIB and policy['disk_paths']==[str(root)]
assert policy['storage_budget']=={'root':str(root),'limits':{'max_allocated_bytes':GIB,'max_logical_bytes':GIB,'max_entries':32768,'max_depth':32,'max_scan_seconds':5}}
rsrc=root/'tradingagents/research/onchain_replication/resources.py';rnode=next(n for n in ast.parse(rsrc.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name=='_native_owned_env');rn={'Path':pathlib.Path};exec(compile(ast.Module(body=[rnode],type_ignores=[]),'native-map-only','exec'),rn);assert rn['_native_owned_env'](root)==docs['native_environment'] and docs['native_environment']!=inputs['environment']
# Actual pinned runtime checker is stdlib-only, no research module import.
rt=docs['runtime'];assert len(rt['distribution_records'])==len({x['name'] for x in rt['distribution_records']})==251
cwd=pathlib.Path.cwd()
try:
 os.chdir(root);spec=importlib.util.spec_from_file_location('request_review_runtime',root/'proof_tools/runtime_gate01.py');runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime);runtime_readback=runtime.check(root,rt)
finally:os.chdir(cwd)
NS=m.NS;absent=[]
for base in [pathlib.Path(q['old_roots'][0]['root']),root,REPO]:
 for i in (identity,otherid):
  for n in NS:
   p=base/n/i;assert not os.path.lexists(p);absent.append(str(p))
assert read(Q/'PREPARATION_BASELINE02.json')['all30_paths_absent']==absent
for old in q['old_roots']:
 ref(old['baseline']);ref(old['withdrawal']);assert git(pathlib.Path(old['root']),'rev-parse','HEAD').decode().strip()==old['source']=='6ab2bf29f0a31c5465e9b4abc8bfbf97d1dd341e'
assert read(q['identity_baseline']['path'])=={'schema_version':1,'root':str(root),'source':q['source'],'phase':'materialize','absent_namespace_paths':[str(root/n/identity) for n in NS],'known_processes':q['known_processes']}
assert len(q['known_processes'])==12 and all(not pathlib.Path('/proc',str(pid)).exists() for pid in q['known_processes'])
assert not any(n.split('.')[0] in {'numpy','torch','scipy','tradingagents'} for n in sys.modules)
result={'status':'passed-prospective-request-and-capsule-metadata-only','observed_at':datetime.datetime.now(datetime.UTC).isoformat(),'request_sha256':sha((Q/'MATERIALIZE_REQUEST02.json').read_bytes()),'command_sha256':sha((Q/'EXACT_COMMAND02.json').read_bytes()),'source_A2':q['source'],'anchor_S2':S,'metadata_T2':T,'source_pins':195,'anchor_pins':147,'inputs':9,'runtime_RECORDs_checked':251,'runtime_package_origins':len(runtime_readback['module_origins']),'full_recovery_nonroot_rows':733,'full_retained_members':734,'files':508,'directories_including_root':226,'logical_bytes':5107186,'installed_envelope_SHA':q['release']['sha256'],'old_main_new_namespace_absences':len(absent),'known_PIDs_absent':q['known_processes'],'fixed_global_output_parent':str(output),'extracted_actual_job_commands_NOT_EXECUTED':commands,'full_check_release_or_admit_called':False,'numerical_imports':False,'parent_wait_wrapper_review_pending':True}
with (P/'REQUEST_READBACK01.json').open('x') as out:json.dump(result,out,indent=2);out.write('\n')
print(json.dumps(result,indent=2))
