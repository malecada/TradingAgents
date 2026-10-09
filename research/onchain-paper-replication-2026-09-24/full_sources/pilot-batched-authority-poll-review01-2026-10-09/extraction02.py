"""Actual extraction generator AST, inert index fixture; no authority or arrays."""
import ast,types,json
from pathlib import Path
H=Path(__file__).resolve().parent;C=H.parent/'pilot-batched-authority-poll-fix01-2026-10-09';S=H.parents[3]/'tradingagents/research/onchain_replication'
def test(path,polling=False,fail_at=None):
 events=[];calls=[0]
 class Index:
  def __init__(self,*a,**k):events.append('index')
  def __enter__(self):return self
  def __exit__(self,*a):events.append('closed')
  def neighborhood(self,*a):events.append('extract');return 'local'
 def poll():
  calls[0]+=1;events.append('poll')
  if calls[0]==fail_at:raise ValueError('poll failed')
 t=ast.parse(path.read_text());fn=next(n for n in t.body if isinstance(n,ast.FunctionDef) and n.name=='_tasks');ns=dict(ArrayNeighborhoodIndex=Index,graph_identity=lambda g:'2'*64)
 exec(compile(ast.Module(body=[fn],type_ignores=[]),'<actual tasks>','exec'),ns)
 args=(types.SimpleNamespace(node_ids=('x','y')),list(range(32)),{},dict(max_buffer_bytes=1,edge_chunk=1),dict(workload_sha256='1'*64,graph_hash='3'*64),['4'*64]*32)
 error=None;rows=[]
 try:rows=list(ns['_tasks'](*args,**({'authority_poll':poll} if polling else {})))
 except ValueError as e:error=str(e)
 return events,error,rows
old=test(S/'batched_driver.py');default=test(C/'batched_driver.py');assert old==default
healthy=test(C/'batched_driver.py',True);assert healthy[2]==old[2] and healthy[0][-1]=='closed'
failed=test(C/'batched_driver.py',True,3);assert failed[1]=='poll failed' and failed[0][-1]=='closed' and failed[2]==[]
(H/'EXTRACTION02.json').write_text(json.dumps(dict(status='PASS',default_trace=default[0],polled_trace=healthy[0],failure_trace=failed[0],all32_purposes_unchanged=True),indent=2)+'\n');print('PASS actual generator default/poll order,32 purposes, failure closes index')
