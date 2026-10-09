import hashlib,importlib.util,json,os,resource,signal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
H=Path(__file__).resolve().parent;P=H.parent/'mcm-batched-execution02-2026-10-09';spec=importlib.util.spec_from_file_location('journal02',P/'batch_journal.py');bj=importlib.util.module_from_spec(spec);spec.loader.exec_module(bj);results=[]
for case in ['partial_write','linked_complete_corruption']:
 root=H/case;j=bj.BatchJournal(root,batch_cells=1,max_cells=1,max_bytes=8192,max_body_bytes=2048,boundary=lambda:None);write=bj.os.write;link=bj.os.link;calls=[];primary=OSError('synthetic-partial-write')
 def altered_write(fd,raw):
  calls.append(1)
  if len(calls)==1:return write(fd,raw[:7])
  raise primary
 def altered_link(src,dst,**kw):
  answer=link(src,dst,**kw)
  if dst.endswith('.complete.json'):(root/dst).write_bytes(b'{}\n')
  return answer
 if case=='partial_write':bj.os.write=altered_write
 else:bj.os.link=altered_link
 try:
  try:j.run_batch([({'ordinal':0},None,None)],lambda *args:(.5,1,'iteration_cap'))
  except (ValueError,OSError) as e:
   if case=='partial_write':assert e is primary
  else:raise AssertionError('publication failure credited')
  assert j.poisoned and j.cells==0;results.append({'case':case,'poisoned':j.poisoned,'credited_cells':j.cells,'files':sorted(p.name for p in root.iterdir())})
 finally:bj.os.write=write;bj.os.link=link;j.close()
p=H/'PUBLICATION02.json';p.write_text(json.dumps(results,indent=2)+'\n');print(hashlib.sha256(p.read_bytes()).hexdigest())
