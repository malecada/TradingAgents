import os,resource
os.sched_setaffinity(0,{2,3});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
import ast,json,hashlib,statistics,runpy,difflib,types,sys,contextlib
from pathlib import Path
F=Path('research/onchain-paper-replication-2026-09-24/full_sources');C=F/'pilot-weekly-graph-digest-pin-candidate-2026-10-12';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=json.loads((C/'SOURCE_MANIFEST01.json').read_text());assert h(C/'SOURCE_MANIFEST01.json')=='a856f0ecf5d2a8db14837e092586d7340bca711fdca0c18f4ba4be37c226998e'
for row in [*m['source_pins'],m['fixture_dependency'],*m['files']]:
 p=Path(row['path']);assert h(p)==row['sha256'] and p.stat().st_size==row['bytes']
a=(C/'BASELINE_imported_mcm_identity.py').read_text();b=(C/'imported_mcm_identity.py').read_text();helper=(C/'weekly_graph_digest_pin.py').read_text();path='tradingagents/research/onchain_replication/'
diff=lambda a,b,x,y:''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=x,tofile=y))
assert (C/'CANDIDATE01.diff').read_text()==diff(a,b,'a/'+path+'imported_mcm_identity.py','b/'+path+'imported_mcm_identity.py')+diff('',helper,'/dev/null','b/'+path+'weekly_graph_digest_pin.py')
assert (C/'INVERSE01.diff').read_text()==diff(helper,'','a/'+path+'weekly_graph_digest_pin.py','/dev/null')+diff(b,a,'a/'+path+'imported_mcm_identity.py','b/'+path+'imported_mcm_identity.py')
ns=runpy.run_path(str(C/'check_candidate01.py'));graph=ns['graph'];np=ns['np'];oh=ns['original_hash'];controls=[]
# Combined immutable tuple identity, hidden base header and optional aggregate tests.
for change in ('tuple_identity','base_header','aggregate'):
 g=graph(4);env,calls=ns['helper']();state=env['create'](g,original_digest=oh(g));assert state is not None
 if change=='tuple_identity':object.__setattr__(g,'node_ids',tuple(list(g.node_ids)))
 elif change=='base_header':g.node_features.base.shape=(2,8)
 else:object.__setattr__(g,'edge_aggregates',np.frombuffer(np.zeros((3,2)).tobytes(),dtype='f8').reshape(3,2))
 digest,new=env['verify'](g,state);assert new is None and digest==oh(g)
 controls.append(change)
# Fresh actual validator must refuse before any rejoin/hash when state exists.
g=graph(4);env,calls=ns['helper']();state=env['create'](g,original_digest=oh(g));fatal=ValueError('independent validation refusal');events=[]
def fail(g):events.append('validate');raise fatal
env['validate_graph']=fail;env['_rejoin']=lambda *a:events.append('rejoin');env['graph_hash']=lambda *a:events.append('hash')
try:env['verify'](g,state)
except ValueError as e:assert e is fatal and events==['validate']
else:raise AssertionError('accepted failed validation')
controls.append('validation refusal before rejoin/hash')
# Initial key mismatch and changed mapping must not pin.
g=graph(4);env,calls=ns['helper']();assert env['create'](g,original_digest='f'*64) is None
backing={};object.__setattr__(g,'exclusion_counts',types.MappingProxyType(backing));state=env['create'](g,original_digest=oh(g));backing['zero']=0;digest,new=env['verify'](g,state);assert new is None and digest==oh(g)
controls.append('original key mismatch/mapping backing mutation')
# Actual source function roster: source omission excludes; inclusion captures every authored helper function and code replacement.
lease=ast.parse(Path(path+'imported_authority_lease.py').read_text());fn=next(n for n in lease.body if isinstance(n,ast.FunctionDef) and n.name=='_loaded')
def require(ok,msg):
 if not ok:raise ValueError(msg)
ld={'sys':sys,'types':types,'Path':Path,'contextlib':contextlib,'require':require,'AUTHORITY_CLASSES':{'Target'}};exec(compile(ast.Module([fn],[]),'<review>','exec'),ld)
name='_synthetic_weekly_pin_review';module=types.ModuleType(name);p=(C/'weekly_graph_digest_pin.py').resolve();module.__file__=str(p);module.__dict__.update({'np':np,'GraphSnapshot':ns['GraphSnapshot'],'validate_graph':ns['validate'],'graph_hash':oh});tree=ast.parse(helper);tree.body=[n for n in tree.body if not (isinstance(n,ast.ImportFrom) and n.level)];exec(compile(tree,str(p),'exec'),module.__dict__);sys.modules[name]=module
try:
 root=Path.cwd();rel=str(p.relative_to(root));assert name not in ld['_loaded'](root,{})
 first=ld['_loaded'](root,{rel:h(p)});saved=first[name][2];assert {v[0] for v in saved}=={n.name for n in tree.body if isinstance(n,ast.FunctionDef)}
 module.verify.__code__=compile('def replacement(*a): return None','<mutation>','exec').co_consts[0]
 assert ld['_loaded'](root,{rel:h(p)})!=first
finally:sys.modules.pop(name,None)
controls.append('source roster required and helper code mutation detected')
bench=json.loads((C/'BENCHMARK02.json').read_text());assert bench['source_sha256']==h(C/'weekly_graph_digest_pin.py');assert bench['helper_validation_calls']==10 and bench['helper_hash_calls']==1
med={k:statistics.median(x['wall'] for x in v) for k,v in bench['samples'].items()};assert all(len(v)==9 for v in bench['samples'].values()) and med==bench['median_wall_seconds'];x,y=med.values();assert bench['baseline_over_pin']==x/y and bench['wall_reduction_fraction']==1-y/x
assert bench['affinity']==[2,3] and bench['address_limit_bytes']==1024**3 and bench['cpu_limit_seconds']==60
# One tiny digest correspondence, not benchmark rerun.
g=graph(3);env,calls=ns['helper']();state=env['create'](g,original_digest=oh(g));assert env['verify'](g,state)[0]==oh(g)
print(json.dumps({'status':'PASS','controls':controls,'manifest_literal_inverse':'PASS','median_wall_seconds':med,'wall_reduction_fraction':1-y/x,'initial_pin_seconds':bench['initial_pin_construction_wall_seconds'],'helper_validation_calls':10,'helper_hash_calls':1,'benchmark_digest':bench['original_digest']},indent=2))
