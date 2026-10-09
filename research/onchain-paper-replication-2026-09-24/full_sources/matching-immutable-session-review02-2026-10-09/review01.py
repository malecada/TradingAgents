import ast,hashlib,importlib.util,json,os,resource,signal,sys,weakref,gc
from pathlib import Path
from types import SimpleNamespace
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
R=Path.cwd();H=Path(__file__).resolve().parent;C=H.parent/'matching-immutable-session02-2026-10-09';OLD=H.parent/'matching-immutable-session01-2026-10-09';sys.path.insert(0,str(R));P='tradingagents.research.onchain_replication.'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(name,file):
 sp=importlib.util.spec_from_file_location(P+name,C/file);m=importlib.util.module_from_spec(sp);sys.modules[sp.name]=m;sp.loader.exec_module(m);return m
import numpy as np
from tradingagents.research.onchain_replication import matching_checkpoint as baseline
from tradingagents.research.onchain_replication.contracts import AttributedGraph
ann=load('_independent_immutable02_ann','matching_annealing.py');engine=load('_independent_immutable02_checkpoint','matching_checkpoint.py');engine.ann=ann;adapter=load('_independent_immutable02_pair','immutable_pair.py')
a=AttributedGraph(node_ids=('x','y'),node_features=np.array([[.1],[.7]]),edge_index=np.array([[0],[1]],dtype=np.int64),edge_features=np.array([[.2]]),parent_hash='a'*64,center_id='x')
b=AttributedGraph(node_ids=('z',),node_features=np.array([[.3]]),edge_index=np.empty((2,0),dtype=np.int64),edge_features=np.empty((0,1)),parent_hash='b'*64,center_id='z')
c=json.loads((R/'research/onchain-paper-replication-2026-09-24/config/matching-stable.json').read_text());policy=dict(max_state_bytes=1048576,normalization_chunk_entries=8,hardening_chunk_entries=8,hardening_buffer_bytes=1048576)
s=adapter.ImmutablePairSession(a,b,c,engine=engine,annealing=ann);state=engine.create(a,b,c,**policy);checks=[]
original=engine.ann;proxy=SimpleNamespace(**vars(ann));calls=[]
def skipped(inner,a,b,c,*,max_operations):calls.append(max_operations);return max_operations
proxy._advance_checked=skipped;engine.ann=proxy
try:
 try:s.advance(state,max_operations=1)
 except ValueError as error:assert str(error)=='matching module dependency changed';checks.append('original_proxy_RED_refused_before_body')
 else:raise AssertionError('proxy accepted')
 assert calls==[] and state['safe'] and state['annealing']['cursor']==0
finally:engine.ann=original
# Original budget order: current state still checked before invalid budget refusal.
for budget in (0,True):
 try:s.advance(state,max_operations=budget)
 except ValueError as e:assert 'positive operation allowance' in str(e)
 else:raise AssertionError('bad budget')
checks.append('invalid_budget_refuses_without_poison_or_operation')
assert s.advance(state,max_operations=1)==baseline.advance((left:=baseline.create(a,b,c,**policy)),a,b,c,max_operations=1)
for name in ('V','M','Q'):assert state['annealing'][name].tobytes()==left['annealing'][name].tobytes()
# Actual unchanged checkpoint publication/load after the changed session boundary.
ref=engine.save(state,H/'checkpoint',a,b,c,max_checkpoint_bytes=1048576)
restored=engine.load(H/'checkpoint',a,b,c,expected_sha256=ref,**policy)
try:
 s.check(restored)
 assert s.advance(restored,max_operations=7)==baseline.advance(left,a,b,c,max_operations=7)
 for name in ('V','M','Q'):assert restored['annealing'][name].tobytes()==left['annealing'][name].tobytes()
 assert restored['annealing']['cursor']==left['annealing']['cursor']
 checks.append('actual_save_load_then_session_advance_matches_public')
 # Mutable state checks still precede arithmetic after restored checkpoint.
 restored['annealing']['Q'][0,0]=float('nan')
 try:s.advance(restored,max_operations=1)
 except ValueError:checks.append('restored_mutable_state_nonfinite_refuses')
 else:raise AssertionError('mutable state accepted')
finally:engine.close(restored);engine.close(state);baseline.close(left)
wa,wb=weakref.ref(a),weakref.ref(b);s.close();del a,b;gc.collect();assert wa() is None and wb() is None;checks.append('close_releases_graph_refs')
for name in ('matching_annealing.py','matching_checkpoint.py'):assert (C/name).read_bytes()==(OLD/name).read_bytes()
# Literal inverse of only02 helper additions, preserving entire01 helper bytes.
x=(C/'immutable_pair.py').read_text();x=x.replace("             (engine, '_advance_owned'), (engine, 'matrix_identity'),\n             (engine.hard, 'check'), (engine.hard, 'create'),\n             (engine.hard, 'advance'),\n             (annealing, 'normalization_policy'),", "             (engine, '_advance_owned'), (engine.hard, 'check'),")
x=x.replace("        self.dependencies = ((engine, 'ann', annealing),\n                             (engine, 'hard', engine.hard),\n                             (engine, 'np', engine.np),\n                             (annealing, 'np', annealing.np))\n",'').replace("        for module, name, dependency in self.dependencies:\n            require(getattr(module, name) is dependency,\n                    'matching module dependency changed')\n",'')
assert x==(OLD/'immutable_pair.py').read_text();checks.append('exact02_to01_helper_inverse_and_numeric_copies_unchanged')
result={'decision':'accepted_narrow_source_seam','checks':checks,'source_sha256':sha(C/'immutable_pair.py'),'candidate_manifest_sha256':sha(C/'MANIFEST01.json'),'original_withheld_sha256':sha(H.parent/'matching-immutable-session-review01-2026-10-09/WITHHELD01.json'),'checkpoint_manifest_sha256':ref,'scope':'One synthetic changed-seam check; no full iteration matrix, graph corpus, speed, capacity, Owner, runtime-authority or launch proof.'}
(H/'RESULT01.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
