import ast,copy,hashlib,json,os,re,stat,resource,signal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
H=Path(__file__).resolve().parent;R=H.parents[3];F=H.parent;C=F/'mcm-batched-accelerated-integration01-2026-10-09';O=F/'mcm-batched-owner-integration03-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((C/'MANIFEST01.json').read_text());assert all(sha(C/n)==v for n,v in m.items());pins=json.loads((C/'PACKAGE_SOURCES01.json').read_text());assert len(pins)==13
for n,v in pins.items():assert sha(R/v['source'])==v['sha256'] and v['destination']=='tradingagents/research/onchain_replication/'+n
# Reuse independently tested hunk inversion, operate only in memory.
helper=F/'mcm-batched-owner-integration-review03-2026-10-09/source05.py';node=next(n for n in ast.parse(helper.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='apply');ns={'re':re};exec(compile(ast.Module(body=[node],type_ignores=[]),str(helper),'exec'),ns)
assert ns['apply']((O/'compact_mcm_batched.py').read_text(),(C/'compact_mcm_batched.py.patch').read_text())==(C/'compact_mcm_batched.py').read_text()
base=(F/'mcm-batched-owner-integration02-2026-10-09/compact_mcm.py').read_text();assert base.replace("policy['schema_version'] in (1,2,4)","policy['schema_version'] in (1,2,5)")==(C/'compact_mcm.py').read_text()
source=ast.parse((C/'compact_mcm_batched.py').read_text());functions={n.name:n for n in ast.walk(source) if isinstance(n,ast.FunctionDef)}
def require(ok,message):
 if not ok:raise ValueError(message)
ns={'require':require,'FORMAT':'ordered-mcm-batch-closure-v2','os':os,'stat':stat};exec(compile(ast.Module(body=[functions[n] for n in ('selected','validate','_children')],type_ignores=[]),'actual_adapter_functions','exec'),ns)
# Build the author's exact finite policy literal, without executing its fixture.
t=ast.parse((C/'verify03.py').read_text());env={'m':type('Metadata',(),{'FORMAT':ns['FORMAT']})()}
for n in t.body:
 if isinstance(n,ast.Assign) and any(isinstance(x,ast.Name) and x.id in ('execution','policy') for x in n.targets):exec(compile(ast.Module(body=[n],type_ignores=[]),'policy_literal','exec'),env)
p=env['policy'];assert ns['validate'](p,64)==p['batched'];checks=['valid_schema5']
for schema in (1,2,3,4,True,'5'):
 q=copy.deepcopy(p);q['schema_version']=schema
 try:ns['validate'](q,64)
 except ValueError:checks.append('refuse_schema_'+repr(schema))
 else:raise AssertionError('wrong schema accepted')
for key,value in [('max_origin_bytes',575),('max_summary_bytes',0),('max_entries',True),('max_retained_bytes',1023),('max_key_bytes',16385)]:
 q=copy.deepcopy(p);q['batched']['execution'][key]=value
 try:ns['validate'](q,64)
 except ValueError:checks.append('refuse_'+key)
 else:raise AssertionError('bad allowance accepted')
root=H/'children';root.mkdir();(root/'numeric-batches').mkdir();(root/'scores.f32').write_bytes(b'');ns['_children'](root,{'numeric-batches','scores.f32'},directories={'numeric-batches'})
try:ns['_children'](root,{'numeric-batches','scores.f32'})
except ValueError:checks.append('legacy_file_only_children_unchanged')
else:raise AssertionError('directory accepted as file')
(root/'numeric-batches').rmdir();(root/'numeric-batches').symlink_to(root)
try:ns['_children'](root,{'numeric-batches','scores.f32'},directories={'numeric-batches'})
except ValueError:checks.append('numeric_directory_symlink_refused')
else:raise AssertionError('redirect accepted')
# Changed caller structure retains the same original task/sink/checkpoint bodies.
old={n.name:n for n in ast.walk(ast.parse((O/'compact_mcm_batched.py').read_text())) if isinstance(n,ast.FunctionDef)}
for name in ('checkpoint','execute','sink','post_batch','consume','final_batches','stage_content','output_source','output_chunks'):
 assert ast.dump(old[name])==ast.dump(functions[name])
mods=ast.unparse(functions['_modules']);assert "'matching_immutable_session'" in mods
compute=ast.unparse(functions['_compute']);assert compute.index('executor.finish()')<compute.index('numeric_execution\': numeric_binding') and 'actions.append(executor.close)' in compute
verify=ast.unparse(functions['verify_content']);assert "modules['numeric_execution'].verify" in verify and "numeric['cells'] == binding['cells']" in verify
prod=ast.unparse(functions['produce']);assert "b['execution']['max_origin_bytes'] + b['execution']['max_summary_bytes']" in prod
# Inspect exact BNE ordering, never release or exercise its withheld cleanup.
bne=ast.parse((R/pins['batched_numeric_execution.py']['source']).read_text());bf={n.name:n for n in ast.walk(bne) if isinstance(n,ast.FunctionDef)}
call=ast.unparse(bf['__call__']);complete=ast.unparse(bf['_complete_batch']);assert call.index('self.memo.begin_batch()')<call.index('self.memo(a, b, purpose)');assert complete.index('self.memo.end_batch()')<complete.index('summary =')<complete.index('write_all(')
r={'decision':'accepted_caller_only','manifest_sha256':sha(C/'MANIFEST01.json'),'package_sources_sha256':sha(C/'PACKAGE_SOURCES01.json'),'source_pins':pins,'checks':checks,'numeric_execution_callee_released':False,'blocked_callee_sha256':pins['batched_numeric_execution.py']['sha256'],'default_compact_mcm_inverse':True,'original_task_sink_checkpoint_arithmetic_bodies_unchanged':True,'genuine_authority':False,'numerical_imports':False,'benchmark':False}
(H/'RESULT01.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r))
