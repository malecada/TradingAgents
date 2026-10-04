import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
LIMITS=dict(max_allocated_bytes=1<<20,max_logical_bytes=1<<20,max_entries=100,max_depth=8,max_scan_seconds=5)
results=[]
def load(name):
 s=importlib.util.spec_from_file_location(name,HERE/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 m.os=SimpleNamespace(**{k:getattr(os,k) for k in dir(os)})
 return m
old=load('original_workflow_storage');new=load('workflow_storage')
def root(name):
 p=HERE/'controls'/name;p.mkdir(parents=True,mode=0o700);return p

def race(module,name,action):
 p=root(name);(p/'.pending-test').write_bytes(b'opaque payload')
 watch=module.StorageWatch(p,LIMITS)
 original=module.os.stat;done=False
 def hooked(path,*a,**kw):
  nonlocal done
  if path=='.pending-test' and not done:
   done=True
   if action=='publish':os.link(p/'.pending-test',p/'published');os.unlink(p/'.pending-test')
   elif action=='rename':os.rename(p/'.pending-test',p/'published')
   elif action=='disappear':os.rename(p/'.pending-test',p.parent/(p.name+'-retained-away'))
   elif action=='replace':
    os.rename(p/'.pending-test',p.parent/(p.name+'-retained-original'))
    (p/'.pending-test').write_bytes(b'new bounded payload')
  return original(path,*a,**kw)
 module.os.stat=hooked
 try:
  try:r=watch.check();out={'status':'returned','logical':r['logical_file_bytes'],'attempts':r['scan_attempts'],'mutations':r.get('mutation_observations',[])}
  except Exception as e:out={'status':'raised','type':type(e).__name__,'observation':getattr(e,'observation',{})}
 finally:module.os.stat=original
 out.update(case=name,actual_action=action);results.append(out);return out
for action in ('publish','rename','disappear','replace'):
 a=race(old,'old-'+action,action);b=race(new,'new-'+action,action)
 if action!='replace':assert a['status']=='raised' and a['type']=='FileNotFoundError'
 assert b['status']=='returned' and b['attempts']==2 and len(b['mutations'])==1
 assert b['logical']==(0 if action=='disappear' else 19 if action=='replace' else 14)

# Actual close callback after initial traversal: output remains in owned fixture.
def closing_change(module,name,kind,always=False):
 p=root(name);(p/'a').write_bytes(b'x');watch=module.StorageWatch(p,LIMITS)
 prior=module.os.close;counter=0
 def close(fd):
  nonlocal counter
  prior(fd)
  if counter==0 or always:
   counter+=1
   if kind=='growth':
    with (p/'a').open('ab') as f:f.write(b'xx')
   else:(p/('added-'+str(counter))).write_bytes(b'zzz')
 module.os.close=close
 try:
  try:r=watch.check();out={'status':'returned','logical':r['logical_file_bytes'],'attempts':r['scan_attempts']}
  except Exception as e:out={'status':'raised','type':type(e).__name__,'observation':getattr(e,'observation',{})}
 finally:module.os.close=prior
 results.append({'case':name,**out,'close_mutations':counter});return out
for kind in ('growth','extra'):
 a=closing_change(old,'old-close-'+kind,kind);b=closing_change(new,'new-close-'+kind,kind)
 assert a['logical']==1 and b['logical']==(3 if kind=='growth' else 4) and b['attempts']==2
x=closing_change(new,'new-persistent-close-churn','extra',True)
assert x['status']=='raised' and x['type']=='StorageMutationObservation'

# Any observed registered limit remains terminal, without a mutation retry.
for key,value,reason in [('max_logical_bytes',1,'logical'),('max_allocated_bytes',1,'allocated'),('max_entries',1,'entries'),('max_depth',1,'depth')]:
 p=root('limit-'+reason);(p/'a').write_bytes(b'xx');(p/'b').mkdir();(p/'b'/'deep').mkdir()
 try:new.StorageWatch(p,{**LIMITS,key:value}).check()
 except new.StorageLimit as e:assert e.reason==reason;results.append({'case':'limit-'+reason,'reason':e.reason,'observation':e.observation})
 else:raise AssertionError(reason)
# Sparse logical oversize is never allocated-only credit.
p=root('sparse-logical');f=p/'sparse.body'
with f.open('xb') as out:out.truncate(4097)
try:new.StorageWatch(p,{**LIMITS,'max_logical_bytes':4096}).check()
except new.StorageLimit as e:assert e.reason=='logical';results.append({'case':'sparse-logical','reason':e.reason})
else:raise AssertionError('sparse accepted')
for kind in ('link','hardlink'):
 p=root(kind);(p/'a').write_bytes(b'x')
 if kind=='link':(p/'b').symlink_to('a')
 else:os.link(p/'a',p/'b')
 try:new.StorageWatch(p,LIMITS).check()
 except ValueError as e:results.append({'case':kind,'type':type(e).__name__})
 else:raise AssertionError(kind)
# Real fd close, then ordinary/fatal callback error; all descriptors remain closed.
for i,primary_type in enumerate((ValueError,KeyboardInterrupt,MemoryError,SystemExit)):
 for j,secondary_type in enumerate((RuntimeError,KeyboardInterrupt,MemoryError,SystemExit)):
  p=root('fatal-'+str(i)+'-'+str(j));fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY)
  primary=primary_type('first');secondary=secondary_type('close')
  def action():os.close(fd);raise secondary
  try:new._cleanup(action,primary)
  except BaseException as e:
   expected=primary if not isinstance(primary,Exception) or isinstance(primary,MemoryError) else secondary if not isinstance(secondary,Exception) or isinstance(secondary,MemoryError) else None
   assert e is expected if expected is not None else type(e) is new.StorageCleanupFailure
   try:os.fstat(fd)
   except OSError:pass
   else:raise AssertionError('descriptor remains open')
   results.append({'case':'fatal-pair','primary':primary_type.__name__,'secondary':secondary_type.__name__,'selected':type(e).__name__,'descriptor_closed':True})
  else:raise AssertionError('cleanup accepted')
# Ordinary cleanup uncertainty is not retried as a publication race.
p=root('uncertain-close');(p/'a').write_bytes(b'x');prior=new.os.close
calls=[]
def uncertain(fd):prior(fd);calls.append(fd);raise RuntimeError('actual close completed but uncertainty reported')
new.os.close=uncertain
try:
 try:new.StorageWatch(p,LIMITS).check()
 except new.StorageCleanupFailure:assert len(calls)==1;results.append({'case':'uncertain-close','attempted_closes':len(calls),'retried':False})
 else:raise AssertionError('cleanup accepted')
finally:new.os.close=prior
print(json.dumps({'status':'OPAQUE_UTILITY_CONTROLS_ONLY','cases':len(results),'results':results,'scientific_execution':False},indent=2))
