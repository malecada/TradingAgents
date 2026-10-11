import ast, copy, difflib, hashlib, json, os, resource, signal, types
from pathlib import Path
os.sched_setaffinity(0,{3});os.nice(10)
resource.setrlimit(resource.RLIMIT_CPU,(10,10));resource.setrlimit(resource.RLIMIT_AS,(512*1024**2,512*1024**2));resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,4*1024**2));signal.alarm(20)
P=Path(__file__).resolve().parent;F=P.parent;R=F.parents[2]
D=F/'matching-compiled-uncached-edge-caller-candidate02-2026-10-11';L=F/'matching-compiled-uncached-edge-caller-candidate01-2026-10-11'
checks=[];refs={}
def read(p):
    assert not ({'.git','.venv','research_artifacts','research_runs','keys','apis'}&set(p.parts)) and p.suffix!='.so'
    b=p.read_bytes();assert len(b)<2*1024**2;refs[str(p.relative_to(R))]={'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)};return b.decode()
def ck(ok,name):
    checks.append({'name':name,'pass':bool(ok)})
    if not ok:raise AssertionError(name)
def refused(call,name):
    try:call()
    except ValueError:ck(True,name)
    else:ck(False,name)
def extract(source,names,ns):
    nodes=[n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name in names]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'extracted-stdlib-only','exec'),ns)
manifest=read(D/'MANIFEST02.json');ck(hashlib.sha256(manifest.encode()).hexdigest()=='77cbfb67bff4346ae4fb35e5d07d750ff7db23ee7bf337a55cd61adcf1636818','exact upper manifest')
for name,row in json.loads(manifest)['files'].items():
    read(D/name);ck(refs[str((D/name).relative_to(R))]==row,'frozen textual member '+name)
requirements=json.loads(read(D/'SOURCE_REQUIREMENTS01.json'))
ck(len(requirements)==10,'ten source requirements')
for relative,row in requirements.items():
    read(D/Path(relative).name);ck(refs[str((D/Path(relative).name).relative_to(R))]==row,'source requirement '+Path(relative).name)
for name,pin in json.loads(read(D/'BASELINES01.json')).items():
    before=read(R/'tradingagents/research/onchain_replication'/name);after=read(D/name)
    ck(hashlib.sha256(before.encode()).hexdigest()==pin,'current frozen baseline '+name)
    ck(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile=name,tofile=name))==read(D/(name+'.patch')),'exact forward diff '+name)
    ck(''.join(difflib.unified_diff(after.splitlines(True),before.splitlines(True),fromfile=name,tofile=name))==read(D/(name+'.inverse.patch')),'exact inverse diff '+name)
ck(hashlib.sha256(read(P/'LOWER_OBSERVATIONS01.json').encode()).hexdigest()=='2ed7350f93720e5f47820f50e71816e59db2f0b898e4051d68cb708dab5cdc85','reuse frozen lower observations without rerun')
owner=read(D/'compiled_edge_owner.py');lower=read(L/'compiled_edge_owner.py')
tree=ast.parse(owner);new={'attach','current_policy','options','join'}
without=ast.Module(body=[n for n in tree.body if not(isinstance(n,ast.FunctionDef) and n.name in new)],type_ignores=[])
ck(ast.dump(without)==ast.dump(ast.parse(lower)),'lower owner unchanged except four policy functions')
for name in ('edge_chunk_adapter.py','matching_annealing.py','matching_checkpoint.py'):
    ck(read(D/name)==read(L/name),'unchanged reviewed lower '+name)
nodes=[n for n in tree.body if isinstance(n,ast.Assign) or isinstance(n,ast.FunctionDef) and n.name in new|{'require','freeze'}]
ns={'Path':Path};exec(compile(ast.Module(body=nodes,type_ignores=[]),'policy-only','exec'),ns)
policy={'format':ns['FORMAT'],'source_sha256':ns['SOURCE'],'adapter_sha256':ns['ADAPTER'],'library_sha256':ns['LIBRARY'],'runtime_sha256':'1'*64,'abi_sha256':'2'*64,'runtime_bytes':345,'abi_bytes':200}
for role in ('source','adapter','library','runtime','abi'):policy[role+'_path']='/synthetic/'+role
a=types.SimpleNamespace();b=types.SimpleNamespace();ns['attach'](a,policy);ns['attach'](b,policy);ns['join'](a,b)
opts=ns['options'](a);opts['compiled_edge_policy_value']['runtime_bytes']=346
ck(dict(a._compiled_edge_policy)['runtime_bytes']==345,'options fresh dictionary cannot mutate parent policy')
b._compiled_edge_policy=tuple(list(b._compiled_edge_policy));refused(lambda:ns['join'](a,b),'equal policy replacement refused by identity')
ns['attach'](b,dict(policy,runtime_bytes=346));refused(lambda:ns['join'](a,b),'child policy content divergence refused')
ns['attach'](b,None);ck(ns['options'](b)=={},'default has no selected keyword')
compact=read(D/'compact_mcm_batched.py');sel={'compiled_edge_owner':types.SimpleNamespace(**ns),'require':ns['require']}
extract(compact,{'_edge_policy'},sel);roles=dict(zip(('source','adapter','library','runtime','abi'),('edge_source','edge_adapter','edge_library','edge_runtime','edge_abi')))
selection={'compiled_edge_policy':policy,'compiled_edge_inputs':roles}
ck(sel['_edge_policy'](selection)==a._compiled_edge_policy and sel['_edge_policy']({}) is None,'exact five roles and omission accepted')
for label,value in [('orphan',{'compiled_edge_inputs':roles}),('missing',{'compiled_edge_policy':policy}),('duplicate',dict(selection,compiled_edge_inputs=dict(roles,abi='edge_runtime'))),('environment',dict(selection,compiled_edge_inputs=dict(roles,abi='environment'))),('extra',dict(selection,compiled_edge_inputs=dict(roles,extra='extra')))]:
    refused(lambda value=value:sel['_edge_policy'](value),'selector refuses '+label)
