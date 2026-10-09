import hashlib,importlib.util,json,os,resource,signal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
H=Path(__file__).resolve().parent;P=H.parent/'mcm-batched-execution01-2026-10-09';spec=importlib.util.spec_from_file_location('engineering_journal',P/'batch_journal.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def sha(b):return hashlib.sha256(b).hexdigest()
assert sha((P/'batch_journal.py').read_bytes())=='34113867e8690e8d6a37d6b345c5f3501c920ed35cde77bef741c0513860b654'
results=[]
for case in ['pending_mutation','root_replacement','purpose_mutation','boundary_exception']:
 root=H/case;calls=[];purpose={'ordinal':0,'kind':'synthetic-engineering'};failure=RuntimeError('synthetic-boundary-refusal')
 def boundary():
  calls.append(1)
  if len(calls)==2:
   if case=='pending_mutation':(root/'00000000.pending.json').write_bytes(b'{}\n')
   elif case=='root_replacement':root.rename(H/'root_replacement_moved');root.mkdir()
   elif case=='boundary_exception':raise failure
 def executor(a,b,key):
  if case=='purpose_mutation':purpose['ordinal']=999
  return 0.5,3,'iteration_cap'
 journal=m.BatchJournal(root,batch_cells=1,max_cells=1,max_bytes=8192,max_body_bytes=2048,boundary=boundary)
 try:
  try:
   returned=journal.run_batch([(purpose,None,None)],executor);error=None
  except BaseException as e:
   returned=None;error=type(e).__name__;assert case=='boundary_exception' and e is failure
  location=H/'root_replacement_moved' if case=='root_replacement' else root
  final=location/'00000000.complete.json';pending=location/'00000000.pending.json'
  record={'case':case,'returned_success':returned is not None,'credited_cells':journal.cells,'poisoned':journal.poisoned,'error':error,'complete_exists_at_fd_root':final.exists(),'complete_exists_at_declared_root':(root/'00000000.complete.json').exists(),'current_purpose_ordinal':purpose['ordinal']}
  if final.exists():
   done=json.loads(final.read_bytes());record.update(pending_hash_matches=done['pending_sha256']==sha(pending.read_bytes()),recorded_ordinal=done['records'][0]['ordinal'],purpose_hash_matches=done['records'][0]['purpose_sha256']==m.digest(m.body(purpose)))
  if case=='pending_mutation':assert record['returned_success'] and record['credited_cells']==1 and not record['pending_hash_matches']
  elif case=='root_replacement':assert record['returned_success'] and record['credited_cells']==1 and not record['complete_exists_at_declared_root']
  elif case=='purpose_mutation':assert record['returned_success'] and not record['purpose_hash_matches']
  else:assert journal.poisoned and journal.cells==0 and not final.exists() and pending.exists()
  results.append(record)
 finally:journal.close()
(H/'REPRODUCTION01.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results))
