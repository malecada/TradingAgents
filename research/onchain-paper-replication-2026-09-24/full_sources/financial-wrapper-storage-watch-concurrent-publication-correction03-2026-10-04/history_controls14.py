import importlib.util,json,os
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent;rows=[]
L=dict(max_allocated_bytes=1<<20,max_logical_bytes=1<<20,max_entries=100,max_depth=8,max_scan_seconds=5)
def load():
 s=importlib.util.spec_from_file_location('m',H/'workflow_storage.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.os=SimpleNamespace(**vars(os));return m
# Actual discarded publication census before a later fatal retains its history.
m=load();p=H/'history';p.mkdir();(p/'.pending').write_bytes(b'x');changed=False;hooks=[];closes=[]
class Fatal(KeyboardInterrupt):
 @property
 def __cause__(self):hooks.append('cause');raise SystemExit('diagnostic')
first=Fatal('first')
def st(name,*a,**kw):
 global changed
 if name=='.pending' and not changed:changed=True;os.rename(p/'.pending',p/'final')
 elif name=='final':raise first
 return os.stat(name,*a,**kw)
def close(fd):os.close(fd);closes.append(fd)
m.os.stat=st;m.os.close=close
try:m.StorageWatch(p,L).check()
except BaseException as e:
 assert e is first and hooks==[] and len(e.observation['mutation_observations'])==1 and len(closes)==2
 rows.append({'case':'prior-publication-history-retained','mutation_observations':e.observation['mutation_observations'],'original_fatal_selected':True,'actual_closes':len(closes)})
else:raise AssertionError('fatal swallowed')
# Hostile observation diagnostics in both wrappers cannot replace original fatal.
for which in ('getter','setter'):
 m=load();p=H/('hostile-observation-'+which);p.mkdir();(p/'f').write_bytes(b'x');calls=[];closes=[]
 if which=='getter':
  def getter(self):calls.append('getter');raise SystemExit('observation getter')
  Fatal=type('Fatal',(KeyboardInterrupt,),{'observation':property(getter)})
 else:
  def setter(self,name,value):
   if name=='observation':calls.append('setter');raise MemoryError('observation setter')
   BaseException.__setattr__(self,name,value)
  Fatal=type('Fatal',(KeyboardInterrupt,),{'__setattr__':setter})
 first=Fatal('first')
 def st(name,*a,**kw):
  if name=='f':raise first
  return os.stat(name,*a,**kw)
 def close(fd):os.close(fd);closes.append(fd)
 m.os.stat=st;m.os.close=close
 try:m.StorageWatch(p,L).check()
 except BaseException as e:
  assert e is first and len(closes)==1 and len(calls)>=1
  rows.append({'case':'hostile-observation-'+which,'original_fatal_selected':True,'diagnostic_hook_calls':len(calls),'actual_closes':len(closes),'retries':0})
 else:raise AssertionError('hostile fatal accepted')
print(json.dumps({'cases':len(rows),'results':rows},indent=2))
