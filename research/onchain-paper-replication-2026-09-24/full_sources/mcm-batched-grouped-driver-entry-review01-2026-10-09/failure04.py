from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'routing02.py').read_text().split('class Journal:pass')[0];exec(compile(s,'reused_callback_setup','exec'))
class Journal:pass
checks=[]
for count in (16,17):
 primary=RuntimeError('synthetic group flush failure');calls=[];records={}
 def preserve(owner,stage,**kw):
  items=kw['items'];calls.append(tuple(i for i,_ in items))
  if items[-1][0]==count-1:raise primary
  r={'n':len(items)};records[kw['work']/'offload.json']=json.dumps(r).encode();return r
 def finalizer(*a,**kw):raise AssertionError('finalizer reached after failed flush')
 off=types.SimpleNamespace(preserve_and_retire=preserve,typed=types.SimpleNamespace(_read=lambda p:records[p]),finalize=finalizer)
 post,final,state=make(lambda:None,require,{'journal':types.SimpleNamespace(BatchJournal=Journal)},off,types.SimpleNamespace(owner=None),None,Path('/synthetic'),hashlib,json,types.SimpleNamespace(fsync=lambda fd:None),lambda *a,**k:{'bytes':1},{'max_offload_entries':1000,'max_offload_metadata_bytes':1000},-1,count)
 j=Journal()
 try:
  for i in range(count):post(j,i,bytes([i])*168,None)
  final(j,None,count,None)
 except RuntimeError as e:assert e is primary and state()[2] is None
 else:raise AssertionError('flush failure swallowed')
 checks.append('full16_failure_primary_no_coverage' if count==16 else 'tail_failure_primary_no_final_sweep')
(OUT/'FAILURE04.json').write_text(json.dumps({'checks':checks,'genuine_authority':False},indent=2)+'\n');print(json.dumps(checks))
