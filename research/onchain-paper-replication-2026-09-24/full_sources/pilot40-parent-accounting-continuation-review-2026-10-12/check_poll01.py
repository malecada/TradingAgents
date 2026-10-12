from pathlib import Path
import os,resource
os.sched_setaffinity(0,{2,3});resource.setrlimit(resource.RLIMIT_AS,(1024**3,1024**3));resource.setrlimit(resource.RLIMIT_CPU,(60,60))
import ast,json,runpy,hashlib,difflib
F=Path('research/onchain-paper-replication-2026-09-24/full_sources');C=F/'pilot40-continuation-target-poll-candidate-2026-10-12';h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert h(C/'SOURCE_MANIFEST02.json')=='7a0e587d828832b1ba11a711aeb2e217376bc7a4aa3cf68b111920b769e3976b'
m=json.loads((C/'SOURCE_MANIFEST02.json').read_text())
for row in m['files']+m['source_pins']:
 p=Path(row['path']);assert p.stat().st_size==row['bytes'] and h(p)==row['sha256']
fwd=[];inv=[]
for name in m['changed_sources']:
 a=(C/('BASELINE_'+name)).read_text();b=(C/name).read_text();path='tradingagents/research/onchain_replication/'+name
 fwd.extend(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='a/'+path,tofile='b/'+path));inv.extend(difflib.unified_diff(b.splitlines(True),a.splitlines(True),fromfile='a/'+path,tofile='b/'+path))
assert ''.join(fwd)==(C/'CANDIDATE02.diff').read_text();assert ''.join(inv)==(C/'INVERSE02.diff').read_text()
t=ast.parse((C/'batched_continuation.py').read_text())
for node in ast.walk(t):
 if isinstance(node,ast.With) and any('_lock(' in ast.unparse(i.context_expr) for i in node.items):
  assert not any(isinstance(c,ast.Call) and isinstance(c.func,ast.Name) and c.func.id=='_poll_target' for c in ast.walk(node))
ns=runpy.run_path(str(C/'check02.py'));Fixture=ns['Fixture'];results=[]
# Original transaction failure propagates identically, without running the post poll.
f=Fixture()
try:
 fatal=SystemExit('source failure');f.run._check_source=lambda:(_ for _ in ()).throw(fatal)
 try:f.ns['_bounded_input'](f.run,'x',max_bytes=100,target=f.target)
 except BaseException as e:assert e is fatal and f.polls==1 and not f.active_lock
 else:raise AssertionError('accepted source failure')
 results.append('original transaction fatal unchanged; lock released; no later poll')
finally:f.close()
# Mutation of a non-first batched input at the second poll is independently rejoined.
f=Fixture()
try:
 def mutate(target):
  if f.polls==2:f.values['y']=b'changed-y'
 f.hook=mutate
 try:f.ns['_polled_batch_inputs'](f.run,('x','y'),f.target)
 except ValueError as e:assert 'body changed after target poll' in str(e)
 else:raise AssertionError('accepted second body mutation')
 results.append('later batch role post-callback mutation refused')
finally:f.close()
# Retained reader rejects a coherent replacement execution before any batch read.
f=Fixture()
try:
 pin=f.ns['_target_identity'](f.run,f.target);reader=(f.run,b'{}',False,'manifest',pin);f.target.execution=ns['N'](_owner=f.owner,_bound=f.owner.bound)
 try:f.ns['_reader_target'](f.run,reader)
 except ValueError:pass
 else:raise AssertionError('accepted replacement execution')
 assert not f.events;results.append('retained execution identity replacement refused before reads')
finally:f.close()
# Exact selected transaction deadline remains binding; two 29s checks fit, two31s do not.
for cost,ok in [(29,True),(31,False)]:
 f=Fixture(cost=cost)
 try:
  try:r=f.ns['_bounded_input'](f.run,'x',max_bytes=100,target=f.target)
  except ValueError as e:assert not ok and 'stale interval' in str(e)
  else:assert ok and r==b'x'
 finally:f.close()
results.append('58-second transaction accepted;62-second transaction still stale-refused')
print(json.dumps({'status':'PASS','controls':results,'no_poll_inside_lock_ast':True,'manifest_and_literal_inverse':True,'genuine_authority_constructed':False},indent=2))
