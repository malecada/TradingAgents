import ast,hashlib,importlib.util,json,os
from pathlib import Path
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent
rows=[]
def load(name):
 spec=importlib.util.spec_from_file_location(name,HERE/(name+'.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.os=SimpleNamespace(**{k:getattr(os,k) for k in dir(os)});return m
m=load('workflow_storage');old=load('original_workflow_storage')
LIMITS=dict(max_allocated_bytes=1<<20,max_logical_bytes=1<<20,max_entries=100,max_depth=8,max_scan_seconds=5)
def root(name):p=HERE/'controls16'/name;p.mkdir(parents=True,mode=0o700);return p
before=len(os.listdir('/proc/self/fd'))
p=root('directory-replace');(p/'child').mkdir();(p/'child'/'original').write_bytes(b'original')
w=m.StorageWatch(p,LIMITS);previous=m.os.open;done=False
def replace(path,*args,**kw):
 global done
 if path=='child' and not done:
  done=True;os.rename(p/'child',p.parent/'retained-old-child');(p/'child').mkdir();(p/'child'/'new').write_bytes(b'new')
 return previous(path,*args,**kw)
m.os.open=replace
try:r=w.check();assert r['logical_file_bytes']==3 and r['scan_attempts']==2;rows.append({'case':'opened-directory-replacement','attempts':r['scan_attempts'],'logical':r['logical_file_bytes']})
finally:m.os.open=previous
p=root('pending-counted');(p/'.pending-still-live').write_bytes(b'counts');r=m.StorageWatch(p,LIMITS).check();assert r['logical_file_bytes']==6 and r['regular_files']==1;rows.append({'case':'pending-name-never-ignored','logical':6})
p=root('cleanup-growth-over-limit');(p/'a').write_bytes(b'x');w=m.StorageWatch(p,{**LIMITS,'max_logical_bytes':2});previous=m.os.close;calls=0
def growth(fd):
 global calls
 previous(fd);calls+=1
 with (p/'a').open('ab') as stream:stream.write(b'xx')
m.os.close=growth
try:
 try:w.check()
 except m.StorageLimit as e:assert e.reason=='logical' and e.observation['logical_file_bytes']==3 and calls==1;rows.append({'case':'observed-cleanup-growth-limit-terminal','closes':calls,'reason':e.reason})
 else:raise AssertionError('observed overlimit retried')
finally:m.os.close=previous
# A permanently changed root is not rebound to a new inode on retry.
p=root('root-replacement');w=m.StorageWatch(p,LIMITS);os.rename(p,p.parent/'root-retained');p.mkdir()
try:w.check()
except ValueError as e:assert str(e)=='owned storage root replaced';rows.append({'case':'root-identity-not-rebound','type':type(e).__name__})
else:raise AssertionError('new root accepted')
# Reproduce inherited diagnostic callback replacing a fatal primary, and correct it.
class PrimaryInterrupt(KeyboardInterrupt):
 def add_note(self,note):raise SystemExit('note callback cannot replace first fatal')
for mod in (old,m):
 p=root('note-'+mod.__name__);fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY);primary=PrimaryInterrupt('original')
 def close():os.close(fd);raise RuntimeError('close failed after actual close')
 try:mod._cleanup(close,primary)
 except BaseException as e:
  if mod is old:assert type(e) is SystemExit
  else:assert e is primary and len(e.storage_cleanup_errors)==1
  rows.append({'case':'primary-note-'+mod.__name__,'selected':type(e).__name__,'original_primary_retained':e is primary})
 else:raise AssertionError('close uncertainty accepted')
# Test genuine original pure observe_storage closure in isolation; no resource guard start.
source=Path('/home/malecada/master_thesis/onchain-financial-isolation/genuine-financial-wrapper-claimedrun-native-20261004-02/source/tradingagents/research/onchain_replication/resources.py')
tree=ast.parse(source.read_text());node=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='observe_storage')
p=root('actual-resource-closure');(p/'a').write_bytes(b'xx');state={};env={'storage_watch':m.StorageWatch(p,LIMITS),'state':state}
exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),env)
env['observe_storage']();assert state['storage_peak_logical_file_bytes']==2
(p/'b').write_bytes(b'xxx');env['observe_storage']();assert state['storage_peak_logical_file_bytes']==5
rows.append({'case':'actual-observe-storage-peaks-retained','logical_peak':state['storage_peak_logical_file_bytes'],'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
# Explicit finite synthetic time refusal: no claim of measured real runtime capacity.
p=root('deadline');w=m.StorageWatch(p,LIMITS);values=iter([0,6]);previous=m.time;m.time=SimpleNamespace(monotonic=lambda:next(values),sleep=lambda x:None)
try:
 try:w.check()
 except m.StorageLimit as e:assert e.reason=='time';rows.append({'case':'aggregate-time-refusal','synthetic_clock':True})
 else:raise AssertionError('deadline accepted')
finally:m.time=previous
assert len(os.listdir('/proc/self/fd'))==before
rows.append({'case':'actual-reviewer-fd-count','before':before,'after':len(os.listdir('/proc/self/fd')),'historical_other_processes_proved':False})
print(json.dumps({'status':'OPAQUE_ADDITIONAL_CONTROLS_ONLY','cases':len(rows),'results':rows},indent=2))
