import importlib.util,json,os,resource
from pathlib import Path
P=Path(__file__).resolve().parent
assert resource.getrlimit(resource.RLIMIT_AS)[0]==268435456 and len(os.sched_getaffinity(0))==2
q=P.parent/'mcm-batched-execution01-2026-10-09/batch_journal.py'
s=importlib.util.spec_from_file_location('old_journal',q);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
r={}
for mode in ['pending','root']:
 root=P/('red01-'+mode);calls=[]
 def boundary():
  calls.append(1)
  if len(calls)==2:
   if mode=='pending':(root/'00000000.pending.json').write_bytes(b'forged\n')
   else:root.rename(P/'red01-moved');root.mkdir()
 j=m.BatchJournal(root,batch_cells=1,max_cells=1,max_bytes=100000,max_body_bytes=8192,boundary=boundary)
 try:
  j.run_batch([({'ordinal':0},None,None)],lambda *args:(0.,1,'iteration_cap'))
  r[mode]={'defect_reproduced':j.cells==1,'credited_cells':j.cells,'poisoned':j.poisoned}
 finally:j.close()
assert all(x['defect_reproduced'] for x in r.values())
(P/'RED01.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
