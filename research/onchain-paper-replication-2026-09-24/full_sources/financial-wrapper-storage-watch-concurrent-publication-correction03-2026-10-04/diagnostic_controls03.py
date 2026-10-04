import importlib.util,json,os
from pathlib import Path
from types import SimpleNamespace
H=Path(__file__).resolve().parent;rows=[]
L=dict(max_allocated_bytes=1<<20,max_logical_bytes=1<<20,max_entries=100,max_depth=8,max_scan_seconds=5)
def load(name):
 s=importlib.util.spec_from_file_location(name,H/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.os=SimpleNamespace(**vars(os));return m

def graph(error):
 todo=[error];seen=[]
 while todo:
  e=todo.pop()
  if any(e is x for x in seen):continue
  seen.append(e)
  for key in ('__cause__','__context__'):
   r=BaseException.__dict__[key].__get__(e)
   if r is not None:todo.append(r)
  state=BaseException.__dict__['__dict__'].__get__(e)
  todo.extend(x for x in state.get('storage_cleanup_errors',()) if isinstance(x,BaseException))
 return seen
before=len(os.listdir('/proc/self/fd'))
# Reproduce all three independently frozen source REDs and successor GREEN.
for label in ('original_workflow_storage','predecessor_workflow_storage','original02_workflow_storage','workflow_storage'):
 m=load(label);p=H/'diagnostic-controls'/label;p.mkdir(parents=True);(p/'f').write_bytes(b'x');hooks=[];closed=[]
 class First(KeyboardInterrupt):
  @property
  def __cause__(self):hooks.append('cause');raise SystemExit('diagnostic replacement')
 first=First('original fatal')
 def st(path,*a,**kw):
  if path=='f':raise first
  return os.stat(path,*a,**kw)
 def close(fd):os.close(fd);closed.append(fd)
 m.os.stat=st;m.os.close=close
 try:m.StorageWatch(p,L).check()
 except BaseException as e:
  is_new=label=='workflow_storage';assert (e is first)==is_new and len(closed)==1
  assert hooks==([] if is_new else ['cause'])
  assert any(first is n for n in graph(e))
  trace=[];tb=BaseException.__dict__['__traceback__'].__get__(e)
  while tb:trace.append({'function':tb.tb_frame.f_code.co_name,'line':tb.tb_lineno,'source':tb.tb_frame.f_code.co_filename});tb=tb.tb_next
  rows.append({'case':'exact-review-'+label,'original_fatal_selected':e is first,'selected_type':type(e).__name__,'hook_calls':hooks[:],'actual_descriptors_closed':len(closed),'traceback':trace})
 else:raise AssertionError('fatal swallowed')
# Real nested traversal: original fatal remains selected through both wrappers,
# despite hostile cause/context and zero/ordinary/fatal close secondary failures.
for base in (KeyboardInterrupt,MemoryError,SystemExit):
 for property_name in ('__cause__','__context__'):
  for close_type in (None,RuntimeError,MemoryError):
   m=load('workflow_storage');key=base.__name__+'-'+property_name+'-'+('clean' if close_type is None else close_type.__name__)
   p=H/'matrix'/key;(p/'d').mkdir(parents=True);(p/'d'/'f').write_bytes(b'x');hooks=[];closed=[];errors=[];stats=[]
   def hostile(self):hooks.append(property_name);raise SystemExit('hostile diagnostic')
   First=type('First',(base,),{property_name:property(hostile)})
   first=First('first')
   def st(path,*a,**kw):
    if path=='f':stats.append(path);raise first
    return os.stat(path,*a,**kw)
   def close(fd):
    os.close(fd);closed.append(fd)
    if close_type is not None:
     error=close_type('actual close uncertainty');errors.append(error);raise error
   m.os.stat=st;m.os.close=close
   try:m.StorageWatch(p,L).check()
   except BaseException as e:
    assert e is first and hooks==[] and len(closed)==2 and len(stats)==1
    reachable=graph(e);assert all(any(error is r for r in reachable) for error in errors)
    rows.append({'case':key,'first_fatal_selected':True,'diagnostic_hooks':hooks[:],'all_secondary_objects_retained':True,'closes':len(closed),'fatal_body_attempts':len(stats)})
   else:raise AssertionError('fatal accepted')
# Isolate the outer check wrapper with a genuine _scan (skip only _check dispatch),
# proving its guard is required independently of the inner guard.
for label in ('original02_workflow_storage','workflow_storage'):
 m=load(label);p=H/'outer'/label;p.mkdir(parents=True);(p/'f').write_bytes(b'x');hooks=[];closed=[]
 class First(KeyboardInterrupt):
  @property
  def __context__(self):hooks.append('context');raise SystemExit('outer diagnostic')
 first=First('first')
 def st(path,*a,**kw):
  if path=='f':raise first
  return os.stat(path,*a,**kw)
 def close(fd):os.close(fd);closed.append(fd)
 m.os.stat=st;m.os.close=close;w=m.StorageWatch(p,L)
 w._check=lambda begin,history:w._scan(begin)
 try:w.check()
 except BaseException as e:
  assert (e is first)==(label=='workflow_storage') and len(closed)==1
  rows.append({'case':'outer-isolated-'+label,'first_fatal_selected':e is first,'hooks':hooks[:],'actual_close_count':len(closed)})
 else:raise AssertionError('outer fatal accepted')
# Ordinary failures keep existing diagnostic attachment and no retry.
m=load('workflow_storage');p=H/'ordinary';p.mkdir();(p/'f').write_bytes(b'x');original=ValueError('ordinary');attempts=[]
def st(path,*a,**kw):
 if path=='f':attempts.append(path);raise original
 return os.stat(path,*a,**kw)
m.os.stat=st
try:m.StorageWatch(p,L).check()
except ValueError as e:
 assert e is original and len(attempts)==1 and 'hardlink_observations' in e.observation and 'mutation_observations' in e.observation
 rows.append({'case':'ordinary-diagnostics-unchanged','attempts':len(attempts),'observation_keys':sorted(e.observation)})
else:raise AssertionError('ordinary accepted')
assert len(os.listdir('/proc/self/fd'))==before
rows.append({'case':'reviewer-fds','before':before,'after':len(os.listdir('/proc/self/fd'))})
print(json.dumps({'status':'OPAQUE_FATAL_DIAGNOSTIC_CONTROLS','cases':len(rows),'results':rows},indent=2))
