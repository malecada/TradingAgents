import importlib.util,json,os
from pathlib import Path
H=Path(__file__).resolve().parent;A=H.parent/'financial-wrapper-storage-watch-concurrent-publication-correction02-2026-10-04';s=importlib.util.spec_from_file_location('m',A/'workflow_storage.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);p=H/'additional';p.mkdir();rows=[]
def state(e):return BaseException.__dict__['__dict__'].__get__(e)
def graph(e):
 pending=[e];seen=[]
 while pending:
  n=pending.pop()
  if any(n is x for x in seen):continue
  seen.append(n)
  for k in ('__cause__','__context__'):
   x=BaseException.__dict__[k].__get__(n)
   if x is not None:pending.append(x)
  attached=state(n).get('storage_cleanup_errors',())
  if type(attached)is tuple:pending.extend(x for x in attached if isinstance(x,BaseException))
 return seen
before=len(os.listdir('/proc/self/fd'))
for ptype in (None,ValueError,KeyboardInterrupt,MemoryError,SystemExit):
 for stype in (RuntimeError,KeyboardInterrupt,MemoryError,SystemExit):
  original=None if ptype is None else ptype('body');selected=original;secondary=[]
  for i in range(3):
   fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY);error=stype('close');secondary.append(error)
   def close():os.close(fd);raise error
   try:m._cleanup(close,selected)
   except BaseException as e:selected=e
   else:raise AssertionError('cleanup failure lost')
  expected=original if ptype in (KeyboardInterrupt,MemoryError,SystemExit) else secondary[0] if stype in (KeyboardInterrupt,MemoryError,SystemExit) else None
  assert expected is None or selected is expected
  reach=graph(selected);assert all(any(x is y for y in reach) for x in secondary+([] if original is None else [original]))
  rows.append({'case':'three-real-closes','primary':None if ptype is None else ptype.__name__,'secondary':stype.__name__,'first_fatal_correct':True,'all_objects_reachable':True})
# Avoid the previous harness mutable-list reporting alias: each row owns a snapshot.
hooks=[]
class Hostile(KeyboardInterrupt):
 @property
 def __dict__(self):hooks.append('dict');raise SystemExit()
 @property
 def storage_cleanup_errors(self):hooks.append('errors-property');raise SystemExit()
 def __getattribute__(self,k):
  if k in ('__dict__','storage_cleanup_errors'):hooks.append('getattr');raise SystemExit()
  return super().__getattribute__(k)
 def __setattr__(self,k,v):hooks.append('setattr');raise SystemExit()
 def __repr__(self):hooks.append('repr');raise SystemExit()
 def __str__(self):hooks.append('str');raise SystemExit()
 def add_note(self,n):hooks.append('note');raise SystemExit()
first=Hostile();errors=[]
for i in range(3):
 fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY);error=RuntimeError();errors.append(error)
 def close():os.close(fd);raise error
 try:m._cleanup(close,first)
 except BaseException as e:assert e is first
assert state(first)['storage_cleanup_errors']==tuple(errors) and not hooks
rows.append({'case':'hostile-cleanup-no-hooks','hooks_snapshot':list(hooks),'all_objects_retained':True})
class HostileTuple(tuple):
 def __iter__(self):raise SystemExit('must not iterate attachment')
 def __add__(self,x):raise SystemExit('must not add subclass')
for earlier in (RuntimeError('opaque earlier'),(RuntimeError('tuple earlier'),),HostileTuple((RuntimeError('subclass earlier'),))):
 first=KeyboardInterrupt();state(first)['storage_cleanup_errors']=earlier;error=OSError();fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY)
 def close():os.close(fd);raise error
 try:m._cleanup(close,first)
 except BaseException as e:assert e is first
 expected=earlier+(error,) if type(earlier)is tuple else (earlier,error)
 assert state(first)['storage_cleanup_errors']==expected
 rows.append({'case':'preexisting-evidence','existing_type':type(earlier).__name__,'existing_identity_retained':True})
for first in (None,KeyboardInterrupt()):
 fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY);m._cleanup(lambda:os.close(fd),first)
 assert first is None or 'storage_cleanup_errors' not in state(first)
 rows.append({'case':'success-no-spurious-error','dormant_primary':first is not None})
assert len(os.listdir('/proc/self/fd'))==before
rows.append({'case':'actual-fd-count','before':before,'after':len(os.listdir('/proc/self/fd'))})
(H/'ADDITIONAL_CONTROLS01.json').write_text(json.dumps({'cases':len(rows),'rows':rows},indent=2)+'\n');print(json.dumps({'cases':len(rows),'status':'PASS'}))
