import ast,hashlib,importlib.util,json,os,resource,signal
from pathlib import Path
resource.setrlimit(resource.RLIMIT_AS,(256*1024**2,)*2);resource.setrlimit(resource.RLIMIT_FSIZE,(4*1024**2,)*2);os.sched_setaffinity(0,{3,4});os.nice(10);signal.alarm(30)
H=Path(__file__).resolve().parent;F=H.parent;P=F/'mcm-batched-execution03-2026-10-09';spec=importlib.util.spec_from_file_location('journal03',P/'batch_journal.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
results=[]
for mode in ['healthy','short','extra','misorder','prior_purpose','workload','close_mutation','pending','root','header']:
 root=H/('stream-'+mode);workload={'scope':'synthetic'};held=[];calls=[];closed=[];bounds=[]
 def boundary():
  bounds.append(1)
  if len(bounds)==2:
   if mode=='pending':(root/'00000000.pending.json').write_text('{}')
   if mode=='root':root.rename(H/'stream-root-moved');root.mkdir()
 j=m.BatchJournal(root,batch_cells=2,max_cells=2,max_bytes=8192,max_body_bytes=1024,boundary=boundary)
 def tasks():
  try:
   assert (root/'00000000.pending.json').exists()
   for i in range(1 if mode=='short' else 3 if mode=='extra' else 2):
    if mode=='prior_purpose' and i==1:held[0]['changed']=True
    purpose={'ordinal':9 if mode=='misorder' else i};held.append(purpose)
    yield purpose,None,None
   if mode=='close_mutation':held[0]['changed']=True
  finally:closed.append(True)
 def execute(*args):
  calls.append(1)
  if mode=='workload':workload['scope']='mutated'
  return (-0. if len(calls)==1 else .5),len(calls),'iteration_cap'
 try:
  try:rows=j.run_batch_stream(2,tasks(),execute,workload)
  except ValueError as error:
   assert mode not in ('healthy','header') and j.poisoned and j.cells==0
   record={'mode':mode,'refused':True,'executor_calls':len(calls),'iterator_closed':bool(closed)}
   if mode=='extra':assert len(calls)==2
   assert closed and not (root/'00000000.complete.json').exists()
  else:
   assert mode in ('healthy','header') and j.cells==2 and closed
   pending=json.loads((root/'00000000.pending.json').read_text());meta=json.loads((root/'00000000.complete.json').read_text());payload=(root/'00000000.records.bin').read_bytes()
   assert 'purposes_sha256' not in pending and meta['purposes_sha256']==hashlib.sha256(b''.join(r[1] for r in rows)).hexdigest() and len(payload)==92+2*53
   if mode=='header':
    p=root/'00000000.records.bin';raw=bytearray(p.read_bytes());raw[0]^=1;p.write_bytes(raw)
    try:j.read_complete(0)
    except ValueError:assert j.poisoned
    else:raise AssertionError('bad header accepted')
   record={'mode':mode,'validated':True,'executor_calls':len(calls),'iterator_closed':bool(closed)}
  results.append(record)
 finally:j.close()
# Check only unchanged low-level functions against accepted02; no rerun.
def methods(path):
 t=ast.parse(path.read_text());c=next(n for n in t.body if isinstance(n,ast.ClassDef));return {n.name:ast.dump(n) for n in c.body if isinstance(n,ast.FunctionDef)}
a=methods(F/'mcm-batched-execution02-2026-10-09/batch_journal.py');b=methods(P/'batch_journal.py')
for name in ['__init__','_root','_read','_write','_publish','_pending','read_complete','close']:assert a[name]==b[name]
for path in [F/'mcm-batched-driver02-2026-10-09/driver.py',F/'mcm-batched-driver03-2026-10-09/driver.py']:
 nodes={n.name:ast.dump(n) for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef)}
 if 'old' not in globals():old=nodes
 else:assert all(nodes[k]==old[k] for k in ['_tasks','_batch'])
(H/'STREAM02.json').write_text(json.dumps({'cases':results,'unchanged_IO_functions':8,'unchanged_task_functions':2},indent=2)+'\n');print(json.dumps({'cases':len(results),'status':'passed'}))
