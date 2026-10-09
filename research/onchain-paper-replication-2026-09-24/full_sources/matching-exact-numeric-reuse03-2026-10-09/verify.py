import ast,hashlib,importlib,json,os,struct,sys,types
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P.parents[3]))
package=types.ModuleType('memo03_fixture');package.__path__=[str(P)];sys.modules[package.__name__]=package
m=importlib.import_module('memo03_fixture.numeric_reuse')
import numpy as np
from tradingagents.research.onchain_replication.contracts import AttributedGraph
c=dict(beta0=.2,beta_final=.5,beta_rate=.1,max_iterations=3,alpha=.7,max_pair_entries=10000,normalization_iterations=1,solver='algorithm1_literal')
p=dict(max_state_bytes=65536,normalization_chunk_entries=8,hardening_chunk_entries=8,hardening_buffer_bytes=65536,max_score_buffer_bytes=65536,chunk_edges=8,max_checkpoint_bytes=262144,max_publications=100,total_checkpoint_bytes=1048576)
s=dict(max_checkpoints=100,calls_per_checkpoint=2,operations_per_call=10000,max_total_checkpoints=1000,max_total_checkpoint_bytes=500000000)
def graph(names):return AttributedGraph(names,np.array([[0.],[1.]]),np.array([[0,1],[1,0]],dtype=np.int64),np.array([[.2],[.3]]),'a'*64,names[0])
a,b=graph(('a','b')),graph(('x','y'));checks=[]
def ck(n,v):assert v,n;checks.append(n)
def make(callback=lambda *a:None,schedule=s):return m.NumericReuseExecutor(c,p,schedule,callback,max_entries=8,max_retained_bytes=16384,max_key_bytes=4096)
ck('single_packaged_executor',m.accepted is importlib.import_module('memo03_fixture.batched_pair_executor'))
ck('actual_installed_session',m.accepted.ImmutablePairSession is m.immutable_session.ImmutablePairSession)
original=m.accepted.PairExecutor(c,p,s,lambda *a:None)(a,b,'a'*64)
x=make();x.begin_batch();computed=x(a,b,'1'*64);first=dict(x.last_receipt);reused=x(a,b,'2'*64);second=dict(x.last_receipt);x.end_batch()
ck('actual_computed_reused_exact_bits',struct.pack('>d',original[0])==struct.pack('>d',computed[0])==struct.pack('>d',reused[0]) and original[1:]==computed[1:]==reused[1:])
ck('fresh_purpose_origin',first['mode']=='computed' and second['mode']=='reused' and second['purpose_sha256']=='2'*64 and second['origin_purpose_sha256']=='1'*64)
ck('provisional_receipt',not second['old_per_occurrence_execution_credit'] and not second['boundary_validated_batch_complete']);x.close();ck('close_clear',x.count==0 and x.last_receipt is None)
# Real checkpoint callback on the unchanged schedule boundary; deliberate primary exception.
short=s|{'operations_per_call':1};seen=[];primary=RuntimeError('synthetic checkpoint stop')
def fail(*args):seen.append((args[0],args[1],args[2]['phase']));raise primary
x=make(fail,short);x.begin_batch()
try:x(a,b,'3'*64)
except RuntimeError as e:ck('real_checkpoint_primary_failure',e is primary and seen[0][:2]==('3'*64,0) and x.poisoned and x.executor.poisoned and x.count==0 and x.last_receipt is None)
else:raise AssertionError('callback did not fail')
x.close()
# Newly included session runtime roster is attested after actual checkpoint callback.
saved=m.immutable_session.config_pin
x=make(lambda *args:setattr(m.immutable_session,'config_pin',lambda *args:None),short);x.begin_batch()
try:
 try:x(a,b,'4'*64)
 except ValueError as e:ck('session_roster_checkpoint_guard',str(e)=='numeric runtime function/code changed' and x.poisoned and x.count==0)
 else:raise AssertionError('changed session accepted')
finally:m.immutable_session.config_pin=saved;x.close()
# Source-body guard is fixed, not refreshed from current runtime.
x=make();x.begin_batch();original_path=m.immutable_session.__file__;fixture=P/'wrong-source.txt';fixture.write_text('source fixture\n');m.immutable_session.__file__=str(fixture)
try:
 try:x.end_batch()
 except ValueError as e:ck('session_fixed_source_guard',str(e)=='numeric source changed' and x.poisoned and x.count==0)
 else:raise AssertionError('changed session source accepted')
finally:m.immutable_session.__file__=original_path;x.close()
old=ast.parse((P.parent/'matching-exact-numeric-reuse02-2026-10-09/numeric_reuse.py').read_text());new=ast.parse((P/'numeric_reuse.py').read_text())
def definitions(t):return {n.name:ast.dump(n) for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
od,nd=definitions(old),definitions(new);ck('cache_and_boundaries_literal_ast_unchanged',all(od[n]==nd[n] for n in od if n not in {'digest','attest'}))
ck('executor02_byte_identical',(P/'batched_pair_executor.py').read_bytes()==(P.parent/'mcm-immutable-pair-executor02-2026-10-09/pair_executor.py').read_bytes())
result={'status':'PASS','checks':checks,'computed':computed,'first_receipt':first,'reused_receipt':second,'checkpoint_trace':seen,'affinity':sorted(os.sched_getaffinity(0)),'empirical_inputs':False,'real_owner_or_authority':False,'source_sha256':hashlib.sha256((P/'numeric_reuse.py').read_bytes()).hexdigest()}
(P/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
