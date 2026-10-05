"""Tiny stdlib semantic counterexamples; no scientific/authority imports."""
from pathlib import Path
import hashlib,io,json,struct,types
D=Path(__file__).resolve().parent
A=D.parent/'real-data-pilot-score-tail-transport-semantics01-2026-10-05'
src=(A/'score_tail_semantics.py').read_bytes()
assert hashlib.sha256(src).hexdigest()=='cff38dda5367882d35d18c3f95ab6d6af849d5918e5005e41e1d4205a40cd009'
v=types.ModuleType('isolated_semantics');exec(compile(src,str(A/'score_tail_semantics.py'),'exec'),v.__dict__)
sha=lambda b:hashlib.sha256(b).hexdigest()
encode=lambda x:json.dumps(x,sort_keys=True,separators=(',',':')).encode()
scope={k:sha(k.encode()) for k in ('graph','node_order','dictionary','ordered_motifs','matching','workflow')}
owner=sha(b'non-authoritative review fixture')
s=encode({'schema_version':1,'kind':'mcm-score-tail','scope':scope,'owner':owner,'start_cell':7,'cells':2,'destination':sha(b'destination'),'record_format':'<Qd32s32s','record_bytes':80})
def fixture(ordinals):
 head=bytes.fromhex(sha(s));body=b''
 for ordinal,value,purpose in zip(ordinals,(-0.0,1.0),(bytes(range(32)),bytes(reversed(range(32))))):
  frame=struct.pack('<Qd32s',ordinal,value,purpose);head=hashlib.sha256(head+frame).digest();body+=frame+head
 t=encode({'schema_version':1,'start_sha256':sha(s),'status':'complete','reason':'bounded original reason permitted','acknowledged_cells':2,'head':head.hex(),'records_bytes':160,'records_sha256':sha(body)})
 return t,body
results=[]
for name,ordinals,truncate in [('valid_fragmented',(7,8),False),('self_consistent_wrong_ordinal',(7,9),False),('last_byte_missing',(7,8),True)]:
 t,body=fixture(ordinals);stream=io.BytesIO(body[:-1] if truncate else body);requests=[];returned=[]
 def read(n):
  requests.append(n);b=stream.read(min(n,3));returned.append(len(b));return b
 try:
  result=v.verify_complete(read,start_raw=s,terminal_raw=t,start_sha256=sha(s),terminal_sha256=sha(t),scope=scope,owner=owner)
  assert name=='valid_fragmented' and result['cells_verified']==2 and result['bytes_verified']==160
  assert all(result[k] is False for k in ('purpose_ancestry_verified','whole_history_roster_verified','immutable_storage_verified','execution_admission','scientific_completion','capacity_verified','deletion_authority'))
  status='accepted'
 except ValueError as e:
  assert name!='valid_fragmented';status='refused: '+str(e)
 assert max(requests)<=80 and sum(returned)<=160
 results.append({'case':name,'result':status,'sum_requested_bytes':sum(requests),'bytes_returned':sum(returned),'maximum_request':max(requests),'requests':len(requests)})
print(json.dumps({'decision':'pass','checks':results,'qualification':'The summed read(n) request arguments can exceed body length under short reads; actual returned bytes and per-request size remain bounded. No authority, filesystem concurrency or deadline claim.'},sort_keys=True,indent=2))
