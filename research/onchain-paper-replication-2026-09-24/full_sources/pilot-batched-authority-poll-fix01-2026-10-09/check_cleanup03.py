"""Actual executor controlflow with inert state/session cleanup spies."""
import ast,copy,types,json
from pathlib import Path
H=Path(__file__).resolve().parent;events=[];calls=[0]
def poll():
 calls[0]+=1
 if calls[0]==2:raise ValueError('original poll failure')
def close(state):events.append('state_closed');raise RuntimeError('cleanup also failed')
class Session:
 def __init__(self,*a,**k):events.append('session')
 def close(self):events.append('session_closed')
ns=dict(copy=copy,pair=types.SimpleNamespace(hash_string=lambda x:None,policy_check=lambda *a,**k:None,LIMIT=1,ENGINE_FIELDS=set()),engine=types.SimpleNamespace(create=lambda *a,**k:{'phase':'numeric'},close=close),annealing=None,ImmutablePairSession=Session,CheckpointStop=RuntimeError)
t=ast.parse((H/'batched_pair_executor.py').read_text());exec(compile(ast.Module(body=[n for n in t.body if isinstance(n,ast.ClassDef) and n.name=='PairExecutor'],type_ignores=[]),'<actual class>','exec'),ns)
x=ns['PairExecutor']({},dict(max_publications=1,max_checkpoint_bytes=1),dict(max_checkpoints=1,calls_per_checkpoint=1,operations_per_call=1,max_total_checkpoints=1,max_total_checkpoint_bytes=10),lambda *a:None,authority_poll=poll)
try:x(None,None,'x')
except ValueError as e:assert str(e)=='original poll failure' and any('cleanup also failed' in n for n in e.__notes__)
else:raise AssertionError('failure missing')
assert x.poisoned and events==['session','session_closed','state_closed'];(H/'CLEANUP03.json').write_text(json.dumps(dict(status='PASS',events=events,primary_preserved=True,all_cleanup_attempted=True))+'\n');print('PASS poll failure after acquisition: both cleanup attempts, original error retained')