inputs=ast.get_source_segment(compact,next(n for n in ast.parse(compact).body if isinstance(n,ast.FunctionDef) and n.name=='_edge_inputs'))
ck(all(t in inputs for t in ["role in ad.inputs","path.resolve()==path","run.read_input(role)==body","runtime['runtime_inventory_sha256']==ad.inputs['environment']['sha256']","source_files","run.read_input('environment')==body"]),'registered roles source/environment genuine-read joins retained')
# Execute only extracted constructor control flow against inert stand-ins. No real owner, native loader or science import.
pair=read(D/'batched_pair_executor.py');cl=next(n for n in ast.parse(pair).body if isinstance(n,ast.ClassDef) and n.name=='PairExecutor')
cl.body=[n for n in cl.body if isinstance(n,ast.FunctionDef) and n.name in ('__init__','close')]
events=[];primary=KeyboardInterrupt('synthetic constructor failure')
def attach_normal(obj,value):obj._compiled_normalization_policy=value
def normal_owner(value):return types.SimpleNamespace(close=lambda:events.append('normal_close'))
def fail_edge(*args,**kwargs):events.append('edge_attempt');raise primary
edge=types.SimpleNamespace(attach=ns['attach'],EdgeOwner=fail_edge)
env={'copy':copy,'sys':types.SimpleNamespace(modules={'scipy':object()}),'adaptive_edge_policy':types.SimpleNamespace(attach=lambda *a:None),'compiled_normalization_policy':types.SimpleNamespace(attach=attach_normal,BackendOwner=normal_owner),'compiled_edge_owner':edge,'annealing':types.SimpleNamespace(np=object(),agreement=object())}
exec(compile(ast.Module(body=[cl],type_ignores=[]),'constructor-only-standins','exec'),env)
schedule=dict(max_checkpoints=1,calls_per_checkpoint=1,operations_per_call=1,max_total_checkpoints=1,max_total_checkpoint_bytes=1)
try:env['PairExecutor']({},dict(max_publications=1),schedule,lambda:None,compiled_normalization_policy_value=(('x',1),),compiled_edge_policy_value=policy)
except BaseException as error:ck(error is primary and events==['edge_attempt','normal_close'],'edge constructor failure before publication closes existing normal owner and preserves fatal identity')
else:ck(False,'expected synthetic failure')
events.clear()
def edge_owner(*args,**kwargs):
    events.append('edge_construct')
    return types.SimpleNamespace(current=lambda:None,borrow=lambda:None,close=lambda:events.append('edge_close'))
edge.EdgeOwner=edge_owner
obj=env['PairExecutor']({},dict(max_publications=1),schedule,lambda:None,compiled_normalization_policy_value=(('x',1),),compiled_edge_policy_value=policy);obj.close()
ck(events==['edge_construct','normal_close','edge_close'],'selected parent captures and closes both owners')
events.clear();obj=env['PairExecutor']({},dict(max_publications=1),schedule,lambda:None);obj.close();ck(events==[],'default constructs neither backend owner')
memo=read(D/'batched_numeric_reuse.py');numeric=read(D/'batched_numeric_execution.py');preload=read(D/'real_pilot_import_caller.py');session=read(D/'matching_immutable_session.py')
ck(memo.index('cleanup=self.executor.close')<memo.index('self._slots=[None]*max_entries') and "try:cleanup()" in memo,'memo constructor tail cleanup captured before table allocation')
ck('compiled_edge_owner.join(self,self.memo)' in numeric and 'compiled_edge_owner.join(self,self.executor)' in memo and 'compiled_edge_owner.join(self,session)' in pair,'numeric to memo to persistent executor to session policy joins')
ck(all(requirements['tradingagents/research/onchain_replication/'+name]['sha256'] in memo for name in ('compiled_edge_owner.py','batched_pair_executor.py','matching_annealing.py','matching_checkpoint.py','matching_immutable_session.py')),'five changed lower source pins rejoined by memo attestation')
ck("if edge:names+=('compiled_edge_owner','edge_chunk_adapter'" in compact and 'if edge:' in preload and 'from . import compiled_edge_owner, edge_chunk_adapter' in preload,'selected helpers admitted and preloaded before lease')
ck('compiled_edge_policy' in numeric and "'closed edge policy differs from admitted input'" in compact,'summary and closed stage retain selected policy')
advance=ast.get_source_segment(session,next(n for n in ast.walk(ast.parse(session)) if isinstance(n,ast.FunctionDef) and n.name=='advance'))
ck(advance.index('self.check(state)')<advance.index('self.engine._advance_owned')<advance.index('self._edge_current()'),'successful advance has two edge-current checks around numerical body')
out={'status':'PASS_BOUNDED_SOURCE_ONLY','checks':checks,'references':refs,'native_executed':False,'scientific_imports':False,'actual_authority_executed':False,'limits':{'cpu':3,'nice':10,'cpu_seconds':10,'address_space_bytes':512*1024**2,'file_bytes':4*1024**2}}
with (P/'UPPER_OBSERVATIONS01.json').open('x') as f:json.dump(out,f,indent=2,sort_keys=True);f.write('\n')
print(json.dumps({'status':out['status'],'checks':len(checks),'sha256':hashlib.sha256((P/'UPPER_OBSERVATIONS01.json').read_bytes()).hexdigest()},sort_keys=True))
