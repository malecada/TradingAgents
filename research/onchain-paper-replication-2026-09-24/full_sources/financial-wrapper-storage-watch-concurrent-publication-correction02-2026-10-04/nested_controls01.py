import importlib.util,json,os
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent
LIMITS=dict(max_allocated_bytes=1<<20,max_logical_bytes=1<<20,max_entries=100,max_depth=8,max_scan_seconds=5)
rows=[]
def load(name):
 spec=importlib.util.spec_from_file_location(name,H/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.os=SimpleNamespace(**vars(os));return m
old=load('predecessor_workflow_storage');new=load('workflow_storage')
def dictionary(error):return BaseException.__dict__['__dict__'].__get__(error)
def graph(error):
 todo=[error];seen=[]
 while todo:
  node=todo.pop()
  if any(node is prior for prior in seen):continue
  seen.append(node)
  for name in ('__cause__','__context__'):
   ref=BaseException.__dict__[name].__get__(node)
   if ref is not None:todo.append(ref)
  todo.extend(x for x in dict.get(dictionary(node),'storage_cleanup_errors',()) if isinstance(x,BaseException))
  if isinstance(node,BaseExceptionGroup):todo.extend(node.exceptions)
 return seen
before=len(os.listdir('/proc/self/fd'))
# Exact reviewer structure: child stat KeyboardInterrupt, two real descriptor
# closes, two distinct uncertainty exceptions, original object graph traversal.
for module in (old,new):
 p=H/'nested-controls'/module.__name__; (p/'d').mkdir(parents=True);(p/'d'/'f').write_bytes(b'x')
 first=KeyboardInterrupt('body');seen=[];closed=[]
 def st(path,*a,**kw):
  if path=='f':raise first
  return os.stat(path,*a,**kw)
 def close(fd):
  os.close(fd);closed.append(fd);e=RuntimeError('separate real close uncertainty');seen.append(e);raise e
 module.os.stat=st;module.os.close=close
 try:module.StorageWatch(p,LIMITS).check()
 except BaseException as e:
  reachable=graph(e);present=[any(x is r for r in reachable) for x in seen]
  assert e is first and len(seen)==2
  if module is old:assert present==[False,True]
  else:assert present==[True,True] and tuple(dictionary(e)['storage_cleanup_errors'])==tuple(seen)
  for fd in closed:
   try:os.fstat(fd)
   except OSError:pass
   else:raise AssertionError('descriptor remains open')
  rows.append({'case':'exact-reviewer-nested-'+module.__name__,'first_fatal_retained':e is first,'close_errors_reachable':present,'actual_descriptors_closed':len(closed),'no_reclose':len(set(closed))==len(closed)})
 else:raise AssertionError('nested failure accepted')
 finally:module.os=SimpleNamespace(**vars(os))
# Every primary/secondary mix; real independent descriptors, nested chains.
for i,primary_type in enumerate((ValueError,KeyboardInterrupt,MemoryError,SystemExit)):
 for j,secondary_type in enumerate((RuntimeError,KeyboardInterrupt,MemoryError,SystemExit)):
  p=H/'matrix'/str(i)/str(j);p.mkdir(parents=True);primary=primary_type('original');current=primary;errors=[];closed=[]
  for count in range(3):
   fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY);secondary=secondary_type('secondary');errors.append(secondary)
   def action():os.close(fd);closed.append(fd);raise secondary
   try:new._cleanup(action,current)
   except BaseException as e:current=e
   else:raise AssertionError('uncertainty accepted')
   try:os.fstat(fd)
   except OSError:pass
   else:raise AssertionError('unclosed descriptor')
  seen=graph(current);assert all(any(e is x for x in seen) for e in errors+[primary])
  if primary_type in (KeyboardInterrupt,MemoryError,SystemExit):assert current is primary
  rows.append({'case':'three-nested-matrix','primary':primary_type.__name__,'secondary':secondary_type.__name__,'all_four_original_objects_reachable':True,'actual_close_calls':len(closed)})
# Exact builtin dictionary descriptor bypasses hostile diagnostics and attribute hooks.
class HostileInterrupt(KeyboardInterrupt):
 calls=[]
 @property
 def __dict__(self):type(self).calls.append('dict-property');raise SystemExit('unsafe property')
 def __getattribute__(self,name):
  if name in ('storage_cleanup_errors','__dict__'):type(self).calls.append('getattr');raise SystemExit('unsafe getattr')
  return super().__getattribute__(name)
 def __setattr__(self,name,value):type(self).calls.append('setattr');raise SystemExit('unsafe setattr')
 def add_note(self,note):type(self).calls.append('add_note');raise SystemExit('unsafe note')
 def __str__(self):type(self).calls.append('str');raise SystemExit('unsafe str')
 def __repr__(self):type(self).calls.append('repr');raise SystemExit('unsafe repr')
p=H/'hostile';p.mkdir();primary=HostileInterrupt('first');errors=[]
for count in range(2):
 fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY);error=RuntimeError('close');errors.append(error)
 def action():os.close(fd);raise error
 try:new._cleanup(action,primary)
 except BaseException as e:assert e is primary
 else:raise AssertionError('hostile close accepted')
assert dictionary(primary)['storage_cleanup_errors']==tuple(errors) and not HostileInterrupt.calls
rows.append({'case':'hostile-diagnostic-hooks-not-called','hooks_called':HostileInterrupt.calls,'retained_errors':2})
# Existing secondary tuple and unusual existing attachment both stay reachable.
for variant in ('tuple','non-tuple'):
 primary=KeyboardInterrupt('first');earlier=RuntimeError('earlier');dictionary(primary)['storage_cleanup_errors']=(earlier,) if variant=='tuple' else earlier
 later=OSError('later');fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY)
 def action():os.close(fd);raise later
 try:new._cleanup(action,primary)
 except BaseException as e:assert e is primary and dictionary(e)['storage_cleanup_errors']==(earlier,later)
 else:raise AssertionError('attachment loss')
 rows.append({'case':'existing-'+variant,'both_error_objects_retained':True})
# Successful cleanup neither raises a dormant primary nor attaches false failures.
for primary in (None,KeyboardInterrupt('dormant')):
 fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY);new._cleanup(lambda:os.close(fd),primary)
 if primary is not None:assert 'storage_cleanup_errors' not in dictionary(primary)
 rows.append({'case':'successful-cleanup','primary_supplied':primary is not None,'returned':True})
assert len(os.listdir('/proc/self/fd'))==before
rows.append({'case':'reviewer-descriptor-count','before':before,'after':len(os.listdir('/proc/self/fd'))})
print(json.dumps({'status':'SOURCE_ONLY_NESTED_CLEANUP_CONTROLS','cases':len(rows),'results':rows},indent=2))
